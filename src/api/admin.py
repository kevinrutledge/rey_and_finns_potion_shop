import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src.api.carts import carts, cart_items

logger = logging.getLogger(__name__)

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
        row = result.mappings().one()

        num_green_potions = row['num_green_potions']
        num_green_ml = row['num_green_ml']
        gold = row['gold']

    logger.debug("admin/reset - out")
    logger.debug(f"Num Green Potions: {num_green_potions}")
    logger.debug(f"Num Green ml: {num_green_ml}")
    logger.debug(f"Gold: {gold}")

    return "OK"
