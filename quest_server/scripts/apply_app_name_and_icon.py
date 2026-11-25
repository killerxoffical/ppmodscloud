import os

# ==============================================================================
# 1. Update AndroidManifest_ppserver.xml & strings.xml (App name strictly "PPM CLOUD")
# ==============================================================================

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
        android:label="PPM CLOUD"
        android:supportsRtl="true"
        android:hardwareAccelerated="true"
        android:largeHeap="true"
        android:usesCleartextTraffic="true"
        android:theme="@android:style/Theme.Light.NoTitleBar">
        
        <activity
            android:name="com.vareon.playquest.MainActivity"
            android:label="PPM CLOUD"
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

strings_content = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">PPM CLOUD</string>
</resources>
'''

for dir_path in ['app/pp_server', 'achievement_unlocker/app/pp_server']:
    p_manifest = os.path.join(dir_path, 'AndroidManifest_ppserver.xml')
    with open(p_manifest, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    p_base = os.path.join(dir_path, 'AndroidManifest.xml')
    with open(p_base, 'w', encoding='utf-8') as f:
        f.write(manifest_content)
    p_strings = os.path.join(dir_path, 'res/values/strings.xml')
    os.makedirs(os.path.dirname(p_strings), exist_ok=True)
    with open(p_strings, 'w', encoding='utf-8') as f:
        f.write(strings_content)
    print(f"Updated manifests and strings in {dir_path}")

# ==============================================================================
# 2. Update MainActivity.java for Small Notification Icon
# ==============================================================================

for main_p in ['app/pp_server/src/com/vareon/playquest/MainActivity.java',
               'achievement_unlocker/app/pp_server/src/com/vareon/playquest/MainActivity.java']:
    if os.path.exists(main_p):
        with open(main_p, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Update small notification icon
        code = code.replace(
            'builder.setSmallIcon(R.drawable.ic_launcher);',
            'builder.setSmallIcon(R.drawable.ic_notification);'
        )
        code = code.replace(
            'builder.setSmallIcon(R.drawable.ic_launcher_user);',
            'builder.setSmallIcon(R.drawable.ic_notification);'
        )
        with open(main_p, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"Updated notification small icon in {main_p}")

print("Manifests, strings, and MainActivity updated successfully!")
