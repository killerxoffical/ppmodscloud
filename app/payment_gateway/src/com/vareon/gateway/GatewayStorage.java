package com.vareon.gateway;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class GatewayStorage {
    private static final String PREF_NAME = "pp_payment_gateway_prefs";
    private static final String KEY_ENABLED = "gw_enabled";
    private static final String KEY_SERVER_URL = "gw_server_url";
    private static final String KEY_CF_URL = "gw_cf_url";
    private static final String KEY_SECRET = "gw_secret";
    private static final String KEY_RECORDS = "gw_records";
    private static final String KEY_STAT_FORWARDED = "stat_forwarded";
    private static final String KEY_STAT_APPROVED = "stat_approved";
    private static final String KEY_STAT_AMOUNT = "stat_amount";

    public static final String DEFAULT_SERVER = "https://ppm-bot-auto.onrender.com";
    public static final String DEFAULT_CF = "https://ppmod-api.tredarskvt.workers.dev";
    public static final String DEFAULT_SECRET = "PPMOD_GATEWAY_SEC_2025";

    private final SharedPreferences prefs;

    public GatewayStorage(Context context) {
        this.prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    public boolean isEnabled() {
        return prefs.getBoolean(KEY_ENABLED, true);
    }

    public void setEnabled(boolean enabled) {
        prefs.edit().putBoolean(KEY_ENABLED, enabled).apply();
    }

    public String getServerUrl() {
        String url = prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER);
        if (url == null || url.trim().isEmpty() || url.contains("pp-mod-auto-quest")) {
            url = DEFAULT_SERVER;
            prefs.edit().putString(KEY_SERVER_URL, url).apply();
        }
        return url;
    }

    public void setServerUrl(String url) {
        prefs.edit().putString(KEY_SERVER_URL, url).apply();
    }

    public String getCloudflareUrl() {
        return prefs.getString(KEY_CF_URL, DEFAULT_CF);
    }

    public void setCloudflareUrl(String url) {
        prefs.edit().putString(KEY_CF_URL, url).apply();
    }

    public String getSecretKey() {
        return prefs.getString(KEY_SECRET, DEFAULT_SECRET);
    }

    public void setSecretKey(String secret) {
        prefs.edit().putString(KEY_SECRET, secret).apply();
    }

    public int getStatForwarded() {
        return prefs.getInt(KEY_STAT_FORWARDED, 0);
    }

    public int getStatApproved() {
        return prefs.getInt(KEY_STAT_APPROVED, 0);
    }

    public double getStatAmount() {
        return Double.longBitsToDouble(prefs.getLong(KEY_STAT_AMOUNT, Double.doubleToLongBits(0.0)));
    }

    public synchronized void recordStats(boolean isApproved, double amount) {
        int f = getStatForwarded() + 1;
        int a = getStatApproved() + (isApproved ? 1 : 0);
        double amt = getStatAmount() + (isApproved ? amount : 0);
        prefs.edit()
            .putInt(KEY_STAT_FORWARDED, f)
            .putInt(KEY_STAT_APPROVED, a)
            .putLong(KEY_STAT_AMOUNT, Double.doubleToLongBits(amt))
            .apply();
    }

    public synchronized List<SmsRecord> getRecords() {
        List<SmsRecord> list = new ArrayList<SmsRecord>();
        String jsonStr = prefs.getString(KEY_RECORDS, "[]");
        try {
            JSONArray arr = new JSONArray(jsonStr);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject obj = arr.getJSONObject(i);
                SmsRecord rec = SmsRecord.fromJson(obj);
                if (rec != null) {
                    list.add(rec);
                }
            }
        } catch (JSONException ignored) {}
        return list;
    }

    public synchronized void addRecord(SmsRecord newRecord) {
        if (newRecord == null) return;
        List<SmsRecord> current = getRecords();
        List<SmsRecord> updated = new ArrayList<SmsRecord>();

        updated.add(newRecord);
        for (SmsRecord rec : current) {
            if (!rec.getTrxId().equalsIgnoreCase(newRecord.getTrxId())) {
                updated.add(rec);
            }
            if (updated.size() >= 100) break; // Limit to latest 100
        }
        saveRecords(updated);
    }

    public synchronized void updateRecordStatus(String trxId, String status) {
        if (trxId == null) return;
        List<SmsRecord> current = getRecords();
        for (SmsRecord rec : current) {
            if (rec.getTrxId().equalsIgnoreCase(trxId)) {
                rec.setStatus(status);
                break;
            }
        }
        saveRecords(current);
    }

    private void saveRecords(List<SmsRecord> list) {
        JSONArray arr = new JSONArray();
        for (SmsRecord rec : list) {
            arr.put(rec.toJson());
        }
        prefs.edit().putString(KEY_RECORDS, arr.toString()).apply();
    }
}
