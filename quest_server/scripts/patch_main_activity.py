import os
import sys

def patch_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        c = f.read()

    old_logout = '''    public void doLogout() {
        if (accountStorage != null) {
            accountStorage.clearUserSession();
            accountStorage.clearAccounts();
        }
        Toast.makeText(this, "Logged out of PP Mod session.", Toast.LENGTH_SHORT).show();'''

    new_logout = '''    public void doLogout() {
        if (accountStorage != null) {
            String lastUid = accountStorage.getUserUid();
            String lastEmail = accountStorage.getUserEmail();
            accountStorage.clearUserSession();
            accountStorage.clearAccounts();
            try {
                CloudSyncClient.notifyDeviceLogout(this, lastUid, lastEmail);
            } catch (Throwable ignored) {
            }
        }
        Toast.makeText(this, "Logged out of PP Mod session.", Toast.LENGTH_SHORT).show();'''

    if old_logout not in c:
        print(f"Error: old_logout not found in {file_path}")
        return False

    c = c.replace(old_logout, new_logout, 1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(c)

    print(f"Successfully patched {file_path}")
    return True

f1 = "app/pp_server/src/com/vareon/playquest/MainActivity.java"
f2 = "achievement_unlocker/app/pp_server/src/com/vareon/playquest/MainActivity.java"
if patch_file(f1) and patch_file(f2):
    print("MainActivity.java successfully patched in both locations!")
else:
    sys.exit(1)
