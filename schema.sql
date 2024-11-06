-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS ledger_entries CASCADE;
DROP TABLE IF EXISTS capacity_upgrade_thresholds CASCADE;
DROP TABLE IF EXISTS strategy_thresholds CASCADE;
DROP TABLE IF EXISTS strategy_transitions CASCADE;
DROP TABLE IF EXISTS active_strategy CASCADE;
DROP TABLE IF EXISTS block_potion_priorities CASCADE;
DROP TABLE IF EXISTS strategy_time_blocks CASCADE;
DROP TABLE IF EXISTS barrel_purchases CASCADE;
DROP TABLE IF EXISTS barrel_details CASCADE; 
DROP TABLE IF EXISTS barrel_visits CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS carts CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS customer_visits CASCADE;
DROP TABLE IF EXISTS current_game_time CASCADE;
DROP TABLE IF EXISTS game_time CASCADE;
DROP TABLE IF EXISTS color_definitions CASCADE;
DROP TABLE IF EXISTS strategies CASCADE;
DROP TABLE IF EXISTS time_blocks CASCADE;
DROP TABLE IF EXISTS potions CASCADE;
DROP VIEW IF EXISTS current_state CASCADE;

-- Core game time tracking
CREATE TABLE game_time (
    time_id BIGSERIAL PRIMARY KEY,
    in_game_day TEXT NOT NULL CHECK (in_game_day IN (
        'Hearthday', 'Crownday', 'Blesseday', 'Soulday', 
        'Edgeday', 'Bloomday', 'Arcanaday'
    )),
    in_game_hour INT NOT NULL CHECK (
        in_game_hour >= 0 
        AND in_game_hour <= 22 
        AND in_game_hour % 2 = 0
    ),
    bottling_time_id BIGINT,  -- 3 ticks ahead
    barrel_time_id BIGINT,    -- 4 ticks ahead
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(in_game_day, in_game_hour)
);

-- Current game time
CREATE TABLE current_game_time (
    id BIGSERIAL PRIMARY KEY,
    game_time_id BIGINT REFERENCES game_time(time_id),
    current_day TEXT NOT NULL CHECK (current_day IN (
        'Hearthday', 'Crownday', 'Blesseday', 'Soulday', 
        'Edgeday', 'Bloomday', 'Arcanaday'
    )),
    current_hour INT NOT NULL CHECK (
        current_hour >= 0 
        AND current_hour <= 22 
        AND current_hour % 2 = 0
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Color system
CREATE TABLE color_definitions (
    color_id BIGSERIAL PRIMARY KEY,
    color_name TEXT NOT NULL UNIQUE CHECK (
        color_name IN ('RED', 'GREEN', 'BLUE', 'DARK')
    ),
    color_index INT NOT NULL UNIQUE CHECK (color_index >= 0 AND color_index < 4),
    priority_order INT NOT NULL UNIQUE CHECK (priority_order > 0)
);

-- Time blocks
CREATE TABLE time_blocks (
    block_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (
        name IN ('NIGHT', 'MORNING', 'AFTERNOON', 'EVENING')
    ),
    start_hour INT NOT NULL,
    end_hour INT NOT NULL,
    CONSTRAINT valid_hours CHECK (
        start_hour >= 0 
        AND end_hour <= 23
        AND start_hour < end_hour
        AND start_hour % 2 = 0 
        AND end_hour % 2 = 0
    ),
    UNIQUE(start_hour, end_hour)
);

-- Strategy system
CREATE TABLE strategies (
    strategy_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (
        name IN ('PREMIUM', 'PENETRATION', 'TIERED', 'DYNAMIC')
    ),
    min_gold INT NOT NULL CHECK (min_gold >= 0),
    max_gold INT,
    ml_capacity_units INT NOT NULL CHECK (ml_capacity_units > 0),
    potion_capacity_units INT NOT NULL CHECK (potion_capacity_units > 0),
    max_potions_per_sku INT NOT NULL,
    CONSTRAINT valid_gold_range CHECK (
        max_gold IS NULL OR max_gold > min_gold
    )
);

-- Initial insert for PREMIUM strategy
CREATE TABLE active_strategy (
    strategy_id BIGINT REFERENCES strategies(strategy_id),
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    game_time_id BIGINT REFERENCES game_time(time_id),
    PRIMARY KEY (strategy_id, game_time_id)
);

-- Strategy transitions with inventory and capacity thresholds
CREATE TABLE strategy_transitions (
    from_strategy_id BIGINT REFERENCES strategies(strategy_id),
    to_strategy_id BIGINT REFERENCES strategies(strategy_id),
    gold_threshold INT,
    potion_threshold INT,
    ml_threshold INT,
    ml_capacity_threshold INT NOT NULL,
    potion_capacity_threshold INT NOT NULL,
    require_all_thresholds BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (from_strategy_id, to_strategy_id)
);

CREATE TABLE strategy_time_blocks (
    block_id BIGSERIAL PRIMARY KEY,
    strategy_id BIGINT REFERENCES strategies(strategy_id),
    time_block_id BIGINT REFERENCES time_blocks(block_id),
    day_name TEXT NOT NULL CHECK (day_name IN (
        'Hearthday', 'Crownday', 'Blesseday', 'Soulday', 
        'Edgeday', 'Bloomday', 'Arcanaday'
    )),
    buffer_multiplier FLOAT NOT NULL DEFAULT 1.0,
    UNIQUE(strategy_id, time_block_id, day_name)
);

-- Potion system
CREATE TABLE potions (
    potion_id BIGSERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    red_ml INT NOT NULL DEFAULT 0 CHECK (red_ml >= 0),
    green_ml INT NOT NULL DEFAULT 0 CHECK (green_ml >= 0),
    blue_ml INT NOT NULL DEFAULT 0 CHECK (blue_ml >= 0),
    dark_ml INT NOT NULL DEFAULT 0 CHECK (dark_ml >= 0),
    base_price INT NOT NULL CHECK (base_price > 0),
    current_quantity INT NOT NULL DEFAULT 0 CHECK (current_quantity >= 0),
    color_id BIGINT REFERENCES color_definitions(color_id),
    CONSTRAINT valid_ml_total CHECK (
        red_ml + green_ml + blue_ml + dark_ml = 100
    )
);

-- Potion mix within each time block
CREATE TABLE block_potion_priorities (
    priority_id BIGSERIAL PRIMARY KEY,
    block_id BIGINT REFERENCES strategy_time_blocks(block_id),
    potion_id BIGINT REFERENCES potions(potion_id),
    sales_mix FLOAT NOT NULL CHECK (sales_mix > 0 AND sales_mix <= 1.0),
    priority_order INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(block_id, potion_id)
);

-- Barrel system
CREATE TABLE barrel_visits (
    visit_id BIGSERIAL PRIMARY KEY,
    time_id BIGINT REFERENCES game_time(time_id),
    wholesale_catalog JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE barrel_details (
    barrel_id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT REFERENCES barrel_visits(visit_id),
    sku TEXT NOT NULL CHECK (
        sku ~ '^(SMALL|MEDIUM|LARGE)_(RED|GREEN|BLUE|DARK)_BARREL$'
    ),
    ml_per_barrel INT NOT NULL CHECK (
        (sku LIKE 'SMALL_%' AND ml_per_barrel = 500) OR
        (sku LIKE 'MEDIUM_%' AND ml_per_barrel = 2500) OR
        (sku LIKE 'LARGE_%' AND ml_per_barrel = 10000)
    ),
    potion_type JSONB NOT NULL,
    price INT NOT NULL CHECK (price > 0),
    quantity INT NOT NULL CHECK (quantity > 0),
    color_id BIGINT REFERENCES color_definitions(color_id),
    UNIQUE(visit_id, sku)
);

CREATE TABLE barrel_purchases (
    purchase_id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT REFERENCES barrel_visits(visit_id),
    barrel_id BIGINT REFERENCES barrel_details(barrel_id),
    time_id BIGINT REFERENCES game_time(time_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    total_cost INT NOT NULL CHECK (total_cost > 0),
    ml_added INT NOT NULL CHECK (ml_added > 0),
    color_id BIGINT REFERENCES color_definitions(color_id),
    purchase_success BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Customer system
CREATE TABLE customer_visits (
    visit_record_id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT NOT NULL,            -- This is the order_id
    time_id BIGINT REFERENCES game_time(time_id),
    customers JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    visit_record_id BIGINT REFERENCES customer_visits(visit_record_id),
    visit_id BIGINT NOT NULL,
    time_id BIGINT REFERENCES game_time(time_id),
    customer_name TEXT NOT NULL,
    character_class TEXT NOT NULL,
    level INT NOT NULL CHECK (level >= 1 AND level <= 20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Cart system
CREATE TABLE carts (
    cart_id BIGSERIAL PRIMARY KEY,
    visit_id BIGINT NOT NULL,
    customer_id BIGINT REFERENCES customers(customer_id),
    time_id BIGINT REFERENCES game_time(time_id),
    checked_out BOOLEAN NOT NULL DEFAULT FALSE,
    purchase_success BOOLEAN,
    checked_out_at TIMESTAMPTZ,
    total_potions INT NOT NULL DEFAULT 0 CHECK (total_potions >= 0),
    total_gold INT NOT NULL DEFAULT 0 CHECK (total_gold >= 0),
    payment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_checkout CHECK (
        (checked_out = FALSE AND checked_out_at IS NULL) OR
        (checked_out = TRUE AND checked_out_at IS NOT NULL)
    )
);

CREATE TABLE cart_items (
    item_id BIGSERIAL PRIMARY KEY,
    cart_id BIGINT REFERENCES carts(cart_id),
    visit_id BIGINT NOT NULL,
    potion_id BIGINT REFERENCES potions(potion_id),
    time_id BIGINT REFERENCES game_time(time_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price INT NOT NULL CHECK (unit_price > 0),
    line_total INT NOT NULL CHECK (line_total = quantity * unit_price),
    UNIQUE(cart_id, potion_id)
);

-- Capacity upgrade threshold system
CREATE TABLE capacity_upgrade_thresholds (
    threshold_id BIGSERIAL PRIMARY KEY,
    min_potion_units INT NOT NULL,          -- Minimum potion capacity units required
    max_potion_units INT,                   -- Maximum potion capacity units required
    min_ml_units INT NOT NULL,              -- Minimum ml capacity units required
    max_ml_units INT,                       -- Maximum ml capacity units required
    gold_threshold INT NOT NULL,            -- Gold required
    secondary_gold_threshold INT,           -- Secondary gold threshold for inventory checks
    capacity_check_threshold FLOAT,         -- Capacity check (e.g. 50%)
    ml_capacity_purchase INT NOT NULL,      -- How many ml units to purchase
    potion_capacity_purchase INT NOT NULL,  -- How many potion units to purchase
    priority_order INT NOT NULL,            -- Higher number = higher priority for sorting
    requires_inventory_check BOOLEAN NOT NULL DEFAULT false, -- Check inventory levels boolean
    CHECK (min_potion_units <= max_potion_units),
    CHECK (min_ml_units <= max_ml_units),
    CHECK (capacity_check_threshold >= 0 AND capacity_check_threshold <= 1)
);

-- Ledger system
CREATE TABLE ledger_entries (
    entry_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time_id BIGINT REFERENCES game_time(time_id),
    entry_type TEXT NOT NULL CHECK (
        entry_type IN (
            'BARREL_PURCHASE',
            'POTION_BOTTLED',
            'POTION_SOLD',
            'CAPACITY_UPGRADE',
            'GOLD_CHANGE',
            'ML_ADJUSTMENT',
            'STRATEGY_CHANGE',
            'ADMIN_CHANGE'
        )
    ),
    -- Reference fields
    barrel_purchase_id BIGINT REFERENCES barrel_purchases(purchase_id),
    cart_id BIGINT REFERENCES carts(cart_id),
    potion_id BIGINT REFERENCES potions(potion_id),
    color_id BIGINT REFERENCES color_definitions(color_id),
    
    -- Change amounts
    gold_change INT,
    ml_change INT,
    potion_change INT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- View ledgers
CREATE VIEW current_state AS
WITH ledger_totals AS (
    SELECT
        COALESCE(SUM(gold_change), 100) as gold,
        COALESCE(SUM(CASE WHEN color_id = (SELECT color_id FROM color_definitions WHERE color_name = 'RED') 
            THEN ml_change ELSE 0 END), 0) as red_ml,
        COALESCE(SUM(CASE WHEN color_id = (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN') 
            THEN ml_change ELSE 0 END), 0) as green_ml,
        COALESCE(SUM(CASE WHEN color_id = (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE') 
            THEN ml_change ELSE 0 END), 0) as blue_ml,
        COALESCE(SUM(CASE WHEN color_id = (SELECT color_id FROM color_definitions WHERE color_name = 'DARK') 
            THEN ml_change ELSE 0 END), 0) as dark_ml,
        COALESCE(SUM(potion_change), 0) as total_potions,
        1 + COUNT(*) FILTER (WHERE entry_type = 'CAPACITY_UPGRADE' AND potion_change IS NOT NULL) as potion_capacity_units,
        1 + COUNT(*) FILTER (WHERE entry_type = 'CAPACITY_UPGRADE' AND ml_change IS NOT NULL) as ml_capacity_units
    FROM ledger_entries
)
SELECT 
    gold,
    red_ml,
    green_ml,
    blue_ml,
    dark_ml,
    total_potions,
    potion_capacity_units,
    ml_capacity_units,
    (red_ml + green_ml + blue_ml + dark_ml) as total_ml,
    (potion_capacity_units * 50) as max_potions,
    (ml_capacity_units * 10000) as max_ml,
    (SELECT strategy_id 
     FROM strategies 
     WHERE gold BETWEEN min_gold AND COALESCE(max_gold, gold)
     LIMIT 1) as strategy_id
FROM ledger_totals;

-- Indexes for common queries
CREATE INDEX idx_game_time_day_hour ON game_time(in_game_day, in_game_hour);
CREATE INDEX idx_barrel_visits_time ON barrel_visits(time_id);
CREATE INDEX idx_barrel_purchases_time ON barrel_purchases(time_id);
CREATE INDEX idx_barrel_purchases_success ON barrel_purchases(purchase_success);
CREATE INDEX idx_cart_items_potion ON cart_items(potion_id);
CREATE INDEX idx_customer_visits_visit_id ON customer_visits(visit_id);
CREATE INDEX idx_customers_visit_id ON customers(visit_id);
CREATE INDEX idx_carts_visit_id ON carts(visit_id);
CREATE INDEX idx_cart_items_visit_id ON cart_items(visit_id);
CREATE INDEX idx_ledger_entries_entry_type ON ledger_entries (entry_type);
CREATE INDEX idx_ledger_entries_gold_change ON ledger_entries (gold_change) WHERE gold_change IS NOT NULL;
CREATE INDEX idx_strategy_time_blocks_lookup ON strategy_time_blocks(strategy_id, time_block_id, day_name);
CREATE INDEX idx_potion_sales_time ON cart_items(time_id, potion_id);

-- Populate game_time with all day/hour combinations and their references
INSERT INTO game_time
(time_id, in_game_day, in_game_hour, bottling_time_id, barrel_time_id)
VALUES 
-- HEARTHDAY
(1, 'Hearthday', 0, 4, 5),
(2, 'Hearthday', 2, 5, 6),
(3, 'Hearthday', 4, 6, 7),
(4, 'Hearthday', 6, 7, 8),
(5, 'Hearthday', 8, 8, 9),
(6, 'Hearthday', 10, 9, 10),
(7, 'Hearthday', 12, 10, 11),
(8, 'Hearthday', 14, 11, 12),
(9, 'Hearthday', 16, 12, 13),
(10, 'Hearthday', 18, 13, 14),
(11, 'Hearthday', 20, 14, 15),
(12, 'Hearthday', 22, 15, 16),

-- CROWNDAY
(13, 'Crownday', 0, 16, 17),
(14, 'Crownday', 2, 17, 18),
(15, 'Crownday', 4, 18, 19),
(16, 'Crownday', 6, 19, 20),
(17, 'Crownday', 8, 20, 21),
(18, 'Crownday', 10, 21, 22),
(19, 'Crownday', 12, 22, 23),
(20, 'Crownday', 14, 23, 24),
(21, 'Crownday', 16, 24, 25),
(22, 'Crownday', 18, 25, 26),
(23, 'Crownday', 20, 26, 27),
(24, 'Crownday', 22, 27, 28),

-- BLESSEDAY
(25, 'Blesseday', 0, 28, 29),
(26, 'Blesseday', 2, 29, 30),
(27, 'Blesseday', 4, 30, 31),
(28, 'Blesseday', 6, 31, 32),
(29, 'Blesseday', 8, 32, 33),
(30, 'Blesseday', 10, 33, 34),
(31, 'Blesseday', 12, 34, 35),
(32, 'Blesseday', 14, 35, 36),
(33, 'Blesseday', 16, 36, 37),
(34, 'Blesseday', 18, 37, 38),
(35, 'Blesseday', 20, 38, 39),
(36, 'Blesseday', 22, 39, 40),

-- SOULDAY
(37, 'Soulday', 0, 40, 41),
(38, 'Soulday', 2, 41, 42),
(39, 'Soulday', 4, 42, 43),
(40, 'Soulday', 6, 43, 44),
(41, 'Soulday', 8, 44, 45),
(42, 'Soulday', 10, 45, 46),
(43, 'Soulday', 12, 46, 47),
(44, 'Soulday', 14, 47, 48),
(45, 'Soulday', 16, 48, 49),
(46, 'Soulday', 18, 49, 50),
(47, 'Soulday', 20, 50, 51),
(48, 'Soulday', 22, 51, 52),

-- EDGEDAY
(49, 'Edgeday', 0, 52, 53),
(50, 'Edgeday', 2, 53, 54),
(51, 'Edgeday', 4, 54, 55),
(52, 'Edgeday', 6, 55, 56),
(53, 'Edgeday', 8, 56, 57),
(54, 'Edgeday', 10, 57, 58),
(55, 'Edgeday', 12, 58, 59),
(56, 'Edgeday', 14, 59, 60),
(57, 'Edgeday', 16, 60, 61),
(58, 'Edgeday', 18, 61, 62),
(59, 'Edgeday', 20, 62, 63),
(60, 'Edgeday', 22, 63, 64),

-- BLOOMDAY
(61, 'Bloomday', 0, 64, 65),
(62, 'Bloomday', 2, 65, 66),
(63, 'Bloomday', 4, 66, 67),
(64, 'Bloomday', 6, 67, 68),
(65, 'Bloomday', 8, 68, 69),
(66, 'Bloomday', 10, 69, 70),
(67, 'Bloomday', 12, 70, 71),
(68, 'Bloomday', 14, 71, 72),
(69, 'Bloomday', 16, 72, 73),
(70, 'Bloomday', 18, 73, 74),
(71, 'Bloomday', 20, 74, 75),
(72, 'Bloomday', 22, 75, 76),

-- ARCANADAY
(73, 'Arcanaday', 0, 76, 77),
(74, 'Arcanaday', 2, 77, 78),
(75, 'Arcanaday', 4, 78, 79),
(76, 'Arcanaday', 6, 79, 80),
(77, 'Arcanaday', 8, 80, 81),
(78, 'Arcanaday', 10, 81, 82),
(79, 'Arcanaday', 12, 82, 83),
(80, 'Arcanaday', 14, 83, 84),
(81, 'Arcanaday', 16, 84, 1),
(82, 'Arcanaday', 18, 1, 2),
(83, 'Arcanaday', 20, 2, 3),
(84, 'Arcanaday', 22, 3, 4);

-- Color Definitions - Priority order matches business logic
INSERT INTO color_definitions 
(color_name, color_index, priority_order) 
VALUES
('DARK', 3, 1),    -- Highest priority, rare resource
('BLUE', 2, 2),    -- Second priority, premium color
('RED', 0, 3),     -- Third priority, common color
('GREEN', 1, 4);   -- Fourth priority, common color

-- Time Blocks - Game day divisions
INSERT INTO time_blocks 
(name, start_hour, end_hour) 
VALUES
('NIGHT', 0, 4),
('MORNING', 6, 10),
('AFTERNOON', 12, 16),
('EVENING', 18, 22);

-- Base Strategies
INSERT INTO strategies
(name, min_gold, max_gold, ml_capacity_units, potion_capacity_units, max_potions_per_sku)
VALUES
('PREMIUM', 0, 249, 1, 1, 20),
('PENETRATION', 250, 1000, 1, 1, 20),
('TIERED', 1001, 2000, 2, 2, 30),
('DYNAMIC', 2001, NULL, 4, 3, 50);

INSERT INTO active_strategy (
    strategy_id,
    game_time_id
) VALUES (
    (SELECT strategy_id FROM strategies WHERE name = 'PREMIUM'),
    (SELECT MIN(time_id) FROM game_time)
);

-- Strategy transition thresholds
INSERT INTO strategy_transitions
(from_strategy_id, to_strategy_id, gold_threshold, potion_threshold, ml_threshold, 
 ml_capacity_threshold, potion_capacity_threshold, require_all_thresholds)
VALUES
-- PREMIUM to PENETRATION (requires any of: 250 gold, 5 potions, or 500 ml)
((SELECT strategy_id FROM strategies WHERE name = 'PREMIUM'),
 (SELECT strategy_id FROM strategies WHERE name = 'PENETRATION'),
 250, 5, 500, 1, 1, true),

-- PENETRATION to TIERED (only checks capacity)
((SELECT strategy_id FROM strategies WHERE name = 'PENETRATION'),
 (SELECT strategy_id FROM strategies WHERE name = 'TIERED'),
 NULL, NULL, NULL, 2, 2, false),

-- TIERED to DYNAMIC (only checks capacity)
((SELECT strategy_id FROM strategies WHERE name = 'TIERED'),
 (SELECT strategy_id FROM strategies WHERE name = 'DYNAMIC'),
 NULL, NULL, NULL, 4, 3, false);

-- Insert strategy_time_blocks
INSERT INTO strategy_time_blocks 
    (strategy_id, time_block_id, day_name, buffer_multiplier)
VALUES
    -- HEARTHDAY
    -- PREMIUM
    (1, 1, 'Hearthday', 1.0),  -- NIGHT
    (1, 2, 'Hearthday', 1.0),  -- MORNING
    (1, 3, 'Hearthday', 1.0),  -- AFTERNOON
    (1, 4, 'Hearthday', 1.0),  -- EVENING

    -- PENETRATION
    (2, 1, 'Hearthday', 1.0), 
    (2, 2, 'Hearthday', 1.0),
    (2, 3, 'Hearthday', 1.0),
    (2, 4, 'Hearthday', 1.0),

    -- TIERED
    (3, 1, 'Hearthday', 1.0),
    (3, 2, 'Hearthday', 1.0),
    (3, 3, 'Hearthday', 1.0),
    (3, 4, 'Hearthday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Hearthday', 1.0),
    (4, 2, 'Hearthday', 1.0),
    (4, 3, 'Hearthday', 1.0),
    (4, 4, 'Hearthday', 1.0),

    -- CROWNDAY
    -- PREMIUM
    (1, 1, 'Crownday', 1.0),
    (1, 2, 'Crownday', 1.0),
    (1, 3, 'Crownday', 1.0),
    (1, 4, 'Crownday', 1.0),

    -- PENETRATION
    (2, 1, 'Crownday', 1.0), 
    (2, 2, 'Crownday', 1.0),
    (2, 3, 'Crownday', 1.0),
    (2, 4, 'Crownday', 1.0),

    -- TIERED
    (3, 1, 'Crownday', 1.0),
    (3, 2, 'Crownday', 1.0),
    (3, 3, 'Crownday', 1.0),
    (3, 4, 'Crownday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Crownday', 1.0),
    (4, 2, 'Crownday', 1.0),
    (4, 3, 'Crownday', 1.0),
    (4, 4, 'Crownday', 1.0),

    -- BLESSEDAY
    -- PREMIUM
    (1, 1, 'Blesseday', 1.0),
    (1, 2, 'Blesseday', 1.0),
    (1, 3, 'Blesseday', 1.0),
    (1, 4, 'Blesseday', 1.0),

    -- PENETRATION
    (2, 1, 'Blesseday', 1.0), 
    (2, 2, 'Blesseday', 1.0),
    (2, 3, 'Blesseday', 1.0),
    (2, 4, 'Blesseday', 1.0),

    -- TIERED
    (3, 1, 'Blesseday', 1.0),
    (3, 2, 'Blesseday', 1.0),
    (3, 3, 'Blesseday', 1.0),
    (3, 4, 'Blesseday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Blesseday', 1.0),
    (4, 2, 'Blesseday', 1.0),
    (4, 3, 'Blesseday', 1.0),
    (4, 4, 'Blesseday', 1.0),

    -- SOULDAY
    -- PREMIUM
    (1, 1, 'Soulday', 1.0),
    (1, 2, 'Soulday', 1.0),
    (1, 3, 'Soulday', 1.0),
    (1, 4, 'Soulday', 1.0),

    -- PENETRATION
    (2, 1, 'Soulday', 1.0), 
    (2, 2, 'Soulday', 1.0),
    (2, 3, 'Soulday', 1.0),
    (2, 4, 'Soulday', 1.0),

    -- TIERED
    (3, 1, 'Soulday', 1.0),
    (3, 2, 'Soulday', 1.0),
    (3, 3, 'Soulday', 1.0),
    (3, 4, 'Soulday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Soulday', 1.0),
    (4, 2, 'Soulday', 1.0),
    (4, 3, 'Soulday', 1.0),
    (4, 4, 'Soulday', 1.0),

    -- EDGEDAY
    -- PREMIUM
    (1, 1, 'Edgeday', 1.0),
    (1, 2, 'Edgeday', 1.0),
    (1, 3, 'Edgeday', 1.0),
    (1, 4, 'Edgeday', 1.0),

    -- PENETRATION
    (2, 1, 'Edgeday', 1.0), 
    (2, 2, 'Edgeday', 1.0),
    (2, 3, 'Edgeday', 1.0),
    (2, 4, 'Edgeday', 1.0),

    -- TIERED
    (3, 1, 'Edgeday', 1.0),
    (3, 2, 'Edgeday', 1.0),
    (3, 3, 'Edgeday', 1.0),
    (3, 4, 'Edgeday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Edgeday', 1.0),
    (4, 2, 'Edgeday', 1.0),
    (4, 3, 'Edgeday', 1.0),
    (4, 4, 'Edgeday', 1.0),

    -- BLOOMDAY
    -- PREMIUM
    (1, 1, 'Bloomday', 1.0),
    (1, 2, 'Bloomday', 1.0),
    (1, 3, 'Bloomday', 1.0),
    (1, 4, 'Bloomday', 1.0),

    -- PENETRATION
    (2, 1, 'Bloomday', 1.0), 
    (2, 2, 'Bloomday', 1.0),
    (2, 3, 'Bloomday', 1.0),
    (2, 4, 'Bloomday', 1.0),

    -- TIERED
    (3, 1, 'Bloomday', 1.0),
    (3, 2, 'Bloomday', 1.0),
    (3, 3, 'Bloomday', 1.0),
    (3, 4, 'Bloomday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Bloomday', 1.0),
    (4, 2, 'Bloomday', 1.0),
    (4, 3, 'Bloomday', 1.0),
    (4, 4, 'Bloomday', 1.0),

    -- ARCANADAY
    -- PREMIUM
    (1, 1, 'Arcanaday', 1.0),
    (1, 2, 'Arcanaday', 1.0),
    (1, 3, 'Arcanaday', 1.0),
    (1, 4, 'Arcanaday', 1.0),

    -- PENETRATION
    (2, 1, 'Arcanaday', 1.0), 
    (2, 2, 'Arcanaday', 1.0),
    (2, 3, 'Arcanaday', 1.0),
    (2, 4, 'Arcanaday', 1.0),

    -- TIERED
    (3, 1, 'Arcanaday', 1.0),
    (3, 2, 'Arcanaday', 1.0),
    (3, 3, 'Arcanaday', 1.0),
    (3, 4, 'Arcanaday', 1.0),
    
    -- DYNAMIC
    (4, 1, 'Arcanaday', 1.0),
    (4, 2, 'Arcanaday', 1.0),
    (4, 3, 'Arcanaday', 1.0),
    (4, 4, 'Arcanaday', 1.0);

-- Potion definitions with color mappings
INSERT INTO potions
(sku, name, red_ml, green_ml, blue_ml, dark_ml, base_price, color_id, current_quantity)
VALUES
-- Pure potions (single color)
('RED', 'Red', 100, 0, 0, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('GREEN', 'Green', 0, 100, 0, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('BLUE', 'Blue', 0, 0, 100, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),
('DARK', 'Dark Red', 0, 0, 0, 100, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),

-- Basic two-color combinations (50/50 splits)
('YELLOW', 'Yellow', 50, 50, 0, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('PURPLE', 'Purple', 50, 0, 50, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),
('TEAL', 'Teal', 0, 50, 50, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),

-- Basic three-color combination
('BROWN', 'Brown', 35, 35, 30, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),

-- Dark three-color combinations
('DARKER_YELLOW', 'Darker Yellow', 35, 35, 0, 30, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('DARKER_PURPLE', 'Darker Purple', 35, 0, 35, 30, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('DARKER_TEAL', 'Darker Teal', 0, 35, 35, 30, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),

-- Light dark combinations (75/25 splits)
('LIGHT_DARK_RED', 'Light Dark Red', 75, 0, 0, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('LIGHT_DARK_GREEN', 'Light Dark Green', 0, 75, 0, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('LIGHT_DARK_BLUE', 'Light Dark Blue', 0, 0, 75, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),

-- Even four-color split
('LIGHT_DARK_BROWN', 'Dark Brown', 25, 25, 25, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),

-- Dark combinations (50/50 splits)
('DARK_RED', 'Dark Red', 50, 0, 0, 50, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('DARK_GREEN', 'Dark Green', 0, 50, 0, 50, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('DARK_BLUE', 'Dark Blue', 0, 0, 50, 50, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),

-- Very dark combinations (25/75 splits)
('VERY_DARK_RED', 'Very Dark Red', 25, 0, 0, 75, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('VERY_DARK_GREEN', 'Very Dark Green', 0, 25, 0, 75, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('VERY_DARK_BLUE', 'Very Dark Blue', 0, 0, 25, 75, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),

-- Dark with two colors (25/25/50 splits)
('DARK_YELLOW', 'Dark Yellow', 25, 25, 0, 50, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('DARK_PURPLE', 'Dark Purple', 25, 0, 25, 50, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),
('DARK_TEAL', 'Dark Teal', 0, 25, 25, 50, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'DARK'), 0),

-- Two-color combinations (75/25 splits)
('ORANGE', 'Orange', 75, 25, 0, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('VIOLET', 'Violet', 75, 0, 25, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('YELLOW_GREEN', 'Yellow Green', 25, 75, 0, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('SEA_GREEN', 'Sea Green', 0, 75, 25, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('INDIGO', 'Indigo', 25, 0, 75, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),
('DEEP_TEAL', 'Deep Teal', 0, 25, 75, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),

-- Three-color combinations
('RUSSET', 'Russet', 50, 25, 25, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('OLIVE', 'Olive', 25, 50, 25, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('STEEL_BLUE', 'Steel Blue', 25, 25, 50, 0, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),

-- Light dark combinations
('LIGHT_DARK_ORANGE', 'Light Dark Orange', 50, 25, 0, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('LIGHT_DARK_VIOLET', 'Light Dark Violet', 50, 0, 25, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'RED'), 0),
('LIGHT_DARK_OLIVE', 'Light Dark Olive', 25, 50, 0, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('LIGHT_DARK_TEAL', 'Light Dark Teal', 0, 50, 25, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'GREEN'), 0),
('LIGHT_DARK_INDIGO', 'Light Dark Indigo', 25, 0, 50, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0),
('SHADOWED_TEAL', 'Shadowed Teal', 0, 25, 50, 25, 50, (SELECT color_id FROM color_definitions WHERE color_name = 'BLUE'), 0);

-- Capacity upgrade definitions
INSERT INTO capacity_upgrade_thresholds
(min_potion_units, max_potion_units, min_ml_units, max_ml_units, 
 gold_threshold, secondary_gold_threshold, capacity_check_threshold,
 ml_capacity_purchase, potion_capacity_purchase, priority_order, requires_inventory_check)
VALUES
-- First tier (1-1 units)
(1, 1, 1, 1, 2800, NULL, NULL, 1, 1, 100, false),
(1, 1, 1, 1, 2000, NULL, 0.5, 1, 1, 90, true),

-- Second tier (2-4 units)
(2, 4, 2, 4, 5550, NULL, NULL, 2, 2, 80, false),
(2, 4, 2, 4, 3550, NULL, 0.5, 2, 2, 70, true),
(2, 4, 2, 4, 3550, NULL, NULL, 1, 1, 60, false),
(2, 4, 2, 4, 2000, NULL, 0.5, 1, 1, 50, true),

-- Third tier (4+ units) 
(4, NULL, 4, NULL, 6250, NULL, 0.6, 1, 1, 40, true),
(4, NULL, 4, NULL, 6250, NULL, 0.6, 1, 0, 30, true),
(4, NULL, 4, NULL, 6250, NULL, 0.6, 0, 1, 20, true);