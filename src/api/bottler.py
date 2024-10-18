import sqlalchemy
import logging
from src.api import auth
from src import database as db
from src import potion_utilities as pu
from src import potion_config as pc
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver/{order_id}", summary="Deliver Bottles", description="Process delivery of bottles.")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """
    Process delivery of bottles to global_inventory.
    """
    logger.info(f"Processing delivery for order_id={order_id}. Number of potions delivered: {len(potions_delivered)}.")
    logger.debug(f"Potions Delivered: {potions_delivered}")

    try:
        with db.engine.begin() as connection:
            # Fetch bottling order corresponding to order_id
            query_order = """
                SELECT bottling_plan, status
                FROM bottling_orders
                WHERE order_id = :order_id;
            """
            result = connection.execute(sqlalchemy.text(query_order), {'order_id': order_id})
            order = result.mappings().fetchone()

            if not order:
                logger.error(f"Bottling order with order_id {order_id} not found.")
                raise HTTPException(status_code=400, detail=f"Bottling order with order_id {order_id} not found.")

            if order['status'] != 'pending':
                logger.error(f"Bottling order with order_id {order_id} is not pending.")
                raise HTTPException(status_code=400, detail=f"Bottling order with order_id {order_id} is not pending.")

            bottling_plan = order['bottling_plan']  # Should be a dict mapping SKU to quantity
            logger.debug(f"Bottling Plan for order_id {order_id}: {bottling_plan}")

            # Verify that delivered potions match bottling plan
            delivered_potions_dict = {}
            for potion in potions_delivered:
                potion_type_normalized = pu.Utilities.normalize_potion_type(potion.potion_type)
                potion_def = None
                # Find matching potion SKU
                for sku, definition in pc.POTION_DEFINITIONS.items():
                    potion_type_def = [
                        definition.get('red_ml', 0),
                        definition.get('green_ml', 0),
                        definition.get('blue_ml', 0),
                        definition.get('dark_ml', 0)
                    ]
                    potion_type_def_normalized = pu.Utilities.normalize_potion_type(potion_type_def)
                    if potion_type_normalized == potion_type_def_normalized:
                        potion_def = definition
                        potion_sku = sku
                        break

                if not potion_def:
                    logger.error(f"No matching potion found for potion_type {potion_type_normalized}")
                    raise HTTPException(status_code=400, detail=f"No matching potion found for potion_type {potion_type_normalized}")

                if potion_sku not in bottling_plan:
                    logger.error(f"Delivered potion SKU {potion_sku} not in bottling plan.")
                    raise HTTPException(status_code=400, detail=f"Delivered potion SKU {potion_sku} not in bottling plan.")

                expected_quantity = bottling_plan[potion_sku]
                if potion.quantity != expected_quantity:
                    logger.error(f"Quantity mismatch for SKU {potion_sku}: Expected {expected_quantity}, Delivered {potion.quantity}")
                    raise HTTPException(status_code=400, detail=f"Quantity mismatch for SKU {potion_sku}")

                delivered_potions_dict[potion_sku] = potion.quantity

            # Update potions inventory
            for sku, quantity in delivered_potions_dict.items():
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = current_quantity + :quantity
                    WHERE sku = :sku;
                """
                connection.execute(sqlalchemy.text(update_potion_query), {'quantity': quantity, 'sku': sku})
                logger.debug(f"Added {quantity} of {sku} to potions inventory.")

            # Update global potion count
            total_delivered_potions = sum(delivered_potions_dict.values())
            update_global_inventory = """
                UPDATE global_inventory
                SET total_potions = total_potions + :total_potions
                WHERE id = 1;
            """
            connection.execute(sqlalchemy.text(update_global_inventory), {'total_potions': total_delivered_potions})

            # Mark bottling order as completed
            update_order_status = """
                UPDATE bottling_orders
                SET status = 'completed'
                WHERE order_id = :order_id;
            """
            connection.execute(sqlalchemy.text(update_order_status), {'order_id': order_id})
            logger.info(f"Marked bottling order_id {order_id} as completed.")

        logger.info(f"Successfully processed delivery for order_id {order_id}.")

    except HTTPException as he:
        logger.error(f"HTTPException in post_deliver_bottles: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in post_deliver_bottles: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"success": True}


@router.post("/plan", summary="Get Bottle Plan", description="Generates bottle plan based on global inventory.")
def get_bottle_plan():
    """
    Generate bottle plan based on available ml in global_inventory.
    """

    # Each bottle has quantity of what proportion of red, blue, and green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    logger.info("Endpoint /bottler/plan called.")

    try:
        with db.engine.begin() as connection:
            # Get current in-game day and hour
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM in_game_time
                ORDER BY created_at DESC
                LIMIT 1;
            """
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise HTTPException(status_code=500, detail="No in-game time found in database.")

            # Fetch current inventory and capacities
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units, red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            global_inventory = result.mappings().fetchone()

            if not global_inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            gold = global_inventory['gold']
            potion_capacity_units = global_inventory['potion_capacity_units']
            ml_capacity_units = global_inventory['ml_capacity_units']
            ml_inventory = {
                'red_ml': global_inventory['red_ml'],
                'green_ml': global_inventory['green_ml'],
                'blue_ml': global_inventory['blue_ml'],
                'dark_ml': global_inventory['dark_ml'],
            }
            potion_capacity_limit = potion_capacity_units * pc.POTION_CAPACITY_PER_UNIT

            # Fetch current potion inventory
            query_potions = """
                SELECT sku, current_quantity
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            potion_inventory = {row['sku']: row['current_quantity'] for row in potions}

        # Determine future in-game time (e.g., 2 ticks ahead)
        future_day, future_hour = pu.Utilities.get_future_in_game_time(
            current_in_game_day, current_in_game_hour, ticks_ahead=2
        )
        logger.info(f"Future in-game time (2 ticks ahead): {future_day}, Hour: {future_hour}")

        # Determine pricing strategy
        current_strategy = pu.PotionShopLogic.determine_pricing_strategy(
            gold=gold,
            ml_capacity_units=ml_capacity_units,
            potion_capacity_units=potion_capacity_units
        )
        logger.info(f"Determined pricing strategy: {current_strategy}")

        # Get potion priorities
        potion_priorities = pu.PotionShopLogic.get_potion_priorities(
            current_day=future_day,
            current_strategy=current_strategy,
            potion_priorities=pc.POTION_PRIORITIES
        )

        # Calculate potion bottling plan
        bottling_plan = pu.PotionShopLogic.calculate_potion_bottling_plan(
            current_strategy=current_strategy,
            potion_priorities=potion_priorities,
            potion_inventory=potion_inventory,
            potion_capacity_units=potion_capacity_units,
            ml_inventory=ml_inventory,
            ml_capacity_units=ml_capacity_units,
            gold=gold
        )

        # Prepare bottle plan
        
        bottle_plan = []
        for sku, quantity in bottling_plan.items():
            potion_def = pc.POTION_DEFINITIONS.get(sku)
            if not potion_def:
                logger.error(f"Potion definition for SKU {sku} not found.")
                continue
            potion_type = [
                potion_def.get('red_ml', 0),
                potion_def.get('green_ml', 0),
                potion_def.get('blue_ml', 0),
                potion_def.get('dark_ml', 0)
            ]
            potion_type_normalized = pu.Utilities.normalize_potion_type(potion_type)
            bottle_plan.append({
                "potion_type": potion_type_normalized,
                "quantity": quantity
            })

        logger.info(f"Generated bottle plan: {bottle_plan}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_bottle_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return bottle_plan