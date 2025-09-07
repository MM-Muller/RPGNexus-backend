import math

XP_BASE = 100
XP_FACTOR = 1.5


def get_xp_for_next_level(level: int) -> int:
    return math.floor(XP_BASE * (level**XP_FACTOR))
