#!/usr/bin/python3
import binascii
import os
import socket
import sys

import memconf

MEMORY_LOCATIONS_NAME = "Locations.txt"
MEMORY_SOCKET_NAME = "MemoryWatcher"
MEMWATCH_DIR = "/home/maximillian/.local/share/dolphin-emu/MemoryWatcher/"


def main():
    memwatch_path = MEMWATCH_DIR + MEMORY_SOCKET_NAME
    locations_path = MEMWATCH_DIR + MEMORY_LOCATIONS_NAME

    # truncate and append the hooks in the memory configuration file
    print(locations_path)
    memory_locations_fd = os.open(
        locations_path, os.O_TRUNC | os.O_APPEND | os.O_WRONLY
    )
    os.lseek(memory_locations_fd, 0, 0)

    # specify which hooks to get out of the configuration
    hooks = []
    # hooks.append(memconf.cursor_positions_hooks())
    # hooks.append(*memconf.game_duration_pause_toggle_hooks())
    hooks.append(*memconf.global_frame_counter_hooks())
    p1 = memconf.players_hooks()["p1"]
    hooks.append(p1["x"])
    hooks.append(p1["y"])
    # hooks.append(p1["z"])
    # hooks.append(p1["delta_x"])
    # hooks.append(p1["delta_y"])
    # hooks.append(p1["delta_z"])

    for hook in hooks:
        os.write(memory_locations_fd, bytes(hook, encoding="utf-8"))
        os.write(memory_locations_fd, bytes("\n", encoding="utf-8"))
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
    while True:
        try:
            data = sock_fd.recv(1024).decode("utf-8").splitlines()
            data[1] = data[1].strip("\x00")
            data[1] = data[1].split(",")
            data[1] = list(map(lambda x: x.zfill(8), data[1]))
            data[1] = list(map(lambda x: int(x, base=16), data[1]))
            # data[1] = list(map(lambda x: binascii.unhexlify(x), data[1]))
            print(data)
            # data[1] = data[1].strip('\x00').zfill(8).split(",")
            # print(data)
            # for d in data[1]:
            #     print(d,end="\t")
            #     print(binascii.unhexlify(d))
            # print(data)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            sock_fd.close()
            break


if __name__ == "__main__":
    main()
