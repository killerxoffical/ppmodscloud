import os
import json

with open('achievement_unlocker/registered_devices.json', 'w', encoding='utf-8') as f:
    json.dump({}, f, indent=2)
print("Cleared achievement_unlocker/registered_devices.json to {}")

if os.path.exists('registered_devices.json'):
    with open('registered_devices.json', 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)
    print("Cleared registered_devices.json to {}")
