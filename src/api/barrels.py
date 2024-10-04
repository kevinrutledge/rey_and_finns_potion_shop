import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from src.api import auth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]  # [red, green, blue, dark]
    price: int
    quantity: int  # Quantity available for sale in catalog

class BarrelPurchase(BaseModel):
    sku: str
    quantity: int

# Constants for capacity calculations
POTION_CAPACITY_PER_UNIT = 50  # Each potion capacity unit allows storage of 50 potions
ML_CAPACITY_PER_UNIT = 10000    # Each ML capacity unit allows storage of 10000 ml


@router.post("/deliver/{order_id}", summary="Deliver Barrels", description="Process delivery of barrels.")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """
    Process delivery of barrels to inventory.
    """
    logger.info(f"Starting post_deliver_barrels endpoint for order_id {order_id}.")
    logger.debug(f"Barrels delivered: {barrels_delivered}")

    try:
        with db.engine.begin() as connection:
            # Retrieve current inventory details
            logger.debug("Fetching current inventory from global_inventory.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT red_ml, green_ml, blue_ml, dark_ml, gold
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
            gold = inventory_row['gold']

            logger.debug(
                f"Inventory before processing: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}, gold={gold}"
            )

            total_gold_spent = 0

            # Mapping of index to color
            color_map = {0: 'red', 1: 'green', 2: 'blue', 3: 'dark'}

            for barrel in barrels_delivered:
                logger.debug(f"Processing delivered barrel: {barrel.dict()}")
                potion_type = barrel.potion_type
                quantity = barrel.quantity

                # Identify color based on potion_type
                try:
                    color_index = potion_type.index(1)
                    color = color_map.get(color_index)
                    if not color:
                        logger.warning(
                            f"Invalid potion_type in delivered barrel SKU {barrel.sku}. Skipping."
                        )
                        continue
                    logger.debug(f"Identified color '{color}' for potion_type {potion_type}")
                except ValueError:
                    logger.warning(
                        f"Invalid potion_type in delivered barrel SKU {barrel.sku}. Skipping."
                    )
                    continue

                ml_to_add = barrel.ml_per_barrel * quantity
                gold_cost = barrel.price * quantity

                logger.debug(
                    f"Barrel SKU {barrel.sku}: ml_to_add={ml_to_add}, gold_cost={gold_cost}"
                )

                # Check if there is enough gold to purchase barrel
                if gold < gold_cost:
                    logger.error(
                        f"Not enough gold to pay for delivered barrel SKU {barrel.sku}. "
                        f"Needed: {gold_cost}, Available: {gold}."
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient gold to pay for delivered barrels SKU {barrel.sku}.",
                    )

                # Update ML levels and deduct gold
                if color == 'red':
                    red_ml += ml_to_add
                elif color == 'green':
                    green_ml += ml_to_add
                elif color == 'blue':
                    blue_ml += ml_to_add
                elif color == 'dark':
                    dark_ml += ml_to_add

                gold -= gold_cost
                total_gold_spent += gold_cost

                logger.debug(
                    f"Updated inventory after processing barrel SKU {barrel.sku}: "
                    f"{color}_ml={locals()[f'{color}_ml']}, gold={gold}"
                )

            # Update global_inventory with new ML levels and gold
            logger.debug("Updating global_inventory with new ML levels and gold.")
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE global_inventory
                    SET red_ml = :red_ml,
                        green_ml = :green_ml,
                        blue_ml = :blue_ml,
                        dark_ml = :dark_ml,
                        gold = :gold
                    WHERE id = 1;
                    """
                ),
                {
                    'red_ml': red_ml,
                    'green_ml': green_ml,
                    'blue_ml': blue_ml,
                    'dark_ml': dark_ml,
                    'gold': gold,
                },
            )

            logger.info(
                f"Processed order_id {order_id}: Spent {total_gold_spent} gold on barrels."
            )
            logger.debug(
                f"Inventory after processing: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}, gold={gold}"
            )

    except HTTPException as e:
        # Re-raise HTTPExceptions after logging
        logger.error(f"HTTPException in post_deliver_barrels: {e.detail}")
        raise e
    except Exception as e:
        # Log exception with traceback
        logger.exception(f"Unhandled exception in post_deliver_barrels: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.debug("Returning response: {'status': 'OK'}")
    logger.info(f"Delivery for order_id {order_id} completed successfully.")
    return {"status": "OK"}


# Gets called once a day
@router.post("/plan", summary="Get Wholesale Purchase Plan", description="Generates purchase plan based on wholesale catalog.")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Generates wholesale purchase plan based on current inventory.
    """
    logger.info("Starting get_wholesale_purchase_plan endpoint.")
    logger.debug(f"Received wholesale_catalog: {[barrel.dict() for barrel in wholesale_catalog]}")

    try:
        with db.engine.begin() as connection:
            # Retrieve current inventory and gold
            logger.debug("Fetching current inventory and gold from global_inventory.")
            result = connection.execute(
                sqlalchemy.text("""
                    SELECT red_ml, green_ml, blue_ml, dark_ml, gold, ml_capacity_units
                    FROM global_inventory
                    WHERE id = 1;
                """)
            )
            inventory = result.mappings().fetchone()
            if not inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory not found.")

            red_ml = inventory['red_ml']
            green_ml = inventory['green_ml']
            blue_ml = inventory['blue_ml']
            dark_ml = inventory['dark_ml']
            gold = inventory['gold']
            ml_capacity_units = inventory['ml_capacity_units']

            logger.debug(f"Current Inventory: red_ml={red_ml}, green_ml={green_ml}, blue_ml={blue_ml}, dark_ml={dark_ml}")
            logger.debug(f"Current Gold: {gold}, ML Capacity Units: {ml_capacity_units}")

            # Calculate total ML capacity and remaining capacity
            total_ml_capacity = ml_capacity_units * ML_CAPACITY_PER_UNIT  # Each unit allows 10000 ML
            total_ml_used = red_ml + green_ml + blue_ml + dark_ml
            remaining_capacity = total_ml_capacity - total_ml_used

            logger.debug(f"Total ML Capacity: {total_ml_capacity}, Total ML Used: {total_ml_used}, Remaining Capacity: {remaining_capacity}")

            # Define purchasing order and filter available barrels
            purchasing_order = ['green', 'red', 'blue']
            color_to_skus = {
                'green': ['SMALL_GREEN_BARREL', 'MEDIUM_GREEN_BARREL', 'LARGE_GREEN_BARREL'],
                'red': ['SMALL_RED_BARREL', 'MEDIUM_RED_BARREL', 'LARGE_RED_BARREL'],
                'blue': ['SMALL_BLUE_BARREL', 'MEDIUM_BLUE_BARREL', 'LARGE_BLUE_BARREL']
            }

            # Create mapping from SKU to Barrel for quick access
            sku_to_barrel = {barrel.sku: barrel for barrel in wholesale_catalog}

            logger.debug(f"Purchasing Order: {purchasing_order}")
            logger.debug(f"SKU to Barrel Mapping: {sku_to_barrel}")

            purchase_plan = []

            # Determine purchasing strategy based on gold
            if gold < 200:
                logger.info("Gold is less than 200. Purchasing Green Barrels to build capital.")
                colors_to_purchase = ['green']
            elif 200 <= gold < 500:
                logger.info("Gold is between 200 and 500. Purchasing Green, Red, and Blue Barrels in order.")
                colors_to_purchase = ['green', 'red', 'blue']
            else:
                logger.info("Gold is 500 or more. Purchasing Green, Red, and Blue Barrels and considering ML capacity expansion.")
                colors_to_purchase = ['green', 'red', 'blue']
                # TODO: Implement further logic when data is collected

            # Iterate through purchasing order and add barrels to purchase_plan
            for color in colors_to_purchase:
                logger.debug(f"Processing color: {color}")

                # Get available SKUs for current color
                available_skus = color_to_skus.get(color, [])
                logger.debug(f"Available SKUs for color '{color}': {available_skus}")

                # Iterate through SKUs in ascending order of size (assuming SMALL to LARGE)
                for sku in available_skus:
                    barrel = sku_to_barrel.get(sku)
                    if not barrel:
                        logger.debug(f"Barrel SKU '{sku}' not available in wholesale catalog. Skipping.")
                        continue  # Barrel not available for purchase

                    # Check if purchasing this barrel exceeds ML capacity
                    if remaining_capacity < barrel.ml_per_barrel:
                        logger.warning(f"Not enough ML capacity to purchase '{sku}'. Required: {barrel.ml_per_barrel}, Available: {remaining_capacity}. Skipping.")
                        continue

                    # Check if there's enough gold to purchase this barrel
                    if gold < barrel.price:
                        logger.warning(f"Not enough gold to purchase '{sku}'. Price: {barrel.price}, Available Gold: {gold}. Skipping.")
                        continue

                    # Decide quantity to purchase
                    quantity_to_purchase = 1 # TODO: Decide amount from data analytics and future algorithm

                    # Add barrel to purchase plan
                    purchase_plan.append({
                        "sku": sku,
                        "quantity": quantity_to_purchase
                    })
                    logger.info(f"Added '{sku}' x{quantity_to_purchase} to purchase plan.")

                    # Update gold and remaining_capacity
                    gold -= barrel.price * quantity_to_purchase
                    remaining_capacity -= barrel.ml_per_barrel * quantity_to_purchase

                    logger.debug(f"Updated Gold: {gold}, Remaining Capacity: {remaining_capacity}")

            logger.debug(f"Final Purchase Plan: {purchase_plan}")
            logger.info("Completed generating barrel purchase plan.")

            return purchase_plan

    except HTTPException as he:
        logger.error(f"HTTPException in get_wholesale_purchase_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_wholesale_purchase_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
