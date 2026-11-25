import re

with open('pp mod/admin.html', 'r', encoding='utf-8') as f:
    c = f.read()

urls = set(re.findall(r'https://[^\s"\'<>]+workers\.dev[^\s"\'<>]*', c))
print("Workers.dev endpoints in pp mod/admin.html:")
for u in sorted(urls):
    print(" ", u)

render_urls = set(re.findall(r'https://[^\s"\'<>]+onrender\.com[^\s"\'<>]*', c))
print("\nRender endpoints in pp mod/admin.html:")
for u in sorted(render_urls):
    print(" ", u)

print("\nWhere is db (Firestore) initialized?")
for line in c.splitlines():
    if 'getFirestore' in line or 'initializeApp' in line or 'apiKey' in line:
        print(" ", line[:120])
