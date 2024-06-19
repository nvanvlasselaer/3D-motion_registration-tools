import json
import csv
import serial
import time
import threading
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.spatial.transform import Rotation as R
from collections import deque
import os
import numpy as np

# Define the serial port and baud rate
port = '/dev/cu.usbserial-02898D2B'  # Change this to the appropriate serial port
baud_rate = 115200

# Define the output CSV file
output_file = 'quaternion_data.csv'

# Initialize the serial connection
ser = serial.Serial(port, baud_rate)

data = deque(maxlen=1000)
angles = deque(maxlen=100)
dataout = deque(maxlen=1000)

euler_sequence = 'xyz'  # Default Euler sequence

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
    counter.clear()

def reorder_quaternion(quat):
    # Reorder quaternion from w, x, y, z to x, y, z, w for Scipy
    return [quat[1], quat[2], quat[3], quat[0]]

def calculate_angular_difference(q1, q2):
    r1 = R.from_quat(q1)
    r2 = R.from_quat(q2)
    r = r1.inv() * r2
    return r.as_euler(euler_sequence, degrees=True)

def quaternion_to_euler(q):
    r = R.from_quat(q)
    return r.as_euler(euler_sequence, degrees=True)


def read_serial_data():
    global angles, calib1, calib2
    global dataout
    global dataout_row
    global counter
    
    quat1 = None
    quat2 = None
    counter = 0

    while True:
        data_row = []
        data_row.append(time.time())  # Append timestamp
        line = ser.readline().decode().strip()

        try:
            data = json.loads(line)

            # Extract quaternion data from sensors
            if data['key'] == '/sensor/1':
                quat1 = data['value']
                calib1 = data['calibration']
            if data['key'] == '/sensor/2':
                quat2 = data['value']
                calib2 = data['calibration']
                
            if quat1 is not None and quat2 is not None:
                # Calculate and store angular differences every 10 iterations
                if counter % 10 == 0:
                    scipy_quat1 = reorder_quaternion(quat1)
                    scipy_quat2 = reorder_quaternion(quat2)
                    euler_angles = calculate_angular_difference(scipy_quat1, scipy_quat2)
                    # euler_angles = quaternion_to_euler(reordered_quat1)


                    angles.append(euler_angles)
                # Update calibration text box
                    calibration_text = f"sensor1={calib1} sensor2={calib2}"
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, calibration_text)
                
                counter += 1
                # Prepare formatted data for output
                dataout_row = [data_row[0]]
                dataout_row.extend(quat1)
                dataout_row.extend(quat2)
                dataout_row.extend(euler_angles)  # The euler_angles variable is used here
                dataout.append(dataout_row)

        except (ValueError, KeyError):
            continue


def update_plot():
    global angles

    if len(angles) > 0:
        ax.clear()
        ax.plot(angles)
        ax.legend(['1', '2', '3'], bbox_to_anchor=(1.05, 1), loc='upper left')  ### check Euler sequence!
        ax.set_xlabel('Time')
        ax.set_ylabel('Angular difference (degrees)')
        canvas.draw()
    root.after(200, update_plot)  # Update plot every 200 milliseconds


def log_text(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

def set_euler_sequence(sequence):
    global euler_sequence
    euler_sequence = sequence

# Create GUI
root = tk.Tk()
root.title("Serial Data Recorder and Plotter")

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

# Create radio buttons for Euler sequence selection
euler_label = tk.Label(root, text="Euler Sequence:")
euler_label.pack(side=tk.LEFT)

euler_frame = tk.Frame(root)
euler_frame.pack(side=tk.LEFT)

sequence_var = tk.StringVar()

# Create a grid to organize the radio buttons
row_num = 0
col_num = 0

xyz_radio = tk.Radiobutton(euler_frame, text="xyz", variable=sequence_var, value="xyz", command=lambda: set_euler_sequence("xyz"))
xyz_radio.grid(row=row_num, column=col_num, sticky="w")

yxz_radio = tk.Radiobutton(euler_frame, text="yxz", variable=sequence_var, value="yxz", command=lambda: set_euler_sequence("yxz"))
yxz_radio.grid(row=row_num, column=col_num+1, sticky="w")

zxy_radio = tk.Radiobutton(euler_frame, text="zyx", variable=sequence_var, value="zyx", command=lambda: set_euler_sequence("zyx"))
zxy_radio.grid(row=row_num, column=col_num+2, sticky="w")

row_num = 1

zyx_radio = tk.Radiobutton(euler_frame, text="xzy", variable=sequence_var, value="xzy", command=lambda: set_euler_sequence("xzy"))
zyx_radio.grid(row=row_num, column=col_num, sticky="w")

xzy_radio = tk.Radiobutton(euler_frame, text="yzx", variable=sequence_var, value="yzx", command=lambda: set_euler_sequence("yzx"))
xzy_radio.grid(row=row_num, column=col_num+1, sticky="w")

yzx_radio = tk.Radiobutton(euler_frame, text="zxy", variable=sequence_var, value="zxy", command=lambda: set_euler_sequence("zxy"))
yzx_radio.grid(row=row_num, column=col_num+2, sticky="w")

# Set default Euler sequence
sequence_var.set(euler_sequence)
set_euler_sequence(sequence_var.get())

# Start serial data reading in a separate thread
serial_thread = threading.Thread(target=read_serial_data)
serial_thread.daemon = True
serial_thread.start()

# Start plot updating in a separate thread
plot_thread = threading.Thread(target=update_plot)
plot_thread.daemon = True
plot_thread.start()

# Start GUI loop
root.mainloop()
