import os
import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from src.api.server import app
from src.api.barrels import Barrel, BarrelPurchase
from src.api.auth import api_keys
from test.sqlite_setup import create_test_db

class TestBarrelDiagnostic:
    """Diagnostic tests for barrel system failures"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_logger):
        """Enhanced setup for diagnostic testing"""
        self.engine = create_test_db()
        self.client = TestClient(app)
        self.logger = test_logger
        
        # Verify testing environment
        self.logger.info(f"Testing environment: {os.environ.get('TESTING')}")
        self.logger.info(f"Database engine: {self.engine.url}")
        
        # Setup auth
        test_api_key = "test_api_key"
        api_keys.append(test_api_key)
        self.headers = {"access_token": test_api_key}
        
        yield
        
        if test_api_key in api_keys:
            api_keys.remove(test_api_key)

    def test_database_setup(self):
        """Verify database initialization"""
        with self.engine.begin() as conn:
            # Check tables exist
            tables = conn.execute(sqlalchemy.text("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)).scalars().all()
            
            self.logger.info(f"Available tables: {tables}")
            
            # Verify initial data
            strategies = conn.execute(sqlalchemy.text("""
                SELECT name FROM strategies
            """)).scalars().all()
            
            self.logger.info(f"Available strategies: {strategies}")
            
            assert 'PREMIUM' in strategies, "Basic strategy data missing"

    def test_basic_barrel_flow(self):
        """Test basic barrel purchase flow with detailed logging"""
        # Create minimal test catalog
        catalog = [Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=500,
            potion_type=[1,0,0,0],
            price=100,
            quantity=1
        )]

        # Log initial state
        with self.engine.begin() as conn:
            current_time = conn.execute(sqlalchemy.text("""
                SELECT cgt.*, gt.* 
                FROM current_game_time cgt
                JOIN game_time gt ON cgt.game_time_id = gt.time_id
            """)).mappings().all()
            self.logger.info(f"Initial game time state: {current_time}")
            
            strategies = conn.execute(sqlalchemy.text("""
                SELECT * FROM active_strategy
            """)).mappings().all()
            self.logger.info(f"Active strategies: {strategies}")
        
        # Test catalog endpoint
        self.logger.info("Testing barrel plan endpoint")
        try:
            response = self.client.post(
                "/barrels/plan",
                json=[b.dict() for b in catalog],
                headers=self.headers
            )

            self.logger.info(f"Plan response status: {response.status_code}")
            if response.status_code != 200:
                self.logger.error(f"Plan response error: {response.json()}")
                with self.engine.begin() as conn:
                    state = conn.execute(sqlalchemy.text(
                        "SELECT * FROM current_state"
                    )).mappings().one()
                    self.logger.error(f"Database state during error: {dict(state)}")

            self.logger.info(f"Plan response status: {response.status_code}")
            self.logger.info(f"Plan response body: {response.json()}")
            
            assert response.status_code == 200, f"Unexpected status: {response.status_code}"
            
        except Exception as e:
            self.logger.error(f"Plan endpoint failed: {str(e)}")
            raise

        # Test delivery endpoint
        self.logger.info("Testing barrel delivery endpoint")
        try:
            delivery_response = self.client.post(
                "/barrels/deliver/1",
                json=[catalog[0].dict()],
                headers=self.headers
            )
            self.logger.info(f"Delivery response status: {delivery_response.status_code}")
            self.logger.info(f"Delivery response body: {delivery_response.json()}")
            
            assert delivery_response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Delivery endpoint failed: {str(e)}")
            raise

    def test_transaction_state(self):
        """Verify transaction handling and state management"""
        with self.engine.begin() as conn:
            # Check initial state
            state = conn.execute(sqlalchemy.text("""
                SELECT * FROM current_state
            """)).mappings().one()
            
            self.logger.info(f"Initial state: {dict(state)}")
            
            # Attempt basic transaction
            try:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO barrel_visits (
                        time_id, wholesale_catalog
                    ) VALUES (
                        1, '[]'
                    )
                """))
                
                self.logger.info("Basic transaction succeeded")
                
            except Exception as e:
                self.logger.error(f"Transaction failed: {str(e)}")
                raise

    def verify_state_after_purchase(self):
        """Verify database state after purchase"""
        with self.engine.begin() as conn:
            ledger = conn.execute(sqlalchemy.text("""
                SELECT entry_type, gold_change, ml_change
                FROM ledger_entries
                ORDER BY entry_id DESC
                LIMIT 1
            """)).mappings().one()
            
            self.logger.info(f"Latest ledger entry: {dict(ledger)}")
            
            return ledger

class TestBarrels:
    """Test barrel endpoint functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_logger):
        """Setup test database and client for barrel endpoint testing."""
        self.engine = create_test_db()
        self.client = TestClient(app)
        self.logger = test_logger
        
        # Setup auth
        test_api_key = "test_api_key"
        api_keys.append(test_api_key)
        self.headers = {"access_token": test_api_key}

        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text(
                "INSERT INTO current_game_time (game_time_id, current_day, current_hour) VALUES (1, 'Hearthday', 0)"
            ))
        
        yield
        
        # Cleanup
        if test_api_key in api_keys:
            api_keys.remove(test_api_key)

    def create_test_barrel(self, size: str, color: str, quantity: int = 1, price: int = 100) -> Barrel:
        """Create test barrel with valid configuration"""
        ml_sizes = {
            'SMALL': 500,
            'MEDIUM': 2500,
            'LARGE': 10000
        }
        
        color_types = {
            'RED': [1,0,0,0],
            'GREEN': [0,1,0,0],
            'BLUE': [0,0,1,0],
            'DARK': [0,0,0,1]
        }
        
        if size not in ml_sizes or color not in color_types:
            raise ValueError(f"Invalid size {size} or color {color}")
        
        return Barrel(
            sku=f"{size}_{color}_BARREL",
            ml_per_barrel=ml_sizes[size],
            potion_type=color_types[color],
            price=price,
            quantity=quantity
        )
    
    def setup_strategy(self, strategy_name: str):
        """Helper to transition to desired strategy"""
        with self.engine.begin() as conn:
            if strategy_name == 'PENETRATION':
                # Add gold to meet threshold
                conn.execute(sqlalchemy.text("""
                    INSERT INTO ledger_entries (
                        time_id, entry_type, gold_change
                    ) VALUES (
                        1, 'GOLD_CHANGE', 250
                    );
                """))
            elif strategy_name in ['TIERED', 'DYNAMIC']:
                # Add capacity to meet threshold
                conn.execute(sqlalchemy.text("""
                    INSERT INTO ledger_entries (
                        time_id, entry_type, 
                        ml_capacity_change, potion_capacity_change
                    ) VALUES (
                        1, 'ML_CAPACITY_UPGRADE', 2, 2
                    );
                """))
            
            # Set strategy
            conn.execute(sqlalchemy.text("""
                INSERT INTO active_strategy (strategy_id, game_time_id)
                VALUES (
                    (SELECT strategy_id FROM strategies WHERE name = :strategy),
                    1
                );
            """), {"strategy": strategy_name})
    
    def set_game_time(self, day: str, hour: int):
        """Helper to set game time"""
        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO current_game_time (game_time_id, current_day, current_hour)
                VALUES (
                    (SELECT time_id FROM game_time 
                    WHERE in_game_day = :day AND in_game_hour = :hour),
                    :day,
                    :hour
                );
            """), {"day": day, "hour": hour})

    def test_premium_barrel_strategy(self):
        """Test PREMIUM strategy barrel purchasing rules"""
        # Verify initial state
        with self.engine.begin() as conn:
            strategy = conn.execute(sqlalchemy.text("""
                SELECT s.name
                FROM active_strategy ast
                JOIN strategies s ON ast.strategy_id = s.strategy_id
                ORDER BY ast.activated_at DESC
                LIMIT 1
            """)).scalar_one()
            self.logger.info(f"Current strategy: {strategy}")
            
            state = conn.execute(sqlalchemy.text(
                "SELECT * FROM current_state"
            )).mappings().one()
            self.logger.info(f"Initial state: {dict(state)}")
        
        # Create catalog with all sizes
        catalog = [
            self.create_test_barrel('SMALL', 'RED', quantity=2),
            self.create_test_barrel('MEDIUM', 'RED', quantity=2),
            self.create_test_barrel('LARGE', 'RED', quantity=2),
            self.create_test_barrel('SMALL', 'DARK', quantity=2)
        ]
        
        self.logger.info(f"Input catalog: {[b.dict() for b in catalog]}")
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        self.logger.info(f"Response: {response.json()}")

    def test_tiered_dark_barrel_purchases(self):
        """Test TIERED strategy dark barrel purchases"""
        self.setup_strategy('TIERED')
        
        special_days = [
            ('Hearthday', 2.0),
            ('Blesseday', 3.0),
            ('Bloomday', 2.0)
        ]
        
        for day, multiplier in special_days:
            self.logger.info(f"\nTesting {day} with multiplier {multiplier}")
            self.set_game_time(day, 22)
            
            # Debug time blocks
            with self.engine.begin() as conn:
                time_blocks = conn.execute(sqlalchemy.text("""
                    SELECT gt.in_game_day, gt.in_game_hour, 
                        tb.name as block_name, 
                        stb.buffer_multiplier, 
                        stb.dark_buffer_multiplier,
                        s.name as strategy_name
                    FROM game_time gt
                    JOIN time_blocks tb 
                        ON gt.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
                    JOIN strategy_time_blocks stb 
                        ON tb.block_id = stb.time_block_id
                    JOIN strategies s ON stb.strategy_id = s.strategy_id
                    WHERE gt.in_game_day = :day 
                    AND gt.in_game_hour = 22
                """), {"day": day}).mappings().all()
                self.logger.info(f"Found time blocks: {[dict(b) for b in time_blocks]}")

    def test_barrel_purchase_plan_premium(self):
        """Test PREMIUM strategy only buys SMALL barrels"""
        self.logger.info("Testing PREMIUM strategy barrel purchases")
        
        # Create test catalog with only SMALL barrels - PREMIUM shouldn't see others
        catalog = [
            self.create_test_barrel('SMALL', 'RED'),
            self.create_test_barrel('SMALL', 'GREEN'),
            self.create_test_barrel('SMALL', 'BLUE')
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        
        # Verify only SMALL barrels purchased
        for purchase in purchases:
            assert "SMALL" in purchase.sku, "PREMIUM strategy bought non-SMALL barrel"
            assert "DARK" not in purchase.sku, "PREMIUM strategy bought DARK barrel"
            
        self.logger.info(f"PREMIUM strategy purchases: {response.json()}")

    @pytest.mark.parametrize("special_day,buffer_multiplier", [
        ("Hearthday", 2.0),
        ("Blesseday", 3.0),
        ("Bloomday", 2.0)
    ])

    def test_dark_barrel_purchases(self, special_day, buffer_multiplier):
        """Test dark barrel purchases on special days with different multipliers"""
        self.logger.info(f"Testing dark barrel purchases for {special_day}")
        
        # First transition to TIERED strategy
        with self.engine.begin() as conn:
            # Add required capacity
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, 
                    entry_type, 
                    ml_capacity_change,
                    potion_capacity_change
                ) VALUES (
                    1, 
                    'ML_CAPACITY_UPGRADE',
                    2,
                    2
                );
            """))
            
            # Set strategy to TIERED
            conn.execute(sqlalchemy.text("""
                INSERT INTO active_strategy (strategy_id, game_time_id)
                VALUES (
                    (SELECT strategy_id FROM strategies WHERE name = 'TIERED'),
                    1
                );
            """))
            
            # Set game time to evening
            conn.execute(sqlalchemy.text("""
                INSERT INTO current_game_time (game_time_id, current_day, current_hour)
                VALUES (
                    (SELECT time_id FROM game_time 
                     WHERE in_game_day = :day AND in_game_hour = 22),
                    :day,
                    22
                );
            """), {"day": special_day})
        
        # Create test catalog with dark and regular barrels
        catalog = [
            self.create_test_barrel('LARGE', 'DARK'),
            self.create_test_barrel('LARGE', 'RED'),
            self.create_test_barrel('MEDIUM', 'GREEN')
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        
        # Verify dark barrel priorities
        dark_purchases = [p for p in purchases if 'DARK' in p.sku]
        assert len(dark_purchases) > 0, f"No dark barrels purchased on {special_day}"
        
        # Verify purchase is LARGE
        assert all("LARGE" in p.sku for p in dark_purchases), \
            "Dark barrels should be LARGE size"
        
        self.logger.info(
            f"{special_day} dark barrel purchases with {buffer_multiplier}x multiplier: "
            f"{dark_purchases}"
        )
    
    def test_barrel_capacity_thresholds(self):
        """Test barrel purchases respect ML capacity thresholds"""
        self.logger.info("Testing ML capacity thresholds")
        
        with self.engine.begin() as conn:
            # Set initial capacity
            total_capacity = 10000  # 1 unit = 10000 ML
            initial_ml = 9000       # 90% full
            
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id,
                    entry_type,
                    ml_change
                ) VALUES (
                    1,
                    'BARREL_PURCHASE',
                    :ml
                );
            """), {"ml": initial_ml})
        
        # Create test catalog
        catalog = [
            self.create_test_barrel('SMALL', 'RED', quantity=5),   # 2500 ML
            self.create_test_barrel('MEDIUM', 'GREEN', quantity=2)  # 5000 ML
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        
        # Calculate total ML from purchases
        total_ml = sum(
            500 if 'SMALL' in p.sku else 2500 if 'MEDIUM' in p.sku else 10000
            for p in purchases
            for _ in range(p.quantity)
        )
        
        # Verify we don't exceed capacity
        assert initial_ml + total_ml <= total_capacity, \
            "Purchases would exceed ML capacity"
        
        self.logger.info(
            f"Capacity threshold test - Initial: {initial_ml}, "
            f"Purchased: {total_ml}, Total: {initial_ml + total_ml}"
        )

    def test_barrel_resource_constraints(self):
        """Test barrel purchases with resource constraints"""
        self.logger.info("Testing resource constraints")
        
        # Set low gold in ledger
        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, gold_change
                ) VALUES (
                    1, 'GOLD_CHANGE', -95  -- Leave only 5 gold
                );
            """))
        
        # Create expensive barrel catalog - proper way with Pydantic
        catalog = [
            Barrel(
                sku='SMALL_RED_BARREL',
                ml_per_barrel=500,
                potion_type=[1,0,0,0],
                price=10,
                quantity=1
            )
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )

    def test_barrel_delivery(self):
        """Test complete barrel purchase and delivery flow"""
        # 1. Create and submit purchase plan
        catalog = [
            self.create_test_barrel('SMALL', 'RED', quantity=2)
        ]
        
        plan_response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        
        assert plan_response.status_code == 200
        planned_purchases = [BarrelPurchase(**p) for p in plan_response.json()]
        assert len(planned_purchases) > 0, "No purchases planned"
        
        # 2. Deliver purchases
        delivery_response = self.client.post(
            "/barrels/deliver/1",
            json=[catalog[0].dict()],
            headers=self.headers
        )
        
        assert delivery_response.status_code == 200
        assert delivery_response.json()["success"] is True
        
        # 3. Verify ledger entries
        with self.engine.begin() as conn:
            entries = conn.execute(sqlalchemy.text("""
                SELECT entry_type, gold_change, ml_change
                FROM ledger_entries
                WHERE entry_type = 'BARREL_PURCHASE'
                ORDER BY entry_id DESC
                LIMIT 1;
            """)).mappings().one()
            
            assert entries["gold_change"] < 0, "No gold deducted"
            assert entries["ml_change"] > 0, "No ML added"
    
    def test_barrel_purchase_plan_penetration(self):
        """Test barrel purchase planning for PENETRATION strategy"""
        self.logger.info("Testing PENETRATION strategy barrel purchases")
        
        # Transition to PENETRATION strategy
        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, gold_change
                ) VALUES (
                    1, 'GOLD_CHANGE', 250  -- Meet PENETRATION threshold
                );
            """))
            
            # Add PENETRATION strategy
            conn.execute(sqlalchemy.text("""
                INSERT INTO active_strategy (strategy_id, game_time_id)
                VALUES (
                    (SELECT strategy_id FROM strategies WHERE name = 'PENETRATION'),
                    1
                );
            """))
        
        # Create test catalog
        catalog = [
            self.create_test_barrel('SMALL', 'RED'),
            self.create_test_barrel('MEDIUM', 'RED'),
            self.create_test_barrel('LARGE', 'RED')
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        
        # PENETRATION should prefer MEDIUM barrels
        medium_purchases = [p for p in purchases if 'MEDIUM' in p.sku]
        assert len(medium_purchases) > 0, "PENETRATION strategy didn't buy MEDIUM barrels"
        
        self.logger.info(f"PENETRATION strategy purchases: {response.json()}")

    def test_barrel_capacity_constraints(self):
        """Test barrel purchases with ml capacity constraints"""
        self.logger.info("Testing ML capacity constraints")
        
        # Fill up ML capacity
        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, ml_change
                ) VALUES (
                    1, 'ML_CAPACITY_UPGRADE', 10000  -- Fill capacity
                );
            """))
        
        catalog = [
            self.create_test_barrel('SMALL', 'RED')
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        assert len(purchases) == 0, "Purchased barrels without available ML capacity"
        
        self.logger.info("Capacity constraint test passed")

    def test_special_day_dark_barrel_timing(self):
        """Test dark barrel purchase timing on special days"""
        special_days = ['Hearthday', 'Blesseday', 'Bloomday']
        
        for day in special_days:
            self.logger.info(f"Testing {day} dark barrel timing")
            
            # Setup evening time (22:00)
            with self.engine.begin() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO current_game_time (game_time_id, current_day, current_hour)
                    VALUES (
                        (SELECT time_id FROM game_time 
                        WHERE in_game_day = :day AND in_game_hour = 22),
                        :day,
                        22
                    );
                """), {"day": day})
            
            catalog = [
                self.create_test_barrel('LARGE', 'DARK')
            ]
            
            response = self.client.post(
                "/barrels/plan",
                json=[b.dict() for b in catalog],
                headers=self.headers
            )
            
            assert response.status_code == 200
            purchases = [BarrelPurchase(**p) for p in response.json()]
            dark_purchases = [p for p in purchases if 'DARK' in p.sku]
            
            assert len(dark_purchases) > 0, f"No dark barrels purchased on {day} evening"
            self.logger.info(f"{day} dark barrel purchases: {dark_purchases}")
    
    def test_penetration_barrel_strategy(self):
        """Test PENETRATION strategy barrel purchasing rules"""
        self.logger.info("Testing PENETRATION strategy purchasing rules")
        
        # Transition to PENETRATION strategy
        with self.engine.begin() as conn:
            self.logger.info("Setting up PENETRATION strategy")
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, gold_change
                ) VALUES (
                    1, 'GOLD_CHANGE', 250
                );
            """))
            
            conn.execute(sqlalchemy.text("""
                INSERT INTO active_strategy (strategy_id, game_time_id)
                VALUES (
                    (SELECT strategy_id FROM strategies WHERE name = 'PENETRATION'),
                    1
                );
            """))
            
            # Verify setup
            strategy = conn.execute(sqlalchemy.text("""
                SELECT s.name
                FROM active_strategy ast
                JOIN strategies s ON ast.strategy_id = s.strategy_id
                ORDER BY ast.activated_at DESC
                LIMIT 1
            """)).scalar_one()
            self.logger.info(f"Current strategy: {strategy}")
            
            state = conn.execute(sqlalchemy.text(
                "SELECT * FROM current_state"
            )).mappings().one()
            self.logger.info(f"Current state: {dict(state)}")

    def test_tiered_dynamic_barrel_strategy(self):
        """Test TIERED/DYNAMIC strategy barrel purchasing rules"""
        self.logger.info("Testing TIERED/DYNAMIC strategy purchasing rules")
        
        # Transition to TIERED strategy with required capacity
        with self.engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, 
                    entry_type, 
                    ml_capacity_change,
                    potion_capacity_change
                ) VALUES (
                    1, 
                    'ML_CAPACITY_UPGRADE',
                    2,
                    2
                );
            """))
            
            conn.execute(sqlalchemy.text("""
                INSERT INTO active_strategy (strategy_id, game_time_id)
                VALUES (
                    (SELECT strategy_id FROM strategies WHERE name = 'TIERED'),
                    1
                );
            """))

        # Test 1: Prefers LARGE when available and affordable
        affordable_catalog = [
            self.create_test_barrel('SMALL', 'RED', quantity=2),
            self.create_test_barrel('MEDIUM', 'RED', quantity=2),
            self.create_test_barrel('LARGE', 'RED', quantity=2)
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in affordable_catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        assert any("LARGE" in p.sku for p in purchases), \
            "TIERED didn't prefer LARGE barrels"
        assert all("SMALL" not in p.sku for p in purchases), \
            "TIERED bought SMALL barrel"
        
        # Test 2: Falls back to MEDIUM when LARGE unaffordable
        with self.engine.begin() as conn:
            # Reset gold to medium amount
            conn.execute(sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, gold_change
                ) VALUES (
                    1, 'GOLD_CHANGE', -200
                );
            """))
        
        expensive_catalog = [
            self.create_test_barrel('SMALL', 'RED', quantity=2),
            self.create_test_barrel('MEDIUM', 'RED', quantity=2),
            self.create_test_barrel('LARGE', 'RED', quantity=2)
        ]
        expensive_catalog[2].price = 300  # Make LARGE unaffordable
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in expensive_catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        assert all("MEDIUM" in p.sku for p in purchases), \
            "TIERED didn't fall back to MEDIUM when LARGE unaffordable"
        assert all("SMALL" not in p.sku for p in purchases), \
            "TIERED bought SMALL barrel when falling back"

        # Test 3: Falls back to MEDIUM when LARGE unavailable
        unavailable_catalog = [
            self.create_test_barrel('SMALL', 'RED', quantity=2),
            self.create_test_barrel('MEDIUM', 'RED', quantity=2)
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in unavailable_catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        assert all("MEDIUM" in p.sku for p in purchases), \
            "TIERED didn't fall back to MEDIUM when LARGE unavailable"
        assert all("SMALL" not in p.sku for p in purchases), \
            "TIERED bought SMALL barrel when falling back"
        
        # Test 4: Can purchase DARK barrels on special days
        with self.engine.begin() as conn:
            # Set time to Hearthday evening
            conn.execute(sqlalchemy.text("""
                INSERT INTO current_game_time (game_time_id, current_day, current_hour)
                VALUES (
                    (SELECT time_id FROM game_time 
                    WHERE in_game_day = 'Hearthday' AND in_game_hour = 22),
                    'Hearthday',
                    22
                );
            """))
        
        dark_catalog = [
            self.create_test_barrel('LARGE', 'DARK', quantity=2),
            self.create_test_barrel('LARGE', 'RED', quantity=2),
            self.create_test_barrel('MEDIUM', 'RED', quantity=2)
        ]
        
        response = self.client.post(
            "/barrels/plan",
            json=[b.dict() for b in dark_catalog],
            headers=self.headers
        )
        
        assert response.status_code == 200
        purchases = [BarrelPurchase(**p) for p in response.json()]
        dark_purchases = [p for p in purchases if "DARK" in p.sku]
        assert len(dark_purchases) > 0, "TIERED couldn't buy DARK barrels on special day"
        assert all("LARGE" in p.sku for p in dark_purchases), \
            "TIERED didn't prefer LARGE for DARK barrels"