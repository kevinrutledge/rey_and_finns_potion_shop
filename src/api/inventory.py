import sqlalchemy
import logging
from src import database as db
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

# Constants for capacity calculations
POTION_CAPACITY_PER_UNIT = 50  # Each potion capacity unit allows storage of 50 potions
ML_CAPACITY_PER_UNIT = 10000    # Each ML capacity unit allows storage of 10000 ml
CAPACITY_UNIT_COST = 1000       # Cost per capacity unit in gold


@router.get("/audit", summary="Audit Inventory", description="Retrieve current state of global inventory.")
def get_inventory():
    """
    Retrieve current state of global inventory.
    """
    logger.info("Starting get_inventory endpoint.")

    # Initialize local variables
    number_of_potions = 0
    ml_in_barrels = 0
    gold = 0

    try:
        with db.engine.begin() as connection:
            # Fetch total number of potions from database
            logger.debug("Executing SQL query to fetch total number of potions.")
            query_total_potions = """
                SELECT SUM(current_quantity) AS total_potions FROM potions;
            """
            logger.debug(f"SQL Query: {query_total_potions.strip()}")
            result = connection.execute(sqlalchemy.text(query_total_potions))
            row = result.mappings().fetchone()

            if row and row["total_potions"] is not None:
                number_of_potions = row["total_potions"]
                logger.debug(f"Total number of potions fetched: {number_of_potions}")
            else:
                number_of_potions = 0
                logger.debug("No potions found in database. Setting total_potions to 0.")

            # Fetch total ml in barrels from global_inventory
            logger.debug("Executing SQL query to fetch total ml in barrels.")
            query_total_ml = """
                SELECT 
                    COALESCE(red_ml, 0) + COALESCE(green_ml, 0) + 
                    COALESCE(blue_ml, 0) + COALESCE(dark_ml, 0) AS total_ml
                FROM global_inventory
                WHERE id = 1;
            """
            logger.debug(f"SQL Query: {query_total_ml.strip()}")
            result = connection.execute(sqlalchemy.text(query_total_ml))
            row = result.mappings().fetchone()

            if row and row["total_ml"] is not None:
                ml_in_barrels = row["total_ml"]
                logger.debug(f"Total ml in barrels fetched: {ml_in_barrels}")
            else:
                ml_in_barrels = 0
                logger.debug("No ml data found in global_inventory. Setting total_ml to 0.")

            # Fetch current gold amount from global_inventory
            logger.debug("Executing SQL query to fetch current gold amount.")
            query_gold = """
                SELECT gold FROM global_inventory WHERE id = 1;
            """
            logger.debug(f"SQL Query: {query_gold.strip()}")
            result = connection.execute(sqlalchemy.text(query_gold))
            row = result.mappings().fetchone()

            if row and row["gold"] is not None:
                gold = row["gold"]
                logger.debug(f"Current gold amount fetched: {gold}")
            else:
                gold = 0
                logger.debug("No gold data found in global_inventory. Setting gold to 0.")

        # Log totals calculated
        logger.info(
            f"Inventory totals - Potions: {number_of_potions}, ML in barrels: {ml_in_barrels}, Gold: {gold}"
        )

    except Exception as e:
        logger.exception(f"Error in get_inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_inventory endpoint.")
    logger.debug(
        f"Returning from get_inventory with response: {{'number_of_potions': {number_of_potions}, 'ml_in_barrels': {ml_in_barrels}, 'gold': {gold}}}"
    )
    return {
        "number_of_potions": number_of_potions,
        "ml_in_barrels": ml_in_barrels,
        "gold": gold,
    }


# Gets called once a day
@router.post("/plan", summary="Get Capacity Plan", description="Generates capacity purchase plan based on current inventory.")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger.info("Starting get_capacity_plan endpoint.")

    # Initialize variables with default values
    potion_capacity_units = 1
    ml_capacity_units = 1
    gold = 100
    total_potions = 0
    total_ml = 0

    try:
        with db.engine.begin() as connection:
            # Fetch current capacity units and gold from global_inventory
            logger.debug("Executing SQL query to fetch current capacity units and gold.")
            query_inventory = """
                SELECT potion_capacity_units, ml_capacity_units, gold
                FROM global_inventory
                WHERE id = 1;
            """
            logger.debug(f"SQL Query: {query_inventory.strip()}")
            result = connection.execute(sqlalchemy.text(query_inventory))
            row = result.mappings().fetchone()

            if row:
                potion_capacity_units = row["potion_capacity_units"]
                ml_capacity_units = row["ml_capacity_units"]
                gold = row["gold"]
                logger.debug(
                    f"Fetched capacity units and gold - Potion Capacity Units: {potion_capacity_units}, "
                    f"ML Capacity Units: {ml_capacity_units}, Gold: {gold}"
                )
            else:
                # Initialize if no record exists
                potion_capacity_units = 1
                ml_capacity_units = 1
                gold = 100
                logger.debug(
                    "No global_inventory record found. Initializing with default values."
                )

            # Fetch total number of potions in inventory
            logger.debug("Executing SQL query to fetch total number of potions in inventory.")
            query_total_potions = """
                SELECT SUM(current_quantity) AS total_potions FROM potions;
            """
            logger.debug(f"SQL Query: {query_total_potions.strip()}")
            result = connection.execute(sqlalchemy.text(query_total_potions))
            row = result.mappings().fetchone()

            if row and row["total_potions"] is not None:
                total_potions = row["total_potions"]
                logger.debug(f"Total potions in inventory fetched: {total_potions}")
            else:
                total_potions = 0
                logger.debug("No potions found in inventory. Setting total_potions to 0.")

            # Fetch total ml in barrels from global_inventory
            logger.debug("Executing SQL query to fetch total ml in barrels.")
            query_total_ml = """
                SELECT 
                    COALESCE(red_ml, 0) + COALESCE(green_ml, 0) + 
                    COALESCE(blue_ml, 0) + COALESCE(dark_ml, 0) AS total_ml
                FROM global_inventory
                WHERE id = 1;
            """
            logger.debug(f"SQL Query: {query_total_ml.strip()}")
            result = connection.execute(sqlalchemy.text(query_total_ml))
            row = result.mappings().fetchone()

            if row and row["total_ml"] is not None:
                total_ml = row["total_ml"]
                logger.debug(f"Total ml in barrels fetched: {total_ml}")
            else:
                total_ml = 0
                logger.debug("No ml data found in global_inventory. Setting total_ml to 0.")

            # Calculate current capacity limits
            potion_capacity_limit = potion_capacity_units * POTION_CAPACITY_PER_UNIT
            ml_capacity_limit = ml_capacity_units * ML_CAPACITY_PER_UNIT
            logger.debug(
                f"Calculated capacity limits - Potion Capacity Limit: {potion_capacity_limit}, "
                f"ML Capacity Limit: {ml_capacity_limit}"
            )

            # Initialize capacity units to purchase
            potion_capacity_needed = 0
            ml_capacity_needed = 0

            # Check if potion inventory exceeds 80% of capacity
            if total_potions >= potion_capacity_limit * 0.8:
                logger.debug("Potion inventory exceeds 80% of capacity.")
                units_to_buy = 1  # Assuming buying 1 unit; adjust as needed
                cost = units_to_buy * CAPACITY_UNIT_COST
                logger.debug(f"Calculated cost for additional potion capacity units: {cost}")

                if gold >= cost:
                    potion_capacity_needed = units_to_buy
                    logger.debug(f"Planning to purchase {potion_capacity_needed} potion capacity unit(s).")
                else:
                    logger.info("Not enough gold to purchase additional potion capacity.")

            else:
                logger.debug("Potion inventory does not exceed 80% of capacity. No purchase needed.")

            # Check if ml inventory exceeds 80% of capacity
            if total_ml >= ml_capacity_limit * 0.8:
                logger.debug("ML inventory exceeds 80% of capacity.")
                units_to_buy = 1  # Assuming buying 1 unit; adjust as needed
                cost = units_to_buy * CAPACITY_UNIT_COST
                logger.debug(f"Calculated cost for additional ml capacity units: {cost}")

                if gold >= cost:
                    ml_capacity_needed = units_to_buy
                    logger.debug(f"Planning to purchase {ml_capacity_needed} ml capacity unit(s).")
                else:
                    logger.info("Not enough gold to purchase additional ml capacity.")

            else:
                logger.debug("ML inventory does not exceed 80% of capacity. No purchase needed.")

            # Log decisions made
            logger.info(f"Potion Capacity Units: {potion_capacity_units}, Total Potions: {total_potions}")
            logger.info(f"ML Capacity Units: {ml_capacity_units}, Total ML: {total_ml}")
            logger.info(f"Planning to purchase Potion Capacity Units: {potion_capacity_needed}")
            logger.info(f"Planning to purchase ML Capacity Units: {ml_capacity_needed}")

    except Exception as e:
        logger.exception(f"Error in get_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_capacity_plan endpoint.")
    logger.debug(
        f"Returning from get_capacity_plan with response: {{'potion_capacity': {potion_capacity_needed}, 'ml_capacity': {ml_capacity_needed}}}"
    )
    return {
        "potion_capacity": potion_capacity_needed,
        "ml_capacity": ml_capacity_needed,
    }


class CapacityPurchase(BaseModel):
    status: str
    total_cost: int


# Gets called once a day
@router.post("/deliver/{order_id}", summary="Deliver Capacity Purchase", description="Process delivery of capacity purchases.")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    logger.info(f"Starting deliver_capacity_plan endpoint for order_id {order_id}.")
    logger.debug(f"Received capacity_purchase data: {capacity_purchase.dict()}")

    # Extract capacities to add from request
    potion_capacity_to_add = capacity_purchase.potion_capacity
    ml_capacity_to_add = capacity_purchase.ml_capacity

    # Calculate total units to add and total cost
    total_units_to_add = potion_capacity_to_add + ml_capacity_to_add
    total_cost = total_units_to_add * CAPACITY_UNIT_COST

    logger.info(f"Capacity units to add - Potion: {potion_capacity_to_add}, ML: {ml_capacity_to_add}")
    logger.info(f"Total cost for capacity units: {total_cost}")

    try:
        with db.engine.begin() as connection:
            # Fetch current gold and capacity units from global_inventory
            logger.debug("Executing SQL query to fetch current gold and capacity units from global_inventory.")
            query_inventory = """
                SELECT gold, potion_capacity_units, ml_capacity_units
                FROM global_inventory
                WHERE id = 1;
            """
            logger.debug(f"SQL Query: {query_inventory.strip()}")
            result = connection.execute(sqlalchemy.text(query_inventory))
            row = result.mappings().fetchone()

            if row:
                gold = row["gold"]
                potion_capacity_units = row["potion_capacity_units"]
                ml_capacity_units = row["ml_capacity_units"]
                logger.debug(
                    f"Fetched inventory - Gold: {gold}, Potion Capacity Units: {potion_capacity_units}, ML Capacity Units: {ml_capacity_units}"
                )
            else:
                # Initialize if no record exists
                gold = 100
                potion_capacity_units = 1
                ml_capacity_units = 1
                logger.debug(
                    "No global_inventory record found. Initializing with default values."
                )

            # Check if there is enough gold to cover total cost
            logger.debug(f"Checking if gold ({gold}) is sufficient to cover total cost ({total_cost}).")
            if gold >= total_cost:
                logger.debug("Sufficient gold to cover total cost.")

                # Calculate new capacity units
                new_potion_capacity_units = potion_capacity_units + potion_capacity_to_add
                new_ml_capacity_units = ml_capacity_units + ml_capacity_to_add
                new_gold = gold - total_cost

                logger.debug(
                    f"Updating capacities - New Potion Capacity Units: {new_potion_capacity_units}, "
                    f"New ML Capacity Units: {new_ml_capacity_units}, New Gold: {new_gold}"
                )

                # Update global_inventory with new capacities and gold
                logger.debug("Executing SQL query to update global_inventory with new capacities and gold.")
                update_query = """
                    UPDATE global_inventory
                    SET potion_capacity_units = :new_potion_capacity_units,
                        ml_capacity_units = :new_ml_capacity_units,
                        gold = :new_gold
                    WHERE id = 1;
                """
                logger.debug(f"SQL Query: {update_query.strip()}")
                connection.execute(
                    sqlalchemy.text(update_query),
                    {
                        "new_potion_capacity_units": new_potion_capacity_units,
                        "new_ml_capacity_units": new_ml_capacity_units,
                        "new_gold": new_gold,
                    },
                )

                logger.info(
                    f"Updated capacities - Potion Capacity Units: {new_potion_capacity_units}, "
                    f"ML Capacity Units: {new_ml_capacity_units}, Gold after purchase: {new_gold}"
                )
            else:
                logger.error("Insufficient gold to purchase requested capacity units.")
                raise HTTPException(
                    status_code=400,
                    detail="Not enough gold to purchase capacity units."
                )

    except HTTPException as e:
        # Re-raise HTTPExceptions after logging
        logger.error(f"HTTPException in deliver_capacity_plan: {e.detail}")
        raise e
    except Exception as e:
        # Log unexpected exceptions with traceback
        logger.exception(f"Error in deliver_capacity_plan: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending deliver_capacity_plan endpoint.")
    logger.debug("Returning response: {'status': 'OK'}")
    return {"status": "OK"}
    