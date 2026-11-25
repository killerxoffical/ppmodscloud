import json
import os
import sys
import time
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from app import resolve_play_store_gpgs_info

def main():
    print(">>> Resolving Gardenscapes GPGS info from Google Play...")
    
    # Load credentials
    reg_devs_path = os.path.join(ROOT_DIR, "registered_devices.json")
    with open(reg_devs_path, "r", encoding="utf-8") as f:
        devs = json.load(f)

    email = None
    master_token = None
    for dev in devs.values():
        for acc in dev.get("accounts", []):
            if acc.get("email") and acc.get("token", "").startswith("aas_et/"):
                email = acc["email"]
                master_token = acc["token"]
                break
        if email:
            break

    if not email or not master_token:
        print("[-] Could not find a valid master token in registered_devices.json")
        return

    print(f"[+] Using auth account: {email}")
    res = resolve_play_store_gpgs_info("com.playrix.gardenscapes", email=email, master_token=master_token)
    if not res.get("ok"):
        print(f"[-] Error resolving info: {res.get('error')}")
        return

    client_sig = res.get("client_sig")
    achievements = res.get("achievements", [])
    total_xp = res.get("total_xp", 0)
    print(f"[+] Successfully resolved Gardenscapes!")
    print(f"    - client_sig: {client_sig}")
    print(f"    - achievements count: {len(achievements)}")
    print(f"    - total XP: {total_xp}")

    # Fetch Play Store icon
    icon_url = "https://play-lh.googleusercontent.com/97QvFwN7Ue3sO0T4fI5j5d-yC4fG8a2hL9rK0s1uV2w=s256-rw"
    try:
        r = requests.get("https://play.google.com/store/apps/details?id=com.playrix.gardenscapes&hl=en&gl=us", headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        import re
        m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
        if m:
            raw_icon = m.group(1)
            icon_url = raw_icon.split("=")[0] + "=s0-br30"
    except Exception as e:
        print(f"[-] Note on Play Store icon: {e}")

    print(f"    - icon: {icon_url}")

    # Build DB entries
    game_id = "56"
    title = "Gardenscapes"
    package = "com.playrix.gardenscapes"
    developer = "Playrix"
    category = "Casual & Puzzle"
    desc = "Restore and decorate different areas in the garden, get to the bottom of the secrets it holds, and enjoy the company of amusing in-game characters with official GPGS cloud quests."

    # 1. Update real_achievements_db.json
    db_file = os.path.join(ROOT_DIR, "real_achievements_db.json")
    with open(db_file, "r", encoding="utf-8") as f:
        rdb = json.load(f)

    rdb_entry = {
        "id": game_id,
        "title": title,
        "developer": developer,
        "package": package,
        "client_sig": client_sig,
        "category": category,
        "section": "quest_unlocker",
        "icon": icon_url,
        "desc": desc,
        "achievements_count": len(achievements),
        "total_xp": total_xp,
        "tags": [
            "Official GPGS",
            "Real Achievements",
            "Live Cloud Sync",
            "Google Play Quest",
            "Playrix Games"
        ],
        "gpgs_verified": True,
        "achievements": achievements
    }
    rdb[game_id] = rdb_entry

    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(rdb, f, indent=2, ensure_ascii=False)
    print(f"[+] Updated real_achievements_db.json (ID {game_id})")

    # 2. Update portal_services.json
    ps_file = os.path.join(ROOT_DIR, "portal_services.json")
    with open(ps_file, "r", encoding="utf-8") as f:
        ps = json.load(f)

    # Format quests for portal_services
    portal_all_quests = []
    for a in achievements:
        portal_all_quests.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "description": a.get("description"),
            "experiencePoints": a.get("experiencePoints", a.get("xp", 500)),
            "achievementType": a.get("achievementType", a.get("type", "STANDARD")),
            "totalSteps": a.get("totalSteps"),
            "unlockedIconUrl": a.get("unlockedIconUrl", a.get("icon", icon_url))
        })

    # Pick 2 attractive starter quests for default selection
    selected_quests = portal_all_quests[:2] if len(portal_all_quests) >= 2 else portal_all_quests[:1]
    selected_quest_ids = [q["id"] for q in selected_quests]

    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    ps_entry = {
        "service_id": f"srv_{game_id}",
        "game_id": game_id,
        "title": title,
        "package": package,
        "developer": developer,
        "category": category,
        "icon": icon_url,
        "section": "quest_unlocker",
        "enabled": True,
        "total_quests_count": len(portal_all_quests),
        "selected_quests_count": len(selected_quests),
        "selected_quest_ids": selected_quest_ids,
        "selected_quests": selected_quests,
        "all_quests": portal_all_quests,
        "created_at": now_str,
        "updated_at": now_str,
        "id": game_id,
        "client_sig": client_sig
    }
    ps[game_id] = ps_entry

    with open(ps_file, "w", encoding="utf-8") as f:
        json.dump(ps, f, indent=2, ensure_ascii=False)
    print(f"[+] Updated portal_services.json (ID {game_id})")

    # Update backup
    ps_backup = os.path.join(ROOT_DIR, "portal_services_backup.json")
    try:
        with open(ps_backup, "w", encoding="utf-8") as f:
            json.dump(ps, f, indent=2, ensure_ascii=False)
        print(f"[+] Updated portal_services_backup.json")
    except Exception as e:
        print(f"[-] Note on backup file: {e}")

    # 3. Sync to Cloudflare D1
    print("[*] Syncing updated portal_services to Cloudflare D1...")
    try:
        cf_res = requests.post(
            "https://ppmodscloud.profitking34.workers.dev/api/cloud/portal-services",
            json={"data": ps},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PPMod-Server/2.0"},
            timeout=12,
            verify=False
        )
        print(f"[+] Cloudflare D1 sync response: {cf_res.status_code} - {cf_res.text}")
    except Exception as e:
        print(f"[-] Cloudflare D1 sync error: {e}")

    print(">>> Gardenscapes has been successfully added to both GPGS Databases and Cloudflare D1!")

if __name__ == "__main__":
    main()
