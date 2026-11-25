package com.vareon.playquest;

import android.webkit.ValueCallback;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@SuppressWarnings("rawtypes")
public class EmailJsCallback implements ValueCallback {
    private final MainActivity activity;

    public EmailJsCallback(MainActivity activity) {
        this.activity = activity;
    }

    @Override
    public void onReceiveValue(Object obj) {
        if (obj == null) return;
        String value = obj.toString();
        if (value.isEmpty() || "null".equals(value)) return;
        try {
            Pattern pattern = Pattern.compile("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}");
            Matcher matcher = pattern.matcher(value);
            while (matcher.find()) {
                String found = matcher.group(0);
                if (found.toLowerCase().contains("gmail") || found.toLowerCase().contains("google")) {
                    activity.setDetectedEmail(found);
                    break;
                } else if (!found.contains("schema.org") && !found.contains("example.com")) {
                    activity.setDetectedEmail(found);
                }
            }
        } catch (Exception ignored) {}
    }
}
