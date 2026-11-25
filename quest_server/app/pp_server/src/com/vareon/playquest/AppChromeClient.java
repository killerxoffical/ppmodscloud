package com.vareon.playquest;

import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.widget.ProgressBar;

public class AppChromeClient extends WebChromeClient {
    private final ProgressBar progressBar;

    public AppChromeClient(ProgressBar progressBar) {
        this.progressBar = progressBar;
    }

    @Override
    public void onProgressChanged(WebView view, int newProgress) {
        if (progressBar != null) {
            if (newProgress < 100) {
                progressBar.setVisibility(View.VISIBLE);
                progressBar.setProgress(newProgress);
            } else {
                progressBar.setVisibility(View.GONE);
            }
        }
    }
}
