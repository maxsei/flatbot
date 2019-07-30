import numpy as np
import toml

"""
The responsibilities of this python script are to take the ssbm memory
configuration and parse it.  Then hard memory address are calculated from the
the offsets in the config for blocked memory addresses.
"""

SSBM_CONFIG_FILENAME = "ssbm-memory-config.toml"


# offset_addr takes in an address and an offset to compute the offset address
def _offset_addr(addr: str, offset: str):
    return "%x" % (int(addr, base=16) + int(offset, base=16))


# _get_offsets will recursively get the offsets of a a peice of data in the config
# by doing "pointer arithmetic" unitil it reaches data without any further
# pointers
def _get_offsets(block_sect: dict, addr: str, offsets: dict, common_cat: str):
    result = {}
    addr_label = block_sect[addr]
    # get all pointers from dictionary and get its offsets
    new_offsets = {}
    for offset in offsets[common_cat]:
        # if offsets is of type pointer get its offsets
        if type(offsets[common_cat][offset]) == str:
            offset_offsets = _get_offsets(
                offsets[common_cat], offset, offsets, offsets[common_cat][offset]
            )
            new_offsets.update(offset_offsets)
            continue
        new_offsets[offset] = offsets[common_cat][offset].copy()
    for offset in new_offsets:
        if type(new_offsets[offset]) == str:
            continue
        new_addr = _offset_addr(addr, offset)
        result[new_addr] = new_offsets[offset].copy()
        result[new_addr]["label"] = addr_label + "." + new_offsets[offset]["label"]
    return result


# load_config loads the toml configuation file and calculates all offset
# addresses.  It returns address and label indexes dictionaries of all data
def load_config(path: str) -> (dict, dict):
    # load config
    config = _open_config(path)
    # split up config into differenent dictionaries
    structure = config["structure"]
    addresses = config["addresses"]
    blocks = config["blocks"]
    offsets = config["offsets"]

    # compute offset data for each block data value
    for cat in blocks:
        for addr in blocks[cat]:
            offset_addresses = _get_offsets(blocks[cat], addr, offsets, cat)
            addresses.update(offset_addresses)
    # swap memory addresses and labels to allow data indexing both ways
    labels = {}
    for addr in addresses:
        # same thing as in addresses except labels and addresses are swapped
        addr_dict = {}
        for info in addresses[addr]:
            if info == "label":
                addr_dict["address"] = addr
                continue
            addr_dict[info] = addresses[addr][info]
        labels[addresses[addr]["label"]] = addr_dict

    return addresses, labels


# q_table_index will return a dictionary of the changing states of the game as
# well as the
def q_table_index(path: str) -> (dict, dict):
    # load config, q types, and the memory address data
    config = _open_config(path)
    return config["q_types"], config["rewards"]


def _open_config(path: str) -> dict:
    # load config
    config = None
    with open(path, "r") as f:
        config = toml.loads(f.read())
    return config


def test():
    addresses, labels = load_config(SSBM_CONFIG_FILENAME)
    import json

    print(json.dumps(addresses, indent=4))
    print(json.dumps(labels, indent=4))


if __name__ == "__main__":
    test()
