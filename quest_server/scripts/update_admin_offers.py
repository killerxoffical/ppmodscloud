with open('pp mod/admin.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the contents of scrOf with an elegant notice pointing to Public Portal
old_scrof_start = '<div id="scrOf" class="ascreen hidden space-y-5">'
scrof_pos = text.find(old_scrof_start)
if scrof_pos != -1:
    # find next screen <!-- ===== 10.
    next_screen_marker = '<!-- ===== 10.'
    next_pos = text.find(next_screen_marker, scrof_pos)
    if next_pos != -1:
        new_scrof = """<div id="scrOf" class="ascreen hidden space-y-5">
                    <div class="glass p-6 sm:p-8 text-center border-2 border-emerald-500/20 bg-emerald-50/10">
                        <div class="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-sm">
                            <i data-lucide="gamepad-2" class="w-7 h-7"></i>
                        </div>
                        <h3 class="text-lg font-black text-slate-900 mb-2">Centralized Public Portal Quest Engine Active</h3>
                        <p class="text-sm text-slate-600 font-medium max-w-xl mx-auto mb-6">
                            পুরাতন ফায়ারবেস Offers সিস্টেম স্থায়ীভাবে পরিবর্তন করা হয়েছে। এখন থেকে সমস্ত গেম কোয়েস্ট, অ্যাচিভমেন্ট, শ্যাডো মোড (No Data) এবং অন/অফ স্ট্যাটাস সরাসরি <strong>PP Quest Server (Public Portal)</strong> থেকে নিয়ন্ত্রিত ও লাইভ সিঙ্ক হচ্ছে।
                        </p>
                        <div class="flex flex-wrap items-center justify-center gap-3">
                            <a href="https://pp-mod-auto-quest.onrender.com" target="_blank"
                                class="btn bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold px-6 py-2.5 rounded-xl shadow-md flex items-center gap-2">
                                <i data-lucide="external-link" class="w-4 h-4"></i> Open Public Portal Manager
                            </a>
                            <a href="https://pp-mod-auto-quest.onrender.com/api/portal/services" target="_blank"
                                class="btn bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold px-4 py-2.5 rounded-xl border border-slate-300 flex items-center gap-1.5 text-xs">
                                <i data-lucide="code" class="w-4 h-4"></i> View Live Services JSON
                            </a>
                        </div>
                    </div>
                </div>
                """
        text = text[:scrof_pos] + new_scrof + text[next_pos:]
        print('[+] scrOf replaced with Public Portal redirect panel')

with open('pp mod/admin.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('[+] pp mod/admin.html updated successfully')
