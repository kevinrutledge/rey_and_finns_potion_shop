import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from src.api.carts import carts, cart_items

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset", summary="Reset Game State", description="Resets game inventory and clears all carts.")
def reset():
    """
    Reset game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    try:
        # clear in-memory data structures
        carts.clear()
        cart_items.clear()
        logger.debug("Cleared carts and cart_items.")

        with db.engine.begin() as connection:
            # Reset inventory in global database
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
            logger.debug("Executed inventory reset SQL statement.")

            # Select updated inventory
            sql_statement_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_statement_select))
            row = result.mappings().one_or_none()  # Use one_or_none to handle empty results

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            num_green_ml = row['num_green_ml']
            gold = row['gold']

        # Log updated inventory
        logger.debug("admin/reset - out")
        logger.debug(f"Num Green Potions: {num_green_potions}")
        logger.debug(f"Num Green volume: {num_green_ml}")
        logger.debug(f"Gold: {gold}")

        return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during admin/reset")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception as e:
        logger.exception("Unexpected error during admin/reset")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
