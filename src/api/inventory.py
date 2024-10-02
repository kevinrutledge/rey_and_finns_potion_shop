import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from src.api import auth
import math

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

# Constants for capacity calculations
POTION_CAPACITY_PER_UNIT = 50  # Each potion capacity unit allows storage of 50 potions
ML_CAPACITY_PER_UNIT = 10000    # Each ML capacity unit allows storage of 10000 ml
CAPACITY_UNIT_COST = 1000       # Cost per capacity unit in gold

# Capacity Manager Class
class CapacityManager:
    def __init__(self):
        # Initialize with 1 capacity unit each
        self.potion_capacity_units = 1
        self.ml_capacity_units = 1
        logger.debug(f"Initialized CapacityManager with potion_capacity_units={self.potion_capacity_units}, ml_capacity_units={self.ml_capacity_units}")

    def get_current_capacity(self):
        capacity = {
            "potion_capacity": self.potion_capacity_units,
            "ml_capacity": self.ml_capacity_units
        }
        logger.debug(f"Current capacity: {capacity}")
        return capacity

    def add_capacity(self, potion_units: int, ml_units: int):
        self.potion_capacity_units += potion_units
        self.ml_capacity_units += ml_units
        logger.info(f"Added capacity - Potion Units: {potion_units}, ML Units: {ml_units}")
        logger.debug(f"Updated capacities: potion_capacity_units={self.potion_capacity_units}, ml_capacity_units={self.ml_capacity_units}")

# Initialize Capacity Manager
capacity_manager = CapacityManager()

# Pydantic Models
class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

    def validate_purchase(cls, values):
        potion_capacity = values.get('potion_capacity')
        ml_capacity = values.get('ml_capacity')

        if potion_capacity < 0:
            raise ValueError("potion_capacity must be non-negative.")
        if ml_capacity < 0:
            raise ValueError("ml_capacity must be non-negative.")
        return values

class CapacityPurchaseResponse(BaseModel):
    status: str
    total_cost: int


@router.get("/audit", summary="Audit Inventory", description="Retrieve current state of global inventory.")
def get_inventory():
    """
    Retrieve current state of global inventory.
    """
    try:
        with db.engine.begin() as connection:
            sql_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_potions = row['num_green_potions']
            ml_in_barrels = row['num_green_ml']
            gold = row['gold']
            logger.debug(f"Fetched inventory: num_potions={num_potions}, ml_in_barrels={ml_in_barrels}, gold={gold}")

        return_inventory = {
            "number_of_potions": num_potions,
            "ml_in_barrels": ml_in_barrels,
            "gold": gold
        }

        logger.info(f"Inventory audit successful: {return_inventory}")

        return return_inventory

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error during get_inventory")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error during get_inventory")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


# Gets called once a day
@router.post("/plan", summary="Get Capacity Plan", description="Generates capacity purchase plan based on current inventory.")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    try:
        with db.engine.begin() as connection:
            # Fetch current inventory
            sql_select = "SELECT num_green_potions, num_green_ml FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_potions = row['num_green_potions']
            ml_in_barrels = row['num_green_ml']
            logger.debug(f"Fetched inventory for plan: num_potions={num_potions}, ml_in_barrels={ml_in_barrels}")

        # Calculate current capacities
        current_potion_capacity = capacity_manager.potion_capacity_units * POTION_CAPACITY_PER_UNIT
        current_ml_capacity = capacity_manager.ml_capacity_units * ML_CAPACITY_PER_UNIT
        logger.debug(f"Current capacities: potion_capacity={current_potion_capacity}, ml_capacity={current_ml_capacity}")

        # Determine needed capacities
        needed_potion_capacity_units = math.ceil(max(0, num_potions - current_potion_capacity) / POTION_CAPACITY_PER_UNIT)
        needed_ml_capacity_units = math.ceil(max(0, ml_in_barrels - current_ml_capacity) / ML_CAPACITY_PER_UNIT)

        purchase_plan = {
            "potion_capacity": needed_potion_capacity_units,
            "ml_capacity": needed_ml_capacity_units
        }

        logger.info(f"Generated capacity purchase plan: {purchase_plan}")

        return purchase_plan

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error during get_capacity_plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error during get_capacity_plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


# Gets called once a day
@router.post("/deliver/{order_id}", summary="Deliver Capacity Purchase", description="Process delivery of capacity purchases.")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    try:
        logger.debug(f"Processing capacity delivery for order_id={order_id} with purchase details: {capacity_purchase}")

        with db.engine.begin() as connection:
            # Fetch current gold
            sql_select = "SELECT gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            gold = row['gold']
            logger.debug(f"Current gold before purchase: {gold}")

            # Calculate total cost
            total_capacity_units = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity
            total_cost = total_capacity_units * CAPACITY_UNIT_COST
            logger.debug(f"Total capacity units to purchase: {total_capacity_units}, Total cost: {total_cost} gold")

            if total_cost > gold:
                logger.error(f"Insufficient gold for capacity purchase. Required: {total_cost}, Available: {gold}")
                raise HTTPException(status_code=400, detail="Not enough gold to purchase additional capacities.")

            # Deduct gold
            sql_update_gold = """
                UPDATE global_inventory
                SET gold = gold - :total_cost
            """
            connection.execute(sqlalchemy.text(sql_update_gold), {'total_cost': total_cost})
            logger.debug(f"Deducted {total_cost} gold from inventory.")

        # Update capacities using CapacityManager
        capacity_manager.add_capacity(capacity_purchase.potion_capacity, capacity_purchase.ml_capacity)

        logger.info(f"Capacity purchase delivered for order_id={order_id}: {capacity_purchase}, Total Cost: {total_cost} gold")

        return CapacityPurchaseResponse(status="OK", total_cost=total_cost)

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception(f"Database error during deliver_capacity_plan for order_id={order_id}")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception(f"Unexpected error during deliver_capacity_plan for order_id={order_id}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    