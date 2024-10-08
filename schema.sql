-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS ledger_entries CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS carts CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS customer_visits CASCADE;
DROP TABLE IF EXISTS potions CASCADE;
DROP TABLE IF EXISTS global_inventory CASCADE;
DROP TABLE IF EXISTS barrels CASCADE;
DROP TABLE IF EXISTS barrel_visits CASCADE;

-- Barrel Visits Table (Parent)
CREATE TABLE barrel_visits (
    barrel_visit_id BIGSERIAL PRIMARY KEY,
    visit_time TIMESTAMPTZ NOT NULL,
    in_game_day VARCHAR,
    in_game_hour INT
);

-- Barrels Table (Reference Barrel Visits)
CREATE TABLE barrels (
    barrel_id BIGSERIAL PRIMARY KEY,
    sku VARCHAR NOT NULL,
    ml_per_barrel INT NOT NULL,
    potion_type VARCHAR(10) NOT NULL,
    price INT NOT NULL,
    quantity INT NOT NULL
);

-- Global Inventory Table (Independent)
CREATE TABLE global_inventory (
    id BIGINT PRIMARY KEY,
    gold INT DEFAULT 100,
    total_potions INT DEFAULT 0,
    total_ml INT DEFAULT 0,
    red_ml INT DEFAULT 0,
    green_ml INT DEFAULT 0,
    blue_ml INT DEFAULT 0,
    dark_ml INT DEFAULT 0,
    potion_capacity_units INT DEFAULT 1,
    ml_capacity_units INT DEFAULT 1
);

-- Potions Table (Independent)
CREATE TABLE potions (
    potion_id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    sku VARCHAR NOT NULL UNIQUE,
    red_ml INT NOT NULL,
    green_ml INT NOT NULL,
    blue_ml INT NOT NULL,
    dark_ml INT NOT NULL,
    total_ml INT NOT NULL,
    price INT NOT NULL,
    description TEXT,
    current_quantity INT NOT NULL
);

-- Customers Table (References Visits)
CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT REFERENCES visits(visit_id),
    customer_name VARCHAR NOT NULL,
    character_class VARCHAR NOT NULL,
    level INT NOT NULL
);

-- Customer Visits Table (Parent)
CREATE TABLE customer_visits (
    visit_id BIGSERIAL PRIMARY KEY,
    visit_time TIMESTAMPTZ NOT NULL,
    in_game_day VARCHAR,
    in_game_hour INT,
);

-- Carts Table (References Customers)
CREATE TABLE carts (
    cart_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT REFERENCES customers(customer_id),
    in_game_day VARCHAR,
    in_game_hour INT,
    created_at TIMESTAMPTZ NOT NULL,
    checked_out BOOLEAN DEFAULT FALSE,
    checked_out_at TIMESTAMPTZ,
    total_potions_bought INT DEFAULT 0,
    total_gold_paid INT DEFAULT 0,
    payment VARCHAR
);

-- Cart Items Table (References Carts and Potions)
CREATE TABLE cart_items (
    cart_item_id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT REFERENCES carts(cart_id),
    potion_id INT REFERENCES potions(potion_id),
    quantity INT NOT NULL,
    price INT NOT NULL,
    line_item_total INT NOT NULL
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Ledger Entries Table (References Potions)
CREATE TABLE ledger_entries (
    ledger_entry_id BIGSERIAL PRIMARY KEY,
    change_type VARCHAR NOT NULL,
    sub_type VARCHAR,
    amount INT NOT NULL,
    ml_type VARCHAR,
    potion_id INT REFERENCES potions(potion_id),
    description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
