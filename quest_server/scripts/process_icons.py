import os
from PIL import Image

p_icon = r'C:/Users/Rubel/.gemini/antigravity/brain/82c3e0ad-9642-43f4-89f2-94725dd7f840/.user_uploaded/media_1795579459831_82f29a65.jpg'
p_notify = r'C:/Users/Rubel/.gemini/antigravity/brain/82c3e0ad-9642-43f4-89f2-94725dd7f840/.user_uploaded/media_1795579751859_c5f35bd3.png'

# 1. Process App Icon
img_icon = Image.open(p_icon).convert("RGBA")

icon_targets = [
    # root app
    ('app/pp_server/res/drawable/ic_launcher.png', (192, 192)),
    ('app/pp_server/res/drawable/ic_launcher_48.png', (48, 48)),
    ('app/pp_server/res/drawable/ic_launcher_96.png', (96, 96)),
    ('app/pp_server/res/drawable/ic_launcher_192.png', (192, 192)),
    ('app/pp_server/res/drawable/ic_launcher_round.png', (192, 192)),
    ('app/pp_server/res/drawable/ic_launcher_user.png', (192, 192)),
    ('app/pp_server/res/drawable/ic_launcher_user_round.png', (192, 192)),
    ('app/pp_server/assets/www/logo.png', (512, 512)),
    ('app/pp_server/assets/www/logo_user.png', (512, 512)),
    # achievement_unlocker
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher.png', (192, 192)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher_48.png', (48, 48)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher_96.png', (96, 96)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher_192.png', (192, 192)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher_round.png', (192, 192)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher_user.png', (192, 192)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_launcher_user_round.png', (192, 192)),
    ('achievement_unlocker/app/pp_server/assets/www/logo.png', (512, 512)),
    ('achievement_unlocker/app/pp_server/assets/www/logo_user.png', (512, 512)),
    ('achievement_unlocker/static/images/pp_logo.png', (512, 512)),
]

for t_path, (w, h) in icon_targets:
    os.makedirs(os.path.dirname(t_path), exist_ok=True)
    resized = img_icon.resize((w, h), Image.Resampling.LANCZOS)
    resized.save(t_path, "PNG")
    print(f"Saved app icon to {t_path} ({w}x{h})")

# 2. Process Notification Small Icon (pure white silhouette on transparent canvas)
img_notify = Image.open(p_notify).convert("RGBA")
bbox = img_notify.getbbox()
if bbox:
    cropped = img_notify.crop(bbox)
else:
    cropped = img_notify

# Force all visible pixels to pure solid white (#FFFFFF) keeping alpha
r, g, b, a = cropped.split()
# Make r, g, b all 255
white = Image.new("L", cropped.size, 255)
pure_white = Image.merge("RGBA", (white, white, white, a))

# Place on square transparent canvas with padding (15% padding)
w, h = pure_white.size
dim = max(w, h)
pad = int(dim * 0.15)
canvas_dim = dim + pad * 2
canvas = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
offset = ((canvas_dim - w) // 2, (canvas_dim - h) // 2)
canvas.paste(pure_white, offset, pure_white)

notify_targets = [
    ('app/pp_server/res/drawable/ic_notification.png', (96, 96)),
    ('app/pp_server/res/drawable/ic_stat_notify.png', (96, 96)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_notification.png', (96, 96)),
    ('achievement_unlocker/app/pp_server/res/drawable/ic_stat_notify.png', (96, 96)),
]

for t_path, (nw, nh) in notify_targets:
    os.makedirs(os.path.dirname(t_path), exist_ok=True)
    res_n = canvas.resize((nw, nh), Image.Resampling.LANCZOS)
    res_n.save(t_path, "PNG")
    print(f"Saved notification icon to {t_path} ({nw}x{nh})")

print("All icons generated and saved successfully!")
