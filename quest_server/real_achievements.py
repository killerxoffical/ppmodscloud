"""
Real Game Achievements Database for Supported Android GPGS Games.
Maps authentic in-game achievements, descriptions, XP rewards, and live Google Play icons directly from Google Play Games REST API.
"""

import json
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "real_achievements_db.json")

REAL_GAME_ACHIEVEMENTS = {}
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for gid, g in data.items():
                pkg = g.get("package")
                if pkg and "achievements" in g:
                    REAL_GAME_ACHIEVEMENTS[pkg] = g["achievements"]
    except Exception as e:
        print(f"[-] Error loading real achievements db: {e}")

def get_real_game_achievements(package_name: str) -> list:
    """Return authentic GPGS achievements list for given package name"""
    if not package_name:
        return []
    return REAL_GAME_ACHIEVEMENTS.get(package_name.strip(), [])
