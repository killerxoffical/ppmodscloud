import json

with open('achievement_unlocker/portal_services.json', 'r', encoding='utf-8') as f:
    ps = json.load(f)

for k, v in ps.items():
    title = v.get('title')
    pkg = v.get('package')
    sel = [q.get('name') for q in v.get('selected_quests', [])]
    print(f"ID {k}: {title} ({pkg}) -> Quests: {sel}")
