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
import math

fifo_path = "/tmp/motion_data_fifo"

# Open the named pipe for reading
fifo_fd = os.open(fifo_path, os.O_RDONLY)

data = deque(maxlen=5000)
angles = deque(maxlen=1200) #needs to be 5x smaller because only calculated every 2 iterations and plotted every 10 
dataout = deque(maxlen=5000)
sensor1_angles = deque(maxlen=500)
sensor2_angles = deque(maxlen=500)
manual_angles = deque(maxlen=500)

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
    data_header_row = ['Time', 'w1', 'x1', 'y1', 'z1', 'loc1_x','loc1_y', 'loc1_z']

    # Create a copy of dataout before iterating over it
    dataout_copy = list(dataout)

    with open(file_path_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data_header_row)
        for row in dataout_copy:
            writer.writerow(row)

snapshot_counter = 0
snapshot_counter_label = None

def update_snapshot_counter_label():
    global snapshot_counter_label, snapshot_counter
    if snapshot_counter_label:
        snapshot_counter_label.config(text="Snapshot Counter: {}".format(snapshot_counter))
    root.after(200, update_snapshot_counter_label)  # Update every 200ms

def create_snapshot():
    global snapshot_counter
    try:
        subject_name = subject_entry.get()  # Get the subject name from the input box

        # Add the counter value to the snapshot row
        snapout_row_with_counter = [snapshot_counter+1] + snapout_row

        write_snapshot_to_csv(snapout_row_with_counter, subject_name + 'snapshot')

        # Increment the snapshot counter only if there is no error
        snapshot_counter += 1

        # Write a message to the log_box
        log_text("Snapshot {} created for subject: {}".format(snapshot_counter, subject_name))

        # Update the snapshot counter label
        update_snapshot_counter_label()
    except NameError as e:
        log_text("Error: {}".format(e))

def write_snapshot_to_csv(snapout_row, subject_name):
    global file_path
    file_name = subject_name + '.csv'  # Create the file name by appending subject_name with '.csv'
    file_path_name = os.path.join(file_path, file_name)  # Combine the directory path with the file name
    snap_header_row = ['Snapshot Counter', 'Time', 'w1', 'x1', 'y1', 'z1', 'loc1_x','loc1_y', 'loc1_z']
    
    with open(file_path_name, mode='a', newline='') as file:  # Use 'a' mode for append
        writer = csv.writer(file)
        
        # Write the header row if the file is empty
        if os.path.getsize(file_path_name) == 0:
            writer.writerow(snap_header_row)
        
        writer.writerow(snapout_row)


def clear_data():
    global data, dataout, angles, ax, snapshot_counter
    data.clear()
    dataout.clear()
    angles.clear()
    ax.clear()
    snapshot_counter = 0  # Reset the snapshot counter to 0
    canvas.draw()
    # Update the snapshot counter label after resetting
    update_snapshot_counter_label()


def calculate_angular_difference(quat1, quat2):
    r1 = R.from_quat(quat1)
    r2 = R.from_quat(quat2)
    r = r2 * r1.inv()
    return r.as_euler(euler_sequence, degrees=True)

# def quat1_to_euler_xyz(quat1):
#     r = R.from_quat(quat1)
#     return r.as_euler(euler_sequence, degrees=True)

def quat2_to_euler_xyz(quat2):
    r = R.from_quat(quat2)
    return r.as_euler(euler_sequence, degrees=True)

def quaternion_to_euler_xyz(q):
    roll = math.degrees(math.atan2(2*(q[0]*q[1] + q[2]*q[3]), 1 - 2*(q[1]**2 + q[2]**2)))
    pitch = math.degrees(math.asin(2*(q[0]*q[2] - q[3]*q[1])))
    yaw = math.degrees(math.atan2(2*(q[0]*q[3] + q[1]*q[2]), 1 - 2*(q[2]**2 + q[3]**2)))
    return roll, pitch, yaw

# def quaternion_to_euler_xyz(q):  # https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
#     # Roll (x-axis rotation)
#     sinr_cosp = 2 * (q[0] * q[1] + q[2] * q[3])
#     cosr_cosp = 1 - 2 * (q[1] * q[1] + q[2] * q[2])
#     roll = math.atan2(sinr_cosp, cosr_cosp)

#     # Pitch (y-axis rotation)
#     sinp = math.sqrt(1 + 2 * (q[0] * q[2] - q[1] * q[3]))
#     cosp = math.sqrt(1 - 2 * (q[0] * q[2] - q[1] * q[3]))
#     pitch = math.atan2(sinp, cosp)

#     # Yaw (z-axis rotation)
#     siny_cosp = 2 * (q[0] * q[3] + q[1] * q[2])
#     cosy_cosp = 1 - 2 * (q[2] * q[2] + q[3] * q[3])
#     yaw = math.atan2(siny_cosp, cosy_cosp)

#     return roll, pitch, yaw

recording = True
RawData = False
Stylus = False

def read_fifo_data():
    global angles, calibration_box
    global dataout
    global dataout_row
    global snapout_row
    global recording
    global sensor1_angles
    global sensor2_angles
    # global manual_angles

    station1 = None
    station2 = None
    station3 = None
    quat1 = None
    quat2 = None
    loc1 = None
    loc2 = None
    loc3 = None
    distort1 = None
    distort2 = None
    distort3 = None

    dataout1_row = []
    dataout2_row = []

    counter = 0

    buffer = ""

    while True:
        if recording:
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
                    sensor1_xyz = None
                    manual_xyz = None

                    if station_id == 0:
                        station1 = data
                        quat1 = station1['quaternion_0'], station1['quaternion_1'], station1['quaternion_2'], station1['quaternion_3']
                        loc1 = station1['x'], station1['y'], station1['z']
                        distort1 = station1["distortion"]
                        dataout1_row = [data_row[0]]
                        dataout1_row.extend(quat1)
                        dataout1_row.extend(loc1)
                        if counter % 10 == 0:
                            sensor1_xyz = quaternion_to_euler_xyz(quat1)
                            sensor1_angles.append(sensor1_xyz)
                            # manual_xyz = quaternion_to_euler_xyz(quat1)
                            # manual_angles.append(manual_xyz)
                        counter += 1

                    elif station_id == 1:
                        station2 = data
                        quat2 = station2['quaternion_0'], station2['quaternion_1'], station2['quaternion_2'], station2['quaternion_3']
                        loc2 = station2['x'], station2['y'], station2['z']
                        distort2 = station2["distortion"]
                        # Initialize dataout_row for station_id 1
                        dataout2_row = [data_row[0]]
                        # Extend dataout_row with quat2 and loc2
                        dataout2_row.extend(quat2)
                        dataout2_row.extend(loc2)
                        # Create dataout_row and append it to dataout when station_id == 1
                        dataout_row = dataout1_row + dataout2_row
                        dataout.append(dataout_row)
                        if counter % 10 == 0:
                            sensor2_xyz = quat2_to_euler_xyz(quat2)
                            sensor2_angles.append(sensor2_xyz)


                    elif station_id == 2:
                        if Stylus:
                            station3 = data
                            loc3 = station3['x'], station3['y'], station3['z']
                            distort3 = station3["distortion"]
                            snapout_row = []
                            snapout_row.extend(dataout_row)
                            snapout_row.extend(loc3)

                    euler_angles = None

                    if station1 and station2:

                        if counter % 10 == 0:
                            euler_angles = calculate_angular_difference(quat1, quat2)
                            angles.append(euler_angles)

                            if RawData:
                                calibration_text = f"Cal: sensor1={distort1} sensor2={distort2} sensor3={distort3}"
                                calibration_box.delete(1.0, tk.END)
                                calibration_box.insert(tk.END, calibration_text)

                                location_text = f"Loc: sensor1={loc1} sensor2={loc2}"
                                location_box.delete(1.0, tk.END)
                                location_box.insert(tk.END, location_text)

                                stylus_text = f"Loc stylus={loc3}"
                                stylus_box.delete(1.0, tk.END)
                                stylus_box.insert(tk.END, stylus_text)             
                        counter += 1


                except (ValueError, KeyError, IndexError):
                    break


def pause_recording():
    global recording
    recording = False

def resume_recording():
    global recording
    recording = True

def activate_stylus():
    global Stylus
    Stylus = True

def deactivate_stylus():
    global Stylus
    Stylus = False

def update_stylus_dot():
    dot_color = "red" if not Stylus else "green"
    canvas_stylus.itemconfig(dot_item, fill=dot_color)
    root.after(200, update_stylus_dot)

def show_raw_data():
    global RawData
    RawData = True

def pause_raw_data():
    global RawData
    RawData = False

def extract_json_object(buffer):
    start_index = buffer.find('{')
    end_index = buffer.find('}')
    if start_index != -1 and end_index != -1:
        json_object = buffer[start_index:end_index + 1]
        buffer = buffer[end_index + 1:]
        return json_object, buffer
    return "", buffer


def update_plot1():
    global angles
    global sensor1_angles
    # global manual_angles

    # if len(manual_angles) > 0:
    #     ax.clear()
    #     ax.plot(manual_angles)
    if len(sensor1_angles) > 0:
        ax1.clear()
        ax1.plot(sensor1_angles)
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1)  # Add line at y=0
        ax1.axhline(y=10, color='red', linestyle='--', linewidth=1)  # Add line at y=10
        ax1.axhline(y=-10, color='red', linestyle='--', linewidth=1)  # Add line at y=-10
        ax1.legend(['1', '2', '3'], bbox_to_anchor=(1.05, 1), loc='upper left')  ### check Euler sequence!
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Sensor 1 - Manual')
        canvas.draw()
    root.after(200, update_plot1)  # Update plot every 200ms

def update_plot2():
    global angles
    global sensor2_angles

    if len(sensor2_angles) > 0:
        ax2.clear()
        ax2.plot(sensor2_angles)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1)  # Add line at y=0
        ax2.axhline(y=10, color='red', linestyle='--', linewidth=1)  # Add line at y=10
        ax2.axhline(y=-10, color='red', linestyle='--', linewidth=1)  # Add line at y=-10
        ax2.legend(['1', '2', '3'], bbox_to_anchor=(1.05, 1), loc='upper left')  ### check Euler sequence!
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Sensor 2 - Scipy')
        canvas.draw()
    root.after(200, update_plot2)  # Update plot every 200ms

def log_text(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    root.after(10, lambda: log_text(message))

def set_euler_sequence(sequence):
    global euler_sequence
    euler_sequence = sequence

# Create GUI
root = tk.Tk()
root.title("Polhemus Manual vs Scipy comparison")

# Frame for directory and filename
info_frame = tk.Frame(root)
info_frame.pack(pady=10)

file_button = tk.Button(info_frame, text="Choose Folder", command=choose_folder)
file_button.pack(side='left', padx=5)

subject_label = tk.Label(info_frame, text="Name:")
subject_label.pack(side='left')

subject_entry = tk.Entry(info_frame)
subject_entry.pack(side='left')

# Create a frame for the buttons
button_frame = tk.Frame(root)
button_frame.pack()

# Frame for data-related buttons
data_frame = tk.Frame(root)
data_frame.pack(pady=10)

save_data_button = tk.Button(data_frame, text="Save Data", command=save_data)
save_data_button.pack(side='left', padx=5)

create_snapshot_button = tk.Button(data_frame, text="Stylus Snapshot", command=create_snapshot)
create_snapshot_button.pack(side='left', padx=5)

snapshot_counter_label = tk.Label(data_frame, text="Snapshot Counter: {}".format(snapshot_counter))
snapshot_counter_label.pack(side='left', padx=5)

clear_button = tk.Button(data_frame, text="Clear Data", command=clear_data)
clear_button.pack(side='left')

# Frame for log information
log_frame = tk.Frame(root)
log_frame.pack(pady=10)

log_box = tk.Text(log_frame, height=2, width=80)
log_box.pack()

# Frame for control buttons
control_frame = tk.Frame(root)
control_frame.pack(pady=10)

pause_button = tk.Button(control_frame, text="Pause", command=pause_recording)
pause_button.pack(side='left', padx=5)

resume_button = tk.Button(control_frame, text="Resume", command=resume_recording)
resume_button.pack(side='left', padx=5)

show_raw_data_button = tk.Button(control_frame, text="Show Raw Data", command=show_raw_data)
show_raw_data_button.pack(side='left', padx=5)

pause_raw_data_button = tk.Button(control_frame, text="Pause Raw Data", command=pause_raw_data)
pause_raw_data_button.pack(side='left', padx=5)

# Frame for stylus activation/deactivation
stylus_frame = tk.Frame(root)
stylus_frame.pack(pady=10)

# Create Canvas for Stylus Dot
canvas_stylus = tk.Canvas(stylus_frame, width=20, height=20, bg="white")
canvas_stylus.grid(row=0, column=1, padx=5)

# Draw initial dot based on the initial value of Stylus
initial_dot_color = "red" if not Stylus else "green"
dot_item = canvas_stylus.create_oval(5, 5, 15, 15, fill=initial_dot_color)

# Stylus activation/deactivation buttons
stylus_activate_button = tk.Button(stylus_frame, text="Activate Stylus", command=activate_stylus)
stylus_activate_button.grid(row=0, column=0, padx=5)

stylus_deactivate_button = tk.Button(stylus_frame, text="Deactivate Stylus", command=deactivate_stylus)
stylus_deactivate_button.grid(row=0, column=2, padx=5)


stylus_box = tk.Text(root, height=1, width=160)
stylus_box.pack(side=tk.BOTTOM)

location_box = tk.Text(root, height=1, width=160)
location_box.pack(side=tk.BOTTOM)

# Create text box
calibration_box = tk.Text(root, height=1, width=160)
calibration_box.pack(side=tk.BOTTOM)

# Create plot
fig = Figure(figsize=(10, 4), dpi=100)
ax1 = fig.add_subplot(211)  # First subplot
ax2 = fig.add_subplot(212)  # Second subplot
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
canvas.draw()

# Create radio buttons for Euler sequence selection
euler_label = tk.Label(root, text="Scipy Euler Sequence:")
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


stylus_dot_thread = threading.Thread(target=update_stylus_dot)
stylus_dot_thread.daemon = True
stylus_dot_thread.start()

# Start serial data reading in a separate thread
serial_thread = threading.Thread(target=read_fifo_data)
serial_thread.daemon = True
serial_thread.start()

# Start plot updating in a separate thread
plot1_thread = threading.Thread(target=update_plot1)
plot1_thread.daemon = True
plot1_thread.start()

# Start plot updating in a separate thread
plot2_thread = threading.Thread(target=update_plot2)
plot2_thread.daemon = True
plot2_thread.start()


update_snapshot_counter_label()
# update_plot()

# Start GUI loop
root.mainloop()