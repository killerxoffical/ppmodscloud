package com.vareon.gateway;

import org.json.JSONException;
import org.json.JSONObject;

public class SmsRecord {
    private String id;
    private String sender;
    private String method;
    private String trxId;
    private double amount;
    private double balance;
    private String senderPhone;
    private String rawMessage;
    private long timestamp;
    private String status; // "SENT", "AUTO_APPROVED", "SAVED", "DUPLICATE", "FAILED"

    public SmsRecord(String id, String sender, String method, String trxId, double amount, double balance, String senderPhone, String rawMessage, long timestamp, String status) {
        this.id = id;
        this.sender = sender;
        this.method = method;
        this.trxId = trxId;
        this.amount = amount;
        this.balance = balance;
        this.senderPhone = senderPhone;
        this.rawMessage = rawMessage;
        this.timestamp = timestamp;
        this.status = status;
    }

    public String getId() { return id; }
    public String getSender() { return sender; }
    public String getMethod() { return method; }
    public String getTrxId() { return trxId; }
    public double getAmount() { return amount; }
    public double getBalance() { return balance; }
    public String getSenderPhone() { return senderPhone; }
    public String getRawMessage() { return rawMessage; }
    public long getTimestamp() { return timestamp; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public JSONObject toJson() {
        JSONObject obj = new JSONObject();
        try {
            obj.put("id", id);
            obj.put("sender", sender);
            obj.put("method", method);
            obj.put("trxId", trxId);
            obj.put("amount", amount);
            obj.put("balance", balance);
            obj.put("senderPhone", senderPhone);
            obj.put("rawMessage", rawMessage);
            obj.put("timestamp", timestamp);
            obj.put("status", status);
        } catch (JSONException ignored) {}
        return obj;
    }

    public static SmsRecord fromJson(JSONObject obj) {
        if (obj == null) return null;
        return new SmsRecord(
            obj.optString("id", String.valueOf(System.currentTimeMillis())),
            obj.optString("sender", "Unknown"),
            obj.optString("method", "bKash"),
            obj.optString("trxId", ""),
            obj.optDouble("amount", 0.0),
            obj.optDouble("balance", 0.0),
            obj.optString("senderPhone", ""),
            obj.optString("rawMessage", ""),
            obj.optLong("timestamp", System.currentTimeMillis()),
            obj.optString("status", "SAVED")
        );
    }
}
