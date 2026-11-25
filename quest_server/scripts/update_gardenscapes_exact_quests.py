import json
import os
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ps_path = os.path.join(ROOT_DIR, "portal_services.json")
ps_backup = os.path.join(ROOT_DIR, "portal_services_backup.json")

with open(ps_path, "r", encoding="utf-8") as f:
    ps = json.load(f)

# The 4 exact Google Play Points Quests for Gardenscapes from user's Play Store screen
icon_url = "https://play-lh.googleusercontent.com/C5Yp55qwwU8zJAkfO9DQTtHauJcmQgMM59HH8odxPM6KlHiqO6WY9jZsWnIN1k3pfgwo2o3e3ygiizwHSIPbY-w=s0-br30"

exact_quests = [
    {
        "id": "CgkIzvLA59wVEAIQbg",
        "name": "Sign into Gardenscapes with your Play Games profile",
        "description": "You must be signed into Play Games in order to collect achievements",
        "experiencePoints": 500,
        "achievementType": "STANDARD",
        "totalSteps": None,
        "unlockedIconUrl": icon_url
    },
    {
        "id": "CgkIzvLA59wVEAIQWg",
        "name": "Match 99 Apple Pieces",
        "description": "Clear 99 red Apple pieces across match-3 levels in Gardenscapes (0/99 apples)",
        "experiencePoints": 1000,
        "achievementType": "INCREMENTAL",
        "totalSteps": 100,
        "unlockedIconUrl": icon_url
    },
    {
        "id": "CgkIzvLA59wVEAIQcQ",
        "name": "Collect 40 bombs",
        "description": "Collect 40 bombs across levels in Gardenscapes (0/40 bombs)",
        "experiencePoints": 1000,
        "achievementType": "INCREMENTAL",
        "totalSteps": 100,
        "unlockedIconUrl": icon_url
    },
    {
        "id": "CgkIzvLA59wVEAIQTQ",
        "name": "Save 140 Moves Remaining",
        "description": "Beat match-3 levels with 140 cumulative moves remaining in Gardenscapes (0/140 moves)",
        "experiencePoints": 1500,
        "achievementType": "STANDARD",
        "totalSteps": None,
        "unlockedIconUrl": icon_url
    }
]

selected_ids = [q["id"] for q in exact_quests]

g56 = ps.get("56", {})
g56["title"] = "Gardenscapes"
g56["package"] = "com.playrix.gardenscapes"
g56["developer"] = "Playrix"
g56["category"] = "Play Points Quest & Casual"
g56["icon"] = icon_url
g56["enabled"] = True
g56["section"] = "quest_unlocker"
g56["selected_quests"] = exact_quests
g56["selected_quest_ids"] = selected_ids
g56["selected_quests_count"] = len(exact_quests)

# Put these 4 quests at the beginning of all_quests so they are prominent in quest search/picker
existing_all = g56.get("all_quests", [])
existing_all_filtered = [q for q in existing_all if q["id"] not in selected_ids]
g56["all_quests"] = exact_quests + existing_all_filtered
g56["total_quests_count"] = len(g56["all_quests"])

ps["56"] = g56

# Write local portal_services.json
with open(ps_path, "w", encoding="utf-8") as f:
    json.dump(ps, f, indent=2, ensure_ascii=False)
print("[+] Updated portal_services.json with exact 4 Play Points quests!")

# Write backup
with open(ps_backup, "w", encoding="utf-8") as f:
    json.dump(ps, f, indent=2, ensure_ascii=False)
print("[+] Updated portal_services_backup.json!")

# Sync to Cloudflare D1
print("[*] Syncing updated portal_services to Cloudflare D1...")
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PPMod-Server/2.0"}
res = requests.post(
    "https://ppmodscloud.profitking34.workers.dev/api/cloud/portal-services",
    json={"data": ps},
    headers=headers,
    timeout=12,
    verify=False
)
print(f"[+] Cloudflare D1 sync response: {res.status_code} - {res.text}")
