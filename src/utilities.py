import base64
import json
import sqlalchemy
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class LedgerManager:
    """Handles ledger operations."""
    
    @staticmethod
    def create_admin_entry(conn, time_id: int) -> None:
        """Creates admin reset ledger entry with 100 gold."""
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id,
                    entry_type,
                    gold_change,
                    ml_capacity_change,
                    potion_capacity_change
                ) VALUES (
                    :time_id,
                    'ADMIN_CHANGE',
                    100,
                    1,
                    1
                )
            """),
            {"time_id": time_id}
        )

class TimeManager:
    """Handles game time and strategy transitions."""
    
    VALID_DAYS = {
        'Hearthday', 'Crownday', 'Blesseday', 'Soulday',
        'Edgeday', 'Bloomday', 'Arcanaday'
    }

    @staticmethod
    def get_current_time(conn) -> dict:
        """Gets latest time_id, day, and hour."""
        result = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    gt.time_id,
                    gt.in_game_day as day,
                    gt.in_game_hour as hour
                FROM current_game_time cgt
                JOIN game_time gt ON cgt.game_time_id = gt.time_id
                ORDER BY cgt.created_at DESC
                LIMIT 1
            """)
        ).mappings().first()
        
        if not result:
            raise HTTPException(status_code=500, detail="No current time found")
        
        return dict(result)
    
    @staticmethod
    def validate_game_time(day: str, hour: int) -> bool:
        """Validates if provided day and hour are valid game time values."""
        if day not in TimeManager.VALID_DAYS:
            return False
            
        if not isinstance(hour, int) or hour < 0 or hour > 22 or hour % 2 != 0:
            return False
        
        return True

    @staticmethod
    def record_time(conn, day: str, hour: int) -> bool:
        """
        Records current game time and checks for strategy transitions.
        Returns True if strategy transition occurred.
        """
        # Get time_id for new time
        time_id = conn.execute(
            sqlalchemy.text("""
                SELECT time_id
                FROM game_time
                WHERE in_game_day = :day AND in_game_hour = :hour
            """),
            {"day": day, "hour": hour}
        ).scalar_one()
        
        # Record new time
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO current_game_time (
                    game_time_id,
                    current_day,
                    current_hour
                ) VALUES (
                    :time_id,
                    :day,
                    :hour
                )
            """),
            {
                "time_id": time_id,
                "day": day,
                "hour": hour
            }
        )
        
        # Check state for strategy transition
        state = conn.execute(
            sqlalchemy.text("""
                WITH current_strat AS (
                    SELECT st.*
                    FROM active_strategy ast
                    JOIN strategy_transitions st ON ast.strategy_id = st.from_strategy_id
                    ORDER BY ast.activated_at DESC
                    LIMIT 1
                ),
                state_check AS (
                    SELECT 
                        cs.*,
                        c.gold,
                        c.total_potions,
                        c.total_ml,
                        c.ml_capacity_units,
                        c.potion_capacity_units
                    FROM current_strat cs
                    CROSS JOIN current_state c
                )
                SELECT 
                    to_strategy_id,
                    CASE
                        WHEN require_all_thresholds THEN
                            (gold >= gold_threshold OR gold_threshold IS NULL) AND
                            (total_potions >= potion_threshold OR potion_threshold IS NULL) AND
                            (total_ml >= ml_threshold OR ml_threshold IS NULL) AND
                            ml_capacity_units >= ml_capacity_threshold AND
                            potion_capacity_units >= potion_capacity_threshold
                        ELSE
                            gold >= gold_threshold OR
                            total_potions >= potion_threshold OR
                            total_ml >= ml_threshold
                    END as should_transition
                FROM state_check
                WHERE to_strategy_id IS NOT NULL
            """)
        ).mappings().first()
    
        if state and state['should_transition']:
            logger.info(
                f"Strategy transition triggered to strategy_id: {state['to_strategy_id']}"
            )
            
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO active_strategy (
                        strategy_id,
                        game_time_id
                    ) VALUES (
                        :strategy_id,
                        :time_id
                    )
                """),
                {
                    "strategy_id": state['to_strategy_id'],
                    "time_id": time_id
                }
            )
            return True
            
        return False

class CatalogManager:
    """Handles catalog creation and potion availability."""
    
    @staticmethod
    def get_available_potions(conn) -> list:
        """Gets available potions based on current strategy and time block."""
        return conn.execute(
            sqlalchemy.text("""
                WITH current_info AS (
                    SELECT 
                        cgt.current_day,
                        cgt.current_hour,
                        ast.strategy_id
                    FROM current_game_time cgt
                    CROSS JOIN (
                        SELECT strategy_id
                        FROM active_strategy
                        ORDER BY activated_at DESC
                        LIMIT 1
                    ) ast
                    ORDER BY cgt.created_at DESC
                    LIMIT 1
                )
                SELECT 
                    p.sku,
                    p.name,
                    p.current_quantity as quantity,
                    p.base_price as price,
                    ARRAY[p.red_ml, p.green_ml, p.blue_ml, p.dark_ml] as potion_type
                FROM current_info ci
                JOIN time_blocks tb 
                    ON ci.current_hour BETWEEN tb.start_hour AND tb.end_hour
                JOIN strategy_time_blocks stb 
                    ON tb.block_id = stb.time_block_id
                    AND ci.strategy_id = stb.strategy_id
                    AND ci.current_day = stb.day_name
                JOIN block_potion_priorities bpp 
                    ON stb.block_id = bpp.block_id
                JOIN potions p 
                    ON bpp.potion_id = p.potion_id
                WHERE p.current_quantity > 0
                ORDER BY bpp.priority_order
                LIMIT 6
                """
            )
        ).mappings().all()

class BarrelManager:
    """Handles barrel purchase planning and processing."""
    
    @staticmethod
    def record_catalog(conn, wholesale_catalog: list, time_id: int) -> int:
        """Records wholesale catalog excluding MINI barrels."""
        # Filter out MINI barrels
        valid_barrels = [b for b in wholesale_catalog if not b['sku'].startswith('MINI')]
        
        # Record visit
        visit_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO barrel_visits (time_id, wholesale_catalog)
                VALUES (:time_id, :catalog)
                RETURNING visit_id
            """),
            {
                "time_id": time_id,
                "catalog": json.dumps([dict(b) for b in wholesale_catalog])
            }
        ).scalar_one()

        # Record barrel details
        for barrel in valid_barrels:
            color_name = barrel['sku'].split('_')[1]
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO barrel_details (
                        visit_id,
                        sku,
                        ml_per_barrel,
                        potion_type,
                        price,
                        quantity,
                        color_id
                    )
                    VALUES (
                        :visit_id,
                        :sku,
                        :ml_per_barrel,
                        :potion_type,
                        :price,
                        :quantity,
                        (SELECT color_id FROM color_definitions WHERE color_name = :color_name)
                    )
                """),
                {
                    "visit_id": visit_id,
                    "sku": barrel["sku"],
                    "ml_per_barrel": barrel["ml_per_barrel"],
                    "potion_type": json.dumps(barrel["potion_type"]),
                    "price": barrel["price"],
                    "quantity": barrel["quantity"],
                    "color_name": color_name
                }
            )
        
        return visit_id
    
    @staticmethod
    def get_color_needs(conn, time_block: dict) -> dict:
        """Calculate color needs based on strategy and time block."""
        # First get base needs from block priorities
        base_needs = conn.execute(
            sqlalchemy.text("""
                WITH current_cap AS (
                    SELECT potion_capacity_units * 50 as total_potion_capacity
                    FROM current_state
                ),
                block_needs AS (
                    SELECT
                        cd.color_name,
                        SUM(
                            CASE
                                WHEN cd.color_name = 'RED' THEN p.red_ml
                                WHEN cd.color_name = 'GREEN' THEN p.green_ml
                                WHEN cd.color_name = 'BLUE' THEN p.blue_ml
                                WHEN cd.color_name = 'DARK' THEN p.dark_ml
                            END * bpp.sales_mix * 
                            (SELECT total_potion_capacity FROM current_cap)
                        ) as ml_needed
                    FROM block_potion_priorities bpp
                    JOIN potions p ON bpp.potion_id = p.potion_id
                    CROSS JOIN color_definitions cd
                    WHERE bpp.block_id = 1
                    GROUP BY cd.color_name
                )
                SELECT 
                    color_name,
                    ml_needed
                FROM block_needs
                WHERE ml_needed > 0
                ORDER BY ml_needed DESC;
            """),
            {"block_id": time_block['block_id']}
        ).mappings().all()

        # Then get strategy multipliers
        multipliers = conn.execute(
            sqlalchemy.text("""
                SELECT
                    buffer_multiplier,
                    dark_buffer_multiplier
                FROM strategy_time_blocks
                WHERE block_id = :block_id
            """),
            {"block_id": time_block['block_id']}
        ).mappings().one()

        # Apply multipliers to needs
        color_needs = {}
        for need in base_needs:
            multiplier = (multipliers['dark_buffer_multiplier'] 
                        if need['color_name'] == 'DARK'
                        else multipliers['buffer_multiplier'])
            color_needs[need['color_name']] = need['ml_needed'] * multiplier

        return color_needs

    @staticmethod
    def plan_barrel_purchases(
        conn,
        wholesale_catalog: list,
        color_needs: dict,
        available_gold: int,
        available_capacity: int,
        block_id: int
    ) -> list:
        """Plan purchases based on needs, current inventory, and buffer strategy."""
        logger.debug(
            f"Starting purchase planning - gold: {available_gold}, "
            f"capacity: {available_capacity}"
        )
        
        # Get current inventory levels
        current_inventory = conn.execute(
            sqlalchemy.text("""
                WITH current_inventory AS (
                    SELECT 
                        p.sku,
                        p.current_quantity,
                        p.red_ml,
                        p.green_ml,
                        p.blue_ml,
                        p.dark_ml
                    FROM potions p
                    JOIN block_potion_priorities bpp ON p.potion_id = bpp.potion_id
                    WHERE bpp.block_id = :block_id
                    AND p.current_quantity > 0
                )
                SELECT
                    'RED' as color_name,
                    SUM(current_quantity * red_ml) as current_ml
                FROM current_inventory
                UNION ALL
                SELECT 'GREEN', SUM(current_quantity * green_ml)
                FROM current_inventory
                UNION ALL
                SELECT 'BLUE', SUM(current_quantity * blue_ml)
                FROM current_inventory
                UNION ALL
                SELECT 'DARK', SUM(current_quantity * dark_ml)
                FROM current_inventory
            """),
            {"block_id": block_id}
        ).mappings().all()
        
        current_ml = {row['color_name']: row['current_ml'] for row in current_inventory}
        logger.debug(f"Current inventory ml by color: {current_ml}")
        
        # Calculate actual ml needed after inventory
        adjusted_needs = {}
        for color, needed_ml in color_needs.items():
            current_amount = current_ml.get(color, 0)
            adjusted_ml = max(0, needed_ml - current_amount)
            adjusted_needs[color] = adjusted_ml
            logger.debug(
                f"{color} - buffered need: {needed_ml}, "
                f"current: {current_amount}, "
                f"adjusted need: {adjusted_ml}"
            )
        
        # Get strategy size preferences
        strategy = conn.execute(sqlalchemy.text("""
            SELECT s.name as strategy_name
            FROM strategies s
            JOIN active_strategy ast ON s.strategy_id = ast.strategy_id
            ORDER BY ast.activated_at DESC
            LIMIT 1
        """)).mappings().one()
        
        logger.debug(f"Current strategy: {strategy['strategy_name']}")
        
        if strategy['strategy_name'] == 'PREMIUM':
            size_preferences = ['SMALL']
        elif strategy['strategy_name'] == 'PENETRATION':
            size_preferences = ['MEDIUM', 'SMALL']
        else:  # TIERED or DYNAMIC
            size_preferences = ['LARGE', 'MEDIUM']
            
        purchases = []
        remaining_gold = available_gold
        remaining_capacity = available_capacity
        catalog_dict = {b['sku']: b for b in wholesale_catalog}
        
        # Prioritize by adjusted color needs
        for color, needed_ml in sorted(
            adjusted_needs.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if needed_ml <= 0:
                continue
                
            logger.debug(f"Processing {color} adjusted need of {needed_ml}ml")
                
            # Try each preferred size
            for size in size_preferences:
                barrel_sku = f"{size}_{color}_BARREL"
                barrel = catalog_dict.get(barrel_sku)
                
                if not barrel:
                    continue
                    
                max_by_gold = remaining_gold // barrel['price']
                max_by_capacity = remaining_capacity // barrel['ml_per_barrel']
                max_by_need = (needed_ml + barrel['ml_per_barrel'] - 1) // barrel['ml_per_barrel']
                max_by_availability = barrel['quantity']
                
                quantity = min(
                    max_by_gold,
                    max_by_capacity,
                    max_by_need,
                    max_by_availability
                )
                
                if quantity > 0:
                    logger.debug(
                        f"Adding purchase - sku: {barrel_sku}, "
                        f"quantity: {quantity}, "
                        f"ml: {quantity * barrel['ml_per_barrel']}"
                    )
                    
                    purchases.append({
                        "sku": barrel_sku,
                        "quantity": quantity
                    })
                    
                    remaining_gold -= quantity * barrel['price']
                    remaining_capacity -= quantity * barrel['ml_per_barrel']
                    needed_ml -= quantity * barrel['ml_per_barrel']
                
                if needed_ml <= 0:
                    break
        
        if purchases:
            logger.info(
                f"Planned {len(purchases)} purchases - "
                f"remaining gold: {remaining_gold}, "
                f"remaining capacity: {remaining_capacity}"
            )
        else:
            logger.debug("No purchases planned after inventory adjustment")
        
        return purchases
    
    @staticmethod
    def validate_purchase_constraints(conn, purchases: list, available_capacity: int) -> None:
        """
        Validates purchases against strategy constraints.
        Raises HTTPException if constraints are violated.
        """
        logger.debug(f"Validating purchases against capacity: {available_capacity}")
        
        # Get current strategy limits
        strategy = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    s.max_potions_per_sku,
                    s.name as strategy_name
                FROM strategies s
                JOIN active_strategy ast ON s.strategy_id = ast.strategy_id
                ORDER BY ast.activated_at DESC
                LIMIT 1
            """)
        ).mappings().one()

        # Validate ml capacity
        total_ml = sum(p['ml_per_barrel'] * p['quantity'] for p in purchases)
        if total_ml > available_capacity:
            logger.error(
                f"Purchase exceeds ml capacity - "
                f"required: {total_ml}, available: {available_capacity}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Purchase would exceed ml capacity: {total_ml} > {available_capacity}"
            )

        # Validate max potions per SKU
        for purchase in purchases:
            potential_potions = (purchase['ml_per_barrel'] * purchase['quantity']) / 100
            if potential_potions > strategy['max_potions_per_sku']:
                logger.error(
                    f"Purchase exceeds max potions per SKU - "
                    f"sku: {purchase['sku']}, "
                    f"potential: {potential_potions}, "
                    f"max: {strategy['max_potions_per_sku']}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Purchase would exceed max potions per SKU: "
                        f"{potential_potions} > {strategy['max_potions_per_sku']}"
                    )
                )
        
        logger.debug("Purchase constraints validated successfully")
    
    @staticmethod
    def process_barrel_purchase(
        conn,
        barrel: dict,
        barrel_id: int,
        time_id: int,
        visit_id: int
    ) -> int:
        """Records a barrel purchase with ledger entry."""
        color_name = barrel['sku'].split('_')[1]
        total_cost = barrel['price'] * barrel['quantity']
        total_ml = barrel['ml_per_barrel'] * barrel['quantity']
        
        logger.debug(
            f"Processing barrel purchase - "
            f"sku: {barrel['sku']}, "
            f"quantity: {barrel['quantity']}, "
            f"cost: {total_cost}"
        )
        
        # Record purchase
        purchase_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO barrel_purchases (
                    visit_id,
                    barrel_id,
                    time_id,
                    quantity,
                    total_cost,
                    ml_added,
                    color_id,
                    purchase_success
                )
                VALUES (
                    :visit_id,
                    :barrel_id,
                    :time_id,
                    :quantity,
                    :total_cost,
                    :ml_added,
                    (SELECT color_id FROM color_definitions WHERE color_name = :color_name),
                    true
                )
                RETURNING purchase_id
            """),
            {
                "visit_id": visit_id,
                "barrel_id": barrel_id,
                "time_id": time_id,
                "quantity": barrel['quantity'],
                "total_cost": total_cost,
                "ml_added": total_ml,
                "color_name": color_name
            }
        ).scalar_one()

        # Create ledger entry
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id,
                    entry_type,
                    barrel_purchase_id,
                    gold_change,
                    ml_change,
                    color_id
                )
                VALUES (
                    :time_id,
                    'BARREL_PURCHASE',
                    :purchase_id,
                    :gold_change,
                    :ml_change,
                    (SELECT color_id FROM color_definitions WHERE color_name = :color_name)
                )
            """),
            {
                "time_id": time_id,
                "purchase_id": purchase_id,
                "gold_change": -total_cost,
                "ml_change": total_ml,
                "color_name": color_name
            }
        )

        logger.info(
            f"Completed barrel purchase {purchase_id} - "
            f"added {total_ml}ml of {color_name}"
        )
        return purchase_id

class BottlerManager:
    """Handles potion bottling planning and processing."""
    
    @staticmethod
    def get_bottling_priorities(conn) -> list:
        """Gets prioritized potions for bottling based on strategy."""
        return conn.execute(
            sqlalchemy.text("""
                WITH future_info AS (
                    SELECT 
                        gt.in_game_day,
                        gt.in_game_hour,
                        ast.strategy_id
                    FROM game_time gt
                    CROSS JOIN (
                        SELECT strategy_id 
                        FROM active_strategy
                        ORDER BY activated_at DESC
                        LIMIT 1
                    ) ast
                    WHERE gt.time_id = (
                        SELECT bottling_time_id
                        FROM game_time
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                )
                SELECT 
                    p.potion_id,
                    p.red_ml,
                    p.green_ml,
                    p.blue_ml,
                    p.dark_ml,
                    bpp.priority_order,
                    bpp.sales_mix
                FROM future_info fi
                JOIN time_blocks tb 
                    ON fi.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
                JOIN strategy_time_blocks stb 
                    ON tb.block_id = stb.time_block_id
                    AND fi.strategy_id = stb.strategy_id
                    AND fi.in_game_day = stb.day_name
                JOIN block_potion_priorities bpp 
                    ON stb.block_id = bpp.block_id
                JOIN potions p 
                    ON bpp.potion_id = p.potion_id
                ORDER BY bpp.priority_order
                """
            )
        ).mappings().all()

    @staticmethod
    def calculate_possible_potions(priorities: list, available_ml: dict, available_capacity: int) -> list:
        """Calculates maximum potions that can be made with available resources."""
        bottling_plan = []
        remaining_ml = available_ml.copy()
        remaining_capacity = available_capacity
        
        for potion in priorities:
            if remaining_capacity <= 0:
                break
            
            max_quantities = [remaining_capacity]
            
            if potion['red_ml'] > 0:
                max_quantities.append(remaining_ml['red_ml'] // potion['red_ml'])
            if potion['green_ml'] > 0:
                max_quantities.append(remaining_ml['green_ml'] // potion['green_ml'])
            if potion['blue_ml'] > 0:
                max_quantities.append(remaining_ml['blue_ml'] // potion['blue_ml'])
            if potion['dark_ml'] > 0:
                max_quantities.append(remaining_ml['dark_ml'] // potion['dark_ml'])
            
            quantity = min(max_quantities)
            
            if quantity > 0:
                bottling_plan.append({
                    "potion_type": [
                        potion['red_ml'],
                        potion['green_ml'],
                        potion['blue_ml'],
                        potion['dark_ml']
                    ],
                    "quantity": quantity
                })
                
                remaining_capacity -= quantity
                if potion['red_ml'] > 0:
                    remaining_ml['red_ml'] -= quantity * potion['red_ml']
                if potion['green_ml'] > 0:
                    remaining_ml['green_ml'] -= quantity * potion['green_ml']
                if potion['blue_ml'] > 0:
                    remaining_ml['blue_ml'] -= quantity * potion['blue_ml']
                if potion['dark_ml'] > 0:
                    remaining_ml['dark_ml'] -= quantity * potion['dark_ml']
        
        return bottling_plan

    @staticmethod
    def process_bottling(conn, potion_data: dict, time_id: int) -> None:
        """Processes potion bottling with ledger entries."""
        # Get potion_id for mixture
        potion_id = conn.execute(
            sqlalchemy.text("""
                SELECT potion_id
                FROM potions
                WHERE ARRAY[red_ml, green_ml, blue_ml, dark_ml] = :potion_type
                """,
                {"potion_type": potion_data['potion_type']}
            )
        ).scalar_one()
        
        # Update potion inventory
        conn.execute(
            sqlalchemy.text("""
                UPDATE potions
                SET current_quantity = current_quantity + :quantity
                WHERE potion_id = :potion_id
                """,
                {
                    "quantity": potion_data['quantity'],
                    "potion_id": potion_id
                }
            )
        )
        
        # Create ledger entries for each color used
        color_map = {0: 'RED', 1: 'GREEN', 2: 'BLUE', 3: 'DARK'}
        
        for idx, amount in enumerate(potion_data['potion_type']):
            if amount > 0:
                ml_used = amount * potion_data['quantity']
                color_id = conn.execute(
                    sqlalchemy.text("""
                        SELECT color_id 
                        FROM color_definitions 
                        WHERE color_name = :color
                        """,
                        {"color": color_map[idx]}
                    )
                ).scalar_one()
                
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO ledger_entries (
                            time_id,
                            entry_type,
                            ml_change,
                            potion_change,
                            color_id,
                            potion_id
                        )
                        VALUES (
                            :time_id,
                            'POTION_BOTTLED',
                            :ml_change,
                            :potion_change,
                            :color_id,
                            :potion_id
                        )
                        """,
                        {
                            "time_id": time_id,
                            "ml_change": -ml_used,
                            "potion_change": potion_data['quantity'],
                            "color_id": color_id,
                            "potion_id": potion_id
                        }
                    )
                )

class CartManager:
    """Handles cart operations and customer interactions."""
    
    PAGE_SIZE = 5  # Maximum results per page for search
    
    @staticmethod
    def record_customer_visit(conn, visit_id: int, customers: list, time_id: int) -> int:
        """Records customer visit and individual customers."""
        visit_record_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO customer_visits (visit_id, time_id, customers)
                VALUES (:visit_id, :time_id, :customers)
                RETURNING visit_record_id
                """,
                {
                    "visit_id": visit_id,
                    "time_id": time_id,
                    "customers": customers
                }
            )
        ).scalar_one()

        for customer in customers:
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO customers (
                        visit_record_id,
                        visit_id,
                        time_id,
                        customer_name,
                        character_class,
                        level
                    ) VALUES (
                        :visit_record_id,
                        :visit_id,
                        :time_id,
                        :name,
                        :class,
                        :level
                    )
                    """,
                    {
                        "visit_record_id": visit_record_id,
                        "visit_id": visit_id,
                        "time_id": time_id,
                        "name": customer['customer_name'],
                        "class": customer['character_class'],
                        "level": customer['level']
                    }
                )
            )
        
        return visit_record_id

    @staticmethod
    def create_cart(conn, customer: dict, time_id: int, visit_id: int) -> int:
        """Creates new cart for customer."""
        customer_id = conn.execute(
            sqlalchemy.text("""
                SELECT c.customer_id
                FROM customers c
                JOIN customer_visits cv ON c.visit_record_id = cv.visit_record_id
                WHERE c.customer_name = :name 
                AND c.character_class = :class
                AND c.level = :level
                AND cv.visit_id = :visit_id
                ORDER BY cv.created_at DESC
                LIMIT 1
                """,
                {
                    "name": customer['customer_name'],
                    "class": customer['character_class'],
                    "level": customer['level'],
                    "visit_id": visit_id
                }
            )
        ).scalar()
        
        return conn.execute(
            sqlalchemy.text("""
                INSERT INTO carts (
                    customer_id,
                    visit_id,
                    time_id,
                    checked_out,
                    total_potions,
                    total_gold
                ) VALUES (
                    :customer_id,
                    :visit_id,
                    :time_id,
                    false,
                    0,
                    0
                )
                RETURNING cart_id
                """,
                {
                    "customer_id": customer_id,
                    "visit_id": visit_id,
                    "time_id": time_id
                }
            )
        ).scalar_one()

    @staticmethod
    def validate_cart_status(conn, cart_id: int) -> dict:
        """Validates cart exists and is not checked out."""
        result = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    c.cart_id,
                    c.visit_id,
                    c.checked_out
                FROM carts c
                WHERE c.cart_id = :cart_id
                """,
                {"cart_id": cart_id}
            )
        ).mappings().first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        if result['checked_out']:
            raise HTTPException(status_code=400, detail="Cart already checked out")
        
        return dict(result)

    @staticmethod
    def update_cart_item(
        conn, 
        cart_id: int, 
        item_sku: str, 
        quantity: int,
        time_id: int,
        visit_id: int
    ) -> None:
        """Updates cart item quantity."""
        potion = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    potion_id,
                    current_quantity,
                    base_price
                FROM potions
                WHERE sku = :sku
                """,
                {"sku": item_sku}
            )
        ).mappings().one()
        
        if potion['current_quantity'] < quantity:
            raise HTTPException(status_code=400, detail="Insufficient quantity")
        
        line_total = potion['base_price'] * quantity
        
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO cart_items (
                    cart_id,
                    visit_id,
                    potion_id,
                    time_id,
                    quantity,
                    unit_price,
                    line_total
                ) VALUES (
                    :cart_id,
                    :visit_id,
                    :potion_id,
                    :time_id,
                    :quantity,
                    :price,
                    :line_total
                )
                ON CONFLICT (cart_id, potion_id) 
                DO UPDATE SET
                    quantity = :quantity,
                    unit_price = :price,
                    line_total = :line_total,
                    time_id = :time_id
                """,
                {
                    "cart_id": cart_id,
                    "visit_id": visit_id,
                    "potion_id": potion['potion_id'],
                    "time_id": time_id,
                    "quantity": quantity,
                    "price": potion['base_price'],
                    "line_total": line_total
                }
            )
        )

    @staticmethod
    def process_checkout(conn, cart_id: int, payment: str, time_id: int) -> dict:
        """Process cart checkout."""
        items = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    ci.potion_id,
                    ci.quantity,
                    ci.unit_price,
                    ci.line_total,
                    p.current_quantity,
                    p.sku
                FROM cart_items ci
                JOIN potions p ON ci.potion_id = p.potion_id
                WHERE ci.cart_id = :cart_id
                """,
                {"cart_id": cart_id}
            )
        ).mappings().all()
        
        if not items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        total_potions = sum(item['quantity'] for item in items)
        total_gold = sum(item['line_total'] for item in items)
        
        # Verify inventory
        for item in items:
            if item['current_quantity'] < item['quantity']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient quantity for {item['sku']}"
                )
        
        # Update inventory and create ledger entries
        for item in items:
            conn.execute(
                sqlalchemy.text("""
                    UPDATE potions
                    SET current_quantity = current_quantity - :quantity
                    WHERE potion_id = :potion_id
                    """,
                    {
                        "quantity": item['quantity'],
                        "potion_id": item['potion_id']
                    }
                )
            )
            
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO ledger_entries (
                        time_id,
                        entry_type,
                        cart_id,
                        potion_id,
                        gold_change,
                        potion_change
                    )
                    VALUES (
                        :time_id,
                        'POTION_SOLD',
                        :cart_id,
                        :potion_id,
                        :gold_change,
                        :potion_change
                    )
                    """,
                    {
                        "time_id": time_id,
                        "cart_id": cart_id,
                        "potion_id": item['potion_id'],
                        "gold_change": item['line_total'],
                        "potion_change": -item['quantity']
                    }
                )
            )
        
        # Mark cart as checked out
        conn.execute(
            sqlalchemy.text("""
                UPDATE carts
                SET 
                    checked_out = true,
                    checked_out_at = NOW(),
                    payment = :payment,
                    total_potions = :total_potions,
                    total_gold = :total_gold,
                    purchase_success = true
                WHERE cart_id = :cart_id
                """,
                {
                    "payment": payment,
                    "total_potions": total_potions,
                    "total_gold": total_gold,
                    "cart_id": cart_id
                }
            )
        )
        
        return {
            "total_potions_bought": total_potions,
            "total_gold_paid": total_gold
        }

    @staticmethod
    def search_orders(
        conn,
        customer_name: str,
        potion_sku: str,
        search_page: str,
        sort_col: str,
        sort_order: str
    ) -> dict:
        """Search orders with pagination."""
        base_query = """
            SELECT
                ci.item_id as line_item_id,
                p.sku as item_sku,
                cu.customer_name,
                ci.line_total as line_item_total,
                c.checked_out_at as timestamp
            FROM cart_items ci
            JOIN carts c ON ci.cart_id = c.cart_id
            JOIN customers cu ON c.customer_id = cu.customer_id
            JOIN potions p ON ci.potion_id = p.potion_id
            WHERE c.checked_out = true
            """
        params = {}
        
        # Add filters
        if customer_name:
            base_query += " AND LOWER(cu.customer_name) LIKE LOWER(:customer_name)"
            params["customer_name"] = f"%{customer_name}%"
        
        if potion_sku:
            base_query += " AND LOWER(p.sku) LIKE LOWER(:potion_sku)"
            params["potion_sku"] = f"%{potion_sku}%"
        
        # Add sorting
        sort_mapping = {
            "customer_name": "cu.customer_name",
            "item_sku": "p.sku",
            "line_item_total": "ci.line_total",
            "timestamp": "c.checked_out_at"
        }
        
        base_query += f" ORDER BY {sort_mapping[sort_col]} {sort_order}"
        
        # Add pagination
        if search_page:
            try:
                decoded_cursor = base64.b64decode(search_page).decode('utf-8')
                cursor_values = json.loads(decoded_cursor)
                
                # Add pagination condition based on sort order
                if sort_order == "desc":
                    base_query += f" AND {sort_mapping[sort_col]} < :cursor_value"
                else:
                    base_query += f" AND {sort_mapping[sort_col]} > :cursor_value"
                
                params["cursor_value"] = cursor_values[sort_col]
            except (ValueError, KeyError) as e:
                logger.error(f"Invalid search page cursor: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid search page")
        
        # Get one extra result to determine if there's a next page
        base_query += " LIMIT :limit"
        params["limit"] = CartManager.PAGE_SIZE + 1
        
        results = conn.execute(
            sqlalchemy.text(base_query),
            params
        ).mappings().all()
        
        # Handle pagination tokens
        has_next = len(results) > CartManager.PAGE_SIZE
        if has_next:
            results = results[:CartManager.PAGE_SIZE]
        
        # Generate previous/next cursors
        previous_cursor = ""
        next_cursor = ""
        
        # Create cursor for previous page
        if search_page:
            previous_params = {
                sort_col: results[0][sort_col] if results else None
            }
            previous_cursor = base64.b64encode(
                json.dumps(previous_params).encode('utf-8')
            ).decode('utf-8')
        
        # Create cursor for next page
        if has_next:

            next_params = {
                sort_col: results[-1][sort_col]
            }
            next_cursor = base64.b64encode(
                json.dumps(next_params).encode('utf-8')
            ).decode('utf-8')
        
        # Format
        formatted_results = [
            {
                "line_item_id": result["line_item_id"],
                "item_sku": result["item_sku"],
                "customer_name": result["customer_name"],
                "line_item_total": result["line_item_total"],
                "timestamp": result["timestamp"].isoformat()
            }
            for result in results
        ]
        
        return {
            "previous": previous_cursor,
            "next": next_cursor,
            "results": formatted_results
        }

class InventoryManager:
    """Handles inventory state and capacity management."""
    
    @staticmethod
    def get_inventory_state(conn) -> dict:
        """Get current inventory state from ledger."""
        result = conn.execute(
            sqlalchemy.text("""
                WITH ledger_totals AS (
                    SELECT
                        COALESCE(SUM(gold_change), 100) as gold,
                        COALESCE(SUM(ml_change), 0) as total_ml,
                        COALESCE(SUM(potion_change), 0) as total_potions,
                        COUNT(*) FILTER (
                            WHERE entry_type = 'CAPACITY_UPGRADE' 
                            AND potion_change IS NOT NULL
                        ) as potion_upgrades,
                        COUNT(*) FILTER (
                            WHERE entry_type = 'CAPACITY_UPGRADE' 
                            AND ml_change IS NOT NULL
                        ) as ml_upgrades
                    FROM ledger_entries
                )
                SELECT
                    gold,
                    total_ml,
                    total_potions,
                    (1 + potion_upgrades) * 50 as max_potions,
                    (1 + ml_upgrades) * 10000 as max_ml,
                    (1 + potion_upgrades) as potion_capacity_units,
                    (1 + ml_upgrades) as ml_capacity_units
                FROM ledger_totals
                """
            )
        ).mappings().one()
        
        return dict(result)
    
    @staticmethod
    def get_capacity_purchase_plan(conn, state: dict) -> dict:
        """Determine capacity purchases based on thresholds."""
        # Calculate current usage percentages
        potion_usage = state['total_potions'] / state['max_potions']
        ml_usage = state['total_ml'] / state['max_ml']
        
        threshold = conn.execute(
            sqlalchemy.text("""
                SELECT *
                FROM capacity_upgrade_thresholds
                WHERE 
                    min_potion_units <= :current_potion_units
                    AND (max_potion_units IS NULL 
                        OR max_potion_units >= :current_potion_units)
                    AND min_ml_units <= :current_ml_units
                    AND (max_ml_units IS NULL 
                        OR max_ml_units >= :current_ml_units)
                    AND gold_threshold <= :current_gold
                    AND (
                        NOT requires_inventory_check
                        OR (
                            :potion_usage >= capacity_check_threshold
                            OR :ml_usage >= capacity_check_threshold
                        )
                    )
                ORDER BY priority_order DESC
                LIMIT 1
                """,
                {
                    "current_potion_units": state['potion_capacity_units'],
                    "current_ml_units": state['ml_capacity_units'],
                    "current_gold": state['gold'],
                    "potion_usage": potion_usage,
                    "ml_usage": ml_usage
                }
            )
        ).mappings().first()
        
        if threshold:
            return {
                "potion_capacity": threshold['potion_capacity_purchase'],
                "ml_capacity": threshold['ml_capacity_purchase']
            }
        
        return {
            "potion_capacity": 0,
            "ml_capacity": 0
        }
    
    @staticmethod
    def process_capacity_upgrade(conn, potion_capacity: int, ml_capacity: int, time_id: int) -> None:
        """Process capacity upgrade with ledger entries."""
        total_cost = (potion_capacity + ml_capacity) * 1000
        
        current_gold = conn.execute(
            sqlalchemy.text("""
                SELECT COALESCE(SUM(gold_change), 100) as gold
                FROM ledger_entries
                """
            )
        ).scalar_one()
        
        if current_gold < total_cost:
            raise HTTPException(
                status_code=400,
                detail="Insufficient gold for capacity upgrade"
            )
        
        if potion_capacity > 0:
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO ledger_entries (
                        time_id,
                        entry_type,
                        gold_change,
                        potion_capacity_change
                    ) VALUES (
                        :time_id,
                        'POTION_CAPACITY_UPGRADE',
                        :gold_change,
                        :potion_capacity
                    )
                """),
                {
                    "time_id": time_id,
                    "gold_change": -(potion_capacity * 1000),
                    "potion_capacity": potion_capacity
                }
            )
        
        if ml_capacity > 0:
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO ledger_entries (
                        time_id,
                        entry_type,
                        gold_change,
                        ml_capacity_change
                    ) VALUES (
                        :time_id,
                        'ML_CAPACITY_UPGRADE',
                        :gold_change,
                        :ml_capacity
                    )
                """),
                {
                    "time_id": time_id,
                    "gold_change": -(ml_capacity * 1000),
                    "ml_capacity": ml_capacity
                }
            )
