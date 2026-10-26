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
-- Passwords are stored as salted scrypt hashes (werkzeug generate_password_hash).
-- All three seed users still log in with the password 'seed'.
INSERT INTO users (email, password, full_name, role) VALUES
    ('ada@finflow.test',   'scrypt:32768:8:1$eQcyv9X15w8l0d57$0004107218a82a9b0cb8608a62c3355f9b7839f393a643adee69965859e5f36acf20026402400b79ed00109c5a49ba36d0398060ee3c125ad9f221d8b49764b7', 'Ada Lovelace', 'customer'),
    ('grace@finflow.test', 'scrypt:32768:8:1$2KwrH9LI9pYbGwcN$1d37148cb122c89aa1a387060c6ab89c061a4bd5579df61d1a86ad5d4fa915d6071a6c86f252204e26d217aeefe8a4bbd5ab9b40532f584a37e242b98b08324b', 'Grace Hopper', 'customer'),
    ('admin@finflow.test', 'scrypt:32768:8:1$UGsjbnXjMQr6P9lD$57f9682628c6dc7cc3e804c0409dffd2dd9feacf2c358a69a9032758c435256a0ed6c29df1d980b760bf9a4326c26883737b940a626e0ef8f62bfe65fc365e96', 'Site Admin',   'admin');

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
