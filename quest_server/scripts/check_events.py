import sys
import os
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from app import get_games_oauth_token, GAMES_API_BASE, get_headers

import json
with open(os.path.join(ROOT_DIR, "registered_devices.json"), "r", encoding="utf-8") as f:
    devs = json.load(f)

email = None
master_token = None
for dev in devs.values():
    for acc in dev.get("accounts", []):
        if acc.get("email") and acc.get("token", "").startswith("aas_et/"):
            email = acc["email"]
            master_token = acc["token"]
            break
    if email:
        break

print("Using email:", email)
package = "com.playrix.gardenscapes"
sig = "b0cb218c78f839529f5721e1b0757a91d1bc1e2e"

tok_res = get_games_oauth_token(email, master_token, "46e14d2451000000", package, sig)
print("Token res:", tok_res.get("ok"), tok_res.get("is_fallback"))

if tok_res.get("ok"):
    token = tok_res["access_token"]
    
    # 1. Check Event Definitions
    print("\n--- Checking Event Definitions (/eventDefinitions) ---")
    ev_res = requests.get(f"{GAMES_API_BASE}/eventDefinitions", headers=get_headers(token), timeout=10)
    print("Events HTTP status:", ev_res.status_code)
    try:
        ev_data = ev_res.json()
        print("Events response items count:", len(ev_data.get("items", [])))
        for item in ev_data.get("items", []):
            print(f"  Event: ID={item.get('id')} | Name='{item.get('displayName')}' | Desc='{item.get('description')}'")
    except Exception as e:
        print("Events parse error:", e, ev_res.text[:200])

    # 2. Check Player Events (/events/my)
    print("\n--- Checking Player Events (/events/my) ---")
    my_ev_res = requests.get(f"{GAMES_API_BASE}/events/my", headers=get_headers(token), timeout=10)
    print("My Events HTTP status:", my_ev_res.status_code)
    try:
        my_ev = my_ev_res.json()
        print("My events items count:", len(my_ev.get("items", [])))
        for item in my_ev.get("items", []):
            print(f"  My Event: ID={item.get('definitionId')} | Count={item.get('numEvents')} | Format={item.get('formattedNumEvents')}")
    except Exception as e:
        print("My events parse error:", e)

    # 3. Check Quests API (/quests)
    print("\n--- Checking Quests API (/quests) ---")
    q_res = requests.get(f"{GAMES_API_BASE}/quests", headers=get_headers(token), timeout=10)
    print("Quests HTTP status:", q_res.status_code)
    try:
        q_data = q_res.json()
        print("Quests items count:", len(q_data.get("items", [])))
        for item in q_data.get("items", []):
            print(f"  Quest: ID={item.get('id')} | Name='{item.get('name')}' | Desc='{item.get('description')}'")
    except Exception as e:
        print("Quests parse error:", e, q_res.text[:200])

    # 4. Check Applications details (/applications/{applicationId} or /applications/com.playrix.gardenscapes)
    print("\n--- Checking Application details ---")
    app_res = requests.get(f"{GAMES_API_BASE}/applications/com.playrix.gardenscapes", headers=get_headers(token), timeout=10)
    print("App details HTTP status:", app_res.status_code)
    if app_res.status_code == 200:
        print(app_res.json().get("name"), "| ID:", app_res.json().get("id"))
