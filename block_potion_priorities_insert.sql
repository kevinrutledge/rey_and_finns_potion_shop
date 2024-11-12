WITH strategy_blocks AS (
    SELECT 
        stb.block_id,
        s.name as strategy_name,
        tb.name as time_block,
        stb.day_name
    FROM strategy_time_blocks stb
    JOIN strategies s ON s.strategy_id = stb.strategy_id
    JOIN time_blocks tb ON tb.block_id = stb.time_block_id
)
INSERT INTO block_potion_priorities (block_id, potion_id, sales_mix, priority_order)
VALUES
-- HEARTHDAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.30, 2),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

 -- HEARTHDAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- HEARTHDAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- HEARTHDAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Hearthday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- CROWNDAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.30, 2),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- CROWNDAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- CROWNDAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- CROWNDAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Crownday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- BLESSEDAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.30, 2),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- BLESSEDAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),

-- BLESSEDAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.05, 6),


-- BLESSEDAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Blesseday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 6),


-- SOULDAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.30, 2),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.05, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.05, 6),

-- SOULDAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- SOULDAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_PURPLE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),


-- SOULDAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.70, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.50, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.05, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.35, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK_BLUE'), 0.10, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Soulday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.10, 6),

-- EDGEDAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

 -- EDGEDAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- EDGEDAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- EDGEDAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.30, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'BLUE'), 0.15, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Edgeday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 5),

-- BLOOMDAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.10, 4),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.40, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.40, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.10, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.10, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- BLOOMDAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.20, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.25, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.25, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- BLOOMDAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.20, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.25, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.25, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- BLOOMDAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.20, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.20, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.20, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RED'), 0.20, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'OLIVE'), 0.20, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.20, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.20, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Bloomday'),
(SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- ARCANADAY NIGHT
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'NIGHT' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- ARCANADAY MORNING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'MORNING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 6),

-- ARCANADAY AFTERNOON
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration  
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.05, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.15, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'AFTERNOON' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- ARCANADAY EVENING
-- Premium
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PREMIUM' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 1.00, 1),

-- Penetration
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.60, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.30, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'PENETRATION' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.10, 3),

-- Tiered
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'TIERED' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6),

-- Dynamic
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'DARK'), 0.15, 1),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'GREEN'), 0.35, 2),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RED'), 0.25, 3),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'YELLOW'), 0.15, 4),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'VIOLET'), 0.05, 5),
((SELECT block_id FROM strategy_blocks WHERE strategy_name = 'DYNAMIC' AND time_block = 'EVENING' AND day_name = 'Arcanaday'),
 (SELECT potion_id FROM potions WHERE sku = 'RUSSET'), 0.05, 6);