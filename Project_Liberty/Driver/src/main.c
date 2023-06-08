#include <usb.h>
#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <signal.h>

#include <sys/time.h>
#include <time.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#include <json-c/json.h>

#include "liberty.h"
#include "protocol.h"

/* Vendor 0x0f44 -> Polhemus */
#define VENDOR 0xf44
/* Product 0xff20 -> Liberty v2 Motion Tracker (with USB 2.0 using an EzUSB fx2
   chip)  after loading the firmware (it has ProductId 0xff21 before) */
#define PRODUCT 0xff20

/* make control character out of ordinary character */
#define control(c) ((c) & 0x1f)

static int count_bits(uint16_t v)
{
    int c;
    for (c = 0; v; c++)
    {
        v &= v - 1; // clear the least significant bit set
    }
    return c;
}

/* main loop running? */
static int go_on;

static void signal_handler(int s)
{
    switch (s)
    {
    case SIGINT:
        go_on = 0;
        break;
    }
}

static void print_hex(FILE *stream, const char *buf, size_t size)
{
    const char *c;
    for (c = buf; c != buf + size; ++c)
        fprintf(stream, "%02x:%c ", (unsigned char)*c, isprint(*c) ? *c : '.');
    fprintf(stream, "\n");
}

static void print_ascii(FILE *stream, const char *buf, size_t size)
{
    const char *c;
    for (c = buf; c != buf + size; ++c)
        if (isprint(*c))
        {
            fprintf(stream, "%c", *c);
        }
    fprintf(stream, "\n");
}

static struct usb_device *find_device_by_id(uint16_t vendor, uint16_t product)
{
    struct usb_bus *bus;

    usb_find_busses();
    usb_find_devices();

    for (bus = usb_get_busses(); bus; bus = bus->next) {
        struct usb_device *dev;
        for (dev = bus->devices; dev; dev = dev->next) {
            if (dev->descriptor.idVendor == vendor
                && dev->descriptor.idProduct == product)
                return dev;
        }
    }
    return NULL;
}

static int request_num_of_stations(usb_dev_handle *handle, buffer_t *b)
{
    static char cmd[] = {control('u'), '0', '\r', '\0'};
    active_station_state_response_t resp;
    liberty_send(handle, cmd);
    liberty_receive(handle, b, &resp, sizeof(resp));

    if (resp.head.init_cmd == 21)
    {
        return count_bits(resp.detected & resp.active);
    }
    else
    {
        return 0;
    }
}

/* sets the zenith of the hemisphere in direction of vector (x, y, z) */
static void set_hemisphere(usb_dev_handle *handle, int x, int y, int z)
{
    char cmd[32];
    snprintf(cmd, sizeof(cmd), "h*,%d,%d,%d\r", x, y, z);
    liberty_send(handle, cmd);
}

static void set_update_rate(usb_dev_handle *handle, int rate)
{
    char cmd[32];
    snprintf(cmd, sizeof(cmd), "R%d\r", rate);
    liberty_send(handle, cmd);
}

int main()
{
    int i;
    struct usb_device *dev;
    usb_dev_handle *handle;

    usb_init();

    dev = find_device_by_id(VENDOR, PRODUCT);
    if (!dev)
    {
        fprintf(stderr, "Could not find the Polhemus Liberty Device.\n");
        abort();
    }

    handle = usb_open(dev);
    if (!handle)
    {
        fprintf(stderr, "Could not get a handle to the Polhemus Liberty Device.\n");
        abort();
    }

    if (!liberty_init(handle))
    {
        fprintf(stderr, "Could not initialize the Polhemus Liberty Device. Aborting.\n");
        usb_close(handle);
        return 1;
    }

    buffer_t buf;
    init_buffer(&buf);

    /* activate binary mode */
    liberty_send(handle, "f1\r");

    int n_stations = request_num_of_stations(handle, &buf);
    fprintf(stderr, "found %d stations\n", n_stations);

    /* Valid amounts of sensors are between 1 and 16 */
    if (n_stations == 0)
    {
        abort();
    }

    /* define which information to get per sensor (called a station
       by Polhemus)

       o* applies to all stations

       if this is changed, the station_t struct has to be edited accordingly */
    liberty_send(handle, "o*,8,9,11,3,7\r");
    /* set output hemisphere -- this will produce a response which we're
       ignoring */
    // see page 34 for other hemisphere options
    set_hemisphere(handle, 1, 0, 0);
    /* switch output to centimeters */
    liberty_send(handle, "u1\r");
    liberty_clear_input(handle); //right now, we just ignore the answer

    station_t *stations = (station_t *)(malloc(sizeof(station_t) * n_stations));
    if (!stations)
        abort();

    // Create a named pipe (FIFO)
    const char *fifoPath = "/tmp/motion_data_fifo";
    mkfifo(fifoPath, 0666);

    // Open the named pipe for writing
    int fifoFd = open(fifoPath, O_WRONLY);
    if (fifoFd == -1)
    {
        fprintf(stderr, "Failed to open the named pipe\n");
        return 1;
    }

    // Set up signal handler to catch the interrupt signal
    signal(SIGINT, signal_handler);

    go_on = 1;

        /* get the time when we begin */
    struct timeval tv;
    gettimeofday(&tv,NULL);
    printf("Timestamp: %d.%06d\n",(unsigned int)(tv.tv_sec),(unsigned int)(tv.tv_usec));
    
    /* enable continuous mode (get data points continously) */
    liberty_send(handle, "c\r");

    // Set the update rate, handle 3 = 120hz-handle 4 = 240hz
    set_update_rate(handle, 3);

    while (go_on) {
        if (!liberty_receive(handle, &buf, stations, sizeof(station_t) * n_stations)) {
            fprintf(stderr, "receive failed\n");
            return 2;
        }

        // Create a JSON array to hold the station data
        json_object *data_array = json_object_new_array();

        for (i = 0; i < n_stations; ++i) {
            // Create a JSON object for each station's data
            json_object *data_object = json_object_new_object();

            // Add the data fields to the JSON object
            json_object_object_add(data_object, "timestamp", json_object_new_int(stations[i].timestamp));
            json_object_object_add(data_object, "framecount", json_object_new_int(stations[i].framecount));
            json_object_object_add(data_object, "station_id", json_object_new_int(i));
            json_object_object_add(data_object, "distortion", json_object_new_int(stations[i].distortion));
            json_object_object_add(data_object, "x", json_object_new_double(stations[i].x));
            json_object_object_add(data_object, "y", json_object_new_double(stations[i].y));
            json_object_object_add(data_object, "z", json_object_new_double(stations[i].z));
            json_object_object_add(data_object, "quaternion_0", json_object_new_double(stations[i].quaternion[0]));
            json_object_object_add(data_object, "quaternion_1", json_object_new_double(stations[i].quaternion[1]));
            json_object_object_add(data_object, "quaternion_2", json_object_new_double(stations[i].quaternion[2]));
            json_object_object_add(data_object, "quaternion_3", json_object_new_double(stations[i].quaternion[3]));

            // Add the station data object to the array
            json_object_array_add(data_array, data_object);
        }

        // Get the JSON string representation of the data array
        const char *json_string = json_object_to_json_string(data_array);

        // Write the JSON string to the named pipe
        write(fifoFd, json_string, strlen(json_string));

        // Free the JSON objects and array
        json_object_put(data_array);

    }


    // Stop continuous mode
    liberty_send(handle, "p");

    usb_close(handle);

    free(stations);
    stations = NULL;

    // Clean up and close the named pipe
    close(fifoFd);
    unlink(fifoPath);

    return 0;
}

