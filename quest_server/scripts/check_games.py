import json

with open('achievement_unlocker/portal_services.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total games in portal_services.json: {len(data)}")
for gid, g in data.items():
    name = str(g.get("name") or "NO_NAME")
    pkg = str(g.get("package") or "")
    active = g.get("active", True)
    is_lvl = g.get("is_level", False)
    no_data = g.get("no_data", False)
    hidden = g.get("hidden", False)
    print(f"ID {str(gid):>3}: {name:<35} | pkg: {pkg:<40} | active={active} is_lvl={is_lvl} no_data={no_data} hidden={hidden}")
