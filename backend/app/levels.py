"""Level system.

XP thresholds are quadratic: to reach level L you need 100 * (L-1)^2 XP.
level_for_xp(0) -> 1, level_for_xp(100) -> 2, level_for_xp(400) -> 3 ...
"""
import math

LEVEL_TITLES = [
    "Lurker", "Newbie", "Poster", "Regular", "Influencer",
    "Celebrity", "Mogul", "Tycoon", "Oligarch", "Legend",
]


def level_for_xp(xp: int) -> int:
    return int(math.sqrt(max(xp, 0) / 100)) + 1


def xp_for_level(level: int) -> int:
    return ((max(level, 1) - 1) ** 2) * 100


def level_title(level: int) -> str:
    if level <= len(LEVEL_TITLES):
        return LEVEL_TITLES[level - 1]
    return f"{LEVEL_TITLES[-1]} +{level - len(LEVEL_TITLES)}"


def level_progress(user) -> dict:
    level = level_for_xp(user.xp)
    current_floor = xp_for_level(level)
    next_floor = xp_for_level(level + 1)
    span = max(next_floor - current_floor, 1)
    into = max(user.xp - current_floor, 0)
    return {
        "level": level,
        "title": level_title(level),
        "xp": user.xp,
        "xp_into_level": into,
        "xp_for_next_level": next_floor,
        "xp_needed": max(next_floor - user.xp, 0),
        "progress": round(min(into / span, 1.0), 4),
    }
