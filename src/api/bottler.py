import sqlalchemy
import logging
from src.api import auth
from src import database as db
from src import utilities as ut
from src import game_constants as gc
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from typing import List, Dict

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
            # Fetch current inventory and capacities
            query = """
                SELECT potion_capacity_units, red_ml, green_ml, blue_ml, dark_ml, total_potions
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            global_inventory = result.mappings().fetchone()

            if not global_inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            potion_capacity_units = global_inventory['potion_capacity_units']
            current_ml = {
                'red_ml': global_inventory['red_ml'],
                'green_ml': global_inventory['green_ml'],
                'blue_ml': global_inventory['blue_ml'],
                'dark_ml': global_inventory['dark_ml'],
            }
            potion_capacity_limit = potion_capacity_units * gc.POTION_CAPACITY_PER_UNIT
            total_potions = global_inventory['total_potions']

            # Fetch potion recipes
            potion_recipes = {}
            for potion in gc.DEFAULT_POTIONS:
                potion_type = ut.Utils.normalize_potion_type([
                    potion['red_ml'],
                    potion['green_ml'],
                    potion['blue_ml'],
                    potion['dark_ml']
                ])
                potion_recipes[tuple(potion_type)] = potion

            # Aggregate ml to deduct and potions to add
            ml_to_deduct = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            potions_to_add = {}
            total_new_potions = 0

            for potion in potions_delivered:
                potion_type = potion.potion_type
                quantity = potion.quantity

                # Normalize potion_type to sum to 100
                potion_type_normalized = ut.Utils.normalize_potion_type(potion_type)

                # Find matching potion recipe
                potion_key = tuple(potion_type_normalized)
                matching_potion = potion_recipes.get(potion_key)

                if not matching_potion:
                    logger.error(f"No matching potion found for potion_type {potion_type_normalized}")
                    raise HTTPException(status_code=400, detail=f"No matching potion found for potion_type {potion_type_normalized}")

                potion_sku = matching_potion['sku']

                # Check if we have enough ml to produce this potion
                required_ml = {color: matching_potion[color] * quantity for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']}

                for color in required_ml:
                    if current_ml[color] < required_ml[color]:
                        logger.error(f"Insufficient {color} to produce {quantity} of {potion_sku}")
                        raise HTTPException(status_code=400, detail=f"Insufficient {color} to produce {quantity} of {potion_sku}")

                # Update ml_to_deduct
                for color in required_ml:
                    ml_to_deduct[color] += required_ml[color]
                    current_ml[color] -= required_ml[color]  # Update current_ml for subsequent checks

                # Update potions_to_add
                if potion_sku in potions_to_add:
                    potions_to_add[potion_sku] += quantity
                else:
                    potions_to_add[potion_sku] = quantity

                # Update total_potions
                total_new_potions += quantity
                if total_potions + total_new_potions > potion_capacity_limit:
                    logger.error("Exceeding potion capacity limit")
                    raise HTTPException(status_code=400, detail="Exceeding potion capacity limit")

            # Deduct ml from global_inventory
            update_ml_query = """
                UPDATE global_inventory
                SET red_ml = red_ml - :red_ml,
                    green_ml = green_ml - :green_ml,
                    blue_ml = blue_ml - :blue_ml,
                    dark_ml = dark_ml - :dark_ml,
                    total_potions = total_potions + :total_potions,
                    total_ml = total_ml - :red_ml - :green_ml - :blue_ml - :dark_ml
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_ml_query),
                {
                    "red_ml": ml_to_deduct['red_ml'],
                    "green_ml": ml_to_deduct['green_ml'],
                    "blue_ml": ml_to_deduct['blue_ml'],
                    "dark_ml": ml_to_deduct['dark_ml'],
                    "total_potions": total_new_potions
                }
            )

            # Update potions table
            for potion_sku, quantity in potions_to_add.items():
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = current_quantity + :quantity
                    WHERE sku = :potion_sku;
                """
                connection.execute(
                    sqlalchemy.text(update_potion_query),
                    {
                        "quantity": quantity,
                        "potion_sku": potion_sku
                    }
                )
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
                raise ValueError("No in-game time found in database.")

            # Fetch current inventory and capacities
            query = """
                SELECT potion_capacity_units, ml_capacity_units, red_ml, green_ml, blue_ml, dark_ml, total_potions
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            global_inventory = result.mappings().fetchone()

            if not global_inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            potion_capacity_units = global_inventory['potion_capacity_units']
            ml_capacity_units = global_inventory['ml_capacity_units']
            current_ml = {
                'red_ml': global_inventory['red_ml'],
                'green_ml': global_inventory['green_ml'],
                'blue_ml': global_inventory['blue_ml'],
                'dark_ml': global_inventory['dark_ml'],
            }
            potion_capacity_limit = potion_capacity_units * gc.POTION_CAPACITY_PER_UNIT
            total_potions = global_inventory['total_potions']

            # Fetch current potions
            query_potions = """
                SELECT sku, current_quantity
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            current_potions = {row['sku']: row['current_quantity'] for row in potions}

        # Determine future in-game time (3 ticks ahead)
        future_day, future_hour = ut.Utils.get_future_in_game_time(current_in_game_day, current_in_game_hour, ticks_ahead=3)
        logger.info(f"Future in-game time: {future_day}, Hour: {future_hour}")

        # Select pricing strategy
        pricing_strategy = ut.Utils.select_pricing_strategy(potion_capacity_units)
        logger.info(f"Selected pricing strategy: {pricing_strategy}")

        # Get potion priorities for future day and pricing strategy
        potion_priorities = gc.POTION_PRIORITIES[future_day][pricing_strategy]
        logger.debug(f"Potion priorities for {future_day} and strategy {pricing_strategy}: {potion_priorities}")

        # Calculate desired potion quantities
        desired_potions = ut.Utils.calculate_desired_potion_quantities(
            potion_capacity_units=potion_capacity_units,
            current_potions=current_potions,
            potion_priorities=potion_priorities,
            pricing_strategy=pricing_strategy
        )

        # Get potion recipes
        potion_recipes = {p['sku']: p for p in gc.DEFAULT_POTIONS}

        # Generate bottle plan
        bottle_plan = ut.Utils.get_bottle_plan(
            current_ml=current_ml,
            desired_potions=desired_potions,
            current_potions=current_potions,
            potion_capacity_limit=potion_capacity_limit,
            potion_recipes=potion_recipes
        )

        logger.info(f"Generated bottle plan: {bottle_plan}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_bottle_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return bottle_plan