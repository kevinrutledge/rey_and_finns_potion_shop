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
    logger.info("POST /inventory/plan called.")
    logger.debug("Generating capacity purchase plan.")

    try:
        with db.engine.begin() as connection:
            # Fetch current inventory and gold
            query = """
                SELECT total_potions, total_ml, gold, potion_capacity_units, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            logger.debug(f"Executing SQL Query: {query.strip()}")
            result = connection.execute(sqlalchemy.text(query))
            row = result.mappings().fetchone()

            if not row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            total_potions = row["total_potions"]
            total_ml = row["total_ml"]
            gold = row["gold"]
            current_potion_capacity_units = row["potion_capacity_units"]
            current_ml_capacity_units = row["ml_capacity_units"]

            logger.debug(f"Current Inventory - Potions: {total_potions}, ML: {total_ml}, Gold: {gold}, Potion Capacity Units: {current_potion_capacity_units}, ML Capacity Units: {current_ml_capacity_units}")

            # Define thresholds (these can be adjusted as per requirements)
            potion_threshold = current_potion_capacity_units * 50  # Each unit allows 50 potions
            ml_threshold = current_ml_capacity_units * 10000       # Each unit allows 10000 ml

            logger.debug(f"Potion Threshold: {potion_threshold}, ML Threshold: {ml_threshold}")

            # Determine if capacity needs to be increased
            need_potion_capacity = total_potions >= potion_threshold
            need_ml_capacity = total_ml >= ml_threshold

            logger.debug(f"Need Potion Capacity: {need_potion_capacity}, Need ML Capacity: {need_ml_capacity}")

            potion_units_to_purchase = 0
            ml_units_to_purchase = 0
            total_cost = 0

            unit_cost = 1000  # Cost per capacity unit

            if need_potion_capacity:
                potion_units_to_purchase = 1  # Purchase 1 additional unit
                total_cost += unit_cost
                logger.debug(f"Potion capacity needs increase. Units to purchase: {potion_units_to_purchase}, Cost: {unit_cost}")

            if need_ml_capacity:
                ml_units_to_purchase = 1  # Purchase 1 additional unit
                total_cost += unit_cost
                logger.debug(f"ML capacity needs increase. Units to purchase: {ml_units_to_purchase}, Cost: {unit_cost}")

            if total_cost == 0:
                logger.info("No capacity purchase needed today.")
                capacity_plan = CapacityPurchase(
                    status="No purchase needed",
                    total_cost=0
                )
                return capacity_plan

            # Check if enough gold is available
            if gold < total_cost:
                logger.warning("Insufficient gold to purchase required capacity units.")
                capacity_plan = CapacityPurchase(
                    status="Insufficient gold",
                    total_cost=total_cost
                )
                return capacity_plan

            # If both capacities need to be increased and have enough gold
            logger.info(f"Capacity purchase plan generated: Potion Units - {potion_units_to_purchase}, ML Units - {ml_units_to_purchase}, Total Cost - {total_cost}")

            capacity_plan = CapacityPurchase(
                status="Purchase recommended",
                total_cost=total_cost
            )

    except HTTPException as he:
        logger.error(f"HTTPException in get_capacity_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("POST /inventory/plan completed successfully.")
    logger.debug(f"Capacity Plan Response: {capacity_plan}")
    return capacity_plan


# Gets called once a day
@router.post("/deliver/{order_id}", summary="Deliver Capacity Purchase", description="Process delivery of capacity purchases.")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger.info(f"POST /inventory/deliver/{order_id} called.")
    logger.debug(f"Capacity Purchase Data: {capacity_purchase}")

    try:
        # Handle different statuses
        if capacity_purchase.status != "Purchase recommended":
            logger.error(f"Invalid status for capacity purchase: {capacity_purchase.status}")
            raise HTTPException(status_code=400, detail="Invalid status for capacity purchase.")

        if capacity_purchase.total_cost <= 0:
            logger.error("Total cost must be greater than zero for capacity purchase.")
            raise HTTPException(status_code=400, detail="Total cost must be greater than zero for capacity purchase.")

        with db.engine.begin() as connection:
            # Fetch current inventory and gold
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            logger.debug(f"Executing SQL Query: {query.strip()}")
            result = connection.execute(sqlalchemy.text(query))
            row = result.mappings().fetchone()

            if not row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            current_gold = row["gold"]
            current_potion_capacity_units = row["potion_capacity_units"]
            current_ml_capacity_units = row["ml_capacity_units"]

            logger.debug(f"Current Gold: {current_gold}, Potion Capacity Units: {current_potion_capacity_units}, ML Capacity Units: {current_ml_capacity_units}")

            # Check if enough gold is available
            if current_gold < capacity_purchase.total_cost:
                logger.error("Insufficient gold to complete capacity purchase.")
                raise HTTPException(status_code=400, detail="Insufficient gold to complete capacity purchase.")

            # Calculate how many units to purchase based on plan
            # Since plan was "Purchase recommended" with total_cost
            # Each unit costs 1000 gold
            unit_cost = 1000
            total_units = capacity_purchase.total_cost // unit_cost

            if total_units <= 0:
                logger.error("Total units to purchase must be at least 1.")
                raise HTTPException(status_code=400, detail="Total units to purchase must be at least 1.")

            # Determine how many units are for potion_capacity and ml_capacity
            # Assuming equal distribution as in plan
            potion_units = total_units // 2
            ml_units = total_units - potion_units  # Assign extra unit to ml_capacity if odd

            logger.debug(f"Units to Purchase - Potion Capacity: {potion_units}, ML Capacity: {ml_units}, Total Cost: {capacity_purchase.total_cost}")

            # Update global_inventory with new capacity units and deduct gold
            update_query = """
                UPDATE global_inventory
                SET 
                    potion_capacity_units = potion_capacity_units + :potion_units,
                    ml_capacity_units = ml_capacity_units + :ml_units,
                    gold = gold - :total_cost
                WHERE id = 1;
            """
            logger.debug(f"Executing SQL Query: {update_query.strip()}")
            connection.execute(
                sqlalchemy.text(update_query),
                {
                    "potion_units": potion_units,
                    "ml_units": ml_units,
                    "total_cost": capacity_purchase.total_cost
                }
            )
            logger.info(f"Updated inventory: +{potion_units} potion_capacity_units, +{ml_units} ml_capacity_units, -{capacity_purchase.total_cost} gold.")

            # Record purchase in ledger_entries table
            insert_ledger_query = """
                INSERT INTO ledger_entries (order_id, action, details, amount, timestamp)
                VALUES (:order_id, :action, :details, :amount, :timestamp);
            """
            details = f"Purchased {potion_units} potion_capacity_units and {ml_units} ml_capacity_units."
            logger.debug(f"Recording purchase in ledger: {details}")
            connection.execute(
                sqlalchemy.text(insert_ledger_query),
                {
                    "order_id": order_id,
                    "action": "Capacity Purchase",
                    "details": details,
                    "amount": capacity_purchase.total_cost,
                    "timestamp": ut.get_current_real_time()
                }
            )
            logger.info(f"Recorded purchase in ledger for order_id={order_id}.")

    except HTTPException as he:
        logger.error(f"HTTPException in deliver_capacity_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in deliver_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"POST /inventory/deliver/{order_id} completed successfully.")
    return "OK"
    