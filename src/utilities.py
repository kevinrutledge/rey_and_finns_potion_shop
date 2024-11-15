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
                FOR UPDATE
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

        # Get current strategy with lock
        current_strategy = conn.execute(
            sqlalchemy.text("""
                SELECT s.name as strategy_name, s.strategy_id
                FROM active_strategy ast
                JOIN strategies s ON ast.strategy_id = s.strategy_id
                ORDER BY ast.activated_at DESC
                LIMIT 1
                FOR UPDATE
            """)
        ).mappings().one()
        
        # Only check for transition if still in PREMIUM
        if current_strategy['strategy_name'] == 'PREMIUM':
            state = conn.execute(
                sqlalchemy.text("""
                    SELECT * 
                    FROM current_state
                    FOR UPDATE
                """)
            ).mappings().one()
            
            # Check if transition needed
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
                
                # Just record new strategy, no ledger entry needed
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
    
    def get_future_block_priorities(conn, time_id: int) -> dict:
        """Get time block and priorities for when barrels will arrive."""
        logger.debug("Getting future block priorities for barrel arrival")

        future_block = conn.execute(sqlalchemy.text("""
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
                    SELECT barrel_time_id
                    FROM game_time
                    WHERE time_id = :time_id
                )
            )
            SELECT 
                stb.block_id,
                tb.name as block_name,
                fi.in_game_day,
                stb.buffer_multiplier,
                stb.dark_buffer_multiplier,
                s.name as strategy_name
            FROM future_info fi
            JOIN time_blocks tb 
                ON fi.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
            JOIN strategy_time_blocks stb 
                ON tb.block_id = stb.time_block_id
                AND fi.strategy_id = stb.strategy_id
                AND fi.in_game_day = stb.day_name
            JOIN strategies s ON s.strategy_id = fi.strategy_id
        """), {"time_id": time_id}).mappings().one()

        logger.debug(
            f"Got future block info - "
            f"day: {future_block['in_game_day']}, "
            f"block: {future_block['block_name']}, "
            f"strategy: {future_block['strategy_name']}, "
            f"buffer: {future_block['buffer_multiplier']}, "
            f"dark_buffer: {future_block['dark_buffer_multiplier']}"
        )
        
        return future_block
    
    @staticmethod
    def filter_barrels_by_strategy(barrels: list, strategy: str) -> list:
        """Filter and sort barrels based on strategy restrictions."""
        # Filter out MINI barrels first
        valid_barrels = [b for b in barrels if not b['sku'].startswith('MINI')]
        
        if strategy == 'PREMIUM':
            filtered = [b for b in valid_barrels if 'SMALL' in b['sku']]
        elif strategy == 'PENETRATION':
            medium = [b for b in valid_barrels if 'MEDIUM' in b['sku']]
            small = [b for b in valid_barrels if 'SMALL' in b['sku']]
            filtered = medium + small
        else:  # TIERED or DYNAMIC
            large = [b for b in valid_barrels if 'LARGE' in b['sku']]
            medium = [b for b in valid_barrels if 'MEDIUM' in b['sku']]
            small = [b for b in valid_barrels if 'SMALL' in b['sku']]
            filtered = large + medium + small
                
        return filtered

    @staticmethod
    def get_color_needs(conn, block: dict) -> dict:
        """Calculate color needs based on future potions that need to sell."""
        logger.debug(f"Calculating color needs for block {block['block_id']}")
        
        # Get current state (potions and ML)
        current_state = conn.execute(sqlalchemy.text("""
            SELECT p.potion_id, p.sku, p.current_quantity,
                p.red_ml, p.green_ml, p.blue_ml, p.dark_ml,
                cs.max_potions
            FROM potions p
            CROSS JOIN current_state cs
        """)).mappings().all()
        
        logger.debug(f"Current state - max potions: {current_state[0]['max_potions']}")
        
        # Get potion needs in priority order
        potion_priorities = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    p.potion_id, p.sku,
                    p.red_ml, p.green_ml, p.blue_ml, p.dark_ml,
                    bpp.sales_mix,
                    s.max_potions_per_sku
                FROM block_potion_priorities bpp
                JOIN potions p ON bpp.potion_id = p.potion_id
                JOIN strategies s ON s.strategy_id = 
                    (SELECT strategy_id FROM active_strategy 
                    ORDER BY activated_at DESC LIMIT 1)
                WHERE bpp.block_id = :block_id
                ORDER BY bpp.priority_order
            """),
            {"block_id": block['block_id']}
        ).mappings().all()
        
        logger.debug(f"Found {len(potion_priorities)} potions in priority order")
        
        # Calculate ML needed for each color
        color_needs = {'RED': 0, 'GREEN': 0, 'BLUE': 0, 'DARK': 0}
        
        for potion in potion_priorities:
            # Calculate target quantity based on sales mix and max allowed
            target_quantity = min(
                int(potion['sales_mix'] * current_state[0]['max_potions']),
                potion['max_potions_per_sku']
            )
            
            # Adjust for current inventory
            current_quantity = next(
                (p['current_quantity'] for p in current_state 
                if p['potion_id'] == potion['potion_id']), 
                0
            )
            needed_quantity = max(0, target_quantity - current_quantity)
            
            logger.debug(
                f"Potion {potion['sku']} - "
                f"target: {target_quantity}, "
                f"current: {current_quantity}, "
                f"needed: {needed_quantity}"
            )
            
            # Add ML needs for each color with buffer
            for color, ml, multiplier in [
                ('RED', potion['red_ml'], block['buffer_multiplier']),
                ('GREEN', potion['green_ml'], block['buffer_multiplier']),
                ('BLUE', potion['blue_ml'], block['buffer_multiplier']),
                ('DARK', potion['dark_ml'], block['dark_buffer_multiplier'])
            ]:
                if ml > 0:
                    ml_needed = ml * needed_quantity * multiplier
                    color_needs[color] += ml_needed
        
        # Adjust for current ML inventory
        logger.debug("Current ML inventory:")
        for color in color_needs:
            current_ml = current_state[0][f"{color.lower()}_ml"]
            original_need = color_needs[color]
            color_needs[color] = max(0, color_needs[color] - current_ml)
            
            logger.debug(
                f"{color}: {original_need:.0f} needed - "
                f"{current_ml} current = "
                f"{color_needs[color]:.0f} adjusted need"
            )
        
        # Remove colors with no needs
        result = {k: v for k, v in color_needs.items() if v > 0}
        
        logger.debug(f"Final color needs: {result}")
        return result


    @staticmethod
    def plan_barrel_purchases(
        conn,
        wholesale_catalog: list,
        time_id: int
    ) -> list:
        """Plan purchases based on future needs and strategy."""

        # Get current state
        state = conn.execute(sqlalchemy.text(
            "SELECT * FROM current_state"
        )).mappings().one()
        
        # Get future block info and priorities
        future_block = BarrelManager.get_future_block_priorities(conn, time_id)

        # Calculate color needs based on future block
        color_needs = BarrelManager.get_color_needs(conn, future_block)
        
        # Plan purchases considering constraints
        purchases = BarrelManager.calculate_purchase_quantities(
            wholesale_catalog,
            color_needs,
            state['gold'],
            state['max_ml'] - state['total_ml'],
            future_block['strategy_name']
        )
        
        if purchases:
            logger.info(
                f"Planned purchases - "
                f"total SKUs: {len(purchases)}, "
                f"total quantity: {sum(p['quantity'] for p in purchases)}"
            )
        else:
            logger.debug("No barrel purchases needed")
            
        return purchases

    @staticmethod
    def calculate_purchase_quantities(
        catalog: list,
        color_needs: dict,
        available_gold: int,
        available_capacity: int,
        strategy: str
    ) -> list:
        """Calculate purchases considering strategy and forward-looking needs."""
        logger.debug(
            f"Planning purchases - "
            f"gold: {available_gold}, "
            f"capacity: {available_capacity}"
        )
        
        # Filter to allowed barrel sizes for strategy
        filtered_barrels = BarrelManager.filter_barrels_by_strategy(catalog, strategy)
        
        remaining_gold = available_gold
        remaining_capacity = available_capacity
        purchase_quantities = {}  # Track quantities per SKU
        
        # Keep trying to buy until can't 
        can_purchase = True
        while can_purchase and remaining_gold > 0 and remaining_capacity > 0:
            can_purchase = False
            
            # Try each color in needs
            for color, needed_ml in color_needs.items():
                if needed_ml <= 0:
                    continue
                    
                # Get barrels for this color
                color_barrels = [b for b in filtered_barrels if color in b['sku']]
                
                # Try each barrel size
                for barrel in color_barrels:
                    if barrel['price'] <= remaining_gold and \
                    barrel['ml_per_barrel'] <= remaining_capacity:
                        # Track quantity for this SKU
                        purchase_quantities[barrel['sku']] = \
                            purchase_quantities.get(barrel['sku'], 0) + 1
                        
                        remaining_gold -= barrel['price']
                        remaining_capacity -= barrel['ml_per_barrel']
                        color_needs[color] -= barrel['ml_per_barrel']
                        can_purchase = True
                        break  # Move to next color
        
        # Convert quantities dict to list of purchases
        purchases = [
            {"sku": sku, "quantity": qty}
            for sku, qty in purchase_quantities.items()
        ]
        
        logger.debug(f"Planned {len(purchases)} purchases")
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
        
        logger.debug("Purchase constraints validated successfully")
    
    @staticmethod
    def process_barrel_purchase(conn, barrel: dict, barrel_id: int, time_id: int, visit_id: int) -> int:
        """Records a barrel purchase with ledger entry."""
        color_name = barrel['sku'].split('_')[1]
        total_cost = barrel['price'] * barrel['quantity']
        total_ml = barrel['ml_per_barrel'] * barrel['quantity']
        
        # Lock ledger entries first, then calculate totals
        state = conn.execute(
            sqlalchemy.text("""
                WITH locked_ledger AS (
                    SELECT entry_id, gold_change, ml_change
                    FROM ledger_entries
                    FOR UPDATE
                )
                SELECT 
                    COALESCE(SUM(gold_change), 0) as gold,
                    COALESCE(SUM(ml_change), 0) as total_ml
                FROM locked_ledger
            """)
        ).mappings().one()

        if state['gold'] < total_cost:
            raise HTTPException(status_code=400, detail="Insufficient gold")

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

        # Create ledger entry in same transaction
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

        return purchase_id

class BottlerManager:
    """Handles potion bottling planning and processing."""
    
    @staticmethod
    def get_bottling_priorities(conn) -> list:
        """Gets prioritized potions for bottling based on future time block."""
        # Get current time
        current_time = TimeManager.get_current_time(conn)
        
        logger.debug(f"Getting bottling priorities for future time block")
    
        priorities = conn.execute(
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
                        WHERE time_id = :time_id
                    )
                ),
                time_block_info AS (
                    SELECT 
                        tb.block_id
                    FROM future_info fi
                    JOIN time_blocks tb 
                        ON fi.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
                )
                SELECT 
                    p.potion_id,
                    COALESCE(p.red_ml, 0) as red_ml,
                    COALESCE(p.green_ml, 0) as green_ml,
                    COALESCE(p.blue_ml, 0) as blue_ml,
                    COALESCE(p.dark_ml, 0) as dark_ml,
                    COALESCE(p.current_quantity, 0) as inventory,
                    bpp.priority_order,
                    bpp.sales_mix,
                    s.max_potions_per_sku,
                    fi.in_game_day,
                    tbi.block_id
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
            """),
            {"time_id": current_time['time_id']}
        ).mappings().all()
        
        if priorities:
            logger.debug(
                f"Got priorities for future block - "
                f"day: {priorities[0]['in_game_day']}, "
                f"block: {priorities[0]['block_id']}, "
                f"count: {len(priorities)}"
            )
        else:
            logger.error("No bottling priorities found for future time block")
        
        return priorities
    
    @staticmethod
    def calculate_possible_potions(
        priorities: List[Dict],
        available_ml: Dict[str, int],
        available_capacity: int
    ) -> List[Dict]:
        """
        Calculate potion bottling plan with even distribution based on priorities.
        Tries to bottle one potion at a time following priority order and sales mix.
        """
        logger.debug(
            f"Planning bottling - "
            f"capacity: {available_capacity}, "
            f"available ml: {available_ml}"
        )

        # Early return if no ML available
        if all(ml == 0 for ml in available_ml.values()):
            logger.debug("No ML available for bottling")
            return []
            
        # Early return if no capacity
        if available_capacity <= 0:
            logger.debug("No capacity available for bottling")
            return []
        
        bottling_plan = {}  # Track quantities per potion type
        remaining_ml = available_ml.copy()
        remaining_capacity = available_capacity
        
        # Keep bottling until can't 
        can_bottle = True
        while can_bottle and remaining_capacity > 0:
            can_bottle = False
            
            # Try each potion in priority order
            for potion in priorities:
                # Create potion type array from individual ML values
                potion_type = [
                    potion['red_ml'],
                    potion['green_ml'],
                    potion['blue_ml'],
                    potion['dark_ml']
                ]
                potion_key = str(potion_type)  # Use as dict key
                
                # Skip if hit max for this potion
                current_quantity = bottling_plan.get(
                    potion_key, 
                    {"quantity": 0}
                )["quantity"]
                
                max_allowed = min(
                    potion['max_potions_per_sku'] - potion.get('inventory', 0),
                    int(potion['sales_mix'] * available_capacity) - potion.get('inventory', 0)
                )
                
                if current_quantity >= max_allowed:
                    continue
                    
                # Check if there is resources for one potion
                can_make = True
                for color, ml in [
                    ("red_ml", potion['red_ml']),
                    ("green_ml", potion['green_ml']),
                    ("blue_ml", potion['blue_ml']),
                    ("dark_ml", potion['dark_ml'])
                ]:
                    if ml > 0 and remaining_ml.get(color, 0) < ml:
                        can_make = False
                        break
                
                if can_make and remaining_capacity > 0:
                    # Add one potion
                    if potion_key not in bottling_plan:
                        bottling_plan[potion_key] = {
                            "potion_type": potion_type,
                            "quantity": 0
                        }
                    
                    bottling_plan[potion_key]["quantity"] += 1
                    
                    # Update remaining resources
                    remaining_capacity -= 1
                    for color, ml in [
                        ("red_ml", potion['red_ml']),
                        ("green_ml", potion['green_ml']),
                        ("blue_ml", potion['blue_ml']),
                        ("dark_ml", potion['dark_ml'])
                    ]:
                        if ml > 0:
                            remaining_ml[color] = remaining_ml.get(color, 0) - ml
                    
                    can_bottle = True
        
        # Convert plan to list format
        result = list(bottling_plan.values())
        
        if result:
            logger.info(
                f"Bottling plan complete - "
                f"total types: {len(result)}, "
                f"total potions: {sum(p['quantity'] for p in result)}"
            )
        else:
            logger.debug("No potions can be bottled")
            
        return result

    @staticmethod
    def process_bottling(conn, potion_data: Dict, time_id: int) -> None:
        """Processes potion bottling with ledger entries."""
        # First get and lock the potion
        potion = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    potion_id,
                    current_quantity,
                    red_ml,
                    green_ml,
                    blue_ml,
                    dark_ml
                FROM potions 
                WHERE ARRAY[red_ml, green_ml, blue_ml, dark_ml] = :potion_type
                FOR UPDATE
            """),
            {"potion_type": potion_data['potion_type']}
        ).mappings().one()

        # Get and lock the ledger entries to check ml availability
        ml_totals = conn.execute(
            sqlalchemy.text("""
                WITH locked_entries AS (
                    SELECT 
                        color_id,
                        ml_change
                    FROM ledger_entries
                    FOR UPDATE
                )
                SELECT 
                    c.color_name,
                    COALESCE(SUM(le.ml_change), 0) as ml_available
                FROM color_definitions c
                LEFT JOIN locked_entries le ON c.color_id = le.color_id
                GROUP BY c.color_name
            """)
        ).mappings().all()

        # Convert to dict for easier access
        ml_available = {
            row['color_name'].lower() + '_ml': row['ml_available']
            for row in ml_totals
        }

        # Log current state
        logger.debug(
            f"Current ml levels - "
            f"red: {ml_available.get('red_ml', 0)}, "
            f"green: {ml_available.get('green_ml', 0)}, "
            f"blue: {ml_available.get('blue_ml', 0)}, "
            f"dark: {ml_available.get('dark_ml', 0)}"
        )

        # Validate resources
        for color, amount in [
            ('red_ml', ml_available.get('red_ml', 0)), 
            ('green_ml', ml_available.get('green_ml', 0)),
            ('blue_ml', ml_available.get('blue_ml', 0)), 
            ('dark_ml', ml_available.get('dark_ml', 0))
        ]:
            color_index = 0 if color == 'red_ml' else 1 if color == 'green_ml' else 2 if color == 'blue_ml' else 3
            ml_needed = potion_data['potion_type'][color_index] * potion_data['quantity']
            
            if ml_needed > 0:
                logger.debug(f"Checking {color}: need {ml_needed}, have {amount}")
                
            if ml_needed > amount:
                logger.error(
                    f"Insufficient {color} - "
                    f"needed: {ml_needed}, "
                    f"available: {amount}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient {color}"
                )

        # Create potion change record
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id,
                    entry_type,
                    potion_change,
                    potion_id
                )
                VALUES (
                    :time_id,
                    'POTION_BOTTLED',
                    :potion_change,
                    :potion_id
                )
            """),
            {
                "time_id": time_id,
                "potion_change": potion_data['quantity'],
                "potion_id": potion['potion_id']
            }
        )

        # Process ml consumption entries
        for idx, (color, ml) in enumerate([
            ('RED', potion_data['potion_type'][0]),
            ('GREEN', potion_data['potion_type'][1]),
            ('BLUE', potion_data['potion_type'][2]),
            ('DARK', potion_data['potion_type'][3])
        ]):
            if ml > 0:
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO ledger_entries (
                            time_id,
                            entry_type,
                            ml_change,
                            color_id,
                            potion_id
                        )
                        VALUES (
                            :time_id,
                            'POTION_BOTTLED',
                            :ml_change,
                            (SELECT color_id FROM color_definitions WHERE color_name = :color),
                            :potion_id
                        )
                    """),
                    {
                        "time_id": time_id,
                        "ml_change": -ml * potion_data['quantity'],
                        "color": color,
                        "potion_id": potion['potion_id']
                    }
                )

        # Update potion inventory
        conn.execute(
            sqlalchemy.text("""
                UPDATE potions
                SET current_quantity = current_quantity + :quantity
                WHERE potion_id = :potion_id
            """),
            {
                "quantity": potion_data['quantity'],
                "potion_id": potion['potion_id']
            }
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
        """Validates cart exists and is not checked out with row lock."""
        result = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    c.cart_id,
                    c.visit_id,
                    c.checked_out
                FROM carts c
                WHERE c.cart_id = :cart_id
                FOR UPDATE
            """),
            {"cart_id": cart_id}
        ).mappings().first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        if result['checked_out']:
            raise HTTPException(status_code=400, detail="Cart already checked out")
        
        return dict(result)

    @staticmethod
    def update_cart_item(conn, cart_id: int, item_sku: str, quantity: int, time_id: int, visit_id: int) -> None:
        """Updates cart item quantity with proper locking."""
        # Lock potion row when checking inventory
        potion = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    potion_id,
                    current_quantity,
                    base_price
                FROM potions
                WHERE sku = :sku
                FOR UPDATE
            """),
            {"sku": item_sku}
        ).mappings().one()
        
        if potion['current_quantity'] < quantity:
            raise HTTPException(status_code=400, detail="Insufficient quantity")
        
        line_total = potion['base_price'] * quantity
        
        # Lock cart_items row
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
                """),
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
        """
        Process cart checkout with proper locking and transaction handling.
        Uses serializable isolation level with explicit locks to prevent race conditions.
        """
        try:
            # First lock the cart and get items with SELECT FOR UPDATE
            cart_items = conn.execute(
                sqlalchemy.text("""
                    WITH locked_cart AS (
                        SELECT cart_id, checked_out 
                        FROM carts 
                        WHERE cart_id = :cart_id
                        FOR UPDATE
                    )
                    SELECT 
                        ci.potion_id,
                        ci.quantity,
                        ci.unit_price,
                        ci.line_total,
                        p.current_quantity,
                        p.sku
                    FROM cart_items ci
                    JOIN potions p ON ci.potion_id = p.potion_id
                    JOIN locked_cart lc ON ci.cart_id = lc.cart_id
                    WHERE ci.cart_id = :cart_id
                    FOR UPDATE OF p
                """),
                {"cart_id": cart_id}
            ).mappings().all()

            if not cart_items:
                raise HTTPException(status_code=400, detail="Cart is empty")

            # Calculate totals
            total_potions = sum(item['quantity'] for item in cart_items)
            total_gold = sum(item['line_total'] for item in cart_items)

            # Verify inventory availability
            for item in cart_items:
                if item['current_quantity'] < item['quantity']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient quantity for {item['sku']}"
                    )

            # Update inventory and create ledger entries atomically
            for item in cart_items:
                # Update potion inventory
                conn.execute(
                    sqlalchemy.text("""
                        UPDATE potions
                        SET current_quantity = current_quantity - :quantity
                        WHERE potion_id = :potion_id
                    """),
                    {
                        "quantity": item['quantity'],
                        "potion_id": item['potion_id']
                    }
                )

                # Create ledger entry
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO ledger_entries (
                            time_id,
                            entry_type,
                            cart_id,
                            potion_id,
                            gold_change,
                            potion_change
                        ) VALUES (
                            :time_id,
                            'POTION_SOLD',
                            :cart_id,
                            :potion_id,
                            :gold_change,
                            :potion_change
                        )
                    """),
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
                        checked_out_at = CURRENT_TIMESTAMP,
                        payment = :payment,
                        total_potions = :total_potions,
                        total_gold = :total_gold,
                        purchase_success = true
                    WHERE cart_id = :cart_id
                """),
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

        except sqlalchemy.exc.SerializationFailure as e:
            logger.error(f"Serialization failure during checkout: {str(e)}")
            raise HTTPException(
                status_code=409,
                detail="Transaction conflict"
            )
        except Exception as e:
            logger.error(f"Checkout failed: {str(e)}")
            raise

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
    def process_capacity_upgrade(conn, potion_capacity: int, ml_capacity: int, time_id: int) -> None:
        """Process capacity upgrade with ledger entries and strategy transition."""
        total_cost = (potion_capacity + ml_capacity) * 1000
        
        # Lock ledger entries first and get current state
        current_state = conn.execute(
            sqlalchemy.text("""
                WITH locked_ledger AS (
                    SELECT entry_id, gold_change, ml_change,
                        ml_capacity_change, potion_capacity_change
                    FROM ledger_entries
                    FOR UPDATE
                )
                SELECT
                    COALESCE(SUM(gold_change), 0) as gold,
                    COALESCE(SUM(ml_capacity_change), 0) as ml_capacity_units,
                    COALESCE(SUM(potion_capacity_change), 0) as potion_capacity_units
                FROM locked_ledger
            """)
        ).mappings().one()
        
        if current_state['gold'] < total_cost:
            raise HTTPException(
                status_code=400,
                detail="Insufficient gold for capacity upgrade"
            )

        # Create capacity upgrade ledger entry
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
        
        # Calculate new totals and check for strategy transition
        new_units = {
            'ml_capacity_units': current_state['ml_capacity_units'] + ml_capacity,
            'potion_capacity_units': current_state['potion_capacity_units'] + potion_capacity
        }
        
        # Lock and check current strategy in one atomic operation
        current_strategy = conn.execute(
            sqlalchemy.text("""
                WITH current_strategy AS (
                    SELECT 
                        ast.strategy_id,
                        s.name as strategy_name
                    FROM active_strategy ast
                    JOIN strategies s ON ast.strategy_id = s.strategy_id
                    WHERE ast.activated_at = (
                        SELECT MAX(activated_at)
                        FROM active_strategy
                    )
                    FOR UPDATE
                )
                SELECT 
                    cs.strategy_id,
                    cs.strategy_name,
                    st.to_strategy_id
                FROM current_strategy cs
                LEFT JOIN strategy_transitions st ON cs.strategy_id = st.from_strategy_id
                WHERE cs.strategy_name != 'DYNAMIC'
            """)
        ).mappings().first()
        
        if current_strategy:
            should_transition = False
            new_strategy_id = None
            
            if (current_strategy['strategy_name'] == 'PENETRATION' and
                new_units['ml_capacity_units'] >= 2 and
                new_units['potion_capacity_units'] >= 2):
                should_transition = True
                new_strategy_id = current_strategy['to_strategy_id']
                
            elif (current_strategy['strategy_name'] == 'TIERED' and
                new_units['ml_capacity_units'] >= 4 and
                new_units['potion_capacity_units'] >= 4):
                should_transition = True
                new_strategy_id = current_strategy['to_strategy_id']
                
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
