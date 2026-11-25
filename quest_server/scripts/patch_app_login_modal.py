import os
import sys

html_path = os.path.abspath("app/pp_server/assets/www/index.html")
with open(html_path, "r", encoding="utf-8") as f:
    c = f.read()

# 1. Add modal dialog markup
target1 = '''    <!-- ==================== LOGOUT & DELETE CONFIRM DIALOG ==================== -->
    <div class="dialog-overlay" id="dialogConfirm">
        <div class="dialog-box">
            <h4 class="dialog-h" id="dialogHeader">Confirm Action</h4>
            <p class="dialog-p" id="dialogBody">Are you sure you want to proceed?</p>
            <div class="dialog-btn-row">
                <button class="btn-dialog btn-dialog-cancel" onclick="closeConfirmDialog()">Cancel</button>
                <button class="btn-dialog btn-dialog-danger" id="btnDialogConfirm">Confirm</button>
            </div>
        </div>
    </div>'''

replacement1 = '''    <!-- ==================== LOGOUT & DELETE CONFIRM DIALOG ==================== -->
    <div class="dialog-overlay" id="dialogConfirm">
        <div class="dialog-box">
            <h4 class="dialog-h" id="dialogHeader">Confirm Action</h4>
            <p class="dialog-p" id="dialogBody">Are you sure you want to proceed?</p>
            <div class="dialog-btn-row">
                <button class="btn-dialog btn-dialog-cancel" onclick="closeConfirmDialog()">Cancel</button>
                <button class="btn-dialog btn-dialog-danger" id="btnDialogConfirm">Confirm</button>
            </div>
        </div>
    </div>

    <!-- ==================== PREMIUM LOGIN & 2-DEVICE ALERT MODAL ==================== -->
    <div class="dialog-overlay" id="dialogLoginAlert" style="z-index: 99999;">
        <div class="dialog-box" style="text-align: center; border-radius: 24px; padding: 26px 20px 22px; box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.35); border: 1px solid #e2e8f0; max-width: 340px; background: #ffffff;">
            <div id="loginAlertIconWrap" style="width: 64px; height: 64px; margin: 0 auto 16px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #fef2f2; border: 3px solid #fee2e2; transition: all 0.3s ease;">
                <svg id="loginAlertIconSvg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
            </div>
            <h4 class="dialog-h" id="loginAlertHeader" style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 8px;">লগইন সতর্কতা</h4>
            <p class="dialog-p" id="loginAlertBody" style="font-size: 13.5px; color: #334155; line-height: 1.55; margin-bottom: 14px; word-break: break-word; font-weight: 500;"></p>
            <div id="loginAlertTip" style="font-size: 11.5px; color: #475569; background: #f8fafc; padding: 10px 12px; border-radius: 12px; margin-bottom: 20px; border: 1px dashed #cbd5e1; text-align: left; line-height: 1.45;">
                🔒 <b>পরামর্শ:</b> আপনার আগের ডিভাইস থেকে অ্যাপটি Logout করুন অথবা নতুন একটি একাউন্ট দিয়ে পুনরায় লগইন চেষ্টা করুন।
            </div>
            <button type="button" class="btn-primary" style="width: 100%; height: 46px; font-size: 14.5px; font-weight: 700; border-radius: 14px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; border: none; cursor: pointer; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35); transition: transform 0.15s ease;" onclick="closeLoginAlertModal()" onmousedown="this.style.transform='scale(0.97)'" onmouseup="this.style.transform='scale(1)'">
                ঠিক আছে (OK)
            </button>
        </div>
    </div>'''

if target1 not in c:
    print("Error: Target 1 not found in index.html")
    sys.exit(1)

c = c.replace(target1, replacement1, 1)

# 2. Add window.onLoginError and closeLoginAlertModal
target2 = '''        function showLoginError(msg) {
            setLoginBtnLoading(false);
            var box = document.getElementById('loginAlertBox');
            box.textContent = msg;
            box.style.display = 'block';
            showToast("Login Failed: " + msg);
        }'''

replacement2 = '''        window.closeLoginAlertModal = function() {
            var modal = document.getElementById('dialogLoginAlert');
            if (modal) modal.classList.remove('open');
            setLoginBtnLoading(false);
            var passEl = document.getElementById('inputLoginPass');
            if (passEl) {
                passEl.value = '';
                passEl.focus();
            }
        };

        window.onLoginError = function(msg) {
            setLoginBtnLoading(false);
            var text = (msg || 'Login failed. Please check your credentials.').trim();

            // Always reset spinner and re-enable button immediately!
            var btn = document.getElementById('btnSubmitPpm');
            var txt = document.getElementById('btnSubmitPpmText');
            var spin = document.getElementById('loginSpinner');
            if (btn) btn.disabled = false;
            if (txt) txt.style.display = 'inline';
            if (spin) spin.style.display = 'none';

            // Populate inline alert box as secondary backup
            var box = document.getElementById('loginAlertBox');
            if (box) {
                box.textContent = text;
                box.style.display = 'block';
            }

            // Check if this is a 2-Device Lock error
            var isMultiDevice = text.indexOf('অন্য একটি ডিভাইসে') !== -1 || text.indexOf('ডিভাইস') !== -1 || text.toLowerCase().indexOf('device') !== -1;

            var headerEl = document.getElementById('loginAlertHeader');
            var bodyEl = document.getElementById('loginAlertBody');
            var iconWrap = document.getElementById('loginAlertIconWrap');
            var iconSvg = document.getElementById('loginAlertIconSvg');
            var tipEl = document.getElementById('loginAlertTip');
            var modal = document.getElementById('dialogLoginAlert');

            if (isMultiDevice) {
                if (headerEl) headerEl.textContent = 'ডিভাইস অ্যাক্সেস লক';
                if (iconWrap) {
                    iconWrap.style.background = '#fffbeb';
                    iconWrap.style.borderColor = '#fde68a';
                }
                if (iconSvg) {
                    iconSvg.setAttribute('stroke', '#d97706');
                    iconSvg.innerHTML = '<rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line>';
                }
                if (tipEl) {
                    tipEl.style.display = 'block';
                    tipEl.innerHTML = '🔒 <b>পরামর্শ:</b> এই একাউন্টটি অন্য একটি ফোনে লগইন করা আছে। নতুন ফোনে লগইন করতে হলে আগের ফোন থেকে একাউন্টটি Logout করুন অথবা এডমিনের সাথে যোগাযোগ করে সেশন রিসেট করুন।';
                }
            } else {
                if (headerEl) headerEl.textContent = 'লগইন ব্যর্থ হয়েছে';
                if (iconWrap) {
                    iconWrap.style.background = '#fef2f2';
                    iconWrap.style.borderColor = '#fee2e2';
                }
                if (iconSvg) {
                    iconSvg.setAttribute('stroke', '#ef4444');
                    iconSvg.innerHTML = '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>';
                }
                if (tipEl) {
                    tipEl.style.display = 'block';
                    tipEl.innerHTML = '💡 <b>পরামর্শ:</b> আপনার ইমেইল ও পাসওয়ার্ড সঠিক আছে কিনা পরীক্ষা করুন, অথবা নতুন আরেকটি একাউন্ট বসিয়ে লগইন চেষ্টা করুন।';
                }
            }

            if (bodyEl) bodyEl.textContent = text;
            if (modal) modal.classList.add('open');
        };

        function showLoginError(msg) {
            window.onLoginError(msg);
        }'''

if target2 not in c:
    print("Error: Target 2 not found in index.html")
    sys.exit(1)

c = c.replace(target2, replacement2, 1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(c)

print("Successfully patched app/pp_server/assets/www/index.html with premium modal and spinner reset!")
