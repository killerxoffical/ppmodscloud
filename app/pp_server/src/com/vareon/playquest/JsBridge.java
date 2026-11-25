package com.vareon.playquest;

import android.webkit.JavascriptInterface;

public class JsBridge {
    private final MainActivity activity;

    public JsBridge(MainActivity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public void closeView() {
        activity.checkCookiesForToken();
    }

    @JavascriptInterface
    public void showView() {
        // Called when Google view is ready
    }

    @JavascriptInterface
    public void addAccount(String json) {
        activity.checkCookiesForToken();
    }
}
