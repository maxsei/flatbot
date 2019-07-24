import configparser
import re


SSBM_CONFIG_FILENAME = "ssbm-memory-config.ini"

ssbm_cfg = configparser.ConfigParser()
ssbm_cfg.read(SSBM_CONFIG_FILENAME)
sections = ssbm_cfg.sections()

def _get_hooks(section):
    return list(map(lambda x: x[1], ssbm_cfg.items(section)))


def global_frame_counter_hooks():
    return _get_hooks("global_frame_counter")


def per_character_action_state_hooks():
    return _get_hooks("per_character_action_state")


def game_duration_pause_toggle_hooks():
    return _get_hooks("game_duration_pause_toggle")


def internal_character_id_hooks():
    return _get_hooks("internal_character_id")


def players_hooks():
    player_blocks = ssbm_cfg.items("player_blocks")
    offset_attributes = ssbm_cfg.items("player_offset_attributes")
    players = {}
    for i in range(len(player_blocks)):
        _, p_block_addr = player_blocks[i]
        player = {"block": p_block_addr}
        # add player attributes
        for attribute, offset in offset_attributes:
            player[attribute] = "%x" % (
                int(p_block_addr, base=16) + int(offset, base=16)
            )

        players["p%d" % (i + 1)] = player

    return players


def cursor_positions_hooks():
    return _get_hooks("cursor_positions")


ph = players_hooks()
import json

print(json.dumps(ph, indent=4))
