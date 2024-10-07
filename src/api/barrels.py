import sqlalchemy
import logging
from src import database as db
from src.utilities import TimeUtils as ti
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from datetime import datetime

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

# Mapping of in-game days to preferred potion colors
DAY_POTION_PREFERENCES = {
    "Hearthday": ["green", "yellow"],
    "Crownday": ["red", "yellow"],
    "Blesseday": ["green", "blue"],
    "Soulday": ["dark", "blue"],
    "Edgeday": ["red", "yellow"],
    "Bloomday": ["green", "blue"],
    "Aracanaday": ["blue", "dark"]
}

def get_color_from_potion_type(potion_type: list[int]) -> str:
    """
    Determines the color based on potion_type list.
    Assumes only one color is set to 100 or a combination exists.
    """
    color_map = {0: 'red', 1: 'green', 2: 'blue', 3: 'dark'}
    if sum(potion_type) != 100:
        logger.warning(f"Invalid potion_type {potion_type}. Sum must be 100.")
        # Normalize potion_type to sum to 100
        if sum(potion_type) > 0:
            factor = 100 / sum(potion_type)
            potion_type = [int(x * factor) for x in potion_type]
            logger.debug(f"Normalized potion_type to {potion_type}.")
        else:
            # All zeros; return 'unknown'
            logger.debug("All potion_type values are zero. Returning 'unknown'.")
            return 'unknown'

    # Check for single color dominance
    try:
        index = potion_type.index(100)
        return color_map.get(index, 'unknown')
    except ValueError:
        # Multiple colors; prioritize based on highest value
        max_ml = max(potion_type)
        indices = [i for i, x in enumerate(potion_type) if x == max_ml]
        if indices:
            return color_map.get(indices[0], 'unknown')
        return 'unknown'


@router.post("/deliver/{order_id}", summary="Deliver Barrels", description="Process delivery of barrels.")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """
    Process delivery of barrels to inventory.
    """
    logger.info(f"Starting post_deliver_barrels endpoint for order_id {order_id}.")
    logger.debug(f"Barrels delivered: {barrels_delivered}")
    
    try:
        with db.engine.begin() as connection:
            # Insert a new barrel visit
            logger.debug("Inserting barrel visit into 'barrel_visits' table.")
            current_time = datetime.now(tz=ti.LOCAL_TIMEZONE)
            in_game_day, in_game_hour = ti.compute_in_game_time(current_time)
            logger.debug(f"Computed in-game time for barrel visit - Day: {in_game_day}, Hour: {in_game_hour}")
            
            result = connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO barrel_visits (visit_time, in_game_day, in_game_hour)
                    VALUES (:visit_time, :in_game_day, :in_game_hour)
                    RETURNING barrel_visit_id;
                    """
                ),
                {
                    'visit_time': current_time,
                    'in_game_day': in_game_day,
                    'in_game_hour': in_game_hour
                }
            )
            barrel_visit = result.mappings().fetchone()
            if not barrel_visit:
                logger.error("Failed to insert barrel_visit record.")
                raise HTTPException(status_code=500, detail="Failed to record barrel visit.")
            barrel_visit_id = barrel_visit['barrel_visit_id']
            logger.info(f"Inserted barrel visit with barrel_visit_id {barrel_visit_id} at {current_time.isoformat()}.")

            # Retrieve current inventory details
            logger.debug("Fetching current inventory from 'global_inventory'.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT red_ml, green_ml, blue_ml, dark_ml, gold, ml_capacity_units
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
            ml_capacity_units = inventory_row['ml_capacity_units']
    
            logger.debug(
                f"Inventory before processing: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}, gold={gold}, ml_capacity_units={ml_capacity_units}"
            )
    
            total_gold_spent = 0
    
            # Mapping of color names to indices
            color_map = {'red': 'red_ml', 'green': 'green_ml', 'blue': 'blue_ml', 'dark': 'dark_ml'}
    
            for barrel in barrels_delivered:
                logger.debug(f"Processing delivered barrel: {barrel.dict()}")
                potion_type = barrel.potion_type
                quantity = barrel.quantity
    
                # Identify color based on potion_type
                color = get_color_from_potion_type(potion_type)
                if color == 'unknown':
                    logger.warning(f"Invalid or mixed potion_type in delivered barrel SKU {barrel.sku}. Skipping.")
                    continue
                logger.debug(f"Identified color '{color}' for potion_type {potion_type}")
    
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
                current_ml_field = color_map[color]
                current_ml = inventory_row[current_ml_field]
                new_ml = current_ml + ml_to_add
    
                logger.debug(f"Updating {current_ml_field}: {current_ml} + {ml_to_add} = {new_ml}")
    
                # Update inventory
                update_inventory_query = sqlalchemy.text(
                    f"""
                    UPDATE global_inventory
                    SET {current_ml_field} = :new_ml,
                        gold = :new_gold
                    WHERE id = 1;
                    """
                )
                connection.execute(
                    update_inventory_query,
                    {
                        'new_ml': new_ml,
                        'new_gold': gold - gold_cost
                    }
                )
    
                # Update local variables
                inventory_row[current_ml_field] = new_ml
                gold -= gold_cost
                total_gold_spent += gold_cost
    
                logger.debug(
                    f"Updated inventory: {current_ml_field}={new_ml}, gold={gold}"
                )
    
                # Insert barrel record linked to barrel_visit
                logger.debug(f"Inserting barrel SKU {barrel.sku} into 'barrels' table linked to barrel_visit_id {barrel_visit_id}.")
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO barrels (sku, ml_per_barrel, potion_type, price, quantity, barrel_visit_id)
                        VALUES (:sku, :ml_per_barrel, :potion_type, :price, :quantity, :barrel_visit_id);
                        """
                    ),
                    {
                        'sku': barrel.sku,
                        'ml_per_barrel': barrel.ml_per_barrel,
                        'potion_type': ','.join(map(str, potion_type)),  # Store as comma-separated string
                        'price': barrel.price,
                        'quantity': barrel.quantity,
                        'barrel_visit_id': barrel_visit_id
                    }
                )
                logger.info(f"Inserted barrel SKU {barrel.sku} with quantity {quantity} linked to barrel_visit_id {barrel_visit_id}.")
    
            # Log total gold spent
            logger.debug(f"Total gold spent on barrels: {total_gold_spent}")
    
    except HTTPException as e:
        logger.error(f"HTTPException in post_deliver_barrels: {e.detail}")
        raise e
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"Unhandled exception in post_deliver_barrels: {e}\nTraceback: {traceback_str}")
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
            # Fetch current in-game day
            current_time = datetime.now(tz=ti.LOCAL_TIMEZONE)
            in_game_day, _ = ti.compute_in_game_time(current_time)
            logger.debug(f"Current in-game day: {in_game_day}")
            
            # Get preferred potion colors for the day
            preferred_colors = DAY_POTION_PREFERENCES.get(in_game_day, ["green", "blue", "red"])
            logger.info(f"Preferred potion colors for {in_game_day}: {preferred_colors}")
            
            # Fetch current inventory details
            logger.debug("Fetching current inventory from 'global_inventory'.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT red_ml, green_ml, blue_ml, dark_ml, gold, ml_capacity_units
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
            ml_capacity_units = inventory_row['ml_capacity_units']
    
            logger.debug(
                f"Inventory before processing: red_ml={red_ml}, green_ml={green_ml}, "
                f"blue_ml={blue_ml}, dark_ml={dark_ml}, gold={gold}, ml_capacity_units={ml_capacity_units}"
            )
    
            total_gold_spent = 0
            purchase_plan = []
    
            # Define purchasing order based on preferred colors
            for color in preferred_colors:
                logger.debug(f"Processing purchases for color: {color}")
                
                # Filter available barrels matching the preferred color
                available_barrels = [
                    barrel for barrel in wholesale_catalog 
                    if get_color_from_potion_type(barrel.potion_type) == color
                ]
                logger.debug(f"Available barrels for color '{color}': {[barrel.sku for barrel in available_barrels]}")
    
                # Sort barrels by price ascending to buy cheaper first
                available_barrels.sort(key=lambda x: x.price)
    
                for barrel in available_barrels:
                    logger.debug(f"Evaluating barrel SKU: {barrel.sku}, Quantity Available: {barrel.quantity}, Price: {barrel.price}")
    
                    # Check if gold is sufficient
                    if gold < barrel.price:
                        logger.warning(f"Insufficient gold to purchase barrel SKU {barrel.sku}. Needed: {barrel.price}, Available: {gold}.")
                        continue
    
                    # Decide how many barrels to purchase (e.g., purchase as many as possible)
                    max_affordable = gold // barrel.price
                    purchase_quantity = min(barrel.quantity, max_affordable)
    
                    if purchase_quantity <= 0:
                        logger.warning(f"No affordable quantity available for barrel SKU {barrel.sku}.")
                        continue
    
                    # Add to purchase plan
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": purchase_quantity
                    })
                    logger.info(f"Planned to purchase {purchase_quantity} of barrel SKU {barrel.sku}.")
    
                    # Update gold and total_gold_spent
                    gold -= barrel.price * purchase_quantity
                    total_gold_spent += barrel.price * purchase_quantity
    
                    logger.debug(f"Updated gold: {gold}, Total gold spent: {total_gold_spent}")
    
            # Log final purchase plan
            logger.debug(f"Final Purchase Plan: {purchase_plan}")
            logger.info("Completed generating barrel purchase plan.")
    
            return purchase_plan

    except HTTPException as he:
        logger.error(f"HTTPException in get_wholesale_purchase_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_wholesale_purchase_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
