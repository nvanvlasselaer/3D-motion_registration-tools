import json
import csv
import os
import time
import threading
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.spatial.transform import Rotation as R
from collections import deque

fifo_path = "/tmp/motion_data_fifo"

# Open the named pipe for reading
fifo_fd = os.open(fifo_path, os.O_RDONLY)

data = deque(maxlen=1000)
angles = deque(maxlen=1000)
dataout = deque(maxlen=1000)

def choose_folder():
    global file_path
    default_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    file_path = filedialog.askdirectory(initialdir=default_path)

def save_data():
    try:
        subject_name = subject_entry.get()  # Get the subject name from the input box
        log_text("Saved data for subject: {}".format(subject_name))
        write_data_to_csv(dataout, subject_name + 'data')  # Use subject_name as the filename
    except NameError as e:
        log_text("Error: {}".format(e))

def write_data_to_csv(dataout, subject_name):
    global file_path
    file_name = subject_name + '.csv'  # Create the file name by appending subject_name with '.csv'
    file_path_name = os.path.join(file_path, file_name)  # Combine the directory path with the file name
    header_row = ['Time', 'w1', 'x1', 'y1', 'z1', 'w2', 'x2', 'y2', 'z2', 'x_diff', 'y_diff', 'z_diff']
    with open(file_path_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header_row)
        for row in dataout:
            writer.writerow(row)

def save_snapshot():
    try:
        subject_name = subject_entry.get()  # Get the subject name from the input box
        log_text("Saved snapshot for subject: {}".format(subject_name))
        write_snapshot_to_csv(dataout_row, subject_name + 'snap')
    except NameError as e:
        log_text("Error: {}".format(e))


def write_snapshot_to_csv(dataout_row, subject_name):
    global file_path
    file_name = subject_name + '.csv'  # Create the file name by appending subject_name with '.csv'
    file_path_name = os.path.join(file_path, file_name)  # Combine the directory path with the file name
    header_row = ['Time', 'w1', 'x1', 'y1', 'z1', 'w2', 'x2', 'y2', 'z2', 'x_diff', 'y_diff', 'z_diff']
    with open(file_path_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(dataout_row)

def clear_data():
    data.clear()
    dataout.clear()
    angles.clear()
    ax.clear()
    canvas.draw()

def calculate_angular_difference(quat1, quat2):
    r1 = R.from_quat(quat1)
    r2 = R.from_quat(quat2)
    r = r2 * r1.inv()
    return r.as_euler('yxz', degrees=True)


def read_fifo_data():
    global angles, text_box
    global dataout
    global dataout_row

    station1 = None
    station2 = None
    quat1 = None
    quat2 = None
    distort1 = None
    distort2 = None

    buffer = ""

    while True:
        data_in = os.read(fifo_fd, 4096)
        buffer += data_in.decode('utf-8')

        # Process complete JSON objects in the buffer
        while True:
            try:
                json_object, buffer = extract_json_object(buffer)
                data = json.loads(json_object)

                data_row = []
                data_row.append(time.time())  # Append timestamp

                # Extract station_id from the data
                station_id = data.get("station_id")
                # Store data in the corresponding variable based on station_id
                if station_id == 0:
                    station1 = data
                elif station_id == 1:
                    station2 = data

                if station1 and station2:
                    # Extract the quaternion components for each station
                    quat1 = station1['quaternion_0'], station1['quaternion_1'], station1['quaternion_2'], station1['quaternion_3']
                    quat2 = station2['quaternion_0'], station2['quaternion_1'], station2['quaternion_2'], station2['quaternion_3']

                    distort1 = station1["distortion"]
                    distort2 = station2["distortion"]

                if quat1 is not None and quat2 is not None:
                    euler_angles = calculate_angular_difference(quat1, quat2)
                    angles.append(euler_angles)

                    calibration_text = f"sensor1={distort1} sensor2={distort2}"
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, calibration_text)

                    dataout_row = [data_row[0]]
                    dataout_row.extend(quat1)
                    dataout_row.extend(quat2)
                    dataout_row.extend(euler_angles)
                    dataout.append(dataout_row)

            except (ValueError, KeyError, IndexError):
                break

def extract_json_object(buffer):
    start_index = buffer.find('{')
    end_index = buffer.find('}')
    if start_index != -1 and end_index != -1:
        json_object = buffer[start_index:end_index + 1]
        buffer = buffer[end_index + 1:]
        return json_object, buffer
    return "", buffer


def update_plot():
    global angles

    if len(angles) > 0:
        ax.clear()
        ax.plot(angles)
        ax.legend(['x', 'y', 'z'], bbox_to_anchor=(1.05, 1), loc='upper left')  ### check Euler sequence!
        ax.set_xlabel('Time')
        ax.set_ylabel('Angular difference (degrees)')
        canvas.draw()
    root.after(200, update_plot)  # Update plot every 100ms

def log_text(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

# Create GUI
root = tk.Tk()
root.title("Polhemus Data Recorder and Plotter")

file_button = tk.Button(root, text="Choose Folder", command=choose_folder)
file_button.pack()

subject_label = tk.Label(root, text="Name:")
subject_label.pack()

subject_entry = tk.Entry(root)
subject_entry.pack()

# Create a frame for the buttons
button_frame = tk.Frame(root)
button_frame.pack()

# Save Data button
save_data_button = tk.Button(button_frame, text="Save Data", command=save_data)
save_data_button.pack(side='left', padx=5)

# Save Snapshot button
snapshot_button = tk.Button(button_frame, text="Save Snapshot", command=save_snapshot)
snapshot_button.pack(side='left', padx=5)

clear_button = tk.Button(root, text="Clear Data", command=clear_data)
clear_button.pack()

# Create text box
text_box = tk.Text(root, height=1, width=160)
text_box.pack(side=tk.BOTTOM)

log_box = tk.Text(root, height=2, width=80)
log_box.pack(side=tk.BOTTOM)

# Create plot
fig = Figure(figsize=(6, 4), dpi=100)
ax = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
canvas.draw()

# Start serial data reading in a separate thread
serial_thread = threading.Thread(target=read_fifo_data)
serial_thread.daemon = True
serial_thread.start()

# Start plot updating in a separate thread
plot_thread = threading.Thread(target=update_plot)
plot_thread.daemon = True
plot_thread.start()

# Start GUI loop
root.mainloop()

## Close the named pipe
#fifo_fd.close()