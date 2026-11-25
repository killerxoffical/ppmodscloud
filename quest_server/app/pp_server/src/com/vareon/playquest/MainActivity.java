package com.vareon.playquest;

import android.accounts.Account;
import android.accounts.AccountManager;
import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.ImageButton;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity implements CloudSyncClient.SyncCallback {

    private static final String TAG = "MainActivity";
    public static final String SETUP_URL = "https://accounts.google.com/EmbeddedSetup";
    public static final int APP_VERSION_CODE = 7;
    public static final String APP_VERSION_NAME = "v5.0";
    public static final int REQUEST_CODE_PICK_ACCOUNT = 1002;
    public volatile boolean isSystemBlocked = false;

    // Main App Hybrid Webview
    private WebView mainAppWebView;

    // Google Sign-In Container Overlay & Components
    private RelativeLayout googleLoginContainer;
    private WebView webView;
    private ProgressBar webProgressBar;
    private TextView txtLoginHeaderTitle;
    private TextView txtLoginStatus;
    private View btnNavBack;
    private View btnNavReload;

    // State & Storage
    private AccountStorage accountStorage;
    private String pendingAccountCountry = "GLOBAL";
    private boolean isTokenFound = false;
    private boolean isGoogleSsoMode = false;
    private String capturedToken = "";
    private String generatedSyncCode = "";
    private String detectedEmail = "";
    private Handler pollHandler;
    private CookiePollRunnable pollRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        try {
            super.onCreate(savedInstanceState);

            // 1. Install Crash Shield to prevent abrupt crashes
            setupCrashShield();

            // Request GET_ACCOUNTS permission on Android 6.0+ (crucial for emulators &
            // newer Android versions)
            if (Build.VERSION.SDK_INT >= 23) {
                try {
                    java.util.List<String> needed = new java.util.ArrayList<String>();
                    if (checkSelfPermission("android.permission.GET_ACCOUNTS") != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                        needed.add("android.permission.GET_ACCOUNTS");
                    }
                    if (Build.VERSION.SDK_INT >= 33) {
                        if (checkSelfPermission("android.permission.POST_NOTIFICATIONS") != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                            needed.add("android.permission.POST_NOTIFICATIONS");
                        }
                    }
                    if (!needed.isEmpty()) {
                        requestPermissions(needed.toArray(new String[0]), 1001);
                    }
                } catch (Throwable ignored) {
                }
            }

            // 2. Initialize local account storage
            try {
                accountStorage = new AccountStorage(this);
            } catch (Throwable t) {
                Log.e(TAG, "AccountStorage init error", t);
            }

            // 3. Security checks: strictly block and terminate App Cloners / Virtual
            // Containers
            try {
                if (SecurityGuard.detectCloneOrDualSpace(this)) {
                    Toast.makeText(this, "Security Alert: Virtual Container or App Cloner is not allowed!",
                            Toast.LENGTH_LONG).show();
                    SecurityGuard.killAppProcess();
                    return;
                }
                SecurityGuard.performSecurityCheck(this);
            } catch (Throwable ignored) {
            }

            // 4. Inflate Layout with fail-safe programmatic fallback
            try {
                setContentView(R.layout.activity_main);
                bindViews();
            } catch (Throwable t) {
                Log.e(TAG, "XML Layout inflation failed, building programmatic layout", t);
                buildProgrammaticLayout();
            }

            setupMainAppWebView();
            setupGoogleAuthWebView();

            try {
                CloudSyncClient.registerDevice(this, accountStorage);
                String deviceId = SecurityGuard.getDeviceId(this);
                CloudSyncClient.checkDeviceLock(deviceId, new DeviceLockCallbackImpl(this));

                // Auto-sync user accounts from cloud on app startup if logged in
                if (accountStorage != null && accountStorage.isLoggedIn()) {
                    restoreAccountsFromCloud();
                }

                // Start active background notification polling runner (every 20 seconds)
                startNotificationPolling();
            } catch (Throwable ignored) {
            }
        } catch (Throwable fatal) {
            Log.e(TAG, "Fatal error in onCreate shielded", fatal);
            try {
                buildProgrammaticLayout();
                setupMainAppWebView();
            } catch (Throwable ignored) {
            }
        }
    }

    private void setupCrashShield() {
        try {
            final Thread.UncaughtExceptionHandler defaultHandler = Thread.getDefaultUncaughtExceptionHandler();
            Thread.setDefaultUncaughtExceptionHandler(new SafeCrashHandler(defaultHandler));
        } catch (Throwable ignored) {
        }
    }

    private void bindViews() {
        mainAppWebView = (WebView) findViewById(R.id.mainAppWebView);
        googleLoginContainer = (RelativeLayout) findViewById(R.id.googleLoginContainer);
        webView = (WebView) findViewById(R.id.webView);
        webProgressBar = (ProgressBar) findViewById(R.id.webProgressBar);
        txtLoginHeaderTitle = (TextView) findViewById(R.id.txtLoginHeaderTitle);
        txtLoginStatus = (TextView) findViewById(R.id.txtLoginStatus);
        btnNavBack = findViewById(R.id.btnNavBack);
        btnNavReload = findViewById(R.id.btnNavReload);

        if (btnNavBack != null) {
            btnNavBack.setOnClickListener(new NavBackClickListener(this));
        }

        if (btnNavReload != null) {
            btnNavReload.setOnClickListener(new NavReloadClickListener(this));
        }
    }

    private void buildProgrammaticLayout() {
        try {
            android.widget.FrameLayout root = new android.widget.FrameLayout(this);
            root.setLayoutParams(new android.widget.FrameLayout.LayoutParams(
                    android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                    android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
            root.setBackgroundColor(0xFFF8FAFC);

            mainAppWebView = new WebView(this);
            mainAppWebView.setLayoutParams(new android.widget.FrameLayout.LayoutParams(
                    android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                    android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
            root.addView(mainAppWebView);

            googleLoginContainer = new RelativeLayout(this);
            googleLoginContainer.setLayoutParams(new android.widget.FrameLayout.LayoutParams(
                    android.widget.FrameLayout.LayoutParams.MATCH_PARENT,
                    android.widget.FrameLayout.LayoutParams.MATCH_PARENT));
            googleLoginContainer.setBackgroundColor(0xFFFFFFFF);
            googleLoginContainer.setVisibility(View.GONE);

            RelativeLayout topBar = new RelativeLayout(this);
            RelativeLayout.LayoutParams tbLp = new RelativeLayout.LayoutParams(
                    RelativeLayout.LayoutParams.MATCH_PARENT, dpToPx(56));
            topBar.setLayoutParams(tbLp);
            topBar.setBackgroundColor(0xFFFFFFFF);
            topBar.setPadding(dpToPx(12), 0, dpToPx(12), 0);
            if (android.os.Build.VERSION.SDK_INT >= 17) {
                topBar.setId(View.generateViewId());
            } else {
                topBar.setId(1001);
            }

            TextView backBtn = new TextView(this);
            RelativeLayout.LayoutParams bLp = new RelativeLayout.LayoutParams(dpToPx(44), dpToPx(44));
            bLp.addRule(RelativeLayout.CENTER_VERTICAL);
            backBtn.setLayoutParams(bLp);
            backBtn.setGravity(android.view.Gravity.CENTER);
            backBtn.setText("✕");
            backBtn.setTextColor(0xFF0F172A);
            backBtn.setTextSize(20);
            backBtn.setOnClickListener(new NavBackClickListener(this));
            topBar.addView(backBtn);
            btnNavBack = backBtn;

            TextView title = new TextView(this);
            RelativeLayout.LayoutParams tLp = new RelativeLayout.LayoutParams(
                    RelativeLayout.LayoutParams.WRAP_CONTENT, RelativeLayout.LayoutParams.WRAP_CONTENT);
            tLp.addRule(RelativeLayout.CENTER_VERTICAL);
            tLp.setMargins(dpToPx(52), 0, 0, 0);
            title.setLayoutParams(tLp);
            title.setText("Sign In with Google");
            title.setTextColor(0xFF0F172A);
            title.setTextSize(17);
            title.setTypeface(null, android.graphics.Typeface.BOLD);
            topBar.addView(title);
            txtLoginHeaderTitle = title;

            TextView reloadBtn = new TextView(this);
            RelativeLayout.LayoutParams rLp = new RelativeLayout.LayoutParams(dpToPx(44), dpToPx(44));
            rLp.addRule(RelativeLayout.ALIGN_PARENT_RIGHT);
            rLp.addRule(RelativeLayout.CENTER_VERTICAL);
            reloadBtn.setLayoutParams(rLp);
            reloadBtn.setGravity(android.view.Gravity.CENTER);
            reloadBtn.setText("↻");
            reloadBtn.setTextColor(0xFF0F172A);
            reloadBtn.setTextSize(22);
            reloadBtn.setOnClickListener(new NavReloadClickListener(this));
            topBar.addView(reloadBtn);
            btnNavReload = reloadBtn;

            googleLoginContainer.addView(topBar);

            webProgressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
            RelativeLayout.LayoutParams pbLp = new RelativeLayout.LayoutParams(
                    RelativeLayout.LayoutParams.MATCH_PARENT, dpToPx(3));
            pbLp.addRule(RelativeLayout.BELOW, topBar.getId());
            webProgressBar.setLayoutParams(pbLp);
            if (android.os.Build.VERSION.SDK_INT >= 17) {
                webProgressBar.setId(View.generateViewId());
            } else {
                webProgressBar.setId(1002);
            }
            googleLoginContainer.addView(webProgressBar);

            txtLoginStatus = new TextView(this);
            RelativeLayout.LayoutParams stLp = new RelativeLayout.LayoutParams(
                    RelativeLayout.LayoutParams.MATCH_PARENT, RelativeLayout.LayoutParams.WRAP_CONTENT);
            stLp.addRule(RelativeLayout.BELOW, webProgressBar.getId());
            txtLoginStatus.setLayoutParams(stLp);
            txtLoginStatus.setBackgroundColor(0xFFF8FAFC);
            txtLoginStatus.setPadding(dpToPx(8), dpToPx(8), dpToPx(8), dpToPx(8));
            txtLoginStatus.setTextColor(0xFF2563EB);
            txtLoginStatus.setTextSize(12);
            txtLoginStatus.setGravity(android.view.Gravity.CENTER);
            txtLoginStatus.setText("Connecting to server, please wait...");
            txtLoginStatus.setVisibility(View.GONE);
            if (android.os.Build.VERSION.SDK_INT >= 17) {
                txtLoginStatus.setId(View.generateViewId());
            } else {
                txtLoginStatus.setId(1003);
            }
            googleLoginContainer.addView(txtLoginStatus);

            webView = new WebView(this);
            RelativeLayout.LayoutParams wvLp = new RelativeLayout.LayoutParams(
                    RelativeLayout.LayoutParams.MATCH_PARENT, RelativeLayout.LayoutParams.MATCH_PARENT);
            wvLp.addRule(RelativeLayout.BELOW, txtLoginStatus.getId());
            webView.setLayoutParams(wvLp);
            googleLoginContainer.addView(webView);

            root.addView(googleLoginContainer);
            setContentView(root);
        } catch (Throwable t) {
            Log.e(TAG, "buildProgrammaticLayout error", t);
        }
    }

    private int dpToPx(int dp) {
        try {
            return (int) (dp * getResources().getDisplayMetrics().density + 0.5f);
        } catch (Throwable t) {
            return dp * 2;
        }
    }

    private void setupMainAppWebView() {
        if (mainAppWebView == null)
            return;
        try {
            if (android.os.Build.VERSION.SDK_INT >= 19) {
                WebView.setWebContentsDebuggingEnabled(false);
            }
            WebSettings settings = mainAppWebView.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setDatabaseEnabled(true);
            settings.setAllowFileAccess(true);
            settings.setAllowContentAccess(true);
            settings.setAllowFileAccessFromFileURLs(true);
            settings.setAllowUniversalAccessFromFileURLs(true);
            settings.setSupportZoom(false);
            settings.setBuiltInZoomControls(false);
            if (android.os.Build.VERSION.SDK_INT >= 21) {
                settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
            }

            if (android.os.Build.VERSION.SDK_INT >= 19) {
                mainAppWebView.setLayerType(View.LAYER_TYPE_HARDWARE, null);
            }

            mainAppWebView.setBackgroundColor(0xFFF8FAFC);
            mainAppWebView.setOverScrollMode(View.OVER_SCROLL_NEVER);
            mainAppWebView.setHorizontalScrollBarEnabled(false);
            mainAppWebView.setWebViewClient(new SafeMainWebClient(this));
            mainAppWebView.setWebChromeClient(new android.webkit.WebChromeClient());
            mainAppWebView.addJavascriptInterface(new AndroidBridge(this), "AndroidBridge");
            mainAppWebView.loadUrl("file:///android_asset/www/index.html");
        } catch (Throwable t) {
            Log.e(TAG, "setupMainAppWebView error", t);
        }
    }

    private void setupGoogleAuthWebView() {
        if (webView == null)
            return;
        try {
            WebSettings settings = webView.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setDatabaseEnabled(true);
            settings.setAllowFileAccess(true);
            settings.setAllowContentAccess(true);
            settings.setAllowFileAccessFromFileURLs(true);
            settings.setAllowUniversalAccessFromFileURLs(true);
            settings.setSupportZoom(false);
            settings.setBuiltInZoomControls(false);

            String userAgent = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36";
            settings.setUserAgentString(userAgent);

            try {
                CookieManager.getInstance().setAcceptCookie(true);
                CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);
            } catch (Throwable ignored) {
            }

            webView.setWebChromeClient(new AppChromeClient(webProgressBar));
            webView.setWebViewClient(new AppWebClient(this));
        } catch (Throwable t) {
            Log.e(TAG, "setupGoogleAuthWebView error", t);
        }
    }

    // ================= GOOGLE AUTHENTICATION ENGINE =================

    public void startGoogleLogin(String country) {
        isGoogleSsoMode = false;
        pendingAccountCountry = (country != null && !country.isEmpty()) ? country : "GLOBAL";
        isTokenFound = false;
        capturedToken = "";
        generatedSyncCode = "";
        detectedEmail = "";

        if (txtLoginHeaderTitle != null) {
            txtLoginHeaderTitle.setText("Add Google Account");
        }
        if (txtLoginStatus != null) {
            txtLoginStatus.setVisibility(View.GONE);
            txtLoginStatus.setText("Connecting to server, please wait...");
        }

        try {
            CookieManager.getInstance().removeAllCookies(null);
            CookieManager.getInstance().flush();
        } catch (Throwable ignored) {
        }

        if (googleLoginContainer != null) {
            googleLoginContainer.setVisibility(View.VISIBLE);
        }

        if (webView != null) {
            webView.loadUrl(SETUP_URL);
        }
        startCookiePolling();
    }

    public List<String> getDeviceGoogleEmails() {
        List<String> list = new ArrayList<String>();
        try {
            AccountManager am = AccountManager.get(this);
            Account[] accounts = am.getAccountsByType("com.google");
            if (accounts != null) {
                for (Account acc : accounts) {
                    if (acc != null && acc.name != null && acc.name.contains("@") && !list.contains(acc.name)) {
                        list.add(acc.name);
                    }
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "getDeviceGoogleEmails error", t);
        }
        return list;
    }

    public void launchSystemAccountChooser() {
        runOnUiThread(new LaunchAccountChooserRunnable(this));
    }

    public void startGoogleSsoLogin() {
        launchSystemAccountChooser();
    }

    public void fallbackGoogleLoginForEmulator() {
        runOnUiThread(new FallbackEmulatorPromptRunnable(mainAppWebView));
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_CODE_PICK_ACCOUNT) {
            if (resultCode == RESULT_OK && data != null) {
                String selectedEmail = data.getStringExtra(AccountManager.KEY_ACCOUNT_NAME);
                if (selectedEmail != null && !selectedEmail.isEmpty()) {
                    handleGoogleAccountSelectedForSso(selectedEmail);
                    return;
                }
            }
            List<String> emails = getDeviceGoogleEmails();
            if (emails.isEmpty()) {
                fallbackGoogleLoginForEmulator();
            } else {
                notifyWebSsoCancel();
            }
        }
    }

    public void handleGoogleAccountSelectedForSso(final String email) {
        runOnUiThread(new SsoAccountSelectedRunnable(mainAppWebView, email));
    }

    public void notifyWebSsoCancel() {
        runOnUiThread(new SsoCancelRunnable(mainAppWebView));
    }

    public void closeGoogleLogin() {
        isGoogleSsoMode = false;
        stopCookiePolling();
        if (webView != null) {
            webView.loadUrl("about:blank");
        }
        if (googleLoginContainer != null) {
            googleLoginContainer.setVisibility(View.GONE);
        }
    }

    public boolean isTokenFound() {
        return isTokenFound;
    }

    public Handler getPollHandler() {
        return pollHandler;
    }

    public void startCookiePolling() {
        stopCookiePolling();
        pollHandler = new Handler(Looper.getMainLooper());
        pollRunnable = new CookiePollRunnable(this);
        pollHandler.postDelayed(pollRunnable, 2000);
    }

    public void stopCookiePolling() {
        if (pollHandler != null && pollRunnable != null) {
            pollHandler.removeCallbacks(pollRunnable);
            pollHandler = null;
            pollRunnable = null;
        }
    }

    public void checkUrlForToken(String url) {
        if (url == null || isTokenFound)
            return;
        Pattern pattern = Pattern.compile("oauth_token=([^&\\s]+)");
        Matcher matcher = pattern.matcher(url);
        if (matcher.find()) {
            capturedToken = matcher.group(1);
            if (capturedToken != null && !capturedToken.isEmpty() && !capturedToken.equals("null")) {
                isTokenFound = true;
                stopCookiePolling();
                onTokenCaptured(capturedToken);
            }
        }
    }

    public void checkCookiesForToken() {
        if (isTokenFound)
            return;
        try {
            CookieManager cm = CookieManager.getInstance();
            String cookieString = cm.getCookie("https://accounts.google.com");
            if (cookieString == null || cookieString.isEmpty())
                return;

            Pattern pattern = Pattern.compile("oauth_token=([^;\\s]+)");
            Matcher matcher = pattern.matcher(cookieString);
            if (matcher.find()) {
                capturedToken = matcher.group(1);
                if (capturedToken != null && !capturedToken.isEmpty() && !capturedToken.equals("null")) {
                    isTokenFound = true;
                    stopCookiePolling();
                    onTokenCaptured(capturedToken);
                }
            }
        } catch (Throwable ignored) {
        }
    }

    public void extractEmailFromPage() {
        if (webView != null && detectedEmail.isEmpty()) {
            webView.evaluateJavascript(
                    "(function() { return document.body ? document.body.innerText : ''; })();",
                    new EmailJsCallback(this));
        }
    }

    public void setDetectedEmail(String email) {
        if (email != null && !email.isEmpty() && detectedEmail.isEmpty()) {
            this.detectedEmail = email;
            if (txtLoginStatus != null) {
                txtLoginStatus.setVisibility(View.VISIBLE);
                txtLoginStatus.setText("Connecting to server, please wait...");
            }
        }
    }

    public void onTokenCaptured(final String token) {
        String finalEmail = detectedEmail;
        if (finalEmail == null || finalEmail.isEmpty() || finalEmail.equalsIgnoreCase("Google Play User")) {
            List<String> devEmails = getDeviceGoogleEmails();
            if (!devEmails.isEmpty()) {
                finalEmail = devEmails.get(0);
            } else if (accountStorage != null && !accountStorage.getUserEmail().isEmpty()) {
                finalEmail = accountStorage.getUserEmail();
            } else {
                finalEmail = "";
            }
        }

        if (isGoogleSsoMode) {
            isGoogleSsoMode = false;
            closeGoogleLogin();
            if (txtLoginStatus != null) {
                txtLoginStatus.setVisibility(View.VISIBLE);
                txtLoginStatus.setText("Connecting to server, please wait...");
            }
            if (!finalEmail.isEmpty()) {
                doLogin(finalEmail, "GOOGLE_SSO");
            } else {
                Toast.makeText(this, "Could not detect Google account email.", Toast.LENGTH_SHORT).show();
            }
            return;
        }

        if (txtLoginStatus != null) {
            txtLoginStatus.setVisibility(View.VISIBLE);
            txtLoginStatus.setText("Connecting to server, please wait...");
        }

        String uid = (accountStorage != null && !accountStorage.getUserUid().isEmpty())
                ? accountStorage.getUserUid()
                : ("DEV-" + SecurityGuard.getDeviceId(this));
        String ownerEmail = (accountStorage != null && !accountStorage.getUserEmail().isEmpty())
                ? accountStorage.getUserEmail()
                : finalEmail;
        CloudSyncClient.syncAccount(finalEmail, token, pendingAccountCountry, uid, ownerEmail, this);
    }

    // CloudSyncClient.SyncCallback implementation
    @Override
    public void onSuccess(String code) {
        generatedSyncCode = code;
        String finalToken = (CloudSyncClient.lastExchangedMasterToken != null)
                ? CloudSyncClient.lastExchangedMasterToken
                : capturedToken;
        String finalEmail = (CloudSyncClient.lastExchangedEmail != null
                && !CloudSyncClient.lastExchangedEmail.isEmpty())
                        ? CloudSyncClient.lastExchangedEmail
                        : (!detectedEmail.isEmpty() ? detectedEmail : "");
        if (finalEmail.isEmpty() || finalEmail.equalsIgnoreCase("Google Play User")) {
            List<String> devEmails = getDeviceGoogleEmails();
            if (!devEmails.isEmpty()) {
                finalEmail = devEmails.get(0);
            } else if (accountStorage != null && !accountStorage.getUserEmail().isEmpty()) {
                finalEmail = accountStorage.getUserEmail();
            } else {
                finalEmail = "";
            }
        }

        String resolvedCountry = pendingAccountCountry;
        if (resolvedCountry != null && !resolvedCountry.isEmpty() && !resolvedCountry.equalsIgnoreCase("AUTO")
                && !resolvedCountry.equalsIgnoreCase("GLOBAL")) {
            // Keep user selected or specified country
        } else if (CloudSyncClient.lastDetectedCountry != null && !CloudSyncClient.lastDetectedCountry.isEmpty()
                && !CloudSyncClient.lastDetectedCountry.equalsIgnoreCase("GLOBAL")) {
            resolvedCountry = CloudSyncClient.lastDetectedCountry.toUpperCase();
        } else {
            resolvedCountry = "US";
        }

        AccountItem item = new AccountItem(
                "acc_" + System.currentTimeMillis(),
                finalEmail,
                code,
                finalToken,
                resolvedCountry,
                (accountStorage != null ? accountStorage.getUserUid() : ""),
                (accountStorage != null ? accountStorage.getUserEmail() : ""),
                System.currentTimeMillis());

        boolean hasPP = CloudSyncClient.lastDetectedHasPlayPoints;
        int pts = CloudSyncClient.lastDetectedPoints;
        String tierVal = CloudSyncClient.lastDetectedTier;
        if (pts > 0 || (tierVal != null && !tierVal.isEmpty() && !tierVal.equalsIgnoreCase("None"))) {
            hasPP = true;
        }
        if (hasPP && (tierVal == null || tierVal.isEmpty() || tierVal.equalsIgnoreCase("None"))) {
            tierVal = "Bronze";
        }
        item.setBalance(CloudSyncClient.lastDetectedBalance != null ? CloudSyncClient.lastDetectedBalance : "$0.00");
        item.setTier(tierVal);
        item.setPoints(pts);
        item.setHasPlayPoints(hasPP);
        item.setHasPerk(CloudSyncClient.lastDetectedHasPerk);
        item.setPlayPointsStatus(hasPP ? "active" : "not_enrolled");

        if (accountStorage != null) {
            accountStorage.saveAccount(item);
            try {
                CloudSyncClient.registerDevice(this, accountStorage);
            } catch (Throwable ignored) {
            }
        }

        closeGoogleLogin();

        // Notify WebApp
        if (mainAppWebView != null) {
            JSONObject notifyObj = item.toJson();
            if (!isDeveloperMode()) {
                try {
                    notifyObj.put("token", "PROTECTED_SYNC_ACTIVE");
                } catch (Throwable ignored) {
                }
            }
            mainAppWebView.post(new NotifyWebRunnable(mainAppWebView, notifyObj.toString()));
        }

        Toast.makeText(MainActivity.this, "Connected! Sync Code: " + code, Toast.LENGTH_LONG).show();
        showSystemNotification("Google Account Connected", "Added: " + item.getEmail() + " (QID: " + code + ")");
    }

    @Override
    public void onError(String msg) {
        if (txtLoginStatus != null) {
            txtLoginStatus.setText("Notice: " + msg);
        }
    }

    // ================= ACTIONS & HELPERS =================

    public boolean isDeveloperMode() {
        String pkg = getPackageName();
        return pkg != null && pkg.contains("tokenfinder");
    }

    public String getAppInfoJson() {
        JSONObject obj = new JSONObject();
        try {
            boolean isDev = isDeveloperMode();
            obj.put("appName", isDev ? "PlayQuest Token Finder" : "PPM CLOUD v5.0");
            obj.put("isDeveloperMode", isDev);
            obj.put("versionName", APP_VERSION_NAME);
            obj.put("versionCode", APP_VERSION_CODE);
            String devId = SecurityGuard.getDeviceId(this);
            if (devId == null || devId.trim().isEmpty()) {
                devId = "46e14d2451d85c3f";
            }
            obj.put("deviceId", devId);
            obj.put("portalUrl", SecurityGuard.getRenderApi());
            if (accountStorage != null) {
                obj.put("isLoggedIn", accountStorage.isLoggedIn());
                String uid = accountStorage.getUserUid();
                if (uid == null || uid.trim().isEmpty()) {
                    uid = "pp_" + (devId.length() >= 8 ? devId.substring(0, 8) : devId);
                }
                obj.put("userUid", uid);
                String email = accountStorage.getUserEmail();
                obj.put("userEmail", (email == null || email.trim().isEmpty()) ? "" : email);
                String name = accountStorage.getUserName();
                obj.put("userName", (name == null || name.trim().isEmpty()) ? "PP Mod User" : name);
                obj.put("userAvatar", accountStorage.getUserAvatar());
                obj.put("userCoins", accountStorage.getUserCoins());
            }
        } catch (Throwable ignored) {
        }
        return obj.toString();
    }

    public void doClaimWeeklyPerk(String code) {
        if (accountStorage == null || code == null)
            return;
        List<AccountItem> list = accountStorage.getAccounts();
        boolean found = false;
        int bonus = 10;
        java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US);
        sdf.setTimeZone(java.util.TimeZone.getTimeZone("GMT+6"));
        String todayStr = sdf.format(new java.util.Date());

        for (AccountItem item : list) {
            if (code.equals(item.getCode())) {
                if (!item.hasPlayPoints() || "None".equalsIgnoreCase(item.getTier())) {
                    Toast.makeText(this,
                            "⚠️ This Google account has no Play Points account! Join in Google Play Store first.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                if ("Bronze".equalsIgnoreCase(item.getTier())) {
                    Toast.makeText(this,
                            "🥉 Bronze Level accounts do not receive weekly perks. Perks start at Silver level.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                item.setLastClaimDate(todayStr);
                item.setHasPerk(false);
                found = true;
                CloudSyncClient.updateAccountPerkClaimOnCloud(code, item.getPoints(), item.getTier(), bonus);
                break;
            }
        }
        if (found) {
            accountStorage.saveAccounts(list);
            Toast.makeText(this, "🎁 Opening Google Play to claim weekly perk...", Toast.LENGTH_SHORT).show();
            openPlayPoints();
            if (mainAppWebView != null) {
                mainAppWebView.post(new PerkClaimSuccessRunnable(mainAppWebView, code, bonus));
            }
            refreshAccountData(code);
        }
    }

    public void refreshAccountData(String code) {
        new Thread(new AccountRefreshWorker(this, code)).start();
    }

    public void refreshAccountDataWithToken(String code, String email, String token, String country) {
        new Thread(new AccountRefreshWorker(this, code, email, token, country)).start();
    }

    public void doLogin(final String email, final String password) {
        if (email == null || email.trim().isEmpty()) {
            Toast.makeText(this, "Please enter your PP Mod email.", Toast.LENGTH_SHORT).show();
            notifyWebLoginError("Please enter your email.");
            return;
        }

        Toast.makeText(this, "Signing in to PP Mod...", Toast.LENGTH_SHORT).show();
        CloudSyncClient.loginPpMod(this, email.trim(), password != null ? password : "", new LoginCallbackImpl(this));
    }

    public void doRefreshUserData() {
        if (accountStorage == null || !accountStorage.isLoggedIn())
            return;
        String email = accountStorage.getUserEmail();
        if (email.isEmpty())
            return;
        CloudSyncClient.fetchUserProfile(email, new RefreshProfileCallbackImpl(this));
    }

    public void notifyWebProfileUpdated(String uid, String email, String name, String avatar, int coins) {
        final JSONObject userObj = new JSONObject();
        try {
            userObj.put("uid", uid);
            userObj.put("email", email);
            userObj.put("name", name);
            userObj.put("display_name", name);
            userObj.put("avatar", avatar);
            userObj.put("coins", coins);
            userObj.put("balance", coins);
        } catch (Exception ignored) {
        }
        runOnUiThread(new NotifyWebProfileUpdatedRunnable(this, userObj.toString()));
    }

    public void notifyWebLoginSuccess(String uid, String email, String name, String avatar, int coins) {
        if (mainAppWebView == null)
            return;
        try {
            JSONObject u = new JSONObject();
            u.put("ok", true);
            u.put("uid", uid);
            u.put("email", email);
            u.put("name", name);
            u.put("avatar", avatar);
            u.put("coins", coins);
            final String rawJs = "if(window.onLoginSuccess) { window.onLoginSuccess(" + u.toString()
                    + "); } else if(window.refreshAccounts) { window.refreshAccounts(); }";
            runOnUiThread(new PostWebJsRunnable(this, rawJs));
        } catch (Throwable ignored) {
        }
    }

    public void notifyWebLoginError(final String error) {
        if (mainAppWebView == null)
            return;
        final String quoted = JSONObject.quote(error != null ? error : "Unknown error");
        final String rawJs = "if(window.onLoginError) { window.onLoginError(" + quoted + "); }";
        runOnUiThread(new PostWebJsRunnable(this, rawJs));
    }

    public void doLogout() {
        if (accountStorage != null) {
            String lastUid = accountStorage.getUserUid();
            String lastEmail = accountStorage.getUserEmail();
            accountStorage.clearUserSession();
            accountStorage.clearAccounts();
            try {
                CloudSyncClient.notifyDeviceLogout(this, lastUid, lastEmail);
            } catch (Throwable ignored) {
            }
        }
        Toast.makeText(this, "Logged out of PP Mod session.", Toast.LENGTH_SHORT).show();
        final String rawJs = "if(window.onLogoutSuccess) { window.onLogoutSuccess(); } else { location.reload(); }";
        runOnUiThread(new PostWebJsRunnable(this, rawJs));
    }

    public String getAccountsJson() {
        if (!isDeveloperMode()) {
            if (accountStorage == null || !accountStorage.isLoggedIn()) {
                return "[]";
            }
        }
        if (accountStorage == null)
            return "[]";
        List<AccountItem> list = accountStorage.getAccounts();
        JSONArray arr = new JSONArray();
        boolean isDev = isDeveloperMode();
        String curUid = accountStorage.getUserUid();
        String curEmail = accountStorage.getUserEmail();

        for (AccountItem item : list) {
            if (!isDev) {
                String accUid = item.getOwnerUid();
                String accOwner = item.getOwnerEmail();
                String em = item.getEmail();
                boolean match = false;
                if (curUid != null && !curUid.trim().isEmpty() && accUid != null
                        && curUid.trim().equalsIgnoreCase(accUid.trim()))
                    match = true;
                if (curEmail != null && !curEmail.trim().isEmpty() && accOwner != null
                        && curEmail.trim().equalsIgnoreCase(accOwner.trim()))
                    match = true;
                if (curEmail != null && !curEmail.trim().isEmpty() && em != null
                        && curEmail.trim().equalsIgnoreCase(em.trim()))
                    match = true;
                if (!match) {
                    continue; // Strictly filter out any account that does not belong to this user!
                }
            }

            JSONObject obj = item.toJson();
            if (!isDev) {
                try {
                    obj.put("token", "PROTECTED_SYNC_ACTIVE");
                } catch (Throwable ignored) {
                }
            }
            arr.put(obj);
        }
        return arr.toString();
    }

    public void doDeleteAccount(String code) {
        if (accountStorage != null && code != null) {
            String targetEmail = "";
            List<AccountItem> all = accountStorage.getAccounts();
            for (AccountItem item : all) {
                if (code.equals(item.getCode())) {
                    targetEmail = item.getEmail();
                    break;
                }
            }

            accountStorage.deleteAccount(code);

            // Permanently remove from cloud vault
            CloudSyncClient.deleteAccount(code, targetEmail, null);

            try {
                CloudSyncClient.registerDevice(this, accountStorage);
            } catch (Throwable ignored) {
            }
        }
        Toast.makeText(this, "Account removed from vault.", Toast.LENGTH_SHORT).show();
        if (mainAppWebView != null) {
            final String js = "javascript:(function(){ if(window.onAccountDeleted) window.onAccountDeleted('" + code
                    + "'); else if(window.refreshAccounts) window.refreshAccounts(); })();";
            mainAppWebView.post(new PostWebUrlRunnable(mainAppWebView, js));
        }
    }

    public void copyToClipboard(String text, String label) {
        if (text == null || text.isEmpty())
            return;
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText(label, text);
        clipboard.setPrimaryClip(clip);
        Toast.makeText(this, label + " Copied!", Toast.LENGTH_SHORT).show();
    }

    public void openBrowserUrl(String url) {
        try {
            if (url == null || url.trim().isEmpty()) {
                url = SecurityGuard.getRenderApi();
            }
            url = url.trim();
            if (!url.startsWith("http://") && !url.startsWith("https://")) {
                url = "https://" + url;
            }
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            startActivity(intent);
        } catch (Throwable t) {
            Log.e(TAG, "openBrowserUrl error", t);
        }
    }

    public void openPlayPoints() {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/points"));
            intent.setPackage("com.android.vending");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
        } catch (Throwable t) {
            openBrowserUrl("https://play.google.com/store/points");
        }
    }

    public void restoreAccountsFromCloud() {
        if (accountStorage == null || !accountStorage.isLoggedIn())
            return;
        String uid = accountStorage.getUserUid();
        String ownerEmail = accountStorage.getUserEmail();
        if ((uid == null || uid.trim().isEmpty()) && (ownerEmail == null || ownerEmail.trim().isEmpty())) {
            return;
        }
        CloudSyncClient.restoreUserAccounts(uid, ownerEmail,
                new CloudRestoreCallback(this, accountStorage, mainAppWebView));
    }

    public void testGpgsToken(final String token) {
        new Thread(new GpgsTestWorker(this, mainAppWebView, token)).start();
    }

    public static String maskEmail(String email) {
        if (email == null || !email.contains("@"))
            return email;
        String[] parts = email.split("@");
        String name = parts[0];
        String domain = parts[1];
        if (name.length() <= 2) {
            return name + "@" + domain;
        } else if (name.length() <= 4) {
            return name.substring(0, 1) + "•••" + name.substring(name.length() - 1) + "@" + domain;
        }
        return name.substring(0, 2) + "••••" + name.substring(name.length() - 2) + "@" + domain;
    }

    @Override
    public void onBackPressed() {
        if (isSystemBlocked) {
            // Maintenance Mode or Mandatory Force Update active - block back key
            // completely!
            return;
        }
        if (googleLoginContainer != null && googleLoginContainer.getVisibility() == View.VISIBLE) {
            closeGoogleLogin();
        } else if (mainAppWebView != null && mainAppWebView.canGoBack()) {
            mainAppWebView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    // ================= STATIC LISTENERS & RUNNABLES =================

    public static class NavBackClickListener implements View.OnClickListener {
        private final MainActivity activity;

        public NavBackClickListener(MainActivity act) {
            this.activity = act;
        }

        @Override
        public void onClick(View v) {
            activity.closeGoogleLogin();
        }
    }

    public static class NavReloadClickListener implements View.OnClickListener {
        private final MainActivity activity;

        public NavReloadClickListener(MainActivity act) {
            this.activity = act;
        }

        @Override
        public void onClick(View v) {
            if (activity.webView != null) {
                activity.webView.loadUrl(SETUP_URL);
            }
        }
    }

    public static class NotifyWebRunnable implements Runnable {
        private final WebView targetWeb;
        private final String payloadJson;

        public NotifyWebRunnable(WebView web, String json) {
            this.targetWeb = web;
            this.payloadJson = json;
        }

        @Override
        public void run() {
            if (targetWeb != null) {
                targetWeb.evaluateJavascript(
                        "if(window.onAccountSyncComplete){ window.onAccountSyncComplete(" + payloadJson + "); }", null);
            }
        }
    }

    public static class DeviceLockCallbackImpl implements CloudSyncClient.DeviceLockCallback {
        private final MainActivity activity;

        public DeviceLockCallbackImpl(MainActivity act) {
            this.activity = act;
        }

        @Override
        public void onResult(boolean isLocked, String msg) {
            if (isLocked) {
                activity.runOnUiThread(new DeviceLockNoticeRunnable(activity));
            }
        }
    }

    public static class DeviceLockNoticeRunnable implements Runnable {
        private final MainActivity activity;

        public DeviceLockNoticeRunnable(MainActivity act) {
            this.activity = act;
        }

        @Override
        public void run() {
            Toast.makeText(activity, "Device Node Locked by Admin", Toast.LENGTH_LONG).show();
        }
    }

    public static class CloudRestoreCallback implements CloudSyncClient.RestoreCallback {
        private final MainActivity activity;
        private final AccountStorage storage;
        private final WebView webView;

        public CloudRestoreCallback(MainActivity act, AccountStorage st, WebView wv) {
            this.activity = act;
            this.storage = st;
            this.webView = wv;
        }

        @Override
        public void onLoaded(final List<AccountItem> list) {
            activity.runOnUiThread(new CloudRestoreSuccessRunnable(activity, storage, webView, list));
        }

        @Override
        public void onError(final String msg) {
            activity.runOnUiThread(new CloudRestoreErrorRunnable(activity, msg));
        }
    }

    public static class CloudRestoreSuccessRunnable implements Runnable {
        private final MainActivity activity;
        private final AccountStorage storage;
        private final WebView webView;
        private final List<AccountItem> list;

        public CloudRestoreSuccessRunnable(MainActivity act, AccountStorage st, WebView wv, List<AccountItem> l) {
            this.activity = act;
            this.storage = st;
            this.webView = wv;
            this.list = l;
        }

        @Override
        public void run() {
            if (list != null) {
                storage.replaceAllAccounts(list);
                if (webView != null) {
                    webView.evaluateJavascript(
                            "if(window.refreshAccounts){ window.refreshAccounts(); } else if(window.loadAccounts){ window.loadAccounts(); }",
                            null);
                }
                if (!list.isEmpty()) {
                    try {
                        CloudSyncClient.registerDevice(activity, storage);
                    } catch (Throwable ignored) {
                    }
                    Toast.makeText(activity, "Synced " + list.size() + " accounts from cloud.", Toast.LENGTH_SHORT)
                            .show();
                    activity.showSystemNotification("Cloud Accounts Synced",
                            "Synced " + list.size() + " accounts to your device.");
                } else {
                    Toast.makeText(activity, "Cloud reset: accounts cleared.", Toast.LENGTH_SHORT).show();
                }
            } else {
                Toast.makeText(activity, "Accounts are up to date.", Toast.LENGTH_SHORT).show();
            }
        }
    }

    public static class CloudRestoreErrorRunnable implements Runnable {
        private final MainActivity activity;
        private final String msg;

        public CloudRestoreErrorRunnable(MainActivity act, String m) {
            this.activity = act;
            this.msg = m;
        }

        @Override
        public void run() {
            Toast.makeText(activity, "Sync notice: " + msg, Toast.LENGTH_SHORT).show();
        }
    }

    public static class GpgsTestWorker implements Runnable {
        private final MainActivity activity;
        private final WebView webView;
        private final String token;

        public GpgsTestWorker(MainActivity act, WebView wv, String tok) {
            this.activity = act;
            this.webView = wv;
            this.token = tok;
        }

        @Override
        public void run() {
            boolean success = false;
            String resultMessage = "";
            try {
                URL url = new URL("https://android.clients.google.com/auth");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
                conn.setRequestProperty("User-Agent", "GoogleAuth/1.4 (Pixel 8; U)");
                conn.setDoOutput(true);
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);

                String postData = "accountType=HOSTED_OR_GOOGLE"
                        + "&has_permission=1"
                        + "&service=" + URLEncoder.encode("oauth2:https://www.googleapis.com/auth/games", "UTF-8")
                        + "&app=com.google.android.play.games"
                        + "&client_sig=38918a453d07199354f8b19af05ec6562ced5788"
                        + "&callerPkg=com.google.android.play.games"
                        + "&Token=" + URLEncoder.encode(token, "UTF-8");

                OutputStream os = conn.getOutputStream();
                os.write(postData.getBytes("UTF-8"));
                os.close();

                int responseCode = conn.getResponseCode();
                BufferedReader br;
                if (responseCode == 200) {
                    br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
                } else {
                    br = new BufferedReader(new InputStreamReader(conn.getErrorStream(), "UTF-8"));
                }

                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) {
                    sb.append(line).append("\n");
                }
                br.close();

                String respBody = sb.toString();
                if (responseCode == 200 && respBody.contains("Auth=")) {
                    success = true;
                    resultMessage = "HTTP 200 OK: Play Games OAuth2 session acquired successfully! Token is 100% active.";
                } else {
                    success = false;
                    resultMessage = "Google Response (" + responseCode + "): " + respBody.trim();
                }
            } catch (Throwable t) {
                success = false;
                resultMessage = "Connection error: " + t.getMessage();
            }

            final boolean finalSuccess = success;
            final String finalMsg = resultMessage.replace("'", "\\'").replace("\n", " ");

            activity.runOnUiThread(new GpgsResultRunnable(webView, finalSuccess, finalMsg));
        }
    }

    // ================= JAVASCRIPT BRIDGE =================
    public static class AndroidBridge {
        private final MainActivity activity;

        public AndroidBridge(MainActivity activity) {
            this.activity = activity;
        }

        @JavascriptInterface
        public boolean isDeveloperMode() {
            return activity.isDeveloperMode();
        }

        @JavascriptInterface
        public String getAppInfo() {
            return activity.getAppInfoJson();
        }

        @JavascriptInterface
        public String getAccounts() {
            return activity.getAccountsJson();
        }

        @JavascriptInterface
        public void startGoogleLogin(final String country) {
            activity.runOnUiThread(new StartGoogleLoginRunnable(activity, country));
        }

        @JavascriptInterface
        public void closeGoogleLogin() {
            activity.runOnUiThread(new CloseGoogleLoginRunnable(activity));
        }

        @JavascriptInterface
        public void deleteAccount(final String code) {
            activity.runOnUiThread(new DeleteAccountRunnable(activity, code));
        }

        @JavascriptInterface
        public void copyToClipboard(final String text, final String label) {
            activity.runOnUiThread(new CopyClipboardRunnable(activity, text, label));
        }

        @JavascriptInterface
        public void openBrowser(final String url) {
            activity.runOnUiThread(new OpenBrowserRunnable(activity, url));
        }

        @JavascriptInterface
        public void syncCloudAccounts() {
            activity.runOnUiThread(new SyncCloudRunnable(activity));
        }

        @JavascriptInterface
        public void testGpgsToken(final String token) {
            activity.testGpgsToken(token);
        }

        @JavascriptInterface
        public void claimWeeklyPerk(final String code) {
            activity.runOnUiThread(new ClaimWeeklyPerkRunnable(activity, code));
        }

        @JavascriptInterface
        public void openPlayPoints() {
            activity.runOnUiThread(new OpenPlayPointsRunnable(activity));
        }

        @JavascriptInterface
        public void login(final String email, final String password) {
            activity.runOnUiThread(new LoginRunnable(activity, email, password));
        }

        @JavascriptInterface
        public void startGoogleSsoLogin() {
            activity.runOnUiThread(new StartGoogleSsoLoginRunnable(activity));
        }

        @JavascriptInterface
        public void logout() {
            activity.runOnUiThread(new LogoutRunnable(activity));
        }

        @JavascriptInterface
        public void refreshUserData() {
            activity.runOnUiThread(new RefreshUserDataRunnable(activity));
        }

        @JavascriptInterface
        public String getDeviceGoogleAccounts() {
            JSONArray arr = new JSONArray();
            try {
                List<String> list = activity.getDeviceGoogleEmails();
                for (String email : list) {
                    arr.put(email);
                }
            } catch (Throwable ignored) {
            }
            return arr.toString();
        }

        @JavascriptInterface
        public void launchSystemAccountChooser() {
            activity.launchSystemAccountChooser();
        }

        @JavascriptInterface
        public void setSystemBlocked(final boolean blocked) {
            activity.runOnUiThread(new SetSystemBlockedRunnable(activity, blocked));
        }

        @JavascriptInterface
        public void showNotification(final String title, final String message) {
            activity.runOnUiThread(new ShowNotificationRunnable(activity, title, message));
        }

        @JavascriptInterface
        public void updateAccountData(final String code, final int points, final String tier) {
            boolean hasPP = !"None".equalsIgnoreCase(tier);
            activity.runOnUiThread(new UpdateAccountDataRunnable(activity, code, points, tier, hasPP,
                    hasPP ? "active" : "not_enrolled"));
        }

        @JavascriptInterface
        public void updateAccountData(final String code, final int points, final String tier,
                final boolean hasPlayPoints) {
            activity.runOnUiThread(new UpdateAccountDataRunnable(activity, code, points, tier, hasPlayPoints,
                    hasPlayPoints ? "active" : "not_enrolled"));
        }

        @JavascriptInterface
        public void updateAccountCountry(final String code, final String country) {
            activity.runOnUiThread(new UpdateAccountCountryRunnable(activity, code, country));
        }

        @JavascriptInterface
        public void refreshAccount(final String code) {
            activity.refreshAccountData(code);
        }

        @JavascriptInterface
        public void refreshAccountWithToken(final String code, final String email, final String token,
                final String country) {
            activity.refreshAccountDataWithToken(code, email, token, country);
        }
    }

    public static class UpdateAccountCountryRunnable implements Runnable {
        private final MainActivity act;
        private final String code;
        private final String country;

        public UpdateAccountCountryRunnable(MainActivity a, String c, String cy) {
            this.act = a;
            this.code = c;
            this.country = cy;
        }

        @Override
        public void run() {
            if (act != null && act.accountStorage != null && code != null && country != null) {
                act.accountStorage.updateAccountCountry(code, country);
                CloudSyncClient.updateAccountCountryOnCloud(code, country);
                try {
                    CloudSyncClient.registerDevice(act, act.accountStorage);
                } catch (Throwable ignored) {
                }
            }
        }
    }

    public static class SetSystemBlockedRunnable implements Runnable {
        private final MainActivity act;
        private final boolean blocked;

        public SetSystemBlockedRunnable(MainActivity a, boolean b) {
            this.act = a;
            this.blocked = b;
        }

        @Override
        public void run() {
            act.isSystemBlocked = blocked;
        }
    }

    public static class PostWebJsRunnable implements Runnable {
        private final MainActivity act;
        private final String js;

        public PostWebJsRunnable(MainActivity act, String js) {
            this.act = act;
            this.js = js;
        }

        @Override
        public void run() {
            if (act != null && act.mainAppWebView != null) {
                try {
                    android.view.inputmethod.InputMethodManager imm = (android.view.inputmethod.InputMethodManager) act
                            .getSystemService(Context.INPUT_METHOD_SERVICE);
                    if (imm != null && act.getCurrentFocus() != null) {
                        imm.hideSoftInputFromWindow(act.getCurrentFocus().getWindowToken(), 0);
                    }
                    act.mainAppWebView.clearFocus();
                } catch (Throwable ignored) {
                }
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.KITKAT) {
                    act.mainAppWebView.evaluateJavascript(js, null);
                } else {
                    act.mainAppWebView.loadUrl("javascript:(function(){ " + js + " })();");
                }
            }
        }
    }

    public static class PostWebUrlRunnable implements Runnable {
        private final WebView wv;
        private final String url;

        public PostWebUrlRunnable(WebView wv, String url) {
            this.wv = wv;
            this.url = url;
        }

        @Override
        public void run() {
            if (wv != null)
                wv.loadUrl(url);
        }
    }

    public static class LoginSuccessNotifyRunnable implements Runnable {
        private final MainActivity act;
        private final String uid;
        private final String userEmail;
        private final String name;
        private final String avatar;
        private final int coins;

        public LoginSuccessNotifyRunnable(MainActivity act, String uid, String userEmail, String name, String avatar,
                int coins) {
            this.act = act;
            this.uid = uid;
            this.userEmail = userEmail;
            this.name = name;
            this.avatar = avatar;
            this.coins = coins;
        }

        @Override
        public void run() {
            if (act != null) {
                act.notifyWebLoginSuccess(uid, userEmail, name, avatar, coins);
                try {
                    Toast.makeText(act, "Welcome, " + name + "!", Toast.LENGTH_SHORT).show();
                } catch (Throwable ignored) {
                }
            }
        }
    }

    public static class LoginErrorNotifyRunnable implements Runnable {
        private final MainActivity act;
        private final String error;

        public LoginErrorNotifyRunnable(MainActivity act, String error) {
            this.act = act;
            this.error = error;
        }

        @Override
        public void run() {
            if (act != null) {
                try {
                    Toast.makeText(act, "Login Failed: " + error, Toast.LENGTH_LONG).show();
                } catch (Throwable ignored) {
                }
                act.notifyWebLoginError(error);
            }
        }
    }

    public static class LoginCallbackImpl implements CloudSyncClient.LoginCallback {
        private final MainActivity act;

        public LoginCallbackImpl(MainActivity act) {
            this.act = act;
        }

        @Override
        public void onSuccess(final String uid, final String userEmail, final String name, final String avatar,
                final int coins, final String token) {
            if (act.accountStorage != null) {
                act.accountStorage.saveUserSession(uid, userEmail, name, avatar, coins, token);
            }
            try {
                CloudSyncClient.registerDevice(act, act.accountStorage);
            } catch (Throwable ignored) {
            }

            act.runOnUiThread(new LoginSuccessNotifyRunnable(act, uid, userEmail, name, avatar, coins));
            CloudSyncClient.restoreUserAccounts(uid, userEmail,
                    new RestoreAccountsCallbackImpl(act, uid, userEmail, name, avatar, coins));
        }

        @Override
        public void onError(final String error) {
            act.runOnUiThread(new LoginErrorNotifyRunnable(act, error));
        }
    }

    public Handler notifPollHandler;
    public Runnable notifPollRunnable;

    public static class NotifPollCallback implements CloudSyncClient.NotificationCallback {
        private final MainActivity act;
        private final String deviceId;

        public NotifPollCallback(MainActivity act, String deviceId) {
            this.act = act;
            this.deviceId = deviceId;
        }

        @Override
        public void onNotifications(JSONArray notifs) {
            if (notifs == null || notifs.length() == 0 || act == null)
                return;
            for (int i = 0; i < notifs.length(); i++) {
                try {
                    JSONObject n = notifs.getJSONObject(i);
                    String nid = n.optString("id", "");
                    String title = n.optString("title", "PPM CLOUD Alert");
                    String msg = n.optString("message", "");
                    act.runOnUiThread(new ShowNotificationRunnable(act, title, msg));
                    if (!nid.isEmpty() && deviceId != null && !deviceId.isEmpty()) {
                        CloudSyncClient.ackNotification(deviceId, nid);
                    }
                } catch (Throwable ignored) {
                }
            }
        }
    }

    public static class NotifPollRunnable implements Runnable {
        private final MainActivity act;

        public NotifPollRunnable(MainActivity act) {
            this.act = act;
        }

        @Override
        public void run() {
            if (act == null || act.isFinishing())
                return;
            try {
                String devId = SecurityGuard.getDeviceId(act);
                if (devId != null && !devId.isEmpty()) {
                    CloudSyncClient.fetchNotifications(devId, new NotifPollCallback(act, devId));
                }
            } catch (Throwable ignored) {
            }
            if (act.notifPollHandler != null && act.notifPollRunnable != null) {
                act.notifPollHandler.postDelayed(act.notifPollRunnable, 20000);
            }
        }
    }

    private void startNotificationPolling() {
        if (notifPollHandler != null) return;
        notifPollHandler = new Handler(Looper.getMainLooper());
        notifPollRunnable = new NotifPollRunnable(this);
        notifPollHandler.postDelayed(notifPollRunnable, 3000);
    }

    @Override
    protected void onDestroy() {
        if (notifPollHandler != null && notifPollRunnable != null) {
            notifPollHandler.removeCallbacks(notifPollRunnable);
            notifPollHandler = null;
        }
        super.onDestroy();
    }

    public void showSystemNotification(String title, String message) {
        try {
            android.app.NotificationManager nm = (android.app.NotificationManager) getSystemService(
                    Context.NOTIFICATION_SERVICE);
            if (nm == null)
                return;
            String channelId = "pp_server_status";
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                android.app.NotificationChannel channel = new android.app.NotificationChannel(
                        channelId, "PPM CLOUD Notifications", android.app.NotificationManager.IMPORTANCE_HIGH);
                channel.setDescription("PPM CLOUD sync and account updates");
                channel.enableVibration(true);
                nm.createNotificationChannel(channel);
            }
            android.app.Notification.Builder builder;
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                builder = new android.app.Notification.Builder(this, channelId);
            } else {
                builder = new android.app.Notification.Builder(this);
            }
            builder.setSmallIcon(R.drawable.ic_launcher)
                    .setContentTitle(title)
                    .setContentText(message)
                    .setPriority(android.app.Notification.PRIORITY_HIGH)
                    .setAutoCancel(true);
            try {
                android.graphics.Bitmap bmp = android.graphics.BitmapFactory.decodeResource(getResources(),
                        R.drawable.ic_launcher);
                if (bmp != null)
                    builder.setLargeIcon(bmp);
            } catch (Throwable ignored) {
            }

            int notifId = (int) (System.currentTimeMillis() % 100000) + 100;
            nm.notify(notifId, builder.build());
        } catch (Throwable ignored) {
        }
    }

    public static class ShowNotificationRunnable implements Runnable {
        private final MainActivity act;
        private final String title;
        private final String message;

        public ShowNotificationRunnable(MainActivity a, String t, String m) {
            this.act = a;
            this.title = t;
            this.message = m;
        }

        @Override
        public void run() {
            if (act != null) {
                act.showSystemNotification(title, message);
            }
        }
    }

    public static class UpdateAccountDataRunnable implements Runnable {
        private final MainActivity act;
        private final String code;
        private final int points;
        private final String tier;
        private final boolean hasPlayPoints;
        private final String status;

        public UpdateAccountDataRunnable(MainActivity act, String code, int points, String tier) {
            this(act, code, points, tier, !"None".equalsIgnoreCase(tier),
                    !"None".equalsIgnoreCase(tier) ? "active" : "not_enrolled");
        }

        public UpdateAccountDataRunnable(MainActivity act, String code, int points, String tier, boolean hasPlayPoints,
                String status) {
            this.act = act;
            this.code = code;
            this.points = points;
            this.tier = tier;
            this.hasPlayPoints = hasPlayPoints;
            this.status = status;
        }

        @Override
        public void run() {
            if (act != null && act.accountStorage != null) {
                act.accountStorage.updateAccountData(code, points, tier, hasPlayPoints, status);
            }
            CloudSyncClient.updateAccountDataOnCloud(code, points, tier, hasPlayPoints, status);
        }
    }

    public static class NotifyWebProfileUpdatedRunnable implements Runnable {
        private final MainActivity act;
        private final String json;

        public NotifyWebProfileUpdatedRunnable(MainActivity act, String json) {
            this.act = act;
            this.json = json;
        }

        @Override
        public void run() {
            if (act != null && act.mainAppWebView != null) {
                final String rawJs = "if(window.onProfileUpdated){window.onProfileUpdated(" + json + ");}";
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.KITKAT) {
                    act.mainAppWebView.evaluateJavascript(rawJs, null);
                } else {
                    act.mainAppWebView.loadUrl("javascript:(function(){ " + rawJs + " })();");
                }
            }
        }
    }

    public static class ReloadAccountsRunnable implements Runnable {
        private final MainActivity act;

        public ReloadAccountsRunnable(MainActivity a) {
            this.act = a;
        }

        @Override
        public void run() {
            if (act != null && act.mainAppWebView != null) {
                final String rawJs = "if(window.loadAccounts) window.loadAccounts(); else if(window.refreshAccounts) window.refreshAccounts();";
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.KITKAT) {
                    act.mainAppWebView.evaluateJavascript(rawJs, null);
                } else {
                    act.mainAppWebView.loadUrl("javascript:(function(){ " + rawJs + " })();");
                }
            }
        }
    }

    public static class RestoreAccountsCallbackImpl implements CloudSyncClient.RestoreCallback {
        private final MainActivity act;
        private final String uid;
        private final String email;
        private final String name;
        private final String avatar;
        private final int coins;

        public RestoreAccountsCallbackImpl(MainActivity act, String uid, String email, String name, String avatar,
                int coins) {
            this.act = act;
            this.uid = uid;
            this.email = email;
            this.name = name;
            this.avatar = avatar;
            this.coins = coins;
        }

        @Override
        public void onLoaded(List<AccountItem> list) {
            if (act.accountStorage != null && list != null && !list.isEmpty()) {
                act.accountStorage.replaceAllAccounts(list);
            }
            act.notifyWebProfileUpdated(uid, email, name, avatar, coins);
            act.notifyWebLoginSuccess(uid, email, name, avatar, coins);
            act.runOnUiThread(new ReloadAccountsRunnable(act));
        }

        @Override
        public void onError(String msg) {
            act.notifyWebProfileUpdated(uid, email, name, avatar, coins);
            act.notifyWebLoginSuccess(uid, email, name, avatar, coins);
        }
    }

    public static class RefreshProfileCallbackImpl implements CloudSyncClient.ProfileCallback {
        private final MainActivity act;

        public RefreshProfileCallbackImpl(MainActivity act) {
            this.act = act;
        }

        @Override
        public void onProfile(String uid, String userEmail, String name, String avatar, int coins) {
            if (act.accountStorage != null) {
                act.accountStorage.saveUserSession(uid, userEmail, name, avatar, coins,
                        act.accountStorage.getUserAuthToken());
            }
            act.notifyWebProfileUpdated(uid, userEmail, name, avatar, coins);
        }
    }

    public static class LoginRunnable implements Runnable {
        private final MainActivity act;
        private final String email;
        private final String pass;

        public LoginRunnable(MainActivity act, String email, String pass) {
            this.act = act;
            this.email = email;
            this.pass = pass;
        }

        @Override
        public void run() {
            act.doLogin(email, pass);
        }
    }

    public static class RefreshUserDataRunnable implements Runnable {
        private final MainActivity act;

        public RefreshUserDataRunnable(MainActivity act) {
            this.act = act;
        }

        @Override
        public void run() {
            act.doRefreshUserData();
        }
    }

    public static class ClaimWeeklyPerkRunnable implements Runnable {
        private final MainActivity act;
        private final String code;

        public ClaimWeeklyPerkRunnable(MainActivity a, String c) {
            this.act = a;
            this.code = c;
        }

        @Override
        public void run() {
            act.doClaimWeeklyPerk(code);
        }
    }

    public static class AccountRefreshWorker implements Runnable {
        private final MainActivity act;
        private final String code;
        private String email;
        private String token;
        private String country;

        public AccountRefreshWorker(MainActivity a, String c) {
            this(a, c, null, null, null);
        }

        public AccountRefreshWorker(MainActivity a, String c, String em, String tok, String cntry) {
            this.act = a;
            this.code = c;
            this.email = em;
            this.token = tok;
            this.country = cntry;
        }

        @Override
        public void run() {
            try {
                if (act.accountStorage != null
                        && (token == null || token.isEmpty() || email == null || email.isEmpty())) {
                    for (AccountItem item : act.accountStorage.getAccounts()) {
                        if (code != null && (code.equals(item.getCode()) || code.equals(item.getEmail()))) {
                            if (email == null || email.isEmpty())
                                email = item.getEmail();
                            if (token == null || token.isEmpty())
                                token = item.getToken();
                            if (country == null || country.isEmpty())
                                country = item.getCountry();
                            break;
                        }
                    }
                }

                boolean success = false;
                String bal = "$0.00";
                boolean hasPP = false;
                String tier = "Bronze";
                int pts = 0;
                boolean hasPerk = false;
                String ppStatus = "active";

                // 1. Try Render API
                try {
                    java.net.URL url = new java.net.URL(SecurityGuard.getRenderApi() + "/api/account/live_data");
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setDoOutput(true);
                    conn.setConnectTimeout(12000);
                    conn.setReadTimeout(12000);

                    org.json.JSONObject body = new org.json.JSONObject();
                    body.put("code", code != null ? code : "");
                    if (email != null && !email.isEmpty())
                        body.put("email", email);
                    if (token != null && !token.isEmpty())
                        body.put("token", token);
                    if (country != null && !country.isEmpty())
                        body.put("country", country);

                    java.io.OutputStream os = conn.getOutputStream();
                    os.write(body.toString().getBytes("UTF-8"));
                    os.close();

                    if (conn.getResponseCode() == 200) {
                        java.io.BufferedReader br = new java.io.BufferedReader(
                                new java.io.InputStreamReader(conn.getInputStream(), "UTF-8"));
                        StringBuilder sb = new StringBuilder();
                        String line;
                        while ((line = br.readLine()) != null)
                            sb.append(line);
                        br.close();

                        org.json.JSONObject res = new org.json.JSONObject(sb.toString());
                        if (res.optBoolean("ok", false)) {
                            bal = res.optString("balance", "$0.00");
                            hasPP = res.optBoolean("has_play_points", false);
                            tier = res.optString("tier", "");
                            pts = res.optInt("points", 0);
                            hasPerk = res.optBoolean("has_perk", false);
                            ppStatus = res.optString("play_points_status", "active");
                            success = true;
                        }
                    }
                } catch (Throwable tRender) {
                }

                // 2. Direct fallback to Cloudflare D1 if Render was unreachable or timed out
                if (!success && code != null && !code.isEmpty()) {
                    try {
                        java.net.URL cfUrl = new java.net.URL(SecurityGuard.getCloudWorkerApi() + "/api/sync/get?code=" + code);
                        java.net.HttpURLConnection cfConn = (java.net.HttpURLConnection) cfUrl.openConnection();
                        cfConn.setRequestMethod("GET");
                        cfConn.setConnectTimeout(6000);
                        cfConn.setReadTimeout(6000);
                        if (cfConn.getResponseCode() == 200) {
                            java.io.BufferedReader cfBr = new java.io.BufferedReader(
                                    new java.io.InputStreamReader(cfConn.getInputStream(), "UTF-8"));
                            StringBuilder cfSb = new StringBuilder();
                            String cfLine;
                            while ((cfLine = cfBr.readLine()) != null)
                                cfSb.append(cfLine);
                            cfBr.close();
                            org.json.JSONObject cfRes = new org.json.JSONObject(cfSb.toString());
                            if (cfRes.optBoolean("ok", false) && cfRes.has("account")) {
                                org.json.JSONObject acc = cfRes.getJSONObject("account");
                                bal = acc.optString("balance", "$0.00");
                                hasPP = acc.optBoolean("has_play_points", false);
                                tier = acc.optString("tier", "");
                                pts = acc.optInt("points", 0);
                                hasPerk = acc.optBoolean("has_perk", false);
                                ppStatus = acc.optString("play_points_status", "active");
                                success = true;
                            }
                        }
                    } catch (Throwable tCf) {
                    }
                }

                if (success) {
                    if (pts > 0 || (tier != null && !tier.isEmpty() && !tier.equalsIgnoreCase("None"))) {
                        hasPP = true;
                    }
                    if (hasPP && (tier == null || tier.isEmpty() || tier.equalsIgnoreCase("None"))) {
                        tier = "Bronze";
                    }
                    final String finalBal = bal;
                    final String finalTier = tier;
                    final int finalPts = pts;
                    final boolean finalPP = hasPP;
                    final boolean finalPerk = hasPerk;
                    final String finalStatus = ppStatus;
                    act.runOnUiThread(
                            new AccountRefreshSuccessRunnable(act, code, finalBal, finalTier, finalPts, finalPP, finalPerk, finalStatus));
                    return;
                }
            } catch (Throwable ignored) {
            }
        }
    }

    public static class AccountRefreshSuccessRunnable implements Runnable {
        private final MainActivity act;
        private final String code;
        private final String balance;
        private final String tier;
        private final int points;
        private final boolean hasPlayPoints;
        private final boolean hasPerk;
        private final String status;

        public AccountRefreshSuccessRunnable(MainActivity a, String c, String b, String t, int p, boolean pp,
                boolean perk, String st) {
            this.act = a;
            this.code = c;
            this.balance = b;
            this.tier = t;
            this.points = p;
            this.hasPlayPoints = pp;
            this.hasPerk = perk;
            this.status = st;
        }

        @Override
        public void run() {
            if (act.accountStorage != null) {
                java.util.List<AccountItem> list = act.accountStorage.getAccounts();
                for (AccountItem item : list) {
                    if (code != null && code.equals(item.getCode())) {
                        item.setBalance(balance);
                        item.setTier(tier);
                        item.setPoints(points);
                        item.setHasPlayPoints(hasPlayPoints);
                        item.setHasPerk(hasPerk);
                        item.setPlayPointsStatus(status);
                        break;
                    }
                }
                act.accountStorage.saveAccounts(list);
            }
            if (act.mainAppWebView != null) {
                try {
                    org.json.JSONObject obj = new org.json.JSONObject();
                    obj.put("code", code);
                    obj.put("balance", balance);
                    obj.put("tier", tier);
                    obj.put("points", points);
                    obj.put("has_play_points", hasPlayPoints);
                    obj.put("has_perk", hasPerk);
                    obj.put("play_points_status", status);
                    final String js = "if(window.onAccountRefreshed){ window.onAccountRefreshed('" + code + "', "
                            + obj.toString() + "); } else if(window.refreshAccounts){ window.refreshAccounts(); }";
                    act.mainAppWebView.evaluateJavascript(js, null);
                } catch (Throwable ignored) {
                    act.mainAppWebView.evaluateJavascript("if(window.refreshAccounts){ window.refreshAccounts(); }",
                            null);
                }
            }
            String msg = (hasPlayPoints ? (tier + " • " + points + " PP") : "⚠️ No Play Points Account");
            android.widget.Toast.makeText(act, msg, android.widget.Toast.LENGTH_SHORT).show();
        }
    }

    public static class LogoutRunnable implements Runnable {
        private final MainActivity act;

        public LogoutRunnable(MainActivity a) {
            this.act = a;
        }

        @Override
        public void run() {
            act.doLogout();
        }
    }

    public static class StartGoogleLoginRunnable implements Runnable {
        private final MainActivity act;
        private final String country;

        public StartGoogleLoginRunnable(MainActivity a, String c) {
            this.act = a;
            this.country = c;
        }

        @Override
        public void run() {
            act.startGoogleLogin(country);
        }
    }

    public static class StartGoogleSsoLoginRunnable implements Runnable {
        private final MainActivity act;

        public StartGoogleSsoLoginRunnable(MainActivity a) {
            this.act = a;
        }

        @Override
        public void run() {
            act.startGoogleSsoLogin();
        }
    }

    public static class CloseGoogleLoginRunnable implements Runnable {
        private final MainActivity act;

        public CloseGoogleLoginRunnable(MainActivity a) {
            this.act = a;
        }

        @Override
        public void run() {
            act.closeGoogleLogin();
        }
    }

    public static class DeleteAccountRunnable implements Runnable {
        private final MainActivity act;
        private final String code;

        public DeleteAccountRunnable(MainActivity a, String c) {
            this.act = a;
            this.code = c;
        }

        @Override
        public void run() {
            act.doDeleteAccount(code);
        }
    }

    public static class CopyClipboardRunnable implements Runnable {
        private final MainActivity act;
        private final String text;
        private final String label;

        public CopyClipboardRunnable(MainActivity a, String t, String l) {
            this.act = a;
            this.text = t;
            this.label = l;
        }

        @Override
        public void run() {
            act.copyToClipboard(text, label);
        }
    }

    public static class OpenBrowserRunnable implements Runnable {
        private final MainActivity act;
        private final String url;

        public OpenBrowserRunnable(MainActivity a, String u) {
            this.act = a;
            this.url = u;
        }

        @Override
        public void run() {
            act.openBrowserUrl(url);
        }
    }

    public static class OpenPlayPointsRunnable implements Runnable {
        private final MainActivity act;

        public OpenPlayPointsRunnable(MainActivity a) {
            this.act = a;
        }

        @Override
        public void run() {
            act.openPlayPoints();
        }
    }

    public static class SyncCloudRunnable implements Runnable {
        private final MainActivity act;

        public SyncCloudRunnable(MainActivity a) {
            this.act = a;
        }

        @Override
        public void run() {
            act.restoreAccountsFromCloud();
        }
    }

    public static class GpgsResultRunnable implements Runnable {
        private final WebView webView;
        private final boolean success;
        private final String msg;

        public GpgsResultRunnable(WebView wv, boolean s, String m) {
            this.webView = wv;
            this.success = s;
            this.msg = m;
        }

        @Override
        public void run() {
            if (webView != null) {
                webView.evaluateJavascript(
                        "if(window.onGpgsTestResult){ window.onGpgsTestResult(" + success + ", '" + msg + "'); }",
                        null);
            }
        }
    }

    public static class RefreshWebRunnable implements Runnable {
        private final WebView web;

        public RefreshWebRunnable(WebView w) {
            this.web = w;
        }

        @Override
        public void run() {
            if (web != null)
                web.evaluateJavascript("if(window.refreshAccounts){ window.refreshAccounts(); }", null);
        }
    }

    public static class PerkClaimSuccessRunnable implements Runnable {
        private final WebView web;
        private final String code;
        private final int bonus;

        public PerkClaimSuccessRunnable(WebView w, String c, int b) {
            this.web = w;
            this.code = c;
            this.bonus = b;
        }

        @Override
        public void run() {
            if (web != null) {
                web.evaluateJavascript("if(window.onPerkClaimSuccess){ window.onPerkClaimSuccess('" + code + "', "
                        + bonus + "); } else if(window.refreshAccounts){ window.refreshAccounts(); }", null);
            }
        }
    }

    public static class ReloadWebRunnable implements Runnable {
        private final WebView web;

        public ReloadWebRunnable(WebView w) {
            this.web = w;
        }

        @Override
        public void run() {
            if (web != null)
                web.loadUrl("file:///android_asset/www/index.html");
        }
    }

    public static class SafeCrashHandler implements Thread.UncaughtExceptionHandler {
        private final Thread.UncaughtExceptionHandler defaultHandler;

        public SafeCrashHandler(Thread.UncaughtExceptionHandler dh) {
            this.defaultHandler = dh;
        }

        @Override
        public void uncaughtException(Thread t, Throwable e) {
            Log.e("CrashShield", "Shielded uncaught exception on thread " + t.getName(), e);
        }
    }

    public static class SafeMainWebClient extends android.webkit.WebViewClient {
        private final MainActivity activity;

        public SafeMainWebClient(MainActivity act) {
            this.activity = act;
        }

        @Override
        public void onReceivedSslError(WebView view, android.webkit.SslErrorHandler handler,
                android.net.http.SslError error) {
            // Gracefully proceed on emulators with outdated root CA certificates or
            // out-of-sync clocks
            if (handler != null) {
                handler.proceed();
            }
        }

        @Override
        public boolean onRenderProcessGone(WebView view, android.webkit.RenderProcessGoneDetail detail) {
            Log.w("SafeMainWebClient", "Renderer process gone, reloading index...");
            if (view != null) {
                view.loadUrl("file:///android_asset/www/index.html");
            }
            return true;
        }
    }

    public static class LaunchAccountChooserRunnable implements Runnable {
        private final MainActivity activity;

        public LaunchAccountChooserRunnable(MainActivity act) {
            this.activity = act;
        }

        @Override
        public void run() {
            if (activity == null)
                return;
            try {
                Intent intent;
                if (Build.VERSION.SDK_INT >= 23) {
                    intent = AccountManager.newChooseAccountIntent(null, null, new String[] { "com.google" }, null,
                            null, null, null);
                } else {
                    intent = AccountManager.newChooseAccountIntent(null, null, new String[] { "com.google" }, false,
                            null, null, null, null);
                }
                activity.startActivityForResult(intent, REQUEST_CODE_PICK_ACCOUNT);
            } catch (Throwable t) {
                Log.e(TAG, "System account chooser error, falling back", t);
                List<String> emails = activity.getDeviceGoogleEmails();
                if (!emails.isEmpty()) {
                    activity.handleGoogleAccountSelectedForSso(emails.get(0));
                } else {
                    activity.fallbackGoogleLoginForEmulator();
                }
            }
        }
    }

    public static class SsoAccountSelectedRunnable implements Runnable {
        private final WebView web;
        private final String email;

        public SsoAccountSelectedRunnable(WebView w, String em) {
            this.web = w;
            this.email = em;
        }

        @Override
        public void run() {
            if (web != null && email != null) {
                String js = "javascript:(function(){ if(window.selectGoogleAccount) window.selectGoogleAccount('"
                        + email + "'); })();";
                web.loadUrl(js);
            }
        }
    }

    public static class SsoCancelRunnable implements Runnable {
        private final WebView web;

        public SsoCancelRunnable(WebView w) {
            this.web = w;
        }

        @Override
        public void run() {
            if (web != null) {
                String js = "javascript:(function(){ if(window.setLoginBtnLoading) window.setLoginBtnLoading(false); })();";
                web.loadUrl(js);
            }
        }
    }

    public static class FallbackEmulatorPromptRunnable implements Runnable {
        private final WebView web;

        public FallbackEmulatorPromptRunnable(WebView w) {
            this.web = w;
        }

        @Override
        public void run() {
            if (web != null) {
                String js = "javascript:(function(){ if(window.showEmulatorAccountPrompt) window.showEmulatorAccountPrompt(); else if(window.setLoginBtnLoading) window.setLoginBtnLoading(false); })();";
                web.loadUrl(js);
            }
        }
    }
}
