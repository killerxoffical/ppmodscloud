# 1. Clean up pp mod/admin.html - remove duplicate cfgPpmServerApk
with open('pp mod/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

card_marker = '<!-- Dedicated PPM Cloud APK Download Link Card -->'
if card_marker in text:
    end_marker = '</div>\n\n'
    pos_start = text.find(card_marker)
    pos_end = text.find('</div>', pos_start)
    if pos_end != -1:
        # find the outer closing div
        pos_outer_end = text.find('</div>', pos_end + 6)
        if pos_outer_end != -1:
            text = text[:pos_start] + text[pos_outer_end + 6:]
            print('[+] Removed duplicate cfgPpmServerApk card from admin.html')

# remove fillConfigForm cfgPpmServerApk
text = text.replace("set('cfgPpmServerApk', c.ppmServerApk || '');\n            ", "")
# remove window.saveApkDownloadLink
if 'window.saveApkDownloadLink' in text:
    save_marker = 'window.saveApkDownloadLink = async function (btn) {'
    pos_save = text.find(save_marker)
    if pos_save != -1:
        pos_save_end = text.find('};', pos_save)
        if pos_save_end != -1:
            text = text[:pos_save] + text[pos_save_end + 2:]
            print('[+] Removed saveApkDownloadLink from admin.html')

with open('pp mod/admin.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] admin.html cleaned up successfully')

# 2. Update pp mod/index.html to fetch and use Server Admin's download_url directly
with open('pp mod/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

new_update_fn = """        // ==========================================
        // PPM CLOUD APK DOWNLOAD URL (Sourced directly from Server Admin)
        async function updatePpmApkDownloadUrl() {
            try {
                let targetLink = localStorage.getItem('pp_server_apk_download_link') || '';

                // Server Admin এপিআই থেকে সেন্ট্রাল ডাউনলোড লিংক ফেচ
                try {
                    const res = await fetch('https://pp-mod-auto-quest.onrender.com/api/app/version', { cache: 'no-store' });
                    const verData = await res.json();
                    if (verData && verData.ok && verData.download_url) {
                        targetLink = verData.download_url.trim();
                        localStorage.setItem('pp_server_apk_download_link', targetLink);
                    }
                } catch (e) { }

                const btn = document.getElementById("btnDownloadPpmApk");
                const btnProfile = document.getElementById("btnDownloadPpmApkProfile");

                const handleApkClick = function (e) {
                    if (!targetLink || targetLink === '#' || targetLink === '') {
                        e.preventDefault();
                        const msg = '⚠️ সার্ভার এডমিন এখনো APK Download Link কনফিগার করেনি। অনুগ্রহ করে সাপোর্টে যোগাযোগ করুন।';
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
        }
        window.updatePpmApkDownloadUrl = updatePpmApkDownloadUrl;
        window.refreshPpmApkDownloadUrl = updatePpmApkDownloadUrl;
        setTimeout(updatePpmApkDownloadUrl, 300);
"""

# replace updatePpmApkDownloadUrl in index.html
start_marker = '// PPM CLOUD APK DOWNLOAD URL (Managed from Admin Panel)'
pos_start = text.find(start_marker)
if pos_start == -1:
    start_marker = '// PPM CLOUD APK DOWNLOAD URL'
    pos_start = text.find(start_marker)

if pos_start != -1:
    pos_end = text.find('// PPM SERVER APP FIRST TIME DOWNLOAD REWARD', pos_start)
    if pos_end != -1:
        text = text[:pos_start] + new_update_fn + "\n        " + text[pos_end:]
        print('[+] index.html updatePpmApkDownloadUrl connected directly to Server Admin')
    else:
        print('[-] pos_end not found')
else:
    print('[-] start_marker not found')

with open('pp mod/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] index.html updated successfully')
