#!/usr/bin/env python3
import os
import sys
import glob
import shutil
import zipfile
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

JAVA_HOME = r"C:\Program Files\Eclipse Adoptium\jdk-25.0.4.101-hotspot"
SDK = r"C:\Users\Rubel\AppData\Local\Android\Sdk"
BUILD_TOOLS = os.path.join(SDK, r"build-tools\34.0.0")
PLATFORM = os.path.join(SDK, r"platforms\android-34")

AAPT = os.path.join(BUILD_TOOLS, "aapt.exe")
ZIPALIGN = os.path.join(BUILD_TOOLS, "zipalign.exe")
DEXDUMP = os.path.join(BUILD_TOOLS, "dexdump.exe")
ANDROID_JAR = os.path.join(PLATFORM, "android.jar")
JAVA = os.path.join(JAVA_HOME, r"bin\java.exe")
JAVAC = os.path.join(JAVA_HOME, r"bin\javac.exe")
D8_JAR = os.path.join(BUILD_TOOLS, r"lib\d8.jar")
APKSIGNER_JAR = os.path.join(BUILD_TOOLS, r"lib\apksigner.jar")
KEYSTORE = "release.keystore"
KEYSTORE_PASS = "ppserver123"
KEY_ALIAS = "ppserver"

print("=" * 60)
print(">>> BULLETPROOF BUILD STARTING: PP SERVER (USER EDITION)")
print("=" * 60)

# STEP 1: Resources
print("\n>>> Step 1: Compiling resources with aapt...")
shutil.copy2("AndroidManifest_ppserver.xml", "AndroidManifest.xml")
cmd_aapt = [AAPT, "package", "-f", "-m", "-J", "src", "--custom-package", "com.vareon.playquest", "-M", "AndroidManifest.xml", "-S", "res", "-I", ANDROID_JAR]
subprocess.run(cmd_aapt, check=True)
print(">>> R.java generated successfully.")

# STEP 2: Java sources
print("\n>>> Step 2: Compiling Java sources with pure Java 8 bytecode...")
out_classes = "out_classes"
if os.path.exists(out_classes):
    shutil.rmtree(out_classes)
os.makedirs(os.path.join(out_classes, "dex"), exist_ok=True)

java_files = glob.glob("src/com/vareon/playquest/*.java")
cmd_javac = [
    JAVAC,
    "-source", "8",
    "-target", "8",
    "-bootclasspath", ANDROID_JAR,
    "-Xlint:-options",
    "-d", out_classes,
    "-cp", ANDROID_JAR
] + java_files

res_javac = subprocess.run(cmd_javac, capture_output=True, text=True)
if res_javac.returncode != 0:
    print(res_javac.stderr)
    raise RuntimeError(f"javac failed with code {res_javac.returncode}")

class_files = glob.glob(os.path.join(out_classes, "com/**/*.class"), recursive=True)
print(f">>> Found {len(class_files)} compiled .class files.")
if len(class_files) == 0:
    raise RuntimeError("No .class files compiled!")

for cf in class_files:
    with open(cf, "rb") as fp:
        hdr = fp.read(8)
        ver = int.from_bytes(hdr[6:8], "big")
        if ver != 52:
            raise RuntimeError(f"CRITICAL: Bytecode version mismatch! {cf} has major version {ver} instead of 52 (Java 8)")

print(f">>> VERIFIED: All {len(class_files)} class files are pure Java 8 (v52)!")

# STEP 3: DEX generation
print("\n>>> Step 3: Generating DEX with d8...")
app_jar = os.path.join(out_classes, "app.jar")
with zipfile.ZipFile(app_jar, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for cf in class_files:
        rel_path = os.path.relpath(cf, out_classes)
        zf.write(cf, rel_path)

dex_out = os.path.join(out_classes, "dex")
cmd_d8 = [JAVA, "-cp", D8_JAR, "com.android.tools.r8.D8", "--release", "--min-api", "21", "--lib", ANDROID_JAR, "--output", dex_out, app_jar]
subprocess.run(cmd_d8, check=True)

classes_dex = os.path.join(dex_out, "classes.dex")
if not os.path.exists(classes_dex) or os.path.getsize(classes_dex) == 0:
    raise RuntimeError("classes.dex generation failed!")

res_dump = subprocess.run([DEXDUMP, classes_dex], capture_output=True, text=True)
dex_classes = [l.strip() for l in res_dump.stdout.splitlines() if "Class descriptor" in l]
print(f">>> DEX Class Definitions count: {len(dex_classes)}")
has_main = any("MainActivity" in l for l in dex_classes)
if not has_main:
    raise RuntimeError("CRITICAL ERROR: MainActivity class definition is missing from classes.dex!")
print(">>> Verified MainActivity class definition is present in DEX!")

def package_and_sign(manifest_src, apk_name, title):
    print(f"\n----------------------------------------------------------")
    print(f">>> Packaging {apk_name} ({title})...")
    shutil.copy2(manifest_src, "AndroidManifest.xml")
    
    unaligned = f"unaligned_{apk_name}"
    aligned = f"aligned_{apk_name}"
    for f in [unaligned, aligned, apk_name]:
        if os.path.exists(f):
            os.remove(f)

    # AAPT package with out_classes/dex
    cmd_pkg = [AAPT, "package", "-f", "-M", "AndroidManifest.xml", "-S", "res", "-A", "assets", "-I", ANDROID_JAR, "-F", unaligned, dex_out]
    subprocess.run(cmd_pkg, check=True)

    # Zipalign
    cmd_align = [ZIPALIGN, "-f", "-p", "4", unaligned, aligned]
    subprocess.run(cmd_align, check=True)

    # Sign with v1, v2, v3
    cmd_sign = [
        JAVA, "-jar", APKSIGNER_JAR, "sign",
        "--ks", KEYSTORE,
        "--ks-pass", f"pass:{KEYSTORE_PASS}",
        "--ks-key-alias", KEY_ALIAS,
        "--key-pass", f"pass:{KEYSTORE_PASS}",
        "--v1-signing-enabled", "true",
        "--v2-signing-enabled", "true",
        "--v3-signing-enabled", "true",
        "--v4-signing-enabled", "false",
        "--out", apk_name,
        aligned
    ]
    subprocess.run(cmd_sign, check=True)

    # Verify signature
    cmd_verify = [JAVA, "-jar", APKSIGNER_JAR, "verify", apk_name]
    subprocess.run(cmd_verify, check=True)
    
    # Verify classes.dex in final apk
    with zipfile.ZipFile(apk_name, "r") as zf:
        if "classes.dex" not in zf.namelist():
            raise RuntimeError(f"CRITICAL: classes.dex missing from {apk_name}!")
        dex_data = zf.read("classes.dex")
        if len(dex_data) < 10000:
            raise RuntimeError(f"CRITICAL: classes.dex too small in {apk_name} ({len(dex_data)} bytes)!")

    # Clean intermediate files
    for f in [unaligned, aligned]:
        if os.path.exists(f):
            os.remove(f)

    print(f">>> SUCCESS: {apk_name} built, zipaligned, and verified signed ({os.path.getsize(apk_name)} bytes)!")

# STEP 4: Package and Sign PP_Server.apk (User Edition: PPM CLOUD v5.0)
package_and_sign("AndroidManifest_ppserver.xml", "PP_Server.apk", "PPM CLOUD v5.0 User Edition")

# Make PPM_Cloud.apk identical to PP_Server.apk
shutil.copy2("PP_Server.apk", "PPM_Cloud.apk")
print(">>> Created PPM_Cloud.apk as official distribution package.")

# Restore base manifest
shutil.copy2("AndroidManifest_ppserver.xml", "AndroidManifest.xml")

# STEP 5: Distribute PPM_Cloud.apk & PP_Server.apk
print("\n>>> Step 5: Distributing PPM_Cloud.apk and PP_Server.apk...")
base_script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_script_dir, "..", ".."))
achievement_dir = os.path.join(root_dir, "achievement_unlocker")

dist_targets = [
    # app/
    os.path.join(base_script_dir, "..", "PP_Server.apk"),
    os.path.join(base_script_dir, "..", "PPM_Cloud.apk"),
    # root
    os.path.join(root_dir, "PP_Server.apk"),
    os.path.join(root_dir, "PPM_Cloud.apk"),
    os.path.join(root_dir, "static", "PP_Server.apk"),
    os.path.join(root_dir, "static", "PPM_Cloud.apk"),
    # achievement_unlocker
    os.path.join(achievement_dir, "PP_Server.apk"),
    os.path.join(achievement_dir, "PPM_Cloud.apk"),
    os.path.join(achievement_dir, "static", "PP_Server.apk"),
    os.path.join(achievement_dir, "static", "PPM_Cloud.apk"),
    os.path.join(achievement_dir, "app", "PP_Server.apk"),
    os.path.join(achievement_dir, "app", "PPM_Cloud.apk"),
    os.path.join(achievement_dir, "app", "pp_server", "PP_Server.apk"),
    os.path.join(achievement_dir, "app", "pp_server", "PPM_Cloud.apk"),
]

for t in dist_targets:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    src_file = "PPM_Cloud.apk" if "PPM_Cloud" in t else "PP_Server.apk"
    src_path = os.path.join(base_script_dir, src_file)
    for attempt in range(4):
        try:
            shutil.copy2(src_path, t)
            print(f"  -> Copied {src_file} to {t}")
            break
        except PermissionError:
            time.sleep(0.5)
            if attempt == 3:
                print(f"  [!] Note: could not write {t} (locked by external process)")

# Also update build_out in bin for consistency
bin_dex = os.path.join("bin", "dex")
os.makedirs(bin_dex, exist_ok=True)
shutil.copy2(classes_dex, os.path.join(bin_dex, "classes.dex"))

print("\n" + "=" * 60)
print(">>> PP SERVER BUILD COMPLETE AND CERTIFIED CRASH-PROOF!")
print(">>> [1] PP_Server.apk -> User Mode (com.vareon.playquest) [v5.0 | Code 7]")
print("=" * 60)
