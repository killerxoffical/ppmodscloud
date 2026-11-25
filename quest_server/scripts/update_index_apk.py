with open('pp mod/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update updatePpmApkDownloadUrl
old_update_fn = """        // ==========================================
        // PPM CLOUD APK DOWNLOAD URL (Managed centrally from Server Admin)
        function updatePpmApkDownloadUrl() {
            try {
                const targetLink = 'https://pp-mod-auto-quest.onrender.com/download/PPM_Cloud.apk';
                const btn = document.getElementById("btnDownloadPpmApk");
                if (btn) btn.href = targetLink;
                const btnProfile = document.getElementById("btnDownloadPpmApkProfile");
                if (btnProfile) btnProfile.href = targetLink;
            } catch (e) {
                // Keep safe fallback
            }
        }"""

new_update_fn = """        // ==========================================
        // PPM CLOUD APK DOWNLOAD URL (Managed from Admin Panel)
        function updatePpmApkDownloadUrl() {
            try {
                let targetLink = '';
                if (window.ppfb && window.ppfb.config && window.ppfb.config.ppmServerApk) {
                    targetLink = (window.ppfb.config.ppmServerApk || '').trim();
                }
                if (!targetLink) {
                    try {
                        const c = JSON.parse(localStorage.getItem('pp_config_cache') || '{}');
                        if (c && c.ppmServerApk) targetLink = (c.ppmServerApk || '').trim();
                    } catch (e) { }
                }
                if (!targetLink) {
                    targetLink = (localStorage.getItem('pp_admin_apk_link') || '').trim();
                }

                const btn = document.getElementById("btnDownloadPpmApk");
                const btnProfile = document.getElementById("btnDownloadPpmApkProfile");

                const handleApkClick = function (e) {
                    if (!targetLink || targetLink === '#' || targetLink === '') {
                        e.preventDefault();
                        const msg = '⚠️ এডমিন এখনো APK Download Link কনফিগার করেনি। অনুগ্রহ করে সাপোর্টে যোগাযোগ করুন।';
                        if (typeof showToast === 'function') showToast(msg, 'warning');
                        else if (typeof showAlertModal === 'function') showAlertModal('Link Unavailable', msg);
                        else alert(msg);
                        return false;
                    }
                };

                if (btn) {
                    btn.href = targetLink || '#';
                    btn.target = targetLink ? '_blank' : '_self';
                    btn.onclick = function (e) {
                        if (!targetLink || targetLink === '#') return handleApkClick(e);
                        if (typeof claimAppDownloadReward === 'function') claimAppDownloadReward(e);
                    };
                }
                if (btnProfile) {
                    btnProfile.href = targetLink || '#';
                    btnProfile.target = targetLink ? '_blank' : '_self';
                    btnProfile.onclick = function (e) {
                        if (!targetLink || targetLink === '#') return handleApkClick(e);
                        if (typeof claimAppDownloadReward === 'function') claimAppDownloadReward(e);
                    };
                }
            } catch (e) { }
        }"""

if old_update_fn in text:
    text = text.replace(old_update_fn, new_update_fn, 1)
    print('[+] updatePpmApkDownloadUrl replaced with admin configured logic')
else:
    print('[-] old_update_fn not found')

# 2. Update applyConfig in pp mod/index.html
old_apply_block = """            const ppmApkBtn = document.getElementById('btnDownloadPpmApk');
            const targetApk = 'https://pp-mod-auto-quest.onrender.com/download/PPM_Cloud.apk';
            if (ppmApkBtn) ppmApkBtn.href = targetApk;
            const ppmProfileApkBtn = document.getElementById('btnDownloadPpmApkProfile');
            if (ppmProfileApkBtn) ppmProfileApkBtn.href = targetApk;"""

new_apply_block = """            if (cfg && cfg.ppmServerApk) {
                try { localStorage.setItem('pp_admin_apk_link', cfg.ppmServerApk.trim()); } catch (e) { }
            }
            if (typeof updatePpmApkDownloadUrl === 'function') updatePpmApkDownloadUrl();"""

if old_apply_block in text:
    text = text.replace(old_apply_block, new_apply_block, 1)
    print('[+] applyConfig updated to use admin configured apk link')
else:
    print('[-] old_apply_block not found')

with open('pp mod/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] pp mod/index.html written successfully')
