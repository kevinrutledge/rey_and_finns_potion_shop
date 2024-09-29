import sqlalchemy
import logging
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
    logging.debug(f"Barrels delivered: {barrels_delivered}")
    logging.debug(f"Order Id: {order_id}")

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            if barrel.potion_type == [0, 1, 0, 0]:
                ml_added = barrel.ml_per_barrel * barrel.quantity

                sqlStatementMl = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET num_green_ml = num_green_ml + :ml_added
                """)
                connection.execute(sqlStatementMl, {'ml_added': ml_added})

                gold_spent = barrel.price * barrel.quantity

                sqlStatementGold = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET gold = gold - :gold_spent
                """)
                connection.execute(sqlStatementGold, {'gold_spent': gold_spent})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    logging.debug(f"Wholesale catalog: {wholesale_catalog}")

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;"))
        num_green_potions = result.mappings().one()['num_green_potions']

    purchase_plan = []

    if num_green_potions < 10:
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL":
                purchase_plan.append({
                    "sku": barrel.sku,
                    "quantity": 1
                })
                break
    
    logging.debug(f"Purchase plan: {purchase_plan}")

    return purchase_plan
