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

    @validator('potion_type')
    def potion_type_must_sum_to_100(cls, potion_type_value):
        if len(potion_type_value) != 4:
            raise ValueError('potion_type must have exactly four elements.')
        if sum(potion_type_value) != 100:
            raise ValueError('potion_type must sum to 100.')
        return potion_type_value

    @validator('quantity')
    def quantity_must_be_positive(cls, quantity_value):
        if quantity_value < 1:
            raise ValueError('Quantity must be at least 1')
        return quantity_value

@router.post("/deliver/{order_id}", summary="Deliver Bottles", description="Process delivery of bottles.")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """
    Process delivery of bottles to global_inventory.
    """
    logger.debug("bottler/deliver - in")
    logger.debug(f"Potions delivered: {potions_delivered}")
    logger.debug(f"Order Id: {order_id}")

    total_potions_added = {}
    total_ml_used = {}

    try:
        with db.engine.begin() as connection:
            # Fetch current inventory once
            sql_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            inventory = result.mappings().one_or_none()

            if inventory is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            logger.debug(f"Current Inventory: {inventory}")

            # Initialize totals
            for potion_key in POTION_TYPE_MAP.values():
                total_potions_added[potion_key] = 0
                total_ml_used[potion_key] = 0

            # Process each delivered potion
            for potion in potions_delivered:
                potion_key = tuple(potion.potion_type)
                potion_category = POTION_TYPE_MAP.get(potion_key, None)

                if potion_category is None:
                    logger.error(f"Unknown potion type: {potion.potion_type}")
                    raise HTTPException(status_code=400, detail=f"Unknown potion type: {potion.potion_type}")

                num_potions = potion.quantity
                ml_used = num_potions * 100  # Assuming each potion uses 100 ml

                total_potions_added[potion_category] += num_potions
                total_ml_used[potion_category] += ml_used

                logger.debug(f"Processing {num_potions} {potion_category} potions, using {ml_used} ml.")

            # Check inventory for each potion
            for category, ml_used in total_ml_used.items():
                current_ml = inventory.get(f"num_{category}_ml", 0)
                if ml_used > current_ml:
                    logger.error(f"Not enough volume to make {category} potions.")
                    raise HTTPException(status_code=400, detail=f"Not enough volume to make {category} potions.")

            # Update inventory for each potion
            for category, potions_added in total_potions_added.items():
                if potions_added > 0:
                    # Update potions
                    sql_update_potions = sqlalchemy.text(f"""
                        UPDATE global_inventory
                        SET num_{category}_potions = num_{category}_potions + :potions_added
                        WHERE id = :inventory_id
                    """)
                    connection.execute(sql_update_potions, {'potions_added': potions_added, 'inventory_id': inventory['id']})
                    logger.debug(f"Updated Potions: Added {potions_added} {category} potions.")

            for category, ml_used in total_ml_used.items():
                if ml_used > 0:
                    # Subtract used volume
                    sql_update_ml = sqlalchemy.text(f"""
                        UPDATE global_inventory
                        SET num_{category}_ml = num_{category}_ml - :ml_used
                        WHERE id = :inventory_id
                    """)
                    connection.execute(sql_update_ml, {'ml_used': ml_used, 'inventory_id': inventory['id']})
                    logger.debug(f"Updated ML: Subtracted {ml_used} ml from {category} inventory.")

            logger.debug("bottler/deliver - out")
            for category in POTION_TYPE_MAP.values():
                logger.debug(f"Total {category.capitalize()} Potions Added: {total_potions_added[category]}")
                logger.debug(f"Total {category.capitalize()} ML Used: {total_ml_used[category]}")

        return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during bottler/deliver")
        raise HTTPException(status_code=500, detail="Database error.")
    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise he
    except Exception as e:
        logger.exception("Unexpected error during bottler/deliver")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

@router.post("/plan", summary="Get Bottle Plan", description="Generates bottle production plan based on global inventory.")
def get_bottle_plan():
    """
    Generate bottle plan based on available volume in globa_inventory.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    logger.debug("bottler/plan - in")
    try:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory;"))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_ml = row['num_green_ml']
            logger.debug(f"Number of Green ML: {num_green_ml}")

        num_potions = num_green_ml // 100
        return_plan = [{"potion_type": [0, 100, 0, 0], "quantity": num_potions}] if num_potions > 0 else []

        logger.debug("bottler/plan - out")
        logger.debug(f"Bottle Plan: {return_plan}")

        return return_plan

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during bottler/plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception as e:
        logger.exception("Unexpected error during bottler/plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

if __name__ == "__main__":
    print(get_bottle_plan())