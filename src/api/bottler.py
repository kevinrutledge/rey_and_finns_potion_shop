import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from enum import Enum
from pydantic import BaseModel, validator
from src.api import auth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

POTION_TYPE_MAP = {
    tuple([100, 0, 0, 0]): 'red',    # Red Potion
    tuple([0, 100, 0, 0]): 'green',  # Green Potion
    tuple([0, 0, 100, 0]): 'blue',   # Blue Potion
    tuple([0, 0, 0, 100]): 'dark',   # Dark Potion
}

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

    @root_validator
    def check_potion_type_and_quantity(cls, values):
        potion_type = values.get('potion_type')
        quantity = values.get('quantity')

        if len(potion_type) != 4:
            raise ValueError('potion_type must have exactly four elements.')
        if sum(potion_type) != 100:
            raise ValueError('potion_type must sum to 100.')
        if quantity < 1:
            raise ValueError('Quantity must be at least 1.')
        
        return values

# Constants for potion processing   
ML_PER_POTION = 100


@router.post("/deliver/{order_id}", summary="Deliver Bottles", description="Process delivery of bottles.")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """
    Process delivery of bottles to global_inventory.
    """
    logger.debug(f"Initiating bottle delivery for order_id: {order_id} with potions: {potions_delivered}")

    try:
        with db.engine.begin() as connection:
            # Fetch current inventory once
            sql_select = "SELECT id, num_green_potions, num_green_ml, gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            inventory = result.mappings().one_or_none()

            if inventory is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            logger.debug(f"Current Inventory: {inventory}")

            # Initialize totals for each potion category
            total_potions_added = {category: 0 for category in POTION_TYPE_MAP.values()}
            total_ml_used = {category: 0 for category in POTION_TYPE_MAP.values()}

            # Process each delivered potion
            for potion in potions_delivered:
                potion_key = tuple(potion.potion_type)
                potion_category = POTION_TYPE_MAP.get(potion_key)

                if potion_category is None:
                    logger.error(f"Unknown potion type: {potion.potion_type}")
                    raise HTTPException(status_code=400, detail=f"Unknown potion type: {potion.potion_type}")

                num_potions = potion.quantity
                ml_used = num_potions * ML_PER_POTION

                total_potions_added[potion_category] += num_potions
                total_ml_used[potion_category] += ml_used

                logger.debug(f"Processing {num_potions} {potion_category} potions, using {ml_used} ml.")

            # Check if there is enough ml in inventory for each potion category
            for category, ml_used in total_ml_used.items():
                current_ml = inventory.get(f"num_{category}_ml", 0)
                if ml_used > current_ml:
                    logger.error(f"Not enough ml to make {category} potions. Required: {ml_used} ml, Available: {current_ml} ml.")
                    raise HTTPException(status_code=400, detail=f"Not enough ml to make {category} potions.")

            # Update potions in inventory
            for category, potions_added in total_potions_added.items():
                if potions_added > 0:
                    sql_update_potions = sqlalchemy.text(f"""
                        UPDATE global_inventory
                        SET num_{category}_potions = num_{category}_potions + :potions_added
                        WHERE id = :inventory_id
                    """)
                    connection.execute(sql_update_potions, {'potions_added': potions_added, 'inventory_id': inventory['id']})
                    logger.debug(f"Added {potions_added} {category} potions to inventory.")

            # Subtract used ml from inventory
            for category, ml_used in total_ml_used.items():
                if ml_used > 0:
                    sql_update_ml = sqlalchemy.text(f"""
                        UPDATE global_inventory
                        SET num_{category}_ml = num_{category}_ml - :ml_used
                        WHERE id = :inventory_id
                    """)
                    connection.execute(sql_update_ml, {'ml_used': ml_used, 'inventory_id': inventory['id']})
                    logger.debug(f"Subtracted {ml_used} ml from {category} inventory.")

            logger.info(f"Successfully processed delivery for order_id: {order_id}")
            return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception(f"Database error during post_deliver_bottles for order_id: {order_id}")
        raise HTTPException(status_code=500, detail="Database error.")
    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise he
    except Exception:
        logger.exception(f"Unexpected error during post_deliver_bottles for order_id: {order_id}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.post("/plan", summary="Get Bottle Plan", description="Generates bottle production plan based on global inventory.")
def get_bottle_plan():
    """
    Generate bottle plan based on available ml in global_inventory.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    logger.debug("Generating bottle plan based on current inventory.")

    try:
        with db.engine.begin() as connection:
            sql_select = "SELECT num_green_ml FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_ml = row['num_green_ml']
            logger.debug(f"Available Green ML: {num_green_ml} ml.")

        # Calculate the number of green potions that can be produced
        num_potions = num_green_ml // ML_PER_POTION
        if num_potions > 0:
            return_plan = [{"potion_type": [0, 100, 0, 0], "quantity": num_potions}]
            logger.info(f"Bottle plan generated: {return_plan}")
        else:
            return_plan = []
            logger.info("No sufficient ML available to generate bottle plan.")

        return return_plan

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error during get_bottle_plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error during get_bottle_plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

if __name__ == "__main__":
    print(get_bottle_plan())