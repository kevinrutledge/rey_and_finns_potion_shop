import sqlalchemy
import logging
from src import database as db
from src import potion_coefficients as po
from src.utilities import Utils as ut
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
    logger.info(f"Endpoint /barrels/deliver/{order_id} called with {len(barrels_delivered)} barrels.")
    logger.debug(f"Received barrels_delivered: {barrels_delivered}")

    try:
        with db.engine.begin() as connection:
            for barrel in barrels_delivered:
                sku = barrel.sku
                quantity = barrel.quantity
                ml_per_barrel = barrel.ml_per_barrel
                potion_type = barrel.potion_type  # [red, green, blue, dark]
                price = barrel.price

                logger.debug(f"Processing delivered barrel - SKU: {sku}, Quantity: {quantity}, ML per barrel: {ml_per_barrel}, Potion Type: {potion_type}, Price: {price}")

                # Validate potion_type
                if len(potion_type) != 4 or sum(potion_type) != 100:
                    logger.error(f"Invalid potion_type for SKU {sku}: {potion_type}")
                    raise HTTPException(status_code=400, detail=f"Invalid potion_type for SKU {sku}")

                # Fetch the corresponding potion from potions table
                logger.debug(f"Fetching potion details for SKU: {sku}")
                query_potion = """
                    SELECT potion_id, red_ml, green_ml, blue_ml, dark_ml, current_quantity
                    FROM potions
                    WHERE sku = :sku
                    LIMIT 1;
                """
                result = connection.execute(
                    sqlalchemy.text(query_potion),
                    {'sku': sku}
                )
                potion = result.mappings().fetchone()

                if not potion:
                    logger.error(f"No potion found with SKU: {sku}")
                    raise HTTPException(status_code=400, detail=f"No potion found with SKU: {sku}")

                potion_id = potion['potion_id']
                current_quantity = potion['current_quantity']

                logger.debug(f"Found Potion ID: {potion_id} with Current Quantity: {current_quantity}")

                # Calculate total ML to add
                total_ml_to_add = ml_per_barrel * quantity
                logger.debug(f"Total ML to add for SKU {sku}: {total_ml_to_add}")

                # Update global_inventory ML counts
                ml_fields = ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']
                for idx, color_ml in enumerate(potion_type):
                    color_field = ml_fields[idx]
                    if color_ml > 0:
                        update_ml_query = f"""
                            UPDATE global_inventory
                            SET {color_field} = {color_field} + :ml_to_add
                            WHERE id = 1;
                        """
                        connection.execute(
                            sqlalchemy.text(update_ml_query),
                            {'ml_to_add': color_ml * quantity}
                        )
                        logger.debug(f"Added {color_ml * quantity} ML to {color_field} in global_inventory.")

                # Update total_ml in global_inventory
                logger.debug("Recalculating total_ml in global_inventory.")
                query_total_ml = """
                    SELECT red_ml, green_ml, blue_ml, dark_ml
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
                logger.debug(f"Total ML after addition: {total_ml}")

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

                # Update potion's current_quantity
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
                logger.info(f"Updated potion ID {potion_id} quantity to {new_quantity}.")

                # Deduct gold based on purchase
                total_cost = price * quantity
                logger.debug(f"Total cost for SKU {sku}: {total_cost}")

                update_gold_query = """
                    UPDATE global_inventory
                    SET gold = gold - :cost
                    WHERE id = 1;
                """
                connection.execute(
                    sqlalchemy.text(update_gold_query),
                    {'cost': total_cost}
                )
                logger.debug(f"Deducted {total_cost} gold from global_inventory.")

        logger.info(f"Successfully processed delivery for order_id {order_id}.")
        return {"success": True}

    except HTTPException as he:
        logger.error(f"HTTPException in post_deliver_barrels: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in post_deliver_barrels: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Gets called once a day
@router.post("/plan", summary="Get Wholesale Purchase Plan", description="Generates purchase plan based on wholesale catalog.")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Generates wholesale purchase plan based on current inventory.
    """
    logger.info("Endpoint /barrels/plan called.")
    logger.debug(f"Received wholesale_catalog: {wholesale_catalog}")

    try:
        with db.engine.begin() as connection:
            # Fetch current inventory and gold from global_inventory
            logger.debug("Fetching current inventory and gold from global_inventory.")
            query_inventory = """
                SELECT gold, total_potions, total_ml, red_ml, green_ml, blue_ml, dark_ml, potion_capacity_units, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_inventory))
            row = result.mappings().fetchone()

            if not row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            # Prepare current inventory dictionary
            current_inventory = {
                'gold': row['gold'],
                'total_potions': row['total_potions'],
                'total_ml': row['total_ml'],
                'red_ml': row['red_ml'],
                'green_ml': row['green_ml'],
                'blue_ml': row['blue_ml'],
                'dark_ml': row['dark_ml'],
                'potion_capacity_units': row['potion_capacity_units'],
                'ml_capacity_units': row['ml_capacity_units'],
            }

            logger.debug(f"Current Inventory: {current_inventory}")

        # Calculate purchase plan
        purchase_plan = ut.calculate_purchase_plan(
            wholesale_catalog=wholesale_catalog,
            current_inventory=current_inventory,
            gold=current_inventory['gold'],
            potion_capacity_units=current_inventory['potion_capacity_units'],
            ml_capacity_units=current_inventory['ml_capacity_units']
        )

        logger.info(f"Generated purchase plan: {purchase_plan}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_wholesale_purchase_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_wholesale_purchase_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_wholesale_purchase_plan endpoint.")
    logger.debug(f"Returning purchase_plan: {purchase_plan}")
    return purchase_plan
