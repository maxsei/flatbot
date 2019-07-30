import numpy as np
import os
import socket
import typing
from struct import unpack

import memconf


MEMORY_LOCATIONS_NAME = "Locations.txt"
MEMORY_SOCKET_NAME = "MemoryWatcher"
MEMWATCH_DIR = "/home/maximillian/.local/share/dolphin-emu/MemoryWatcher/"

# TODO: debug remove in production
DEBUG_LABELS = {
    # "stage.blastzone_bottom", # check
    # "stage.blastzone_top", # check
    # "stage.blastzone_right", # check
    # "stage.blastzone_left", # check
    "match.frame_count",  # check
    # "match.finished", # check
    # "p2.entity.sheild_size",
    # "p2.body_state", # bust
    # "p1.entity.sheild_size",
    # "p1.body_state", # bust
    # "p2.falls",
    # "p2.percentage", # check
    # "p2.y", # check
    # "p2.x",  # check
    # "p1.falls", # check
    # "p1.percentage", # check
    # "p1.facing_direction", # bust
    # "p1.y", # check
    # "p1.x", # check
    # "p1.entity.body_state",
}


def watch_memory_locations(adr_idx: dict, lbl_idx: dict, mem_path: str, echo=False):
    # open memory locations file in append mode and truncate
    memory_locations_fd = os.open(
        mem_path, os.O_TRUNC | os.O_APPEND | os.O_WRONLY | os.O_CREAT
    )
    os.lseek(memory_locations_fd, 0, 0)
    # append all memory location to watch
    if echo:
        print("=====WATCHING=====")
    for addr in sorted(list(adr_idx.keys()), reverse=True):
        if echo:
            print(addr, adr_idx[addr]["label"])
        os.write(memory_locations_fd, bytes(addr + "\n", encoding="utf-8"))
    os.close(memory_locations_fd)
    # display debugging labels
    if echo:
        print("=====SHOWING=====")
        for label in DEBUG_LABELS:
            print(lbl_idx[label]["address"], label)


def get_dolphin_socket(socket_path) -> int:
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
    return sock_fd


def get_dolphin_data(adr_idx: dict, lbl_idx: dict, sock: int, echo=False) -> dict:
    result = {}
    if echo:
        print("listening at %s..." % socket_path)
    try:
        message = sock.recv(1024)
        if message[0] == 0:
            return result
        data = address_data_pairs(message)
        for i in range(len(data)):
            addr, hex_value = data[i]
            # find the datatype of the address
            dtype = None
            try:
                dtype = adr_idx[addr]["type"]
            except:
                print("address %s not in index" % addr, file=2)
                continue
            result[addr] = decode_hex_value(hex_value, dtype)
            """
            DUBUG PRINTING( SEE DEBUG_LABELS )
            """
            # TODO: debug remove in production
            if adr_idx[addr]["label"] in DEBUG_LABELS:
                print(addr, result[addr], adr_idx[addr]["label"], adr_idx[addr]["type"])
        return result
    except socket.timeout:
        return result


# address_data_pairs will take in messages from dolphin an return a list of tuples
# that contrain (address, data) pairs.  They will be zero filled and utf-8
# decoded i.e. b'dedbeef\ndedbeef\n\00' -> [[ "0dedbeef", "0dedbeef" ]]
def address_data_pairs(msg: bytes) -> np.array:
    data = msg.strip(b"\00")
    data = data.strip(b"\n")
    data = data.decode("utf-8")
    data = np.array(data.split("\n"))
    return data.reshape((data.size // 2, 2))


def decode_hex_value(hex_value: str, dtype: str):
    # properly convert data type
    if dtype == "float":
        hex_value = unpack(">f", bytes.fromhex(hex_value.zfill(8)))[0]
    elif dtype == "int":
        hex_value = unpack(">i", bytes.fromhex(hex_value.zfill(8)))[0]
    elif dtype == "short":
        hex_value = unpack(">i", bytes.fromhex(hex_value[:-4].zfill(8)))[0]
    else:
        pass
    return hex_value
