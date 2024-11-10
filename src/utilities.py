import json
import sqlalchemy
import logging
from fastapi import HTTPException
from typing import Dict, List

logger = logging.getLogger(__name__)

class LedgerManager:
    """Handles ledger operations."""
    
    @staticmethod
    def create_admin_entry(conn, time_id: int) -> None:
        """Creates admin reset ledger entry with initial values."""
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
                    100,  -- Initial gold
                    1,    -- Initial ml capacity unit
                    1     -- Initial potion capacity unit
                )
            """),
            {"time_id": time_id}
        )
        logger.info("Created admin reset ledger entry with initial values")

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

    def record_time(conn, day: str, hour: int) -> bool:
        """
        Records current game time and processes strategy transitions.
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

        # Get current strategy
        current_strategy = conn.execute(
            sqlalchemy.text("""
                SELECT s.name as strategy_name, s.strategy_id
                FROM active_strategy ast
                JOIN strategies s ON ast.strategy_id = s.strategy_id
                ORDER BY ast.activated_at DESC
                LIMIT 1
            """)
        ).mappings().one()
        
        # Only check for transition if still in PREMIUM
        if current_strategy['strategy_name'] == 'PREMIUM':
            state = conn.execute(
                sqlalchemy.text("SELECT * FROM current_state")
            ).mappings().one()
            
            # Check if any transition condition is met
            should_transition = conn.execute(
                sqlalchemy.text("""
                    WITH transition_check AS (
                        SELECT 
                            st.to_strategy_id,
                            CASE 
                                WHEN :gold >= st.gold_threshold THEN true
                                WHEN :total_potions >= st.potion_threshold THEN true
                                WHEN :total_ml >= st.ml_threshold THEN true
                                ELSE false
                            END as should_transition
                        FROM active_strategy ast
                        JOIN strategies s ON ast.strategy_id = s.strategy_id
                        JOIN strategy_transitions st ON ast.strategy_id = st.from_strategy_id
                        WHERE s.name = 'PREMIUM'
                        ORDER BY ast.activated_at DESC
                        LIMIT 1
                    )
                    SELECT to_strategy_id, should_transition
                    FROM transition_check
                    WHERE should_transition = true
                """),
                {
                    "gold": state['gold'],
                    "total_potions": state['total_potions'],
                    "total_ml": state['total_ml']
                }
            ).mappings().first()

            if should_transition:
                new_strategy_id = should_transition['to_strategy_id']
                
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
                        "strategy_id": new_strategy_id,
                        "time_id": time_id
                    }
                )
                
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO ledger_entries (
                            time_id,
                            entry_type
                        ) VALUES (
                            :time_id,
                            'STRATEGY_CHANGE'
                        )
                    """),
                    {"time_id": time_id}
                )
                
                logger.info(f"Successfully transitioned from PREMIUM to PENETRATION")
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
                    COALESCE(p.current_quantity, 0) as quantity,
                    p.base_price as price,
                    ARRAY[
                        COALESCE(p.red_ml, 0),
                        COALESCE(p.green_ml, 0),
                        COALESCE(p.blue_ml, 0),
                        COALESCE(p.dark_ml, 0)
                    ] as potion_type
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
                WHERE COALESCE(p.current_quantity, 0) > 0
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
        
        # Get current inventory levels with proper NULL handling
        current_inventory = conn.execute(
            sqlalchemy.text("""
                WITH color_inventory AS (
                    SELECT 
                        cd.color_name,
                        COALESCE(
                            SUM(
                                p.current_quantity * 
                                CASE 
                                    WHEN cd.color_name = 'RED' THEN p.red_ml
                                    WHEN cd.color_name = 'GREEN' THEN p.green_ml
                                    WHEN cd.color_name = 'BLUE' THEN p.blue_ml
                                    WHEN cd.color_name = 'DARK' THEN p.dark_ml
                                END
                            ),
                            0
                        ) as current_ml
                    FROM color_definitions cd
                    LEFT JOIN block_potion_priorities bpp ON bpp.block_id = :block_id
                    LEFT JOIN potions p ON p.potion_id = bpp.potion_id 
                        AND p.current_quantity > 0
                    GROUP BY cd.color_name
                )
                SELECT color_name, current_ml
                FROM color_inventory
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
                """
            ),
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
                """
            ),
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
        result = conn.execute(
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
                ),
                time_block_info AS (
                    SELECT 
                        tb.name as block_name,
                        tb.block_id
                    FROM future_info fi
                    JOIN time_blocks tb 
                        ON fi.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
                )
                SELECT 
                    p.potion_id,
                    p.red_ml,
                    p.green_ml,
                    p.blue_ml,
                    p.dark_ml,
                    p.current_quantity as inventory,
                    bpp.priority_order,
                    bpp.sales_mix,
                    s.max_potions_per_sku,
                    fi.in_game_day,
                    tbi.block_name
                FROM future_info fi
                CROSS JOIN time_block_info tbi
                JOIN strategy_time_blocks stb 
                    ON tbi.block_id = stb.time_block_id
                    AND fi.strategy_id = stb.strategy_id
                    AND fi.in_game_day = stb.day_name
                JOIN block_potion_priorities bpp 
                    ON stb.block_id = bpp.block_id
                JOIN potions p 
                    ON bpp.potion_id = p.potion_id
                JOIN strategies s 
                    ON fi.strategy_id = s.strategy_id
                ORDER BY bpp.priority_order
            """
            )
        ).mappings().all()
        
        logger.debug(
            f"Getting priorities for time block - "
            f"day: {result[0]['in_game_day']}, "
            f"block: {result[0]['block_name']}"
        )
        
        return list(result)
    
    @staticmethod
    def calculate_color_resource_limits(
        potion: Dict,
        available_ml: Dict[str, int]
    ) -> int:
        """Calculate maximum potions possible based on available color resources."""
        limits = []
        for color in ["red_ml", "green_ml", "blue_ml", "dark_ml"]:
            if potion[color] > 0:
                limits.append(available_ml[color] // potion[color])
        return min(limits) if limits else 0


    @staticmethod
    def calculate_possible_potions(
        priorities: List[Dict],
        available_ml: Dict[str, int],
        available_capacity: int
    ) -> List[Dict]:
        """Calculates maximum potions that can be made with available resources."""
        bottling_plan = []
        remaining_ml = available_ml.copy()
        remaining_capacity = available_capacity
        
        for potion in priorities:
            if remaining_capacity <= 0:
                break
                
            # Calculate resource limits with NULL safety
            resource_limits = []
            for color, ml_amount in [
                ("red_ml", remaining_ml.get("red_ml", 0)),
                ("green_ml", remaining_ml.get("green_ml", 0)),
                ("blue_ml", remaining_ml.get("blue_ml", 0)),
                ("dark_ml", remaining_ml.get("dark_ml", 0))
            ]:
                if potion[color] > 0:
                    resource_limits.append(ml_amount // potion[color])
            
            resource_max = min(resource_limits) if resource_limits else 0
            
            # Apply strategy limits
            final_max = min(
                resource_max,
                remaining_capacity,
                potion['max_potions_per_sku'] - potion.get('inventory', 0),
                int(potion['sales_mix'] * available_capacity) - potion.get('inventory', 0)
            )
            
            if final_max > 0:
                bottling_plan.append({
                    "potion_type": [
                        potion['red_ml'],
                        potion['green_ml'],
                        potion['blue_ml'],
                        potion['dark_ml']
                    ],
                    "quantity": final_max
                })
                
                remaining_capacity -= final_max
                for color in ["red_ml", "green_ml", "blue_ml", "dark_ml"]:
                    if potion[color] > 0:
                        remaining_ml[color] = remaining_ml.get(color, 0) - (final_max * potion[color])
        
        return bottling_plan

    @staticmethod
    def process_bottling(conn, potion_data: Dict, time_id: int) -> None:
        """Processes potion bottling with ledger entries."""
        # Get potion_id for mixture
        potion_id = conn.execute(
            sqlalchemy.text("""
                SELECT potion_id 
                FROM potions 
                WHERE ARRAY[red_ml, green_ml, blue_ml, dark_ml] = :potion_type
            """),
            {"potion_type": potion_data['potion_type']}
        ).scalar_one()

        # Update potion inventory
        conn.execute(
            sqlalchemy.text("""
                UPDATE potions
                SET current_quantity = current_quantity + :quantity
                WHERE potion_id = :potion_id
            """),
            {
                "quantity": potion_data['quantity'],
                "potion_id": potion_id
            }
        )

        # Calculate ml used for logging
        ml_used = {}
        color_map = {0: 'red', 1: 'green', 2: 'blue', 3: 'dark'}
        
        for idx, amount in enumerate(potion_data['potion_type']):
            if amount > 0:
                ml_used[color_map[idx]] = amount * potion_data['quantity']
                
                # Create ledger entry
                color_id = conn.execute(
                    sqlalchemy.text("""
                        SELECT color_id 
                        FROM color_definitions 
                        WHERE color_name = :color
                    """),
                    {"color": color_map[idx].upper()}
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
                    """),
                    {
                        "time_id": time_id,
                        "ml_change": -ml_used[color_map[idx]],
                        "potion_change": potion_data['quantity'],
                        "color_id": color_id,
                        "potion_id": potion_id
                    }
                )
        
        # Get remaining capacity for logging
        remaining_capacity = conn.execute(
            sqlalchemy.text("""
                SELECT max_potions - total_potions as remaining
                FROM current_state
            """)
        ).scalar_one()
        
        logger.info(
            f"Bottled potions - quantity: {potion_data['quantity']}, "
            f"ml used: {ml_used}, remaining capacity: {remaining_capacity}"
        )

class CartManager:
    """Handles cart operations and customer interactions."""
    
    PAGE_SIZE = 5

    @staticmethod
    def record_customer_visit(conn, visit_id: int, customers: list, time_id: int) -> int:
        """Records customer visit and individual customers."""
        visit_record_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO customer_visits (visit_id, time_id, customers)
                VALUES (:visit_id, :time_id, :customers)
                RETURNING visit_record_id
                """
            ),
            {
                "visit_id": visit_id,
                "time_id": time_id,
                "customers": json.dumps(customers)
            }
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
                    """
                ),
                {
                    "visit_record_id": visit_record_id,
                    "visit_id": visit_id,
                    "time_id": time_id,
                    "name": customer['customer_name'],
                    "class": customer['character_class'],
                    "level": customer['level']
                }
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
                """
            ),
            {
                "name": customer['customer_name'],
                "class": customer['character_class'],
                "level": customer['level'],
                "visit_id": visit_id
            }
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
                """
            ),
            {
                "customer_id": customer_id,
                "visit_id": visit_id,
                "time_id": time_id
            }
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
                """
            ),
            {"cart_id": cart_id}
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
                """
            ),
            {"sku": item_sku}
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
                """
            ),
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

    @staticmethod
    def process_checkout(conn, cart_id: int, payment: str, time_id: int) -> dict:
        """Process cart checkout."""
        items = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    ci.potion_id,
                    COALESCE(ci.quantity, 0) as quantity,
                    COALESCE(ci.unit_price, 0) as unit_price,
                    COALESCE(ci.line_total, 0) as line_total,
                    COALESCE(p.current_quantity, 0) as current_quantity,
                    p.sku
                FROM cart_items ci
                JOIN potions p ON ci.potion_id = p.potion_id
                WHERE ci.cart_id = :cart_id
                """
            ),
            {"cart_id": cart_id}
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
                    """
                ),
                {
                    "quantity": item['quantity'],
                    "potion_id": item['potion_id']
                }
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
                    """
                ),
                {
                    "time_id": time_id,
                    "cart_id": cart_id,
                    "potion_id": item['potion_id'],
                    "gold_change": item['line_total'],
                    "potion_change": -item['quantity']
                }
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
                """
            ),
            {
                "payment": payment,
                "total_potions": total_potions,
                "total_gold": total_gold,
                "cart_id": cart_id
            }
        )
        
        return {
            "total_potions_bought": total_potions,
            "total_gold_paid": total_gold
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
                        COALESCE(SUM(gold_change), 0) as gold,
                        COALESCE(SUM(ml_change), 0) as total_ml,
                        COALESCE(SUM(potion_change), 0) as total_potions,
                        COALESCE(SUM(ml_capacity_change), 0) as ml_capacity_units,
                        COALESCE(SUM(potion_capacity_change), 0) as potion_capacity_units
                    FROM ledger_entries
                )
                SELECT
                    gold,
                    total_ml,
                    total_potions,
                    ml_capacity_units,
                    potion_capacity_units,
                    (potion_capacity_units * 50) as max_potions,
                    (ml_capacity_units * 10000) as max_ml
                FROM ledger_totals
            """)
        ).mappings().one()
        
        return dict(result)
    
    @staticmethod
    def get_capacity_purchase_plan(conn, state: dict) -> dict:
        """Determine capacity purchases based on thresholds."""
        # Calculate current usage percentages
        potion_usage = state['total_potions'] / state['max_potions']
        ml_usage = state['total_ml'] / state['max_ml']
        
        logger.debug(
            f"Checking capacity thresholds - "
            f"potion usage: {potion_usage:.2%}, "
            f"ml usage: {ml_usage:.2%}"
        )
        
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
            """),
            {
                "current_potion_units": state['potion_capacity_units'],
                "current_ml_units": state['ml_capacity_units'],
                "current_gold": state['gold'],
                "potion_usage": potion_usage,
                "ml_usage": ml_usage
            }
        ).mappings().first()
        
        if threshold:
            logger.debug(
                f"Found capacity upgrade threshold - "
                f"potion purchase: {threshold['potion_capacity_purchase']}, "
                f"ml purchase: {threshold['ml_capacity_purchase']}"
            )
            return {
                "potion_capacity": threshold['potion_capacity_purchase'],
                "ml_capacity": threshold['ml_capacity_purchase']
            }
        
        logger.debug("No capacity upgrade needed at current thresholds")
        return {
            "potion_capacity": 0,
            "ml_capacity": 0
        }
    
    @staticmethod
    def check_strategy_transition(conn, current_units: dict) -> tuple[bool, int]:
        """Check if capacity upgrade triggers strategy transition."""
        result = conn.execute(
            sqlalchemy.text("""
                WITH current_strategy AS (
                    SELECT strategy_id 
                    FROM active_strategy 
                    ORDER BY activated_at DESC 
                    LIMIT 1
                )
                SELECT 
                    st.from_strategy_id,
                    st.to_strategy_id,
                    s.name as current_strategy
                FROM current_strategy cs
                JOIN strategies s ON cs.strategy_id = s.strategy_id
                LEFT JOIN strategy_transitions st ON cs.strategy_id = st.from_strategy_id
                WHERE s.name != 'DYNAMIC'
            """)
        ).mappings().first()
        
        if not result:
            return False, None
            
        # PENETRATION to TIERED
        if (result['current_strategy'] == 'PENETRATION' and
            current_units['ml_capacity_units'] >= 2 and
            current_units['potion_capacity_units'] >= 2):
            return True, result['to_strategy_id']
            
        # TIERED to DYNAMIC
        if (result['current_strategy'] == 'TIERED' and
            current_units['ml_capacity_units'] >= 4 and
            current_units['potion_capacity_units'] >= 4):
            return True, result['to_strategy_id']
            
        return False, None
    
    @staticmethod
    def process_capacity_upgrade(
        conn,
        potion_capacity: int,
        ml_capacity: int,
        time_id: int
    ) -> None:
        """Process capacity upgrade with ledger entries and strategy transition."""
        total_cost = (potion_capacity + ml_capacity) * 1000
        
        current_state = InventoryManager.get_inventory_state(conn)
        
        if current_state['gold'] < total_cost:
            logger.error(
                f"Insufficient gold for capacity upgrade - "
                f"required: {total_cost}, available: {current_state['gold']}"
            )
            raise HTTPException(
                status_code=400,
                detail="Insufficient gold for capacity upgrade"
            )
        
        # Record capacity upgrade in ledger
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
                    'ML_CAPACITY_UPGRADE',
                    :gold_change,
                    :ml_capacity,
                    :potion_capacity
                )
            """),
            {
                "time_id": time_id,
                "gold_change": -total_cost,
                "ml_capacity": ml_capacity,
                "potion_capacity": potion_capacity
            }
        )
        
        # Check if upgrade triggers strategy transition
        new_units = {
            'ml_capacity_units': current_state['ml_capacity_units'] + ml_capacity,
            'potion_capacity_units': current_state['potion_capacity_units'] + potion_capacity
        }
        
        should_transition, new_strategy_id = InventoryManager.check_strategy_transition(
            conn, 
            new_units
        )
        
        if should_transition:
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
                    "strategy_id": new_strategy_id,
                    "time_id": time_id
                }
            )
            logger.info(f"Upgraded to strategy_id: {new_strategy_id}")
            
        logger.info(
            f"Processed capacity upgrade - "
            f"potion units: +{potion_capacity}, "
            f"ml units: +{ml_capacity}, "
            f"total cost: {total_cost}"
        )
