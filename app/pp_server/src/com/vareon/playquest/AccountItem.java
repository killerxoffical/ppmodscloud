package com.vareon.playquest;

import org.json.JSONException;
import org.json.JSONObject;

public class AccountItem {
    private String id;
    private String email;
    private String code;
    private String token;
    private String country;
    private long timestamp;

    // Real Account State & Balance
    private String balance = "$0.00";
    private int points = 0;
    private String tier = "None";
    private boolean hasPerk = false;
    private String lastClaimDate = "";
    private int claimedPoints = 0;
    private boolean isRevoked = false;
    private boolean hasPlayPoints = false;
    private String playPointsStatus = "not_enrolled"; // "active", "not_enrolled", "unsupported_region"

    // Strict Account Ownership Isolation
    private String ownerUid = "";
    private String ownerEmail = "";

    public AccountItem(String id, String email, String code, String token, String country, long timestamp) {
        this.id = id;
        this.email = email;
        this.code = code;
        this.token = token;
        this.country = (country != null && !country.isEmpty() && !country.equalsIgnoreCase("GLOBAL")) ? country : "US";
        this.timestamp = timestamp;
    }

    public AccountItem(String id, String email, String code, String token, String country, String ownerUid, String ownerEmail, long timestamp) {
        this(id, email, code, token, country, timestamp);
        this.ownerUid = (ownerUid != null) ? ownerUid : "";
        this.ownerEmail = (ownerEmail != null) ? ownerEmail : "";
    }

    public AccountItem(String id, String email, String code, String token, long timestamp) {
        this(id, email, code, token, "US", timestamp);
    }

    public String getId() {
        return id;
    }

    public String getEmail() {
        return email != null && !email.isEmpty() ? email : "Google Account";
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public String getMasterToken() {
        return token;
    }

    public String getCountry() {
        return (country != null && !country.isEmpty() && !country.equalsIgnoreCase("GLOBAL")) ? country : "US";
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public String getBalance() {
        if (balance == null || balance.isEmpty()) return "$0.00";
        String b = balance.trim();
        if (b.startsWith(".")) {
            return "$0" + b;
        } else if (Character.isDigit(b.charAt(0))) {
            return "$" + b;
        }
        return b;
    }

    public void setBalance(String balance) {
        this.balance = balance;
    }

    
    public String getTier() {
        if (tier != null && !tier.isEmpty() && !"None".equalsIgnoreCase(tier)) {
            return tier;
        }
        if (hasPlayPoints || points > 0) {
            return "Bronze";
        }
        return "None";
    }

    public void setTier(String tier) {
        if (tier != null && !tier.isEmpty() && !"None".equalsIgnoreCase(tier)) {
            this.tier = tier;
        } else if (hasPlayPoints || points > 0) {
            this.tier = "Bronze";
        } else {
            this.tier = "None";
        }
    }

    public int getPoints() {
        return points;
    }

    public void setPoints(int points) {
        this.points = points;
    }

    public boolean hasPerk() {
        return hasPerk;
    }

    public void setHasPerk(boolean hasPerk) {
        this.hasPerk = hasPerk;
    }

    public String getLastClaimDate() {
        return lastClaimDate != null ? lastClaimDate : "";
    }

    public void setLastClaimDate(String lastClaimDate) {
        this.lastClaimDate = lastClaimDate;
    }

    public int getClaimedPoints() {
        return claimedPoints;
    }

    public void setClaimedPoints(int claimedPoints) {
        this.claimedPoints = claimedPoints;
    }

    public boolean isRevoked() {
        return isRevoked;
    }

    public void setRevoked(boolean revoked) {
        isRevoked = revoked;
    }

    public String getOwnerUid() {
        return ownerUid != null ? ownerUid : "";
    }

    public void setOwnerUid(String ownerUid) {
        this.ownerUid = ownerUid;
    }

    public String getOwnerEmail() {
        return ownerEmail != null ? ownerEmail : "";
    }

    public void setOwnerEmail(String ownerEmail) {
        this.ownerEmail = ownerEmail;
    }

    public boolean hasPlayPoints() {
        if (hasPlayPoints || points > 0) return true;
        if (tier != null && !tier.isEmpty() && !"None".equalsIgnoreCase(tier)) return true;
        return false;
    }

    public void setHasPlayPoints(boolean hasPlayPoints) {
        this.hasPlayPoints = hasPlayPoints;
    }

    public String getPlayPointsStatus() {
        return playPointsStatus != null ? playPointsStatus : "active";
    }

    public void setPlayPointsStatus(String playPointsStatus) {
        this.playPointsStatus = playPointsStatus;
    }

    public JSONObject toStorageJson() {
        JSONObject obj = new JSONObject();
        try {
            obj.put("id", id);
            obj.put("email", email);
            obj.put("code", code);
            obj.put("token", token);
            obj.put("country", getCountry());
            obj.put("timestamp", timestamp);
            obj.put("owner_uid", ownerUid);
            obj.put("owner_email", ownerEmail);
        } catch (JSONException ignored) {
        }
        return obj;
    }

    public JSONObject toJson() {
        JSONObject obj = new JSONObject();
        try {
            obj.put("id", id);
            obj.put("email", email);
            obj.put("code", code);
            obj.put("token", token);
            obj.put("country", getCountry());
            obj.put("timestamp", timestamp);
            obj.put("balance", balance);
            obj.put("points", points);
            obj.put("tier", getTier());
            obj.put("has_perk", hasPerk);
            obj.put("claimed", !hasPerk);
            obj.put("last_claim_date", lastClaimDate);
            obj.put("claimed_points", claimedPoints);
            obj.put("is_revoked", isRevoked);
            obj.put("has_play_points", hasPlayPoints);
            obj.put("play_points_status", getPlayPointsStatus());
            obj.put("owner_uid", ownerUid);
            obj.put("owner_email", ownerEmail);
        } catch (JSONException ignored) {
        }
        return obj;
    }

    public static AccountItem fromJson(JSONObject obj) {
        if (obj == null)
            return null;
        String id = obj.optString("id", "");
        String email = obj.optString("email", "");
        String code = obj.optString("code", "");
        String token = obj.optString("token", "");
        String country = obj.optString("country", "US");
        if (country == null || country.isEmpty() || country.equalsIgnoreCase("GLOBAL")) country = "US";
        long timestamp = obj.optLong("timestamp", System.currentTimeMillis());
        
        AccountItem item = new AccountItem(id, email, code, token, country, timestamp);
        item.setBalance(obj.optString("balance", "$0.00"));
        item.setPoints(obj.optInt("points", 0));
        
        boolean hasPP = obj.optBoolean("has_play_points", false);
        if (!hasPP && (obj.optInt("has_play_points", 0) == 1 || "true".equalsIgnoreCase(obj.optString("has_play_points", "")))) {
            hasPP = true;
        }
        int pts = obj.optInt("points", 0);
        String tierVal = obj.optString("tier", "");
        if (pts > 0 || (!tierVal.isEmpty() && !"None".equalsIgnoreCase(tierVal))) {
            hasPP = true;
        }
        if (hasPP && (tierVal.isEmpty() || "None".equalsIgnoreCase(tierVal))) {
            tierVal = "Bronze";
        } else if (!hasPP && tierVal.isEmpty()) {
            tierVal = "None";
        }
        item.setTier(tierVal);
        item.setHasPlayPoints(hasPP);
        item.setPlayPointsStatus(obj.optString("play_points_status", hasPP ? "active" : "not_enrolled"));

        boolean perkFlag = obj.optBoolean("has_perk", false);
        if (obj.has("claimed") && obj.optBoolean("claimed", false)) {
            perkFlag = false;
        }
        if (!hasPP || "None".equalsIgnoreCase(tierVal) || "Bronze".equalsIgnoreCase(tierVal)) {
            perkFlag = false;
        }
        item.setHasPerk(perkFlag);
        item.setLastClaimDate(obj.optString("last_claim_date", ""));
        item.setClaimedPoints(obj.optInt("claimed_points", 0));
        item.setRevoked(obj.optBoolean("is_revoked", false));
        item.setOwnerUid(obj.optString("owner_uid", obj.optString("uid", "")));
        item.setOwnerEmail(obj.optString("owner_email", ""));
        return item;
    }
}
