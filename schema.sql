DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'checking',
    balance_cents INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (account_id) REFERENCES accounts (id)
);

-- Sample data so the dashboard has something to show out of the box.
INSERT INTO users (email, password, full_name, role) VALUES
    ('ada@finflow.test',   'seed', 'Ada Lovelace', 'customer'),
    ('grace@finflow.test', 'seed', 'Grace Hopper', 'customer'),
    ('admin@finflow.test', 'seed', 'Site Admin',   'admin');

INSERT INTO accounts (user_id, account_number, account_type, balance_cents) VALUES
    (1, 'FF-1001', 'checking', 452300),
    (1, 'FF-1002', 'savings',  1200000),
    (2, 'FF-2001', 'checking', 88050),
    (3, 'FF-9000', 'checking', 5000000);

INSERT INTO transactions (account_id, description, amount_cents) VALUES
    (1, 'Payroll deposit',       500000),
    (1, 'Grocery store',          -6540),
    (1, 'Electric bill',          -8900),
    (2, 'Transfer from FF-1001',  200000),
    (3, 'Coffee',                   -450);
