#!/usr/bin/python3
import datetime as dt
import pandas as pd
import os
import sys

import controller
import memconf
import memwatcher
import numpy as np


def main() -> int:
    # load the memory configuration
    mem_path = memconf.SSBM_CONFIG_FILENAME
    address_index, label_index = memconf.load_config(mem_path)
    # set the pysical memory locations to watch
    mem_locations_path = memwatcher.MEMWATCH_DIR + memwatcher.MEMORY_LOCATIONS_NAME
    memwatcher.watch_memory_locations(
        address_index, label_index, mem_locations_path, echo=True
    )

    # set up dolpin socket
    socket_path = memwatcher.MEMWATCH_DIR + memwatcher.MEMORY_SOCKET_NAME
    socket_fd = memwatcher.get_dolphin_socket(socket_path)
    # set up dolpin pipe
    dolphin_pipe = controller.dolphin_input_pipe()
    # set up controller
    agent_controller = controller.Controller()
    # controller_state = controller.controller_state(agent_controller)
    actions = controller.ControllerActions()

    # seperate static from volitile values in the game dynamic state is a
    # convenience for adding history to the game_history data frame below
    static_labels, volitile_labels, dynamic_state = {}, {}, {}
    for addr in address_index:
        label = address_index[addr]["label"]
        value = None
        if type(address_index[addr]["value"]) == dict:
            value = address_index[addr]["value"].copy()
        else:
            value = address_index[addr]["value"]
        try:
            if address_index[addr]["mod"] == "static":
                static_labels[label] = value
                continue
            elif address_index[addr]["mod"] == "volitile":
                volitile_labels[label] = value
        except:
            pass
        dynamic_state[label] = value
    # add controller state to the dynamic state
    dynamic_state.update(controller.actions_state(actions))
    # instantiate current states and game states dataframe
    game_history = pd.DataFrame(columns=list(volitile_labels.keys()))

    discount_factor = 0.1
    time_steps_information = 180
    prediction_lag = 15

    q_index, _ = memconf.q_table_index(memconf.SSBM_CONFIG_FILENAME)
    q_table = None
    env_max = []
    env_min = []
    discrete_size = []
    discrete_delta = []
    discrete_state = None

    done = False
    reward = 0
    p2_falls = 0
    start_date = dt.datetime.now()
    init_counter = 0
    while not done:
        try:
            # init counter will try and count up to the length of the static
            # labels to check and see if all of them update within a single data
            # message
            update = False
            # get the message and check what is in it
            data = memwatcher.get_dolphin_data(address_index, label_index, socket_fd)
            for addr in data:
                hex_value = data[addr]
                # update the current values and the data frame if a new frame passes
                # current_state[address_index[addr]["label"]] = hex_value
                label = address_index[addr]["label"]
                if label == "match.frame_count" and hex_value > 0:
                    update = True
                if label == "p1.falls":
                    reward += 1
                if label == "p2.falls":
                    p2_falls += 1
                    reward = 0
                    # compute the average reward per action for each episode
                    game_history["p1.falls"] = game_history["p1.falls"] - reward
                    save_episode(start_date, p2_falls, game_history, echo=True)
                    game_history = game_history.drop(game_history.index)
                # seperate static from dynamic data
                if label in volitile_labels:
                    volitile_labels[label] = hex_value
                elif label in dynamic_state:
                    dynamic_state[label] = hex_value
                else:
                    static_labels[label] = hex_value
                    init_counter += 1
            if not update:
                continue
            if init_counter % len(static_labels) == 0 and init_counter != 0:
                init_counter = 0
                # initialize q learning parameters
                for label in label_index:
                    if not "q_type" in label_index[label]:
                        continue
                    q_info = q_index[label_index[label]["q_type"]]
                    if type(q_info["max"]) == str:
                        env_min.append(static_labels[q_info["min"]])
                        env_max.append(static_labels[q_info["max"]])
                    else:
                        env_min.append(q_info["min"])
                        env_max.append(q_info["max"])
                    discrete_delta.append(q_info["delta"])
                # initialize q learing environment
                env_min = np.array(env_min, np.int8)
                env_max = np.array(env_max, np.int8)
                discrete_delta = np.array(discrete_delta, np.int8)
                discrete_size = abs(env_max - env_min) // discrete_delta
                q_table = np.random.uniform(
                    size=(discrete_size + len(controller.actions_state(actions)))
                ).astype(np.float16)
                discrete_state = get_discrete_state(np.array())
            # create q table of discrete states
            if len(game_history) % 10 == 0:
                # TODO: make prediction of action
                # do action
                for name in controller.actions_state(actions):
                    controller._set_action(actions, name, np.random.uniform())
                controller.do_controller_actions(
                    agent_controller, actions, dolphin_pipe
                )
            # controller_state = controller.controller_state(agent_controller)
            volitile_labels.update(controller.actions_state(actions))
            game_history.loc[len(game_history)] = list(dynamic_state.values())

        except KeyboardInterrupt:
            break

    os.close(dolphin_pipe)
    socket_fd.close()
    try:
        os.mkdir("dumps")
    except:
        pass
    print("saving csv as dumps/%s.csv" % dt.datetime.now())
    game_history.to_csv("dumps/%s.csv" % dt.datetime.now())
    return 0


# get_discrete_state given the current state, environment minimum, and the delta
# step size of your space will return the state as a discrete value in the state
# space
def get_discrete_state(state: np.array, env_min: np.array, delta: np.array) -> np.array:
    discrete_state = (state - env_min) / delta
    return tuple(discrete_state.astype(np.int16))


def save_episode(date: dt.datetime, episode: int, df: pd.DataFrame, echo=False):
    datestr = str(date).replace(" ", ".")
    try:
        os.mkdir("episodes/%s" % datestr)
    except:
        pass
    path = "episodes/%s/%03d.csv" % (datestr, episode)
    if echo:
        print(path)
    df.to_csv(path)


def bellman():
    pass


if __name__ == "__main__":
    exit = main()
    sys.exit(exit)
