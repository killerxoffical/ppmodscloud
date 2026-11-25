package com.vareon.gateway;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class GatewayHttp {

    public interface GatewayCallback {
        void onComplete(String trxId, String status, String message);
    }

    public static void forwardSms(GatewayStorage storage, SmsRecord record, GatewayCallback callback) {
        new Thread(new ForwardTask(storage, record, callback)).start();
    }

    private static class ForwardTask implements Runnable {
        private final GatewayStorage storage;
        private final SmsRecord record;
        private final GatewayCallback callback;

        ForwardTask(GatewayStorage storage, SmsRecord record, GatewayCallback callback) {
            this.storage = storage;
            this.record = record;
            this.callback = callback;
        }

        @Override
        public void run() {
            String resultingStatus = "SAVED";
            String serverMsg = "Saved to Cloud";
            boolean isAutoApproved = false;

            String primaryUrl = storage.getServerUrl() + "/api/gateway/sms";
            String cfUrl = storage.getCloudflareUrl() + "/api/gateway/sms";

            JSONObject payload = new JSONObject();
            try {
                payload.put("secret", storage.getSecretKey());
                payload.put("sender", record.getSender());
                payload.put("message", record.getRawMessage());
                payload.put("trxId", record.getTrxId());
                payload.put("amount", record.getAmount());
                payload.put("balance", record.getBalance());
                payload.put("method", record.getMethod());
                payload.put("timestamp", record.getTimestamp());
            } catch (Exception ignored) {}

            // Send to Cloudflare D1 first (0ms cold start)
            try {
                JSONObject cfResp = postJson(cfUrl, payload, storage.getSecretKey());
                if (cfResp != null) {
                    if (cfResp.optBoolean("autoApproved", false)) {
                        resultingStatus = "AUTO_APPROVED";
                        isAutoApproved = true;
                        serverMsg = "Auto Approved on Cloudflare D1!";
                    } else if (cfResp.optBoolean("duplicate", false)) {
                        resultingStatus = "DUPLICATE";
                        serverMsg = "Duplicate TrxID Blocked";
                    }
                }
            } catch (Exception ignored) {}

            // Send to Render Server
            try {
                JSONObject renderResp = postJson(primaryUrl, payload, storage.getSecretKey());
                if (renderResp != null) {
                    if (renderResp.optBoolean("autoApproved", false)) {
                        resultingStatus = "AUTO_APPROVED";
                        isAutoApproved = true;
                        serverMsg = "Auto Approved on Render!";
                    } else if (renderResp.optBoolean("duplicate", false) || renderResp.optString("error", "").contains("ইতিমধ্যে")) {
                        resultingStatus = "DUPLICATE";
                        serverMsg = "Duplicate TrxID Blocked";
                    }
                }
            } catch (Exception ignored) {}

            // Update local storage & stats
            storage.updateRecordStatus(record.getTrxId(), resultingStatus);
            storage.recordStats(isAutoApproved, record.getAmount());

            if (callback != null) {
                callback.onComplete(record.getTrxId(), resultingStatus, serverMsg);
            }
        }
    }

    private static JSONObject postJson(String targetUrl, JSONObject body, String secret) {
        HttpURLConnection conn = null;
        try {
            URL u = new URL(targetUrl);
            conn = (HttpURLConnection) u.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setRequestProperty("x-gateway-secret", secret);
            conn.setDoOutput(true);
            conn.setConnectTimeout(7000);
            conn.setReadTimeout(7000);

            OutputStream os = conn.getOutputStream();
            os.write(body.toString().getBytes("UTF-8"));
            os.close();

            int code = conn.getResponseCode();
            BufferedReader br;
            if (code >= 200 && code < 300) {
                br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"));
            } else if (conn.getErrorStream() != null) {
                br = new BufferedReader(new InputStreamReader(conn.getErrorStream(), "UTF-8"));
            } else {
                return null;
            }

            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line);
            }
            br.close();

            return new JSONObject(sb.toString());
        } catch (Exception e) {
            return null;
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
}
