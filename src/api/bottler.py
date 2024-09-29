import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
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

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    logger.debug("bottler/deliver - in")
    logger.debug(f"Potions delivered: {potions_delivered}")
    logger.debug(f"Order Id: {order_id}")

    with db.engine.begin() as connection:
        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                num_potions = potion.quantity
                ml_used = num_potions * 100

                sql_statement_select = "SELECT num_green_potions, num_green_ml FROM global_inventory;"
                result = connection.execute(sqlalchemy.text(sql_statement_select))
                row = result.mappings().one()

                num_green_potions = row['num_green_potions']
                num_green_ml = row['num_green_ml']

                if ml_used > num_green_ml:
                    logger.error("Not enough ml to brew potions.")
                    raise HTTPException(status_code=400, detail="Not enough ml to brew potions.")

                sql_statement_potions = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET num_green_potions = num_green_potions + :num_potions
                """)
                connection.execute(sql_statement_potions, {'num_potions': num_potions})

                sql_statement_ml = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET num_green_ml = num_green_ml - :ml_used
                """)
                connection.execute(sql_statement_ml, {'ml_used': ml_used})

    logger.debug("bottler/deliver - out")
    logger.debug(f"Num Green Potions: {num_green_potions}")
    logger.debug(f"Num Green ml: {num_green_ml}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory;"))
        num_green_ml = result.mappings().one()['num_green_ml']

    num_potions = num_green_ml // 100
    return_plan = [{"potion_type": [0, 100, 0, 0], "quantity": num_potions}]

    logger.debug("bottler/plan - out")
    logger.debug(f"Number of potions: {return_plan}")

    if num_potions > 0:
        return return_plan

    return []

if __name__ == "__main__":
    print(get_bottle_plan())