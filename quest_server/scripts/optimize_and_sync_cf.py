import json
import os
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ps_path = os.path.join(ROOT_DIR, "portal_services.json")
ps_backup = os.path.join(ROOT_DIR, "portal_services_backup.json")

with open(ps_path, "r", encoding="utf-8") as f:
    ps = json.load(f)

icon_url = "https://play-lh.googleusercontent.com/C5Yp55qwwU8zJAkfO9DQTtHauJcmQgMM59HH8odxPM6KlHiqO6WY9jZsWnIN1k3pfgwo2o3e3ygiizwHSIPbY-w=s0-br30"

# Exact 4 Google Play Points Quests for Gardenscapes from the screenshot:
exact_gardenscapes_quests = [
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

# Update Gardenscapes
g56 = ps.get("56", {})
g56["title"] = "Gardenscapes"
g56["package"] = "com.playrix.gardenscapes"
g56["client_sig"] = "b0cb218c78f839529f5721e1b0757a91d1bc1e2e"
g56["developer"] = "Playrix"
g56["category"] = "Play Points Quest & Casual"
g56["icon"] = icon_url
g56["enabled"] = True
g56["section"] = "quest_unlocker"
g56["selected_quests"] = exact_gardenscapes_quests
g56["selected_quest_ids"] = [q["id"] for q in exact_gardenscapes_quests]
g56["selected_quests_count"] = 4
g56["total_quests_count"] = 114
g56["all_quests"] = exact_gardenscapes_quests # Keep light!
ps["56"] = g56

# Optimize all services: only keep selected_quests or max 5 quests in all_quests to keep payload ultra light
optimized_ps = {}
for gid, srv in ps.items():
    s = dict(srv)
    if "all_quests" in s and len(s.get("all_quests", [])) > 5:
        # Keep selected plus first few
        sel_ids = set(s.get("selected_quest_ids", []))
        light_all = list(s.get("selected_quests", []))
        for q in s["all_quests"]:
            if q["id"] not in sel_ids and len(light_all) < 6:
                light_all.append(q)
        s["all_quests"] = light_all
    optimized_ps[gid] = s

raw_json = json.dumps(optimized_ps, ensure_ascii=False)
print(f"[+] Optimized payload size: {len(raw_json)} bytes (down from 423,824 bytes!)")

# Save optimized local files
with open(ps_path, "w", encoding="utf-8") as f:
    f.write(raw_json)

with open(ps_backup, "w", encoding="utf-8") as bf:
    bf.write(raw_json)

print("[+] Local files saved successfully.")

# Now sync to Cloudflare D1
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PPMod-Server/2.0", "Content-Type": "application/json"}
try:
    cf_res = requests.post(
        "https://ppmod-api.tredarskvt.workers.dev/api/cloud/portal-services",
        data=raw_json,
        headers=headers,
        timeout=12,
        verify=False
    )
    print(f"[+] Cloudflare D1 sync status: {cf_res.status_code}")
    print(f"[+] Cloudflare D1 response: {cf_res.text[:200]}")
except Exception as e:
    print(f"[-] Cloudflare sync error: {e}")
