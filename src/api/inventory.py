import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
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
    status: str
    total_cost: int

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
            logger.debug(f"Executing SQL Query: {query.strip()}")

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
            potion_capacity_limit = potion_capacity_units * ut.POTION_CAPACITY_PER_UNIT
            ml_capacity_limit = ml_capacity_units * ut.ML_CAPACITY_PER_UNIT

            # Calculate usage percentages
            potion_usage = (total_potions / potion_capacity_limit) if potion_capacity_limit > 0 else 0
            ml_usage = (total_ml / ml_capacity_limit) if ml_capacity_limit > 0 else 0

            logger.debug(f"Potion usage: {potion_usage*100:.2f}%, ML usage: {ml_usage*100:.2f}%")

            # Determine if we need to purchase more capacity
            potion_capacity_to_buy = 0
            ml_capacity_to_buy = 0
            threshold = 0.5  # 50%

            if potion_usage >= threshold and gold >= ut.CAPACITY_UNIT_COST:
                # Purchase additional capacity units incrementally
                potion_capacity_to_buy = 1
                logger.info("Potion capacity usage exceeded 50%. Planning to purchase additional potion capacity.")

            if ml_usage >= threshold and gold >= ut.CAPACITY_UNIT_COST:
                ml_capacity_to_buy = 1
                logger.info("ML capacity usage exceeded 50%. Planning to purchase additional ML capacity.")

            # Calculate total cost
            total_capacity_units_to_buy = potion_capacity_to_buy + ml_capacity_to_buy
            total_cost = total_capacity_units_to_buy * ut.CAPACITY_UNIT_COST

            if total_cost > gold:
                # Adjust purchases if not enough gold
                if gold >= ut.CAPACITY_UNIT_COST:
                    if potion_capacity_to_buy and gold >= ut.CAPACITY_UNIT_COST:
                        potion_capacity_to_buy = 1
                        ml_capacity_to_buy = 0
                        total_cost = ut.CAPACITY_UNIT_COST
                    elif ml_capacity_to_buy and gold >= ut.CAPACITY_UNIT_COST:
                        ml_capacity_to_buy = 1
                        potion_capacity_to_buy = 0
                        total_cost = ut.CAPACITY_UNIT_COST
                    else:
                        potion_capacity_to_buy = 0
                        ml_capacity_to_buy = 0
                        total_cost = 0
                else:
                    potion_capacity_to_buy = 0
                    ml_capacity_to_buy = 0
                    total_cost = 0
                logger.warning("Adjusted capacity purchase plan due to insufficient gold.")

    except Exception as e:
        logger.exception(f"Unhandled exception in get_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    logger.debug(f"Total capacity units to buy: {total_capacity_units_to_buy}, Total cost: {total_cost}")
    return {
        "potion_capacity": potion_capacity_to_buy,
        "ml_capacity": ml_capacity_to_buy
    }


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
                SELECT 
                    gold,
                    potion_capacity_units,
                    ml_capacity_units
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

            # Calculate total cost
            total_capacity_units_purchased = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity
            total_cost = total_capacity_units_purchased * ut.CAPACITY_UNIT_COST

            if total_cost > gold:
                logger.error(f"Insufficient gold to purchase capacities. Gold available: {gold}, Total cost: {total_cost}")
                raise HTTPException(status_code=400, detail="Insufficient gold to purchase capacities.")

            # Update capacities and gold
            new_potion_capacity_units = potion_capacity_units + capacity_purchase.potion_capacity
            new_ml_capacity_units = ml_capacity_units + capacity_purchase.ml_capacity
            new_gold = gold - total_cost

            update_query = """
                UPDATE global_inventory
                SET
                    potion_capacity_units = :new_potion_capacity_units,
                    ml_capacity_units = :new_ml_capacity_units,
                    gold = :new_gold
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_query),
                {
                    "new_potion_capacity_units": new_potion_capacity_units,
                    "new_ml_capacity_units": new_ml_capacity_units,
                    "new_gold": new_gold
                }
            )
            logger.info(f"Updated capacities and deducted gold. New potion capacity units: {new_potion_capacity_units}, New ml capacity units: {new_ml_capacity_units}, New gold: {new_gold}")
            
    except Exception as e:
        logger.exception(f"Unhandled exception in deliver_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return {"success": True}
    