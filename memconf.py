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
            for offset in offsets[cat]:
                new_addr = _offset_addr(addr, offset)
                addresses[new_addr] = offsets[cat][offset].copy()
                addresses[new_addr]["label"] = (
                    blocks[cat][addr] + "." + offsets[cat][offset]["label"]
                )

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
