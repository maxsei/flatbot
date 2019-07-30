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
    q_index, reward_index = memconf.q_table_index(mem_path)
    q_table = np.random.random((len(dynamic_labels), len(controller_state)))
    q_table = None  # see init below
    env_min = np.zeros(len(dynamic_labels))
    env_max = np.ones(len(dynamic_labels))
    action_space = np.random.uniform(size=8)
    discrete_state = None
    discrete_size = None
    discrete_delta = np.zeros(len(dynamic_labels))

    learning_rate = 0.1
    discount_factor = 0.95
    mutation_chance = 0.5

    done = False
    while not done:
        try:
            # init counter will try and count up to the length of the static
            # labels to check and see if all of them update within a single data
            # message
            init_counter = 0
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
                # we haven't initalized yet so seperate static from dynamic data
                if label in dynamic_labels:
                    dynamic_labels[label] = hex_value
                else:
                    static_labels[label] = hex_value
                    init_counter += 1
            # check for initialization of save state
            if init_counter == len(static_labels):
                game_history = game_history.drop(game_history.index)
                # create q table by adding the initialized values
                for i, label in enumerate(dynamic_labels):
                    if label not in label_index:
                        continue
                    if "q_type" in label_index[label]:
                        q_type = label_index[label]["q_type"]
                        discrete_delta[i] = q_index[q_type]["delta"]
                        if type(q_index[q_type]["min"]) != str:
                            env_min[i] = q_index[q_type]["min"]
                            env_max[i] = q_index[q_type]["max"]
                            continue
                        env_min[i] = static_labels[q_index[q_type]["min"]]
                        env_max[i] = static_labels[q_index[q_type]["max"]]

                print("discrete_delta:", discrete_delta)
                print("env_max:", env_max)
                print("env_min:", env_min)
                # discrete_delta = (env_max - env_min) / discrete_size
                # discrete_state = get_discrete_state(
                #     np.array([*dynamic_labels.values()]), env_min, discrete_delta
                # )
                # print("discrete_state: ", discrete_state)
                # print("discrete_delta: ", discrete_delta)
            # if there is not an update we don't care about these next few things
            if not update:
                continue
            # do q learning stuff here
            # q_table = np.random.uniform(size=(discrete_size + [len(action_space)]))
            # print(q_table.size)

            # add to game history
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


# get_discrete_state given the current state, environment minimum, and the delta
# step size of your space will return the state as a discrete value in the state
# space
def get_discrete_state(state: np.array, env_min: np.array, delta: np.array) -> np.array:
    discrete_state = (state - env_min) / delta
    return tuple(discrete_state.astype(np.int))


def bellman():
    pass


if __name__ == "__main__":
    exit = main()
    sys.exit(exit)
