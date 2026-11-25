with open('achievement_unlocker/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. New load_portal_services implementation
old_load_portal = '''def load_portal_services(force_refresh=False):
    global PORTAL_SERVICES_CACHE, PORTAL_SERVICES_CACHE_TIME
    now = time.time()
    if not force_refresh and PORTAL_SERVICES_CACHE is not None and (now - PORTAL_SERVICES_CACHE_TIME < 5):
        return PORTAL_SERVICES_CACHE

    local_data = None
    if os.path.exists(PORTAL_SERVICES_FILE):
        try:
            with open(PORTAL_SERVICES_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict):
                    local_data = content
        except Exception as e:
            print(f"[-] Error reading local portal_services: {e}")

    # If local file exists, it is the primary state.
    # Only if local file is missing (e.g. freshly created container), restore from Cloudflare D1:
    if local_data is None:
        cf_data = {}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PPMod-Server/2.0"}
        for attempt in range(2):
            try:
                cf_res = requests.get("https://ppmodscloud.profitking34.workers.dev/api/cloud/portal-services", headers=headers, timeout=5, verify=False)
                if cf_res.status_code == 200:
                    cloud_data = cf_res.json()
                    if isinstance(cloud_data, dict):
                        if "data" in cloud_data and isinstance(cloud_data["data"], dict):
                            cloud_data = cloud_data["data"]
                        cf_data = cloud_data
                        break
            except Exception:
                time.sleep(0.3)
        local_data = cf_data if cf_data else {}
        try:
            with open(PORTAL_SERVICES_FILE, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass'''

new_load_portal = '''def load_portal_services(force_refresh=False):
    global PORTAL_SERVICES_CACHE, PORTAL_SERVICES_CACHE_TIME
    now = time.time()
    if not force_refresh and PORTAL_SERVICES_CACHE is not None and (now - PORTAL_SERVICES_CACHE_TIME < 5):
        return PORTAL_SERVICES_CACHE

    # 1. Read local file first as baseline
    local_data = {}
    if os.path.exists(PORTAL_SERVICES_FILE):
        try:
            with open(PORTAL_SERVICES_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict):
                    local_data = content
        except Exception as e:
            print(f"[-] Error reading local portal_services: {e}")

    # 2. Always query Cloudflare D1 persistent cloud store so new games added on live site are NEVER lost on redeploy
    cf_data = None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PPMod-Server/2.0"}
    try:
        cf_res = requests.get("https://ppmodscloud.profitking34.workers.dev/api/cloud/portal-services", headers=headers, timeout=5, verify=False)
        if cf_res.status_code == 200:
            cloud_json = cf_res.json()
            if isinstance(cloud_json, dict):
                if "data" in cloud_json and isinstance(cloud_json["data"], dict):
                    cloud_json = cloud_json["data"]
                if isinstance(cloud_json, dict) and len(cloud_json) > 0:
                    cf_data = cloud_json
    except Exception as e:
        print(f"[-] Cloudflare portal-services fetch warning: {e}")

    if cf_data is not None:
        # Merge Cloudflare D1 into local so any games in cloud or local are safely combined
        merged = dict(local_data)
        merged.update(cf_data)
        local_data = merged
        try:
            with open(PORTAL_SERVICES_FILE, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass'''

assert old_load_portal in code, "old_load_portal not found!"
code = code.replace(old_load_portal, new_load_portal, 1)

# 2. New load_registered_devices and save_registered_devices implementation
old_devices_block = '''def load_registered_devices(force_refresh=False):
    global REGISTERED_DEVICES_CACHE, REGISTERED_DEVICES_CACHE_TIME
    now = time.time()
    if not force_refresh and REGISTERED_DEVICES_CACHE is not None and (now - REGISTERED_DEVICES_CACHE_TIME < 15):
        return REGISTERED_DEVICES_CACHE
    data = {}
    # 1. Load local file first
    if os.path.exists(REGISTERED_DEVICES_FILE):
        try:
            with open(REGISTERED_DEVICES_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, dict):
                    data = raw
                elif isinstance(raw, list):
                    for item in raw:
                        if isinstance(item, dict) and item.get("device_id"):
                            data[str(item["device_id"])] = item
        except Exception:
            pass

    # 2. ALWAYS fetch and deep-merge Cloudflare D1 persistent cloud store
    try:
        cf_res = requests.get("https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices", timeout=5)
        if cf_res.status_code == 200:
            cloud_raw = cf_res.json()
            cloud_dict = {}
            if isinstance(cloud_raw, list):
                cloud_dict = {str(item["device_id"]): item for item in cloud_raw if isinstance(item, dict) and item.get("device_id")}
            elif isinstance(cloud_raw, dict):
                cloud_dict = cloud_raw
            if cloud_dict:
                data = deep_merge_device_dicts(data, cloud_dict)
                try:
                    with open(REGISTERED_DEVICES_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
    except Exception as e:
        print(f"[-] Cloudflare device fetch error: {e}")

    if not isinstance(data, dict):
        data = {}

    REGISTERED_DEVICES_CACHE = data
    REGISTERED_DEVICES_CACHE_TIME = time.time()
    return data

def save_registered_devices(data, overwrite_cloud=False):
    global REGISTERED_DEVICES_CACHE, REGISTERED_DEVICES_CACHE_TIME
    if not isinstance(data, dict):
        data = {}
    REGISTERED_DEVICES_CACHE = dict(data)
    REGISTERED_DEVICES_CACHE_TIME = time.time()
    try:
        with open(REGISTERED_DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[-] Error saving registered devices: {e}")

    # Asynchronously persist with Cloudflare D1
    def _sync_devs():
        try:
            if overwrite_cloud:
                # Direct overwrite so deletions are permanently saved in Cloudflare D1
                requests.post("https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices", json=data, timeout=8)
            else:
                cf_get = requests.get("https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices", timeout=5)
                cloud_cur = cf_get.json() if (cf_get.status_code == 200 and isinstance(cf_get.json(), dict)) else {}
                all_merged = deep_merge_device_dicts(cloud_cur, data)
                requests.post("https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices", json=all_merged, timeout=8)
        except Exception as e:
            print(f"[-] Cloudflare D1 device sync error: {e}")
    threading.Thread(target=_sync_devs, daemon=True).start()'''

new_devices_block = '''def load_registered_devices(force_refresh=False):
    global REGISTERED_DEVICES_CACHE, REGISTERED_DEVICES_CACHE_TIME
    now = time.time()
    if not force_refresh and REGISTERED_DEVICES_CACHE is not None and (now - REGISTERED_DEVICES_CACHE_TIME < 5):
        return REGISTERED_DEVICES_CACHE

    cf_success = False
    cloud_data = {}
    # 1. Primary Authority: Cloudflare D1 persistent cloud store
    try:
        cf_res = requests.get("https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices", timeout=5)
        if cf_res.status_code == 200:
            cf_raw = cf_res.json()
            if isinstance(cf_raw, dict):
                cloud_data = cf_raw
                cf_success = True
            elif isinstance(cf_raw, list):
                cloud_data = {str(item["device_id"]): item for item in cf_raw if isinstance(item, dict) and item.get("device_id")}
                cf_success = True
    except Exception as e:
        print(f"[-] Cloudflare device fetch error: {e}")

    if cf_success:
        # Cloudflare D1 is authoritative! If admin wiped devices (cloud_data is {}), THAT is the truth!
        data = cloud_data
        try:
            with open(REGISTERED_DEVICES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    else:
        # Fallback to local file ONLY when Cloudflare D1 network call completely fails
        data = {}
        if os.path.exists(REGISTERED_DEVICES_FILE):
            try:
                with open(REGISTERED_DEVICES_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    if isinstance(raw, dict):
                        data = raw
                    elif isinstance(raw, list):
                        for item in raw:
                            if isinstance(item, dict) and item.get("device_id"):
                                data[str(item["device_id"])] = item
            except Exception:
                pass

    if not isinstance(data, dict):
        data = {}

    REGISTERED_DEVICES_CACHE = data
    REGISTERED_DEVICES_CACHE_TIME = time.time()
    return data

def save_registered_devices(data, overwrite_cloud=True):
    global REGISTERED_DEVICES_CACHE, REGISTERED_DEVICES_CACHE_TIME
    if not isinstance(data, dict):
        data = {}
    REGISTERED_DEVICES_CACHE = dict(data)
    REGISTERED_DEVICES_CACHE_TIME = time.time()
    try:
        with open(REGISTERED_DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[-] Error saving registered devices: {e}")

    # Persist directly to Cloudflare D1 so server state and cloud are identical
    def _sync_devs():
        try:
            requests.post("https://ppmodscloud.profitking34.workers.dev/api/cloud/registered-devices", json=data, timeout=8)
        except Exception as e:
            print(f"[-] Cloudflare D1 device sync error: {e}")
    threading.Thread(target=_sync_devs, daemon=True).start()'''

assert old_devices_block in code, "old_devices_block not found!"
code = code.replace(old_devices_block, new_devices_block, 1)

with open('achievement_unlocker/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully patched app.py with bulletproof Cloudflare D1 persistence and wipe protection!")
