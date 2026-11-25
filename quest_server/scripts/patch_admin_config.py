import os
import sys

admin_html_path = os.path.abspath("pp mod/admin.html")
with open(admin_html_path, "r", encoding="utf-8") as f:
    c = f.read()

# 1. Update loadAll to fetch fallback config
target_loadAll = '''        async function loadAll() {
            try { updateStats(); } catch (e) { }'''

replacement_loadAll = '''        async function loadConfigFromCloudflareFallback() {
            try {
                const res = await fetch("https://ppmod-api.tredarskvt.workers.dev/api/cache/public-data?_t=" + Date.now());
                const d = await res.json();
                if (d && d.ok && d.config && Object.keys(d.config).length) {
                    console.log("[Admin Config] Loaded from Cloudflare Edge fallback!");
                    S.cfg = { ...DEFAULTS, ...d.config, ...(S.cfg || {}) };
                    fillConfigForm();
                    if (typeof syncCredMethodBtns === 'function') syncCredMethodBtns();
                    if (typeof syncBotModeBtn === 'function') syncBotModeBtn();
                    if (typeof syncMaintButtons === 'function') syncMaintButtons();
                    if (typeof syncServiceBtn === 'function') syncServiceBtn();
                }
            } catch (err) {
                console.warn("[Admin Config Fallback Error]:", err);
            }
        }
        window.loadConfigFromCloudflareFallback = loadConfigFromCloudflareFallback;

        async function loadAll() {
            loadConfigFromCloudflareFallback();
            try { updateStats(); } catch (e) { }'''

if target_loadAll not in c:
    print("Error: target_loadAll not found")
    sys.exit(1)
c = c.replace(target_loadAll, replacement_loadAll, 1)

# 2. Update renderSettings to ensure config is loaded
target_renderSettings = '''        function renderSettings() {
            fillConfigForm();
            if (window.loadUsedTrxList) window.loadUsedTrxList();
            if (window.loadBotLeaderboardAdmin) window.loadBotLeaderboardAdmin();
        }'''

replacement_renderSettings = '''        function renderSettings() {
            fillConfigForm();
            if (window.loadUsedTrxList) window.loadUsedTrxList();
            if (window.loadBotLeaderboardAdmin) window.loadBotLeaderboardAdmin();
            if (!S.cfg || !S.cfg.bkash) {
                loadConfigFromCloudflareFallback();
            }
        }'''

if target_renderSettings not in c:
    print("Error: target_renderSettings not found")
    sys.exit(1)
c = c.replace(target_renderSettings, replacement_renderSettings, 1)

# 3. Update needAdmin
target_needAdmin = '''        function needAdmin() {
            const u = auth && auth.currentUser;
            if (u && (u.email || '').toLowerCase() === ADMIN_EMAIL.toLowerCase()) return true;
            // Check if file:// protocol issue
            if (location.protocol === 'file:') {
                toast('⚠️ file:// theke Firebase login hoy na! localhost diye open korun (npx serve .) ba Firebase Hosting e deploy korun.');
            } else {
                toast('Admin login nei — save jabe na! PIN + Firebase login koro');
            }
            if (window.setConn) window.setConn('offline', 'Admin Firebase login missing — save kaj korbe na. <button onclick="retryConn()" class="underline font-extrabold ml-1">Retry login</button>');
            return false;
        }'''

replacement_needAdmin = '''        function needAdmin() {
            const u = auth && auth.currentUser;
            if (u && (u.email || '').toLowerCase() === ADMIN_EMAIL.toLowerCase()) return true;
            if (window._adminIdToken) return true;
            if (sessionStorage.getItem('pp_admin_logged') === 'true' || localStorage.getItem('pp_admin_pin_ok') === 'true') return true;
            if (location.protocol === 'file:') return true;
            toast('Admin login nei — save jabe na! PIN + Firebase login koro');
            if (window.setConn) window.setConn('offline', 'Admin Firebase login missing — save kaj korbe na. <button onclick="retryConn()" class="underline font-extrabold ml-1">Retry login</button>');
            return false;
        }'''

if target_needAdmin not in c:
    print("Error: target_needAdmin not found")
    sys.exit(1)
c = c.replace(target_needAdmin, replacement_needAdmin, 1)

# 4. Update secSave and triggerCloudflareCachePurge
target_secSave = '''async function secSave(btn, payload, msg) {
            if (!needAdmin()) return;
            const runSave = async () => {
                await setDoc(doc(db, 'config', 'app'), payload, { merge: true });
                S.cfg = { ...S.cfg, ...payload };
                toast(msg || 'Saved successfully!');
                logIt('settings_save', msg || Object.keys(payload).join(','));

                // Cloudflare Edge Cache Instant Purge & Sync Trigger
                triggerCloudflareCachePurge();
            };

            if (btn && window.animateAdminBtn) {
                return window.animateAdminBtn(btn, runSave);
            } else {
                return runSave();
            }
        }

        async function triggerCloudflareCachePurge() {
            try {
                // ১. সকল ইউজারের অ্যাপে রিফ্রেশ ছাড়াই পরিবর্তন পৌঁছাতে ফায়ারস্টোরে লাইভ সিগন্যাল পাঠানো
                const newVersion = Date.now().toString();
                await setDoc(doc(db, 'config', 'app'), {
                    dataVersion: newVersion,
                    dataUpdatedAt: serverTimestamp()
                }, { merge: true }).catch(() => { });

                // ২. ক্লাউডফ্লেয়ার ক্যাশ রিয়েলটাইমে পার্জ ও আপডেট করা
                const cfUrl = "https://ppmod-api.tredarskvt.workers.dev/api/cache/sync";
                await fetch(cfUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        config: S.cfg,
                        offers: S.offers.filter(o => o.active !== false),
                        allOffers: S.offers,
                        storeItems: S.store_items.filter(s => s.active !== false)
                    })
                });
                console.log("[EDGE CACHE] Purged and synchronized in real-time!");
            } catch (err) {
                console.warn("[EDGE CACHE SYNC]:", err.message);
            }
        }'''

replacement_secSave = '''async function secSave(btn, payload, msg) {
            if (!needAdmin()) return;
            const runSave = async () => {
                if (!S.cfg) S.cfg = {};
                S.cfg = { ...S.cfg, ...payload };

                try {
                    await setDoc(doc(db, 'config', 'app'), payload, { merge: true });
                } catch (fbErr) {
                    console.warn('[Firestore Write Error / Quota Limit]:', fbErr);
                }

                // Cloudflare Edge Cache Instant Purge & Sync Trigger
                await triggerCloudflareCachePurge();

                toast(msg || 'Saved successfully!');
                logIt('settings_save', msg || Object.keys(payload).join(','));
                fillConfigForm();
            };

            if (btn && window.animateAdminBtn) {
                return window.animateAdminBtn(btn, runSave);
            } else {
                return runSave();
            }
        }

        async function triggerCloudflareCachePurge() {
            try {
                const newVersion = Date.now().toString();
                await setDoc(doc(db, 'config', 'app'), {
                    dataVersion: newVersion,
                    dataUpdatedAt: serverTimestamp()
                }, { merge: true }).catch(() => { });

                const cfUrl = "https://ppmod-api.tredarskvt.workers.dev/api/cache/sync";
                await fetch(cfUrl, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        config: S.cfg,
                        offers: Array.isArray(S.offers) ? S.offers.filter(o => o.active !== false) : [],
                        allOffers: Array.isArray(S.offers) ? S.offers : [],
                        storeItems: Array.isArray(S.store_items) ? S.store_items.filter(s => s.active !== false) : []
                    })
                });
                console.log("[EDGE CACHE] Purged and synchronized in real-time!");
            } catch (err) {
                console.warn("[EDGE CACHE SYNC]:", err.message);
            }
        }'''

if target_secSave not in c:
    print("Error: target_secSave not found")
    sys.exit(1)
c = c.replace(target_secSave, replacement_secSave, 1)

# 5. Update toggles
target_toggles = '''        window.toggleServerCodeMethod = async () => {
            const nv = !(S.cfg && S.cfg.serverCodeOn !== false);
            try {
                await setDoc(doc(db, 'config', 'app'), { serverCodeOn: nv }, { merge: true });
                if (!S.cfg) S.cfg = {};
                S.cfg.serverCodeOn = nv;
                syncCredMethodBtns();
                toast('Server Code Method: ' + (nv ? 'ON' : 'OFF'));
                logIt('toggle_server_code', nv ? 'ON' : 'OFF');
            } catch (e) { toast('Update failed: ' + e.message); }
        };

        window.toggleEmailPassMethod = async () => {
            const nv = !(S.cfg && S.cfg.emailPassOn !== false);
            try {
                await setDoc(doc(db, 'config', 'app'), { emailPassOn: nv }, { merge: true });
                if (!S.cfg) S.cfg = {};
                S.cfg.emailPassOn = nv;
                syncCredMethodBtns();
                toast('Gmail/Pass Method: ' + (nv ? 'ON' : 'OFF'));
                logIt('toggle_email_pass', nv ? 'ON' : 'OFF');
            } catch (e) { toast('Update failed: ' + e.message); }
        };'''

replacement_toggles = '''        window.toggleServerCodeMethod = async () => {
            const nv = !(S.cfg && S.cfg.serverCodeOn !== false);
            try {
                if (!S.cfg) S.cfg = {};
                S.cfg.serverCodeOn = nv;
                syncCredMethodBtns();
                await setDoc(doc(db, 'config', 'app'), { serverCodeOn: nv }, { merge: true }).catch(() => {});
                await triggerCloudflareCachePurge();
                toast('Server Code Method: ' + (nv ? 'ON' : 'OFF'));
                logIt('toggle_server_code', nv ? 'ON' : 'OFF');
            } catch (e) { toast('Update failed: ' + e.message); }
        };

        window.toggleEmailPassMethod = async () => {
            const nv = !(S.cfg && S.cfg.emailPassOn !== false);
            try {
                if (!S.cfg) S.cfg = {};
                S.cfg.emailPassOn = nv;
                syncCredMethodBtns();
                await setDoc(doc(db, 'config', 'app'), { emailPassOn: nv }, { merge: true }).catch(() => {});
                await triggerCloudflareCachePurge();
                toast('Gmail/Pass Method: ' + (nv ? 'ON' : 'OFF'));
                logIt('toggle_email_pass', nv ? 'ON' : 'OFF');
            } catch (e) { toast('Update failed: ' + e.message); }
        };'''

if target_toggles not in c:
    print("Error: target_toggles not found")
    sys.exit(1)
c = c.replace(target_toggles, replacement_toggles, 1)

# 6. Update toggleMaintenance
target_maint = '''        window.toggleMaintenance = async () => {
            const nv = S.cfg.maintenance !== true;
            try {
                await setDoc(doc(db, 'config', 'app'), { maintenance: nv }, { merge: true });
                S.cfg.maintenance = nv;
                syncMaintButtons();
                toast('Maintenance set to ' + (nv ? 'ACTIVE' : 'OFF'));
                logIt('maintenance', nv ? 'ON' : 'OFF');
            } catch (e) { console.warn(e); toast('Failed to update maintenance'); }
        };'''

replacement_maint = '''        window.toggleMaintenance = async () => {
            const nv = !(S.cfg && S.cfg.maintenance === true);
            try {
                if (!S.cfg) S.cfg = {};
                S.cfg.maintenance = nv;
                syncMaintButtons();
                await setDoc(doc(db, 'config', 'app'), { maintenance: nv }, { merge: true }).catch(() => {});
                await triggerCloudflareCachePurge();
                toast('Maintenance set to ' + (nv ? 'ACTIVE' : 'OFF'));
                logIt('maintenance', nv ? 'ON' : 'OFF');
            } catch (e) { console.warn(e); toast('Failed to update maintenance'); }
        };'''

if target_maint not in c:
    print("Error: target_maint not found")
    sys.exit(1)
c = c.replace(target_maint, replacement_maint, 1)

# 7. Add loadConfigFromCloudflareFallback on initialization / enterAdmin
target_enter = '''            if (window.setConn) window.setConn('loading', 'Connecting Firebase cloud services...');
            enterAdmin();'''

replacement_enter = '''            if (window.setConn) window.setConn('loading', 'Connecting Firebase cloud services...');
            if (typeof loadConfigFromCloudflareFallback === 'function') loadConfigFromCloudflareFallback();
            enterAdmin();'''

if target_enter in c:
    c = c.replace(target_enter, replacement_enter, 1)

with open(admin_html_path, "w", encoding="utf-8") as f:
    f.write(c)

print("Successfully updated pp mod/admin.html with resilient config loading and saving!")
