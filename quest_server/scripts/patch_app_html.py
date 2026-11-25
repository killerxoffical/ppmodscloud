with open('app/pp_server/assets/www/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update CSS for .home-topbar, .settings-topbar, .topbar-logo-box, .btn-tutorial-trigger
old_css_target = '''.home-topbar {
            background: #ffffff;
            border-bottom: 1px solid rgba(226, 232, 240, 0.65);
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            z-index: 40;
            flex-shrink: 0;
        }'''

new_css_target = '''.home-topbar {
            background: #ffffff url('hd.png') center center / 100% 100% no-repeat !important;
            border-bottom: 1.5px solid rgba(226, 232, 240, 0.8);
            border-bottom-left-radius: 22px;
            border-bottom-right-radius: 22px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.05);
            padding: 10px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            z-index: 40;
            flex-shrink: 0;
        }

        .settings-topbar {
            background: #ffffff url('hd.png') center center / 100% 100% no-repeat !important;
        }

        .topbar-logo-box {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            border: 2.5px solid #eab308;
            box-shadow: 0 0 14px rgba(234, 179, 8, 0.5);
            flex-shrink: 0;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0f172a;
            transition: border-color 0.4s ease, box-shadow 0.4s ease, transform 0.2s ease;
            animation: profilePulseGlow 3s infinite ease-in-out;
        }

        .topbar-logo-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transform: scale(1.24);
            border-radius: 9px;
        }

        .btn-tutorial-trigger {
            margin-top: 14px;
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #ffffff;
            border: none;
            border-radius: 13px;
            padding: 11px 18px;
            font-size: 13px;
            font-weight: 800;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.2s ease;
            width: 100%;
            max-width: 290px;
        }

        .btn-tutorial-trigger:active {
            transform: scale(0.96);
        }'''

assert old_css_target in html, "old_css_target not found!"
html = html.replace(old_css_target, new_css_target, 1)

# 2. Update topbar HTML to wrap logo in .topbar-logo-box
old_home_logo = '<img id="topbarUserLogo" src="logo.png" alt="Profile" class="topbar-logo-img" onerror="this.src=\'logo.png\'">'
new_home_logo = '<div class="topbar-logo-box"><img id="topbarUserLogo" src="logo.png" alt="Profile" onerror="this.src=\'logo.png\'"></div>'
assert old_home_logo in html, "old_home_logo not found!"
html = html.replace(old_home_logo, new_home_logo, 1)

old_settings_logo = '<img id="topbarUserLogoSettings" src="logo.png" alt="Profile" class="topbar-logo-img" onerror="this.src=\'logo.png\'">'
new_settings_logo = '<div class="topbar-logo-box"><img id="topbarUserLogoSettings" src="logo.png" alt="Profile" onerror="this.src=\'logo.png\'"></div>'
assert old_settings_logo in html, "old_settings_logo not found!"
html = html.replace(old_settings_logo, new_settings_logo, 1)

# 3. Add video guide button to homeEmptyState
old_empty = '''                    <h4 class="empty-home-title">No Google Accounts Connected</h4>
                    <p class="empty-home-sub">Tap "+" below to connect your Google Play account and generate your QID.</p>
                </div>'''

new_empty = '''                    <h4 class="empty-home-title">No Google Accounts Connected</h4>
                    <p class="empty-home-sub">Tap "+" below to connect your Google Play account and generate your QID.</p>

                    <!-- Video Guide Trigger Button -->
                    <button type="button" onclick="openVideoGuideModal()" class="btn-tutorial-trigger">
                        <span style="font-size:17px;">🎬</span>
                        <span>কীভাবে অ্যাপ ব্যবহার করব? (ভিডিও)</span>
                        <span style="font-size:14px; opacity:0.8; margin-left:4px;">→</span>
                    </button>
                </div>'''

assert old_empty in html, "old_empty not found!"
html = html.replace(old_empty, new_empty, 1)

# 4. Add video guide button in viewSettings
old_settings_btn = '''<button class="btn-settings-logout btn-premium-logout" id="btnSettingsLogout" onclick="promptLogout()">'''

new_settings_btn = '''<button type="button" class="btn-settings-action btn-settings-video" onclick="openVideoGuideModal()" style="background:linear-gradient(135deg, rgba(2,132,199,0.08), rgba(14,165,233,0.12)); border:1.5px solid rgba(2,132,199,0.35); color:#0284c7; margin-bottom:12px; display:flex; align-items:center; gap:10px; width:100%; padding:12px 14px; border-radius:14px; cursor:pointer;">
                    <span style="font-size:18px;">🎬</span>
                    <span style="font-weight:800; font-size:13px;">কীভাবে ব্যবহার করবেন? (ভিডিও গাইড)</span>
                    <span style="margin-left:auto; font-weight:bold; opacity:0.7;">→</span>
                </button>

                <button class="btn-settings-logout btn-premium-logout" id="btnSettingsLogout" onclick="promptLogout()">'''

assert old_settings_btn in html, "old_settings_btn not found!"
html = html.replace(old_settings_btn, new_settings_btn, 1)

# 5. Append #viewVideoGuide modal and JS handlers before </body>
video_modal_html = '''
    <!-- ==================== VIDEO TUTORIAL MODAL ==================== -->
    <div id="viewVideoGuide" style="display:none; position:fixed; inset:0; background:#0b1120; z-index:99999; flex-direction:column; overflow-y:auto; -webkit-overflow-scrolling:touch;">
        <div style="display:flex; align-items:center; justify-content:space-between; padding:14px 16px; background:#0f172a; border-bottom:1px solid rgba(255,255,255,0.08); position:sticky; top:0; z-index:10;">
            <button type="button" onclick="closeVideoGuideModal()" style="display:flex; align-items:center; gap:6px; background:rgba(255,255,255,0.1); border:none; color:#f8fafc; font-size:13px; font-weight:700; padding:8px 14px; border-radius:10px; cursor:pointer;">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5">
                    <line x1="19" y1="12" x2="5" y2="12"></line>
                    <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                <span>ফিরে যান</span>
            </button>
            <h3 style="margin:0; font-size:15px; font-weight:800; color:#f8fafc; text-align:center;">অ্যাপ সেটআপ ভিডিও গাইড</h3>
            <div style="width:40px;"></div>
        </div>

        <div style="padding:16px; max-width:540px; margin:0 auto; width:100%; box-sizing:border-box;">
            <div style="background:#1e293b; border-radius:16px; overflow:hidden; box-shadow:0 12px 32px rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.1);">
                <video id="appTutorialVideo" controls playsinline preload="metadata" style="width:100%; display:block; aspect-ratio:16/9; background:#000;">
                    <source src="https://pub-4c6b2dbf3a0c4862a8964b1546de6283.r2.dev/ppmods/pp_cloud_app_setup.mp4" type="video/mp4">
                    Your phone does not support HTML5 video.
                </video>
            </div>

            <div style="margin-top:16px; background:rgba(30,41,59,0.7); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:16px;">
                <h4 style="margin:0 0 10px; font-size:14px; font-weight:800; color:#38bdf8; display:flex; align-items:center; gap:8px;">
                    <span>💡</span>
                    <span>সহজ ৩টি ধাপে সেটআপ করুন:</span>
                </h4>
                <div style="display:flex; flex-direction:column; gap:10px; font-size:12.5px; color:#cbd5e1; line-height:1.5;">
                    <div style="display:flex; gap:10px;">
                        <span style="width:22px; height:22px; border-radius:50%; background:#0284c7; color:#fff; font-size:11px; font-weight:bold; display:flex; align-items:center; justify-content:center; flex-shrink:0;">1</span>
                        <span>নিচের বড় <strong>"+" বাটন</strong> চাপ দিয়ে আপনার যে কোনো গুগল প্লে অ্যাকাউন্ট সিলেক্ট করুন।</span>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <span style="width:22px; height:22px; border-radius:50%; background:#0284c7; color:#fff; font-size:11px; font-weight:bold; display:flex; align-items:center; justify-content:center; flex-shrink:0;">2</span>
                        <span>অ্যাকাউন্ট যুক্ত হওয়ার সাথে সাথে স্ক্রিনে একটি <strong>৬ ডিজিটের QID কোড</strong> তৈরি হবে।</span>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <span style="width:22px; height:22px; border-radius:50%; background:#0284c7; color:#fff; font-size:11px; font-weight:bold; display:flex; align-items:center; justify-content:center; flex-shrink:0;">3</span>
                        <span>এই কোডটি কপি করে <strong>PP Mod ওয়েবসাইটে</strong> বসিয়ে পয়েন্ট ক্লেইম করুন!</span>
                    </div>
                </div>
            </div>

            <button type="button" onclick="closeVideoGuideModal()" style="margin-top:20px; width:100%; padding:14px; border-radius:14px; background:linear-gradient(135deg, #0284c7, #0369a1); border:none; color:#fff; font-size:14px; font-weight:800; cursor:pointer; box-shadow:0 4px 14px rgba(2,132,199,0.4);">
                ← মূল পেজে ফিরে যান
            </button>
        </div>
    </div>

    <script>
    function openVideoGuideModal() {
        var el = document.getElementById('viewVideoGuide');
        if (el) el.style.display = 'flex';
        var vid = document.getElementById('appTutorialVideo');
        if (vid) {
            vid.currentTime = 0;
            vid.play().catch(function(){});
        }
    }

    function closeVideoGuideModal() {
        var vid = document.getElementById('appTutorialVideo');
        if (vid) {
            vid.pause();
        }
        var el = document.getElementById('viewVideoGuide');
        if (el) el.style.display = 'none';
    }
    </script>
</body>'''

assert '</body>' in html, "</body> tag not found!"
html = html.replace('</body>', video_modal_html, 1)

with open('app/pp_server/assets/www/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('achievement_unlocker/app/pp_server/assets/www/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated app/pp_server/assets/www/index.html and synced successfully!")
