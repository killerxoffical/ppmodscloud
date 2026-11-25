# PP MOD & AUTO-QUEST SYSTEM ARCHITECTURE

> **Last Updated:** November 22, 2026  
> **Workspace Root:** `c:\Users\Rubel\Downloads\backup_20261112_160011`  
> **GitHub Repository:** [https://github.com/killerxoffical/pp-mod-auto-quest](https://github.com/killerxoffical/pp-mod-auto-quest)

---

## 📁 Directory Structure Overview (প্রজেক্ট ফাইল স্ট্রাকচার)

প্রজেক্টের প্রতিটি মডিউল সম্পূর্ণ আলাদা ও পরিচ্ছন্ন ফোল্ডারে সাজানো হয়েছে যাতে যে-কোনো ইউজার বা এআই (AI) খুব সহজেই বুঝতে পারে কোন ফাইলের কাজ কী।

```
backup_20261112_160011/
├── app/                        # 📱 [1] Android App Source Code, Web UI, & APK Build
│   └── pp_server/
│       ├── src/                # Pure Java Source Code (Android Native Engine)
│       │   └── com/vareon/playquest/
│       │       ├── MainActivity.java      # Main Activity, WebView bridge, UI lifecycle
│       │       ├── CloudSyncClient.java   # Strict Cloudflare D1 & Render sync client
│       │       ├── AccountItem.java       # Account model (Points, Tier, Country, QID)
│       │       ├── AccountStorage.java    # Local persistent encrypted storage
│       │       └── SecurityGuard.java     # Endpoint URLs and security guards
│       ├── assets/www/         # Modern Mobile Web UI
│       │   ├── index.html      # Responsive mobile dashboard & account manager
│       │   ├── earth_globe.png # Custom transparent Earth icon for Region Filter
│       │   └── img/            # High-res image assets
│       ├── res/                # Android Resources (Drawables, Strings, Layouts)
│       ├── build_apk.py        # One-click standalone build & sign script (Java 8 bytecode)
│       ├── release.keystore    # Production APK signing keystore
│       ├── PP_Server.apk       # Compiled & Signed User Edition APK
│       └── PlayQuest_Token_Finder.apk # Developer Token Finder Edition APK
│
├── achievement_unlocker/       # 🚀 [2] Backend Automation Server & Git Repository
│   ├── app.py                  # Primary Flask backend API (Port 5000 / Render)
│   ├── play_points_checker.py  # 100% Real Google Play Points & Tier live verification
│   ├── sync_codes.json         # Master Token Vault & Live Play Points Data
│   ├── registered_devices.json # Connected mobile device registry
│   ├── portal_services.json    # Game services and achievement definitions
│   ├── static/                 # Downloadable signed APKs & web assets
│   │   ├── PP_Server.apk
│   │   └── PlayQuest_Token_Finder.apk
│   ├── templates/              # Backend admin web templates
│   ├── requirements.txt        # Python backend dependencies
│   ├── Dockerfile & Procfile   # Cloud deployment configs (Render / Docker)
│   └── .git/                   # Git repository for killerxoffical/pp-mod-auto-quest
│
├── pp mod/                     # 🌐 [3] PP MOD Cloudflare Edge API & Web Portal
│   ├── Coud f warker page.txt  # Cloudflare Worker + D1 Database Edge API script
│   ├── admin.html              # PP MOD Admin Console (User management, licenses)
│   ├── index.html              # PP MOD User Web Portal
│   ├── worker.js               # Node / Edge worker script
│   ├── FIRESTORE_RULES.txt     # Security rules
│   └── brand_logo.png, etc.    # Official branding & coin assets
│
├── play-points-extension/      # 🧩 [4] Google Play Points Auto-Perk Chrome Extension
│   ├── manifest.json           # Chrome Extension Manifest V3
│   ├── background.js           # Background service worker & Friday 1:01 PM BD drop timer
│   ├── content.js              # Injected DOM script to detect points and click claim
│   ├── popup.html & popup.js   # Extension user popup interface
│   ├── extension_admin.html    # Extension admin console & license manager
│   └── icon.png                # Extension logo
│
└── backups/                    # 📦 [5] Centralized Backups, Archives & Old Scripts
    ├── archives/               # Historical .zip archives and .bak files
    ├── old_root_files/         # Deprecated loose root test scripts and images
    ├── scratch/                # Developer test scripts and intermediate files
    └── scripts/                # Historical Windows .bat build helpers
```

---

## 🛠️ Components & Roles (কোন ফোল্ডারে কী কাজ)

### 1. `app/` (Android Application)
* **উদ্দেশ্য:** অ্যান্ড্রয়েড ডিভাইসে চলার জন্য তৈরি নেটিভ হাইব্রিড অ্যাপ।
* **বিল্ড স্ক্রিপ্ট:** `python app/pp_server/build_apk.py` চালালেই স্বয়ংক্রিয়ভাবে `R.java`, Java 8 Bytecode compile, `d8` DEX generation, zipalign এবং v1/v2/v3 sign হয়ে `PP_Server.apk` তৈরি হয়।
* **UI Features:**
  * রিয়েল Google Play Points (যেমন: `Gold • 310 PP`) লাইভ ডিসপ্লে।
  * কাস্টম ট্রান্সপারেন্ট পৃথিবীর আইকন (`earth_globe.png`) সহ কান্ট্রি ও রিজিয়ন ফিল্টার।
  * ৬-সংখ্যার সুরক্ষিত QID কোড ডিসপ্লে ও এক-ট্যাপ কপি।
  * কোনো ফেক ক্লেইম বা ডলার ব্যালেন্স নেই; সম্পূর্ণ ছিমছাম ইন্টারফেস।

### 2. `achievement_unlocker/` (Backend Automation Engine)
* **উদ্দেশ্য:** GPGS অ্যাচিভমেন্ট আনলকিং, মাস্টার টোকেন ও লাইভ প্লে পয়েন্ট ভেরিফিকেশন ইঞ্জিন।
* **মূল ফাইল:**
  * `app.py`: Flask ব্যাকএন্ড এন্ডপয়েন্ট।
  * `play_points_checker.py`: Google Web Session ও OAuth ব্যবহার করে Google Play থেকে ১০০% রিয়েল পয়েন্ট ও টায়ার ডাটা ফেচ করে।
  * `sync_codes.json`: টোকেন এবং সিঙ্ক কোডের এনক্রিপ্টেড ডাটাবেস।
* **Git Repo:** এই ফোল্ডারটি সরাসরি `https://github.com/killerxoffical/pp-mod-auto-quest` রিপোজিটরির সাথে সংযুক্ত।

### 3. `pp mod/` (Web Portal & Cloudflare Edge)
* **উদ্দেশ্য:** Cloudflare D1 ডেটাবেসের সাথে সংযুক্ত এজ API এবং ইউজার কনসোল।
* **মূল ফাইল:**
  * `Coud f warker page.txt`: Cloudflare Worker কোড (D1 ভল্ট, স্ট্রিক্ট ইউজার প্রাইভেসি গার্ড `WHERE uid = ? OR owner_email = ?`)।
  * `admin.html`: লাইসেন্স কি, ইউজার ব্যালেন্স ও ডিভাইস ম্যানেজমেন্ট।

### 4. `play-points-extension/` (Chrome Auto-Claim Extension)
* **উদ্দেশ্য:** ব্রাউজারে স্বয়ংক্রিয়ভাবে উইকলি পারক (Weekly Perk) ক্লেইম করা।
* **মূল ফাইল:**
  * `background.js`: প্রতি শুক্রবার বাংলাদেশ সময় দুপুর ১:০১ টায় (Friday 1:01 PM BD Time / UTC+6) অটো ড্রপ ডিটেক্ট করে।
  * `content.js`: Google Play Points পেজে ঢুকে স্বয়ংক্রিয়ভাবে ক্লেইম বাটনে ক্লিক করে পয়েন্ট আপডেট করে।

### 5. `backups/` (একক ব্যাকআপ ফোল্ডার)
* সমস্ত পুরোনো জিপ আর্কাইভ, এককালীন স্ক্র্যাচ ফাইল ও ব্যাকআপ স্ক্রিপ্ট এই ফোল্ডারে সুন্দরভাবে ক্যাটাগরি করে রাখা হয়েছে যাতে মূল প্রজেক্ট রুট ফোল্ডার একদম ফ্রেশ থাকে।

---

## 🚀 Quick Execution Commands (জরুরি কমান্ডসমূহ)

1. **অ্যান্ড্রয়েড APK বিল্ড করতে:**
   ```powershell
   python app/pp_server/build_apk.py
   ```
2. **ব্যাকএন্ড সার্ভার চালাতে:**
   ```powershell
   python achievement_unlocker/app.py
   ```
3. **GitHub-এ আপডেট পুশ করতে:**
   ```powershell
   git -C achievement_unlocker add -A
   git -C achievement_unlocker commit -m "update message"
   git -C achievement_unlocker push origin main
   ```
