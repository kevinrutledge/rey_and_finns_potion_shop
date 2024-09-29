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

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

    @validator('potion_type')
    def potion_type_must_sum_to_100(cls, potion_type_value):
        if sum(potion_type_value) != 100:
            raise ValueError('potion_type must sum to 100')
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

    try:
        with db.engine.begin() as connection:
            for potion in potions_delivered:
                if potion.potion_type == [0, 100, 0, 0]:
                    num_potions = potion.quantity
                    ml_used = num_potions * 100

                    # Fetch current inventory
                    sql_statement_select = "SELECT num_green_potions, num_green_ml FROM global_inventory;"
                    result = connection.execute(sqlalchemy.text(sql_statement_select))
                    row = result.mappings().one_or_none()

                    if row is None:
                        logger.error("No inventory record found.")
                        raise HTTPException(status_code=500, detail="Inventory record not found.")

                    num_green_potions = row['num_green_potions']
                    num_green_ml = row['num_green_ml']
                    logger.debug(f"Current Inventory - Potions: {num_green_potions}, ML: {num_green_ml}")

                    if ml_used > num_green_ml:
                        logger.error("Not enough volume to make potions.")
                        raise HTTPException(status_code=400, detail="Not enough volume to make potions.")

                    # Update potions
                    sql_statement_potions = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET num_green_potions = num_green_potions + :num_potions
                    """)
                    connection.execute(sql_statement_potions, {'num_potions': num_potions})
                    logger.debug(f"Updated Potions: Added {num_potions} green potions.")

                    # Subtract used volume
                    sql_statement_ml = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET num_green_ml = num_green_ml - :ml_used
                    """)
                    connection.execute(sql_statement_ml, {'ml_used': ml_used})
                    logger.debug(f"Updated ML: Subtracted {ml_used} ml from inventory.")

            logger.debug("bottler/deliver - out")
            logger.debug(f"Num Green Potions after delivery: {num_green_potions + num_potions}")
            logger.debug(f"Num Green volume after delivery: {num_green_ml - ml_used}")

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

@router.post("/plan", summary="Get Bottle Plan", description="Generates a bottle production plan based on global inventory.")
def get_bottle_plan():
    """
    Generate a bottle plan based on available volume in globa_inventory.
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