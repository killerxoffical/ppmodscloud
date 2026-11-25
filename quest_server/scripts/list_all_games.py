import json

with open('achievement_unlocker/portal_services.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total: {len(data)}")
for gid in sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
    g = data[gid]
    print(f"[{gid:>2}] {g.get('title')} ({g.get('package')}) - {len(g.get('all_quests', []))} quests, selected: {len(g.get('selected_quests', []))}")
