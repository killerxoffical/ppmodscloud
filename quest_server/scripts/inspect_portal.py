with open('achievement_unlocker/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '@app.route("/portal"' in l or '@app.route("/api/portal' in l or 'def portal(' in l or 'def get_portal_services' in l:
        print(f"{i+1}: {l.strip()[:100]}")
