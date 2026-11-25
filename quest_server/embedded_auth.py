"""
Google EmbeddedSetup Authenticator with Pixel 7 Pro Simulation
Simulates an official Android setup wizard (Pixel 7 Pro, US) on Google's EmbeddedSetup endpoint.
Handles 2-Step Verification Phone Prompt (Tap 42 on your phone) and captures the oauth_token.
"""

import time
import re
import uuid
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import gpsoauth
from config import GOOGLE_CLIENT_SIG
from auth import generate_android_id, get_games_oauth_token
from engine import get_player_profile

# Active authentication tasks: auth_id -> task_state
AUTH_TASKS = {}

PIXEL_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7 Pro Build/UQ1A.240105.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

def start_interactive_login(email: str, password: str, format_profile_fn) -> str:
    """Start headless Pixel login in a background thread and return auth_id"""
    auth_id = str(uuid.uuid4())
    AUTH_TASKS[auth_id] = {
        "status": "starting",
        "email": email.strip(),
        "prompt_number": None,
        "device": "Pixel 7 Pro (United States)",
        "message": "গুগল সিকিউরিটি সার্ভারে কানেক্ট হচ্ছে...",
        "start_time": time.time()
    }

    t = threading.Thread(
        target=_run_pixel_login_worker,
        args=(auth_id, email.strip(), password.strip(), format_profile_fn),
        daemon=True
    )
    t.start()
    return auth_id

def _run_pixel_login_worker(auth_id: str, email: str, password: str, format_profile_fn):
    driver = None
    android_id = generate_android_id()
    try:
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument(f"--user-agent={PIXEL_UA}")
        opts.add_argument("--window-size=412,915")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        try:
            import undetected_chromedriver as uc
            uc_opts = uc.ChromeOptions()
            uc_opts.add_argument("--headless=new")
            uc_opts.add_argument(f"--user-agent={PIXEL_UA}")
            uc_opts.add_argument("--window-size=412,915")
            driver = uc.Chrome(options=uc_opts)
        except Exception:
            driver = webdriver.Chrome(options=opts)

        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        AUTH_TASKS[auth_id]["status"] = "navigating"
        AUTH_TASKS[auth_id]["message"] = "Pixel 7 Pro সেটআপ উইজার্ডে লোড হচ্ছে..."
        
        login_url = "https://accounts.google.com/EmbeddedSetup?xoauth_display_name=Pixel+7+Pro&source=android"
        driver.get(login_url)
        time.sleep(3)

        # 1. Email input
        try:
            elem = driver.find_element(By.ID, "identifierId")
            elem.clear()
            elem.send_keys(email)
            elem.send_keys(Keys.ENTER)
        except Exception:
            # Fallback to name or input
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.get_attribute("type") in ["email", "text"] and inp.is_displayed():
                    inp.clear()
                    inp.send_keys(email)
                    inp.send_keys(Keys.ENTER)
                    break

        time.sleep(4)

        current_url = driver.current_url.lower()
        if "rejected" in current_url:
            AUTH_TASKS[auth_id] = {
                "status": "error",
                "error": "গুগল সিকিউরিটি এই সেশনটি প্রত্যাখ্যান করেছে। অনুগ্রহ করে পরে চেষ্টা করুন।"
            }
            return

        # 2. Password input
        AUTH_TASKS[auth_id]["status"] = "entering_password"
        AUTH_TASKS[auth_id]["message"] = "পাসওয়ার্ড যাচাই করা হচ্ছে..."

        try:
            pwd_elem = driver.find_element(By.NAME, "Passwd")
            pwd_elem.clear()
            pwd_elem.send_keys(password)
            pwd_elem.send_keys(Keys.ENTER)
        except Exception:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                if inp.get_attribute("type") == "password" and inp.is_displayed():
                    inp.clear()
                    inp.send_keys(password)
                    inp.send_keys(Keys.ENTER)
                    break

        time.sleep(5)

        # 3. Detect 2FA / Google Prompt Number
        prompt_number = None
        for _ in range(8):
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Check for incorrect password error
            lower_text = page_text.lower()
            if "wrong password" in lower_text or "incorrect password" in lower_text:
                AUTH_TASKS[auth_id] = {
                    "status": "error",
                    "error": "ভুল পাসওয়ার্ড! দয়া করে সঠিক পাসওয়ার্ড দিন।"
                }
                return

            if "couldn't find your google account" in lower_text:
                AUTH_TASKS[auth_id] = {
                    "status": "error",
                    "error": "গুগল অ্যাকাউন্টটি খুঁজে পাওয়া যায়নি।"
                }
                return

            # Search for tap prompt number
            m = re.search(r'tap\s+(\d{1,3})\s+on\s+your\s+phone', page_text, re.IGNORECASE)
            if m:
                prompt_number = m.group(1)
                break
            
            samps = driver.find_elements(By.TAG_NAME, "samp")
            for s in samps:
                st = s.text.strip()
                if st.isdigit() and len(st) <= 3:
                    prompt_number = st
                    break
            
            if prompt_number:
                break
            time.sleep(1)

        if prompt_number:
            AUTH_TASKS[auth_id]["status"] = "prompt_required"
            AUTH_TASKS[auth_id]["prompt_number"] = prompt_number
            AUTH_TASKS[auth_id]["device"] = "Pixel 7 Pro (United States)"
            AUTH_TASKS[auth_id]["message"] = f"আপনার ফোনে গুগল নোটিফিকেশন পাঠানো হয়েছে! স্ক্রিনে [{prompt_number}] নাম্বারে ট্যাপ করে Yes চাপুন।"

        # 4. Wait for user to approve prompt on phone (up to 90 seconds)
        oauth_token = None
        wait_start = time.time()

        while time.time() - wait_start < 90:
            # Auto-click 'I agree' / 'Accept' if it appears
            try:
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    txt = btn.text.lower()
                    if "agree" in txt or "accept" in txt or "পরবর্তী" in txt:
                        if btn.is_displayed():
                            btn.click()
                            time.sleep(1)
                            break
            except Exception:
                pass

            # Check for oauth_token cookie
            try:
                cookies = driver.get_cookies()
                for c in cookies:
                    if c.get("name") == "oauth_token":
                        oauth_token = c.get("value")
                        break
            except Exception:
                pass

            if oauth_token:
                break

            try:
                curr = driver.current_url
                if "oauth_token=" in curr:
                    m = re.search(r'oauth_token=([a-zA-Z0-9_\-]+)', curr)
                    if m:
                        oauth_token = m.group(1)
                        break
            except Exception:
                pass

            time.sleep(2)

        if not oauth_token:
            AUTH_TASKS[auth_id] = {
                "status": "error",
                "error": "ফোনে নির্দিষ্ট সময়ে নাম্বারে ট্যাপ করা হয়নি অথবা সেশন শেষ হয়ে গেছে।"
            }
            return

        AUTH_TASKS[auth_id]["status"] = "exchanging"
        AUTH_TASKS[auth_id]["message"] = "গুগল মাস্টার টোকেন ও আসল প্রোফাইল লোড হচ্ছে..."

        # 5. Exchange oauth_token for Master Token (aas_et/...)
        master_res = gpsoauth.exchange_token(email, oauth_token, android_id, service="ac2dm", client_sig=GOOGLE_CLIENT_SIG)
        master_token = master_res.get("Token")

        if not master_token:
            AUTH_TASKS[auth_id] = {
                "status": "error",
                "error": f"মাস্টার টোকেন এক্সচেঞ্জ ব্যর্থ: {master_res.get('Error', 'Unknown Error')}"
            }
            return

        # 6. Fetch Genuine Google Play Games Profile
        tok_res = get_games_oauth_token(email, master_token, android_id)
        if not tok_res.get("ok"):
            AUTH_TASKS[auth_id] = {
                "status": "error",
                "error": f"Play Games টোকেন পাওয়া যায়নি: {tok_res.get('error')}"
            }
            return

        profile_res = get_player_profile(tok_res["access_token"])
        if not profile_res.get("ok"):
            AUTH_TASKS[auth_id] = {
                "status": "error",
                "error": "গুগল প্লে গেমস প্রোফাইল লোড হয়নি।"
            }
            return

        formatted = format_profile_fn(profile_res)

        AUTH_TASKS[auth_id] = {
            "status": "success",
            "email": email,
            "master_token": master_token,
            "android_id": android_id,
            "profile": formatted
        }

    except Exception as e:
        AUTH_TASKS[auth_id] = {
            "status": "error",
            "error": f"লগইন প্রসেসে সমস্যা: {str(e)}"
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
