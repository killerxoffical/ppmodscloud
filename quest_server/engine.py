"""
Google Play Games Achievement Engine
Interacts directly with Google Play Games Services REST API (v1)
"""

import requests
from config import GAMES_API_BASE, USER_AGENT

def get_headers(access_token: str) -> dict:
    """Standard authenticated headers for GPGS API"""
    return {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

def get_player_profile(access_token: str) -> dict:
    """
    Fetch authenticated player profile.
    Verifies that the OAuth token is valid and Google Play Games profile exists.
    """
    url = f"{GAMES_API_BASE}/players/me"
    try:
        res = requests.get(url, headers=get_headers(access_token), timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "player_id": data.get("playerId"),
                "display_name": data.get("displayName"),
                "avatar_url": data.get("avatarImageUrl"),
                "experience": data.get("experienceInfo", {}),
                "raw": data
            }
        else:
            return {
                "ok": False,
                "status_code": res.status_code,
                "error": res.text
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_application_info(access_token: str, app_id: str) -> dict:
    """
    Get Game metadata (Title, Developer, Category, Icon) by Google Play Games App ID
    """
    url = f"{GAMES_API_BASE}/applications/{app_id.strip()}"
    try:
        res = requests.get(url, headers=get_headers(access_token), timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "name": data.get("name", "Unknown Game"),
                "category": data.get("category", {}).get("primary", ""),
                "description": data.get("description", ""),
                "raw": data
            }
        return {"ok": False, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_player_achievements(access_token: str) -> dict:
    """
    List progress of all achievements for the player.
    """
    url = f"{GAMES_API_BASE}/players/me/achievements"
    try:
        res = requests.get(url, headers=get_headers(access_token), timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "items": data.get("items", []),
                "raw": data
            }
        else:
            return {"ok": False, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def list_achievement_definitions(access_token: str) -> dict:
    """
    List achievement definitions (Names, Descriptions, Points/XP, Icons)
    """
    url = f"{GAMES_API_BASE}/achievements"
    try:
        res = requests.get(url, headers=get_headers(access_token), timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "items": data.get("items", []),
                "raw": data
            }
        return {"ok": False, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def reveal_achievement(access_token: str, achievement_id: str) -> dict:
    """
    Reveal a hidden achievement in Google Play Games.
    POST https://games.googleapis.com/games/v1/achievements/{achievementId}/reveal
    """
    clean_id = achievement_id.strip()
    url = f"{GAMES_API_BASE}/achievements/{clean_id}/reveal"
    try:
        res = requests.post(url, headers=get_headers(access_token), json={}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "achievement_id": clean_id,
                "current_state": data.get("currentState"),
                "raw": data
            }
        return {"ok": False, "achievement_id": clean_id, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        return {"ok": False, "achievement_id": clean_id, "error": str(e)}

def unlock_achievement(access_token: str, achievement_id: str) -> dict:
    """
    Unlock a single achievement in Google Play Games.
    POST https://games.googleapis.com/games/v1/achievements/{achievementId}/unlock
    """
    clean_id = achievement_id.strip()
    url = f"{GAMES_API_BASE}/achievements/{clean_id}/unlock"
    
    try:
        res = requests.post(url, headers=get_headers(access_token), json={}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "achievement_id": clean_id,
                "newly_unlocked": data.get("newlyUnlocked", False),
                "raw": data
            }
        else:
            return {
                "ok": False,
                "achievement_id": clean_id,
                "status_code": res.status_code,
                "error": res.text
            }
    except Exception as e:
        return {"ok": False, "achievement_id": clean_id, "error": str(e)}

def set_achievement_steps(access_token: str, achievement_id: str, steps: int) -> dict:
    """
    For incremental achievements: set minimum steps.
    POST https://games.googleapis.com/games/v1/achievements/{achievementId}/setStepsAtLeast?steps={steps}
    """
    clean_id = achievement_id.strip()
    url = f"{GAMES_API_BASE}/achievements/{clean_id}/setStepsAtLeast"
    params = {"steps": steps}
    
    try:
        res = requests.post(url, headers=get_headers(access_token), params=params, json={}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "achievement_id": clean_id,
                "current_steps": data.get("currentSteps"),
                "newly_unlocked": data.get("newlyUnlocked", False),
                "raw": data
            }
        else:
            return {
                "ok": False,
                "achievement_id": clean_id,
                "status_code": res.status_code,
                "error": res.text
            }
    except Exception as e:
        return {"ok": False, "achievement_id": clean_id, "error": str(e)}

def increment_achievement(access_token: str, achievement_id: str, steps: int = 1) -> dict:
    """
    Increment steps for an incremental achievement in Google Play Games.
    POST https://games.googleapis.com/games/v1/achievements/{achievementId}/increment?stepsToIncrement={steps}
    """
    clean_id = achievement_id.strip()
    url = f"{GAMES_API_BASE}/achievements/{clean_id}/increment"
    params = {"stepsToIncrement": int(steps)}

    try:
        res = requests.post(url, headers=get_headers(access_token), params=params, json={}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "ok": True,
                "achievement_id": clean_id,
                "current_steps": data.get("currentSteps"),
                "newly_unlocked": data.get("newlyUnlocked", False),
                "raw": data
            }
        else:
            return {
                "ok": False,
                "achievement_id": clean_id,
                "status_code": res.status_code,
                "error": res.text
            }
    except Exception as e:
        return {"ok": False, "achievement_id": clean_id, "error": str(e)}

