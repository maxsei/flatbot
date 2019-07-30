#!/usr/bin/python3
import datetime as dt
import pandas as pd
import os
import sys

import controller
import memconf
import memwatcher
import numpy as np


def main()->int:
    # load the memory configuration
    mem_path = memconf.SSBM_CONFIG_FILENAME
    address_index, label_index = memconf.load_config(mem_path)
    q_index, reward_index = memconf.q_table_index(mem_path)
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
    controller_state = controller.controller_state(agent_controller)

    # seperate static from volitile values in the game
    static_labels, dynamic_labels = {}, {}
    for addr in address_index:
        label = address_index[addr]["label"]
        value = address_index[addr]["value"]
        try:
            if address_index[addr]["mod"] == "static":
                static_labels[label] = value
                continue
        except:
            pass
        dynamic_labels[label] = value
    # add controller state to the dynamic state
    dynamic_labels.update(controller_state)
    # instantiate current states and game states dataframe
    game_history = pd.DataFrame(columns=list(dynamic_labels.keys()))

    # Q learnin'
    q_table = np.random.random((len(dynamic_labels), len(controller_state)))

    # print(q_table)
    # return
    q_table = None  # see init below
    env_min = np.zeros(len(dynamic_labels))
    env_max = np.ones(len(dynamic_labels))
    actions = np.zeros(shape=8)
    discrete_delta = np.array([100] * len(env_max))
    discrete_state = None

    learning_rate = 0.1
    discount_factor = 0.95
    mutation_chance = 0.5

    done = False
    init_counter = 0
    while not done:
        try:
            update = False
            data = memwatcher.get_dolphin_data(address_index, label_index, socket_fd)
            for addr in data:
                hex_value = data[addr]
                # update the current values and the data frame if a new frame passes
                # current_state[address_index[addr]["label"]] = hex_value
                label = address_index[addr]["label"]
                if label == "match.frame_count" and hex_value > 0:
                    update = True
                # we haven't initalized yet so seperate static from dynamic data
                if label in dynamic_labels:
                    dynamic_labels[label] = hex_value
                else:
                    static_labels[label] = hex_value
                    init_counter += 1

            if update and not init_counter % len(static_labels) and init_counter > 0:
                game_history = game_history.drop(game_history.index)
                # create q table by adding the initialized values
                for i, q_type in enumerate(q_index):
                    q_range = q_index[q_type]
                    # if the q range is predefined use this
                    if type(q_range["min"]) != str:
                        env_min[i] = q_range["min"]
                        env_max[i] = q_range["max"]
                        continue
                    # otherwise the q_type is in a static variable
                    env_min[i] = static_labels[q_range["min"]]
                    env_max[i] = static_labels[q_range["max"]]
                discrete_state = get_discrete_state(
                    np.array([*dynamic_labels.values()]), env_min, discrete_delta
                )
                print(env_min)
                print(env_max)
                return 0

            # do q learning stuff here
            if update:
                # add to game history reveal current state to agent
                game_history.loc[len(game_history)] = list(dynamic_labels.values())


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


def get_discrete_state(state: np.array, env_low: np.array, delta: np.array) -> np.array:
    try:
        discrete_state = (state - env_low) / delta
        return tuple(discrete_state.astype(np.int))
    except:
        print(state)
        print(env_low)


def bellman():
    pass


if __name__ == "__main__":
    exit = main()
    sys.exit(exit)
