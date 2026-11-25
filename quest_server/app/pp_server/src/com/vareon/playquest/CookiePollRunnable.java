package com.vareon.playquest;

public class CookiePollRunnable implements Runnable {
    private final MainActivity activity;

    public CookiePollRunnable(MainActivity activity) {
        this.activity = activity;
    }

    @Override
    public void run() {
        if (!activity.isTokenFound()) {
            activity.checkCookiesForToken();
            if (!activity.isTokenFound() && activity.getPollHandler() != null) {
                activity.getPollHandler().postDelayed(this, 1000);
            }
        }
    }
}
