# Polhemus Liberty Driver for Linux

This driver provides support for the Polhemus Liberty v2 motion tracker on Linux systems. The driver utilizes the USB2 interface of the Liberty v2 device to transmit tracking data at a frequency of 120Hz (optionally 240Hz).

The driver consists of two main parts:

1. Firmware loader: This includes scripts for udev and the firmware itself.
2. Library based on libUSB: The library communicates with the motion tracker and is built on top of the libUSB library.

## Dependencies

Before installing and using the driver, ensure that the following dependencies are installed on your system:

- fxload: Used to load the firmware onto the USB device.
- libusb-dev: Development files for the libUSB library, which is used for programming USB applications without requiring knowledge of Linux kernel internals.

On Debian GNU/Linux, you can install these dependencies by running the following command:

```
sudo apt-get install fxload libusb-dev
```

On Mac you can use homebrew (fxload, libusb and libusb-compat)

## Installation

Follow these steps to install and set up the driver:

1. Install the dependencies mentioned above using the provided command.
2. Navigate to the `firmware_load` directory and follow the instructions provided there to install the udev configuration files and firmware files.
3. Run the `make` command in the `src` directory to build the driver.
4. Once the build process is complete, execute the program using the following command:

```
./liberty
```

The driver should detect the connected motion tracker and display the number of sensors attached to it. It will then start printing the position and orientation data to the fifo location ("/tmp/motion_data_fifo").

Note: Ensure that you connect the sensors correctly. Connect the first sensor to input #1 and subsequent sensors to the following inputs without leaving any empty inputs in between. For example, if you have three sensors, connect them to inputs #1, #2, and #3, rather than #1, #2, and #4.

## Development

If you wish to develop your own programs utilizing the Polhemus Liberty v2 motion tracker, you can utilize the provided `liberty.c` and `liberty.h` files. These files handle all the low-level communication with the Liberty v2 device and offer a convenient API for accessing the tracking data.

## Acknowledgments

This driver includes parts implemented from the Cognition for Technical Systems (CoTeSys) project, working at the Technische Universitaet Muenchen, specifically at the chair for intelligent autonomous systems. The project's collaborators include Alexis Maldonado, Federico Ruiz, Jonathan Kleinehellefort, and Ingo Kresse, under the supervision of Prof. Michael Beetz, PhD.

We would like to express our gratitude to the auteurs for making their code available and contributing to the development of this driver.


