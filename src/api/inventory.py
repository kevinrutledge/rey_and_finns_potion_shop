import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
from src import game_constants as gc
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
import math

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

@router.get("/audit", summary="Audit Inventory", description="Retrieve current state of global inventory.")
def get_inventory():
    """
    Retrieve current state of global inventory.
    """
    logger.info("GET /inventory/audit called.")
    logger.debug("Fetching current inventory status.")

    try:
        with db.engine.begin() as connection:
            # SQL query to fetch total_potions, total_ml, and gold from global_inventory
            query = """
                SELECT total_potions, total_ml, gold
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            row = result.mappings().fetchone()

            if not row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            audit_data = {
                "number_of_potions": row["total_potions"],
                "ml_in_barrels": row["total_ml"],
                "gold": row["gold"]
            }

            logger.debug(f"Audit Data: {audit_data}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_inventory: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("GET /inventory/audit completed successfully.")
    return audit_data


# Gets called once a day
@router.post("/plan", summary="Get Capacity Plan", description="Generates capacity purchase plan based on current inventory.")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger = logging.getLogger("inventory.plan")
    logger.info("POST /inventory/plan called.")
    
    try:
        with db.engine.begin() as connection:
            # Fetch current capacities and usage from global_inventory
            query = """
                SELECT 
                    gold,
                    potion_capacity_units,
                    ml_capacity_units,
                    total_potions,
                    total_ml
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            inventory = result.mappings().fetchone()
            
            if not inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")
            
            gold = inventory['gold']
            potion_capacity_units = inventory['potion_capacity_units']
            ml_capacity_units = inventory['ml_capacity_units']
            total_potions = inventory['total_potions'] or 0
            total_ml = inventory['total_ml'] or 0

            # Calculate capacities
            potion_capacity_limit = potion_capacity_units * gc.POTION_CAPACITY_PER_UNIT
            ml_capacity_limit = ml_capacity_units * gc.ML_CAPACITY_PER_UNIT

            # Calculate usage percentages
            potion_usage = (total_potions / potion_capacity_limit) if potion_capacity_limit > 0 else 0
            ml_usage = (total_ml / ml_capacity_limit) if ml_capacity_limit > 0 else 0

            logger.debug(f"Potion usage: {potion_usage*100:.2f}%, ML usage: {ml_usage*100:.2f}%")

            # Determine capacity unit difference
            capacity_unit_diff = potion_capacity_units - ml_capacity_units

            potion_capacity_to_buy = 0
            ml_capacity_to_buy = 0

            # TODO: Implement purchasing logic per PRICE_STRATEGY
            if gold >= 5000:
                if capacity_unit_diff <= 0:
                    # Potion capacity units less than or equal to ml capacity units
                    potion_capacity_to_buy = 2
                    ml_capacity_to_buy = 2
                    logger.info("Gold > 5000 and capacity units equal or potion less. Purchasing potion capacity.")
            elif gold >= 3000:
                if capacity_unit_diff <= 0:
                    # Potion capacity units less than or equal to ml capacity units
                    potion_capacity_to_buy = 1
                    logger.info("Gold > 3000 and capacity units equal or potion less. Purchasing potion capacity.")
                elif capacity_unit_diff >= 1:
                    # Potion capacity units exceed ml capacity units
                    ml_capacity_to_buy = 1
                    logger.info("Gold > 2000 and potion capacity units exceed ml by 1 or more. Purchasing ml capacity.")
            elif gold >= 2300:
                if potion_usage >= 0.5 or ml_usage >= 0.5:
                    if capacity_unit_diff <= 0:
                        potion_capacity_to_buy = 1
                        logger.info("Gold > 2300, usage >= 50%, capacity units equal or potion less. Purchasing potion capacity.")
                    elif capacity_unit_diff >= 1:
                        ml_capacity_to_buy = 1
                        logger.info("Gold > 2300, usage >= 50%, potion capacity units exceed ml. Purchasing ml capacity.")
            elif gold >= 2000:
                if potion_usage >= 0.5 and ml_usage >= 0.5:
                    if capacity_unit_diff <= 0:
                        potion_capacity_to_buy = 1
                        logger.info("Gold >= 1000, both usage >= 50%, capacity units equal or potion less. Purchasing potion capacity.")
                    elif capacity_unit_diff >=1:
                        ml_capacity_to_buy = 1
                        logger.info("Gold >= 1000, both usage >= 50%, potion capacity units exceed ml. Purchasing ml capacity.")

            # Calculate total cost
            total_capacity_units_to_buy = potion_capacity_to_buy + ml_capacity_to_buy
            total_cost = total_capacity_units_to_buy * gc.CAPACITY_UNIT_COST

            # Adjust purchases if not enough gold
            if total_cost > gold:
                logger.warning("Not enough gold to purchase both capacities. Adjusting purchase plan.")
                if gold >= gc.CAPACITY_UNIT_COST:
                    # Can only afford one unit
                    if ml_capacity_to_buy == 1 and capacity_unit_diff >= 1:
                        # Prioritize ml capacity
                        potion_capacity_to_buy = 0
                        total_cost = gc.CAPACITY_UNIT_COST
                        logger.info("Prioritizing ml capacity due to gold constraints and capacity unit difference.")
                    else:
                        # Prioritize potion capacity
                        ml_capacity_to_buy = 0
                        total_cost = gc.CAPACITY_UNIT_COST
                        logger.info("Prioritizing potion capacity due to gold constraints.")
                else:
                    # Cannot afford any capacity units
                    potion_capacity_to_buy = 0
                    ml_capacity_to_buy = 0
                    total_cost = 0
                    logger.warning("Insufficient gold to purchase any capacity units.")

            logger.debug(f"Final capacity units to buy: Potion={potion_capacity_to_buy}, ML={ml_capacity_to_buy}, Total cost: {total_cost}")
            return {
                "potion_capacity": potion_capacity_to_buy,
                "ml_capacity": ml_capacity_to_buy
            }

    except Exception as e:
        logger.exception(f"Unhandled exception in get_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Gets called once a day
@router.post("/deliver/{order_id}", summary="Deliver Capacity Purchase", description="Process delivery of capacity purchases.")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger = logging.getLogger("inventory.deliver")
    logger.info("POST /inventory/deliver called.")
    logger.debug(f"CapacityPurchase data: {capacity_purchase}")
    
    try:
        with db.engine.begin() as connection:
            # Fetch current gold and capacities
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            inventory = result.mappings().fetchone()
            
            if not inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            current_gold = inventory['gold']
            current_potion_capacity_units = inventory['potion_capacity_units']
            current_ml_capacity_units = inventory['ml_capacity_units']

            logger.debug(f"Current gold: {current_gold}")

            # Calculate total cost
            total_capacity_units_purchased = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity
            total_cost = total_capacity_units_purchased * gc.CAPACITY_UNIT_COST

            logger.debug(f"Total capacity units purchased: {total_capacity_units_purchased}, Total cost: {total_cost}")

            # Check if sufficient gold is available
            if current_gold < total_cost:
                logger.error(f"Insufficient gold. Available: {current_gold}, Required: {total_cost}")
                raise HTTPException(status_code=400, detail="Insufficient gold to complete capacity purchase.")

            # Update capacities and deduct gold
            update_inventory_query = """
                UPDATE global_inventory
                SET potion_capacity_units = potion_capacity_units + :potion_capacity,
                    ml_capacity_units = ml_capacity_units + :ml_capacity,
                    gold = gold - :total_cost
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_inventory_query),
                {
                    "potion_capacity": capacity_purchase.potion_capacity,
                    "ml_capacity": capacity_purchase.ml_capacity,
                    "total_cost": total_cost
                }
            )
            logger.info(f"Updated capacities and deducted gold. New potion capacity units: {current_potion_capacity_units + capacity_purchase.potion_capacity}, New ml capacity units: {current_ml_capacity_units + capacity_purchase.ml_capacity}, New gold: {current_gold - total_cost}")
            
    except HTTPException as he:
        logger.error(f"HTTPException in deliver_capacity_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in deliver_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"success": True}