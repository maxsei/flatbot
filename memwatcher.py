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

    # truncate and append the gamestate_hooks in the memory configuration file
    print(locations_path)
    memory_locations_fd = os.open(
        locations_path, os.O_TRUNC | os.O_APPEND | os.O_WRONLY
    )
    os.lseek(memory_locations_fd, 0, 0)

    # specify which gamestate_hooks to get out of the configuration
    gamestate_hooks = {}

    # gamestate_hooks.update(memconf.cursor_positions_gamestate_hooks())
    # gamestate_hooks.update(memconf.game_duration_pause_toggle_gamestate_hooks())

    # gamestate_hooks = update_gamestate_dict(
    #     gamestate_hooks, memconf.global_frame_counter_hooks()
    # )
    gamestate_hooks = update_gamestate_dict(gamestate_hooks, memconf.players_hooks())
    import json

    print(json.dumps(gamestate_hooks, indent=4))

    print("writing addresses")
    for addr in sorted(list(gamestate_hooks["mem_key"].keys()), reverse=True):
        print(addr)
        os.write(memory_locations_fd, bytes(addr, encoding="utf-8"))
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
    comma_char = 0x2C
    while True:
        try:
            data = sock_fd.recv(1024)
            data = data.strip(b"\00")
            data = bytes(filter(lambda x: x != comma_char, data))
            data = data.split(b"\n")
            # if data is float decode the data from a float
            data = list(map(lambda x: x.zfill(8), data))
            hexstr = data[1].decode("utf-8")
            data[1] = unpack(">f", bytes.fromhex(hexstr))
            print(data)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            sock_fd.close()
            break


def decode_float():
    pass


# update_gamestate_dict takes the each key of the source dictionary and
# stores it in the destination dictionary key: idk i'm tired
def update_gamestate_dict(a, b):
    if len(a.keys()) == 0:
        return b
    if len(b.keys()) == 0:
        return a
    for k in a:
        a[k].update(b[k])
    return a


if __name__ == "__main__":
    main()
