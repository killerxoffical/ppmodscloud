with open('achievement_unlocker/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '@app.route' in l and 'user' in l.lower():
        print(f"{i+1}: {l.strip()[:100]}")
