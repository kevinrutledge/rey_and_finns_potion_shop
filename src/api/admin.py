import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src.api.carts import carts, cart_items

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    carts.clear()
    cart_items.clear()
    with db.engine.begin() as connection:
        sql_statement_reset = sqlalchemy.text("""
            UPDATE global_inventory
            SET num_green_potions = :num_green_potions,
                num_green_ml = :num_green_ml,
                gold = :gold
        """)
        connection.execute(sql_statement_reset, {
            'num_green_potions': 0,
            'num_green_ml': 0,
            'gold': 100
        })

        sql_statement_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
        result = connection.execute(sqlalchemy.text(sql_statement_select))
        num_green_potions = result.mappings().one()['num_green_potions']
        num_green_ml = result.mappings().one()['num_green_ml']
        gold = result.mappings().one()['gold']

    logging.debug("admin/reset - out")
    logging.debug(f"Num Green Potions: {num_green_potions}")
    logging.debug(f"Num Green ml: {num_green_ml}")
    logging.debug(f"Gold: {gold}")

    return "OK"
