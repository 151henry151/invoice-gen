DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS labor_items;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS sales_tax_rates;
DROP TABLE IF EXISTS line_items;
DROP TABLE IF EXISTS invoices;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    profile_picture TEXT
);

CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    email TEXT,
    phone TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    email TEXT,
    phone TEXT,
    logo_path TEXT,
    invoice_template TEXT DEFAULT 'invoice_pretty',
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE labor_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    hours REAL NOT NULL,
    rate REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, key)
);

CREATE TABLE sales_tax_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    rate REAL NOT NULL,
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    invoice_number TEXT NOT NULL,
    client_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    total REAL NOT NULL,
    sales_tax_id INTEGER,
    tax_applies_to TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (client_id) REFERENCES clients (id),
    FOREIGN KEY (sales_tax_id) REFERENCES sales_tax_rates (id)
);

CREATE TABLE line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity TEXT NOT NULL,
    unit_price REAL NOT NULL,
    total REAL NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices (id)
); 