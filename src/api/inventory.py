import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        sql_statement_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
        result = connection.execute(sqlalchemy.text(sql_statement_select))
        row = result.mappings().one()
        
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

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    return_capacity_plan = {"potion_capacity": 0, "ml_capacity": 0}

    logger.debug("inventory/plan Get Capacity Plan - out")
    logger.debug(f"Capacity Plan: {return_capacity_plan}")

    return return_capacity_plan

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger.debug("inventory/deliver/order_id - Deliver Capacity Plan - in")
    logger.debug(f"Capacity Purchase: {capacity_purchase}")
    logger.debug(f"Order Id: {order_id}")

    return "OK"
