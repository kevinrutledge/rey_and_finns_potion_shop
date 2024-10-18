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
    logger.info(f"Processing delivery of bottles. Number of potions delivered: {len(potions_delivered)}.")
    logger.debug(f"Potions Delivered: {potions_delivered}")

    try:
        with db.engine.begin() as connection:
            delivered_potions_dict = {}
            ml_used = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            for potion in potions_delivered:
                # Normalize potion type
                potion_type_normalized = pu.Utilities.normalize_potion_type(potion.potion_type)
                potion_def = None
                potion_sku = None

                # Find matching potion SKU from potion definitions
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

                if not potion_def or not potion_sku:
                    logger.error(f"No matching potion found for potion_type {potion_type_normalized}")
                    raise HTTPException(status_code=400, detail=f"No matching potion found for potion_type {potion_type_normalized}")

                # Accumulate quantities of each potion SKU delivered
                delivered_potions_dict[potion_sku] = delivered_potions_dict.get(potion_sku, 0) + potion.quantity

                # Calculate ml used per color for this potion
                for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']:
                    ml_per_potion = potion_def.get(color, 0)
                    ml_used[color] += ml_per_potion * potion.quantity

            # Update ml inventory
            update_global_inventory_ml = """
                UPDATE global_inventory
                SET
                    red_ml = red_ml - :red_ml_used,
                    green_ml = green_ml - :green_ml_used,
                    blue_ml = blue_ml - :blue_ml_used,
                    dark_ml = dark_ml - :dark_ml_used,
                    total_ml = total_ml - :total_ml_used,
                    total_potions = total_potions + :total_potions
                WHERE id = 1;
            """
            total_ml_used = sum(ml_used.values())
            total_delivered_potions = sum(delivered_potions_dict.values())
            connection.execute(sqlalchemy.text(update_global_inventory_ml), {
                'red_ml_used': ml_used['red_ml'],
                'green_ml_used': ml_used['green_ml'],
                'blue_ml_used': ml_used['blue_ml'],
                'dark_ml_used': ml_used['dark_ml'],
                'total_ml_used': total_ml_used,
                'total_potions': total_delivered_potions
            })

            logger.debug(f"Deducted ml used from global_inventory: {ml_used}")

            # Update potions inventory
            for sku, quantity in delivered_potions_dict.items():
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = current_quantity + :quantity
                    WHERE sku = :sku;
                """
                result = connection.execute(sqlalchemy.text(update_potion_query), {'quantity': quantity, 'sku': sku})

                if result.rowcount == 0:
                    # If potion does not exist in potions table, insert it
                    potion_def = pc.POTION_DEFINITIONS[sku]
                    insert_potion_query = """
                        INSERT INTO potions (name, sku, red_ml, green_ml, blue_ml, dark_ml, total_ml, price, current_quantity)
                        VALUES (:name, :sku, :red_ml, :green_ml, :blue_ml, :dark_ml, :total_ml, :price, :current_quantity);
                    """
                    connection.execute(sqlalchemy.text(insert_potion_query), {
                        'name': potion_def['name'],
                        'sku': sku,
                        'red_ml': potion_def.get('red_ml', 0),
                        'green_ml': potion_def.get('green_ml', 0),
                        'blue_ml': potion_def.get('blue_ml', 0),
                        'dark_ml': potion_def.get('dark_ml', 0),
                        'total_ml': potion_def.get('total_ml', 0),
                        'price': potion_def.get('price', 0),
                        'current_quantity': quantity
                    })
                    logger.debug(f"Inserted new potion {sku} with quantity {quantity} into potions inventory.")
                else:
                    logger.debug(f"Added {quantity} of {sku} to potions inventory.")

            # No need to update total_potions again here since it's already updated above

        logger.info(f"Successfully processed delivery of bottles.")

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