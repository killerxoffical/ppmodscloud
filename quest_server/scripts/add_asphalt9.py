import json
import os
import sys
import time
import requests
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from app import resolve_play_store_gpgs_info

def main():
    package = "com.gameloft.android.ANMP.GloftA9HM"
    print(f">>> Resolving {package} GPGS info from Google Play...")
    
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
    res = resolve_play_store_gpgs_info(package, email=email, master_token=master_token)
    if not res.get("ok"):
        print(f"[-] Error resolving info: {res.get('error')}")
        return

    client_sig = res.get("client_sig")
    achievements = res.get("achievements", [])
    total_xp = res.get("total_xp", 0)
    print(f"[+] Successfully resolved {package}!")
    print(f"    - client_sig: {client_sig}")
    print(f"    - achievements count: {len(achievements)}")
    print(f"    - total XP: {total_xp}")

    # Fetch Play Store icon and title
    icon_url = "https://play-lh.googleusercontent.com/fM3Zz_4bS5X9k0Zl7z_Q9w=s256-rw"
    title = "Asphalt Legends Unite"
    try:
        r = requests.get(f"https://play.google.com/store/apps/details?id={package}&hl=en&gl=us", headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
        if m:
            raw_icon = m.group(1)
            icon_url = raw_icon.split("=")[0] + "=s0-br30"
        tm = re.search(r'<meta property="og:title" content="([^"]+)"', r.text)
        if tm:
            raw_title = tm.group(1).split(" - ")[0].strip()
            if raw_title:
                title = raw_title
    except Exception as e:
        print(f"[-] Note on Play Store icon/title: {e}")

    print(f"    - title: {title}")
    print(f"    - icon: {icon_url}")

    game_id = "57"
    developer = "Gameloft SE"
    category = "Racing & Action"
    desc = "Take the wheel and defy your limits in Asphalt Legends Unite with official real-time GPGS cloud quest unlocking."

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
            "Gameloft Games"
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

    portal_all_quests = []
    for a in achievements:
        portal_all_quests.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "description": a.get("description") or f"Unlock {a.get('name')} in {title}",
            "experiencePoints": a.get("experiencePoints", 1500),
            "achievementType": a.get("achievementType", "STANDARD"),
            "totalSteps": a.get("totalSteps"),
            "unlockedIconUrl": a.get("unlockedIconUrl") or icon_url
        })

    # Pick top starter quests
    selected_quests = portal_all_quests[:4] if len(portal_all_quests) >= 4 else portal_all_quests
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
        "no_data": False,
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
        with open(ps_backup, "w", encoding="utf-8") as bf:
            json.dump(ps, bf, indent=2, ensure_ascii=False)
        print(f"[+] Updated portal_services_backup.json")
    except Exception as e:
        print(f"[-] Note on backup: {e}")

    # 3. Sync to Cloudflare D1
    print("[*] Syncing updated portal_services to Cloudflare D1...")
    try:
        cf_res = requests.post(
            "https://ppmod-api.tredarskvt.workers.dev/api/cloud/portal-services",
            json={"data": ps},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PPMod-Server/2.0"},
            timeout=12,
            verify=False
        )
        print(f"[+] Cloudflare D1 sync response: {cf_res.status_code}")
    except Exception as e:
        print(f"[-] Cloudflare D1 sync error: {e}")

    print(f">>> {title} ({package}) has been successfully added to both Databases and Cloudflare D1!")

if __name__ == "__main__":
    main()
