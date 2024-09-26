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
    total_ml = 0
    total_cost = 0

    for barrel in barrels_delivered:
        if barrel.potion_type == [0, 100, 0, 0]:
            total_ml += barrel.ml_per_barrel * barrel.quantity
            total_cost += barrel.price * barrel.quantity

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                "UPDATE global_inventory SET num_green_ml = num_green_ml + :ml, gold = gold - :cost"
            ),
            {"ml": total_ml, "cost": total_cost},
        )

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory"))
        row = result.fetchone()
        if row:
            num_green_potions = row.num_green_potions
            gold = row.gold
        else:
            num_green_potions = 0
            gold = 100

    purchase_plan = []

    if num_green_potions < 10:
        green_barrels = []
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 100, 0, 0]:
                green_barrels.append(barrel)

        if green_barrels:
            affordable_barrels = []
            for barrel in green_barrels:
                if barrel.price <= gold and barrel.quantity > 0:
                    affordable_barrels.append(barrel)

            if affordable_barrels:
                small_green_barrel = affordable_barrels[0]
                for barrel in affordable_barrels:
                    if barrel.price < small_green_barrel.price:
                        small_green_barrel = barrel
                purchase_plan.append({"sku": small_green_barrel.sku, "quantity": 1})

    return purchase_plan
