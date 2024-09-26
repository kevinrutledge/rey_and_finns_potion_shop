import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            if barrel.potion_type == 1:
                ml_added = barrel.ml_per_barrel * barrel.quantity

                connection.execute(sqlalchemy.text(
                    f"UPDATE global_inventory SET num_green_ml = num_green_ml + {ml_added};"
                ))

                gold_spent = barrel.price * barrel.quantity

                connection.execute(sqlalchemy.text(
                    f"UPDATE global_inventory SET gold = gold - {gold_spent};"
                ))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;"))
        num_green_potions = result.fetchone()['num_green_potions']

    purchase_plan = []

    if num_green_potions < 10:
        for barrel in wholesale_catalog:
            if barrel.potion_type == 1 and barrel.sku == "SMALL_GREEN_BARREL":
                purchase_plan.append({
                    "sku": barrel.sku,
                    "quantity": 1
                })
                break
    return purchase_plan