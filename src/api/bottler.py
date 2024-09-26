import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

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
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                num_potions = potion.quantity
                ml_used = num_potions * 100

                connection.execute(sqlalchemy.text(
                    f"UPDATE global_inventory SET num_green_potions = num_green_potions + {num_potions};"
                ))

                connection.execute(sqlalchemy.text(
                    f"UPDATE global_inventory SET num_green_ml = num_green_ml - {ml_used};"
                ))

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

    if num_potions > 0:
        return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": num_potions
            }
        ]

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": 0,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())