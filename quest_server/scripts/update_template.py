with open('achievement_unlocker/templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update loadPortalServices card rendering
old_card_badge = """                                    <div style="display:flex; align-items:center; gap:6px; margin-top:4px;">
                                        <span class="badge-status ${isEnabled ? 'active' : 'banned'}" style="font-size:10px; padding:2px 7px;">
                                            ${isEnabled ? '● Live on Public Portal' : '○ Service Paused'}
                                        </span>
                                        ${secBadge}
                                    </div>"""

new_card_badge = """                                    <div style="display:flex; align-items:center; gap:6px; margin-top:4px; flex-wrap:wrap;">
                                        <span class="badge-status ${isEnabled ? 'active' : 'banned'}" style="font-size:10px; padding:2px 7px;">
                                            ${isEnabled ? '● Live' : '○ Off (Hidden)'}
                                        </span>
                                        ${isNoData ? '<span style="background:rgba(245,158,11,0.2); color:#f59e0b; border:1px solid rgba(245,158,11,0.4); font-size:10px; font-weight:800; padding:2px 7px; border-radius:4px;">🔒 No Data (Shadow)</span>' : '<span style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); font-size:10px; font-weight:800; padding:2px 7px; border-radius:4px;">✓ Data OK</span>'}
                                        ${secBadge}
                                    </div>"""

if old_card_badge in text:
    # Also add const isNoData = s.no_data === true;
    card_start = "const isEnabled = s.enabled !== false;"
    new_card_start = "const isEnabled = s.enabled !== false;\n                const isNoData = s.no_data === true;"
    text = text.replace(card_start, new_card_start, 1)
    text = text.replace(old_card_badge, new_card_badge, 1)
    print('[+] index.html card badges updated')
else:
    print('[-] old_card_badge not found')

# 2. Update Action Buttons in card
old_btns = """                        <div style="display:flex; align-items:center; gap:6px;">
                            <button class="btn-sync-protocol" style="padding:6px 12px; font-size:11.5px; font-weight:700;" onclick="openPortalServiceModal('${s.id || s.game_id || s.service_id || s.package}')">
                                <span>✏️ Edit Quests</span>
                            </button>
                            <button class="btn-inspect-action" style="padding:6px 10px; font-size:11.5px; font-weight:700; color:${isEnabled ? '#f59e0b' : '#10b981'};" onclick="togglePortalService('${s.id || s.game_id || s.service_id || s.package}')">
                                ${isEnabled ? '⏸️ Pause' : '▶️ Activate'}
                            </button>
                            <button class="btn-inspect-action" style="padding:6px 9px; font-size:11.5px; color:#ef4444;" title="Delete Service" onclick="deletePortalService('${s.id || s.game_id || s.service_id || s.package}')">
                                🗑️
                            </button>
                        </div>"""

new_btns = """                        <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                            <button class="btn-sync-protocol" style="padding:6px 10px; font-size:11.5px; font-weight:700;" onclick="openPortalServiceModal('${s.id || s.game_id || s.service_id || s.package}')">
                                <span>✏️ Edit</span>
                            </button>
                            <button class="btn-inspect-action" style="padding:6px 10px; font-size:11.5px; font-weight:700; color:${isEnabled ? '#f59e0b' : '#10b981'};" onclick="togglePortalService('${s.id || s.game_id || s.service_id || s.package}')" title="${isEnabled ? 'Turn Off to hide completely from user' : 'Turn On to show'}">
                                ${isEnabled ? '👁️ Turn Off' : '▶️ Turn On'}
                            </button>
                            <button class="btn-inspect-action" style="padding:6px 10px; font-size:11.5px; font-weight:700; color:${isNoData ? '#10b981' : '#f59e0b'};" onclick="togglePortalServiceNoData('${s.id || s.game_id || s.service_id || s.package}')" title="${isNoData ? 'Normal Data' : 'Shadow Mode (No Data)'}">
                                ${isNoData ? '🔓 Data OK' : '🔒 No Data'}
                            </button>
                            <button class="btn-inspect-action" style="padding:6px 9px; font-size:11.5px; color:#ef4444;" title="Delete Service" onclick="deletePortalService('${s.id || s.game_id || s.service_id || s.package}')">
                                🗑️
                            </button>
                        </div>"""

if old_btns in text:
    text = text.replace(old_btns, new_btns, 1)
    print('[+] index.html card action buttons updated')
else:
    print('[-] old_btns not found')

# 3. Add togglePortalServiceNoData js function
toggle_no_data_js = """        async function togglePortalServiceNoData(gameId) {
            try {
                const res = await fetch(`${API_BASE}/api/portal/services/toggle-no-data`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ game_id: gameId })
                });
                const data = await res.json();
                if (data.ok) {
                    showToast(data.message || "Data mode updated.", "success");
                    loadPortalServices();
                } else {
                    showToast(data.error || "Failed to update data mode.", "error");
                }
            } catch (e) {
                showToast("Connection error updating data mode.", "error");
            }
        }

"""

if 'function togglePortalServiceNoData' not in text:
    target_fn = 'async function togglePortalService(gameId)'
    pos = text.find(target_fn)
    if pos != -1:
        text = text[:pos] + toggle_no_data_js + text[pos:]
        print('[+] togglePortalServiceNoData function added to index.html')
    else:
        print('[-] target_fn not found')

with open('achievement_unlocker/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] index.html write complete')
