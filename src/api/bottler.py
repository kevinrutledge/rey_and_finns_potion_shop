import sqlalchemy
import logging
import math
from src.api import auth
from src import database as db
from src.potion_coefficients import potion_coefficients
from src.utilities import Utils as ut
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
    logger.info(f"Endpoint /bottler/deliver/{order_id} called with {len(potions_delivered)} potions.")
    logger.debug(f"Potions Delivered: {potions_delivered}")

    try:
        with db.engine.begin() as connection:
            for potion in potions_delivered:
                composition = potion.potion_type  # [r, g, b, d]
                quantity = potion.quantity
                logger.debug(f"Processing delivery - Composition: {composition}, Quantity: {quantity}")

                # Fetch potion details from the potions table
                logger.debug("Fetching potion details from potions table.")
                query_potion = """
                    SELECT potion_id, current_quantity
                    FROM potions
                    WHERE red_ml = :red_ml
                    AND green_ml = :green_ml
                    AND blue_ml = :blue_ml
                    AND dark_ml = :dark_ml
                    LIMIT 1;
                """
                result = connection.execute(
                    sqlalchemy.text(query_potion),
                    {
                        'red_ml': composition[0],
                        'green_ml': composition[1],
                        'blue_ml': composition[2],
                        'dark_ml': composition[3]
                    }
                )
                potion_row = result.mappings().fetchone()
                if not potion_row:
                    logger.error(f"No potion found with composition {composition}.")
                    raise HTTPException(status_code=400, detail=f"No potion found with composition {composition}.")

                potion_id = potion_row['potion_id']
                current_quantity = potion_row['current_quantity']
                logger.debug(f"Found Potion ID: {potion_id} with Current Quantity: {current_quantity}")

                # Calculate total ml required for brewing
                total_ml_required = {
                    'red_ml': composition[0] * quantity,
                    'green_ml': composition[1] * quantity,
                    'blue_ml': composition[2] * quantity,
                    'dark_ml': composition[3] * quantity
                }
                logger.debug(f"Total ML required - {total_ml_required}")

                # Check if sufficient ml is available in global_inventory
                logger.debug("Checking if sufficient ML is available in global_inventory.")
                query_inventory = """
                    SELECT red_ml, green_ml, blue_ml, dark_ml
                    FROM global_inventory
                    WHERE id = 1;
                """
                result = connection.execute(sqlalchemy.text(query_inventory))
                inventory = result.mappings().fetchone()
                if not inventory:
                    logger.error("Global inventory record not found.")
                    raise HTTPException(status_code=500, detail="Global inventory record not found.")

                # Verify and deduct ml
                for color, ml_required in total_ml_required.items():
                    if inventory[color] < ml_required:
                        logger.error(f"Insufficient {color} ml in inventory for brewing.")
                        raise HTTPException(status_code=400, detail=f"Insufficient {color} ml in inventory for brewing.")
                    # Deduct ml
                    new_ml = inventory[color] - ml_required
                    logger.debug(f"Deducting {ml_required} ml from {color}. New {color} ml: {new_ml}")
                    update_ml_query = f"""
                        UPDATE global_inventory
                        SET {color} = :new_ml
                        WHERE id = 1;
                    """
                    connection.execute(
                        sqlalchemy.text(update_ml_query),
                        {'new_ml': new_ml}
                    )

                # Update potion quantity
                new_quantity = current_quantity + quantity
                logger.debug(f"Updating potion ID {potion_id} quantity from {current_quantity} to {new_quantity}.")
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = :new_quantity
                    WHERE potion_id = :potion_id;
                """
                connection.execute(
                    sqlalchemy.text(update_potion_query),
                    {
                        'new_quantity': new_quantity,
                        'potion_id': potion_id
                    }
                )

                logger.info(f"Brewed {quantity} of potion ID {potion_id}. Updated quantity to {new_quantity}.")

            # Optionally, update total_ml in global_inventory
            logger.debug("Recalculating total_ml in global_inventory.")
            query_total_ml = """
                SELECT 
                    red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_total_ml))
            updated_inventory = result.mappings().fetchone()
            total_ml = (
                updated_inventory['red_ml'] +
                updated_inventory['green_ml'] +
                updated_inventory['blue_ml'] +
                updated_inventory['dark_ml']
            )
            logger.debug(f"Total ML after brewing: {total_ml}")

            update_total_ml_query = """
                UPDATE global_inventory
                SET total_ml = :total_ml
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_total_ml_query),
                {'total_ml': total_ml}
            )
            logger.debug("Updated total_ml in global_inventory.")

        logger.info(f"Successfully processed delivery for order_id {order_id}.")
        return {"success": True}

    except HTTPException as e:
        logger.error(f"HTTPException in post_deliver_bottles: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/plan", summary="Get Bottle Plan", description="Generates bottle plan based on global inventory.")
def get_bottle_plan():
    """
    Generate bottle plan based on available ml in global_inventory.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    logger.info("Endpoint /bottler/plan called.")
    try:
        # Step 1: Determine current in-game day and hour
        real_time = ut.get_current_real_time()
        in_game_day, in_game_hour = ut.compute_in_game_time(real_time)
        hour_block = ut.get_hour_block(in_game_hour)
        logger.debug(f"Computed in-game time - Day: {in_game_day}, Hour: {in_game_hour}, Block: {hour_block}")

        # Step 2: Fetch potion demands for the current day and hour block
        day_potions = potion_coefficients.get(in_game_day, {}).get(hour_block, [])
        if not day_potions:
            logger.warning(f"No potion coefficients found for Day: {in_game_day}, Hour Block: {hour_block}. Returning empty plan.")
            return BottlePlanResponse(plan=[])

        logger.debug(f"Potion demands for Day: {in_game_day}, Block: {hour_block}: {day_potions}")

        # Step 3: Calculate available ml from global_inventory
        with db.engine.begin() as connection:
            logger.debug("Fetching available ml from global_inventory.")
            query_ml = """
                SELECT red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_ml))
            inventory = result.mappings().fetchone()
            if not inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")
            available_ml = {
                'red_ml': inventory['red_ml'],
                'green_ml': inventory['green_ml'],
                'blue_ml': inventory['blue_ml'],
                'dark_ml': inventory['dark_ml']
            }
            logger.debug(f"Available ML - Red: {available_ml['red_ml']}, Green: {available_ml['green_ml']}, Blue: {available_ml['blue_ml']}, Dark: {available_ml['dark_ml']}")

            # Fetch current capacities
            logger.debug("Fetching current capacity units from global_inventory.")
            query_capacity = """
                SELECT potion_capacity_units, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_capacity))
            capacities = result.mappings().fetchone()
            if not capacities:
                logger.error("Global inventory record not found for capacities.")
                raise HTTPException(status_code=500, detail="Global inventory record not found for capacities.")
            potion_capacity_units = capacities['potion_capacity_units']
            ml_capacity_units = capacities['ml_capacity_units']
            potion_capacity_limit = potion_capacity_units * 50  # Each unit allows 50 potions
            ml_capacity_limit = ml_capacity_units * 10000     # Each unit allows 10000 ml
            logger.debug(f"Potion Capacity - Units: {potion_capacity_units}, Limit: {potion_capacity_limit}")
            logger.debug(f"ML Capacity - Units: {ml_capacity_units}, Limit: {ml_capacity_limit}")

        # Step 4: Fetch current number of potions
        with db.engine.begin() as connection:
            logger.debug("Fetching total number of potions from potions table.")
            query_total_potions = """
                SELECT SUM(current_quantity) AS total_potions
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_total_potions))
            total_potions_row = result.mappings().fetchone()
            total_potions = total_potions_row['total_potions'] if total_potions_row['total_potions'] else 0
            logger.debug(f"Total potions currently in inventory: {total_potions}")

        # Step 5: Calculate ROI and sort potions
        for potion in day_potions:
            composition = potion['composition']
            demand = potion['demand']
            price = potion['price']
            total_ml = sum(composition)
            if total_ml == 0:
                potion['roi'] = 0
            else:
                # Define ROI as (demand * price) / total_ml_required
                potion['roi'] = (demand * price) / total_ml

        # Sort potions by ROI in descending order
        day_potions_sorted = sorted(day_potions, key=lambda x: x['roi'], reverse=True)
        logger.debug(f"Potions sorted by ROI: {day_potions_sorted}")

        # Step 6: Allocate brew quantities
        potion_plan = []
        for potion in day_potions_sorted:
            composition = potion['composition']  # [r, g, b, d]
            demand = potion['demand']          # Integer representing demand
            price = potion['price']
            roi = potion['roi']

            # Calculate desired_quantity based on demand
            desired_quantity = math.floor((demand / 100) * potion_capacity_limit)
            desired_quantity = min(desired_quantity, potion_capacity_limit - total_potions)

            if desired_quantity <= 0:
                logger.debug(f"No capacity left to brew potion: {potion['name']}. Skipping.")
                continue  # Skip if no capacity left

            # Determine max quantity based on available ml
            max_quantity_ml = float('inf')
            for idx, color in enumerate(['red_ml', 'green_ml', 'blue_ml', 'dark_ml']):
                ml_required = composition[idx]
                if ml_required > 0:
                    possible = available_ml[color] // ml_required
                    max_quantity_ml = min(max_quantity_ml, possible)

            brew_quantity = min(desired_quantity, max_quantity_ml)

            if brew_quantity <= 0:
                logger.debug(f"Insufficient ML to brew potion: {potion['name']}. Skipping.")
                continue  # Skip if insufficient ML

            # Add to potion plan
            potion_plan.append({
                "potion_type": composition,
                "quantity": brew_quantity
            })

            # Update totals
            total_potions += brew_quantity
            for idx, color in enumerate(['red_ml', 'green_ml', 'blue_ml', 'dark_ml']):
                available_ml[color] -= composition[idx] * brew_quantity

            logger.debug(f"Planned to brew {brew_quantity} of {potion['name']} with ROI {roi}.")

        logger.info(f"Brew plan generated: {potion_plan}")
        return BottlePlanResponse(plan=potion_plan)

    except HTTPException as e:
        logger.error(f"HTTPException in get_bottle_plan: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"Brew plan generated: {potion_plan}")
    return BottlePlanResponse(plan=potion_plan)
