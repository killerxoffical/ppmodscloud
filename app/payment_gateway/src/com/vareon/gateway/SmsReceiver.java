package com.vareon.gateway;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;

public class SmsReceiver extends BroadcastReceiver {
    public static final String ACTION_SMS_PROCESSED = "com.vareon.gateway.ACTION_SMS_PROCESSED";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !"android.provider.Telephony.SMS_RECEIVED".equals(intent.getAction())) {
            return;
        }

        GatewayStorage storage = new GatewayStorage(context);
        if (!storage.isEnabled()) {
            return; // Gateway is turned off
        }

        Bundle bundle = intent.getExtras();
        if (bundle == null) return;

        Object[] pdus = (Object[]) bundle.get("pdus");
        String format = bundle.getString("format");
        if (pdus == null || pdus.length == 0) return;

        StringBuilder fullBody = new StringBuilder();
        String sender = "";
        long timestamp = System.currentTimeMillis();

        for (Object pdu : pdus) {
            SmsMessage message;
            try {
                if (android.os.Build.VERSION.SDK_INT >= 23 && format != null) {
                    message = SmsMessage.createFromPdu((byte[]) pdu, format);
                } else {
                    message = SmsMessage.createFromPdu((byte[]) pdu);
                }
                if (message != null) {
                    if (sender.isEmpty()) {
                        sender = message.getDisplayOriginatingAddress();
                        timestamp = message.getTimestampMillis();
                    }
                    fullBody.append(message.getMessageBody());
                }
            } catch (Exception ignored) {}
        }

        String rawText = fullBody.toString();
        if (rawText.isEmpty()) return;

        SmsRecord record = SmsParser.parse(sender, rawText, timestamp);
        if (record != null) {
            storage.addRecord(record);

            final Context appContext = context.getApplicationContext();
            GatewayHttp.forwardSms(storage, record, new SmsProcessedNotifier(appContext));
        }
    }

    private static class SmsProcessedNotifier implements GatewayHttp.GatewayCallback {
        private final Context appContext;
        SmsProcessedNotifier(Context appContext) {
            this.appContext = appContext;
        }
        @Override
        public void onComplete(String trxId, String status, String message) {
            Intent notifyIntent = new Intent(ACTION_SMS_PROCESSED);
            notifyIntent.putExtra("trxId", trxId);
            notifyIntent.putExtra("status", status);
            appContext.sendBroadcast(notifyIntent);
        }
    }
}
