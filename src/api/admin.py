import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src.api.carts import carts, cart_items

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
        sqlStatementReset = sqlalchemy.text("""
            UPDATE global_inventory
            SET num_green_potions = :num_green_potions,
                num_green_ml = :num_green_ml,
                gold = :gold
        """)
        connection.execute(sqlStatementReset, {
            'num_green_potions': 0,
            'num_green_ml': 0,
            'gold': 100
        })

    return "OK"
