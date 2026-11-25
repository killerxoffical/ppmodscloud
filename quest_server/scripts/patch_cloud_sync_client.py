import os
import sys

def patch_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        c = f.read()

    # 1. Update LoginWorker to add checkSessionLock and wrap logins
    old_login_block = '''        private void handleGoogleSsoLogin(String cleanEmail) {
            String genUid = "UID-" + Math.abs(cleanEmail.hashCode() % 900000 + 100000);
            String defaultName = cleanEmail.contains("@") ? cleanEmail.split("@")[0] : cleanEmail;
            String token = "ppmod_sso_token_" + System.currentTimeMillis();
            String avatar = "https://ui-avatars.com/api/?name=" + defaultName + "&background=10b981&color=fff&bold=true&rounded=true&size=128";
            new Handler(Looper.getMainLooper())
                    .post(new LoginSuccessRunnable(callback, genUid, cleanEmail, defaultName, avatar, 0, token));
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
                    String uid = res.optString("localId", "UID-" + Math.abs(cleanEmail.hashCode() % 900000 + 100000));
                    String retEmail = res.optString("email", cleanEmail);
                    String name = res.optString("displayName", cleanEmail.split("@")[0]);
                    if (name == null || name.isEmpty())
                        name = cleanEmail.split("@")[0];
                    String avatar = res.optString("photoUrl", res.optString("profilePicture", ""));
                    if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                        avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=true&size=128";
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

                if (conn.getResponseCode() == 200) {
                    BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null)
                        sb.append(line);
                    br.close();

                    JSONObject res = new JSONObject(sb.toString());
                    if (res.optBoolean("ok", false)) {
                        String uid = res.optString("uid", "UID-" + Math.abs(cleanEmail.hashCode() % 900000 + 100000));
                        String retEmail = res.optString("email", cleanEmail);
                        String name = res.optString("display_name", cleanEmail.split("@")[0]);
                        String avatar = res.optString("avatar", res.optString("photoUrl", ""));
                        if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                            avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=true&size=128";
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
                        String uid = u.optString("uid", "UID-" + Math.abs(email.hashCode() % 900000 + 100000));
                        String retEmail = u.optString("email", email);
                        String name = u.optString("name", email.split("@")[0]);
                        String avatar = u.optString("avatar", u.optString("photoUrl", u.optString("picture", "")));
                        if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                            avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=true&size=128";
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
        }'''

    new_login_block = '''        private String checkSessionLock(String cleanEmail, String uid) {
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
            String genUid = "UID-" + Math.abs(cleanEmail.hashCode() % 900000 + 100000);
            String lockMsg = checkSessionLock(cleanEmail, genUid);
            if (lockMsg != null) {
                new Handler(Looper.getMainLooper()).post(new LoginErrorRunnable(callback, lockMsg));
                return;
            }
            String defaultName = cleanEmail.contains("@") ? cleanEmail.split("@")[0] : cleanEmail;
            String token = "ppmod_sso_token_" + System.currentTimeMillis();
            String avatar = "https://ui-avatars.com/api/?name=" + defaultName + "&background=10b981&color=fff&bold=true&rounded=true&size=128";
            new Handler(Looper.getMainLooper())
                    .post(new LoginSuccessRunnable(callback, genUid, cleanEmail, defaultName, avatar, 0, token));
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
                    String uid = res.optString("localId", "UID-" + Math.abs(cleanEmail.hashCode() % 900000 + 100000));
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
                        avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=true&size=128";
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
                        String uid = res.optString("uid", "UID-" + Math.abs(cleanEmail.hashCode() % 900000 + 100000));
                        String retEmail = res.optString("email", cleanEmail);
                        String name = res.optString("display_name", cleanEmail.split("@")[0]);
                        String avatar = res.optString("avatar", res.optString("photoUrl", ""));
                        if (avatar == null || avatar.trim().isEmpty() || !avatar.startsWith("http")) {
                            avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=true&size=128";
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
                        String uid = u.optString("uid", "UID-" + Math.abs(email.hashCode() % 900000 + 100000));
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
                            avatar = "https://ui-avatars.com/api/?name=" + name + "&background=6366f1&color=fff&bold=true&rounded=true&size=128";
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
        }'''

    if old_login_block not in c:
        print(f"Error: old_login_block not found in {file_path}")
        return False
    c = c.replace(old_login_block, new_login_block, 1)

    # 2. Add notifyDeviceLogout static method
    old_method_marker = '''    public static void registerDevice(final Context ctx, final AccountStorage storage) {'''
    new_method_addition = '''    public static void notifyDeviceLogout(final Context ctx, final String uid, final String email) {
        new Thread(new Runnable() {
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
        }).start();
    }

    public static void registerDevice(final Context ctx, final AccountStorage storage) {'''

    if old_method_marker not in c:
        print(f"Error: old_method_marker not found in {file_path}")
        return False
    c = c.replace(old_method_marker, new_method_addition, 1)

    # 3. In RegisterDeviceWorker, detect 409 and log out if locked out
    old_reg_rCode = '''                int rCode = conn.getResponseCode();
                if (rCode == 200 && storage != null) {'''
    new_reg_rCode = '''                int rCode = conn.getResponseCode();
                if (rCode == 409) {
                    if (storage != null && storage.isLoggedIn()) {
                        storage.clearUserSession();
                        storage.clearAccounts();
                        if (ctx != null) {
                            new Handler(Looper.getMainLooper()).post(new Runnable() {
                                @Override
                                public void run() {
                                    try {
                                        Toast.makeText(ctx,
                                                "এই একাউন্টটি অন্য ডিভাইসে লগইন করা হয়েছে। এই ডিভাইস থেকে লগআউট করা হলো।",
                                                Toast.LENGTH_LONG).show();
                                    } catch (Throwable ignored) {
                                    }
                                }
                            });
                        }
                    }
                }
                if (rCode == 200 && storage != null) {'''

    if old_reg_rCode not in c:
        print(f"Error: old_reg_rCode not found in {file_path}")
        return False
    c = c.replace(old_reg_rCode, new_reg_rCode, 1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(c)

    print(f"Successfully patched {file_path}")
    return True

f1 = "app/pp_server/src/com/vareon/playquest/CloudSyncClient.java"
f2 = "achievement_unlocker/app/pp_server/src/com/vareon/playquest/CloudSyncClient.java"
if patch_file(f1) and patch_file(f2):
    print("CloudSyncClient.java successfully patched in both locations!")
else:
    sys.exit(1)
