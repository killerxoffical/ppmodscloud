# PPM CLOUD (Pure Cloudflare Native Platform)

This is the independent, new-generation version of the PP MOD platform, designed to operate **100% on Cloudflare** with zero Firebase dependencies.

---

## 📁 Directory Architecture

```text
ppmclode/
│
├── 📁 web/                  --> Frontend Web App (index.html, admin.html, assets)
│                               - Cleaned and prepared for Pure Cloudflare Auth & D1 REST API.
│                               - Super fast static delivery via Cloudflare Pages.
│
├── 📁 cloudflare_backend/   --> Cloudflare Workers & D1 Database Engine
│   ├── schema.sql           --> Complete Serverless SQLite relational database schema.
│   ├── worker.js            --> Cloudflare worker script for API & endpoints.
│   └── Coud f warker page.txt --> Baseline reference worker routines.
│
├── 📁 quest_server/         --> Render Python Auto-Quest Unlocker Engine
│   ├── app.py               --> FastAPI / Flask backend for Google Play Quest Unlock API.
│   ├── requirements.txt     --> Python dependencies.
│   ├── render.yaml          --> Render deployment configuration.
│   └── app_version_config.json --> Cloud App version control (v5.0 Build 7).
│
└── 📁 app/                  --> Android Application Sources & Binaries
    ├── pp_server/           --> Android app source for PPM Cloud / Token Finder.
    ├── payment_gateway/     --> Payment Gateway APK sources.
    └── PPM_Cloud.apk        --> Latest release APK (v5.0 Build 7).
```

---

## 🎯 Architecture Goals

1. **Zero Firebase Dependencies:** All user authentication, data queries, and wallet balances live in Cloudflare D1 SQL.
2. **5 Million Free Reads/Day:** Unlimited scalability without database billings or permission errors.
3. **Completely Independent:** Has its own separate GitHub repository, separate Cloudflare account, and separate Render deployment without touching legacy systems.
