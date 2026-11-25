package com.vareon.playquest;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class AccountStorage {
    private static final String PREF_NAME = "pp_server_accounts_pref";
    private static final String KEY_ACCOUNTS = "accounts_list_v3";

    // PP Mod User Session Keys
    private static final String KEY_IS_LOGGED_IN = "is_logged_in";
    private static final String KEY_USER_UID = "user_uid";
    private static final String KEY_USER_EMAIL = "user_email";
    private static final String KEY_USER_NAME = "user_name";
    private static final String KEY_USER_AVATAR = "user_avatar";
    private static final String KEY_USER_COINS = "user_coins";
    private static final String KEY_USER_AUTH_TOKEN = "user_auth_token";

    private final SharedPreferences prefs;

    public AccountStorage(Context context) {
        this.prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        // Purge legacy global key to strictly isolate per-user accounts
        if (prefs.contains("accounts_list_v3")) {
            prefs.edit().remove("accounts_list_v3").apply();
        }
        if (prefs.contains("accounts_list_v3_guest")) {
            prefs.edit().remove("accounts_list_v3_guest").apply();
        }
        purgeDeletedAccounts();
    }

    public synchronized void purgeDeletedAccounts() {
        try {
            String[] keysToCheck = new String[] {
                    getAccountsStorageKey(),
                    KEY_ACCOUNTS + "_guest",
                    KEY_ACCOUNTS + "_" + getUserUid()
            };
            for (String key : keysToCheck) {
                if (key == null)
                    continue;
                String jsonStr = prefs.getString(key, null);
                if (jsonStr != null && !jsonStr.isEmpty() && !jsonStr.equals("[]")) {
                    org.json.JSONArray arr = new org.json.JSONArray(jsonStr);
                    org.json.JSONArray clean = new org.json.JSONArray();
                    boolean changed = false;
                    for (int i = 0; i < arr.length(); i++) {
                        org.json.JSONObject obj = arr.getJSONObject(i);
                        String cd = obj.optString("code", "");
                        String em = obj.optString("email", "");
                        if (isDeleted(cd, em)) {
                            changed = true;
                        } else {
                            clean.put(obj);
                        }
                    }
                    if (changed) {
                        prefs.edit().putString(key, clean.toString()).apply();
                    }
                }
            }
        } catch (Exception ignored) {
        }
    }

    // ================= USER SESSION MANAGEMENT =================
    public boolean isLoggedIn() {
        return prefs.getBoolean(KEY_IS_LOGGED_IN, false);
    }

    public void saveUserSession(String uid, String email, String name, String avatar, int coins, String token) {
        prefs.edit()
                .putBoolean(KEY_IS_LOGGED_IN, true)
                .putString(KEY_USER_UID, uid)
                .putString(KEY_USER_EMAIL, email)
                .putString(KEY_USER_NAME, name)
                .putString(KEY_USER_AVATAR, avatar != null ? avatar : "")
                .putInt(KEY_USER_COINS, coins)
                .putString(KEY_USER_AUTH_TOKEN, token)
                .apply();
    }

    public void saveUserSession(String uid, String email, String name, int coins, String token) {
        saveUserSession(uid, email, name, "", coins, token);
    }

    public void updateUserCoins(int coins) {
        prefs.edit().putInt(KEY_USER_COINS, coins).apply();
    }

    public String getUserUid() {
        return prefs.getString(KEY_USER_UID, "");
    }

    public String getUserEmail() {
        return prefs.getString(KEY_USER_EMAIL, "");
    }

    public String getUserName() {
        return prefs.getString(KEY_USER_NAME, "PP User");
    }

    public String getUserAvatar() {
        String av = prefs.getString(KEY_USER_AVATAR, "");
        if (av != null && av.trim().startsWith("http")) {
            return av.trim();
        }
        String name = getUserName();
        if (name == null || name.trim().isEmpty() || "PP User".equalsIgnoreCase(name)) {
            name = getUserEmail();
        }
        if (name != null && !name.trim().isEmpty()) {
            return "https://ui-avatars.com/api/?name=" + name + "&background=10b981&color=fff&bold=true&rounded=true&size=128";
        }
        return "";
    }

    public String getUserDisplayName() {
        return getUserName();
    }

    public int getUserCoins() {
        return prefs.getInt(KEY_USER_COINS, 0);
    }

    public String getUserAuthToken() {
        return prefs.getString(KEY_USER_AUTH_TOKEN, "");
    }

    public String getAccountsStorageKey() {
        String uid = getUserUid();
        if (uid != null && !uid.trim().isEmpty()) {
            return KEY_ACCOUNTS + "_" + uid.trim();
        }
        String email = getUserEmail();
        if (email != null && !email.trim().isEmpty()) {
            return KEY_ACCOUNTS + "_" + email.trim().toLowerCase().replaceAll("[^a-zA-Z0-9]", "_");
        }
        return KEY_ACCOUNTS + "_guest";
    }

    public void clearUserSession() {
        String accKey = getAccountsStorageKey();
        prefs.edit()
                .putBoolean(KEY_IS_LOGGED_IN, false)
                .remove(KEY_USER_UID)
                .remove(KEY_USER_EMAIL)
                .remove(KEY_USER_NAME)
                .remove(KEY_USER_AVATAR)
                .remove(KEY_USER_COINS)
                .remove(KEY_USER_AUTH_TOKEN)
                .remove(accKey)
                .apply();
    }

    public synchronized void clearAccounts() {
        prefs.edit().remove(getAccountsStorageKey()).apply();
    }

    // ================= CONNECTED ACCOUNTS =================
    private String getDeletedKey() {
        return "deleted_blacklist_v3_" + getUserUid();
    }

    public synchronized void addDeletedBlacklist(String code, String email) {
        java.util.Set<String> set = new java.util.HashSet<String>(
                prefs.getStringSet(getDeletedKey(), new java.util.HashSet<String>()));
        if (code != null && !code.trim().isEmpty())
            set.add(code.trim());
        if (email != null && !email.trim().isEmpty())
            set.add(email.trim().toLowerCase());
        prefs.edit().putStringSet(getDeletedKey(), set).apply();
    }

    public synchronized boolean isDeleted(String code, String email) {
        java.util.Set<String> set = prefs.getStringSet(getDeletedKey(), null);
        if (set == null || set.isEmpty())
            return false;
        if (code != null && set.contains(code.trim()))
            return true;
        if (email != null && set.contains(email.trim().toLowerCase()))
            return true;
        return false;
    }

    public synchronized List<AccountItem> getAccounts() {
        List<AccountItem> list = new ArrayList<AccountItem>();
        if (!isLoggedIn()) {
            return list;
        }
        String jsonStr = prefs.getString(getAccountsStorageKey(), "[]");
        String curUid = getUserUid();
        String curEmail = getUserEmail();
        try {
            JSONArray arr = new JSONArray(jsonStr);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject obj = arr.getJSONObject(i);
                AccountItem item = AccountItem.fromJson(obj);
                if (item != null) {
                    if (isDeleted(item.getCode(), item.getEmail())) {
                        continue;
                    }
                    String oUid = item.getOwnerUid();
                    String oEm = item.getOwnerEmail();
                    String em = item.getEmail();
                    boolean match = false;
                    if (curUid != null && !curUid.trim().isEmpty() && oUid != null
                            && curUid.trim().equalsIgnoreCase(oUid.trim()))
                        match = true;
                    if (curEmail != null && !curEmail.trim().isEmpty() && oEm != null
                            && curEmail.trim().equalsIgnoreCase(oEm.trim()))
                        match = true;
                    if (curEmail != null && !curEmail.trim().isEmpty() && em != null
                            && curEmail.trim().equalsIgnoreCase(em.trim()))
                        match = true;
                    if (match) {
                        list.add(item);
                    }
                }
            }
        } catch (JSONException ignored) {
        }
        return list;
    }

    public synchronized List<AccountItem> getAccountsFiltered(String countryFilter, String searchQuery) {
        List<AccountItem> all = getAccounts();
        List<AccountItem> filtered = new ArrayList<AccountItem>();

        String q = (searchQuery != null) ? searchQuery.toLowerCase().trim() : "";
        boolean filterCountry = (countryFilter != null && !countryFilter.equalsIgnoreCase("ALL")
                && !countryFilter.equalsIgnoreCase("GLOBAL"));

        for (AccountItem item : all) {
            // Country filter
            if (filterCountry && !item.getCountry().equalsIgnoreCase(countryFilter)) {
                continue;
            }

            // Search query filter (matches email or code)
            if (!q.isEmpty()) {
                String em = item.getEmail().toLowerCase();
                String cd = item.getCode().toLowerCase();
                if (!em.contains(q) && !cd.contains(q)) {
                    continue;
                }
            }

            filtered.add(item);
        }
        return filtered;
    }

    public synchronized void saveAccount(AccountItem newItem) {
        if (newItem == null)
            return;
        if (newItem.getOwnerUid().isEmpty()) {
            newItem.setOwnerUid(getUserUid());
        }
        if (newItem.getOwnerEmail().isEmpty()) {
            newItem.setOwnerEmail(getUserEmail());
        }
        List<AccountItem> current = getAccounts();
        List<AccountItem> updated = new ArrayList<AccountItem>();

        // Add new item at top
        updated.add(newItem);

        // Keep others (avoid duplicate by email or code)
        for (AccountItem item : current) {
            boolean sameEmail = item.getEmail().equalsIgnoreCase(newItem.getEmail()) && !newItem.getEmail().isEmpty();
            boolean sameCode = item.getCode().equals(newItem.getCode());
            if (!sameEmail && !sameCode) {
                updated.add(item);
            }
        }

        saveList(updated);
    }

    public synchronized void deleteAccount(String code) {
        if (code == null)
            return;
        List<AccountItem> current = getAccounts();
        List<AccountItem> updated = new ArrayList<AccountItem>();
        String deletedEmail = "";
        for (AccountItem item : current) {
            if (code.equals(item.getCode())) {
                deletedEmail = item.getEmail();
            } else {
                updated.add(item);
            }
        }
        addDeletedBlacklist(code, deletedEmail);
        saveList(updated);
    }

    public synchronized void updateAccountData(String code, int points, String tier, boolean hasPlayPoints,
            String status) {
        if (code == null)
            return;
        List<AccountItem> current = getAccounts();
        for (AccountItem item : current) {
            if (code.equals(item.getCode())) {
                if (points >= 0)
                    item.setPoints(points);
                if (tier != null && !tier.isEmpty())
                    item.setTier(tier);
                item.setHasPlayPoints(hasPlayPoints);
                if (status != null && !status.isEmpty())
                    item.setPlayPointsStatus(status);
                break;
            }
        }
        saveList(current);
    }

    public synchronized void updateAccountData(String code, int points, String tier) {
        updateAccountData(code, points, tier, points > 0, points > 0 ? "active" : "not_enrolled");
    }

    public synchronized void updateAccountCountry(String code, String newCountry) {
        if (code == null || newCountry == null)
            return;
        List<AccountItem> current = getAccounts();
        for (AccountItem item : current) {
            if (code.equals(item.getCode())) {
                item.setCountry(newCountry.trim().toUpperCase());
                break;
            }
        }
        saveList(current);
    }

    public synchronized void replaceAllAccounts(List<AccountItem> list) {
        if (list == null)
            return;
        List<AccountItem> current = getAccounts();
        java.util.Map<String, AccountItem> localMap = new java.util.HashMap<String, AccountItem>();
        for (AccountItem item : current) {
            if (item != null && item.getCode() != null) {
                localMap.put(item.getCode(), item);
            }
        }

        List<AccountItem> secureList = new ArrayList<AccountItem>();
        java.util.Set<String> processedCodes = new java.util.HashSet<String>();
        String curUid = getUserUid();
        String curEmail = getUserEmail();

        // Merge intelligently to protect user manual edits & claim state
        for (AccountItem cloudItem : list) {
            if (cloudItem == null || cloudItem.getCode() == null)
                continue;
            if (isDeleted(cloudItem.getCode(), cloudItem.getEmail()))
                continue;

            // Strict User Isolation Check: Discard any account belonging to another user
            if (isLoggedIn()) {
                String oUid = cloudItem.getOwnerUid();
                String oEm = cloudItem.getOwnerEmail();
                String em = cloudItem.getEmail();
                boolean match = false;
                if (curUid != null && !curUid.trim().isEmpty() && oUid != null
                        && curUid.trim().equalsIgnoreCase(oUid.trim()))
                    match = true;
                if (curEmail != null && !curEmail.trim().isEmpty() && oEm != null
                        && curEmail.trim().equalsIgnoreCase(oEm.trim()))
                    match = true;
                if (curEmail != null && !curEmail.trim().isEmpty() && em != null
                        && curEmail.trim().equalsIgnoreCase(em.trim()))
                    match = true;
                if (!match)
                    continue; // Skip accounts of other users!
            }

            AccountItem local = localMap.get(cloudItem.getCode());
            if (local != null) {
                // NEVER let cloud overwrite local live points, level (tier), dollar balance, or
                // perks!
                cloudItem.setPoints(local.getPoints());
                cloudItem.setTier(local.getTier());
                cloudItem.setBalance(local.getBalance());
                cloudItem.setHasPlayPoints(local.hasPlayPoints());
                cloudItem.setHasPerk(local.hasPerk());
                cloudItem.setPlayPointsStatus(local.getPlayPointsStatus());
                cloudItem.setLastClaimDate(local.getLastClaimDate());
                cloudItem.setClaimedPoints(local.getClaimedPoints());

                // If cloud country is default but local has customized country, keep local
                String cloudCountry = cloudItem.getCountry();
                String localCountry = local.getCountry();
                if ((cloudCountry.equals("GLOBAL") || cloudCountry.equals("US"))
                        && (!localCountry.equals("GLOBAL") && !localCountry.equals("US"))) {
                    cloudItem.setCountry(localCountry);
                }
            }
            secureList.add(cloudItem);
            processedCodes.add(cloudItem.getCode());
        }

        // Protect freshly added local accounts (< 3 minutes old) that haven't synced to
        // cloud yet
        long now = System.currentTimeMillis();
        for (AccountItem local : current) {
            if (local != null && local.getCode() != null && !processedCodes.contains(local.getCode())) {
                if (!isDeleted(local.getCode(), local.getEmail())) {
                    if (now - local.getTimestamp() < 180000) { // 3 minutes grace period
                        secureList.add(local);
                        processedCodes.add(local.getCode());
                    }
                }
            }
        }

        saveList(secureList);
    }

    public synchronized void saveAccounts(List<AccountItem> list) {
        replaceAllAccounts(list);
    }

    private void saveList(List<AccountItem> list) {
        JSONArray arr = new JSONArray();
        String curUid = getUserUid();
        String curEmail = getUserEmail();
        for (AccountItem item : list) {
            if (item != null) {
                if (isLoggedIn()) {
                    if (item.getOwnerUid().isEmpty() && !curUid.isEmpty()) {
                        item.setOwnerUid(curUid);
                    }
                    if (item.getOwnerEmail().isEmpty() && !curEmail.isEmpty()) {
                        item.setOwnerEmail(curEmail);
                    }
                }
                arr.put(item.toStorageJson());
            }
        }
        prefs.edit().putString(getAccountsStorageKey(), arr.toString()).apply();
    }
}
