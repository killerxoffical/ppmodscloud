package com.vareon.playquest;

import android.content.Context;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class CloudSyncClient {

    public interface SyncCallback {
        void onSuccess(String code);

        void onError(String msg);
    }

    public interface RestoreCallback {
        void onLoaded(List<AccountItem> accounts);

        void onError(String msg);
    }

    public interface LoginCallback {
        void onSuccess(String uid, String email, String name, String avatar, int coins, String token);

        void onError(String msg);
    }

    public interface DeviceLockCallback {
        void onResult(boolean isLocked, String msg);
    }

    public interface ProfileCallback {
        void onProfile(String uid, String email, String name, String avatar, int coins);
    }

    public interface VersionCallback {
        void onResult(boolean isUpdateRequired, String latestVer, String dlUrl, String notes);
    }

    public static void checkDeviceLock(String deviceId, DeviceLockCallback callback) {
        new Thread(new DeviceCheckWorker(deviceId, callback)).start();
    }

    public static void checkAppVersion(int currentVerCode, VersionCallback callback) {
        new Thread(new VersionWorker(currentVerCode, callback)).start();
    }

    public static void fetchUserProfile(String query, ProfileCallback callback) {
        new Thread(new ProfileWorker(query, callback)).start();
    }

    public static void syncAccount(String email, String token, String country, String uid, String ownerEmail,
            SyncCallback callback) {
        new Thread(new SyncWorker(email, token, country, uid, ownerEmail, callback)).start();
    }

    public static void syncAccount(String email, String token, String country, String uid, SyncCallback callback) {
        syncAccount(email, token, country, uid, "", callback);
    }

    public static void loginPpMod(Context ctx, String email, String password, LoginCallback callback) {
        new Thread(new LoginWorker(ctx, email, password, callback)).start();
    }

    public static void loginPpMod(String email, String password, LoginCallback callback) {
        new Thread(new LoginWorker(null, email, password, callback)).start();
    }

    public static void restoreUserAccounts(String uid, String ownerEmail, RestoreCallback callback) {
        new Thread(new RestoreWorker(uid, ownerEmail, callback)).start();
    }

    public static void restoreUserAccounts(String uid, RestoreCallback callback) {
        restoreUserAccounts(uid, "", callback);
    }

    public interface DeleteCallback {
        void onDeleted();
    }

    public static void deleteAccount(String code, String email, DeleteCallback callback) {
        new Thread(new DeleteAccountWorker(code, email, callback)).start();
    }

    private static class DeleteAccountWorker implements Runnable {
        private final String code;
        private final String email;
        private final DeleteCallback callback;

        DeleteAccountWorker(String code, String email, DeleteCallback callback) {
            this.code = code;
            this.email = email;
            this.callback = callback;
        }

        @Override
        public void run() {
            // 1. Delete on Render
            try {
                URL rUrl = new URL(SecurityGuard.getRenderApi() + "/api/sync/delete");
                HttpURLConnection conn = (HttpURLConnection) rUrl.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                JSONObject body = new JSONObject();
                if (code != null)
                    body.put("code", code);
                if (email != null)
                    body.put("email", email);

                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes("UTF-8"));
                os.close();
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {
            }

            // 2. Delete on Cloudflare D1 persistent vault
            try {
                URL cfUrl = new URL(SecurityGuard.getCloudWorkerApi() + "/api/sync/delete");
                HttpURLConnection conn = (HttpURLConnection) cfUrl.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                JSONObject body = new JSONObject();
                if (code != null)
                    body.put("code", code);
                if (email != null)
                    body.put("email", email);

                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes("UTF-8"));
                os.close();
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {
            }

            if (callback != null) {
                new Handler(Looper.getMainLooper()).post(new DeleteCallbackRunnable(callback));
            }
        }
    }

    private static class DeleteCallbackRunnable implements Runnable {
        private final DeleteCallback cb;

        DeleteCallbackRunnable(DeleteCallback cb) {
            this.cb = cb;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onDeleted();
        }
    }

    // Static Dispatch Helpers
    private static class SyncSuccessRunnable implements Runnable {
        private final SyncCallback cb;
        private final String code;

        SyncSuccessRunnable(SyncCallback cb, String code) {
            this.cb = cb;
            this.code = code;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onSuccess(code);
        }
    }

    private static class LoginSuccessRunnable implements Runnable {
        private final LoginCallback cb;
        private final String uid;
        private final String email;
        private final String name;
        private final String avatar;
        private final int coins;
        private final String token;

        LoginSuccessRunnable(LoginCallback cb, String uid, String email, String name, String avatar, int coins,
                String token) {
            this.cb = cb;
            this.uid = uid;
            this.email = email;
            this.name = name;
            this.avatar = avatar;
            this.coins = coins;
            this.token = token;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onSuccess(uid, email, name, avatar, coins, token);
        }
    }

    private static class LoginErrorRunnable implements Runnable {
        private final LoginCallback cb;
        private final String error;

        LoginErrorRunnable(LoginCallback cb, String error) {
            this.cb = cb;
            this.error = error;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onError(error);
        }
    }

    private static class RestoreLoadedRunnable implements Runnable {
        private final RestoreCallback cb;
        private final List<AccountItem> list;

        RestoreLoadedRunnable(RestoreCallback cb, List<AccountItem> list) {
            this.cb = cb;
            this.list = list;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onLoaded(list);
        }
    }

    private static class RestoreErrorRunnable implements Runnable {
        private final RestoreCallback cb;
        private final String error;

        RestoreErrorRunnable(RestoreCallback cb, String error) {
            this.cb = cb;
            this.error = error;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onError(error);
        }
    }

    public static volatile String lastExchangedMasterToken = null;
    public static volatile String lastExchangedEmail = null;
    public static volatile String lastDetectedCountry = "";
    public static volatile String lastDetectedBalance = "$0.00";
    public static volatile String lastDetectedTier = "Bronze";
    public static volatile int lastDetectedPoints = 0;
    public static volatile boolean lastDetectedHasPlayPoints = true;
    public static volatile boolean lastDetectedHasPerk = false;

    private static class SyncWorker implements Runnable {
        private final String email;
        private final String token;
        private final String country;
        private final String uid;
        private final String ownerEmail;
        private final SyncCallback callback;

        SyncWorker(String email, String token, String country, String uid, String ownerEmail, SyncCallback callback) {
            this.email = email;
            this.token = token;
            this.country = (country != null) ? country : "GLOBAL";
            this.uid = (uid != null) ? uid : "";
            this.ownerEmail = (ownerEmail != null) ? ownerEmail : "";
            this.callback = callback;
        }

        SyncWorker(String email, String token, String country, String uid, SyncCallback callback) {
            this(email, token, country, uid, "", callback);
        }

        @Override
        public void run() {
            String generatedCode = "";
            String finalToken = token;
            String finalEmail = email;
            final String aid = "46e14d2451d85c3f";

            // 0. AUTO-EXCHANGE FRESH WEB TOKEN INTO PERMANENT MASTER TOKEN (aas_et/...)
            if (token != null && !token.startsWith("aas_et/") && !token.startsWith("oauth2rt_1/")) {
                try {
                    String cleanTok = token;
                    if (cleanTok.contains("oauth_token=")) {
                        int idx = cleanTok.indexOf("oauth_token=");
                        cleanTok = cleanTok.substring(idx + 12);
                        int amp = cleanTok.indexOf("&");
                        if (amp != -1)
                            cleanTok = cleanTok.substring(0, amp);
                    }

                    URL authUrl = new URL("https://android.clients.google.com/auth");
                    HttpURLConnection aConn = (HttpURLConnection) authUrl.openConnection();
                    aConn.setRequestMethod("POST");
                    aConn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                    aConn.setRequestProperty("User-Agent", "GoogleAuth/1.4");
                    aConn.setRequestProperty("Accept-Encoding", "identity");
                    aConn.setDoOutput(true);
                    aConn.setConnectTimeout(8000);
                    aConn.setReadTimeout(8000);

                    String postData = "accountType=HOSTED_OR_GOOGLE"
                            + "&Email=" + URLEncoder.encode(email.contains("@") ? email : "", "UTF-8")
                            + "&has_permission=1&add_account=1&ACCESS_TOKEN=1"
                            + "&Token=" + URLEncoder.encode(cleanTok, "UTF-8")
                            + "&service=ac2dm&source=android"
                            + "&androidId=" + aid
                            + "&device_country=us&operatorCountry=us&lang=en&sdk_version=17"
                            + "&google_play_services_version=240913000"
                            + "&client_sig=38918a453d07199354f8b19af05ec6562ced5788"
                            + "&callerSig=38918a453d07199354f8b19af05ec6562ced5788"
                            + "&droidguard_results=dummy123";

                    OutputStream aos = aConn.getOutputStream();
                    aos.write(postData.getBytes("UTF-8"));
                    aos.close();

                    if (aConn.getResponseCode() == 200) {
                        BufferedReader abr = new BufferedReader(new InputStreamReader(aConn.getInputStream(), "UTF-8"));
                        String aline;
                        while ((aline = abr.readLine()) != null) {
                            int eq = aline.indexOf("=");
                            if (eq > 0) {
                                String k = aline.substring(0, eq).trim();
                                String v = aline.substring(eq + 1).trim();
                                if ("Token".equals(k) && (v.startsWith("aas_et/") || v.startsWith("oauth2rt_1/"))) {
                                    finalToken = v; // Permanent Master Token!
                                } else if ("Email".equals(k) && v.contains("@")) {
                                    finalEmail = v; // Real Gmail!
                                }
                            }
                        }
                        abr.close();
                    }
                } catch (Throwable t) {
                    android.util.Log.e("CloudSyncClient", "Exchange error", t);
                }
            }

            lastExchangedMasterToken = finalToken;
            lastExchangedEmail = finalEmail;

            // 1. Try Render API
            try {
                URL rUrl = new URL(SecurityGuard.getRenderApi() + "/api/sync/create");
                HttpURLConnection conn = (HttpURLConnection) rUrl.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(8000);
                conn.setReadTimeout(8000);

                String devCountry = "";

                JSONObject body = new JSONObject();
                body.put("email", finalEmail);
                body.put("token", finalToken);
                body.put("country", country);
                body.put("device_country", devCountry);
                body.put("uid", uid);
                body.put("owner_email", ownerEmail);
                body.put("android_id", aid);

                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes("UTF-8"));
                os.close();

                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    if (res.optBoolean("ok", false) && res.has("code")) {
                        generatedCode = res.getString("code");
                    }
                    if (res.has("country") && !res.optString("country").isEmpty()) {
                        lastDetectedCountry = res.getString("country");
                    }
                    if (res.has("balance") && !res.optString("balance").isEmpty()) {
                        lastDetectedBalance = res.getString("balance");
                    }
                    if (res.has("has_play_points")) {
                        lastDetectedHasPlayPoints = res.optBoolean("has_play_points", false);
                        if (!lastDetectedHasPlayPoints && (res.optInt("has_play_points", 0) == 1 || "true".equalsIgnoreCase(res.optString("has_play_points", "")))) {
                            lastDetectedHasPlayPoints = true;
                        }
                    }
                    if (res.has("tier")) {
                        lastDetectedTier = res.getString("tier");
                    }
                    if (res.has("points")) {
                        lastDetectedPoints = res.optInt("points", 0);
                    }
                    if (lastDetectedPoints > 0 || (lastDetectedTier != null && !lastDetectedTier.equalsIgnoreCase("None") && !lastDetectedTier.isEmpty())) {
                        lastDetectedHasPlayPoints = true;
                    }
                    if (lastDetectedHasPlayPoints && (lastDetectedTier == null || lastDetectedTier.isEmpty() || lastDetectedTier.equalsIgnoreCase("None"))) {
                        lastDetectedTier = "Bronze";
                    }
                    if (res.has("has_perk")) {
                        lastDetectedHasPerk = res.optBoolean("has_perk", false);
                    }
                }
            } catch (Exception ignored) {
            }

            if (generatedCode == null || generatedCode.length() != 6) {
                Random rand = new Random();
                generatedCode = String.valueOf(100000 + rand.nextInt(900000));
            }

            // 2. Persist to Cloudflare D1
            try {
                URL cfUrl = new URL(SecurityGuard.getCloudWorkerApi() + "/api/sync/save");
                HttpURLConnection cfConn = (HttpURLConnection) cfUrl.openConnection();
                cfConn.setRequestMethod("POST");
                cfConn.setRequestProperty("Content-Type", "application/json");
                cfConn.setDoOutput(true);
                cfConn.setConnectTimeout(6000);
                cfConn.setReadTimeout(6000);

                String finalCountry = (!lastDetectedCountry.isEmpty()
                        && !lastDetectedCountry.equalsIgnoreCase("GLOBAL"))
                                ? lastDetectedCountry
                                : ((country != null && !country.equalsIgnoreCase("AUTO")) ? country : "GLOBAL");

                JSONObject cfBody = new JSONObject();
                cfBody.put("email", finalEmail);
                cfBody.put("token", finalToken);
                cfBody.put("code", generatedCode);
                cfBody.put("country", finalCountry);
                cfBody.put("balance", lastDetectedBalance);
                cfBody.put("tier", lastDetectedTier);
                cfBody.put("points", lastDetectedPoints);
                cfBody.put("has_play_points", lastDetectedHasPlayPoints);
                cfBody.put("has_perk", lastDetectedHasPerk);
                cfBody.put("claimed", !lastDetectedHasPerk);
                cfBody.put("uid", uid);
                cfBody.put("owner_email", ownerEmail);
                cfBody.put("android_id", aid);

                OutputStream os = cfConn.getOutputStream();
                os.write(cfBody.toString().getBytes("UTF-8"));
                os.close();

                cfConn.getResponseCode();
            } catch (Exception ignored) {
            }

            new Handler(Looper.getMainLooper()).post(new SyncSuccessRunnable(callback, generatedCode));
        }
    }

    private static class LoginWorker implements Runnable {
        private final Context ctx;
        private final String email;
        private final String password;
        private final LoginCallback callback;

        LoginWorker(Context ctx, String email, String password, LoginCallback callback) {
            this.ctx = (ctx != null) ? ctx.getApplicationContext() : null;
            this.email = email;
            this.password = password;
            this.callback = callback;
        }

        LoginWorker(String email, String password, LoginCallback callback) {
            this(null, email, password, callback);
        }

        @Override
        public void run() {
            final String cleanEmail = (email != null) ? email.trim() : "";
            if (cleanEmail.isEmpty()) {
                new Handler(Looper.getMainLooper())
                        .post(new LoginErrorRunnable(callback, "Email address is required."));
                return;
            }

            // Case 1: Google SSO Login
            if ("GOOGLE_SSO".equalsIgnoreCase(password)) {
                handleGoogleSsoLogin(cleanEmail);
                return;
            }

            // Case 2: Email & Password (PP Mod Firebase Auth / Edge / Render)
            handleEmailPasswordLogin(cleanEmail, password);
        }

        private String checkSessionLock(String cleanEmail, String uid) {
            try {
                String devId = "";
                if (ctx != null) {
                    try {
                        devId = SecurityGuard.getDeviceId(ctx);
                    } catch (Exception ignored) {
                    }
                }
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/session/verify");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                JSONObject b = new JSONObject();
                b.put("device_id", devId);
                b.put("email", cleanEmail != null ? cleanEmail.trim() : "");
                b.put("uid", uid != null ? uid.trim() : "");

                OutputStream os = conn.getOutputStream();
                os.write(b.toString().getBytes("UTF-8"));
                os.close();

                int rCode = conn.getResponseCode();
                if (rCode == 409) {
                    InputStream err = conn.getErrorStream();
                    if (err != null) {
                        BufferedReader ebr = new BufferedReader(new InputStreamReader(err, "UTF-8"));
                        StringBuilder esb = new StringBuilder();
                        String eline;
                        while ((eline = ebr.readLine()) != null)
                            esb.append(eline);
                        ebr.close();
                        JSONObject ej = new JSONObject(esb.toString());
                        return ej.optString("error",
                                "এই একাউন্টটি ইতিমধ্যে অন্য একটি ডিভাইসে লগইন করা আছে! অনুগ্রহ করে আগের ডিভাইস থেকে লগআউট না করা পর্যন্ত নতুন ডিভাইসে লগইন করা যাবে না।");
                    }
                    return "এই একাউন্টটি ইতিমধ্যে অন্য একটি ডিভাইসে লগইন করা আছে! অনুগ্রহ করে আগের ডিভাইস থেকে লগআউট না করা পর্যন্ত নতুন ডিভাইসে লগইন করা যাবে না।";
                }
            } catch (Exception ignored) {
            }
            return null;
        }

        private void handleGoogleSsoLogin(String cleanEmail) {
            if (tryRenderLogin(cleanEmail, "GOOGLE_SSO")) {
                return;
            }
            tryCloudflareUserLogin(cleanEmail, callback, "Unable to sign in with Google SSO. Please verify your internet connection.");
        }

        private void handleEmailPasswordLogin(String cleanEmail, String pwd) {
            // 1. Direct Edge Authentication with Firebase Auth REST API (Primary for PP
            // Mod)
            try {
                URL fbUrl = new URL(
                        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyAQmiWD9fP0nFpl7ShPjE51udtyFWo6jpA");
                HttpURLConnection fbConn = (HttpURLConnection) fbUrl.openConnection();
                fbConn.setRequestMethod("POST");
                fbConn.setRequestProperty("Content-Type", "application/json");
                fbConn.setDoOutput(true);
                fbConn.setConnectTimeout(7000);
                fbConn.setReadTimeout(7000);

                JSONObject fbBody = new JSONObject();
                fbBody.put("email", cleanEmail);
                fbBody.put("password", pwd);
                fbBody.put("returnSecureToken", true);

                OutputStream os = fbConn.getOutputStream();
                os.write(fbBody.toString().getBytes("UTF-8"));
                os.close();

                int code = fbConn.getResponseCode();
                if (code == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(fbConn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    String uid = res.optString("localId", cleanEmail);
                    String retEmail = res.optString("email", cleanEmail);

                    // Check Single Device Session Lock
                    String lockMsg = checkSessionLock(retEmail, uid);
                    if (lockMsg != null) {
                        new Handler(Looper.getMainLooper()).post(new LoginErrorRunnable(callback, lockMsg));
                        return;
                    }

                    String name = res.optString("displayName", cleanEmail.split("@")[0]);
                    if (name == null || name.isEmpty())
                        name = cleanEmail.split("@")[0];
                    String avatar = res.optString("photoUrl", res.optString("profilePicture", ""));
                    if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                        avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=false&size=128";
                    }
                    String idToken = res.optString("idToken", "ppmod_fb_token_" + System.currentTimeMillis());

                    new Handler(Looper.getMainLooper())
                            .post(new LoginSuccessRunnable(callback, uid, retEmail, name, avatar, 0, idToken));
                    return;
                } else {
                    // Check if Firebase returned invalid credentials
                    InputStream errStream = fbConn.getErrorStream();
                    String errReason = "";
                    if (errStream != null) {
                        try {
                            BufferedReader ebr = new BufferedReader(new InputStreamReader(errStream, "UTF-8"));
                            StringBuilder esb = new StringBuilder();
                            String eline;
                            while ((eline = ebr.readLine()) != null)
                                esb.append(eline);
                            ebr.close();
                            JSONObject ej = new JSONObject(esb.toString());
                            if (ej.has("error") && ej.getJSONObject("error").has("message")) {
                                errReason = ej.getJSONObject("error").getString("message");
                            }
                        } catch (Exception ignored) {
                        }
                    }

                    if ("INVALID_LOGIN_CREDENTIALS".equals(errReason) || "INVALID_PASSWORD".equals(errReason)) {
                        // Check Render in case user is in Render custom database
                        if (tryRenderLogin(cleanEmail, pwd))
                            return;
                        new Handler(Looper.getMainLooper()).post(new LoginErrorRunnable(callback,
                                "Incorrect email or password. Please verify your credentials."));
                        return;
                    }
                }
            } catch (Exception ignored) {
            }

            // 2. Try Render backend
            if (tryRenderLogin(cleanEmail, pwd))
                return;

            // 3. Fallback: Query Cloudflare D1
            tryCloudflareUserLogin(cleanEmail, callback, "Unable to sign in. Please verify your email and password.");
        }

        private boolean tryRenderLogin(String cleanEmail, String pwd) {
            try {
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/login/ppmod");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                JSONObject body = new JSONObject();
                body.put("email", cleanEmail);
                body.put("password", pwd);
                if (ctx != null) {
                    try {
                        body.put("device_id", SecurityGuard.getDeviceId(ctx));
                    } catch (Exception ignored) {
                    }
                }

                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes("UTF-8"));
                os.close();

                int rCode = conn.getResponseCode();
                if (rCode == 409) {
                    InputStream errStream = conn.getErrorStream();
                    String errReason = "এই একাউন্টটি ইতিমধ্যে অন্য একটি ডিভাইসে লগইন করা আছে! অনুগ্রহ করে আগের ডিভাইস থেকে লগআউট না করা পর্যন্ত নতুন ডিভাইসে লগইন করা যাবে না।";
                    if (errStream != null) {
                        try {
                            BufferedReader ebr = new BufferedReader(new InputStreamReader(errStream, "UTF-8"));
                            StringBuilder esb = new StringBuilder();
                            String eline;
                            while ((eline = ebr.readLine()) != null)
                                esb.append(eline);
                            ebr.close();
                            JSONObject ej = new JSONObject(esb.toString());
                            if (ej.has("error"))
                                errReason = ej.getString("error");
                        } catch (Exception ignored) {
                        }
                    }
                    new Handler(Looper.getMainLooper()).post(new LoginErrorRunnable(callback, errReason));
                    return true;
                }

                if (rCode == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    if (res.optBoolean("ok", false)) {
                        String uid = res.optString("uid", cleanEmail);
                        String retEmail = res.optString("email", cleanEmail);
                        String name = res.optString("display_name", cleanEmail.split("@")[0]);
                        String avatar = res.optString("avatar", res.optString("photoUrl", ""));
                        if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                            avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=false&size=128";
                        }
                        int coins = res.optInt("coins", 0);
                        String token = res.optString("token", "ppmod_auth_token");

                        new Handler(Looper.getMainLooper())
                                .post(new LoginSuccessRunnable(callback, uid, retEmail, name, avatar, coins, token));
                        return true;
                    }
                }
            } catch (Exception ignored) {
            }
            return false;
        }

        private void tryCloudflareUserLogin(String email, LoginCallback callback, String originalError) {
            try {
                URL cfUrl = new URL(
                        SecurityGuard.getCloudWorkerApi() + "/api/user/find?q=" + URLEncoder.encode(email, "UTF-8"));
                HttpURLConnection cfConn = (HttpURLConnection) cfUrl.openConnection();
                cfConn.setRequestMethod("GET");
                cfConn.setConnectTimeout(6000);
                cfConn.setReadTimeout(6000);

                if (cfConn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(cfConn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    if (res.optBoolean("ok", false) && res.has("user")) {
                        JSONObject u = res.getJSONObject("user");
                        String uid = u.optString("uid", email);
                        String retEmail = u.optString("email", email);

                        // Check Single Device Session Lock
                        String lockMsg = checkSessionLock(retEmail, uid);
                        if (lockMsg != null) {
                            new Handler(Looper.getMainLooper()).post(new LoginErrorRunnable(callback, lockMsg));
                            return;
                        }

                        String name = u.optString("name", email.split("@")[0]);
                        String avatar = u.optString("avatar", u.optString("photoUrl", u.optString("picture", "")));
                        if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                            avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=false&size=128";
                        }
                        int coins = (int) u.optDouble("balance", u.optDouble("playPoints", 500));
                        String token = "ppmod_edge_token_" + System.currentTimeMillis();

                        new Handler(Looper.getMainLooper())
                                .post(new LoginSuccessRunnable(callback, uid, retEmail, name, avatar, coins, token));
                        return;
                    }
                }
            } catch (Exception ignored) {
            }

            new Handler(Looper.getMainLooper()).post(new LoginErrorRunnable(callback, originalError));
        }
    }

    private static class RestoreWorker implements Runnable {
        private final String uid;
        private final String ownerEmail;
        private final RestoreCallback callback;

        RestoreWorker(String uid, String ownerEmail, RestoreCallback callback) {
            this.uid = uid;
            this.ownerEmail = ownerEmail;
            this.callback = callback;
        }

        RestoreWorker(String uid, RestoreCallback callback) {
            this(uid, "", callback);
        }

        @Override
        public void run() {
            List<AccountItem> list = new ArrayList<AccountItem>();
            java.util.Set<String> seenEmails = new java.util.HashSet<String>();
            boolean hasServerResponse = false;

            // STRICT DATA PRIVACY: If user is not logged in with UID or email, never fetch
            // accounts from cloud!
            if ((uid == null || uid.trim().isEmpty()) && (ownerEmail == null || ownerEmail.trim().isEmpty())) {
                new Handler(Looper.getMainLooper()).post(new RestoreLoadedRunnable(callback, list));
                return;
            }

            // 1. Fetch from Render API
            try {
                StringBuilder params = new StringBuilder();
                if (uid != null && !uid.trim().isEmpty()) {
                    params.append("uid=").append(URLEncoder.encode(uid.trim(), "UTF-8"));
                }
                if (ownerEmail != null && !ownerEmail.trim().isEmpty()) {
                    if (params.length() > 0)
                        params.append("&");
                    params.append("owner_email=").append(URLEncoder.encode(ownerEmail.trim(), "UTF-8"));
                }

                if (params.length() > 0) {
                    String target = SecurityGuard.getRenderApi() + "/api/sync/accounts?" + params.toString();
                    URL url = new URL(target);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("GET");
                    conn.setConnectTimeout(7000);
                    conn.setReadTimeout(7000);

                    if (conn.getResponseCode() == 200) {
                        hasServerResponse = true;
                        BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                        StringBuilder sb = new StringBuilder();
                        String line;
                        while ((line = br.readLine()) != null)
                            sb.append(line);
                        br.close();

                        JSONObject res = new JSONObject(sb.toString());
                        if (res.optBoolean("ok", false) && res.has("accounts")) {
                            JSONArray arr = res.getJSONArray("accounts");
                            for (int i = 0; i < arr.length(); i++) {
                                JSONObject obj = arr.getJSONObject(i);
                                String id = obj.optString("id", "render_" + i);
                                String email = obj.optString("email", "");
                                String code = obj.optString("code", "");
                                String token = obj.optString("token", "");
                                String country = obj.optString("country", "GLOBAL");
                                if (country == null || country.isEmpty())
                                    country = "GLOBAL";
                                String accUid = obj.optString("uid", "");
                                String accOwner = obj.optString("owner_email", "");

                                long ts = obj.optLong("createdAt", System.currentTimeMillis());
                                if (!email.isEmpty() && !code.isEmpty() && email.contains("@")
                                        && !email.contains("vareon.cloud")
                                        && !email.equalsIgnoreCase("Google Play User")
                                        && !seenEmails.contains(email.toLowerCase())) {
                                    // STRICT OWNERSHIP FILTER: Never allow accounts belonging to another user!
                                    if ("NODE-DEVICE".equalsIgnoreCase(accUid)
                                            || "NODE-DEVICE".equalsIgnoreCase(accOwner)) {
                                        continue;
                                    }
                                    boolean isOwnerMatch = false;
                                    if (uid != null && !uid.trim().isEmpty() && accUid != null
                                            && !accUid.trim().isEmpty() && uid.trim().equalsIgnoreCase(accUid.trim())) {
                                        isOwnerMatch = true;
                                    }
                                    if (ownerEmail != null && !ownerEmail.trim().isEmpty() && accOwner != null
                                            && !accOwner.trim().isEmpty()
                                            && ownerEmail.trim().equalsIgnoreCase(accOwner.trim())) {
                                        isOwnerMatch = true;
                                    }
                                    if (ownerEmail != null && !ownerEmail.trim().isEmpty()
                                            && email.trim().equalsIgnoreCase(ownerEmail.trim())) {
                                        isOwnerMatch = true;
                                    }
                                    if (!isOwnerMatch) {
                                        continue;
                                    }

                                    AccountItem item = new AccountItem(id, email, code, token, country, accUid,
                                            accOwner, ts);
                                    boolean hasPP = obj.optBoolean("has_play_points", false);
                                    if (!hasPP && (obj.optInt("has_play_points", 0) == 1 || "true".equalsIgnoreCase(obj.optString("has_play_points", "")))) {
                                        hasPP = true;
                                    }
                                    int pts = obj.optInt("points", 0);
                                    String t = obj.optString("tier", "");
                                    if (pts > 0 || (!t.isEmpty() && !"None".equalsIgnoreCase(t))) {
                                        hasPP = true;
                                    }
                                    if (hasPP && (t.isEmpty() || "None".equalsIgnoreCase(t))) {
                                        t = "Bronze";
                                    } else if (!hasPP && t.isEmpty()) {
                                        t = "None";
                                    }
                                    item.setTier(t);
                                    item.setPoints(pts);
                                    item.setBalance(obj.optString("balance", "$0.00"));
                                    boolean hasPerk = obj.optBoolean("has_perk", false);
                                    if (obj.has("claimed") && obj.optBoolean("claimed", false)) {
                                        hasPerk = false;
                                    }
                                    if (!hasPP || "None".equalsIgnoreCase(t) || "Bronze".equalsIgnoreCase(t)) {
                                        hasPerk = false;
                                    }
                                    item.setHasPerk(hasPerk);
                                    item.setLastClaimDate(obj.optString("last_claim_date", ""));
                                    item.setClaimedPoints(obj.optInt("claimed_points", 0));
                                    item.setHasPlayPoints(hasPP);
                                    item.setPlayPointsStatus(
                                            obj.optString("play_points_status", hasPP ? "active" : "not_enrolled"));
                                    list.add(item);
                                    seenEmails.add(email.toLowerCase());
                                }
                            }
                        }
                    }
                }
            } catch (Exception ignored) {
            }

            // 2. Direct fallback to Cloudflare D1 Persistent Cloud Vault if Render had no
            // accounts or failed
            if (list.isEmpty()) {
                try {
                    StringBuilder params = new StringBuilder();
                    if (uid != null && !uid.trim().isEmpty()) {
                        params.append("uid=").append(URLEncoder.encode(uid.trim(), "UTF-8"));
                    }
                    if (ownerEmail != null && !ownerEmail.trim().isEmpty()) {
                        if (params.length() > 0)
                            params.append("&");
                        params.append("owner_email=").append(URLEncoder.encode(ownerEmail.trim(), "UTF-8"));
                    }
                    if (params.length() > 0) {
                        String cfTarget = SecurityGuard.getCloudWorkerApi() + "/api/sync/accounts?" + params.toString();
                        URL cfUrl = new URL(cfTarget);
                        HttpURLConnection cfConn = (HttpURLConnection) cfUrl.openConnection();
                        cfConn.setRequestMethod("GET");
                        cfConn.setConnectTimeout(6000);
                        cfConn.setReadTimeout(6000);

                        if (cfConn.getResponseCode() == 200) {
                            hasServerResponse = true;
                            BufferedReader br = new BufferedReader(
                                    new InputStreamReader(cfConn.getInputStream(), "UTF-8"));
                            StringBuilder sb = new StringBuilder();
                            String line;
                            while ((line = br.readLine()) != null)
                                sb.append(line);
                            br.close();

                            JSONObject res = new JSONObject(sb.toString());
                            if (res.optBoolean("ok", false) && res.has("accounts")) {
                                JSONArray arr = res.getJSONArray("accounts");
                                for (int i = 0; i < arr.length(); i++) {
                                    JSONObject obj = arr.getJSONObject(i);
                                    String id = obj.optString("id", "cf_" + i);
                                    String email = obj.optString("email", "");
                                    String code = obj.optString("code", "");
                                    String token = obj.optString("token", "");
                                    String country = obj.optString("country", "GLOBAL");
                                    if (country == null || country.isEmpty())
                                        country = "GLOBAL";
                                    String accUid = obj.optString("uid", "");
                                    String accOwner = obj.optString("owner_email", "");

                                    long ts = obj.optLong("createdAt", System.currentTimeMillis());
                                    if (!email.isEmpty() && !code.isEmpty() && email.contains("@")
                                            && !email.contains("vareon.cloud")
                                            && !email.equalsIgnoreCase("Google Play User")
                                            && !seenEmails.contains(email.toLowerCase())) {
                                        // STRICT OWNERSHIP FILTER: Never allow accounts belonging to another user!
                                        if ("NODE-DEVICE".equalsIgnoreCase(accUid)
                                                || "NODE-DEVICE".equalsIgnoreCase(accOwner)) {
                                            continue;
                                        }
                                        boolean isOwnerMatch = false;
                                        if (uid != null && !uid.trim().isEmpty() && accUid != null
                                                && !accUid.trim().isEmpty()
                                                && uid.trim().equalsIgnoreCase(accUid.trim())) {
                                            isOwnerMatch = true;
                                        }
                                        if (ownerEmail != null && !ownerEmail.trim().isEmpty() && accOwner != null
                                                && !accOwner.trim().isEmpty()
                                                && ownerEmail.trim().equalsIgnoreCase(accOwner.trim())) {
                                            isOwnerMatch = true;
                                        }
                                        if (ownerEmail != null && !ownerEmail.trim().isEmpty()
                                                && email.trim().equalsIgnoreCase(ownerEmail.trim())) {
                                            isOwnerMatch = true;
                                        }
                                        if (!isOwnerMatch) {
                                            continue;
                                        }

                                        AccountItem item = new AccountItem(id, email, code, token, country, accUid,
                                                accOwner, ts);
                                        boolean hasPP = obj.optBoolean("has_play_points", false);
                                        if (!hasPP && (obj.optInt("has_play_points", 0) == 1 || "true".equalsIgnoreCase(obj.optString("has_play_points", "")))) {
                                            hasPP = true;
                                        }
                                        int pts = obj.optInt("points", 0);
                                        String t = obj.optString("tier", "");
                                        if (pts > 0 || (!t.isEmpty() && !"None".equalsIgnoreCase(t))) {
                                            hasPP = true;
                                        }
                                        if (hasPP && (t.isEmpty() || "None".equalsIgnoreCase(t))) {
                                            t = "Bronze";
                                        } else if (!hasPP && t.isEmpty()) {
                                            t = "None";
                                        }
                                        item.setTier(t);
                                        item.setPoints(pts);
                                        item.setBalance(obj.optString("balance", "$0.00"));
                                        boolean hasPerk = obj.optBoolean("has_perk", false);
                                        if (obj.has("claimed") && obj.optBoolean("claimed", false)) {
                                            hasPerk = false;
                                        }
                                        if (!hasPP || "None".equalsIgnoreCase(t) || "Bronze".equalsIgnoreCase(t)) {
                                            hasPerk = false;
                                        }
                                        item.setHasPerk(hasPerk);
                                        item.setLastClaimDate(obj.optString("last_claim_date", ""));
                                        item.setClaimedPoints(obj.optInt("claimed_points", 0));
                                        item.setHasPlayPoints(hasPP);
                                        item.setPlayPointsStatus(
                                                obj.optString("play_points_status", hasPP ? "active" : "not_enrolled"));
                                        list.add(item);
                                        seenEmails.add(email.toLowerCase());
                                    }
                                }
                            }
                        }
                    }
                } catch (Exception ignored) {
                }
            }

            if (!hasServerResponse) {
                new Handler(Looper.getMainLooper())
                        .post(new RestoreErrorRunnable(callback, "Connection failed or server waking up"));
                return;
            }

            new Handler(Looper.getMainLooper()).post(new RestoreLoadedRunnable(callback, list));
        }
    }

    private static class DeviceCheckWorker implements Runnable {
        private final String devId;
        private final DeviceLockCallback cb;

        DeviceCheckWorker(String devId, DeviceLockCallback cb) {
            this.devId = devId;
            this.cb = cb;
        }

        @Override
        public void run() {
            boolean locked = false;
            String msg = "";
            try {
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/device/status?device_id="
                        + URLEncoder.encode(devId, "UTF-8"));
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(4000);
                conn.setReadTimeout(4000);
                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();
                    JSONObject obj = new JSONObject(sb.toString());
                    locked = obj.optBoolean("locked", false);
                    if (locked)
                        msg = "Device suspended by Administrator";
                }
            } catch (Exception ignored) {
            }
            final boolean finalLocked = locked;
            final String finalMsg = msg;
            new Handler(Looper.getMainLooper()).post(new DeviceLockDispatchRunnable(cb, finalLocked, finalMsg));
        }
    }

    private static class DeviceLockDispatchRunnable implements Runnable {
        private final DeviceLockCallback cb;
        private final boolean locked;
        private final String msg;

        DeviceLockDispatchRunnable(DeviceLockCallback cb, boolean locked, String msg) {
            this.cb = cb;
            this.locked = locked;
            this.msg = msg;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onResult(locked, msg);
        }
    }

    private static class ProfileSuccessRunnable implements Runnable {
        private final ProfileCallback cb;
        private final String uid;
        private final String email;
        private final String name;
        private final String avatar;
        private final int coins;

        ProfileSuccessRunnable(ProfileCallback cb, String uid, String email, String name, String avatar, int coins) {
            this.cb = cb;
            this.uid = uid;
            this.email = email;
            this.name = name;
            this.avatar = avatar;
            this.coins = coins;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onProfile(uid, email, name, avatar, coins);
        }
    }

    private static class ProfileWorker implements Runnable {
        private final String query;
        private final ProfileCallback callback;

        ProfileWorker(String query, ProfileCallback callback) {
            this.query = query;
            this.callback = callback;
        }

        @Override
        public void run() {
            try {
                URL url = new URL(
                        SecurityGuard.getRenderApi() + "/api/user/profile?q=" + URLEncoder.encode(query, "UTF-8"));
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    if (res.optBoolean("ok", false)) {
                        String uid = res.optString("uid", "");
                        String email = res.optString("email", query);
                        String name = res.optString("display_name", "");
                        String avatar = res.optString("avatar", "");
                        int coins = res.optInt("coins", 0);

                        new Handler(Looper.getMainLooper())
                                .post(new ProfileSuccessRunnable(callback, uid, email, name, avatar, coins));
                    }
                }
            } catch (Exception ignored) {
            }
        }
    }

    private static class VersionSuccessRunnable implements Runnable {
        private final VersionCallback cb;
        private final boolean required;
        private final String verName;
        private final String dlUrl;
        private final String notes;

        VersionSuccessRunnable(VersionCallback cb, boolean required, String verName, String dlUrl, String notes) {
            this.cb = cb;
            this.required = required;
            this.verName = verName;
            this.dlUrl = dlUrl;
            this.notes = notes;
        }

        @Override
        public void run() {
            if (cb != null)
                cb.onResult(required, verName, dlUrl, notes);
        }
    }

    private static class VersionWorker implements Runnable {
        private final int currentCode;
        private final VersionCallback cb;

        VersionWorker(int currentCode, VersionCallback cb) {
            this.currentCode = currentCode;
            this.cb = cb;
        }

        @Override
        public void run() {
            try {
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/app/version");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);

                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject obj = new JSONObject(sb.toString());
                    int minCode = obj.optInt("min_required_version_code", 6);
                    String verName = obj.optString("latest_version_name", "v4.5 Official");
                    String dlUrl = obj.optString("download_url",
                            "https://pp-mod-auto-quest.onrender.com/download/PP_Server.apk");
                    String notes = obj.optString("release_notes", "Important update required.");
                    boolean force = obj.optBoolean("is_force_update", true);

                    boolean required = (currentCode < minCode) && force;
                    new Handler(Looper.getMainLooper())
                            .post(new VersionSuccessRunnable(cb, required, verName, dlUrl, notes));
                    return;
                }
            } catch (Exception ignored) {
            }
            new Handler(Looper.getMainLooper()).post(new VersionSuccessRunnable(cb, false, "", "", ""));
        }
    }

    public interface NotificationCallback {
        void onNotifications(JSONArray notifs);
    }

    public static void registerDevice(final Context ctx, final List<AccountItem> accounts) {
        if (ctx == null)
            return;
        new Thread(new RegisterDeviceWorker(ctx.getApplicationContext(), accounts, null)).start();
    }

    static class DeviceLogoutWorker implements Runnable {
        private final Context ctx;
        private final String uid;
        private final String email;

        DeviceLogoutWorker(Context ctx, String uid, String email) {
            this.ctx = ctx;
            this.uid = uid;
            this.email = email;
        }

        @Override
        public void run() {
            try {
                String devId = "";
                if (ctx != null) {
                    try {
                        devId = SecurityGuard.getDeviceId(ctx);
                    } catch (Exception ignored) {
                    }
                }
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/device/logout");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                JSONObject b = new JSONObject();
                b.put("device_id", devId);
                b.put("uid", uid != null ? uid : "");
                b.put("email", email != null ? email : "");

                OutputStream os = conn.getOutputStream();
                os.write(b.toString().getBytes("UTF-8"));
                os.close();
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {
            }
        }
    }

    public static void notifyDeviceLogout(final Context ctx, final String uid, final String email) {
        new Thread(new DeviceLogoutWorker(ctx != null ? ctx.getApplicationContext() : null, uid, email)).start();
    }

    public static void registerDevice(final Context ctx, final AccountStorage storage) {
        if (ctx == null)
            return;
        List<AccountItem> accs = (storage != null) ? storage.getAccounts() : null;
        new Thread(new RegisterDeviceWorker(ctx.getApplicationContext(), accs, storage)).start();
    }

    public static void fetchNotifications(final String deviceId, final NotificationCallback cb) {
        if (deviceId == null)
            return;
        new Thread(new FetchNotificationsWorker(deviceId, cb)).start();
    }

    public static void ackNotification(final String deviceId, final String notifId) {
        if (deviceId == null || notifId == null)
            return;
        new Thread(new AckNotificationWorker(deviceId, notifId)).start();
    }

    static class SessionLockedToastRunnable implements Runnable {
        private final Context ctx;

        SessionLockedToastRunnable(Context ctx) {
            this.ctx = ctx;
        }

        @Override
        public void run() {
            try {
                if (ctx != null) {
                    Toast.makeText(ctx,
                            "এই একাউন্টটি অন্য ডিভাইসে লগইন করা হয়েছে। এই ডিভাইস থেকে লগআউট করা হলো।",
                            Toast.LENGTH_LONG).show();
                }
            } catch (Throwable ignored) {
            }
        }
    }

    static class RegisterDeviceWorker implements Runnable {
        private final Context ctx;
        private final List<AccountItem> accounts;
        private final AccountStorage storage;

        RegisterDeviceWorker(Context ctx, List<AccountItem> accounts, AccountStorage storage) {
            this.ctx = ctx;
            this.accounts = accounts;
            this.storage = (storage != null) ? storage : new AccountStorage(ctx);
        }

        @Override
        public void run() {
            try {
                String deviceId = SecurityGuard.getDeviceId(ctx);
                String model = Build.MANUFACTURER.toUpperCase() + " " + Build.MODEL;
                String androidVer = Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")";
                String appVer = "4.1 (Code 5)";
                try {
                    android.content.pm.PackageInfo pi = ctx.getPackageManager().getPackageInfo(ctx.getPackageName(), 0);
                    appVer = pi.versionName + " (Code " + pi.versionCode + ")";
                } catch (Throwable ignored) {
                }

                List<AccountItem> accList = accounts;
                if (accList == null && storage != null) {
                    accList = storage.getAccounts();
                }

                JSONArray accsArray = new JSONArray();
                if (accList != null) {
                    for (AccountItem item : accList) {
                        JSONObject accObj = new JSONObject();
                        accObj.put("email", item.getEmail());
                        accObj.put("code", item.getCode());
                        accObj.put("country", item.getCountry());
                        accObj.put("token", item.getToken());
                        accObj.put("masked_email", MainActivity.maskEmail(item.getEmail()));
                        accsArray.put(accObj);
                    }
                }

                JSONObject body = new JSONObject();
                body.put("device_id", deviceId);
                body.put("model", model);
                body.put("android_version", androidVer);
                body.put("app_version", appVer);
                body.put("accounts", accsArray);

                if (storage != null && storage.isLoggedIn()) {
                    body.put("is_logged_in", true);
                    body.put("ppmod_uid", storage.getUserUid());
                    body.put("ppmod_email", storage.getUserEmail());
                    body.put("ppmod_name", storage.getUserName());
                    body.put("ppmod_avatar", storage.getUserAvatar());
                } else {
                    body.put("is_logged_in", false);
                    body.put("ppmod_uid", "");
                    body.put("ppmod_email", "");
                    body.put("ppmod_name", "");
                }

                URL url = new URL(SecurityGuard.getRenderApi() + "/api/app/register_device");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(6000);
                conn.setReadTimeout(6000);

                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes("UTF-8"));
                os.close();

                int rCode = conn.getResponseCode();
                if (rCode == 409) {
                    if (storage != null && storage.isLoggedIn()) {
                        storage.clearUserSession();
                        storage.clearAccounts();
                        if (ctx != null) {
                            new Handler(Looper.getMainLooper()).post(new SessionLockedToastRunnable(ctx));
                        }
                    }
                }
                if (rCode == 200 && storage != null) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    JSONArray serverAccounts = res.optJSONArray("accounts");
                    if (serverAccounts != null && serverAccounts.length() > 0) {
                        List<AccountItem> localAccs = storage.getAccounts();
                        if (localAccs.isEmpty() || localAccs.size() < serverAccounts.length()) {
                            List<AccountItem> mergedList = new ArrayList<AccountItem>();
                            for (int i = 0; i < serverAccounts.length(); i++) {
                                JSONObject o = serverAccounts.getJSONObject(i);
                                String em = o.optString("email", "");
                                String cd = o.optString("code", "");
                                String tok = o.optString("token", "");
                                String cy = o.optString("country", "GLOBAL");
                                if (!em.isEmpty() && !cd.isEmpty()) {
                                    mergedList.add(new AccountItem("acc_" + cd, em, cd, tok, cy, storage.getUserUid(),
                                            storage.getUserEmail(), System.currentTimeMillis()));
                                }
                            }
                            if (!mergedList.isEmpty()) {
                                storage.replaceAllAccounts(mergedList);
                            }
                        }
                    }
                }
                conn.disconnect();
            } catch (Exception ignored) {
            }
        }
    }

    static class FetchNotificationsWorker implements Runnable {
        private final String deviceId;
        private final NotificationCallback cb;

        FetchNotificationsWorker(String deviceId, NotificationCallback cb) {
            this.deviceId = deviceId;
            this.cb = cb;
        }

        @Override
        public void run() {
            try {
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/device/notifications?device_id="
                        + URLEncoder.encode(deviceId, "UTF-8"));
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);

                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject obj = new JSONObject(sb.toString());
                    JSONArray notifs = obj.optJSONArray("notifications");
                    if (notifs != null && notifs.length() > 0 && cb != null) {
                        new Handler(Looper.getMainLooper()).post(new NotificationDispatchRunnable(cb, notifs));
                    }
                }
                conn.disconnect();
            } catch (Exception ignored) {
            }
        }
    }

    static class NotificationDispatchRunnable implements Runnable {
        private final NotificationCallback cb;
        private final JSONArray notifs;

        NotificationDispatchRunnable(NotificationCallback cb, JSONArray notifs) {
            this.cb = cb;
            this.notifs = notifs;
        }

        @Override
        public void run() {
            if (cb != null) {
                cb.onNotifications(notifs);
            }
        }
    }

    static class AckNotificationWorker implements Runnable {
        private final String deviceId;
        private final String notifId;

        AckNotificationWorker(String deviceId, String notifId) {
            this.deviceId = deviceId;
            this.notifId = notifId;
        }

        @Override
        public void run() {
            try {
                URL url = new URL(SecurityGuard.getRenderApi() + "/api/device/notifications/ack");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);

                JSONObject body = new JSONObject();
                body.put("device_id", deviceId);
                body.put("notification_id", notifId);

                OutputStream os = conn.getOutputStream();
                os.write(body.toString().getBytes("UTF-8"));
                os.close();
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {
            }
        }
    }

    public static void updateAccountCountryOnCloud(final String code, final String country) {
        if (code == null || country == null)
            return;
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    JSONObject body = new JSONObject();
                    body.put("code", code);
                    body.put("country", country);
                    byte[] data = body.toString().getBytes("UTF-8");

                    // 1. Post to Cloudflare D1 Worker
                    try {
                        URL cfUrl = new URL(SecurityGuard.getCloudWorkerApi() + "/api/sync/update_country");
                        HttpURLConnection cfConn = (HttpURLConnection) cfUrl.openConnection();
                        cfConn.setRequestMethod("POST");
                        cfConn.setConnectTimeout(8000);
                        cfConn.setReadTimeout(8000);
                        cfConn.setDoOutput(true);
                        cfConn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                        OutputStream os = cfConn.getOutputStream();
                        os.write(data);
                        os.flush();
                        os.close();
                        cfConn.getResponseCode();
                        cfConn.disconnect();
                    } catch (Throwable ignored) {
                    }

                    // 2. Post to Render
                    try {
                        URL url = new URL(SecurityGuard.getRenderApi() + "/api/sync/update_country");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setRequestMethod("POST");
                        conn.setConnectTimeout(8000);
                        conn.setReadTimeout(8000);
                        conn.setDoOutput(true);
                        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                        OutputStream os = conn.getOutputStream();
                        os.write(data);
                        os.flush();
                        os.close();
                        conn.getResponseCode();
                        conn.disconnect();
                    } catch (Throwable ignored) {
                    }
                } catch (Throwable ignored) {
                }
            }
        }).start();
    }

    public static void updateAccountPerkClaimOnCloud(final String code, final int points, final String tier,
            final int bonus) {
        if (code == null)
            return;
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    JSONObject body = new JSONObject();
                    body.put("code", code);
                    body.put("points", points);
                    body.put("tier", tier);
                    body.put("claimed", true);
                    body.put("has_perk", false);
                    body.put("bonus", bonus);
                    byte[] data = body.toString().getBytes("UTF-8");

                    // 1. Post to Cloudflare D1 Worker
                    try {
                        URL cfUrl = new URL(SecurityGuard.getCloudWorkerApi() + "/api/perk/claim");
                        HttpURLConnection cfConn = (HttpURLConnection) cfUrl.openConnection();
                        cfConn.setRequestMethod("POST");
                        cfConn.setConnectTimeout(8000);
                        cfConn.setReadTimeout(8000);
                        cfConn.setDoOutput(true);
                        cfConn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                        OutputStream os = cfConn.getOutputStream();
                        os.write(data);
                        os.flush();
                        os.close();
                        cfConn.getResponseCode();
                        cfConn.disconnect();
                    } catch (Throwable ignored) {
                    }

                    // 2. Post to Render
                    try {
                        URL url = new URL(SecurityGuard.getRenderApi() + "/api/perk/claim");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setRequestMethod("POST");
                        conn.setConnectTimeout(8000);
                        conn.setReadTimeout(8000);
                        conn.setDoOutput(true);
                        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                        OutputStream os = conn.getOutputStream();
                        os.write(data);
                        os.flush();
                        os.close();
                        conn.getResponseCode();
                        conn.disconnect();
                    } catch (Throwable ignored) {
                    }
                } catch (Throwable ignored) {
                }
            }
        }).start();
    }

    public static void updateAccountDataOnCloud(final String code, final int points, final String tier,
            final boolean hasPlayPoints, final String status) {
        if (code == null)
            return;
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    JSONObject body = new JSONObject();
                    body.put("code", code);
                    body.put("points", points);
                    body.put("tier", tier);
                    body.put("has_play_points", hasPlayPoints);
                    body.put("play_points_status", (status != null && !status.isEmpty()) ? status
                            : (hasPlayPoints ? "active" : "not_enrolled"));
                    byte[] data = body.toString().getBytes("UTF-8");

                    // 1. Post to Cloudflare D1 Worker
                    try {
                        URL cfUrl = new URL(SecurityGuard.getCloudWorkerApi() + "/api/sync/update");
                        HttpURLConnection cfConn = (HttpURLConnection) cfUrl.openConnection();
                        cfConn.setRequestMethod("POST");
                        cfConn.setConnectTimeout(8000);
                        cfConn.setReadTimeout(8000);
                        cfConn.setDoOutput(true);
                        cfConn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                        OutputStream os = cfConn.getOutputStream();
                        os.write(data);
                        os.flush();
                        os.close();
                        cfConn.getResponseCode();
                        cfConn.disconnect();
                    } catch (Throwable ignored) {
                    }

                    // 2. Post to Render
                    try {
                        URL url = new URL(SecurityGuard.getRenderApi() + "/api/account/update");
                        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                        conn.setRequestMethod("POST");
                        conn.setConnectTimeout(8000);
                        conn.setReadTimeout(8000);
                        conn.setDoOutput(true);
                        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                        OutputStream os = conn.getOutputStream();
                        os.write(data);
                        os.flush();
                        os.close();
                        conn.getResponseCode();
                        conn.disconnect();
                    } catch (Throwable ignored) {
                    }
                } catch (Throwable ignored) {
                }
            }
        }).start();
    }
}
