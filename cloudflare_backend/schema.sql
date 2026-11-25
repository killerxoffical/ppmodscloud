-- ===================================================================
-- PPM CLOUD - Pure Cloudflare D1 Serverless SQL Database Schema
-- Single Coin Balance (PP Coin) • 8-char PP ID • Persistent Cloud Storage
-- ===================================================================

-- 1. Users Table (Email + Password Auth, 8-char PP ID, Single Balance)
CREATE TABLE IF NOT EXISTS users (
    pp_id TEXT PRIMARY KEY,               -- 8-char alphanumeric e.g. '9JO38FH4'
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,               -- Real/plain password accessible to Admin
    name TEXT NOT NULL DEFAULT 'User',
    avatar_url TEXT DEFAULT '',
    coins REAL NOT NULL DEFAULT 0.0,      -- Only 1 balance: PP Coin
    monthly_points REAL NOT NULL DEFAULT 0.0,
    monthly_points_month TEXT DEFAULT '',
    device_id TEXT DEFAULT '',            -- Device Lock (App active device)
    role TEXT NOT NULL DEFAULT 'user',    -- 'user' | 'admin'
    is_banned INTEGER NOT NULL DEFAULT 0,
    ban_reason TEXT DEFAULT '',
    telegram_chat_id TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_device ON users(device_id);

-- 2. Orders Table (Clean Quest Orders)
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,                -- PP ID
    user_email TEXT,
    game TEXT NOT NULL,
    logo TEXT DEFAULT '',
    coins REAL NOT NULL DEFAULT 2.0,      -- Deducted PP Coins
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'completed' | 'refunded'
    qid TEXT DEFAULT '',                  -- 6-digit QID Code
    sync_code TEXT DEFAULT '',
    admin_msg TEXT DEFAULT '',
    time_elapsed INTEGER DEFAULT 1,
    retry_count INTEGER DEFAULT 1,
    created_at INTEGER NOT NULL,
    completed_at INTEGER,
    refunded_at INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(pp_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_uid ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);

-- 3. Deposits Table (bKash / Nagad / Rocket Top-up)
CREATE TABLE IF NOT EXISTS deposits (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,                -- PP ID
    user_email TEXT,
    method TEXT NOT NULL,                 -- 'bKash' | 'Nagad' | 'Rocket'
    amount_taka REAL NOT NULL,            -- Paid in BDT
    coins REAL NOT NULL,                  -- Awarded PP Coins
    trx_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
    admin_msg TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    reviewed_at INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(pp_id)
);

CREATE INDEX IF NOT EXISTS idx_deposits_uid ON deposits(user_id);
CREATE INDEX IF NOT EXISTS idx_deposits_trx ON deposits(trx_id);
CREATE INDEX IF NOT EXISTS idx_deposits_status ON deposits(status);

-- 4. Transactions Table (10 per page pagination, max 200 per user)
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,                -- PP ID
    type TEXT NOT NULL,                   -- 'pay_task' | 'auto_refund' | 'deposit' | 'daily_claim' | 'redeem' | 'admin_adjust'
    coins REAL NOT NULL,                  -- + coins or - coins
    balance_before REAL NOT NULL,
    balance_after REAL NOT NULL,
    title TEXT NOT NULL,
    details TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(pp_id)
);

CREATE INDEX IF NOT EXISTS idx_tx_uid ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_created ON transactions(created_at DESC);

-- 5. Portal Games & Quests (Permanent Cloud Persistence - Never lost on Render restarts!)
CREATE TABLE IF NOT EXISTS portal_games (
    game_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    package_name TEXT NOT NULL,
    icon_url TEXT DEFAULT '',
    quests_json TEXT NOT NULL DEFAULT '[]', -- JSON array of quests
    cost_coins REAL NOT NULL DEFAULT 2.0,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_games_active ON portal_games(is_active, sort_order);

-- 6. Promo Codes & Redemptions
CREATE TABLE IF NOT EXISTS redemptions (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    user_id TEXT NOT NULL,
    coins REAL NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(pp_id)
);

CREATE INDEX IF NOT EXISTS idx_redemptions_uid_code ON redemptions(user_id, code);

-- 7. Promo Codes Definition (Admin managed)
CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    coins REAL NOT NULL,
    max_uses INTEGER NOT NULL DEFAULT 100,
    used_count INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL
);
