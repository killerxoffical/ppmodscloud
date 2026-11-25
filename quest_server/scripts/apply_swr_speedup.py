with open('achievement_unlocker/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace load_portal_services with instant SWR cache
old_load_portal = '''def load_portal_services(force_refresh=False):
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
            pass

    # Ensure every game with known signature in real_achievements_db has client_sig populated
    try:
        real_db_path = os.path.join(DATA_DIR, "real_achievements_db.json")
        if os.path.exists(real_db_path):
            with open(real_db_path, "r", encoding="utf-8") as rdbf:
                rdb = json.load(rdbf)
                for gid, srv in local_data.items():
                    if isinstance(srv, dict) and not srv.get("client_sig"):
                        g_entry = rdb.get(gid) or rdb.get(str(srv.get("game_id", "")))
                        if not g_entry and srv.get("package"):
                            g_entry = next((item for item in rdb.values() if isinstance(item, dict) and item.get("package") == srv.get("package")), None)
                        if g_entry and g_entry.get("client_sig"):
                            srv["client_sig"] = g_entry["client_sig"]
    except Exception:
        pass

    PORTAL_SERVICES_CACHE = local_data
    PORTAL_SERVICES_CACHE_TIME = time.time()
    return local_data'''

new_load_portal = '''PORTAL_SERVICES_SYNCING = False

def _do_sync_portal_services():
    global PORTAL_SERVICES_CACHE, PORTAL_SERVICES_CACHE_TIME
    local_data = {}
    if os.path.exists(PORTAL_SERVICES_FILE):
        try:
            with open(PORTAL_SERVICES_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict):
                    local_data = content
        except Exception as e:
            print(f"[-] Error reading local portal_services: {e}")

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
        merged = dict(local_data)
        merged.update(cf_data)
        local_data = merged
        try:
            with open(PORTAL_SERVICES_FILE, "w", encoding="utf-8") as f:
                json.dump(local_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    try:
        real_db_path = os.path.join(DATA_DIR, "real_achievements_db.json")
        if os.path.exists(real_db_path):
            with open(real_db_path, "r", encoding="utf-8") as rdbf:
                rdb = json.load(rdbf)
                for gid, srv in local_data.items():
                    if isinstance(srv, dict) and not srv.get("client_sig"):
                        g_entry = rdb.get(gid) or rdb.get(str(srv.get("game_id", "")))
                        if not g_entry and srv.get("package"):
                            g_entry = next((item for item in rdb.values() if isinstance(item, dict) and item.get("package") == srv.get("package")), None)
                        if g_entry and g_entry.get("client_sig"):
                            srv["client_sig"] = g_entry["client_sig"]
    except Exception:
        pass

    PORTAL_SERVICES_CACHE = local_data
    PORTAL_SERVICES_CACHE_TIME = time.time()
    return local_data

def load_portal_services(force_refresh=False):
    global PORTAL_SERVICES_CACHE, PORTAL_SERVICES_CACHE_TIME, PORTAL_SERVICES_SYNCING
    now = time.time()
    # 1. Instant 0ms return if cache is fresh (< 60s)
    if not force_refresh and PORTAL_SERVICES_CACHE is not None and (now - PORTAL_SERVICES_CACHE_TIME < 60):
        return PORTAL_SERVICES_CACHE

    # 2. If cache exists (> 60s), return cached immediately and refresh in background (Stale-While-Revalidate)
    if not force_refresh and PORTAL_SERVICES_CACHE is not None:
        if not PORTAL_SERVICES_SYNCING:
            def _bg_portal():
                global PORTAL_SERVICES_SYNCING
                PORTAL_SERVICES_SYNCING = True
                try:
                    _do_sync_portal_services()
                finally:
                    PORTAL_SERVICES_SYNCING = False
            threading.Thread(target=_bg_portal, daemon=True).start()
        return PORTAL_SERVICES_CACHE

    return _do_sync_portal_services()'''

assert old_load_portal in code, "old_load_portal not found!"
code = code.replace(old_load_portal, new_load_portal, 1)

# Replace load_registered_devices with instant SWR cache
old_devices = '''def load_registered_devices(force_refresh=False):
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
    return data'''

new_devices = '''REGISTERED_DEVICES_SYNCING = False

def _do_sync_registered_devices():
    global REGISTERED_DEVICES_CACHE, REGISTERED_DEVICES_CACHE_TIME
    cf_success = False
    cloud_data = {}
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
        data = cloud_data
        try:
            with open(REGISTERED_DEVICES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    else:
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

def load_registered_devices(force_refresh=False):
    global REGISTERED_DEVICES_CACHE, REGISTERED_DEVICES_CACHE_TIME, REGISTERED_DEVICES_SYNCING
    now = time.time()
    # 1. Instant 0ms return if cache is fresh (< 60s)
    if not force_refresh and REGISTERED_DEVICES_CACHE is not None and (now - REGISTERED_DEVICES_CACHE_TIME < 60):
        return REGISTERED_DEVICES_CACHE

    # 2. If cache exists (> 60s), return cached immediately and refresh in background (Stale-While-Revalidate)
    if not force_refresh and REGISTERED_DEVICES_CACHE is not None:
        if not REGISTERED_DEVICES_SYNCING:
            def _bg_devs():
                global REGISTERED_DEVICES_SYNCING
                REGISTERED_DEVICES_SYNCING = True
                try:
                    _do_sync_registered_devices()
                finally:
                    REGISTERED_DEVICES_SYNCING = False
            threading.Thread(target=_bg_devs, daemon=True).start()
        return REGISTERED_DEVICES_CACHE

    return _do_sync_registered_devices()'''

assert old_devices in code, "old_devices not found!"
code = code.replace(old_devices, new_devices, 1)

with open('achievement_unlocker/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Applied instant Stale-While-Revalidate speed optimization to app.py successfully!")
