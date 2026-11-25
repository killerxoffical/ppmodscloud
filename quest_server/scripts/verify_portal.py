import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from app import load_portal_services

srvs = load_portal_services(force_refresh=True)
g56 = srvs.get("56", {})
print("Title:", g56.get("title"))
print("Package:", g56.get("package"))
print("Client Sig:", g56.get("client_sig"))
print("Selected count:", g56.get("selected_quests_count"))
for q in g56.get("selected_quests", []):
    print(f"  * {q.get('name')}: {q.get('description')}")
