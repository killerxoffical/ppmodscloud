# 1. Update MainActivity.java to request POST_NOTIFICATIONS on app start
with open('app/pp_server/src/com/vareon/playquest/MainActivity.java', 'r', encoding='utf-8') as f:
    text = f.read()

old_perm_block = """            if (Build.VERSION.SDK_INT >= 23) {
                try {
                    if (checkSelfPermission(
                            "android.permission.GET_ACCOUNTS") != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                        requestPermissions(new String[] { "android.permission.GET_ACCOUNTS" }, 1001);
                    }
                } catch (Throwable ignored) {
                }
            }"""

new_perm_block = """            if (Build.VERSION.SDK_INT >= 23) {
                try {
                    java.util.List<String> needed = new java.util.ArrayList<String>();
                    if (checkSelfPermission("android.permission.GET_ACCOUNTS") != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                        needed.add("android.permission.GET_ACCOUNTS");
                    }
                    if (Build.VERSION.SDK_INT >= 33) {
                        if (checkSelfPermission("android.permission.POST_NOTIFICATIONS") != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                            needed.add("android.permission.POST_NOTIFICATIONS");
                        }
                    }
                    if (!needed.isEmpty()) {
                        requestPermissions(needed.toArray(new String[0]), 1001);
                    }
                } catch (Throwable ignored) {
                }
            }"""

if old_perm_block in text:
    text = text.replace(old_perm_block, new_perm_block, 1)
    print('[+] MainActivity.java updated with POST_NOTIFICATIONS runtime request')
else:
    print('[-] old_perm_block not matched directly')

with open('app/pp_server/src/com/vareon/playquest/MainActivity.java', 'w', encoding='utf-8') as f:
    f.write(text)

# Also copy to achievement_unlocker/app/pp_server/src/com/vareon/playquest/MainActivity.java
with open('achievement_unlocker/app/pp_server/src/com/vareon/playquest/MainActivity.java', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] MainActivity.java synced to achievement_unlocker')

# 2. Update achievement_unlocker/app.py with single device session lock & logout endpoint
with open('achievement_unlocker/app.py', 'r', encoding='utf-8') as f:
    app_text = f.read()

# Add logout endpoint
logout_endpoint = """@app.route("/api/device/logout", methods=["POST"])
def device_logout():
    \"\"\"
    Clears device session so the user account can be logged in on another device.
    \"\"\"
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
    return jsonify({"ok": True, "message": "Successfully logged out from device session."})

"""

if '@app.route("/api/device/logout"' not in app_text:
    target_pos = app_text.find('@app.route("/api/login/ppmod"')
    if target_pos != -1:
        app_text = app_text[:target_pos] + logout_endpoint + app_text[target_pos:]
        print('[+] Added /api/device/logout route to app.py')
    else:
        print('[-] target_pos for logout not found')

# Enforce single device login in ppmod_login
old_login_block = """    # Auto-link and persist device session in registered_devices.json
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    devices = load_registered_devices()"""

new_login_block = """    # Enforce strictly 1 active device per account (Single Device Session Lock)
    devices = load_registered_devices()
    if device_id:
        for did, dev in devices.items():
            if did != device_id and dev.get("is_logged_in"):
                if (dev.get("ppmod_uid") and dev.get("ppmod_uid") == uid) or (dev.get("ppmod_email") and dev.get("ppmod_email") == real_email):
                    return jsonify({
                        "ok": False,
                        "error": "এই একাউন্টটি ইতিমধ্যে অন্য একটি ডিভাইসে লগইন করা আছে! অনুগ্রহ করে আগের ডিভাইস থেকে লগআউট না করা পর্যন্ত নতুন ডিভাইসে লগইন করা যাবে না।"
                    }), 409

    # Auto-link and persist device session in registered_devices.json
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")"""

if old_login_block in app_text:
    app_text = app_text.replace(old_login_block, new_login_block, 1)
    print('[+] Enforced single device session check in ppmod_login')
else:
    print('[-] old_login_block not matched directly')

with open('achievement_unlocker/app.py', 'w', encoding='utf-8') as f:
    f.write(app_text)
print('[+] app.py updated successfully')

# 3. Update achievement_unlocker/templates/index.html APK Card to v4.5 PPM CLOUD
with open('achievement_unlocker/templates/index.html', 'r', encoding='utf-8') as f:
    tpl_text = f.read()

old_card_1 = """                                    <div>
                                        <h4 style="font-size:16px; font-weight:800; color:var(--text-primary);">PP
                                            Server Node Client</h4>
                                        <span style="font-size:11.5px; color:var(--accent-green); font-weight:700;">v4.2
                                            Official • Release Signed (V1+V2+V3)</span>
                                    </div>"""

new_card_1 = """                                    <div>
                                        <h4 style="font-size:16px; font-weight:800; color:var(--text-primary);">PPM CLOUD Client App</h4>
                                        <span style="font-size:11.5px; color:var(--accent-green); font-weight:700;">v4.5 Official • Release Signed (V1+V2+V3)</span>
                                    </div>"""

if old_card_1 in tpl_text:
    tpl_text = tpl_text.replace(old_card_1, new_card_1, 1)
    print('[+] Updated APK card 1 title & version text in templates/index.html')

# Update package name display and download button
old_pkg = "<span>Package:</span><code style=\"font-size:11px;\">com.vareon.playquest</code>"
new_pkg = "<span>Package:</span><code style=\"font-size:11px;\">com.ppm.cloud</code>"
if old_pkg in tpl_text:
    tpl_text = tpl_text.replace(old_pkg, new_pkg, 1)

old_dl_btn = """                        <a href="/download/PP_Server.apk" class="btn-download-apk" download>
                            <svg style="width:16px; height:16px; fill:currentColor;" viewBox="0 0 24 24">
                                <path
                                    d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z" />
                            </svg>
                            <span>⬇️ Download PP_Server.apk</span>
                        </a>"""

new_dl_btn = """                        <div style="display:flex; flex-direction:column; gap:6px;">
                            <a href="/download/PPM_Cloud.apk" class="btn-download-apk" download>
                                <svg style="width:16px; height:16px; fill:currentColor;" viewBox="0 0 24 24">
                                    <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z" />
                                </svg>
                                <span>⬇️ Download PPM_Cloud.apk (v4.5)</span>
                            </a>
                            <a href="/download/PP_Server.apk" class="btn-download-apk" download style="background:rgba(255,255,255,0.06); font-size:11px; padding:6px 12px;">
                                <span>⬇️ Download PP_Server.apk (Legacy)</span>
                            </a>
                        </div>"""

if old_dl_btn in tpl_text:
    tpl_text = tpl_text.replace(old_dl_btn, new_dl_btn, 1)
    print('[+] Added PPM_Cloud.apk download button in templates/index.html')

with open('achievement_unlocker/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(tpl_text)
print('[+] templates/index.html updated successfully')
