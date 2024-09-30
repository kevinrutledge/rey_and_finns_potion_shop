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

    def get_current_capacity(self):
        return {
            "potion_capacity": self.potion_capacity_units,
            "ml_capacity": self.ml_capacity_units
        }

    def add_capacity(self, potion_units: int, ml_units: int):
        self.potion_capacity_units += potion_units
        self.ml_capacity_units += ml_units
        logger.debug(f"Potion Units: {self.potion_capacity_units}")
        logger.debug(f"Volume Units: {self.ml_capacity_units}")

# Initialize Capacity Manager
capacity_manager = CapacityManager()

# Pydantic Models
class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

    @validator('potion_capacity', 'ml_capacity')
    def capacity_must_be_non_negative(cls, capacity_value, field):
        if capacity_value < 0:
            raise ValueError(f"{field.name} must be non-negative")
        return capacity_value

class CapacityPurchaseResponse(BaseModel):
    status: str
    total_cost: int


@router.get("/audit", summary="Audit Inventory", description="Retrieve current state of global inventory.")
def get_inventory():
    """
    Retrieve current state of global inventory.
    """
    logger.debug("inventory/audit - in")

    try:
        with db.engine.begin() as connection:
            sql_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_potions = row['num_green_potions']
            ml_in_barrels = row['num_green_ml']
            gold = row['gold']

        return_inventory = {
            "number_of_potions": num_potions,
            "ml_in_barrels": ml_in_barrels,
            "gold": gold
        }

        logger.debug("inventory/audit - out")
        logger.debug(f"Inventory: {return_inventory}")

        return return_inventory

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error during inventory/audit")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error during inventory/audit")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

# Gets called once a day
@router.post("/plan", summary="Get Capacity Plan", description="Generates capacity purchase plan based on current inventory.")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger.debug("inventory/plan - in")

    try:
        with db.engine.begin() as connection:
            # Fetch current inventory
            sql_select = "SELECT num_green_potions, num_green_ml FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_potions = row['num_green_potions']
            ml_in_barrels = row['num_green_ml']

        # Calculate current capacities
        current_potion_capacity = capacity_manager.potion_capacity_units * POTION_CAPACITY_PER_UNIT
        current_ml_capacity = capacity_manager.ml_capacity_units * ML_CAPACITY_PER_UNIT

        logger.debug(f"Current Potion Capacity: {current_potion_capacity} (Units: {capacity_manager.potion_capacity_units})")
        logger.debug(f"Current ML Capacity: {current_ml_capacity} (Units: {capacity_manager.ml_capacity_units})")

        # Determine needed capacities
        needed_potion_capacity_units = math.ceil(max(0, num_potions - current_potion_capacity) / POTION_CAPACITY_PER_UNIT)
        needed_ml_capacity_units = math.ceil(max(0, ml_in_barrels - current_ml_capacity) / ML_CAPACITY_PER_UNIT)

        purchase_plan = {
            "potion_capacity": needed_potion_capacity_units,
            "ml_capacity": needed_ml_capacity_units
        }

        logger.debug(f"Capacity Purchase Plan: {purchase_plan}")
        logger.debug("inventory/plan - out")

        return purchase_plan

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error during inventory/plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error during inventory/plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

# Gets called once a day
@router.post("/deliver/{order_id}", summary="Deliver Capacity Purchase", description="Process delivery of capacity purchases.")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger.debug("inventory/deliver/{order_id} - Deliver Capacity Plan - in")
    logger.debug(f"Capacity Purchase: {capacity_purchase}")
    logger.debug(f"Order Id: {order_id}")

    try:
        with db.engine.begin() as connection:
            # Fetch current gold
            sql_select = "SELECT gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            gold = row['gold']

            # Calculate total cost
            total_capacity_units = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity
            total_cost = total_capacity_units * CAPACITY_UNIT_COST

            logger.debug(f"Total Capacity Units: {total_capacity_units}")
            logger.debug(f"Total Cost: {total_cost} gold")

            if total_cost > gold:
                logger.error("Not enough gold to purchase additional capacities.")
                raise HTTPException(status_code=400, detail="Not enough gold to purchase additional capacities.")

            # Deduct gold
            sql_update_gold = sqlalchemy.text("""
                UPDATE global_inventory
                SET gold = gold - :total_cost
            """)
            connection.execute(sql_update_gold, {'total_cost': total_cost})
            logger.debug(f"Updated Gold: Subtracted {total_cost} gold from inventory.")

        # Update capacities using CapacityManager
        capacity_manager.add_capacity(capacity_purchase.potion_capacity, capacity_purchase.ml_capacity)

        logger.debug(f"inventory/deliver/{order_id} - Deliver Capacity Plan - out")
        logger.debug(f"Additional Potions: {capacity_purchase.potion_capacity}")
        logger.debug(f"Additional ML: {capacity_purchase.ml_capacity}")
        logger.debug(f"Total Cost: {total_cost} gold")

        return CapacityPurchaseResponse(status="OK", total_cost=total_cost)

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception(f"Database error during inventory/deliver/{order_id}")
        raise HTTPException(status_code=500, detail="Database error.")
    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise he
    except Exception:
        logger.exception(f"Unexpected error during inventory/deliver/{order_id}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
    