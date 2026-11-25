package com.vareon.playquest;

import android.webkit.JavascriptInterface;

public class GServicesBridge {
    private final MainActivity activity;

    public GServicesBridge(MainActivity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public void closeOob() {
        activity.checkCookiesForToken();
    }
}
