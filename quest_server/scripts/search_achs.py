import json
import os

with open("achievement_unlocker/real_achievements_db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

g56 = db.get("56", {})
achs = g56.get("achievements", [])
print(f"Total achievements in Gardenscapes (ID 56): {len(achs)}")

keywords = ["apple", "bomb", "move", "sign", "match", "play games", "piece", "remain", "collect", "beat"]
matches = []
for a in achs:
    name = a.get("name", "")
    desc = a.get("description", "")
    full = (name + " " + desc).lower()
    for kw in keywords:
        if kw in full:
            matches.append((kw, a))
            break

print(f"Total keyword matches: {len(matches)}")
for kw, a in matches:
    print(f"[{kw.upper()}] ID: {a.get('id')} | Name: '{a.get('name')}' | Desc: '{a.get('description')}' | Steps: {a.get('totalSteps')}")

# Also let's print ALL achievement names to see what exists in Gardenscapes GPGS
print("\n--- ALL 114 ACHIEVEMENT NAMES IN GARDENSCAPES ---")
for i, a in enumerate(achs):
    print(f"{i+1}. {a.get('name')} (ID: {a.get('id')}) - {a.get('description')}")
