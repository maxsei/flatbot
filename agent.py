#!/usr/bin/python3
import datetime as dt
import pandas as pd
import os

import controller
import memconf
import memwatcher
import numpy as np


def main():
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

    # create a dictionary of the default value found in the game
    current_state = dict(map(lambda x: (x, label_index[x]["value"]), label_index))
    # set up controller
    agent_controller = controller.Controller()
    controller_state = controller.controller_state(agent_controller)
    # current_state.update(controller_state)

    # instantial dataframe with current state
    game_state = pd.DataFrame(columns=list(current_state.keys()))
    done = False

    # Q learnin'
    q_table = np.zeros((len(game_state), len(controller_state)))
    # episodes =
    learning_rate = 0.1
    discount_factor = 0.95
    mutation_chance = 0.5
    while not done:
        update = False
        try:
            data = memwatcher.get_dolphin_data(address_index, label_index, socket_fd)
            for addr in data:
                hex_value = data[addr]
                # update the current values and the data frame if a new frame passes
                current_state[address_index[addr]["label"]] = hex_value
                if address_index[addr]["label"] == "match.frame_count":
                    update = True
        except KeyboardInterrupt:
            break

        # do q learning stuff here
        if update:
            # state = np.array([current_state.values()])
            # print(state)
            # action = np.argmax(q_table[state, :] + np.randn(1, len(controller_state)))
            # print(action)
            # add to game history
            game_state.loc[len(game_state)] = list(current_state.values())

    os.close(dolphin_pipe)
    socket_fd.close()
    try:
        os.mkdir("dumps")
    except:
        pass
    print("saving csv as dumps/%s.csv" % dt.datetime.now())
    game_state.to_csv("dumps/%s.csv" % dt.datetime.now())


# Q will take in the current q table, the environment state, and the action
# state to update the q table
# def Q(q_table:np.array, environment: pd.df, action: np.array)->np.array:
#     current_state = np.array(environment.iloc[-1,:])
#     prev_state = np.array(environment.iloc[-2,:])
#     max_future_q = np.max(q_table[])
#     # update q table with action
#     current_q = q_table[discrete_state + (action,)]
#     # q formula
#     new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (
#     reward + DISCOUNT * max_future_q
#     )
#     return new_q


def bellman():
    pass


if __name__ == "__main__":
    main()
