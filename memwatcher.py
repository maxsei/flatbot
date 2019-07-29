#!/usr/bin/python3
import binascii
import datetime as dt
import pandas as pd
import numpy as np
import os
import socket
import sys
import typing
from struct import unpack

import memconf


MEMORY_LOCATIONS_NAME = "Locations.txt"
MEMORY_SOCKET_NAME = "MemoryWatcher"
MEMWATCH_DIR = "/home/maximillian/.local/share/dolphin-emu/MemoryWatcher/"

# TODO: debug remove in production
DEBUG_LABELS = {
    # "global_frame_counter",
    # "p1.x",
    "p1.y",
    # "p1.direction",
    # "p1.percentage",
    # "p2.x",
    # "p2.y",
    # "p2.direction",
    # "p2.percentage",
    # "match.",
    # "match.player_last_died",
    # "match.finished",
    # "match.frame_count",
    # "match.seconds_left",
    # "stage.blastzone_left",
    # "stage.blastzone_right",
    # "stage.blastzone_top",
    # "stage.blastzone_bottom",
}


def main():
    # set up socket path and memory locations path
    socket_path = MEMWATCH_DIR + MEMORY_SOCKET_NAME
    mem_locations_path = MEMWATCH_DIR + MEMORY_LOCATIONS_NAME
    # load the configuation of addresses to watch
    address_index, label_index = memconf.load_config(memconf.SSBM_CONFIG_FILENAME)

    # open the memory locations file to be overwritten by the addresses in the
    # memory configuration file ssbm-memory-config.toml
    memory_locations_fd = os.open(
        mem_locations_path, os.O_TRUNC | os.O_APPEND | os.O_WRONLY | os.O_CREAT
    )
    os.lseek(memory_locations_fd, 0, 0)
    for addr in sorted(list(address_index.keys()), reverse=True):
        os.write(memory_locations_fd, bytes(addr + "\n", encoding="utf-8"))
    os.close(memory_locations_fd)

    # unlink the sockets whether or not it exists or not
    try:
        os.unlink(socket_path)
        if os.path.exists(socket_path):
            pass
    except OSError:
        raise
    # create a new socket to listen on
    sock_fd = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    # bind and listen to the dolphin socket
    sock_fd.bind(socket_path)

    # create a dictionary of the default value found in the game
    current_values_dict = dict(map(lambda x: (x, label_index[x]["value"]), label_index))
    # values have to be in a list to instantiate a pandas df
    df = pd.DataFrame(columns=list(current_values_dict.keys()))
    print(df.T)

    print("listening at %s..." % socket_path)
    while True:
        try:
            # data = sock_fd.recv(1024)
            message = sock_fd.recv(1024 * 8)
            if message[0] == 0:
                continue
            data = address_data_pairs(message)
            # print(data.shape)
            for addr, hex_value in data:
                dtype = type(address_index[addr]["value"])
                if dtype == float:
                    hex_value = unpack(">f", bytes.fromhex(hex_value))[0]
                elif dtype == int:
                    hex_value = unpack(">i", bytes.fromhex(hex_value))[0]
                else:
                    pass
                # update the current values and the data frame if a new frame passes
                current_values_dict[address_index[addr]["label"]] = hex_value
                if address_index[addr]["label"] == "match.frame_count":
                    df.loc[len(df)] = list(current_values_dict.values())
                """
                DUBUG PRINTING( SEE DEBUG_LABELS )
                """
                # TODO: debug remove in production
                if address_index[addr]["label"] in DEBUG_LABELS:
                    print(addr, hex_value, address_index[addr]["label"])

        except socket.timeout:
            continue
        except KeyboardInterrupt:
            break

    sock_fd.close()
    try:
        os.mkdir("dumps")
    except:
        pass
    df.to_csv("dumps/%s.csv" % dt.datetime.now())

def update_df(data:np.array, df:pd.DataFrame):
    pass
    

# address_data_pairs will take in messages from dolphin an return a list of tuples
# that contrain (address, data) pairs.  They will be zero filled and utf-8
# decoded i.e. b'dedbeef\ndedbeef\n\00' -> [[ "0dedbeef", "0dedbeef" ]]
def address_data_pairs(msg: bytes) -> np.array:
    data = msg.strip(b"\00")
    data = data.strip(b"\n")
    data = data.split(b"\n")
    data = np.array(
        list(map(lambda x: x.zfill(8).decode("utf-8"), data)), dtype="object"
    )
    return data.reshape((data.size // 2, 2))


if __name__ == "__main__":
    main()
