import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
from src import game_constants as gc
from src.api import auth
from sqlalchemy import bindparam, JSON
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
            ml_capacity_limit = ml_capacity_units * gc.ML_CAPACITY_PER_UNIT

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
                raise HTTPException(status_code=400, detail="Insufficient ML capacity to store delivered barrels.")

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
            # Get current in-game day and hour
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM in_game_time
                ORDER BY created_at DESC
                LIMIT 1;
            """
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise ValueError("No in-game time found in database.")
            
            logger.info(f"In-game time: {current_in_game_day}, {current_in_game_hour}")

            # Convert wholesale_catalog to list of dicts
            wholesale_catalog_json = [barrel.dict() for barrel in wholesale_catalog]

            # Prepare and execute insert into barrel_visits
            insert_barrel_visit_query = sqlalchemy.text("""
                INSERT INTO barrel_visits (wholesale_catalog, in_game_day, in_game_hour, visit_time)
                VALUES (:wholesale_catalog, :in_game_day, :in_game_hour, NOW())
                RETURNING barrel_visit_id;
            """).bindparams(bindparam('wholesale_catalog', type_=JSON))

            result = connection.execute(
                insert_barrel_visit_query,
                {
                    "wholesale_catalog": wholesale_catalog_json,
                    "in_game_day": current_in_game_day,
                    "in_game_hour": current_in_game_hour
                }
            )
            barrel_visit_id = result.scalar()
            logger.info(f"Inserted barrel_visit_id: {barrel_visit_id}")

            # Prepare insert into barrels
            insert_barrel_query = sqlalchemy.text("""
                INSERT INTO barrels (barrel_visit_id, sku, ml_per_barrel, potion_type, price, quantity, in_game_day, in_game_hour)
                VALUES (:barrel_visit_id, :sku, :ml_per_barrel, :potion_type, :price, :quantity, :in_game_day, :in_game_hour)
            """).bindparams(bindparam('potion_type', type_=JSON))

            # Insert each barrel into barrels table
            for barrel in wholesale_catalog:
                connection.execute(
                    insert_barrel_query,
                    {
                        "barrel_visit_id": barrel_visit_id,
                        "sku": barrel.sku,
                        "ml_per_barrel": barrel.ml_per_barrel,
                        "potion_type": barrel.potion_type,
                        "price": barrel.price,
                        "quantity": barrel.quantity,
                        "in_game_day": current_in_game_day,
                        "in_game_hour": current_in_game_hour
                    }
                )
                logger.debug(f"Inserted barrel with SKU: {barrel.sku}")

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
            ml_capacity_limit = ml_capacity_units * gc.ML_CAPACITY_PER_UNIT

            logger.debug(f"Global Inventory: {global_inventory}")

            # Fetch current potions
            query_potions = """
                SELECT name, current_quantity
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            current_potions = {row['name']: row['current_quantity'] for row in potions}
            total_potions = sum(current_potions.values())

        # Determine future in-game day and hour (4 ticks ahead)
        future_day, future_hour = ut.Utils.get_future_in_game_time(current_in_game_day, current_in_game_hour, ticks_ahead=4)
        logger.info(f"Future in-game time (4 ticks ahead): {future_day}, Hour: {future_hour}")

        # Select pricing strategy based on potion capacity units
        pricing_strategy = ut.Utils.select_pricing_strategy(potion_capacity_units)
        logger.info(f"Selected pricing strategy: {pricing_strategy}")

        # Get potion priorities for future day and strategy
        potion_priorities = gc.POTION_PRIORITIES[future_day][pricing_strategy]
        logger.debug(f"Potion priorities for {future_day} and strategy {pricing_strategy}: {potion_priorities}")

        # Calculate desired potion quantities
        desired_potions = ut.Utils.calculate_desired_potion_quantities(
            potion_capacity_units=potion_capacity_units,
            current_potions=current_potions,
            potion_priorities=potion_priorities,
            pricing_strategy=pricing_strategy
        )

        # Get potion recipes from DEFAULT_POTIONS
        potion_recipes = {p['name']: p for p in gc.DEFAULT_POTIONS}

        # Calculate ml needed per color to meet desired potion quantities
        ml_needed = ut.Utils.calculate_ml_needed(
            desired_potions=desired_potions,
            current_potions=current_potions,
            potion_recipes=potion_recipes
        )

        # Generate barrel purchase plan
        purchase_plan = ut.Utils.get_barrel_purchase_plan(
            ml_needed=ml_needed,
            current_ml=current_ml,
            ml_capacity_limit=ml_capacity_limit,
            gold=gold,
            ml_capacity_units=ml_capacity_units,
            wholesale_catalog=wholesale_catalog,
            pricing_strategy=pricing_strategy
        )

        # Map purchase plan to match catalog SKUs and quantities
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
