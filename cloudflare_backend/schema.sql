-- ===================================================================
-- PPM CLOUD - Pure Cloudflare D1 Serverless SQL Database Schema
-- Zero Firebase Dependency - 100% ACID Compliant
-- ===================================================================

-- 1. Users Table (Auth, Roles & Balances)
CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'User',
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    salt TEXT,
    auth_provider TEXT DEFAULT 'custom', -- 'custom' | 'google'
    avatar_url TEXT DEFAULT '',
    balance REAL NOT NULL DEFAULT 0.0,
    real_balance REAL NOT NULL DEFAULT 0.0,
    bonus_balance REAL NOT NULL DEFAULT 0.0,
    play_points REAL NOT NULL DEFAULT 0.0,
    pending_points REAL NOT NULL DEFAULT 0.0,
    loyalty_stars INTEGER NOT NULL DEFAULT 0,
    monthly_points REAL NOT NULL DEFAULT 0.0,
    monthly_points_month TEXT DEFAULT '',
    role TEXT NOT NULL DEFAULT 'user', -- 'user' | 'reseller' | 'admin'
    is_reseller INTEGER NOT NULL DEFAULT 0,
    is_banned INTEGER NOT NULL DEFAULT 0,
    ban_reason TEXT DEFAULT '',
    telegram_chat_id TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Orders Table (Quest & Service Orders)
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    name TEXT,
    email TEXT,
    game TEXT NOT NULL,
    logo TEXT DEFAULT '',
    method TEXT DEFAULT 'PP Coins',
    trx_id TEXT,
    amount REAL NOT NULL DEFAULT 2.0,
    paid_with_real REAL DEFAULT 0.0,
    paid_with_bonus REAL DEFAULT 0.0,
    is_free_task INTEGER DEFAULT 0,
    previous_balance REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'processing' | 'completed' | 'refunded' | 'rejected'
    admin_msg TEXT DEFAULT '',
    qid TEXT DEFAULT '',
    sync_code TEXT DEFAULT '',
    is_qid INTEGER DEFAULT 1,
    login_method TEXT DEFAULT 'qid',
    time_elapsed INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 1,
    gamer_name TEXT DEFAULT '',
    assigned_worker TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    completed_at INTEGER,
    refunded_at INTEGER,
    FOREIGN KEY(uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_orders_uid ON orders(uid);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);

-- 3. Deposits Table (Wallet Top-ups)
CREATE TABLE IF NOT EXISTS deposits (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    name TEXT,
    email TEXT,
    method TEXT NOT NULL, -- 'bKash' | 'Nagad' | 'Rocket' | 'Telegram Stars'
    amount REAL NOT NULL,
    coins REAL NOT NULL,
    trx_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
    admin_msg TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    reviewed_at INTEGER,
    FOREIGN KEY(uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_deposits_uid ON deposits(uid);
CREATE INDEX IF NOT EXISTS idx_deposits_trx ON deposits(trx_id);
CREATE INDEX IF NOT EXISTS idx_deposits_status ON deposits(status);

-- 4. Wallet Ledger (Full Audit Trail of every credit/debit)
CREATE TABLE IF NOT EXISTS wallet_ledger (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    type TEXT NOT NULL, -- 'pay_task' | 'auto_refund' | 'deposit' | 'bonus' | 'admin_adjust'
    amount REAL NOT NULL,
    balance_before REAL NOT NULL,
    balance_after REAL NOT NULL,
    order_id TEXT,
    note TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    FOREIGN KEY(uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_ledger_uid ON wallet_ledger(uid);
CREATE INDEX IF NOT EXISTS idx_ledger_created ON wallet_ledger(created_at DESC);

-- 5. Redemptions Table (Promo codes & Daily rewards)
CREATE TABLE IF NOT EXISTS redemptions (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    uid TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    FOREIGN KEY(uid) REFERENCES users(uid)
);

CREATE INDEX IF NOT EXISTS idx_redemptions_uid_code ON redemptions(uid, code);
