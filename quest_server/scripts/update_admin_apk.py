# Update pp mod/admin.html

with open('pp mod/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add APK Download Link card in admin.html under data-cfgsec="links"
apk_card_html = """                        <!-- Dedicated PPM Cloud APK Download Link Card -->
                        <div class="glass p-4 sm:p-6 space-y-3 border-2 border-indigo-200 bg-indigo-50/20" data-cfgsec="links">
                            <div class="flex items-center justify-between border-b border-slate-100 pb-2">
                                <div>
                                    <h4 class="text-xs font-black uppercase tracking-wider text-indigo-700 flex items-center gap-1.5">
                                        <i data-lucide="download" class="w-4 h-4"></i>
                                        <span>PPM Cloud APK Download Link (Admin Configured)</span>
                                    </h4>
                                    <p class="text-[11px] text-slate-500 font-semibold mt-0.5">
                                        ইউজার ওয়েব অ্যাপের "Download APK" বাটনে চাপলে সরাসরি আপনার দেওয়া এই লিংকে যাবে (Drive, MediaFire, বা আপনার যেকোনো কাস্টম ডিরেক্ট লিংক)।
                                    </p>
                                </div>
                            </div>
                            <div>
                                <label class="lbl">Official APK Download URL</label>
                                <input id="cfgPpmServerApk" class="fld font-mono text-xs" placeholder="https://drive.google.com/... বা আপনার দেওয়া যেকোনো লিংক">
                            </div>
                            <button onclick="saveApkDownloadLink(this)" class="btn bg-indigo-600 hover:bg-indigo-700 text-white font-bold w-full py-2.5 btn-save-premium">
                                💾 Save APK Download Link
                            </button>
                        </div>

"""

if 'id="cfgPpmServerApk"' not in text:
    # insert before <div class="glass p-4 sm:p-6 space-y-3" data-cfgsec="links">
    marker = '<div class="glass p-4 sm:p-6 space-y-3" data-cfgsec="links">'
    pos = text.find(marker)
    if pos != -1:
        text = text[:pos] + apk_card_html + text[pos:]
        print('[+] Added cfgPpmServerApk card to admin.html')
    else:
        print('[-] marker for cfgPpmServerApk card not found')
else:
    print('[=] cfgPpmServerApk card already present in admin.html')

# 2. Add set('cfgPpmServerApk', c.ppmServerApk || ''); in fillConfigForm
if "set('cfgPpmServerApk'" not in text:
    target_fill = "set('cfgNotice', c.notice || '');"
    pos_fill = text.find(target_fill)
    if pos_fill != -1:
        text = text[:pos_fill] + "set('cfgPpmServerApk', c.ppmServerApk || '');\n            " + text[pos_fill:]
        print('[+] Added cfgPpmServerApk to fillConfigForm in admin.html')
    else:
        print('[-] target_fill not found')
else:
    print('[=] cfgPpmServerApk already in fillConfigForm')

# 3. Add saveApkDownloadLink function in admin.html
save_apk_fn = """        window.saveApkDownloadLink = async function (btn) {
            const val = (document.getElementById('cfgPpmServerApk').value || '').trim();
            await secSave(btn, { ppmServerApk: val }, 'APK Download Link saved successfully!');
        };

"""

if 'function saveApkDownloadLink' not in text:
    target_sec = 'async function secSave(btn, payload, msg) {'
    pos_sec = text.find(target_sec)
    if pos_sec != -1:
        text = text[:pos_sec] + save_apk_fn + text[pos_sec:]
        print('[+] Added saveApkDownloadLink function in admin.html')
    else:
        print('[-] target_sec not found')
else:
    print('[=] saveApkDownloadLink already present')

with open('pp mod/admin.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] admin.html written successfully')
