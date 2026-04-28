#This is a test .py not sure if it will work(can be skipped)

#pip install adafruit-circuitpython-servokit
#sudo apt-get update
#sudo apt-get install python3-tk

from adafruit_servokit import ServoKit
import time
import tkinter as tk

# Initialize servo driver (16 channels)
kit = ServoKit(channels=16)

# Assign your servos (change channels if needed)
LEFT_ARM = 0
RIGHT_ARM = 1
LEFT_LEG = 2
RIGHT_LEG = 3

# Default positions
DEFAULT_POS = 90

# ---- RESET FUNCTION ----
def reset_position():
    kit.servo[LEFT_ARM].angle = DEFAULT_POS
    kit.servo[RIGHT_ARM].angle = DEFAULT_POS
    kit.servo[LEFT_LEG].angle = DEFAULT_POS
    kit.servo[RIGHT_LEG].angle = DEFAULT_POS
    print("Reset to default position")

# ---- FORWARD WALK ----
def move_forward():
    print("Moving forward")

    # Step 1
    kit.servo[LEFT_LEG].angle = 60
    kit.servo[RIGHT_LEG].angle = 120
    kit.servo[LEFT_ARM].angle = 120
    kit.servo[RIGHT_ARM].angle = 60
    time.sleep(0.4)

    # Step 2
    kit.servo[LEFT_LEG].angle = 120
    kit.servo[RIGHT_LEG].angle = 60
    kit.servo[LEFT_ARM].angle = 60
    kit.servo[RIGHT_ARM].angle = 120
    time.sleep(0.4)

    # Back to neutral
    reset_position()

# ---- MANUAL CONTROL ----
def set_servo(channel, angle):
    kit.servo[channel].angle = int(angle)

# ---- GUI CONTROL PANEL ----
root = tk.Tk()
root.title("TARS Robot Control Panel")

# Sliders for manual control
def create_slider(label, channel):
    frame = tk.Frame(root)
    frame.pack()

    tk.Label(frame, text=label).pack()

    slider = tk.Scale(frame, from_=0, to=180, orient=tk.HORIZONTAL,
                      command=lambda val: set_servo(channel, val))
    slider.set(DEFAULT_POS)
    slider.pack()

create_slider("Left Arm", LEFT_ARM)
create_slider("Right Arm", RIGHT_ARM)
create_slider("Left Leg", LEFT_LEG)
create_slider("Right Leg", RIGHT_LEG)

# Buttons
tk.Button(root, text="Reset", command=reset_position).pack()
tk.Button(root, text="Move Forward", command=move_forward).pack()

# Start in reset position
reset_position()

root.mainloop()