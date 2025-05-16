-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    logo_path TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, key)
);

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    invoice_number TEXT NOT NULL,
    client_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (client_id) REFERENCES clients (id)
);

-- Line items table
CREATE TABLE IF NOT EXISTS line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL,
    total REAL,
    date TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices (id)
);

-- Labor items table
CREATE TABLE IF NOT EXISTS labor_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    rate REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Items table
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create sales_tax table
CREATE TABLE IF NOT EXISTS sales_tax (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rate REAL NOT NULL,
    description TEXT NOT NULL UNIQUE
); 