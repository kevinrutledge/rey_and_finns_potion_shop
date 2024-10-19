import sqlalchemy
import logging
from src import database as db
from src import potion_utilities as pu
from src import potion_config as pc
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
            query_inventory = """
                SELECT gold, total_ml, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_inventory))
            inventory = result.mappings().fetchone()

            if not inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            current_gold = inventory['gold']
            current_total_ml = inventory['total_ml']
            ml_capacity_units = inventory['ml_capacity_units']
            ml_capacity_limit = ml_capacity_units * pc.ML_CAPACITY_PER_UNIT

            # Calculate total gold cost (should match purchase plan)
            total_gold_cost = sum(barrel.price * barrel.quantity for barrel in barrels_delivered)
            logger.debug(f"Total Gold Cost for Delivery: {total_gold_cost}")

            # Check if sufficient gold is available
            if current_gold < total_gold_cost:
                logger.error(f"Insufficient gold. Available: {current_gold}, Required: {total_gold_cost}")
                raise HTTPException(status_code=400, detail="Insufficient gold to complete purchase.")

            # Calculate total ML to add
            total_ml_to_add = sum(barrel.ml_per_barrel * barrel.quantity for barrel in barrels_delivered)
            total_ml_after_adding = current_total_ml + total_ml_to_add

            # Check if ML capacity is sufficient
            if total_ml_after_adding > ml_capacity_limit:
                logger.error(f"Insufficient ML capacity. ML Capacity Limit: {ml_capacity_limit}, Total ML After Adding: {total_ml_after_adding}")
                raise HTTPException(status_code=400, detail="Insufficient ML capacity to store delivered barrels.")

            # Aggregate ML additions per color
            ml_additions = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}

            for barrel in barrels_delivered:
                color_index = barrel.potion_type.index(1)
                color_keys = ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']
                color_key = color_keys[color_index]
                ml_to_add = barrel.ml_per_barrel * barrel.quantity
                ml_additions[color_key] += ml_to_add
                logger.debug(f"Adding {ml_to_add} of {color_key} from barrel SKU {barrel.sku}")

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
                    **ml_additions,
                    "total_ml": total_ml_to_add,
                    "gold_spent": total_gold_cost
                }
            )
            logger.info(f"Updated global_inventory with new MLs and deducted gold.")

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
            query_inventory = """
                SELECT gold, potion_capacity_units, ml_capacity_units, red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query_inventory))
            global_inventory = result.mappings().fetchone()

            if not global_inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            gold = global_inventory['gold']
            ml_capacity_units = global_inventory['ml_capacity_units']
            potion_capacity_units = global_inventory['potion_capacity_units']
            ml_inventory = {
                'red_ml': global_inventory['red_ml'],
                'green_ml': global_inventory['green_ml'],
                'blue_ml': global_inventory['blue_ml'],
                'dark_ml': global_inventory['dark_ml'],
            }

            # Fetch current potion inventory
            query_potions = """
                SELECT sku, current_quantity
                FROM potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            potion_inventory = {row['sku']: row['current_quantity'] for row in potions}

        # Determine future in-game day and hour (4 ticks ahead)
        future_day, future_hour = pu.Utilities.get_future_in_game_time(current_in_game_day, current_in_game_hour, ticks_ahead=4)
        logger.info(f"Future in-game time (4 ticks ahead): {future_day}, Hour: {future_hour}")

        # Determine pricing strategy
        current_strategy = pu.PotionShopLogic.determine_pricing_strategy(
            gold=gold,
            ml_capacity_units=ml_capacity_units,
            potion_capacity_units=potion_capacity_units
        )
        logger.info(f"Determined pricing strategy: {current_strategy}")

        # Get potion priorities
        potion_priorities = pu.PotionShopLogic.get_potion_priorities(
            current_day=future_day,
            current_strategy=current_strategy,
            potion_priorities=pc.POTION_PRIORITIES
        )

        # Fetch potion definitions
        potion_definitions = pc.POTION_DEFINITIONS

        # Calculate desired bottling plan (without ml adjustments)
        desired_bottling_plan = pu.PotionShopLogic.calculate_potion_bottling_plan(
            current_strategy=current_strategy,
            potion_priorities=potion_priorities,
            potion_inventory=potion_inventory,
            potion_capacity_units=potion_capacity_units,
            ml_inventory=ml_inventory,
            ml_capacity_units=ml_capacity_units,
            gold=gold,
            adjust_for_ml_inventory=False  # Get desired quantities
        )

        # Calculate adjusted bottling plan (with ml adjustments)
        bottling_plan = pu.PotionShopLogic.calculate_potion_bottling_plan(
            current_strategy=current_strategy,
            potion_priorities=potion_priorities,
            potion_inventory=potion_inventory,
            potion_capacity_units=potion_capacity_units,
            ml_inventory=ml_inventory,
            ml_capacity_units=ml_capacity_units,
            gold=gold,
            adjust_for_ml_inventory=True  # Adjust for ml_inventory
        )

        # Calculate ml needed based on desired bottling plan
        ml_needed = pu.PotionShopLogic.calculate_ml_needed_for_bottling_plan(
            bottling_plan=desired_bottling_plan,
            potion_definitions=potion_definitions
        )

        logger.debug(f"Desired bottling plan: {desired_bottling_plan}")
        logger.info(f"ML needed for desired bottling plan: {ml_needed}")

        # Decide barrels to purchase
        purchase_plan = pu.PotionShopLogic.decide_barrels_to_purchase(
            current_strategy=current_strategy,
            potion_priorities=potion_priorities,
            ml_inventory=ml_inventory,
            ml_capacity_units=ml_capacity_units,
            gold=gold,
            future_potion_needs=desired_bottling_plan,  # Use desired plan
            wholesale_catalog=[barrel.dict() for barrel in wholesale_catalog]
        )

        logger.info(f"Generated purchase plan: {purchase_plan}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_wholesale_purchase_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_wholesale_purchase_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_wholesale_purchase_plan endpoint.")
    return purchase_plan
