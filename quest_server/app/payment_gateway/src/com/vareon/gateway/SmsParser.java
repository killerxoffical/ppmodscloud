package com.vareon.gateway;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SmsParser {

    public static SmsRecord parse(String sender, String rawMessage, long timestamp) {
        if (rawMessage == null || rawMessage.trim().isEmpty()) {
            return null;
        }

        String text = rawMessage.replace("\n", " ");
        String lowerSender = sender != null ? sender.toLowerCase() : "";
        String lowerText = text.toLowerCase();

        // 1. Determine Payment Method with multi-signal intelligence
        String method = "bKash";

        // Check Rocket (DBBL / NexusPay)
        if (lowerSender.contains("rocket") || lowerSender.contains("16216") || lowerSender.contains("dbbl")
                || lowerSender.contains("nexus") || lowerSender.contains("dutch-bangla")
                || lowerText.contains("nexuspay") || lowerText.contains("nexus") || lowerText.contains("bit.ly/nexuspay")
                || lowerText.contains("rocket") || lowerText.contains("রকেট") || lowerText.contains("dbbl")
                || lowerText.contains("16216") || lowerText.contains("dutch-bangla")
                || lowerText.contains("a/c:***") || lowerText.contains("a/c:")
                || (lowerText.contains("fee:tk") && lowerText.contains("txnid"))) {
            method = "Rocket";
        }
        // Check Nagad (Post Office / 16167 / Ref: signature)
        else if (lowerSender.contains("nagad") || lowerSender.contains("16167") || lowerSender.contains("nagad-bd")
                || lowerText.contains("nagad") || lowerText.contains("নগদ")
                || (lowerText.contains("ref:") && (lowerText.contains("txnid") || lowerText.contains("balance:")))
                || Pattern.compile("txnid[:\\s]*[A-Za-z0-9]{8}\\b", Pattern.CASE_INSENSITIVE).matcher(lowerText).find()) {
            method = "Nagad";
        }
        // Check Upay (UCB / 16268)
        else if (lowerSender.contains("upay") || lowerSender.contains("16268") || lowerSender.contains("ucb")
                || lowerText.contains("upay") || lowerText.contains("উপায়") || lowerText.contains("উপায়")
                || lowerText.contains("16268") || lowerText.contains("ucb")) {
            method = "Upay";
        }
        // Check bKash (16247 / TrxID)
        else if (lowerSender.contains("bkash") || lowerSender.contains("16247")
                || lowerText.contains("bkash") || lowerText.contains("বিকাশ") || lowerText.contains("16247")
                || lowerText.contains("trxid")) {
            method = "bKash";
        }

        // 2. Parse TrxID / TxnID (Exclude 'Ref' to prevent matching reference notes)
        String trxId = null;
        Pattern trxPattern = Pattern.compile("(?:TrxID|TxnID|TxnId|Txn_ID|Txn|Transaction ID|আইডি)[:\\s]*([A-Za-z0-9]{7,16})", Pattern.CASE_INSENSITIVE);
        Matcher trxMatcher = trxPattern.matcher(text);
        if (trxMatcher.find()) {
            trxId = trxMatcher.group(1).trim().toUpperCase();
        } else {
            // Backup word match (8-14 alphanumeric characters)
            Pattern rawTrxPattern = Pattern.compile("\\b([A-Z0-9]{8,14})\\b");
            Matcher rawMatcher = rawTrxPattern.matcher(text);
            while (rawMatcher.find()) {
                String candidate = rawMatcher.group(1).toUpperCase();
                // Filter out common false positives
                if (!candidate.equals("SUCCESS") && !candidate.equals("PAYMENT") && !candidate.equals("BALANCE")
                        && !candidate.equals("DOWNLOAD") && !candidate.equals("NEXUSPAY") && !candidate.equals("RECEIVED")) {
                    trxId = candidate;
                    break;
                }
            }
        }

        if (trxId == null || trxId.length() < 7) {
            return null; // Not a payment notification SMS
        }

        // Method refinement by TrxID pattern if method is still default
        if ("bKash".equals(method)) {
            if (trxId.matches("^\\d{9,12}$")) {
                method = "Rocket";
            } else if (trxId.length() == 8) {
                method = "Nagad";
            }
        }

        // 3. Parse Amount
        double amount = 0.0;
        Pattern amtPattern = Pattern.compile("(?:Tk|Amount|received|টাকা|BDT)[:\\s]*([\\d,]+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);
        Matcher amtMatcher = amtPattern.matcher(text);
        if (amtMatcher.find()) {
            try {
                amount = Double.parseDouble(amtMatcher.group(1).replace(",", ""));
            } catch (Exception ignored) {}
        } else {
            Pattern amtAltPattern = Pattern.compile("([\\d,]+(?:\\.\\d+)?)\\s*(?:Tk|টাকা|BDT)", Pattern.CASE_INSENSITIVE);
            Matcher altMatcher = amtAltPattern.matcher(text);
            if (altMatcher.find()) {
                try {
                    amount = Double.parseDouble(altMatcher.group(1).replace(",", ""));
                } catch (Exception ignored) {}
            }
        }

        if (amount <= 0.0) {
            return null; // Missing or zero amount
        }

        // 4. Parse Merchant Remaining Balance
        double balance = 0.0;
        Pattern balPattern = Pattern.compile("(?:Balance|ব্যালেন্স|Current Balance)[:\\s]*(?:Tk|টাকা|BDT)?\\s*([\\d,]+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);
        Matcher balMatcher = balPattern.matcher(text);
        if (balMatcher.find()) {
            try {
                balance = Double.parseDouble(balMatcher.group(1).replace(",", ""));
            } catch (Exception ignored) {}
        }

        // 5. Parse Customer Phone Number (if present)
        String senderPhone = "";
        Pattern phonePattern = Pattern.compile("(?:from|Sender)[:\\s]*(01[3-9]\\d{8})", Pattern.CASE_INSENSITIVE);
        Matcher phoneMatcher = phonePattern.matcher(text);
        if (phoneMatcher.find()) {
            senderPhone = phoneMatcher.group(1);
        } else {
            Pattern acPattern = Pattern.compile("(?:A/C:?\\s*\\*{0,3}(\\d{3,11}))", Pattern.CASE_INSENSITIVE);
            Matcher acMatcher = acPattern.matcher(text);
            if (acMatcher.find()) {
                senderPhone = "A/C:***" + acMatcher.group(1);
            }
        }

        String recordId = "TX-" + System.currentTimeMillis();
        return new SmsRecord(recordId, sender != null ? sender : "Payment", method, trxId, amount, balance, senderPhone, rawMessage, timestamp, "PENDING");
    }
}
