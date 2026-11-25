import requests
import json

try:
    r = requests.get('https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices', timeout=6)
    print('CF status:', r.status_code)
    cf_data = r.json()
    if isinstance(cf_data, dict):
        print('Cloudflare D1 devices count:', len(cf_data))
        for k, v in list(cf_data.items())[:5]:
            print(f' - {k}: user={v.get("ppmod_username")} name={v.get("ppmod_name")} email={v.get("google_email")}')
    elif isinstance(cf_data, list):
        print('Cloudflare D1 devices count (list):', len(cf_data))
except Exception as e:
    print('CF Error:', e)

with open('achievement_unlocker/registered_devices.json', 'r', encoding='utf-8') as f:
    local_devs = json.load(f)
print('Local registered_devices count:', len(local_devs))
for k, v in list(local_devs.items())[:5]:
    print(f' - local {k}: user={v.get("ppmod_username")} name={v.get("ppmod_name")} email={v.get("google_email")}')
