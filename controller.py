"""
This python file just mutates the state of a controller and that is all it will
do do not ask of it much else it tries its best.
The intention of this script is to serve two purposes:
    - the way to configure the dolphin controller for the pipe (executable)
    - a means for the agent to interface with the game(package)

When configuring, make sure you have a profile for the controller existing at in
/path/to/dolphinconfig/Profiles/GCPad/flatbot.ini
also running the latest version of dolphin couldn't hurt either or at least
Dolphin 5.0-10715
"""
from dataclasses import dataclass
from dataclasses import fields
import math
import numpy as np
import os
import configparser
import re
import random
import sys
import time


SSBM_CONFIG_FILENAME = "ssbm-memory-config.ini"
DOLPHIN_DIR = "/home/maximillian/.local/share/dolphin-emu/"
PIPE_PATH = "Pipes/flatbot"
CONTROLLER_PATH = "Config/GCPadNew.ini"
DOLPHIN_PATH = "Config/Dolphin.ini"

STICK_NEUTRAL = 0.5

BUTTON_PRESS = "PRESS"
BUTTON_RELEASE = "RELEASE"

# TODO: make this configureable
PORT = 2

CONTROLLER_UNPLUGGED = 0
CONTROLLER_STANDARD = 6
CONTROLLER_GCN_ADAPTER = 12

CARDINAL_DIRECTIONS = {
    # ordered for dolphin controller callibration
    "up": 90.0,
    "down": 270.0,
    "left": 180.0,
    "right": 0.0,
}
STICK_ITERATION_LENGTH = 5 / 60


@dataclass
class Button:
    pressed: bool = 0
    name: str = ""


@dataclass
class Stick:
    x: float = STICK_NEUTRAL
    y: float = STICK_NEUTRAL
    name: str = ""


@dataclass
class Analog:
    value: float = 0.0
    name: str = ""


@dataclass
class Controller:
    buttons_a: Button = Button(name="A")
    buttons_b: Button = Button(name="B")
    buttons_x: Button = Button(name="X")
    # buttons_y: Button = Button(name="Y")
    buttons_z: Button = Button(name="Z")
    # buttons_start: Button = Button(name="START")
    stick_main: Stick = Stick(name="MAIN")
    stick_c: Stick = Stick(name="C")
    # my bot won't disrespect
    # d_pad_up: Button = Button(name="D_UP")
    # d_pad_down: Button = Button(name="D_DOWN")
    # d_pad_left: Button = Button(name="D_LEFT")
    # d_pad_right: Button = Button(name="D_RIGHT")
    # triggers_l: Button = Button(name="L")
    # triggers_r: Button = Button(name="R")
    # analog_l: Analog = Analog(name="L")
    analog_r: Analog = Analog(name="R")


# action state
ACTION_A = 0
ACTION_B = 1
ACTION_X = 2
ACTION_ANALOG_R = 3
ACTION_STICK_MAIN_DIRECTION = 4
ACTION_STICK_MAIN_DISTANCE = 5
ACTION_STICK_C_DIRECTION = 6
ACTION_STICK_C_DISTANCE = 7

# controller_dict returns a dictionary of the controllers current state
def controller_state(controller: Controller) -> dict:
    result = {}
    for field in fields(controller):
        controller_attr = getattr(controller, field.name)
        if field.type == type(Button()):
            result[field.name] = controller_attr.pressed
            continue
        if field.type == type(Stick()):
            result["%s.x" % field.name] = controller_attr.x
            result["%s.y" % field.name] = controller_attr.y
            continue
        # analog
        result[field.name] = controller_attr.value
    return result


# callibrate_controller will sequentially press each button once so be
# ready in the dolphin controller configuration to listen for input.  Note if you
# already have a configuration saved doing this is not necessary
def callibrate_controller(controller: Controller, pipe: int, intvl: float, echo=False):
    # iterate over the default controller fields and send their results to dolphin
    for field in fields(controller):
        controller_attr = getattr(controller, field.name)
        if echo:
            print("sending %s" % field.name, flush=True)
        # button presses
        if field.type == type(Button()):
            time.sleep(intvl)
            _send_button_command(BUTTON_PRESS, controller_attr, pipe, echo=echo)
            time.sleep(0.05)
            _send_button_command(BUTTON_RELEASE, controller_attr, pipe, echo=echo)
            continue
        # do stick commands manually up, down, left, right
        if field.type == type(Stick()):
            for direction_name in CARDINAL_DIRECTIONS:
                direction_value = CARDINAL_DIRECTIONS[direction_name]
                if echo:
                    print("moving %s in direction %s" % (field.name, direction_name))
                time.sleep(intvl)
                move_stick(controller_attr, pipe, direction_value, 0.5, echo=echo)
                _release_stick(controller_attr, pipe, echo=echo)
            continue
        # analog shoulders
        set_analog_value(controller_attr, 1.0)
        time.sleep(intvl)
        _send_analog_command(controller_attr, pipe, echo=echo)
        set_analog_value(controller_attr, 0.0)
        time.sleep(0.05)
        _send_analog_command(controller_attr, pipe, echo=echo)


# _reset_controller will reset the controller and will send this result back to
# dolphin
def _reset_controller(controller: Controller, pipe: int, echo=False):
    # iterate over the default controller fields and send their results to dolphin
    for field in fields(controller):
        controller_attr = getattr(controller, field.name)
        if field.type == type(Button()):
            _send_button_command(BUTTON_RELEASE, controller_attr, pipe, echo=echo)
            continue
        if field.type == type(Stick()):
            continue
            _set_stick_xy(controller_attr, STICK_NEUTRAL, STICK_NEUTRAL)
            _send_stick_command(controller_attr, pipe, echo=echo)
        set_analog_value(controller_attr, 0.0)
        _send_analog_command(controller_attr, pipe, echo=echo)


"""
THIS FUNCTION IS V BAD PLS FIX LATER
"""
# TODO: make this much more readable between files this code is so shit at this
# point [ A, B, X, R, MAIN_DIRECTION, MAIN_DISTANCE, C_DIRECTION, C_DISTANCE ]
# controller actions will come in as floats from 0,1
def do_controller_actions(
    controller: Controller, actions: np.array, pipe: int, echo=False
):
    if len(np.array != 8):
        return
    # decide will generate a one if the random number(between 0 and 1) generated
    # is greater than the value passed in
    decide = lambda x: 1 if x > random.uniform(0, 1) else 1
    # actions A,B,X
    controller.buttons_a.pressed = decide(np.array[ACTION_A])
    _update_dolphin_button(controller.buttons_a, echo=echo)
    controller.buttons_b.pressed = decide(np.array[ACTION_B])
    _update_dolphin_button(controller.buttons_a, echo=echo)
    controller.buttons_x.pressed = decide(np.array[ACTION_X])
    _update_dolphin_button(controller.buttons_a, echo=echo)
    # analog R shoulder
    set_analog_value(controller.analog_r, np.array[ACTION_ANALOG_R])
    _send_analog_command(controller.analog_r, pipe, echo=echo)
    # sticks MAIN and C
    move_stick(
        controller.stick_main,
        pipe,
        np.array[ACTION_STICK_MAIN_DIRECTION] * 360,
        np.array[ACTION_STICK_MAIN_DISTANCE],
        echo=echo,
    )
    move_stick(
        controller.stick_main,
        pipe,
        np.array[ACTION_STICK_C_DIRECTION] * 360,
        np.array[ACTION_STICK_C_DISTANCE],
        echo=echo,
    )


def main():
    # TODO: take in custom configuration of a controller could affect dolphin
    # controller reset function
    # open or create pipe if none exists
    dolphin_pipe = dolphin_input_pipe()

    controller = Controller()
    print(type(controller))
    # print("sending keys get ready...")
    # countdown = 3
    # for i in range(countdown):
    #     print(countdown - i)
    #     time.sleep(1)

    _reset_controller(controller, dolphin_pipe, echo=True)
    callibrate_controller(controller, dolphin_pipe, 1.5, echo=True)
    # close the pipe pointer
    os.close(dolphin_pipe)


# dolphin_input_pipe returns a file descriptor for the dolphin pipe
def dolphin_input_pipe() -> int:
    # paths to the controller configuration and the dolphin pipe
    flatbot_pipe_path = DOLPHIN_DIR + PIPE_PATH
    controller_config_path = DOLPHIN_DIR + CONTROLLER_PATH

    # open or create pipe if none exists
    if not os.path.exists(flatbot_pipe_path):
        os.mkfifo(flatbot_pipe_path)
    dolphin_pipe = os.open(flatbot_pipe_path, os.O_WRONLY | os.O_NONBLOCK)
    return dolphin_pipe


# push_button and depress a button after a certain time.  The button passed to
# this function is passed by reference and therefor the state of the button is
# modified
def push_button(button: Button, duration: float, pipe: int, echo=False):
    _send_button_command(BUTTON_PRESS, button, pipe, echo=echo)
    button.pressed = 1
    time.sleep(duration)
    _send_button_command(BUTTON_RELEASE, button, pipe, echo=echo)
    button.pressed = 0


def press_button(button: Button, pipe: int, echo=False):
    _send_button_command(BUTTON_PRESS, button, pipe, echo=echo)
    button.pressed = 1


def release_button(button: Button, pipe: int, echo=False):
    _send_button_command(BUTTON_RELEASE, button, pipe, echo=echo)
    button.pressed = 0


# _update_dolphin_button will take the current button state and determine what
# action to take either press or release the dolphin controller
def _update_dolphin_button(button: Button, pipe: int, echo=False):
    if button.pressed:
        _send_button_command(BUTTON_PRESS, button, pipe, echo=echo)
        return
    _send_button_command(BUTTON_RELEASE, button, pipe, echo=echo)


# _send_button_command will send the desired button "PRESS/RELEASE BUTTON ?" to
# the specified pipe and will echo the output if echo is set to true
def _send_button_command(cmd: str, button: Button, pipe: int, echo=False):
    cmd_bytestr = bytes("%s %s\n" % (cmd, button.name), encoding="utf-8")
    if echo:
        os.write(1, cmd_bytestr)
    os.write(pipe, cmd_bytestr)


# _set_stick_xy will update the value of the stick to the new x and y locations
# TODO eventually program stick physics
def _set_stick_xy(stick: Stick, x: float, y: float):
    # check proper values of x and y
    err = False
    if abs(x) > 1:
        err = True
        os.write(2, b"x not between [-1.0, 1.0]: %.3f\n" % x)
    if abs(y) > 1:
        err = True
        os.write(2, b"y not between [-1.0, 1.0]: %.3f\n" % y)
    if err:
        return

    stick.x = x
    stick.y = y


# move_stick takes in a stick to move, a direction with the angle 0-360, the
# distance in units of the stick and the speed to move at in units per frame
#
# if the distance exceeds the bounds of the stick it will be truncated found
# that the human speed is: 5 frame of a video therefore 0.0833 seconds to reach
# the radius of the control stick.  Since this input is fixed to 1/60th of a
# second to account for each frame melee is eating inputs.  the max distance
# step can only be 0.043 the STICK_ITERATION_LENGTH units per frame since the
# radius of the control stick is .5 long
def move_stick(stick: Stick, pipe: int, direction: float, distance: float, echo=False):
    if direction < 0 or 360 < direction:
        os.write(2, b"direction must be between [0.0, 360.0): %f" % direction)
        return
    new_x = stick.x + distance * math.cos(math.pi * direction / 180)
    new_y = stick.y + distance * math.sin(math.pi * direction / 180)
    # truncate the new x and y locations at the edges of the controller
    new_x = max(0.0, min(1.0, new_x))
    new_y = max(0.0, min(1.0, new_y))
    # recalculate the distance and change in x and y
    dx = new_x - stick.x
    dy = new_y - stick.y
    distance = (dx ** 2 + dy ** 2) ** 0.5
    # avoid unecessary calucation
    if distance < STICK_ITERATION_LENGTH:
        _set_stick_xy(stick, new_x, new_y)
        _send_stick_command(stick, pipe)
        return
    # iteratively move controller and send stick movements
    steps = int(distance / STICK_ITERATION_LENGTH)
    for i in range(1, steps + 1):
        time.sleep(1 / 60)
        _set_stick_xy(
            stick, (new_x - dx) + dx * i / steps, (new_y - dy) + dy * i / steps
        )
        _send_stick_command(stick, pipe, echo=echo)
    _set_stick_xy(stick, new_x, new_y)


# _release_stick is just an alias for setting the a given stick back to a neutral
# position
def _release_stick(stick: Stick, pipe: int, echo=False):
    distance = ((STICK_NEUTRAL - stick.x) ** 2 + (STICK_NEUTRAL - stick.y) ** 2) ** 0.5
    direction = -1.0
    if abs(stick.x - STICK_NEUTRAL) < STICK_ITERATION_LENGTH:
        if stick.y < STICK_NEUTRAL:
            direction = CARDINAL_DIRECTIONS["up"]
        else:
            direction = CARDINAL_DIRECTIONS["down"]
    elif abs(stick.y - STICK_NEUTRAL) < STICK_ITERATION_LENGTH:
        if stick.x < STICK_NEUTRAL:
            direction = CARDINAL_DIRECTIONS["right"]
        else:
            direction = CARDINAL_DIRECTIONS["left"]
    else:
        direction = math.acos(stick.x / distance)
        direction = (direction + 180) % 360
    if echo:
        print("direction on release: %.3f distance: %.3f" % (direction, distance))
    move_stick(stick, pipe, direction, distance, echo=echo)
    _set_stick_xy(stick, STICK_NEUTRAL, STICK_NEUTRAL)


# _send_stick_command will send the command "SET stick_name X Y" to the specified
# pipe and will echo the command if echo is set to true
def _send_stick_command(stick: Stick, pipe: int, echo=False):
    # create the command to set the stick to
    cmd_bytestr = bytes(
        "SET %s %f %f\n" % (stick.name, stick.x, stick.y), encoding="utf-8"
    )
    if echo:
        os.write(1, cmd_bytestr)
    os.write(pipe, cmd_bytestr)


# set_analog_value modifies the value of an analog trigger
def set_analog_value(analog: Analog, value: float):
    if value < 0 or 1 < value:
        os.write(2, b"analog not between [0.0, 1.0]: %d" % value)
        return
    analog.value = value


# _send_analog_command will send the analog value to the dolphin controller
def _send_analog_command(analog: Analog, pipe: int, echo=False):
    cmd_bytestr = bytes(
        "SET %s %f\n" % (analog.name, analog.value * 100), encoding="utf-8"
    )
    if echo:
        os.write(1, cmd_bytestr)
    os.write(pipe, cmd_bytestr)


if __name__ == "__main__":
    main()
