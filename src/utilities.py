import sqlalchemy
import logging
import json
from fastapi import HTTPException
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class LedgerManager:
    """Handles ledger operations and state management."""
    
    VALID_ENTRY_TYPES = {
        'BARREL_PURCHASE',
        'POTION_BOTTLED',
        'POTION_SOLD',
        'CAPACITY_UPGRADE',
        'GOLD_CHANGE',
        'ML_ADJUSTMENT',
        'STRATEGY_CHANGE',
        'ADMIN_CHANGE'
    }
    
    @staticmethod
    def create_ledger_entry(
        conn,
        time_id: int,
        entry_type: str,
        gold_change: Optional[int] = None,
        ml_change: Optional[int] = None,
        potion_change: Optional[int] = None,
        color_id: Optional[int] = None,
        barrel_purchase_id: Optional[int] = None,
        cart_id: Optional[int] = None,
        potion_id: Optional[int] = None
    ) -> int:
        """
        Creates a ledger entry and returns its ID.
        Validates entry type and ensures at least one change value is provided.
        """
        if entry_type not in LedgerManager.VALID_ENTRY_TYPES:
            raise ValueError(f"Invalid entry type: {entry_type}")
            
        if not any([gold_change, ml_change, potion_change]):
            raise ValueError("At least one change value must be provided")
            
        entry_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO ledger_entries (
                    time_id, entry_type, gold_change, ml_change, potion_change,
                    color_id, barrel_purchase_id, cart_id, potion_id
                ) VALUES (
                    :time_id, :entry_type, :gold_change, :ml_change, :potion_change,
                    :color_id, :barrel_purchase_id, :cart_id, :potion_id
                )
                RETURNING entry_id
            """),
            {
                "time_id": time_id,
                "entry_type": entry_type,
                "gold_change": gold_change,
                "ml_change": ml_change,
                "potion_change": potion_change,
                "color_id": color_id,
                "barrel_purchase_id": barrel_purchase_id,
                "cart_id": cart_id,
                "potion_id": potion_id
            }
        ).scalar_one()
            
        return entry_id

class StateValidator:
    """Handles state validation and verification."""
    
    @staticmethod
    def get_current_state(conn) -> Dict:
        """
        Gets current state from current_state view.
        Returns complete game state including gold, ml, potions, and capacities.
        """
        return conn.execute(
            sqlalchemy.text("SELECT * FROM current_state")
        ).mappings().one()

    @staticmethod
    def verify_reset_state(conn) -> bool:
        """
        Verifies game state matches initial conditions after reset.
        Returns True if state matches initial conditions, False otherwise.
        """
        state = StateValidator.get_current_state(conn)
        
        if state['gold'] != 100:
            return False
            
        if state['total_potions'] != 0:
            return False
            
        if state['total_ml'] != 0:
            return False
            
        strategy_id = conn.execute(
            sqlalchemy.text("""
                SELECT strategy_id 
                FROM active_strategy
                ORDER BY activated_at DESC 
                LIMIT 1
            """)
        ).scalar_one()
        
        premium_id = conn.execute(
            sqlalchemy.text("""
                SELECT strategy_id 
                FROM strategies 
                WHERE name = 'PREMIUM'
            """)
        ).scalar_one()
            
        if strategy_id != premium_id:
            return False
            
        return True

    @staticmethod
    def verify_resources(
        conn,
        needed_gold: Optional[int] = None,
        needed_ml: Optional[Dict[str, int]] = None,
        needed_potions: Optional[int] = None
    ) -> bool:
        """
        Validates available resources against requested amounts.
        Returns True if sufficient resources exist, False otherwise.
        """
        if needed_gold:
            gold = conn.execute(
                sqlalchemy.text("""
                    SELECT COALESCE(SUM(gold_change), 100) as gold
                    FROM ledger_entries
                """)
            ).scalar_one()
            
            if gold < needed_gold:
                return False
        
        if needed_ml:
            ml_totals = conn.execute(
                sqlalchemy.text("""
                    SELECT 
                        cd.color_name,
                        COALESCE(SUM(le.ml_change), 0) as total_ml
                    FROM color_definitions cd
                    LEFT JOIN ledger_entries le ON cd.color_id = le.color_id
                    GROUP BY cd.color_name
                """)
            ).mappings().all()
            
            ml_dict = {row['color_name'].lower() + '_ml': row['total_ml'] 
                        for row in ml_totals}
            
            for color, needed in needed_ml.items():
                if ml_dict.get(color, 0) < needed:
                    return False
        
        if needed_potions is not None:
            total_potions = conn.execute(
                sqlalchemy.text("""
                    SELECT COALESCE(SUM(potion_change), 0) as total
                    FROM ledger_entries
                """)
            ).scalar_one()
            
            if total_potions + needed_potions > 0:  # Consider capacity
                return False
        
        return True

class TimeManager:
    """Handles game time and strategy transitions."""
    
    @staticmethod
    def record_time(conn, day: str, hour: int) -> bool:
        """
        Records current game time and checks for strategy transitions based on state.
        Returns True if strategy changed, False otherwise.
        """
        time_id = conn.execute(
            sqlalchemy.text("""
                SELECT time_id
                FROM game_time
                WHERE in_game_day = :day AND in_game_hour = :hour
            """),
            {"day": day, "hour": hour}
        ).scalar_one()
        
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
        
        # Check for strategy transition based on current state
        state = conn.execute(
            sqlalchemy.text("""
                WITH current_totals AS (
                    SELECT 
                        COALESCE(SUM(gold_change), 100) as gold,
                        COALESCE(SUM(potion_change), 0) as total_potions,
                        COALESCE(SUM(ml_change), 0) as total_ml
                    FROM ledger_entries
                ),
                current_strat AS (
                    SELECT st.*
                    FROM active_strategy ast
                    JOIN strategy_transitions st ON ast.strategy_id = st.from_strategy_id
                    ORDER BY ast.activated_at DESC
                    LIMIT 1
                )
                SELECT 
                    cs.to_strategy_id,
                    ct.gold >= cs.gold_threshold OR
                    ct.total_potions >= cs.potion_threshold OR
                    ct.total_ml >= cs.ml_threshold as should_transition
                FROM current_strat cs
                CROSS JOIN current_totals ct
                WHERE cs.to_strategy_id IS NOT NULL
            """)
        ).mappings().first()
        
        if state and state['should_transition']:
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

    @staticmethod
    def validate_game_time(day: str, hour: int) -> bool:
        """
        Validates if provided day and hour are valid game time values.
        Returns True if time values are valid, False otherwise.
        """
        valid_days = {
            'Hearthday', 'Crownday', 'Blesseday', 'Soulday',
            'Edgeday', 'Bloomday', 'Arcanaday'
        }
        
        return (
            day in valid_days and
            isinstance(hour, int) and
            hour >= 0 and
            hour <= 22 and
            hour % 2 == 0
        )

class CatalogManager:
    """Handles catalog creation and potion availability."""
    
    @staticmethod
    def get_available_potions(conn) -> list:
        """
        Gets available potions based on current strategy and time block.
        Returns list of available potions with quantity, price, and attributes.
        """
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
            """)
        ).mappings().all()

class BarrelManager:
    """Handles barrel purchase planning and processing."""
    
    @staticmethod
    def get_ml_needs(conn) -> list:
        """
        Calculates ML needs based on current strategy and future time block.
        Returns list of needed ml amounts by color, ordered by priority.
        """
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
                        SELECT barrel_time_id
                        FROM game_time
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                )
                SELECT 
                    cd.color_name,
                    cd.priority_order,
                    SUM(
                        CASE 
                            WHEN cd.color_name = 'RED' THEN p.red_ml
                            WHEN cd.color_name = 'GREEN' THEN p.green_ml
                            WHEN cd.color_name = 'BLUE' THEN p.blue_ml
                            WHEN cd.color_name = 'DARK' THEN p.dark_ml
                        END * bpp.sales_mix
                    ) as ml_needed
                FROM future_info fi
                JOIN time_blocks tb 
                    ON fi.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
                JOIN strategy_time_blocks stb 
                    ON tb.block_id = stb.time_block_id
                    AND fi.strategy_id = stb.strategy_id
                    AND fi.in_game_day = stb.day_name
                JOIN block_potion_priorities bpp 
                    ON stb.block_id = bpp.block_id
                JOIN potions p ON bpp.potion_id = p.potion_id
                CROSS JOIN color_definitions cd
                GROUP BY cd.color_name, cd.priority_order
                ORDER BY cd.priority_order
            """)
        ).mappings().all()

    @staticmethod
    def plan_purchases(needs: list, wholesale_catalog: list, current_state: dict) -> list:
        """Calculate optimal barrel purchases based on needs and constraints."""
        purchases = []
        catalog_dict = {b['sku']: b for b in wholesale_catalog}
        
        available_gold = current_state['gold']
        available_capacity = current_state['max_ml'] - current_state['total_ml']
        
        logger.debug(f"Starting purchase planning with {available_gold} gold and {available_capacity} ml capacity")
        
        for need in needs:
            if need['ml_needed'] <= 0:
                continue
            
            barrel_sizes = ['LARGE', 'MEDIUM', 'SMALL']
            
            for size in barrel_sizes:
                barrel_sku = f"{size}_{need['color_name']}_BARREL"
                barrel = catalog_dict.get(barrel_sku)
                
                if not barrel:
                    continue
                    
                if available_gold < barrel['price']:
                    logger.debug(f"Insufficient gold for {barrel_sku} - need {barrel['price']}, have {available_gold}")
                    continue
                    
                # Calculate maximum possible purchase
                max_by_gold = int(available_gold // barrel['price'])
                max_by_capacity = int(available_capacity // barrel['ml_per_barrel'])
                max_by_need = int((need['ml_needed'] + barrel['ml_per_barrel'] - 1) // barrel['ml_per_barrel'])
                max_by_availability = int(barrel['quantity'])
                
                quantity = min(
                    max_by_gold,
                    max_by_capacity,
                    max_by_need,
                    max_by_availability
                )
                
                if quantity > 0:
                    purchases.append({
                        "sku": barrel_sku,
                        "quantity": int(quantity)
                    })
                    
                    available_gold -= quantity * barrel['price']
                    available_capacity -= quantity * barrel['ml_per_barrel']
                    need['ml_needed'] -= quantity * barrel['ml_per_barrel']
                    
                if need['ml_needed'] <= 0:
                    break
        
        return purchases

    @staticmethod
    def process_barrel_delivery(conn, barrel: dict, time_id: int, visit_id: int) -> None:
        """
        Processes barrel delivery with ledger entries and inventory updates.
        Returns None, raises exception on failure.
        """
        barrel_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO barrel_details (
                    visit_id, sku, ml_per_barrel, potion_type,
                    price, quantity, color_id
                )
                VALUES (
                    :visit_id, :sku, :ml_per_barrel, :potion_type,
                    :price, :quantity,
                    (SELECT color_id FROM color_definitions 
                     WHERE color_name = split_part(:sku, '_', 2))
                )
                RETURNING barrel_id
            """),
            {
                "visit_id": visit_id,
                "sku": barrel["sku"],
                "ml_per_barrel": barrel["ml_per_barrel"],
                "potion_type": json.dumps(barrel["potion_type"]),
                "price": barrel["price"],
                "quantity": barrel["quantity"]
            }
        ).scalar_one()
        
        purchase_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO barrel_purchases (
                    visit_id, time_id, barrel_id, quantity,
                    total_cost, ml_added, color_id, purchase_success
                )
                VALUES (
                    :visit_id, :time_id, :barrel_id, :quantity,
                    :total_cost, :ml_added,
                    (SELECT color_id FROM color_definitions 
                     WHERE color_name = split_part(:sku, '_', 2)),
                    true
                )
                RETURNING purchase_id
            """),
            {
                "visit_id": visit_id,
                "time_id": time_id,
                "barrel_id": barrel_id,
                "quantity": barrel['quantity'],
                "total_cost": barrel['price'] * barrel['quantity'],
                "ml_added": barrel['ml_per_barrel'] * barrel['quantity'],
                "sku": barrel['sku']
            }
        ).scalar_one()
        
        LedgerManager.create_ledger_entry(
            conn=conn,
            time_id=time_id,
            entry_type='BARREL_PURCHASE',
            gold_change=-(barrel['price'] * barrel['quantity']),
            ml_change=barrel['ml_per_barrel'] * barrel['quantity'],
            color_id=conn.execute(
                sqlalchemy.text("""
                    SELECT color_id 
                    FROM color_definitions 
                    WHERE color_name = split_part(:sku, '_', 2)
                """),
                {"sku": barrel['sku']}
            ).scalar_one(),
            barrel_purchase_id=purchase_id
        )

class BottlerManager:
    """Handles potion bottling planning and processing."""
    
    @staticmethod
    def get_bottling_priorities(conn) -> list:
        """
        Gets prioritized potions for bottling based on current strategy.
        Returns list of potions with their mix ratios and priorities.
        """
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
            """)
        ).mappings().all()

    @staticmethod
    def calculate_possible_potions(
        priorities: list,
        available_ml: dict,
        available_capacity: int
    ) -> list:
        """
        Calculates maximum potions that can be made with available resources.
        Returns list of possible potions and their quantities.
        """
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
        """
        Processes potion bottling with ledger entries and inventory updates.
        Returns None, raises exception on failure.
        """
        potion_id = conn.execute(
            sqlalchemy.text("""
                SELECT potion_id
                FROM potions
                WHERE ARRAY[red_ml, green_ml, blue_ml, dark_ml] = :potion_type
            """),
            {"potion_type": potion_data['potion_type']}
        ).scalar_one()
        
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
        
        for i, color in enumerate(['RED', 'GREEN', 'BLUE', 'DARK']):
            ml_used = potion_data['potion_type'][i] * potion_data['quantity']
            if ml_used > 0:
                color_id = conn.execute(
                    sqlalchemy.text("""
                        SELECT color_id 
                        FROM color_definitions 
                        WHERE color_name = :color
                    """),
                    {"color": color}
                ).scalar_one()
                
                LedgerManager.create_ledger_entry(
                    conn=conn,
                    time_id=time_id,
                    entry_type='POTION_BOTTLED',
                    ml_change=-ml_used,
                    color_id=color_id,
                    potion_id=potion_id
                )
        
        LedgerManager.create_ledger_entry(
            conn=conn,
            time_id=time_id,
            entry_type='POTION_BOTTLED',
            potion_change=potion_data['quantity'],
            potion_id=potion_id
        )

class CartManager:
    """Handles cart operations and customer interactions."""
    
    @staticmethod
    def record_customer_visit(conn, visit_id: int, customers: list, time_id: int) -> None:
        """
        Records customer visit and individual customers in the database.
        Returns None, raises exception on failure.
        """
        visit_record_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO public.customer_visits (
                    visit_id,
                    time_id,
                    customers
                ) VALUES (
                    :visit_id,
                    :time_id,
                    :customers
                )
                RETURNING visit_record_id
            """),
            {
                "visit_id": visit_id,
                "time_id": time_id,
                "customers": json.dumps([dict(c) for c in customers])
            }
        ).scalar_one()
        
        for customer in customers:
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO public.customers (
                        visit_record_id,
                        time_id,
                        customer_name,
                        character_class,
                        level
                    ) VALUES (
                        :visit_record_id,
                        :time_id,
                        :name,
                        :class,
                        :level
                    )
                """),
                {
                    "visit_record_id": visit_record_id,
                    "time_id": time_id,
                    "name": customer.customer_name,
                    "class": customer.character_class,
                    "level": customer.level
                }
            )

    @staticmethod
    def create_cart(conn, customer: dict, time_id: int) -> int:
        """
        Creates new cart for customer.
        Returns cart_id of created cart.
        """
        result = conn.execute(
            sqlalchemy.text("""
                SELECT customer_id
                FROM public.customers
                WHERE customer_name = :name 
                AND character_class = :class
                AND level = :level
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {
                "name": customer['customer_name'],
                "class": customer['character_class'],
                "level": customer['level']
            }
        ).scalar_one()
        
        cart_id = conn.execute(
            sqlalchemy.text("""
                INSERT INTO public.carts (
                    customer_id,
                    time_id,
                    checked_out,
                    total_potions,
                    total_gold
                ) VALUES (
                    :customer_id,
                    :time_id,
                    false,
                    0,
                    0
                )
                RETURNING cart_id
            """),
            {
                "customer_id": result,
                "time_id": time_id
            }
        ).scalar_one()
        
        return cart_id

    @staticmethod
    def validate_cart_status(conn, cart_id: int) -> dict:
        """
        Validates cart exists and is not checked out.
        Returns cart details if valid, raises HTTPException otherwise.
        """
        result = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    c.cart_id,
                    c.checked_out,
                    c.customer_id,
                    cust.customer_name,
                    cust.character_class,
                    cust.level
                FROM public.carts c
                JOIN public.customers cust ON c.customer_id = cust.customer_id
                WHERE c.cart_id = :cart_id
            """),
            {"cart_id": cart_id}
        ).mappings().one()
        
        if result['checked_out']:
            raise HTTPException(
                status_code=400,
                detail="Cart is already checked out"
            )
            
        return dict(result)

    @staticmethod
    def update_cart_item(conn, cart_id: int, item_sku: str, quantity: int, time_id: int) -> None:
        """
        Adds or updates item in cart.
        Returns None, raises exception if potion unavailable or insufficient quantity.
        """
        potion = conn.execute(
            sqlalchemy.text("""
                SELECT 
                    potion_id,
                    current_quantity,
                    base_price
                FROM public.potions
                WHERE sku = :sku
            """),
            {"sku": item_sku}
        ).mappings().one()
        
        if potion['current_quantity'] < quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient quantity in inventory"
            )
        
        line_total = potion['base_price'] * quantity
        conn.execute(
            sqlalchemy.text("""
                INSERT INTO public.cart_items (
                    cart_id,
                    potion_id,
                    time_id,
                    quantity,
                    unit_price,
                    line_total
                ) VALUES (
                    :cart_id,
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
                "potion_id": potion['potion_id'],
                "time_id": time_id,
                "quantity": quantity,
                "price": potion['base_price'],
                "line_total": line_total
            }
        )

    @staticmethod
    def process_checkout(
        conn,
        cart_id: int,
        payment: str,
        time_id: int
    ) -> dict:
        """
        Processes cart checkout with ledger entries and inventory updates.
        Returns checkout summary with totals.
        """
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
            """),
            {"cart_id": cart_id}
        ).mappings().all()
        
        if not items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        total_potions = sum(item['quantity'] for item in items)
        total_gold = sum(item['line_total'] for item in items)
        
        for item in items:
            if item['current_quantity'] < item['quantity']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity for {item['sku']}"
                )
        
        for item in items:
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
            
            LedgerManager.create_ledger_entry(
                conn=conn,
                time_id=time_id,
                entry_type='POTION_SOLD',
                cart_id=cart_id,
                potion_id=item['potion_id'],
                gold_change=item['line_total'],
                potion_change=-item['quantity']
            )
        
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

class InventoryManager:
    """Handles inventory state and capacity management."""
    
    @staticmethod
    def get_inventory_state(conn) -> dict:
        """Get current inventory state from ledger."""

        return conn.execute(
            sqlalchemy.text("""
                WITH ledger_totals AS (
                    SELECT
                        COALESCE(SUM(l.gold_change), 100) as gold,
                        COALESCE(SUM(l.ml_change), 0) as total_ml,
                        COALESCE(SUM(l.potion_change), 0) as total_potions,
                        COUNT(*) FILTER (
                            WHERE l.entry_type = 'CAPACITY_UPGRADE' 
                            AND l.potion_change IS NOT NULL
                        ) as potion_upgrades,
                        COUNT(*) FILTER (
                            WHERE l.entry_type = 'CAPACITY_UPGRADE' 
                            AND l.ml_change IS NOT NULL
                        ) as ml_upgrades
                    FROM public.ledger_entries l
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
            """)
        ).mappings().one()
    
    @staticmethod
    def get_capacity_purchase_plan(conn, state: dict) -> dict:
        """Determine capacity purchases based on thresholds and current state."""
        potion_usage = state['total_potions'] / state['max_potions']
        ml_usage = state['total_ml'] / state['max_ml']
        
        threshold = conn.execute(
            sqlalchemy.text("""
                SELECT *
                FROM public.capacity_upgrade_thresholds t
                WHERE 
                    -- Check capacity unit ranges
                    t.min_potion_units <= :current_potion_units
                    AND (t.max_potion_units IS NULL OR t.max_potion_units >= :current_potion_units)
                    AND t.min_ml_units <= :current_ml_units
                    AND (t.max_ml_units IS NULL OR t.max_ml_units >= :current_ml_units)
                    -- Check gold threshold
                    AND t.gold_threshold <= :current_gold
                    -- Check inventory threshold if required
                    AND (
                        NOT t.requires_inventory_check
                        OR (
                            :capacity_usage >= t.capacity_check_threshold
                            OR :ml_usage >= t.capacity_check_threshold
                        )
                    )
                ORDER BY t.priority_order DESC
                LIMIT 1
            """),
            {
                "current_potion_units": state['potion_capacity_units'],
                "current_ml_units": state['ml_capacity_units'],
                "current_gold": state['gold'],
                "capacity_usage": potion_usage,
                "ml_usage": ml_usage
            }
        ).mappings().first()
        
        if threshold:
            logger.debug(
                f"Found capacity upgrade threshold {threshold['threshold_id']} "
                f"with priority {threshold['priority_order']}"
            )
            return {
                "potion_capacity": threshold['potion_capacity_purchase'],
                "ml_capacity": threshold['ml_capacity_purchase']
            }
        
        logger.debug("No capacity upgrade threshold met")
        return {
            "potion_capacity": 0,
            "ml_capacity": 0
        }

    @staticmethod
    def process_capacity_upgrade(
        conn,
        potion_capacity: int,
        ml_capacity: int,
        time_id: int
    ) -> None:
        """Process capacity upgrade with ledger entries."""
        total_cost = (potion_capacity + ml_capacity) * 1000
        
        # Validate gold availability
        current_gold = conn.execute(
            sqlalchemy.text("""
                SELECT COALESCE(SUM(l.gold_change), 100) as gold
                FROM public.ledger_entries l
            """)
        ).scalar_one()
        
        if current_gold < total_cost:
            raise HTTPException(
                status_code=400,
                detail="Insufficient gold for capacity upgrade"
            )
        
        # Process potion capacity upgrade
        if potion_capacity > 0:
            LedgerManager.create_ledger_entry(
                conn=conn,
                time_id=time_id,
                entry_type='CAPACITY_UPGRADE',
                gold_change=-(potion_capacity * 1000),
                potion_change=0  # Signals potion capacity increase
            )
        
        # Process ML capacity upgrade
        if ml_capacity > 0:
            LedgerManager.create_ledger_entry(
                conn=conn,
                time_id=time_id,
                entry_type='CAPACITY_UPGRADE',
                gold_change=-(ml_capacity * 1000),
                ml_change=0  # Signals ml capacity increase
            )
        
        logger.info(
            f"Processed capacity upgrade - "
            f"Potion: +{potion_capacity}, ML: +{ml_capacity}"
        )