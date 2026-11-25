import os
import sys

app_py_path = os.path.abspath("achievement_unlocker/app.py")

with open(app_py_path, "r", encoding="utf-8") as f:
    c = f.read()

# 1. Update register_device
target1 = '''    # MULTI-DEVICE ACCOUNT MERGE:
    # Pull any existing accounts belonging to this user across all registered devices & SYNC_CODES'''

replacement1 = '''    # Enforce strictly 1 active device per user account (Single Device Session Lock)
    if is_logged_in and (ppmod_email or ppmod_uid):
        for other_dev_id, other_dev in devices.items():
            if other_dev_id != device_id and other_dev.get("is_logged_in"):
                o_email = str(other_dev.get("ppmod_email", "")).strip().lower()
                o_uid = str(other_dev.get("ppmod_uid", "")).strip()
                if (ppmod_email and o_email and o_email == ppmod_email) or (ppmod_uid and o_uid and o_uid == ppmod_uid):
                    if device_id in devices:
                        devices[device_id]["is_logged_in"] = False
                        save_registered_devices(devices)
                    return jsonify({
                        "ok": False,
                        "error": "এই একাউন্টটি ইতিমধ্যে অন্য একটি ডিভাইসে লগইন করা আছে! অনুগ্রহ করে আগের ডিভাইস থেকে লগআউট না করা পর্যন্ত নতুন ডিভাইসে লগইন করা যাবে না।"
                    }), 409

    # MULTI-DEVICE ACCOUNT MERGE:
    # Pull any existing accounts belonging to this user across all registered devices & SYNC_CODES'''

if target1 not in c:
    print("Error: Target 1 not found in app.py")
    sys.exit(1)

c = c.replace(target1, replacement1, 1)

# 2. Update device_logout and add verify_session & admin_reset_device_session
target2 = '''@app.route("/api/device/logout", methods=["POST"])
def device_logout():
    """
    Clears device session so the user account can be logged in on another device.
    """
    data = request.get_json(silent=True) or {}
    device_id = str(data.get("device_id", "")).strip()
    uid = str(data.get("uid", "")).strip()
    email = str(data.get("email", "")).strip().lower()

    devices = load_registered_devices()
    updated = False
    for did, dev in devices.items():
        if (device_id and did == device_id) or (uid and dev.get("ppmod_uid") == uid) or (email and dev.get("ppmod_email") == email):
            dev["is_logged_in"] = False
            dev["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
            updated = True

    if updated:
        save_registered_devices(devices)
    return jsonify({"ok": True, "message": "Successfully logged out from device session."})'''

replacement2 = '''@app.route("/api/device/logout", methods=["POST"])
def device_logout():
    """
    Clears device session so the user account can be logged in on another device.
    """
    data = request.get_json(silent=True) or {}
    device_id = str(data.get("device_id", "")).strip()
    uid = str(data.get("uid", "")).strip()
    email = str(data.get("email", "")).strip().lower()

    devices = load_registered_devices(force_refresh=True)
    updated = False
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    for did, dev in devices.items():
        if (device_id and did == device_id) or (uid and dev.get("ppmod_uid") == uid) or (email and dev.get("ppmod_email") == email):
            dev["is_logged_in"] = False
            dev["last_seen"] = now_str
            updated = True

    if updated:
        save_registered_devices(devices, overwrite_cloud=True)
    return jsonify({"ok": True, "message": "Successfully logged out from device session."})

@app.route("/api/session/verify", methods=["POST"])
def verify_session():
    """
    Verifies if a user (by uid or email) is currently active on another device.
    Used by PPM Cloud Android app before allowing login.
    Returns 409 Conflict if locked by another device.
    """
    data = request.get_json(silent=True) or {}
    device_id = str(data.get("device_id", "")).strip()
    uid = str(data.get("uid", "")).strip()
    email = str(data.get("email", "")).strip().lower()

    if not uid and not email:
        return jsonify({"ok": True, "locked": False})

    devices = load_registered_devices(force_refresh=True)
    for did, dev in devices.items():
        if did != device_id and dev.get("is_logged_in"):
            d_uid = str(dev.get("ppmod_uid", "")).strip()
            d_email = str(dev.get("ppmod_email", "")).strip().lower()
            if (uid and d_uid and d_uid == uid) or (email and d_email and d_email == email):
                return jsonify({
                    "ok": False,
                    "locked": True,
                    "active_device": dev.get("model", "Another Device"),
                    "error": "এই একাউন্টটি ইতিমধ্যে অন্য একটি ডিভাইসে লগইন করা আছে! অনুগ্রহ করে আগের ডিভাইস থেকে লগআউট না করা পর্যন্ত নতুন ডিভাইসে লগইন করা যাবে না।"
                }), 409

    return jsonify({"ok": True, "locked": False})

@app.route("/api/admin/device/reset_session", methods=["POST"])
def admin_reset_device_session():
    """
    Allows Admin to force-clear session locks for a device, uid, or email.
    """
    data = request.get_json(silent=True) or {}
    device_id = str(data.get("device_id", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    uid = str(data.get("uid", "")).strip()

    devices = load_registered_devices(force_refresh=True)
    unlocked = False
    for did, dev in devices.items():
        if (device_id and did == device_id) or (email and dev.get("ppmod_email") == email) or (uid and dev.get("ppmod_uid") == uid):
            dev["is_logged_in"] = False
            unlocked = True

    if unlocked:
        save_registered_devices(devices, overwrite_cloud=True)
        return jsonify({"ok": True, "message": "Device session successfully reset."})
    return jsonify({"ok": False, "error": "Device or user not found."}), 404'''

if target2 not in c:
    print("Error: Target 2 not found in app.py")
    sys.exit(1)

c = c.replace(target2, replacement2, 1)

with open(app_py_path, "w", encoding="utf-8") as f:
    f.write(c)

print("Successfully updated achievement_unlocker/app.py with session verification!")
