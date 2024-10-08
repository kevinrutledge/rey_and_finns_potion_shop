import sqlalchemy
import logging
from src import database as db
from src.api import auth
from src import utilities as ut
from src.utilities import Utils as utl
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: List[int]  # [red, green, blue, dark]
    price: int
    quantity: int  # Quantity available for sale in catalog

class BarrelPurchase(BaseModel):
    sku: str
    quantity: int

class BarrelDelivery(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: List[int]  # [red, green, blue, dark]
    price: int
    quantity: int


@router.post("/deliver/{order_id}", summary="Deliver Barrels", description="Process delivery of barrels.")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """
    Process delivery of barrels to inventory.
    """
    logger.info(f"Processing delivery for order_id={order_id}. Number of barrels delivered: {len(barrels_delivered)}.")
    logger.debug(f"Barrels Delivered: {barrels_delivered}")

    try:
        with db.engine.begin() as connection:
            # Fetch current gold and ML capacity from global_inventory
            logger.debug("Fetching current gold and ML capacity from global_inventory.")
            query = """
                SELECT gold, total_ml, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            inventory = result.mappings().fetchone()

            if not inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            current_gold = inventory['gold']
            current_total_ml = inventory['total_ml']
            ml_capacity_units = inventory['ml_capacity_units']
            ml_capacity_limit = ml_capacity_units * ut.ML_CAPACITY_PER_UNIT

            logger.debug(f"Current Gold: {current_gold}, Total ML: {current_total_ml}, ML Capacity Limit: {ml_capacity_limit}")

            # Calculate total gold cost
            total_gold_cost = sum(barrel.price * barrel.quantity for barrel in barrels_delivered)
            logger.debug(f"Total Gold Cost for Delivery: {total_gold_cost}")

            # Check if sufficient gold is available
            if current_gold < total_gold_cost:
                logger.error(f"Insufficient gold. Available: {current_gold}, Required: {total_gold_cost}")
                raise HTTPException(status_code=400, detail="Insufficient gold to complete purchase.")

            # Calculate total ML to add
            total_ml_to_add = sum(barrel.ml_per_barrel * barrel.quantity for barrel in barrels_delivered)
            total_ml_after_adding = current_total_ml + total_ml_to_add
            logger.debug(f"Total ML to Add: {total_ml_to_add}, Total ML After Adding: {total_ml_after_adding}")

            # Check if ML capacity is sufficient
            if total_ml_after_adding > ml_capacity_limit:
                logger.error(f"Insufficient ML capacity. ML Capacity Limit: {ml_capacity_limit}, Total ML After Adding: {total_ml_after_adding}")
                raise HTTPException(status_code=400, detail="Insufficient ML capacity to store the delivered barrels.")

            # Aggregate ML additions per color
            total_red_ml = 0
            total_green_ml = 0
            total_blue_ml = 0
            total_dark_ml = 0

            for barrel in barrels_delivered:
                red_flag, green_flag, blue_flag, dark_flag = barrel.potion_type

                red_ml_to_add = red_flag * barrel.ml_per_barrel * barrel.quantity
                green_ml_to_add = green_flag * barrel.ml_per_barrel * barrel.quantity
                blue_ml_to_add = blue_flag * barrel.ml_per_barrel * barrel.quantity
                dark_ml_to_add = dark_flag * barrel.ml_per_barrel * barrel.quantity

                total_red_ml += red_ml_to_add
                total_green_ml += green_ml_to_add
                total_blue_ml += blue_ml_to_add
                total_dark_ml += dark_ml_to_add

                logger.debug(f"Barrel SKU {barrel.sku}: Adding Red={red_ml_to_add}, Green={green_ml_to_add}, Blue={blue_ml_to_add}, Dark={dark_ml_to_add}")

            # Update global_inventory
            update_inventory_query = """
                UPDATE global_inventory
                SET red_ml = red_ml + :red_ml,
                    green_ml = green_ml + :green_ml,
                    blue_ml = blue_ml + :blue_ml,
                    dark_ml = dark_ml + :dark_ml,
                    total_ml = total_ml + :total_ml,
                    gold = gold - :gold_spent
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_inventory_query),
                {
                    "red_ml": total_red_ml,
                    "green_ml": total_green_ml,
                    "blue_ml": total_blue_ml,
                    "dark_ml": total_dark_ml,
                    "total_ml": total_ml_to_add,
                    "gold_spent": total_gold_cost
                }
            )
            logger.info(f"Updated global_inventory with new MLs and deducted gold.")

            # Log updated inventory
            logger.debug("Fetching updated inventory from global_inventory.")
            query_updated_inventory = """
                SELECT gold, red_ml, green_ml, blue_ml, dark_ml, total_ml
                FROM global_inventory
                WHERE id = 1;
            """
            updated_inventory = connection.execute(sqlalchemy.text(query_updated_inventory)).mappings().fetchone()
            logger.debug(f"Updated Inventory: {updated_inventory}")

    except HTTPException as he:
        logger.error(f"HTTPException in post_deliver_barrels: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in post_deliver_barrels: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"Successfully processed delivery for order_id {order_id}.")
    return {"success": True}


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
        purchase_plan = utl.calculate_purchase_plan(
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
