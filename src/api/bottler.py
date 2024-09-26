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
    total_potions = 0
    total_ml_used = 0

    for potion in potions_delivered:
        if potion.potion_type == [0, 100, 0, 0]:
            total_potions += potion.quantity
            total_ml_used += potion.quantity * 100

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                "UPDATE global_inventory SET num_green_potions = num_green_potions + :potions, num_green_ml = num_green_ml - :ml"
            ),
            {"potions": total_potions, "ml": total_ml_used},
        )

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
        result = connection.execute(
            sqlalchemy.text("SELECT num_green_ml FROM global_inventory")
        )
        row = result.fetchone()
        if row:
            num_green_ml = row.num_green_ml
        else:
            num_green_ml = 0

    num_potions = num_green_ml // 100

    plan = []
    if num_potions > 0:
        plan = [
                {
                    "potion_type": [0, 100, 0, 0],
                    "quanitity": num_potions,
                }
            ]

    return plan

if __name__ == "__main__":
    print(get_bottle_plan())
