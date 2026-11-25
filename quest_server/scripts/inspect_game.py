import json

with open('achievement_unlocker/portal_services.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for gid in ['56', '57', '4']:
    print(f"=== Game {gid} ===")
    print(json.dumps(data.get(gid, {}), indent=2))
