import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
from src import potions as po
from src.api import auth
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
            # Fetch current inventory and capacities
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units, red_ml, green_ml, blue_ml, dark_ml
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
            gold = global_inventory['gold']
            current_ml = {
                'red_ml': global_inventory['red_ml'],
                'green_ml': global_inventory['green_ml'],
                'blue_ml': global_inventory['blue_ml'],
                'dark_ml': global_inventory['dark_ml'],
            }
            ml_capacity_limit = ml_capacity_units * ut.ML_CAPACITY_PER_UNIT

            logger.debug(f"Global Inventory: {global_inventory}")

            # Fetch current potions
            query_potions = """
                SELECT name, current_quantity
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            current_potions = {row['name']: row['current_quantity'] for row in potions}

        # Determine future in-game time
        future_day, future_hour = ut.Utils.get_future_in_game_time(3)
        logger.info(f"Future in-game time: {future_day}, Hour: {future_hour}")

        # Select pricing strategy
        potion_priorities = po.POTION_PRIORITIES[future_day]['PRICE_STRATEGY_PREMIUM']
        logger.debug(f"Potion priorities: {potion_priorities}")

        # Calculate desired potion quantities
        desired_potions = ut.Utils.calculate_desired_potion_quantities(
            potion_capacity_units,
            current_potions,
            potion_priorities
        )

        # Calculate ml needed per color
        ml_needed = ut.Utils.calculate_ml_needed(desired_potions, current_potions)

        # Determine barrels to purchase
        purchase_plan = ut.Utils.get_barrel_purchase_plan(
            ml_needed, current_ml, ml_capacity_limit, gold, ml_capacity_units
        )

        # Map purchase plan to match the catalog SKUs and quantities
        catalog_skus = {item.sku: item for item in wholesale_catalog}
        final_purchase_plan = []
        for purchase in purchase_plan:
            sku = purchase['sku']
            quantity = purchase['quantity']
            if sku in catalog_skus:
                available_quantity = catalog_skus[sku].quantity
                purchase_quantity = min(quantity, available_quantity)
                if purchase_quantity > 0:
                    final_purchase_plan.append({'sku': sku, 'quantity': purchase_quantity})
                    logger.debug(f"Adding {purchase_quantity} of {sku} to final purchase plan.")
            else:
                logger.debug(f"SKU {sku} not found in catalog.")

        logger.info(f"Generated purchase plan: {final_purchase_plan}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_wholesale_purchase_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_wholesale_purchase_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_wholesale_purchase_plan endpoint.")
    logger.debug(f"Returning purchase_plan: {final_purchase_plan}")
    return final_purchase_plan
