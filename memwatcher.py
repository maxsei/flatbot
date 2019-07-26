#!/usr/bin/python3
import binascii
import os
import socket
import sys
from struct import unpack

import memconf


MEMORY_LOCATIONS_NAME = "Locations.txt"
MEMORY_SOCKET_NAME = "MemoryWatcher"
MEMWATCH_DIR = "/home/maximillian/.local/share/dolphin-emu/MemoryWatcher/"

# TODO: debug remove in production
debug_labels = ["match.frame_count"]


def main():
    # set up socket path and memory locations path
    socket_path = MEMWATCH_DIR + MEMORY_SOCKET_NAME
    mem_locations_path = MEMWATCH_DIR + MEMORY_LOCATIONS_NAME
    # load the configuation of addresses to watch
    address_index, label_index = memconf.load_config(memconf.SSBM_CONFIG_FILENAME)

    # open the memory locations file to be overwritten by the addresses in the
    # memory configuration file ssbm-memory-config.toml
    memory_locations_fd = os.open(
        mem_locations_path, os.O_TRUNC | os.O_APPEND | os.O_WRONLY
    )
    os.lseek(memory_locations_fd, 0, 0)
    for addr in sorted(list(address_index.keys()), reverse=True):
        os.write(memory_locations_fd, bytes(addr + "\n", encoding="utf-8"))
    os.close(memory_locations_fd)

    # unlink the sockets whether or not it exists or not
    try:
        os.unlink(socket_path)
    except OSError:
        if os.path.exists(socket_path):
            raise
    # create a new socket to listen on
    sock_fd = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    # bind and listen to the dolphin socket
    sock_fd.bind(socket_path)

    # comma char is used to filter out comma char read in through the socket
    COMMA_CHAR = 0x2C
    print("listening at %s..." % socket_path)
    while True:
        try:
            data = sock_fd.recv(1024)
            data = data.strip(b"\00")
            data = bytes(filter(lambda x: x != COMMA_CHAR, data))
            data = data.split(b"\n")
            data = list(map(lambda x: x.zfill(8), data))
            data = list(map(lambda x: x.decode("utf-8"), data))
            addr, hex_value = data[0], data[1]
            # detect type and decode accordingly
            dtype = type(address_index[addr]["value"])
            if dtype == float:
                hex_value = unpack(">f", bytes.fromhex(hex_value))[0]
            elif dtype == int:
                hex_value = unpack(">i", bytes.fromhex(hex_value))[0]
            else:
                pass

            # TODO: debug remove in production
            if address_index[addr]["label"] in debug_labels:
                print(addr, hex_value, address_index[addr]["label"])
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            sock_fd.close()
            break


def decode_float():
    pass


if __name__ == "__main__":
    main()
