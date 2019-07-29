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


import time


def __get_offsets(blocks: dict, addr: str, offsets: dict, cat: str):
    result = {}
    cat_trace = cat.split(".")
    if type(cat_trace) == list:
        cat = cat_trace[-1]

    new_offsets = {}
    for offset in offsets[cat]:
        # pointers are only stored in the config as strings
        if type(offsets[cat][offset]) == str:
            sub = _get_offsets(
                offsets.copy(),
                offset,
                offsets.copy(),
                ".".join(cat_trace) + "." + offsets[cat][offset],
            )
            new_offsets.update(sub)
            continue
        new_offsets[offset] = offsets[cat][offset]

    for offset in new_offsets:
        if type(new_offsets[offset]) == str:
            continue
        new_addr = _offset_addr(addr, offset)
        result[new_addr] = new_offsets[offset].copy()
        print(list(map(lambda x: offsets[x], cat_trace)))
        print(offsets)
        print(cat_trace)
        result[new_addr]["label"] = (
            ".".join(list(map(lambda x: offsets[x]["label"], cat_trace)))
            + "."
            + new_offsets[offset]["label"]
        )
    return result


def _get_offsets(block_sect: dict, addr: str, offsets: dict, common_cat: str):
    result = {}
    addr_label = block_sect[addr]
    # get all pointers from dictionary and get its offsets
    new_offsets = {}
    for offset in offsets[common_cat]:
        # if offsets is of type pointer get its offsets
        if type(offsets[common_cat][offset]) == str:
            offset_offsets = _get_offsets(offsets[common_cat], offset, offsets, offsets[common_cat][offset])
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
# addresses.
def load_config(path: str):
    # load config
    config = None
    with open(path, "r") as f:
        config = toml.loads(f.read())
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


def test():
    addresses, labels = load_config(SSBM_CONFIG_FILENAME)
    import json

    print(json.dumps(addresses, indent=4))
    print(json.dumps(labels, indent=4))


if __name__ == "__main__":
    test()
