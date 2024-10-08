import sqlalchemy
import logging
from src import database as db
from src import potion_coefficients as po
from src.api import auth
from src.utilities import Utils as ut
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from datetime import datetime
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
            # Fetch current gold from global_inventory
            logger.debug("Fetching current gold from global_inventory.")
            query_gold = """
                SELECT gold
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_gold))
            current_gold_row = result.mappings().fetchone()
            if not current_gold_row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            current_gold = current_gold_row['gold']
            logger.debug(f"Current Gold: {current_gold}")

            # Calculate total gold cost
            total_gold_cost = sum(barrel.price * barrel.quantity for barrel in barrels_delivered)
            logger.debug(f"Total Gold Cost for Delivery: {total_gold_cost}")

            # Check if sufficient gold is available
            if current_gold < total_gold_cost:
                logger.error(f"Insufficient gold. Available: {current_gold}, Required: {total_gold_cost}")
                raise HTTPException(status_code=400, detail="Insufficient gold to complete purchase.")

            # Add ML of each color to global_inventory
            logger.debug("Adding ML from delivered barrels to global_inventory.")
            for barrel in barrels_delivered:
                red_flag, green_flag, blue_flag, dark_flag = barrel.potion_type

                # Calculate ML to add per colors
                red_ml_to_add = red_flag * barrel.ml_per_barrel * barrel.quantity
                green_ml_to_add = green_flag * barrel.ml_per_barrel * barrel.quantity
                blue_ml_to_add = blue_flag * barrel.ml_per_barrel * barrel.quantity
                dark_ml_to_add = dark_flag * barrel.ml_per_barrel * barrel.quantity
                total_ml_to_add = barrel.ml_per_barrel * barrel.quantity

                logger.debug(f"Adding ML for SKU {barrel.sku}: Red={red_ml_to_add}, Green={green_ml_to_add}, "
                             f"Blue={blue_ml_to_add}, Dark={dark_ml_to_add}")

                update_ml_query = """
                    UPDATE global_inventory
                    SET red_ml = red_ml + :red_ml,
                        green_ml = green_ml + :green_ml,
                        blue_ml = blue_ml + :blue_ml,
                        dark_ml = dark_ml + :dark_ml,
                        total_ml = total_ml + :total_ml
                    WHERE id = 1;
                """
                connection.execute(
                    sqlalchemy.text(update_ml_query),
                    {
                        "red_ml": red_ml_to_add,
                        "green_ml": green_ml_to_add,
                        "blue_ml": blue_ml_to_add,
                        "dark_ml": dark_ml_to_add,
                        "total_ml": total_ml_to_add
                    }
                )
                logger.info(f"Updated ML in global_inventory for SKU {barrel.sku}.")

            # Subtract total gold cost from global_inventory
            logger.debug("Subtracting total gold cost from global_inventory.")
            update_gold_query = """
                UPDATE global_inventory
                SET gold = gold - :total_gold_cost
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_gold_query),
                {"total_gold_cost": total_gold_cost}
            )
            logger.info(f"Subtracted {total_gold_cost} gold from global_inventory.")

            # Log updated gold and ML
            logger.debug("Fetching updated gold and ML from global_inventory.")
            query_updated_inventory = """
                SELECT gold, red_ml, green_ml, blue_ml, dark_ml, total_ml
                FROM global_inventory
                WHERE id = 1;
            """
            updated_inventory = connection.execute(sqlalchemy.text(query_updated_inventory)).mappings().fetchone()
            logger.debug(f"Updated Inventory - Gold: {updated_inventory['gold']}, "
                         f"Red ML: {updated_inventory['red_ml']}, Green ML: {updated_inventory['green_ml']}, "
                         f"Blue ML: {updated_inventory['blue_ml']}, Dark ML: {updated_inventory['dark_ml']}, "
                         f"Total ML: {updated_inventory['total_ml']}")

    except HTTPException as he:
        logger.error(f"HTTPException in post_deliver_barrels: {he.detail}")
        logger.debug(traceback.format_exc())
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in post_deliver_barrels: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"Successfully processed delivery for order_id {order_id}.")
    logger.debug(f"Delivery processed: {len(barrels_delivered)} barrels delivered, {total_gold_cost} gold deducted.")
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
