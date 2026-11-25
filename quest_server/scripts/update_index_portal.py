with open('pp mod/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update renderOffers and add handleNoDataGameClick
old_render_offers = """        function renderOffers(list) {
            window._currentRenderedOffers = list;
            const grid = document.getElementById('gameGrid');
            if (!grid || !list.length) return;
            grid.innerHTML = list.map((o, i) => {
                const nm = (o.name || 'Game').toString();
                const pts = (o.points !== undefined && o.points !== null && o.points !== '') ? o.points : 50;
                const tag = nm + ' (' + pts + ')';
                const lg = o.logo ? '<img class="g-logo w-full h-full object-cover scale-[1.12]" src="' + o.logo + '" alt="" loading="lazy" onerror="this.src=\\'brand_logo.png\\'">' : '<span class="g-letter font-black">' + escH(nm.charAt(0).toUpperCase()) + '</span>';
                return '<button onclick="selectGame(this, \\'' + escQ(tag) + '\\')" class="game-card flex items-center p-0 rounded-lg bg-white border border-slate-300 hover:border-slate-400 transition-all text-left shadow-2xs group cursor-pointer active:scale-98 overflow-hidden h-[56px]">'
                    + '<div class="h-full w-[52px] flex-shrink-0 overflow-hidden border-r border-slate-300 relative bg-slate-50 flex items-center justify-center">'
                    + lg
                    + '</div>'
                    + '<div class="min-w-0 flex-1 px-2.5 py-1 flex flex-col justify-center">'
                    + '<span class="g-name text-xs font-black text-slate-900 truncate leading-snug group-hover:text-emerald-700 transition-colors">' + escH(nm) + '</span>'
                    + '<div class="mt-0.5 flex items-center">'
                    + '<span class="inline-flex items-center gap-1 text-[10px] font-extrabold bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded"><img src="' + PP_LOGO + '" class="w-3.5 h-3.5">' + escH(pts) + '</span>'
                    + '</div>'
                    + '</div>'
                    + '</button>';
            }).join('');
            if (typeof updateGameCount === 'function') updateGameCount(list.length);
            const sInp = document.getElementById('gameSearchInput');
            if (sInp && sInp.value.trim() && typeof filterGames === 'function') {
                filterGames(sInp.value);
            }
            const sl = document.getElementById('offerSlider');
            if (sl) sl.innerHTML = list.map((o, i) => {
                const nm = (o.name || '').toString();
                const im = o.logo ? '<img src="' + o.logo + '" alt="" loading="lazy" onerror="this.style.display=\\'none\\'">' : '<span class="g-letter">' + escH(nm.charAt(0).toUpperCase()) + '</span>';
                return '<button onclick="sliderPick(' + i + ')" class="oslide">' + im + '<span>' + escH(nm) + '</span></button>';
            }).join('');
        }"""

new_render_offers = """        window.handleNoDataGameClick = function (gameName) {
            const msg = '⚠️ ' + gameName + ' বর্তমানে প্রিভিউ মোডে রয়েছে (No Data)। খুব শীঘ্রই কোয়েস্ট যুক্ত করা হবে।';
            if (typeof showToast === 'function') {
                showToast(msg, 'warning');
            } else if (typeof showAlertModal === 'function') {
                showAlertModal('Coming Soon', msg);
            } else {
                alert(msg);
            }
        };

        function renderOffers(list) {
            window._currentRenderedOffers = list;
            const grid = document.getElementById('gameGrid');
            if (!grid || !list.length) return;
            grid.innerHTML = list.map((o, i) => {
                const nm = (o.name || 'Game').toString();
                const pts = (o.points !== undefined && o.points !== null && o.points !== '') ? o.points : 50;
                const tag = nm + ' (' + pts + ')';
                const isNoData = !!o.no_data;
                const lg = o.logo ? '<img class="g-logo w-full h-full object-cover scale-[1.12]" src="' + o.logo + '" alt="" loading="lazy" onerror="this.src=\\'brand_logo.png\\'">' : '<span class="g-letter font-black">' + escH(nm.charAt(0).toUpperCase()) + '</span>';
                
                const clickAction = isNoData 
                    ? 'handleNoDataGameClick(\\'' + escQ(nm) + '\\'); return false;'
                    : 'selectGame(this, \\'' + escQ(tag) + '\\')';

                const cardClasses = isNoData
                    ? 'game-card flex items-center p-0 rounded-lg bg-slate-50 border border-slate-300 transition-all text-left shadow-2xs overflow-hidden h-[56px] opacity-60 grayscale-[40%] cursor-not-allowed'
                    : 'game-card flex items-center p-0 rounded-lg bg-white border border-slate-300 hover:border-slate-400 transition-all text-left shadow-2xs group cursor-pointer active:scale-98 overflow-hidden h-[56px]';

                const noDataBadge = isNoData
                    ? '<span class="inline-flex items-center gap-0.5 text-[9px] font-extrabold bg-amber-100 text-amber-800 border border-amber-300 px-1 py-0.5 rounded ml-1.5">🔒 No Data</span>'
                    : '';

                return '<button onclick="' + clickAction + '" class="' + cardClasses + '">'
                    + '<div class="h-full w-[52px] flex-shrink-0 overflow-hidden border-r border-slate-300 relative bg-slate-50 flex items-center justify-center">'
                    + lg
                    + '</div>'
                    + '<div class="min-w-0 flex-1 px-2.5 py-1 flex flex-col justify-center">'
                    + '<span class="g-name text-xs font-black text-slate-900 truncate leading-snug group-hover:text-emerald-700 transition-colors">' + escH(nm) + '</span>'
                    + '<div class="mt-0.5 flex items-center">'
                    + '<span class="inline-flex items-center gap-1 text-[10px] font-extrabold bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded"><img src="' + PP_LOGO + '" class="w-3.5 h-3.5">' + escH(pts) + '</span>'
                    + noDataBadge
                    + '</div>'
                    + '</div>'
                    + '</button>';
            }).join('');
            if (typeof updateGameCount === 'function') updateGameCount(list.length);
            const sInp = document.getElementById('gameSearchInput');
            if (sInp && sInp.value.trim() && typeof filterGames === 'function') {
                filterGames(sInp.value);
            }
            const sl = document.getElementById('offerSlider');
            if (sl) sl.innerHTML = list.map((o, i) => {
                const nm = (o.name || '').toString();
                const isNoData = !!o.no_data;
                const im = o.logo ? '<img src="' + o.logo + '" alt="" loading="lazy" onerror="this.style.display=\\'none\\'">' : '<span class="g-letter">' + escH(nm.charAt(0).toUpperCase()) + '</span>';
                const clickSlide = isNoData ? 'handleNoDataGameClick(\\'' + escQ(nm) + '\\');' : 'sliderPick(' + i + ')';
                const slideStyle = isNoData ? 'style=\"opacity:0.55; filter:grayscale(40%);\"' : '';
                return '<button onclick=\"' + clickSlide + '\" ' + slideStyle + ' class=\"oslide\">' + im + '<span>' + escH(nm) + '</span></button>';
            }).join('');
        }"""

if old_render_offers in text:
    text = text.replace(old_render_offers, new_render_offers, 1)
    print('[+] renderOffers updated with shadow mode and no_data')
else:
    print('[-] old_render_offers not found')

# 2. Update loadFromPublicServerCache so it loads from Public Portal directly and ignores firestore offers
old_load_cache_marker = 'async function loadFromPublicServerCache() {'
load_cache_pos = text.find(old_load_cache_marker)
if load_cache_pos != -1:
    end_marker = '// Dynamic Sell Points Packages Listener'
    end_pos = text.find(end_marker, load_cache_pos)
    if end_pos != -1:
        new_load_cache = """async function loadFromPublicServerCache() {
            // ১. ক্যাশ মেমোরি থেকে তাৎক্ষণিক গেম ও কনফিগ লোড
            try {
                const c = JSON.parse(localStorage.getItem('pp_config_cache') || '{}');
                if (c && Object.keys(c).length) applyConfig(c);
            } catch (e) { }
            try {
                const oc = JSON.parse(localStorage.getItem('pp_portal_games_cache') || '[]');
                if (Array.isArray(oc) && oc.length && typeof renderOffers === 'function') renderOffers(oc);
            } catch (e) { }

            // ২. পাবলিক পোর্টাল সার্ভিসেস থেকে সরাসরি লাইভ গেম লোড (এডমিন অফারস সম্পূর্ণ বাদ)
            window.syncPortalGamesToGrid = async function () {
                try {
                    const res = await fetch(`https://pp-mod-auto-quest.onrender.com/api/portal/services?_t=${Date.now()}`, {
                        cache: 'no-store',
                        headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache' }
                    });
                    const pData = await res.json();
                    if (pData && pData.ok && Array.isArray(pData.services) && pData.services.length) {
                        // ১. ফিল্টারিং: লেভেল আপ গেম ইউজার পোর্টালে সম্পূর্ণ হাইড
                        // ২. ফিল্টারিং: enabled === false (Off) সম্পূর্ণ হাইড
                        const activeServices = pData.services.filter(ps => {
                            if (ps.enabled === false) return false;
                            if (ps.section === 'level_up' || ps.category === 'level_up') return false;
                            return true;
                        });

                        const lgCache = JSON.parse(localStorage.getItem('pp_game_logo_cache') || '{}');
                        const gamesList = activeServices.map((ps, idx) => {
                            const cleanT = (ps.title || 'Game').replace(/\\s*\\(\\d+\\)|\\s*\\(all\\)/gi, '').trim();
                            const logo = ps.icon || (typeof findGameLogoByName === 'function' ? findGameLogoByName(cleanT) : '') || '';
                            if (logo) lgCache[cleanT.toLowerCase()] = logo;
                            return {
                                id: ps.id || ps.game_id || ps.package,
                                name: cleanT,
                                points: ps.price_points || 50,
                                logo: logo,
                                no_data: !!ps.no_data,
                                order: idx + 1
                            };
                        });
                        try {
                            localStorage.setItem('pp_game_logo_cache', JSON.stringify(lgCache));
                            localStorage.setItem('pp_portal_games_cache', JSON.stringify(gamesList));
                        } catch (e) { }

                        if (typeof renderOffers === 'function') {
                            renderOffers(gamesList.length ? gamesList : DEFAULT_OFFERS);
                        }
                        return true;
                    }
                } catch (e) { }

                // ফেইলওভার: ক্লাউডফ্লেয়ার মিরর
                try {
                    const cfRes = await fetch("https://ppmod-api.tredarskvt.workers.dev/api/cloud/portal-services", { cache: 'no-store' });
                    const cfData = await cfRes.json();
                    let sMap = cfData && cfData.data ? cfData.data : cfData;
                    if (sMap && typeof sMap === 'object') {
                        const sList = Array.isArray(sMap) ? sMap : Object.values(sMap);
                        if (sList.length) {
                            const activeServices = sList.filter(ps => {
                                if (ps.enabled === false) return false;
                                if (ps.section === 'level_up' || ps.category === 'level_up') return false;
                                return true;
                            });
                            const gamesList = activeServices.map((ps, idx) => {
                                const cleanT = (ps.title || 'Game').replace(/\\s*\\(\\d+\\)|\\s*\\(all\\)/gi, '').trim();
                                return {
                                    id: ps.id || ps.game_id || ps.package,
                                    name: cleanT,
                                    points: ps.price_points || 50,
                                    logo: ps.icon || '',
                                    no_data: !!ps.no_data,
                                    order: idx + 1
                                };
                            });
                            if (typeof renderOffers === 'function') renderOffers(gamesList);
                            return true;
                        }
                    }
                } catch (e) { }

                return false;
            };

            // ৩. স্টোর আইটেম ও গ্লোবাল কনফিগ লোড (ফায়ারবেস অফার্স ছাড়া)
            try {
                const res = await fetch("https://ppmod-api.tredarskvt.workers.dev/api/cache/public-data");
                const data = await res.json();
                if (data && data.ok) {
                    if (data.config && Object.keys(data.config).length) applyConfig(data.config);
                    if (data.storeItems && data.storeItems.length && typeof renderStoreList === 'function') renderStoreList(data.storeItems);
                }
            } catch (e) { }

            // সিঙ্ক কল
            await window.syncPortalGamesToGrid();
        }
        loadFromPublicServerCache();
        window.addEventListener('focus', () => { if (typeof window.syncPortalGamesToGrid === 'function') window.syncPortalGamesToGrid(); });
        setInterval(() => { if (typeof window.syncPortalGamesToGrid === 'function') window.syncPortalGamesToGrid(); }, 30000);

        """
        text = text[:load_cache_pos] + new_load_cache + text[end_pos:]
        print('[+] loadFromPublicServerCache replaced with pure portal services')
    else:
        print('[-] end_marker not found')
else:
    print('[-] load_cache_pos not found')

with open('pp mod/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] pp mod/index.html updated successfully')
