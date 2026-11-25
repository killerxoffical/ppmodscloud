import os
import shutil

# 1. Update strings.xml
strings_content = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">PPM CLOUD v4.5</string>
</resources>
'''

for dir_path in ['app/pp_server/res/values', 'achievement_unlocker/app/pp_server/res/values']:
    os.makedirs(dir_path, exist_ok=True)
    p = os.path.join(dir_path, 'strings.xml')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(strings_content)
    print(f"Updated {p}")

# 2. Update AndroidManifest_ppserver.xml and AndroidManifest.xml
manifest_content = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.ppm.cloud"
    android:versionCode="45"
    android:versionName="4.5">

    <uses-sdk
        android:minSdkVersion="21"
        android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.GET_ACCOUNTS" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <queries>
        <intent>
            <action android:name="android.intent.action.VIEW" />
            <data android:scheme="https" />
        </intent>
    </queries>

    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher_user"
        android:roundIcon="@drawable/ic_launcher_user_round"
        android:label="PPM CLOUD v4.5"
        android:supportsRtl="true"
        android:hardwareAccelerated="true"
        android:largeHeap="true"
        android:usesCleartextTraffic="true"
        android:theme="@android:style/Theme.Light.NoTitleBar">
        
        <activity
            android:name="com.vareon.playquest.MainActivity"
            android:label="PPM CLOUD v4.5"
            android:exported="true"
            android:hardwareAccelerated="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

for dir_path in ['app/pp_server', 'achievement_unlocker/app/pp_server']:
    p_manifest = os.path.join(dir_path, 'AndroidManifest_ppserver.xml')
    with open(p_manifest, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    print(f"Updated {p_manifest}")
    p_base = os.path.join(dir_path, 'AndroidManifest.xml')
    with open(p_base, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    print(f"Updated {p_base}")

# 3. Update MainActivity.java
for dir_path in ['app/pp_server/src/com/vareon/playquest', 'achievement_unlocker/app/pp_server/src/com/vareon/playquest']:
    main_p = os.path.join(dir_path, 'MainActivity.java')
    if os.path.exists(main_p):
        with open(main_p, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Replace app name in getAppInfoJson
        code = code.replace(
            'obj.put("appName", isDev ? "PlayQuest Token Finder" : "PPM Server");',
            'obj.put("appName", isDev ? "PlayQuest Token Finder" : "PPM CLOUD v4.5");'
        )
        # Notification channel name
        code = code.replace(
            'channelId, "PP Server Notifications"',
            'channelId, "PPM CLOUD v4.5 Notifications"'
        )
        code = code.replace(
            'channel.setDescription("PP Server sync and account updates");',
            'channel.setDescription("PPM CLOUD sync and account updates");'
        )
        with open(main_p, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Updated {main_p}")

print("Manifests and sources updated successfully!")
