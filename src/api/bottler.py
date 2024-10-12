import sqlalchemy
import logging
import math
from src.api import auth
from src import database as db
from src import potions as po
from src import utilities as ut
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

class BottlePlanItem(BaseModel):
    potion_type: List[int]  # [red_ml, green_ml, blue_ml, dark_ml]
    quantity: int

class BottlePlanResponse(BaseModel):
    plan: List[BottlePlanItem]


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
            potion_capacity_limit = potion_capacity_units * ut.POTION_CAPACITY_PER_UNIT
            total_potions = global_inventory['total_potions']

            # Fetch potion recipes
            potion_recipes = {(
                p['red_ml'], p['green_ml'], p['blue_ml'], p['dark_ml']
            ): p for p in po.DEFAULT_POTIONS}

            # Aggregate ml to deduct and potions to add
            ml_to_deduct = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            potions_to_add = {}

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

                potion_name = matching_potion['name']

                # Check if we have enough ml to produce this potion
                required_ml = {color: matching_potion[color] * quantity for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']}

                for color in required_ml:
                    if current_ml[color] < required_ml[color]:
                        logger.error(f"Insufficient {color} to produce {quantity} of {potion_name}")
                        raise HTTPException(status_code=400, detail=f"Insufficient {color} to produce {quantity} of {potion_name}")

                # Update ml_to_deduct
                for color in required_ml:
                    ml_to_deduct[color] += required_ml[color]
                    current_ml[color] -= required_ml[color]  # Update current_ml for subsequent checks

                # Update potions_to_add
                if potion_name in potions_to_add:
                    potions_to_add[potion_name] += quantity
                else:
                    potions_to_add[potion_name] = quantity

                # Update total_potions
                total_potions += quantity
                if total_potions > potion_capacity_limit:
                    logger.error("Exceeding potion capacity limit")
                    raise HTTPException(status_code=400, detail="Exceeding potion capacity limit")

            # Deduct ml from global_inventory
            update_ml_query = """
                UPDATE global_inventory
                SET red_ml = red_ml - :red_ml,
                    green_ml = green_ml - :green_ml,
                    blue_ml = blue_ml - :blue_ml,
                    dark_ml = dark_ml - :dark_ml,
                    total_potions = total_potions + :total_potions
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_ml_query),
                {
                    "red_ml": ml_to_deduct['red_ml'],
                    "green_ml": ml_to_deduct['green_ml'],
                    "blue_ml": ml_to_deduct['blue_ml'],
                    "dark_ml": ml_to_deduct['dark_ml'],
                    "total_potions": sum(potions_to_add.values())
                }
            )

            # Update potions table
            for potion_name, quantity in potions_to_add.items():
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = current_quantity + :quantity
                    WHERE name = :potion_name;
                """
                connection.execute(
                    sqlalchemy.text(update_potion_query),
                    {
                        "quantity": quantity,
                        "potion_name": potion_name
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
            # Fetch current inventory and capacities
            query = """
                SELECT potion_capacity_units, ml_capacity_units, red_ml, green_ml, blue_ml, dark_ml
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
            potion_capacity_limit = potion_capacity_units * ut.POTION_CAPACITY_PER_UNIT

            # Fetch current potions
            query_potions = """
                SELECT name, current_quantity
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            current_potions = {row['name']: row['current_quantity'] for row in potions}

        # Determine future in-game time
        future_day, future_hour = ut.Utils.get_future_in_game_time(2)
        logger.info(f"Future in-game time: {future_day}, Hour: {future_hour}")

        # Select pricing strategy
        pricing_strategy = ut.Utils.select_pricing_strategy(potion_capacity_units)

        # Get potion priorities for future day and pricing strategy
        potion_priorities = po.POTION_PRIORITIES[future_day][pricing_strategy]

        # Calculate desired potion quantities
        desired_potions = ut.Utils.calculate_desired_potion_quantities(
            potion_capacity_units,
            pricing_strategy,
            potion_priorities
        )

        # Generate bottle plan
        bottle_plan = ut.Utils.get_bottle_plan(
            current_ml,
            desired_potions,
            current_potions,
            potion_capacity_limit
        )

        # Adjust potion_type to sum to exactly 100
        for item in bottle_plan:
            potion_type = item['potion_type']
            potion_type_normalized = ut.Utils.normalize_potion_type(potion_type)
            item['potion_type'] = potion_type_normalized

        logger.info(f"Generated bottle plan: {bottle_plan}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_bottle_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return bottle_plan