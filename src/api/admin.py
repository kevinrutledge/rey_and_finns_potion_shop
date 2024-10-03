import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth

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
    logger.info("Starting reset endpoint. Resetting shop state.")
    try:
        with db.engine.begin() as connection:
            # Reset global_inventory
            logger.debug("Resetting global_inventory table.")
            connection.execute(sqlalchemy.text(
                """
                UPDATE global_inventory
                SET gold = 100,
                    red_ml = 0,
                    green_ml = 0,
                    blue_ml = 0,
                    dark_ml = 0,
                    potion_capacity_units = 1,
                    ml_capacity_units = 1
                WHERE id = 1;
                """
            ))

            # Reset current_quantity of all potions to 0
            logger.debug("Resetting potion quantities to 0.")
            connection.execute(sqlalchemy.text(
                """
                UPDATE potions
                SET current_quantity = 0;
                """
            ))

            # Clear carts and cart_items tables
            logger.debug("Deleting all records from cart_items and carts tables.")
            connection.execute(sqlalchemy.text(
                """
                DELETE FROM cart_items;
                """
            ))
            connection.execute(sqlalchemy.text(
                """
                DELETE FROM carts;
                """
            ))

            # Clear ledger_entries table
            logger.debug("Deleting all records from ledger_entries table.")
            connection.execute(sqlalchemy.text(
                """
                DELETE FROM ledger_entries;
                """
            ))

            logger.info("Shop state reset successfully.")
        logger.debug("Returning success response: {'success': True}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error in reset endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
