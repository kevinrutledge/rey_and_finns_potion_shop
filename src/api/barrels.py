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
            result = connection.execute(sqlalchemy.text(
                """
                SELECT red_ml, green_ml, blue_ml, dark_ml, gold
                FROM global_inventory
                WHERE id = 1;
                """
            ))
            inventory_row = result.mappings().fetchone()
            if not inventory_row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory not found.")

            red_ml = inventory_row['red_ml']
            green_ml = inventory_row['green_ml']
            blue_ml = inventory_row['blue_ml']
            dark_ml = inventory_row['dark_ml']
            gold = inventory_row['gold']

            logger.debug(f"Current inventory ml - red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}, gold: {gold}")

            total_gold_spent = 0

            # Mapping of index to color
            color_map = {0: 'red', 1: 'green', 2: 'blue', 3: 'dark'}

            for barrel in barrels_delivered:
                logger.debug(f"Processing barrel: {barrel.dict()}")
                potion_type = barrel.potion_type
                quantity = barrel.quantity

                try:
                    # Identify the color based on potion_type
                    color_index = potion_type.index(1)
                    color = color_map.get(color_index)
                    if not color:
                        logger.warning(f"Invalid potion_type in delivered barrel SKU {barrel.sku}. Skipping.")
                        continue
                except ValueError:
                    logger.warning(f"Invalid potion_type in delivered barrel SKU {barrel.sku}. Skipping.")
                    continue

                ml_to_add = barrel.ml_per_barrel * quantity
                gold_cost = barrel.price * quantity

                # Check if there is enough gold to purchase the barrel
                if gold < gold_cost:
                    logger.error(f"Not enough gold to pay for delivered barrel SKU {barrel.sku}. Needed: {gold_cost}, Available: {gold}.")
                    raise HTTPException(status_code=400, detail="Insufficient gold to pay for delivered barrels.")

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

                logger.info(f"Added {ml_to_add} ML of {color} to inventory from barrel SKU {barrel.sku}. Spent {gold_cost} gold.")
                logger.debug(f"Updated ML levels - red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}, gold: {gold}")

            # Update global_inventory with new ML levels and gold
            connection.execute(sqlalchemy.text(
                """
                UPDATE global_inventory
                SET red_ml = :red_ml,
                    green_ml = :green_ml,
                    blue_ml = :blue_ml,
                    dark_ml = :dark_ml,
                    gold = :gold
                WHERE id = 1;
                """
            ), {
                'red_ml': red_ml,
                'green_ml': green_ml,
                'blue_ml': blue_ml,
                'dark_ml': dark_ml,
                'gold': gold
            })

            logger.info("Updated global inventory ML levels and gold after processing delivered barrels.")
            logger.info(f"Total gold spent on delivered barrels: {total_gold_spent}.")
            logger.debug(f"Final inventory ml - red_ml: {red_ml}, green_ml: {green_ml}, blue_ml: {blue_ml}, dark_ml: {dark_ml}, gold: {gold}")
            logger.info("Ending post_deliver_barrels endpoint.")
            return {"status": "OK"}

    except HTTPException as e:
        # Re-raise HTTPExceptions
        logger.error(f"HTTPException in post_deliver_barrels: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error in post_deliver_barrels: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
            # Retrieve current inventory details
            result = connection.execute(sqlalchemy.text(
                """
                SELECT red_ml, green_ml, blue_ml, dark_ml, gold, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
                """
            ))
            inventory_row = result.mappings().fetchone()
            if not inventory_row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory not found.")
    
            red_ml = inventory_row['red_ml']
            green_ml = inventory_row['green_ml']
            blue_ml = inventory_row['blue_ml']
            dark_ml = inventory_row['dark_ml']
            gold = inventory_row['gold']
            ml_capacity_units = inventory_row['ml_capacity_units']
    
            # Calculate total ML and remaining capacity
            total_ml = red_ml + green_ml + blue_ml + dark_ml
            ml_capacity = ml_capacity_units * 10000  # Each ML capacity unit allows 10,000 ML storage
            remaining_capacity = ml_capacity - total_ml
            logger.debug(f"Current total ML: {total_ml}, ML capacity: {ml_capacity}, remaining capacity: {remaining_capacity}")
            logger.debug(f"Current gold: {gold}")
    
            purchase_plan = []
    
            # Create mapping from SKU to Barrel for easy access
            sku_to_barrel = {barrel.sku: barrel for barrel in wholesale_catalog}
    
            # Define desired ML per color (can be adjusted as needed)
            desired_ml_per_color = {
                'red': 5000,
                'green': 5000,
                'blue': 5000,
                'dark': 5000
            }
    
            # Current ML levels by color
            color_levels = {
                'red': red_ml,
                'green': green_ml,
                'blue': blue_ml,
                'dark': dark_ml
            }
    
            # Sort colors by how much ML is needed (ascending order)
            colors_needed = sorted(desired_ml_per_color.items(), key=lambda x: x[1] - color_levels.get(x[0], 0))
            logger.debug(f"Colors sorted by ML needed: {colors_needed}")
    
            # Maximum number of barrels to plan to buy per request to avoid over-purchasing
            max_barrels_to_buy = 2
    
            # Initialize count of barrels planned to buy
            barrels_planned = 0
    
            # Priority order for purchasing barrels when gold is low
            priority_order = ['green', 'red', 'blue', 'dark']
    
            for color, desired_ml in colors_needed:
                if color_levels[color] >= desired_ml:
                    continue  # Skip colors that have met desired ML
                
                # Get list of possible barrels for current color, sorted by size (small to large)
                color_to_barrels = {
                    'red': ['SMALL_RED_BARREL', 'MEDIUM_RED_BARREL', 'LARGE_RED_BARREL'],
                    'green': ['SMALL_GREEN_BARREL', 'MEDIUM_GREEN_BARREL', 'LARGE_GREEN_BARREL'],
                    'blue': ['SMALL_BLUE_BARREL', 'MEDIUM_BLUE_BARREL', 'LARGE_BLUE_BARREL'],
                    'dark': ['LARGE_DARK_BARREL']  # Only large dark barrels available
                }
                barrel_skus = color_to_barrels[color]
                
                for barrel_sku in barrel_skus:
                    if barrels_planned >= max_barrels_to_buy:
                        break  # Reached purchase limit
                    
                    if barrel_sku in sku_to_barrel:
                        barrel = sku_to_barrel[barrel_sku]
                        barrel_total_ml = barrel.ml_per_barrel
                        barrel_price = barrel.price
                        barrel_quantity_available = barrel.quantity
                        logger.debug(f"Considering purchase of {barrel_sku}: price {barrel_price}, ML {barrel_total_ml}, quantity available {barrel_quantity_available}, color {color}")
                        
                        # Check if there is enough ML capacity to store barrel
                        if remaining_capacity < barrel_total_ml:
                            logger.info(f"Not enough ML capacity to store {barrel_sku}. Required: {barrel_total_ml}, Available: {remaining_capacity}")
                            continue  # Skip this barrel
                
                        # Check if there is enough gold to purchase barrel
                        if gold < barrel_price:
                            logger.info(f"Not enough gold to buy {barrel_sku}. Required: {barrel_price}, Available: {gold}")
                            continue  # Skip this barrel
                
                        # Decide how many barrels to buy (start with 1)
                        quantity_to_buy = 1
                        quantity_to_buy = min(quantity_to_buy, barrel_quantity_available)
                        if quantity_to_buy <= 0:
                            logger.info(f"No available quantity to buy for {barrel_sku}.")
                            continue  # Skip if no quantity is available
                
                        # Add to purchase plan
                        purchase_plan.append({
                            "sku": barrel_sku,
                            "quantity": quantity_to_buy
                        })
                
                        # Update gold, remaining capacity, and color ML levels
                        gold -= barrel_price * quantity_to_buy
                        remaining_capacity -= barrel_total_ml * quantity_to_buy
                        color_levels[color] += barrel_total_ml * quantity_to_buy
                        barrels_planned += 1
                
                        logger.info(f"Planning to purchase {quantity_to_buy} of {barrel_sku}")
                        logger.debug(f"Updated gold: {gold}, remaining capacity: {remaining_capacity}, updated {color} ML: {color_levels[color]}")
                    else:
                        logger.info(f"{barrel_sku} not available in catalog")
                
                if barrels_planned >= max_barrels_to_buy:
                    break  # Reached purchase limit
    
            logger.info("Completed wholesale purchase plan.")
            logger.info("Ending get_wholesale_purchase_plan endpoint.")
            logger.debug(f"Purchase plan: {purchase_plan}")
            return purchase_plan
    
    except Exception as e:
        logger.error(f"Error in get_wholesale_purchase_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
