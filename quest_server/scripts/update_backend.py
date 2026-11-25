import re

with open('achievement_unlocker/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update save_portal_service to include no_data
old_save = '"enabled": enabled,\n        "total_quests_count": len(all_quests),'
new_save = '"enabled": enabled,\n        "no_data": bool(data.get("no_data", existing.get("no_data", False))),\n        "total_quests_count": len(all_quests),'

if old_save in text:
    text = text.replace(old_save, new_save, 1)
    print('[+] save_portal_service updated with no_data')
else:
    print('[-] old_save not found or already replaced')

# 2. Add toggle_portal_service_no_data
toggle_func = '''@app.route("/api/portal/services/toggle-no-data", methods=["POST"])
def toggle_portal_service_no_data():
    """
    Toggles a game service between Normal and No-Data (Shadow Mode).
    """
    data = request.get_json(silent=True) or {}
    game_id = str(data.get("game_id") or data.get("id") or "").strip()
    services = load_portal_services()
    found_key, service = find_portal_service(services, game_id)

    if found_key:
        curr = bool(services[found_key].get("no_data", False))
        services[found_key]["no_data"] = not curr
        services[found_key]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_portal_services(services)
        state_str = "No Data (Shadow Mode)" if services[found_key]["no_data"] else "Normal Active Data"
        return jsonify({
            "ok": True,
            "no_data": services[found_key]["no_data"],
            "message": f"Service '{services[found_key].get('title')}' is now set to {state_str}."
        })
    return jsonify({"ok": False, "error": "Service not found."}), 404

'''

if '@app.route("/api/portal/services/toggle-no-data"' not in text:
    target = 'def toggle_portal_service():'
    pos = text.find(target)
    if pos != -1:
        # find the @app.route before it
        route_pos = text.rfind('@app.route', 0, pos)
        text = text[:route_pos] + toggle_func + text[route_pos:]
        print('[+] toggle_portal_service_no_data added')
    else:
        print('[-] target for toggle not found')
else:
    print('[=] toggle_portal_service_no_data already exists')

# 3. In get_portal_services, add no_data flag and support exclude_level_up
old_gps = 's["section"] = s.get("section") or g.get("section", "quest_unlocker")'
new_gps = 's["section"] = s.get("section") or g.get("section", "quest_unlocker")\n            s["no_data"] = bool(s.get("no_data", False))'
if old_gps in text:
    text = text.replace(old_gps, new_gps, 1)
    print('[+] get_portal_services updated with no_data')

# Also filter if exclude_level_up or public is set
filter_marker = 'out.sort(key=lambda x: (not x.get("enabled", True), x.get("title", "")))'
filter_replacement = '''    exclude_level_up = bool(request.args.get("exclude_level_up") == "1" or request.args.get("public") == "1" or request.args.get("for_home") == "1")
    if exclude_level_up:
        out = [s for s in out if s.get("section") != "level_up" and s.get("category") != "level_up" and s.get("enabled", True)]

    out.sort(key=lambda x: (not x.get("enabled", True), x.get("title", "")))'''

if filter_marker in text and 'exclude_level_up' not in text:
    text = text.replace(filter_marker, filter_replacement, 1)
    print('[+] get_portal_services exclude_level_up filter added')

# 4. Update Level 1-10 restriction and GPGS_LEVEL_XP in get_level_up_status & execute_level_up_boost
old_lvl_status = '''    target_level = int(data.get("target_level", 10) or 10)
    target_xp = target_level * 10000'''
new_lvl_status = '''    target_level = int(data.get("target_level", 10) or 10)
    if target_level < 1 or target_level > 10:
        return jsonify({"ok": False, "error": "লেভেল আপ বুস্ট শুধুমাত্র লেভেল ১ থেকে ১০ এর মধ্যে সীমাবদ্ধ।"}), 400

    GPGS_LEVEL_XP = {1: 0, 2: 10000, 3: 16000, 4: 26000, 5: 42000, 6: 67000, 7: 106000, 8: 169000, 9: 270000, 10: 432000}
    target_xp = GPGS_LEVEL_XP.get(target_level, 432000)'''

if old_lvl_status in text:
    # replace first occurrence in get_level_up_status
    text = text.replace(old_lvl_status, new_lvl_status, 1)
    print('[+] get_level_up_status updated')
    # replace second occurrence in execute_level_up_boost
    if old_lvl_status in text:
        text = text.replace(old_lvl_status, new_lvl_status, 1)
        print('[+] execute_level_up_boost updated')

with open('achievement_unlocker/app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] app.py update complete')
