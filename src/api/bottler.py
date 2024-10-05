import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from enum import Enum
from pydantic import BaseModel, validator
from src.api import auth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

# Constants for capacity calculations
POTION_CAPACITY_PER_UNIT = 50  # Each potion capacity unit allows storage of 50 potions
ML_CAPACITY_PER_UNIT = 10000    # Each ML capacity unit allows storage of 10000 ml


@router.post("/deliver/{order_id}", summary="Deliver Bottles", description="Process delivery of bottles.")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """
    Process delivery of bottles to global_inventory.
    """
    logger.info(f"Received request to deliver bottles for order_id: {order_id}")
    logger.debug(f"Potions Delivered: {[p.dict() for p in potions_delivered]}")

    try:
        with db.engine.begin() as connection:
            logger.debug("Fetching current inventory from global_inventory.")
            # Retrieve current inventory details
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT red_ml, green_ml, blue_ml, dark_ml
                    FROM global_inventory
                    WHERE id = 1;
                    """
                )
            )
            inventory_row = result.mappings().fetchone()
            logger.debug(f"Current Inventory: {inventory_row}")

            if not inventory_row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory not found.")

            red_ml = inventory_row['red_ml']
            green_ml = inventory_row['green_ml']
            blue_ml = inventory_row['blue_ml']
            dark_ml = inventory_row['dark_ml']

            logger.debug(
                f"Inventory before processing: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}"
            )

            # Initialize totals for ML used
            total_red_ml_used = 0
            total_green_ml_used = 0
            total_blue_ml_used = 0
            total_dark_ml_used = 0

            for potion in potions_delivered:
                logger.debug(f"Processing delivered potion: {potion.dict()}")
                potion_type = potion.potion_type
                quantity = potion.quantity

                # Validate potion_type sums to 100
                if sum(potion_type) != 100:
                    logger.error(
                        f"Invalid potion_type {potion_type} for delivered potion. "
                        f"Sum must be 100."
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Potion type ML must sum to 100.",
                    )

                # Check if potion exists in potions table
                logger.debug(
                    f"Checking existence of potion with type {potion_type} in potions table."
                )
                result = connection.execute(
                    sqlalchemy.text(
                        """
                        SELECT potion_id, current_quantity
                        FROM potions
                        WHERE red_ml = :red_ml AND green_ml = :green_ml
                        AND blue_ml = :blue_ml AND dark_ml = :dark_ml;
                        """
                    ),
                    {
                        'red_ml': potion_type[0],
                        'green_ml': potion_type[1],
                        'blue_ml': potion_type[2],
                        'dark_ml': potion_type[3]
                    }
                )
                potion_row = result.mappings().fetchone()

                if not potion_row:
                    logger.error(
                        f"Potion with composition {potion_type} does not exist."
                    )
                    raise HTTPException(status_code=404, detail="Potion not found.")

                potion_id = potion_row['potion_id']
                current_quantity = potion_row['current_quantity']
                logger.debug(
                    f"Found potion_id: {potion_id}, current_quantity: {current_quantity}"
                )

                # Update potions table by adding delivered quantity
                new_quantity = current_quantity + quantity
                logger.debug(
                    f"Updating potion_id {potion_id}: Adding quantity {quantity}, "
                    f"new_quantity={new_quantity}"
                )
                connection.execute(
                    sqlalchemy.text(
                        """
                        UPDATE potions
                        SET current_quantity = :new_quantity
                        WHERE potion_id = :potion_id;
                        """
                    ),
                    {
                        'new_quantity': new_quantity,
                        'potion_id': potion_id
                    }
                )

                # Accumulate ML used for each color
                total_red_ml_used += potion_type[0] * quantity
                total_green_ml_used += potion_type[1] * quantity
                total_blue_ml_used += potion_type[2] * quantity
                total_dark_ml_used += potion_type[3] * quantity

                logger.debug(
                    f"Accumulated ML used - red_ml: {total_red_ml_used}, "
                    f"green_ml: {total_green_ml_used}, blue_ml: {total_blue_ml_used}, "
                    f"dark_ml: {total_dark_ml_used}"
                )

            # Check if there is enough ML to deduct from inventory
            logger.debug("Checking if inventory has sufficient ML to deduct.")
            if red_ml < total_red_ml_used or green_ml < total_green_ml_used or \
               blue_ml < total_blue_ml_used or dark_ml < total_dark_ml_used:
                logger.error("Insufficient ML in inventory to cover used ML.")
                logger.debug(
                    f"Required ML - red_ml: {total_red_ml_used}, green_ml: {total_green_ml_used}, "
                    f"blue_ml: {total_blue_ml_used}, dark_ml: {total_dark_ml_used}"
                )
                logger.debug(
                    f"Available ML - red_ml: {red_ml}, green_ml: {green_ml}, "
                    f"blue_ml: {blue_ml}, dark_ml: {dark_ml}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient ML in inventory.",
                )

            # Deduct used ML from global_inventory
            new_red_ml = red_ml - total_red_ml_used
            new_green_ml = green_ml - total_green_ml_used
            new_blue_ml = blue_ml - total_blue_ml_used
            new_dark_ml = dark_ml - total_dark_ml_used

            logger.debug(
                f"Updating global_inventory with new ML levels: "
                f"red_ml={new_red_ml}, green_ml={new_green_ml}, "
                f"blue_ml={new_blue_ml}, dark_ml={new_dark_ml}"
            )
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE global_inventory
                    SET red_ml = :new_red_ml,
                        green_ml = :new_green_ml,
                        blue_ml = :new_blue_ml,
                        dark_ml = :new_dark_ml
                    WHERE id = 1;
                    """
                ),
                {
                    'new_red_ml': new_red_ml,
                    'new_green_ml': new_green_ml,
                    'new_blue_ml': new_blue_ml,
                    'new_dark_ml': new_dark_ml
                }
            )

            logger.info(
                f"Successfully processed delivery for order_id {order_id}. "
                f"Total ML deducted: red_ml={total_red_ml_used}, "
                f"green_ml={total_green_ml_used}, blue_ml={total_blue_ml_used}, "
                f"dark_ml={total_dark_ml_used}."
            )
            logger.debug(
                f"Inventory after processing: red_ml={new_red_ml}, green_ml={new_green_ml}, "
                f"blue_ml={new_blue_ml}, dark_ml={new_dark_ml}"
            )

    except HTTPException as e:
        # Re-raise HTTPExceptions after logging
        logger.error(f"HTTPException in post_deliver_bottles: {e.detail}")
        raise e
    except Exception as e:
        # Log exception with traceback
        logger.exception(f"Unhandled exception in post_deliver_bottles: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"Delivery for order_id {order_id} completed successfully.")
    return {"status": "OK"}


@router.post("/plan", summary="Get Bottle Plan", description="Generates bottle plan based on global inventory.")
def get_bottle_plan():
    """
    Generate bottle plan based on available ml in global_inventory.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    logger.info("Received request to generate bottle plan.")

    try:
        with db.engine.begin() as connection:
            logger.debug("Fetching current inventory and capacities from global_inventory.")
            # Retrieve current inventory details
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT red_ml, green_ml, blue_ml, dark_ml, potion_capacity_units, ml_capacity_units, gold
                    FROM global_inventory
                    WHERE id = 1;
                    """
                )
            )
            inventory_row = result.mappings().fetchone()
            logger.debug(f"Current Inventory: {inventory_row}")

            if not inventory_row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory not found.")

            red_ml = inventory_row['red_ml']
            green_ml = inventory_row['green_ml']
            blue_ml = inventory_row['blue_ml']
            dark_ml = inventory_row['dark_ml']
            potion_capacity_units = inventory_row['potion_capacity_units']
            ml_capacity_units = inventory_row['ml_capacity_units']
            gold = inventory_row['gold']

            logger.debug(
                f"Inventory before planning: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}"
            )
            logger.debug(
                f"Current Capacities - potion_capacity_units: {potion_capacity_units}, "
                f"ml_capacity_units: {ml_capacity_units}"
            )
            logger.debug(f"Current Gold: {gold}")

            # Calculate total ML capacity and remaining capacity
            total_ml_capacity = ml_capacity_units * ML_CAPACITY_PER_UNIT  # Each unit allows 10000 ML
            total_ml_used = red_ml + green_ml + blue_ml + dark_ml
            remaining_capacity = total_ml_capacity - total_ml_used

            logger.debug(f"Total ML Capacity: {total_ml_capacity}, Total ML Used: {total_ml_used}, Remaining Capacity: {remaining_capacity}")

            # Define potion priorities
            potion_priorities = [
                {'name': 'Green Potion', 'potion_type': [0, 100, 0, 0]},
                {'name': 'Blue Potion', 'potion_type': [0, 0, 100, 0]},
                {'name': 'Red Potion', 'potion_type': [100, 0, 0, 0]},
                {'name': 'Dark Potion', 'potion_type': [0, 0, 0, 100]},
                # {'name': 'Cyan Potion', 'potion_type': [0, 50, 50, 0]},
                # {'name': 'Yellow Potion', 'potion_type': [50, 50, 0, 0]},
                # {'name': 'Magenta Potion', 'potion_type': [50, 0, 50, 0]},
                # {'name': 'Dark Green Potion', 'potion_type': [0, 50, 0, 50]},
                # {'name': 'Dark Blue Potion', 'potion_type': [0, 0, 50, 50]},
                # {'name': 'Dark Red Potion', 'potion_type': [50, 0, 0, 50]},
                # {'name': 'Dark Brown Potion', 'potion_type': [25, 25, 25, 25]},
                # TODO: Use data analytics to see if there's more combos to be made
            ]

            bottle_plan = []

            for potion in potion_priorities:
                potion_type = potion['potion_type']
                total_ml_required = sum(potion_type)
                logger.debug(f"Evaluating potion: {potion['name']} with potion_type: {potion_type}")

                # Determine available ML for each color
                available_ml = min(
                    (red_ml // potion_type[0] if potion_type[0] > 0 else float('inf')),
                    (green_ml // potion_type[1] if potion_type[1] > 0 else float('inf')),
                    (blue_ml // potion_type[2] if potion_type[2] > 0 else float('inf')),
                    (dark_ml // potion_type[3] if potion_type[3] > 0 else float('inf'))
                )

                if available_ml <= 0:
                    logger.debug(f"Insufficient ML to brew {potion['name']}. Skipping.")
                    continue  # Cannot brew this potion

                # Determine how many potions can be brewed without exceeding capacity
                max_potions_capacity = remaining_capacity // total_ml_required
                potions_to_brew = min(available_ml, max_potions_capacity, 10000)  # Limit to 10000

                if potions_to_brew <= 0:
                    logger.debug(f"No capacity to brew {potion['name']}. Skipping.")
                    continue  # No capacity to brew this potion

                # Add to bottle plan
                bottle_plan.append({
                    "potion_type": potion_type,
                    "quantity": potions_to_brew
                })
                
                logger.info(f"Planned to brew {potions_to_brew} units of {potion['name']}.")

                # Update remaining capacity and ML in inventory
                remaining_capacity -= potions_to_brew * total_ml_required
                red_ml -= potions_to_brew * potion_type[0]
                green_ml -= potions_to_brew * potion_type[1]
                blue_ml -= potions_to_brew * potion_type[2]
                dark_ml -= potions_to_brew * potion_type[3]

                logger.debug(f"Updated Remaining Capacity: {remaining_capacity}")
                logger.debug(f"Updated ML Levels - red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}")

                # Check if capacity threshold is reached
                if remaining_capacity / total_ml_capacity < 0.8:
                    logger.info("Inventory nearing capacity. Halting further bottling to consider capacity expansion.")
                    break  # Exit loop to consider capacity expansion

            # Limit bottle plan to 6 potions as per API specification
            bottle_plan = bottle_plan[:6]
            logger.debug(f"Bottle plan after limiting to 6 potions: {bottle_plan}")
            logger.info("Bottle plan generated successfully.")

            return bottle_plan

    except HTTPException as e:
        logger.error(f"HTTPException in get_bottle_plan: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Finished processing bottle plan.")
    return bottle_plan
