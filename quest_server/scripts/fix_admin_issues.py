with open('pp mod/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Clean up residual cfgPpmServerApk in admin.html
# Find:
# <div>
#     <label class="lbl">Official APK Download URL</label>
#     <input id="cfgPpmServerApk" ...
# ...
# </div>

import re
old_fragment = re.search(r'<div>\s*<label class="lbl">Official APK Download URL</label>.*?</div>\s*<button onclick="saveApkDownloadLink\(this\)".*?</button>\s*</div>', text, re.DOTALL)
if old_fragment:
    text = text[:old_fragment.start()] + text[old_fragment.end():]
    print('[+] Residual Official APK Download URL box removed completely')
else:
    print('[-] Residual box regex not matched directly, searching lines...')
    lines = text.splitlines(True)
    out_lines = []
    skip = False
    for l in lines:
        if 'Official APK Download URL' in l:
            skip = True
            # remove previous line if it was <div> or whitespace
            if out_lines and ('<div>' in out_lines[-1] or out_lines[-1].strip() == ''):
                out_lines.pop()
            continue
        if skip:
            if '</button>' in l:
                continue
            if '</div>' in l:
                skip = False
                continue
            continue
        out_lines.append(l)
    text = "".join(out_lines)
    print('[+] Line-by-line removal executed')

# 2. Upgrade window.userSheet to have instant loading state and parallel fetches
old_user_sheet_start = 'window.userSheet = async (uid) => {'
pos_us = text.find(old_user_sheet_start)
if pos_us != -1:
    pos_us_end = text.find('function rowLine(k, t, a, s, ts, prevBal = null) {', pos_us)
    if pos_us_end != -1:
        # We replace from pos_us up to pos_us_end
        new_user_sheet = """window.userSheet = async (uid) => {
            // 0. Instant Visual Response: তড়িৎ লোডিং স্পিনার ও শিট ওপেন
            const initialUser = (S.users || []).find(x => x.id === uid || x.uid === uid) || { name: 'User', email: '', balance: 0 };
            openSheet(`
                <div class="p-6 sm:p-8 text-center space-y-4">
                    <div class="relative w-14 h-14 mx-auto flex items-center justify-center">
                        <div class="w-14 h-14 rounded-full border-4 border-indigo-200 border-t-indigo-600 animate-spin"></div>
                        <div class="absolute inset-0 flex items-center justify-center text-lg">⚡</div>
                    </div>
                    <div>
                        <h4 class="text-sm font-black text-slate-900">${esc(initialUser.name || 'User Profile')}</h4>
                        <p class="text-xs text-indigo-600 font-bold mt-0.5">Fetching live data from Cloudflare D1...</p>
                        <p class="text-[11px] text-slate-400 font-medium">Synced Google Accounts, Orders & Live Balance লোড হচ্ছে</p>
                    </div>
                    <div class="p-2.5 bg-slate-100 rounded-xl border border-slate-200 text-xs font-mono text-slate-600 truncate max-w-xs mx-auto">
                        UID: ${esc(uid)}
                    </div>
                    <button onclick="closeSheet()" class="px-4 py-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 bg-slate-200/60 rounded-lg">Cancel</button>
                </div>
            `);

            // ১. প্যারালাল ফেচ (Parallel Fetch): একসাথে ৩টি এপিআই কল (১ সেকেন্ডের মধ্যে রেডি)
            let u = {
                id: uid,
                uid: uid,
                name: initialUser.name || 'User',
                email: initialUser.email || '',
                photo: initialUser.avatar || initialUser.photo || '',
                balance: Number(initialUser.balance || 0),
                realBalance: Number(initialUser.realBalance !== undefined ? initialUser.realBalance : initialUser.balance || 0),
                bonusBalance: Number(initialUser.bonusBalance || 0),
                playPoints: Number(initialUser.playPoints || 0),
                pendingPoints: Number(initialUser.pendingPoints || 0),
                loyaltyStars: Number(initialUser.loyaltyStars || 0),
                banned: (initialUser.banned === 1 || initialUser.banned === true),
                banReason: initialUser.banReason || ''
            };

            let vaultHtml = '';
            let ord = (S.orders || []).filter(d => d.uid === uid || (u.email && (d.accEmail === u.email || d.email === u.email)));

            try {
                const fetchWithTimeout = (url, timeoutMs = 6000) => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
                    return fetch(url, { signal: controller.signal })
                        .then(r => { clearTimeout(timeoutId); return r.json(); })
                        .catch(() => null);
                };

                const [walletRes, ordRes, vaultRes] = await Promise.allSettled([
                    fetchWithTimeout(`https://ppmodscloud.profitking34.workers.dev/api/wallet?uid=${encodeURIComponent(uid)}`),
                    fetchWithTimeout(`https://ppmodscloud.profitking34.workers.dev/api/admin/orders?uid=${encodeURIComponent(uid)}&_t=${Date.now()}`),
                    fetchWithTimeout(`https://ppmodscloud.profitking34.workers.dev/api/sync/accounts?uid=${encodeURIComponent(uid)}`)
                ]);

                // Wallet Data
                const walletData = walletRes.status === 'fulfilled' ? walletRes.value : null;
                if (walletData && walletData.ok && walletData.wallet) {
                    const w = walletData.wallet;
                    u = {
                        id: uid,
                        uid: uid,
                        name: w.name || initialUser.name || 'User',
                        email: w.email || initialUser.email || '',
                        photo: w.avatar || initialUser.photo || '',
                        balance: Number(w.balance || 0),
                        realBalance: Number(w.realBalance !== undefined ? w.realBalance : w.balance),
                        bonusBalance: Number(w.bonusBalance || 0),
                        playPoints: Number(w.playPoints || 0),
                        pendingPoints: Number(w.pendingPoints || 0),
                        loyaltyStars: Number(w.loyaltyStars || 0),
                        banned: (w.banned === 1 || w.banned === true),
                        banReason: w.banReason || ''
                    };
                }

                // Orders Data
                const cfOrdRes = ordRes.status === 'fulfilled' ? ordRes.value : null;
                if (cfOrdRes && cfOrdRes.ok && Array.isArray(cfOrdRes.orders)) {
                    const ordMap = new Map();
                    ord.forEach(o => ordMap.set(o.id, o));
                    cfOrdRes.orders.forEach(o => {
                        ordMap.set(o.id, {
                            id: o.id,
                            uid: o.uid,
                            name: o.name || 'User',
                            email: o.email || '',
                            accEmail: o.accEmail || '',
                            accPass: o.accPass || '',
                            game: o.game || 'Task',
                            logo: o.logo || '',
                            amount: Number(o.amount) || 2,
                            status: o.status || 'pending',
                            adminMsg: o.adminMsg || '',
                            gamerName: o.gamerName || '',
                            userTgId: o.userTgId || '',
                            createdAt: o.createdAt ? new Date(Number(o.createdAt) || o.createdAt) : new Date()
                        });
                    });
                    ord = Array.from(ordMap.values()).sort((x, y) => msOf(y) - msOf(x));
                }

                // Connected Vault Accounts
                const vData = vaultRes.status === 'fulfilled' ? vaultRes.value : null;
                const vAccounts = (vData && vData.accounts) || [];
                if (vAccounts.length > 0) {
                    vaultHtml = `
                        <div class="mt-4 p-3.5 rounded-2xl border border-indigo-200 bg-indigo-50/50 space-y-2.5">
                            <div class="flex items-center justify-between">
                                <span class="text-xs font-black text-slate-800 flex items-center gap-1.5">
                                    <span>📱 Connected Google Accounts (${vAccounts.length})</span>
                                </span>
                                <button type="button" onclick="adminDeleteAllVaultAccounts('${uid}')" style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; padding:3px 8px; border-radius:8px; font-size:10px; font-weight:800; cursor:pointer;">
                                    🗑️ Delete All Accounts
                                </button>
                            </div>
                            <div class="space-y-1.5 max-h-48 overflow-y-auto">
                                ${vAccounts.map(acc => `
                                    <div class="flex items-center justify-between p-2 rounded-xl bg-white border border-slate-200 text-xs">
                                        <div class="min-w-0 flex-1">
                                            <div class="flex items-center gap-1.5">
                                                <span class="font-bold text-slate-900 truncate">${esc(acc.email)}</span>
                                                ${acc.code ? `<span class="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 font-mono text-[10px] font-bold">Code: ${acc.code}</span>` : ''}
                                            </div>
                                            <div class="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                                                <span>Added: ${fmtDate(acc.createdAt)}</span>
                                                ${acc.country ? `<span>• ${acc.country}</span>` : ''}
                                            </div>
                                        </div>
                                        <button type="button" onclick="adminDeleteVaultAccount('${acc.id}', '${uid}')" style="color:#ef4444; padding:2px 6px; font-size:11px;" title="Delete this account">🗑️</button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
            } catch (e) {
                console.warn('[userSheet parallel fetch warn]:', e);
            }

            const dep = (S.deposits || []).filter(d => d.uid === uid || (u.email && (d.userEmail === u.email || d.email === u.email)));
            const red = (S.redemptions || []).filter(d => d.uid === uid);
            const wd = (S.withdrawals || []).filter(d => d.uid === uid);
            const sell = (S.point_sells || []).filter(d => d.uid === uid);
            const buy = (S.account_orders || []).filter(d => d.uid === uid);
            const pend = (S.pending_points || []).filter(d => d.uid === uid);
            const sum = arr => arr.reduce((a, b) => a + (Number(b.amount) || 0), 0);
            const isD = c => (c || '').toString().toUpperCase() === 'DAILY';
            const isR = c => (c || '').toString().toUpperCase() === 'REFERRAL';
            const isE = c => (c || '').toString().toUpperCase() === 'EXCHANGE';
            const dDaily = red.filter(d => isD(d.code)), dRef = red.filter(d => isR(d.code)),
                dEx = red.filter(d => isE(d.code)), dCode = red.filter(d => !isD(d.code) && !isR(d.code) && !isE(d.code));

            openSheet(
                '<div class="flex items-center gap-3">'
                + thumb(u.photo || '', u.name, 48)
                + '<div class="grow min-w-0"><h3 class="font-bold text-base text-slate-900 truncate">' + esc(u.name || u.email || u.id)
                + (u.isReseller ? ' <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-500 text-white font-black" title="Reseller Account">👑 RESELLER</span>' : '')
                + (u._virtual ? ' <span class="text-[10px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold" title="Auto-detected from deposits/orders">Unsynced</span>' : '')
                + '</h3>'
                + '<div class="cpline"><p class="grow text-xs text-slate-500 truncate">' + esc(u.email || 'No email') + '</p>' + cpBtn(u.email, 'Copy Email') + '</div>'
                + '<div class="cpline"><p class="grow text-[11px] font-mono text-slate-400 truncate">' + esc(u.id) + '</p>' + cpBtn(u.id, 'Copy UID') + '</div>'
                + '</div></div>'
                + vaultHtml
                + '<div class="grid grid-cols-2 gap-2 mt-4">'
                + '<div class="p-3 bg-amber-50/70 border border-amber-200 rounded-2xl text-center"><p class="text-[10px] font-extrabold uppercase text-amber-800 tracking-wider">🪙 Total Coins</p><p class="text-xl font-black text-amber-600 mt-0.5">' + coins(u.balance) + '</p><p class="text-[10px] font-mono font-bold text-amber-700/80 mt-0.5">Real: ' + (u.realBalance !== undefined ? u.realBalance : (u.balance || 0)) + ' | Bonus: ' + (u.bonusBalance || 0) + '</p></div>'
                + '<div class="p-3 bg-emerald-50/70 border border-emerald-200 rounded-2xl text-center"><p class="text-[10px] font-extrabold uppercase text-emerald-800 tracking-wider">৳ Total Taka</p><p class="text-xl font-black text-emerald-600 mt-0.5">৳ ' + (u.playPoints || 0) + '</p><p class="text-[10px] font-mono font-bold text-emerald-700/80 mt-0.5">Live: ৳ ' + (u.playPoints || 0) + ' | Pend: ৳ ' + (u.pendingPoints || 0) + '</p></div>'
                + '</div>'
                + '<div class="mt-3 p-3 bg-slate-50 border border-slate-200 rounded-2xl space-y-1.5">'
                + '<p class="text-[10px] font-black uppercase text-slate-600 tracking-wider border-b border-slate-200 pb-1">📊 Taka Wallet Breakdown</p>'
                + [['Earn/Sell থেকে প্রাপ্ত', '৳ ' + (sell.reduce((a, b) => a + (Number(b.creditedPoints || b.points) || 0), 0)) + ' (' + sell.length + ' req)'],
                ['Withdraw করা', '৳ ' + (wd.reduce((a, b) => a + (Number(b.points) || 0), 0)) + ' (' + wd.length + 'x)'],
                ['পেন্ডিং আছে', '৳ ' + ((u.pendingPoints || 0))]]
                    .map(c => '<div class="flex items-center justify-between text-xs"><span class="font-bold text-slate-600">' + c[0] + '</span><span class="font-black text-slate-900">' + c[1] + '</span></div>').join('')
                + '</div>'
                + (Number(u.pendingPoints) > 0 ? '<div class="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between gap-2"><div><p class="text-xs font-black text-amber-900">Pending: ৳ ' + u.pendingPoints + '</p><p class="text-[10px] font-semibold text-amber-700">এখনই লাইভ ব্যালেন্সে পাঠাতে চান?</p></div><button onclick="forceMakeLive(\'' + u.id + '\', ' + u.pendingPoints + ')" class="btn bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs py-2 px-3 shadow-sm">⚡ Make Live Now</button></div>' : '')
                + '<p class="text-xs font-semibold text-slate-600 py-2">Total Deposited: <span class="font-bold text-slate-900">' + money(sum(dep.filter(d => d.status === 'approved'))) + '</span> &middot; Spent: <span class="font-bold text-amber-600">' + coins(sum(ord)) + '</span></p>'
                + '<div class="space-y-2 py-2 bg-slate-100/70 p-3 rounded-2xl border border-slate-200">'
                + '<p class="text-[10px] font-black uppercase tracking-wider text-slate-600">🪙 Coins Balance Adjust (Real vs Bonus)</p>'
                + '<div class="grid grid-cols-3 gap-2">'
                + '<input id="sheetAdj" type="number" placeholder="+/- Coins" class="fld">'
                + '<button onclick="adjUserDualBalance(\'' + u.id + '\',document.getElementById(\'sheetAdj\').value, \'real\')" class="btn bg-emerald-600 hover:bg-emerald-700 text-white font-bold">± Real</button>'
                + '<button onclick="adjUserDualBalance(\'' + u.id + '\',document.getElementById(\'sheetAdj\').value, \'bonus\')" class="btn bg-amber-600 hover:bg-amber-700 text-white font-bold">± Bonus</button>'
                + '</div></div>'
                + '<div class="space-y-2 py-2.5 bg-emerald-50/70 p-3 rounded-2xl border border-emerald-200 mt-2 text-left">'
                + '<div class="flex items-center justify-between"><p class="text-[10px] font-black uppercase tracking-wider text-emerald-800">৳ Taka Balance Adjust (লাইভ ও পেন্ডিং টাকা)</p><span class="text-[9.5px] font-bold text-emerald-700 font-mono">Live: ৳ ' + (u.playPoints || 0) + ' | Pend: ৳ ' + (u.pendingPoints || 0) + '</span></div>'
                + '<div class="grid grid-cols-3 gap-2">'
                + '<input id="sheetTakaAdj" type="number" placeholder="+/- Taka" class="fld bg-white text-xs">'
                + '<button onclick="adjUserTakaBalance(\'' + u.id + '\', document.getElementById(\'sheetTakaAdj\').value, \'live\')" class="btn bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-1.5">± Live Taka</button>'
                + '<button onclick="adjUserTakaBalance(\'' + u.id + '\', document.getElementById(\'sheetTakaAdj\').value, \'pending\')" class="btn bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs py-1.5">± Pending Taka</button>'
                + '</div></div>'
                + '<div class="space-y-2 py-2.5 bg-indigo-50/70 p-3 rounded-2xl border border-indigo-200 mt-2 text-left">'
                + '<p class="text-[10px] font-black uppercase tracking-wider text-indigo-900">🎁 Send Balance / Reward (টাইটেল ও পেন্ডিং ডে সহ)</p>'
                + '<div class="space-y-1.5">'
                + '<input id="sheetCustomTitle" type="text" placeholder="Title/Reason (e.g. Special Bonus, Compensation)" class="fld bg-white text-xs">'
                + '<div class="grid grid-cols-3 gap-2">'
                + '<input id="sheetCustomAmt" type="number" placeholder="Amount" class="fld bg-white text-xs">'
                + '<select id="sheetCustomUnit" class="fld bg-white text-xs font-bold">'
                + '<option value="taka">৳ Taka</option>'
                + '<option value="coins">🪙 Coins</option>'
                + '</select>'
                + '<input id="sheetCustomDays" type="number" min="0" placeholder="Days (0=Live)" class="fld bg-white text-xs">'
                + '</div>'
                + '<button onclick="sendUserCustomReward(\'' + u.id + '\')" class="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-xs cursor-pointer shadow-xs">🚀 Send Balance to User</button>'
                + '</div></div>'
                + '<div class="space-y-2 py-2 bg-slate-100/70 p-3 rounded-2xl border border-slate-200 mt-2 text-left">'
                + '<p class="text-[10px] font-black uppercase tracking-wider text-slate-600">👑 Reseller Account Permission (কয়েন রিসেলার)</p>'
                + '<div class="flex items-center justify-between">'
                + '<span class="text-xs font-bold ' + (u.isReseller ? 'text-amber-600' : 'text-slate-500') + '">' + (u.isReseller ? '● Active Reseller (অনুমোদিত)' : '○ Regular User (সাধারণ ইউজার)') + '</span>'
                + '<button onclick="toggleResellerStatus(\'' + u.id + '\', ' + (u.isReseller ? 'false' : 'true') + ')" class="btn ' + (u.isReseller ? 'bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 font-bold' : 'bg-amber-500 hover:bg-amber-600 text-white font-black') + '">' + (u.isReseller ? 'Revoke Reseller' : 'Make Reseller') + '</button>'
                + '</div></div>'
                + (u.banned ? '<div class="p-3 bg-rose-50 border border-rose-200 rounded-2xl text-left space-y-1.5 my-2">'
                    + '<div class="flex items-center justify-between">'
                    + '<span class="text-[11px] font-black text-rose-800 uppercase tracking-wide">🚫 এই ইউজার বর্তমানে ব্যান রয়েছে</span>'
                    + '<span class="text-[10px] px-2 py-0.5 rounded-full bg-rose-200 text-rose-900 font-bold">Banned</span>'
                    + '</div>'
                    + '<div class="p-2 bg-white rounded-xl border border-rose-100 text-xs text-rose-900 leading-relaxed font-semibold">'
                    + '<p class="text-[10px] text-slate-400 font-mono mb-0.5">বর্তমান ব্যান নোটিশ:</p>'
                    + '<p class="whitespace-pre-wrap">' + esc(u.banReason || 'কোনো কারণ উল্লেখ করা হয়নি (ডিফল্ট ব্যান নোটিশ ইউজার স্ক্রিনে দেখানো হচ্ছে)') + '</p>'
                    + '</div>'
                    + '<button onclick="openBanModal(\'' + u.id + '\', \'' + esc(u.email || u.name || u.id) + '\', \'' + esc(u.banReason || '') + '\', true)" class="shrink-0 px-2.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-[11px] font-black rounded-xl shadow-xs transition-all cursor-pointer flex items-center gap-1">✏️ এডিট</button>'
                    + '</div>' : '')
                + '<div class="grid ' + (u.banned ? 'grid-cols-4' : 'grid-cols-3') + ' gap-2 py-2">'
                + (u.banned ? '<button onclick="openBanModal(\'' + u.id + '\', \'' + esc(u.email || u.name || u.id) + '\', \'' + esc(u.banReason || '') + '\', true)" class="btn bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs" title="ব্যান নোটিশ এডিট করুন">✏️ Edit Notice</button>' : '')
                + '<button onclick="toggleBanWithNotice(\'' + u.id + '\', ' + (u.banned ? 'true' : 'false') + ')" class="btn ' + (u.banned ? 'bg-emerald-600 hover:bg-emerald-700 text-white font-bold' : 'bg-rose-600 hover:bg-rose-700 text-white font-bold') + '">' + (u.banned ? '✅ Unban User' : '🚫 Ban (With Notice)') + '</button>'
                + '<button onclick="resetUser(\'' + u.id + '\')" class="btn bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-700 font-bold">Reset Bal 0</button>'
                + '<button onclick="deleteRow(\'users\',\'' + u.id + '\')" class="btn bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 font-bold">Delete</button>'
                + '</div>'
                + '<div class="grid grid-cols-2 gap-2 mt-2">'
                + '<button onclick="resetUserDailyBonus(\'' + u.id + '\')" class="w-full py-2 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-800 font-bold rounded-xl text-xs cursor-pointer transition-all flex items-center justify-center gap-1"><i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i> Reset Daily Bonus</button>'
                + '<button onclick="resetWdPin(\'' + u.id + '\')" class="w-full py-2 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-700 font-bold rounded-xl text-xs cursor-pointer transition-all">Reset Withdraw PIN</button>'
                + '</div>'
                + '<div class="border-t border-slate-200 pt-3 space-y-2 max-h-96 overflow-y-auto">'
                + (dep.slice(0, 15).map(d => rowLine('TOP-UP', (d.method || '') + ' ' + (d.trxId || '') + ' +' + (d.coins || 0) + 'c', d.amount, d.status, d.createdAt, d.previousBalance))
                    .concat(ord.slice(0, 15).map(d => rowLine('TASK', (d.game || '') + ' -' + (d.amount || 0) + 'c', d.amount, d.status, d.createdAt, d.previousBalance)))
                    .concat(red.slice(0, 15).map(d => {
                        const cc = (d.code || '').toUpperCase();
                        const k = cc === 'DAILY' ? 'DAILY' : cc === 'REFERRAL' ? 'REF' : cc === 'EXCHANGE' ? 'EXCH' : 'REDEEM';
                        return rowLine(k, (d.code || '') + ' +' + (d.amount || 0) + 'c ' + (d.note || ''), d.amount, d.status || 'approved', d.createdAt, d.previousBalance);
                    }))
                    .concat(wd.slice(0, 10).map(d => rowLine('WDR', (d.method || '') + ' ' + (d.points || 0) + 'pts', d.points, d.status, d.createdAt, d.previousBalance)))
                    .concat(sell.slice(0, 10).map(d => rowLine('SELL', (d.packageTitle || '') + ' +' + (d.creditedPoints || d.points || 0) + 'pts', (d.creditedPoints || d.points || 0), d.status, d.createdAt, d.previousBalance)))
                    .concat(buy.slice(0, 10).map(d => rowLine('BUY', (d.packageTitle || '') + ' -' + (d.coinsCost || 0) + 'c', (d.coinsCost || 0), d.status, d.createdAt, d.previousBalance)))
                    .concat(pend.slice(0, 10).map(d => rowLine('PEND', (d.packageTitle || '') + ' ' + (d.points || 0) + 'pts', (d.points || 0), (d.status || 'pending'), d.createdAt, d.previousBalance)))
                    .join('') || '<p class="text-xs text-slate-400 font-semibold py-3 text-center">No transaction history found</p>')
                + '</div>'
                + '<button onclick="closeSheet()" class="w-full mt-4 py-2.5 bg-slate-800 hover:bg-slate-900 text-white font-extrabold rounded-xl text-xs cursor-pointer transition-all">Close</button>'
            );
        };

        """
        text = text[:pos_us] + new_user_sheet + text[pos_us_end:]
        print('[+] Upgraded userSheet with instant response and parallel fetching!')
    else:
        print('[-] pos_us_end not found')
else:
    print('[-] pos_us not found')

with open('pp mod/admin.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] pp mod/admin.html written successfully')
