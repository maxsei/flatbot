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

# SIGNED_ADDRESSES = set([""])


def main():
    memwatch_path = MEMWATCH_DIR + MEMORY_SOCKET_NAME
    locations_path = MEMWATCH_DIR + MEMORY_LOCATIONS_NAME

    memory_locations_fd = os.open(
        locations_path, os.O_TRUNC | os.O_APPEND | os.O_WRONLY
    )
    os.lseek(memory_locations_fd, 0, 0)

    address_index, label_index = memconf.load_config(memconf.SSBM_CONFIG_FILENAME)

    print("writing addresses")
    for addr in sorted(list(address_index.keys()), reverse=True):
        print(addr)
        os.write(memory_locations_fd, bytes(addr + "\n", encoding="utf-8"))
    os.close(memory_locations_fd)

    # unlink the sockets whether or not it exists or not
    try:
        os.unlink(memwatch_path)
    except OSError:
        if os.path.exists(memwatch_path):
            raise

    # create a new socket to listen on
    sock_fd = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    # bind and listen to the dolphin socket
    sock_fd.bind(memwatch_path)

    # listen on the socket for data
    comma_char = 0x2C
    while True:
        try:
            data = sock_fd.recv(1024)
            data = data.strip(b"\00")
            data = bytes(filter(lambda x: x != comma_char, data))
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
                # decode hex value into string
                # hex_value = 

            print(addr, hex_value)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            sock_fd.close()
            break


def decode_float():
    pass


if __name__ == "__main__":
    main()
