import sqlalchemy
import logging
from src import database as db
from src import potion_utilities as pu
from src import potion_config as pc
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth

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

    try:
        with db.engine.begin() as connection:
            # Fetch total_potions, total_ml, and gold from global_inventory
            query = """
                SELECT total_potions, total_ml, gold
                FROM temp_global_inventory
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

        logger.info("GET /inventory/audit completed successfully.")
        return audit_data

    except HTTPException as he:
        logger.error(f"HTTPException in get_inventory: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Gets called once a day
@router.post("/plan", summary="Get Capacity Plan", description="Generates capacity purchase plan based on current inventory.")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
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
                    red_ml,
                    green_ml,
                    blue_ml,
                    dark_ml
                FROM temp_global_inventory
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

            ml_inventory = {
                'red_ml': inventory['red_ml'] or 0,
                'green_ml': inventory['green_ml'] or 0,
                'blue_ml': inventory['blue_ml'] or 0,
                'dark_ml': inventory['dark_ml'] or 0,
            }

            # Fetch current potion inventory
            query_potions = """
                SELECT sku, current_quantity
                FROM temp_potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            potion_inventory = {row['sku']: row['current_quantity'] for row in potions}

        # Determine pricing strategy
        current_strategy = pu.PotionShopLogic.determine_pricing_strategy(
            gold=gold,
            ml_capacity_units=ml_capacity_units,
            potion_capacity_units=potion_capacity_units
        )
        logger.info(f"Determined pricing strategy: {current_strategy}")

        # Decide on capacity upgrades
        capacity_to_purchase = pu.PotionShopLogic.should_purchase_capacity_upgrade(
            current_strategy=current_strategy,
            gold=gold,
            potion_inventory=potion_inventory,
            ml_inventory=ml_inventory,
            ml_capacity_units=ml_capacity_units,
            potion_capacity_units=potion_capacity_units
        )

        logger.info(f"Capacity purchase plan: {capacity_to_purchase}")
        return capacity_to_purchase

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
    logger.info("POST /inventory/deliver called.")
    logger.debug(f"CapacityPurchase data: {capacity_purchase}")
    
    try:
        with db.engine.begin() as connection:
            # Fetch current gold and capacities
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units
                FROM temp_global_inventory
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

            # Calculate total cost
            total_capacity_units_purchased = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity
            total_cost = total_capacity_units_purchased * pc.CAPACITY_UNIT_COST

            logger.debug(f"Total capacity units purchased: {total_capacity_units_purchased}, Total cost: {total_cost}")

            # Check if sufficient gold is available
            if current_gold < total_cost:
                logger.error(f"Insufficient gold. Available: {current_gold}, Required: {total_cost}")
                raise HTTPException(status_code=400, detail="Insufficient gold to complete capacity purchase.")

            # Update capacities and deduct gold
            update_inventory_query = """
                UPDATE temp_global_inventory
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
                
        return {"success": True}

    except HTTPException as he:
        logger.error(f"HTTPException in deliver_capacity_plan: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in deliver_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")