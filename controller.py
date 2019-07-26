from dataclasses import dataclass
from dataclasses import fields
import os
import sys
import configparser
import re
import time


SSBM_CONFIG_FILENAME = "ssbm-memory-config.ini"
DOLPHIN_DIR = "/home/maximillian/.local/share/dolphin-emu/"
PIPE_PATH = "Pipes/flatbot"
CONTROLLER_PATH = "Config/GCPadNew.ini"
DOLPHIN_PATH = "Config/Dolphin.ini"

STICK_NEUTRAL_X = 0.5
STICK_NEUTRAL_Y = 0.5

BUTTON_PRESS = "PRESS"
BUTTON_RELEASE = "RELEASE"

# TODO: make this configureable
PORT = 2

CONTROLLER_UNPLUGGED = 0
CONTROLLER_STANDARD = 6
CONTROLLER_GCN_ADAPTER = 12


@dataclass
class Button:
    pressed: bool = False
    name: str = ""


@dataclass
class Stick:
    x: float = STICK_NEUTRAL_X
    y: float = STICK_NEUTRAL_Y
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
    buttons_y: Button = Button(name="Y")
    buttons_z: Button = Button(name="Z")
    buttons_start: Button = Button(name="START")
    main_stick: Stick = Stick(name="MAIN")
    c_stick: Stick = Stick(name="C")
    d_pad_up: Button = Button(name="D_UP")
    d_pad_down: Button = Button(name="D_DOWN")
    d_pad_left: Button = Button(name="D_LEFT")
    d_pad_right: Button = Button(name="D_RIGHT")
    triggers_l: Button = Button(name="L")
    triggers_r: Button = Button(name="R")
    analog_l: Analog = Analog(name="L")
    analog_r: Analog = Analog(name="R")


def main():
    # TODO: take in custom configuration of a controller could affect dolphin
    # contoller reset function
    """
    # read in the controller configuration from dolphin
    controller_cfg = configparser.ConfigParser()
    controller_cfg.read(controller_config_path)
    controller_cfg = dict(controller_cfg.items(controller_cfg.sections()[0]))
    # format command names correctly for echoing commands properly
    commands = {}
    for k in controller_cfg:
        words = controller_cfg[k].split(" ")
        if len(words) < 2:
            continue
        commands[k] = words[1].strip("`")

    # configure controller with these commands
    controller = Controller(
        buttons_a=Button(False, commands["buttons/a"]),
        buttons_b=Button(False, commands["buttons/b"]),
        buttons_x=Button(False, commands["buttons/x"]),
        buttons_y=Button(False, commands["buttons/y"]),
        buttons_z=Button(False, commands["buttons/z"]),
        triggers_l=Button(False, commands["triggers/l"]),
        triggers_r=Button(False, commands["triggers/r"]),
        d_pad_up=Button(False, commands["d-pad/up"]),
        d_pad_down=Button(False, commands["d-pad/down"]),
        d_pad_left=Button(False, commands["d-pad/left"]),
        d_pad_right=Button(False, commands["d-pad/right"]),
        buttons_start=Button(False, commands["buttons/start"]),
        # there are multiple directions here but we can pick any directions
        main_stick=Stick(STICK_NEUTRAL_X, STICK_NEUTRAL_Y, commands["main stick/up"]),
        c_stick=Stick(STICK_NEUTRAL_X, STICK_NEUTRAL_Y, commands["c-stick/up"]),
    )
    """

    # read in the dolphin config to configure with controller
    # dolphin_config_path = DOLPHIN_DIR + DOLPHIN_PATH
    # dolphin_config = configparser.ConfigParser()
    # dolphin_config.read(dolphin_config_path)
    # # setup standard input device on port 2 (for now) with background inputs
    # # enabled i.e. window doesn't need to be in focus
    # dolphin_config.set("Core", "sidevice0" + str(PORT), "%d" % CONTROLLER_STANDARD)
    # dolphin_config.set("Input", "backgroundinput", "True")
    # with open(dolphin_config_path, "w") as f:
    #     dolphin_config.write(f)

    # os.write()

    # paths to the controller configuration and the dolphin pipe
    flatbot_pipe_path = DOLPHIN_DIR + PIPE_PATH
    controller_config_path = DOLPHIN_DIR + CONTROLLER_PATH

    # open or create pipe if none exists
    if not os.path.exists(flatbot_pipe_path):
        os.mkfifo(flatbot_pipe_path)
    dolphin_pipe = os.open(flatbot_pipe_path, os.O_WRONLY | os.O_SYNC)

    controller = Controller()
    import random

    print("sending keys get ready...")
    countdown = 3
    for i in range(countdown):
        print(countdown - i)
        time.sleep(1)
    collibrate_dolphin_controller(dolphin_pipe, 3, echo=True)
    # while True:
    #     try:
    #         time.sleep(1)
    #         push_button(controller.buttons_b, 1, dolphin_pipe, echo=True)

    #         set_stick_xy(
    #             controller.main_stick, random.uniform(-1, 1), random.uniform(-1, 1)
    #         )
    #         _send_stick_command(controller.main_stick, dolphin_pipe, echo=True)
    #     except KeyboardInterrupt:
    #         break

    reset_dolphin_controller(dolphin_pipe, echo=True)
    # close the pipe pointer
    os.close(dolphin_pipe)


# collibrate_dolphin_controller will sequentially press each button once so be
# ready in the dolphin controller configuration to listen for input.  Note if you
# already have a configuration saved doing this is not necessary
def collibrate_dolphin_controller(pipe, sleep_time, echo=False):
    blank_controller = Controller()
    # iterate over the default controller fields and send their results to dolphin
    for f in fields(blank_controller):
        controller_attr = getattr(blank_controller, f.name)
        print("sending %s" % f.name, flush=True)
        if f.type == type(Button()):
            continue
            time.sleep(sleep_time)
            _send_button_command(BUTTON_PRESS, controller_attr, pipe, echo=echo)
            time.sleep(0.05)
            _send_button_command(BUTTON_RELEASE, controller_attr, pipe, echo=echo)
            continue
        # do stick commands manually up, down, left, right
        if f.type == type(Stick()):
            for x_sign, y_sign in [(0.0, 1.0), (0.0, -1.0), (-1.0, 0.0), (1.0, 0.0)]:
                print(
                    "moving stick to x: %.3f y: %.3f"
                    % (STICK_NEUTRAL_X + x_sign, STICK_NEUTRAL_Y + y_sign)
                )
                time.sleep(sleep_time)
                for i in range(9):
                    set_stick_xy(
                        controller_attr,
                        STICK_NEUTRAL_X + x_sign * i * STICK_NEUTRAL_X / 8,
                        STICK_NEUTRAL_Y + y_sign * i * STICK_NEUTRAL_Y / 8,
                    )
                    _send_stick_command(controller_attr, pipe, echo=echo)
                    time.sleep(0.05)
                set_stick_xy(controller_attr, STICK_NEUTRAL_X, STICK_NEUTRAL_Y)
                time.sleep(0.05)
                _send_stick_command(controller_attr, pipe, echo=echo)
            continue
        continue
        set_analog_value(controller_attr, 1.0)
        time.sleep(sleep_time)
        _send_analog_command(controller_attr, pipe, echo=echo)
        set_analog_value(controller_attr, 0.0)
        time.sleep(0.05)
        _send_analog_command(controller_attr, pipe, echo=echo)


def reset_dolphin_controller(pipe, echo=False):
    blank_controller = Controller()
    # iterate over the default controller fields and send their results to dolphin
    for f in fields(blank_controller):
        controller_attr = getattr(blank_controller, f.name)
        if f.type == type(Button()):
            _send_button_command(BUTTON_RELEASE, controller_attr, pipe, echo=echo)
            continue
        if f.type == type(Analog()):
            set_analog_value(controller_attr, 0.0)
            _send_analog_command(controller_attr, pipe, echo=echo)
            continue
        set_stick_xy(controller_attr, STICK_NEUTRAL_X, STICK_NEUTRAL_Y)
        _send_stick_command(controller_attr, pipe, echo=echo)


# push_button and depress a button after a certain time.  The button passed to
# this function is passed by reference and therefor the state of the button is
# modified
def push_button(button: Button, duration: float, pipe: int, echo=False):
    _send_button_command(BUTTON_PRESS, button, pipe, echo=echo)
    button.pressed = True
    time.sleep(duration)
    _send_button_command(BUTTON_RELEASE, button, pipe, echo=echo)
    button.pressed = False


# _send_button_command will send the desired button "PRESS/RELEASE BUTTON ?" to
# the specified pipe and will echo the output if echo is set to true
def _send_button_command(cmd: str, button: Button, pipe: int, echo=False):
    cmd_bytestr = bytes("%s %s\n" % (cmd, button.name), encoding="utf-8")
    if echo:
        os.write(1, cmd_bytestr)
    os.write(pipe, cmd_bytestr)


# set_stick_xy will update the value of the stick to the new x and y locations
# TODO eventually program stick physics
def set_stick_xy(stick: Stick, x: float, y: float):
    # check proper values of x and y
    err = False
    if abs(x) > 1:
        err = True
        os.write(2, b"x not between [-1.0, 1.0]: %d" % x)
    if abs(y) > 1:
        err = True
        os.write(2, b"y not between [-1.0, 1.0]: %d" % y)
    if err:
        return
    stick.x = x
    stick.y = y


move_stick takes in a stick to move, a direction with the angle 0-360, the
def move_stick(stick: Stick, direction:)
    pass

def release_stick(stick: Stick):
    pass


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
        os.write(2, b"analog not between [0.0, 1.0]: %d" % cmd_bytestr)
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
