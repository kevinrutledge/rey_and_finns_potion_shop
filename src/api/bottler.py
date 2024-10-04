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


@router.post("/deliver/{order_id}", summary="Deliver Bottles", description="Process delivery of bottles.")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """
    Process delivery of bottles to global_inventory.
    """
    logger.info(f"Received request to deliver bottles for order_id: {order_id}")
    logger.debug(f"Potions Delivered: {potions_delivered}")

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

    logger.debug("Returning response: {'status': 'OK'}")
    return {"status": "OK"}


@router.post("/plan", summary="Get Bottle Plan", description="Generates bottle production plan based on global inventory.")
def get_bottle_plan():
    """
    Generate bottle plan based on available ml in global_inventory.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    logger.info("Received request to generate bottle production plan.")

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
                f"Inventory before planning: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}"
            )

            # Define desired potions
            desired_potions = [
                {'name': 'Red Potion', 'potion_type': [100, 0, 0, 0]},
                {'name': 'Green Potion', 'potion_type': [0, 100, 0, 0]},
                {'name': 'Blue Potion', 'potion_type': [0, 0, 100, 0]},
                {'name': 'Yellow Potion', 'potion_type': [50, 50, 0, 0]},
                {'name': 'Magenta Potion', 'potion_type': [50, 0, 50, 0]},
                {'name': 'Cyan Potion', 'potion_type': [0, 50, 50, 0]},
                # Additional combinations can be added here
            ]

            bottle_plan = []

            for potion in desired_potions:
                logger.debug(f"Processing desired potion: {potion}")
                potion_type = potion['potion_type']

                # Check if potion exists in potions table
                logger.debug(
                    f"Checking existence of potion '{potion['name']}' with type {potion_type}."
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
                    logger.debug(
                        f"Potion '{potion['name']}' does not exist. Inserting into potions table."
                    )
                    # Insert new potion into potions table
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO potions (name, sku, red_ml, green_ml, blue_ml, dark_ml, total_ml, price, current_quantity)
                            VALUES (:name, :sku, :red_ml, :green_ml, :blue_ml, :dark_ml, 100, :price, 0);
                            """
                        ),
                        {
                            'name': potion['name'],
                            'sku': potion['name'].upper().replace(' ', '_'),
                            'red_ml': potion_type[0],
                            'green_ml': potion_type[1],
                            'blue_ml': potion_type[2],
                            'dark_ml': potion_type[3],
                            'price': 100  # Adjust prices as needed
                        }
                    )
                    # Retrieve newly inserted potion_id
                    potion_id = connection.execute(
                        sqlalchemy.text("SELECT potion_id FROM potions WHERE sku = :sku;"),
                        {'sku': potion['name'].upper().replace(' ', '_')}
                    ).scalar()
                    current_quantity = 0
                    logger.debug(
                        f"Inserted new potion '{potion['name']}' with potion_id {potion_id}."
                    )
                else:
                    potion_id = potion_row['potion_id']
                    current_quantity = potion_row['current_quantity']
                    logger.debug(
                        f"Found existing potion '{potion['name']}' with potion_id {potion_id} "
                        f"and current_quantity {current_quantity}."
                    )

                # Determine desired stock level
                desired_stock = 10
                needed_quantity = desired_stock - current_quantity
                logger.debug(
                    f"Desired stock for potion '{potion['name']}': {desired_stock}, "
                    f"needed_quantity={needed_quantity}"
                )

                if needed_quantity <= 0:
                    logger.debug(
                        f"Sufficient stock for potion '{potion['name']}'. No purchase needed."
                    )
                    continue  # Skip if enough stock is available

                # Calculate how much ML is required for one potion
                potion_ml = potion_type

                # Calculate maximum number of potions that can be mixed based on available ML
                max_potions_red = red_ml // potion_ml[0] if potion_ml[0] > 0 else float('inf')
                max_potions_green = green_ml // potion_ml[1] if potion_ml[1] > 0 else float('inf')
                max_potions_blue = blue_ml // potion_ml[2] if potion_ml[2] > 0 else float('inf')
                max_potions_dark = dark_ml // potion_ml[3] if potion_ml[3] > 0 else float('inf')

                max_potions_possible = min(
                    max_potions_red, max_potions_green, max_potions_blue, max_potions_dark
                )
                max_potions_possible = int(max_potions_possible)

                logger.debug(
                    f"Maximum potions possible to mix for '{potion['name']}': {max_potions_possible}"
                )

                quantity_to_mix = min(needed_quantity, max_potions_possible)

                if quantity_to_mix <= 0:
                    logger.debug(
                        f"Insufficient ML to mix potion '{potion['name']}'. Skipping."
                    )
                    continue  # Skip if no potions can be mixed

                # Add to bottle plan
                bottle_plan.append(
                    {
                        "potion_type": potion_ml,
                        "quantity": quantity_to_mix
                    }
                )
                logger.info(
                    f"Planning to mix {quantity_to_mix} units of '{potion['name']}'."
                )

                # Deduct ML that will be used for mixing these potions
                red_ml -= potion_ml[0] * quantity_to_mix
                green_ml -= potion_ml[1] * quantity_to_mix
                blue_ml -= potion_ml[2] * quantity_to_mix
                dark_ml -= potion_ml[3] * quantity_to_mix

                logger.debug(
                    f"Inventory after planning to mix '{potion['name']}': red_ml={red_ml}, "
                    f"green_ml={green_ml}, blue_ml={blue_ml}, dark_ml={dark_ml}"
                )

            # Limit bottle plan to 6 potions as per API specification
            bottle_plan = bottle_plan[:6]
            logger.debug(f"Bottle plan after limiting to 6 potions: {bottle_plan}")

            logger.info("Bottle production plan generated successfully.")

    except HTTPException as e:
        logger.error(f"HTTPException in get_bottle_plan: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in get_bottle_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.debug(f"Returning bottle_plan: {bottle_plan}")
    logger.info("Finished processing bottle production plan.")
    return bottle_plan