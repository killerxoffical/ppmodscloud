package com.vareon.gateway;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Random;

public class MainActivity extends Activity implements View.OnClickListener {
    private static final int PERMISSION_REQ_CODE = 101;

    private TextView txtStatusHeader;
    private TextView txtHeroTitle;
    private Button btnToggleService;
    private TextView txtStatForwarded;
    private TextView txtStatApproved;
    private TextView txtStatAmount;
    private ImageButton btnRefresh;
    private Button btnTestSms;
    private Button btnScanInbox;
    private EditText editServerUrl;
    private EditText editSecretKey;
    private Button btnSaveConfig;
    private LinearLayout layoutEmptyState;
    private LinearLayout smsFeedContainer;

    private GatewayStorage storage;
    private BroadcastReceiver smsProcessedReceiver;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        storage = new GatewayStorage(this);

        // Bind views
        txtStatusHeader = (TextView) findViewById(R.id.txtStatusHeader);
        txtHeroTitle = (TextView) findViewById(R.id.txtHeroTitle);
        btnToggleService = (Button) findViewById(R.id.btnToggleService);
        txtStatForwarded = (TextView) findViewById(R.id.txtStatForwarded);
        txtStatApproved = (TextView) findViewById(R.id.txtStatApproved);
        txtStatAmount = (TextView) findViewById(R.id.txtStatAmount);
        btnRefresh = (ImageButton) findViewById(R.id.btnRefresh);
        btnTestSms = (Button) findViewById(R.id.btnTestSms);
        btnScanInbox = (Button) findViewById(R.id.btnScanInbox);
        editServerUrl = (EditText) findViewById(R.id.editServerUrl);
        editSecretKey = (EditText) findViewById(R.id.editSecretKey);
        btnSaveConfig = (Button) findViewById(R.id.btnSaveConfig);
        layoutEmptyState = (LinearLayout) findViewById(R.id.layoutEmptyState);
        smsFeedContainer = (LinearLayout) findViewById(R.id.smsFeedContainer);

        // Click listeners
        btnToggleService.setOnClickListener(this);
        btnRefresh.setOnClickListener(this);
        btnTestSms.setOnClickListener(this);
        btnScanInbox.setOnClickListener(this);
        btnSaveConfig.setOnClickListener(this);

        // Load configs
        editServerUrl.setText(storage.getServerUrl());
        editSecretKey.setText(storage.getSecretKey());

        // Check Permissions
        checkPermissions();

        // Start Gateway Service if enabled
        if (storage.isEnabled()) {
            startGatewayService();
        }

        updateUi();

        // Register local broadcast receiver for live feed updates
        smsProcessedReceiver = new LocalSmsReceiver(this);
        IntentFilter filter = new IntentFilter(SmsReceiver.ACTION_SMS_PROCESSED);
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(smsProcessedReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(smsProcessedReceiver, filter);
        }
    }

    private void checkPermissions() {
        if (Build.VERSION.SDK_INT >= 23) {
            String[] perms;
            if (Build.VERSION.SDK_INT >= 33) {
                perms = new String[] {
                    Manifest.permission.RECEIVE_SMS,
                    Manifest.permission.READ_SMS,
                    Manifest.permission.POST_NOTIFICATIONS
                };
            } else {
                perms = new String[] {
                    Manifest.permission.RECEIVE_SMS,
                    Manifest.permission.READ_SMS
                };
            }

            boolean needsRequest = false;
            for (String p : perms) {
                if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) {
                    needsRequest = true;
                    break;
                }
            }

            if (needsRequest) {
                requestPermissions(perms, PERMISSION_REQ_CODE);
            }
        }
    }

    public void updateUi() {
        boolean running = storage.isEnabled();
        if (running) {
            txtHeroTitle.setText("GATEWAY ACTIVE");
            txtHeroTitle.setTextColor(0xFF10B981);
            txtStatusHeader.setText("Live SMS Payment Bridge");
            txtStatusHeader.setTextColor(0xFF10B981);
            btnToggleService.setText("Running");
            btnToggleService.setBackgroundResource(R.drawable.badge_pill_green);
        } else {
            txtHeroTitle.setText("GATEWAY PAUSED");
            txtHeroTitle.setTextColor(0xFFEF4444);
            txtStatusHeader.setText("Service Stopped");
            txtStatusHeader.setTextColor(0xFFEF4444);
            btnToggleService.setText("Paused");
            btnToggleService.setBackgroundResource(R.drawable.badge_pill_red);
        }

        txtStatForwarded.setText(String.valueOf(storage.getStatForwarded()));
        txtStatApproved.setText(String.valueOf(storage.getStatApproved()));
        txtStatAmount.setText("৳ " + Math.round(storage.getStatAmount()));

        renderSmsFeed();
    }

    private void renderSmsFeed() {
        if (smsFeedContainer == null) return;
        smsFeedContainer.removeAllViews();

        List<SmsRecord> records = storage.getRecords();
        if (records.isEmpty()) {
            layoutEmptyState.setVisibility(View.VISIBLE);
            return;
        }

        layoutEmptyState.setVisibility(View.GONE);
        LayoutInflater inflater = LayoutInflater.from(this);
        SimpleDateFormat sdf = new SimpleDateFormat("dd/MM HH:mm", Locale.getDefault());

        for (int i = 0; i < records.size(); i++) {
            SmsRecord rec = records.get(i);
            View card = inflater.inflate(R.layout.item_sms_card, smsFeedContainer, false);

            TextView txtMethod = (TextView) card.findViewById(R.id.txtItemMethod);
            TextView txtTrxId = (TextView) card.findViewById(R.id.txtItemTrxId);
            TextView txtStatus = (TextView) card.findViewById(R.id.txtItemStatus);
            TextView txtAmount = (TextView) card.findViewById(R.id.txtItemAmount);
            TextView txtBalance = (TextView) card.findViewById(R.id.txtItemBalance);
            TextView txtTime = (TextView) card.findViewById(R.id.txtItemTime);

            txtMethod.setText(rec.getMethod());
            if ("Nagad".equalsIgnoreCase(rec.getMethod())) {
                txtMethod.setBackgroundResource(R.drawable.badge_pill_nagad);
            } else if ("Rocket".equalsIgnoreCase(rec.getMethod())) {
                txtMethod.setBackgroundResource(R.drawable.badge_pill_rocket);
            } else {
                txtMethod.setBackgroundResource(R.drawable.badge_pill_bkash);
            }

            txtTrxId.setText(rec.getTrxId());
            txtAmount.setText("৳ " + Math.round(rec.getAmount()));
            txtBalance.setText(rec.getBalance() > 0 ? "Bal: ৳" + Math.round(rec.getBalance()) : "");
            txtTime.setText(sdf.format(new Date(rec.getTimestamp())));

            String st = rec.getStatus();
            txtStatus.setText(st);
            if ("AUTO_APPROVED".equalsIgnoreCase(st)) {
                txtStatus.setBackgroundResource(R.drawable.badge_pill_green);
            } else if ("DUPLICATE".equalsIgnoreCase(st) || "FAILED".equalsIgnoreCase(st)) {
                txtStatus.setBackgroundResource(R.drawable.badge_pill_red);
            } else {
                txtStatus.setBackgroundResource(R.drawable.badge_pill_cyan);
            }

            smsFeedContainer.addView(card);
        }
    }

    @Override
    public void onClick(View v) {
        int id = v.getId();
        if (id == R.id.btnToggleService) {
            boolean newState = !storage.isEnabled();
            storage.setEnabled(newState);
            if (newState) {
                startGatewayService();
                Toast.makeText(this, "Gateway Service Started", Toast.LENGTH_SHORT).show();
            } else {
                stopGatewayService();
                Toast.makeText(this, "Gateway Service Paused", Toast.LENGTH_SHORT).show();
            }
            updateUi();
        } else if (id == R.id.btnRefresh) {
            updateUi();
            Toast.makeText(this, "Feed refreshed", Toast.LENGTH_SHORT).show();
        } else if (id == R.id.btnSaveConfig) {
            String url = editServerUrl.getText().toString().trim();
            String sec = editSecretKey.getText().toString().trim();
            if (!url.isEmpty()) storage.setServerUrl(url);
            if (!sec.isEmpty()) storage.setSecretKey(sec);
            Toast.makeText(this, "Configuration saved", Toast.LENGTH_SHORT).show();
        } else if (id == R.id.btnTestSms) {
            sendTestBkasSms();
        } else if (id == R.id.btnScanInbox) {
            scanInboxForSms();
        }
    }

    private void sendTestBkasSms() {
        String randomTrx = "BK" + (100000 + new Random().nextInt(900000));
        String testMsg = "You have received Tk 500.00 from 01712345678. Fee Tk 0.00. Balance Tk 2,500.00. TrxID " + randomTrx + " at 17/11/2026 16:15";
        SmsRecord rec = SmsParser.parse("bKash", testMsg, System.currentTimeMillis());

        if (rec != null) {
            storage.addRecord(rec);
            updateUi();
            Toast.makeText(this, "Simulating bKash payment: " + randomTrx, Toast.LENGTH_SHORT).show();

            GatewayHttp.forwardSms(storage, rec, new TestForwardCallback(this));
        }
    }

    private void scanInboxForSms() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.READ_SMS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[] { Manifest.permission.READ_SMS }, PERMISSION_REQ_CODE);
            return;
        }

        try {
            Uri inboxUri = Uri.parse("content://sms/inbox");
            Cursor cursor = getContentResolver().query(inboxUri, new String[] { "address", "body", "date" }, null, null, "date DESC LIMIT 30");
            int scanned = 0;
            if (cursor != null) {
                while (cursor.moveToNext()) {
                    String address = cursor.getString(0);
                    String body = cursor.getString(1);
                    long date = cursor.getLong(2);

                    SmsRecord rec = SmsParser.parse(address, body, date);
                    if (rec != null) {
                        storage.addRecord(rec);
                        scanned++;
                    }
                }
                cursor.close();
            }
            updateUi();
            Toast.makeText(this, "Scanned recent inbox. Found " + scanned + " payment SMS.", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Inbox read error: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void startGatewayService() {
        Intent serviceIntent = new Intent(this, GatewayService.class);
        if (Build.VERSION.SDK_INT >= 26) {
            startForegroundService(serviceIntent);
        } else {
            startService(serviceIntent);
        }
    }

    private void stopGatewayService() {
        Intent serviceIntent = new Intent(this, GatewayService.class);
        stopService(serviceIntent);
    }

    @Override
    protected void onDestroy() {
        if (smsProcessedReceiver != null) {
            try {
                unregisterReceiver(smsProcessedReceiver);
            } catch (Exception ignored) {}
        }
        super.onDestroy();
    }

    // Static helper classes
    private static class LocalSmsReceiver extends BroadcastReceiver {
        private final MainActivity activity;
        LocalSmsReceiver(MainActivity activity) { this.activity = activity; }
        @Override
        public void onReceive(Context context, Intent intent) {
            activity.runOnUiThread(new UiUpdateTask(activity));
        }
    }

    private static class UiUpdateTask implements Runnable {
        private final MainActivity activity;
        UiUpdateTask(MainActivity activity) { this.activity = activity; }
        @Override public void run() { activity.updateUi(); }
    }

    private static class TestForwardCallback implements GatewayHttp.GatewayCallback {
        private final MainActivity activity;
        TestForwardCallback(MainActivity activity) { this.activity = activity; }
        @Override
        public void onComplete(String trxId, String status, String message) {
            activity.runOnUiThread(new ToastAndRefreshTask(activity, status, message));
        }
    }

    private static class ToastAndRefreshTask implements Runnable {
        private final MainActivity activity;
        private final String status;
        private final String message;
        ToastAndRefreshTask(MainActivity activity, String status, String message) {
            this.activity = activity;
            this.status = status;
            this.message = message;
        }
        @Override
        public void run() {
            activity.updateUi();
            Toast.makeText(activity, "Server Result: " + status + " (" + message + ")", Toast.LENGTH_LONG).show();
        }
    }
}
