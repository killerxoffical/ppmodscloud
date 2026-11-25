"""
Authentication Module for Google Play Services using gpsoauth
"""

import os
import random
import gpsoauth
from config import SCOPE_GAMES, PLAY_GAMES_PACKAGE, GOOGLE_CLIENT_SIG

def generate_android_id(seed: str = None) -> str:
    """Generate a 16-character hexadecimal Android Device ID (deterministic if seed provided)"""
    if seed:
        import hashlib
        h = hashlib.sha256(str(seed).strip().lower().encode("utf-8")).hexdigest()
        return h[:16]
    return "".join(random.choices("0123456789abcdef", k=16))

def exchange_oauth_token_for_master(email: str, oauth_token: str, android_id: str = None) -> dict:
    """
    Modern Google Login Flow (Alternative Token Exchange Flow):
    Converts browser oauth_token cookie into an official Master Token (aas_et/...).
    This 100% bypasses Google's 'BadAuthentication' bot-detection block!
    """
    if not android_id:
        android_id = generate_android_id()

    try:
        res = gpsoauth.exchange_token(
            email=email.strip(),
            token=oauth_token.strip(),
            android_id=android_id,
            service="ac2dm",
            client_sig=GOOGLE_CLIENT_SIG
        )

        if "Token" in res:
            return {
                "ok": True,
                "master_token": res["Token"],
                "email": res.get("Email", email.strip()),
                "android_id": android_id,
                "raw": res
            }
        
        return {
            "ok": False,
            "error": res.get("Error", "FailedToExchangeToken"),
            "message": "টোকেন এক্সচেঞ্জ ব্যর্থ হয়েছে।",
            "raw": res
        }
    except Exception as e:
        return {"ok": False, "error": "Exception", "message": str(e)}

def perform_google_login(email: str, password: str, android_id: str = None) -> dict:
    """
    Legacy direct master login. Note: Google now blocks direct password logins
    with BadAuthentication unless using EmbeddedSetup token exchange.
    """
    if not android_id:
        android_id = generate_android_id()

    clean_email = email.strip()
    clean_password = password.strip()

    try:
        res = gpsoauth.perform_master_login(
            email=clean_email,
            password=clean_password,
            android_id=android_id,
            service="ac2dm",
            client_sig=GOOGLE_CLIENT_SIG
        )

        if "Token" in res:
            return {
                "ok": True,
                "master_token": res["Token"],
                "email": res.get("Email", email.strip()),
                "android_id": android_id,
                "raw": res
            }
        
        err = res.get("Error", "UnknownError")
        detail = res.get("detail", "")
        
        return {
            "ok": False,
            "error": err,
            "message": detail or err,
            "raw": res
        }

    except Exception as e:
        return {
            "ok": False,
            "error": "Exception",
            "message": str(e)
        }

def get_games_oauth_token(email: str, master_token: str, android_id: str, app_package: str = None, client_sig: str = None) -> dict:
    """
    Exchange Master Token for Google Play Games OAuth2 Bearer Access Token (ya29...)
    for the specific game package and signing signature.
    """
    target_app = app_package or PLAY_GAMES_PACKAGE
    target_sig = client_sig or GOOGLE_CLIENT_SIG

    try:
        res = gpsoauth.perform_oauth(
            email=email.strip(),
            master_token=master_token,
            android_id=android_id,
            service=f"oauth2:{SCOPE_GAMES}",
            app=target_app,
            client_sig=target_sig
        )

        if "Auth" in res:
            return {
                "ok": True,
                "access_token": res["Auth"],
                "expires_in": res.get("Expiry", 3600),
                "is_fallback": False,
                "target_app": target_app,
                "raw": res
            }

        # Fallback to base Google Play Games package if game-specific signature failed
        if target_app != PLAY_GAMES_PACKAGE:
            res_fallback = gpsoauth.perform_oauth(
                email=email.strip(),
                master_token=master_token,
                android_id=android_id,
                service=f"oauth2:{SCOPE_GAMES}",
                app=PLAY_GAMES_PACKAGE,
                client_sig=GOOGLE_CLIENT_SIG
            )
            if "Auth" in res_fallback:
                return {
                    "ok": True,
                    "access_token": res_fallback["Auth"],
                    "expires_in": res_fallback.get("Expiry", 3600),
                    "is_fallback": True,
                    "target_app": PLAY_GAMES_PACKAGE,
                    "raw": res_fallback
                }
        
        return {
            "ok": False,
            "error": res.get("Error", "FailedToGetOAuthToken"),
            "raw": res
        }

    except Exception as e:
        return {
            "ok": False,
            "error": "Exception",
            "message": str(e)
        }
