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
    logger.debug("Initiating game state reset.")

    try:
        # Clear in-memory data structures
        carts.clear()
        cart_items.clear()
        logger.info("Cleared all in-memory carts and cart items.")

        with db.engine.begin() as connection:
            # Reset inventory in the global database
            sql_reset = sqlalchemy.text("""
                UPDATE global_inventory
                SET num_green_potions = :num_green_potions,
                    num_green_ml = :num_green_ml,
                    gold = :gold
            """)
            connection.execute(sql_reset, {
                'num_green_potions': 0,
                'num_green_ml': 0,
                'gold': 100
            })
            logger.debug("Executed inventory reset SQL statement.")

            # Select updated inventory
            sql_select = "SELECT num_green_potions, num_green_ml, gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found after reset.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            num_green_ml = row['num_green_ml']
            gold = row['gold']
            logger.debug(f"Post-reset inventory state - Green Potions: {num_green_potions}, Green ML: {num_green_ml}, Gold: {gold}")

        logger.info("Game state has been successfully reset.")
        return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error occurred during game state reset.")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error occurred during game state reset.")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
