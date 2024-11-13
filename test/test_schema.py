import pytest
import sqlalchemy
import logging
from pathlib import Path
from test.sqlite_setup import create_test_db

class TestSchema:
    """Test database schema implementation"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_logger):
        """Setup test database and logging"""
        self.engine = create_test_db()
        self.logger = test_logger
        
        yield
    
    def test_table_existence(self):
        """Verify all required tables are created"""
        self.logger.info("Testing table existence")
        
        with self.engine.begin() as conn:
            tables = conn.execute(sqlalchemy.text("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name;
            """)).scalars().all()
            
            expected_tables = {
                'active_strategy', 'barrel_details', 'barrel_purchases',
                'barrel_visits', 'block_potion_priorities',
                'capacity_upgrade_thresholds', 'cart_items', 'carts',
                'color_definitions', 'current_game_time', 'customer_visits',
                'customers', 'game_time', 'ledger_entries', 'potions',
                'strategies', 'strategy_time_blocks', 'strategy_transitions',
                'time_blocks'
            }
            
            actual_tables = set(table for table in tables if table != 'sqlite_sequence')
            missing_tables = expected_tables - actual_tables
            extra_tables = actual_tables - expected_tables
            
            self.logger.info(f"Expected tables: {len(expected_tables)}")
            self.logger.info(f"Actual tables: {len(actual_tables)}")
            
            if missing_tables:
                self.logger.error(f"Missing tables: {missing_tables}")
            if extra_tables:
                self.logger.warning(f"Extra tables: {extra_tables}")
                
            assert not missing_tables, f"Missing tables: {missing_tables}"
            assert not extra_tables, f"Unexpected tables: {extra_tables}"
    
    def test_initial_data_setup(self):
        """Verify initial data is properly loaded"""
        self.logger.info("Testing initial data setup")
        
        with self.engine.begin() as conn:
            # Test color definitions
            colors = conn.execute(sqlalchemy.text("""
                SELECT color_name, priority_order 
                FROM color_definitions 
                ORDER BY priority_order;
            """)).mappings().all()
            
            self.logger.info("Color definitions:")
            for color in colors:
                self.logger.info(f"  {color['color_name']}: priority {color['priority_order']}")
            
            assert len(colors) == 4, "Should have exactly 4 colors"
            
            # Test strategies
            strategies = conn.execute(sqlalchemy.text("""
                SELECT name, ml_capacity_units, potion_capacity_units, max_potions_per_sku
                FROM strategies 
                ORDER BY strategy_id;
            """)).mappings().all()
            
            self.logger.info("Strategy configurations:")
            for strategy in strategies:
                self.logger.info(
                    f"  {strategy['name']}: "
                    f"ML units={strategy['ml_capacity_units']}, "
                    f"Potion units={strategy['potion_capacity_units']}, "
                    f"Max per SKU={strategy['max_potions_per_sku']}"
                )
            
            assert len(strategies) == 4, "Should have exactly 4 strategies"
            
            # Test time blocks
            time_blocks = conn.execute(sqlalchemy.text("""
                SELECT name, start_hour, end_hour 
                FROM time_blocks 
                ORDER BY start_hour;
            """)).mappings().all()
            
            self.logger.info("Time blocks:")
            for block in time_blocks:
                self.logger.info(
                    f"  {block['name']}: "
                    f"{block['start_hour']:02d}:00-{block['end_hour']:02d}:00"
                )
            
            assert len(time_blocks) == 4, "Should have exactly 4 time blocks"
    
    def test_game_time_setup(self):
        """Test game time configuration and relationships"""
        self.logger.info("Testing game time setup")
        
        with self.engine.begin() as conn:
            # Test days setup
            days = conn.execute(sqlalchemy.text("""
                SELECT DISTINCT in_game_day 
                FROM game_time 
                ORDER BY time_id;
            """)).scalars().all()
            
            expected_days = [
                'Hearthday', 'Crownday', 'Blesseday', 'Soulday',
                'Edgeday', 'Bloomday', 'Arcanaday'
            ]
            
            self.logger.info("Game days configuration:")
            for day in days:
                self.logger.info(f"  {day}")
            
            assert days == expected_days, "Game days not properly configured"
            
            # Test hours setup
            hours = conn.execute(sqlalchemy.text("""
                SELECT DISTINCT in_game_hour 
                FROM game_time 
                ORDER BY in_game_hour;
            """)).scalars().all()
            
            expected_hours = list(range(0, 23, 2))
            
            self.logger.info("Game hours configuration:")
            self.logger.info(f"  Hours: {hours}")
            
            assert hours == expected_hours, "Game hours not properly configured"
            
            # Test time references
            references = conn.execute(sqlalchemy.text("""
                SELECT time_id, bottling_time_id, barrel_time_id
                FROM game_time
                ORDER BY time_id
                LIMIT 5;
            """)).mappings().all()
            
            self.logger.info("Time references sample:")
            for ref in references:
                self.logger.info(
                    f"  Time {ref['time_id']}: "
                    f"Bottling={ref['bottling_time_id']}, "
                    f"Barrel={ref['barrel_time_id']}"
                )
            
            # Verify references are valid
            for ref in references:
                assert ref['bottling_time_id'] is not None, "Missing bottling reference"
                assert ref['barrel_time_id'] is not None, "Missing barrel reference"
    
    def test_constraints(self):
        """Test table constraints and validations"""
        self.logger.info("Testing database constraints")
        
        with self.engine.begin() as conn:
            # Test color constraints
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO color_definitions (color_name, priority_order)
                    VALUES ('INVALID', 5);
                """))
            self.logger.info("Color constraint test passed")
            
            # Test barrel constraints
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO barrel_details (
                        visit_id, sku, ml_per_barrel, potion_type,
                        price, quantity, color_id
                    ) VALUES (
                        1, 'INVALID_BARREL', 500,
                        '[1,0,0,0]', 100, 1, 1
                    );
                """))
            self.logger.info("Barrel SKU constraint test passed")
            
            # Test game time constraints
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO game_time (
                        in_game_day, in_game_hour,
                        bottling_time_id, barrel_time_id
                    ) VALUES (
                        'InvalidDay', 1, 1, 1
                    );
                """))
            self.logger.info("Game time day constraint test passed")
            
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO game_time (
                        in_game_day, in_game_hour,
                        bottling_time_id, barrel_time_id
                    ) VALUES (
                        'Hearthday', 3, 1, 1
                    );
                """))
            self.logger.info("Game time hour constraint test passed")
    
    def test_potion_system(self):
        """Test potion system setup and constraints"""
        self.logger.info("Testing potion system")
        
        with self.engine.begin() as conn:
            # Test potion types
            potions = conn.execute(sqlalchemy.text("""
                SELECT sku, red_ml, green_ml, blue_ml, dark_ml, base_price
                FROM potions
                ORDER BY sku;
            """)).mappings().all()
            
            self.logger.info("Potion configurations sample:")
            for potion in potions[:5]:  # Show first 5 potions
                self.logger.info(
                    f"  {potion['sku']}: "
                    f"R={potion['red_ml']} "
                    f"G={potion['green_ml']} "
                    f"B={potion['blue_ml']} "
                    f"D={potion['dark_ml']} "
                    f"Price={potion['base_price']}"
                )
            
            # Verify ML total constraint
            for potion in potions:
                total_ml = (potion['red_ml'] + potion['green_ml'] + 
                           potion['blue_ml'] + potion['dark_ml'])
                assert total_ml == 100, f"Invalid ML total for {potion['sku']}"
            
            self.logger.info(f"Verified ML constraints for {len(potions)} potions")
            
            # Test potion-color relationships
            relationships = conn.execute(sqlalchemy.text("""
                SELECT p.sku, cd.color_name
                FROM potions p
                JOIN color_definitions cd ON p.color_id = cd.color_id
                ORDER BY p.sku
                LIMIT 5;
            """)).mappings().all()
            
            self.logger.info("Potion-color relationships sample:")
            for rel in relationships:
                self.logger.info(f"  {rel['sku']}: {rel['color_name']}")
    
    def test_capacity_system(self):
        """Test capacity upgrade system configuration"""
        self.logger.info("Testing capacity upgrade system")
        
        with self.engine.begin() as conn:
            thresholds = conn.execute(sqlalchemy.text("""
                SELECT 
                    min_potion_units,
                    max_potion_units,
                    min_ml_units,
                    max_ml_units,
                    gold_threshold,
                    capacity_check_threshold,
                    requires_inventory_check
                FROM capacity_upgrade_thresholds
                ORDER BY priority_order DESC;
            """)).mappings().all()
            
            self.logger.info("Capacity upgrade thresholds:")
            for threshold in thresholds:
                self.logger.info(
                    f"  Potion: {threshold['min_potion_units']}-"
                    f"{threshold['max_potion_units'] or 'MAX'}, "
                    f"ML: {threshold['min_ml_units']}-"
                    f"{threshold['max_ml_units'] or 'MAX'}, "
                    f"Gold: {threshold['gold_threshold']}"
                )
            
            assert len(thresholds) > 0, "No capacity upgrade thresholds defined"
            
            # Verify threshold relationships
            for threshold in thresholds:
                if threshold['max_potion_units']:
                    assert threshold['min_potion_units'] <= threshold['max_potion_units'], \
                        "Invalid potion unit range"
                if threshold['max_ml_units']:
                    assert threshold['min_ml_units'] <= threshold['max_ml_units'], \
                        "Invalid ML unit range"
    
    def test_ledger_system(self):
        """Test ledger system setup and initial state"""
        self.logger.info("Testing ledger system")
        
        with self.engine.begin() as conn:
            # Check initial ledger entry
            initial_entry = conn.execute(sqlalchemy.text("""
                SELECT 
                    entry_type,
                    gold_change,
                    ml_capacity_change,
                    potion_capacity_change
                FROM ledger_entries
                WHERE entry_type = 'ADMIN_CHANGE'
                ORDER BY entry_id
                LIMIT 1;
            """)).mappings().one()
            
            self.logger.info("Initial ledger entry:")
            self.logger.info(
                f"  Type: {initial_entry['entry_type']}, "
                f"Gold: {initial_entry['gold_change']}, "
                f"ML Capacity: {initial_entry['ml_capacity_change']}, "
                f"Potion Capacity: {initial_entry['potion_capacity_change']}"
            )
            
            assert initial_entry['gold_change'] == 100, "Wrong initial gold"
            assert initial_entry['ml_capacity_change'] == 1, "Wrong initial ML capacity"
            assert initial_entry['potion_capacity_change'] == 1, "Wrong initial potion capacity"
            
            # Verify ledger entry types
            valid_types = {
                'BARREL_PURCHASE', 'POTION_BOTTLED', 'POTION_SOLD',
                'ML_CAPACITY_UPGRADE', 'POTION_CAPACITY_UPGRADE',
                'GOLD_CHANGE', 'ML_ADJUSTMENT', 'ADMIN_CHANGE'
            }
            
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO ledger_entries (
                        time_id, entry_type, gold_change
                    ) VALUES (
                        1, 'INVALID_TYPE', 100
                    );
                """))
            self.logger.info("Ledger entry type constraint test passed")

    def test_strategy_transitions(self):
        """Test strategy transition rules and constraints"""
        self.logger.info("Testing strategy transition system")
        
        with self.engine.begin() as conn:
            # Test transition rules
            transitions = conn.execute(sqlalchemy.text("""
                SELECT 
                    s1.name as from_strategy,
                    s2.name as to_strategy,
                    st.gold_threshold,
                    st.potion_threshold,
                    st.ml_threshold,
                    st.ml_capacity_threshold,
                    st.potion_capacity_threshold,
                    st.require_all_thresholds
                FROM strategy_transitions st
                JOIN strategies s1 ON st.from_strategy_id = s1.strategy_id
                JOIN strategies s2 ON st.to_strategy_id = s2.strategy_id
                ORDER BY s1.strategy_id, s2.strategy_id;
            """)).mappings().all()
            
            self.logger.info("Strategy transition rules:")
            for transition in transitions:
                self.logger.info(
                    f"  {transition['from_strategy']} -> {transition['to_strategy']}:"
                    f"\n    Gold: {transition['gold_threshold']}"
                    f"\n    Potion: {transition['potion_threshold']}"
                    f"\n    ML: {transition['ml_threshold']}"
                    f"\n    ML Capacity: {transition['ml_capacity_threshold']}"
                    f"\n    Potion Capacity: {transition['potion_capacity_threshold']}"
                    f"\n    Require All: {transition['require_all_thresholds']}"
                )
            
            # Verify PREMIUM to PENETRATION transition
            premium_trans = next(t for t in transitions 
                               if t['from_strategy'] == 'PREMIUM')
            assert premium_trans['to_strategy'] == 'PENETRATION'
            assert premium_trans['gold_threshold'] == 250
            assert premium_trans['potion_threshold'] == 5
            assert premium_trans['ml_threshold'] == 500
            
            # Verify no backwards transitions
            strategy_order = ['PREMIUM', 'PENETRATION', 'TIERED', 'DYNAMIC']
            for i, from_strategy in enumerate(strategy_order[:-1]):
                for to_strategy in strategy_order[:i+1]:
                    invalid_transition = next(
                        (t for t in transitions 
                         if t['from_strategy'] == from_strategy 
                         and t['to_strategy'] == to_strategy), 
                        None
                    )
                    assert invalid_transition is None, \
                        f"Invalid backward transition: {from_strategy} -> {to_strategy}"
            
            self.logger.info("Strategy transition rules validated")
    
    def test_cart_system(self):
        """Test cart system constraints and relationships"""
        self.logger.info("Testing cart system")
        
        with self.engine.begin() as conn:
            # Test cart state constraints
            self.logger.info("Testing cart state constraints")
            
            # Insert test customer visit
            conn.execute(sqlalchemy.text("""
                INSERT INTO customer_visits (
                    visit_id, time_id, customers
                ) VALUES (
                    1, 1, '[]'
                );
            """))
            
            # Insert test customer
            conn.execute(sqlalchemy.text("""
                INSERT INTO customers (
                    visit_record_id, visit_id, time_id,
                    customer_name, character_class, level
                ) VALUES (
                    1, 1, 1, 'TestCustomer', 'Warrior', 1
                );
            """))
            
            # Test cart creation
            conn.execute(sqlalchemy.text("""
                INSERT INTO carts (
                    customer_id, visit_id, time_id,
                    checked_out, total_potions, total_gold
                ) VALUES (
                    1, 1, 1, false, 0, 0
                );
            """))
            
            # Verify cart constraints
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO cart_items (
                        cart_id, visit_id, potion_id, time_id,
                        quantity, unit_price, line_total
                    ) VALUES (
                        1, 1, 1, 1, -1, 50, -50
                    );
                """))
            self.logger.info("Cart quantity constraint test passed")
            
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO cart_items (
                        cart_id, visit_id, potion_id, time_id,
                        quantity, unit_price, line_total
                    ) VALUES (
                        1, 1, 1, 1, 1, -50, -50
                    );
                """))
            self.logger.info("Cart price constraint test passed")
            
            # Test cart checkout constraints
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    UPDATE carts 
                    SET checked_out = true
                    WHERE cart_id = 1;
                """))
            self.logger.info("Cart checkout constraint test passed")
    
    def test_time_block_relationships(self):
        """Test time block relationships and strategy effects"""
        self.logger.info("Testing time block relationships")
        
        with self.engine.begin() as conn:
            # Test strategy time blocks
            blocks = conn.execute(sqlalchemy.text("""
                SELECT 
                    s.name as strategy_name,
                    tb.name as time_block,
                    stb.day_name,
                    stb.buffer_multiplier,
                    stb.dark_buffer_multiplier
                FROM strategy_time_blocks stb
                JOIN strategies s ON stb.strategy_id = s.strategy_id
                JOIN time_blocks tb ON stb.time_block_id = tb.block_id
                ORDER BY s.strategy_id, stb.day_name, tb.start_hour;
            """)).mappings().all()
            
            self.logger.info("Strategy time block configurations sample:")
            day_sample = 'Hearthday'
            sample_blocks = [b for b in blocks if b['day_name'] == day_sample]
            for block in sample_blocks:
                self.logger.info(
                    f"  {block['strategy_name']} - {block['time_block']}:"
                    f"\n    Buffer: {block['buffer_multiplier']}"
                    f"\n    Dark Buffer: {block['dark_buffer_multiplier']}"
                )
            
            # Verify special day configurations
            special_days = ['Hearthday', 'Blesseday', 'Bloomday']
            for day in special_days:
                day_blocks = [b for b in blocks if b['day_name'] == day]
                evening_blocks = [b for b in day_blocks 
                                if b['time_block'] == 'EVENING']
                
                for block in evening_blocks:
                    if block['strategy_name'] in ['TIERED', 'DYNAMIC']:
                        assert block['dark_buffer_multiplier'] > 1.0, \
                            f"Invalid dark buffer for {day} evening"
            
            self.logger.info("Special day configurations validated")
    
    def test_barrel_system(self):
        """Test barrel system constraints and relationships"""
        self.logger.info("Testing barrel system")
        
        with self.engine.begin() as conn:
            # Insert test visit
            conn.execute(sqlalchemy.text("""
                INSERT INTO barrel_visits (
                    time_id, wholesale_catalog
                ) VALUES (
                    1, '[]'
                );
            """))
            
            # Test valid barrel sizes
            sizes = ['SMALL', 'MEDIUM', 'LARGE']
            colors = ['RED', 'GREEN', 'BLUE', 'DARK']
            
            self.logger.info("Testing barrel size constraints:")
            for size in sizes:
                for color in colors:
                    sku = f"{size}_{color}_BARREL"
                    ml = {
                        'SMALL': 500,
                        'MEDIUM': 2500,
                        'LARGE': 10000
                    }[size]
                    
                    self.logger.info(f"  Testing {sku} with {ml}ml")
                    
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO barrel_details (
                            visit_id, sku, ml_per_barrel, potion_type,
                            price, quantity, color_id
                        ) VALUES (
                            1, :sku, :ml, '[1,0,0,0]', 100, 1,
                            (SELECT color_id FROM color_definitions 
                             WHERE color_name = :color)
                        );
                    """), {
                        "sku": sku,
                        "ml": ml,
                        "color": color
                    })
            
            # Test invalid barrel configurations
            self.logger.info("Testing invalid barrel configurations")
            
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO barrel_details (
                        visit_id, sku, ml_per_barrel, potion_type,
                        price, quantity, color_id
                    ) VALUES (
                        1, 'SMALL_RED_BARREL', 1000, '[1,0,0,0]',
                        100, 1, 1
                    );
                """))
            self.logger.info("Invalid ml per barrel test passed")
            
            # Test barrel purchase constraints
            self.logger.info("Testing barrel purchase constraints")
            
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO barrel_purchases (
                        visit_id, barrel_id, time_id,
                        quantity, total_cost, ml_added, color_id
                    ) VALUES (
                        1, 1, 1, -1, 100, 500, 1
                    );
                """))
            self.logger.info("Negative quantity test passed")
            
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO barrel_purchases (
                        visit_id, barrel_id, time_id,
                        quantity, total_cost, ml_added, color_id
                    ) VALUES (
                        1, 1, 1, 1, -100, 500, 1
                    );
                """))
            self.logger.info("Negative cost test passed")
    
    def test_potion_mixing_view(self):
        """Test potion mixing constraints and current_state view"""
        self.logger.info("Testing potion mixing and state view")
        
        with self.engine.begin() as conn:
            # Insert test ledger entries
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, gold_change, 
                    ml_change, color_id, potion_change
                ) VALUES
                (1, 'BARREL_PURCHASE', -100, 1000, 1, NULL),
                (1, 'BARREL_PURCHASE', -100, 1000, 2, NULL),
                (1, 'POTION_BOTTLED', NULL, -100, 1, 1),
                (1, 'POTION_SOLD', 50, NULL, NULL, -1);
            """))
            
            # Test current_state view
            state = conn.execute(sqlalchemy.text("""
                SELECT 
                    gold, red_ml, green_ml, blue_ml, dark_ml,
                    total_potions, potion_capacity_units, ml_capacity_units,
                    total_ml, max_potions, max_ml, strategy_id
                FROM current_state;
            """)).mappings().one()
            
            self.logger.info("Current state:")
            self.logger.info(
                f"  Gold: {state['gold']}"
                f"\n  ML: Red={state['red_ml']}, Green={state['green_ml']}, "
                f"Blue={state['blue_ml']}, Dark={state['dark_ml']}"
                f"\n  Total ML: {state['total_ml']}/{state['max_ml']}"
                f"\n  Potions: {state['total_potions']}/{state['max_potions']}"
                f"\n  Strategy: {state['strategy_id']}"
            )
            
            # Verify view calculations
            assert state['total_ml'] == state['red_ml'] + state['green_ml'] + \
                state['blue_ml'] + state['dark_ml'], "Invalid total ML"
            assert state['max_potions'] == state['potion_capacity_units'] * 50, \
                "Invalid max potions"
            assert state['max_ml'] == state['ml_capacity_units'] * 10000, \
                "Invalid max ML"
            
            self.logger.info("State view calculations validated")
    
    def test_foreign_key_relationships(self):
        """Test foreign key relationships and cascade behaviors"""
        self.logger.info("Testing foreign key relationships")
        
        with self.engine.begin() as conn:
            # Test strategy references
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO active_strategy (
                        strategy_id, game_time_id
                    ) VALUES (
                        999, 1
                    );
                """))
            self.logger.info("Invalid strategy reference test passed")
            
            # Test color references
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO potions (
                        sku, name, red_ml, green_ml, blue_ml, dark_ml,
                        base_price, color_id
                    ) VALUES (
                        'TEST', 'Test', 100, 0, 0, 0, 50, 999
                    );
                """))
            self.logger.info("Invalid color reference test passed")
            
            # Test game time references
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO current_game_time (
                        game_time_id, current_day, current_hour
                    ) VALUES (
                        999, 'Hearthday', 0
                    );
                """))
            self.logger.info("Invalid game time reference test passed")
            
            # Test cart references
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO cart_items (
                        cart_id, visit_id, potion_id, time_id,
                        quantity, unit_price, line_total
                    ) VALUES (
                        999, 1, 1, 1, 1, 50, 50
                    );
                """))
            self.logger.info("Invalid cart reference test passed")
    
    def test_unique_constraints(self):
        """Test unique constraints across tables"""
        self.logger.info("Testing unique constraints")
        
        with self.engine.begin() as conn:
            # Test color name uniqueness
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO color_definitions (
                        color_name, priority_order
                    ) VALUES (
                        'RED', 10
                    );
                """))
            self.logger.info("Color name uniqueness test passed")
            
            # Test potion SKU uniqueness
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO potions (
                        sku, name, red_ml, green_ml, blue_ml, dark_ml,
                        base_price, color_id
                    ) VALUES (
                        'RED', 'Test Red', 100, 0, 0, 0, 50, 1
                    );
                """))
            self.logger.info("Potion SKU uniqueness test passed")
            
            # Test strategy name uniqueness
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO strategies (
                        name, ml_capacity_units, potion_capacity_units,
                        max_potions_per_sku
                    ) VALUES (
                        'PREMIUM', 1, 1, 20
                    );
                """))
            self.logger.info("Strategy name uniqueness test passed")
            
            # Test time block name uniqueness
            with pytest.raises(Exception) as exc_info:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO time_blocks (
                        name, start_hour, end_hour
                    ) VALUES (
                        'NIGHT', 0, 4
                    );
                """))
            self.logger.info("Time block name uniqueness test passed")