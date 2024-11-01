import sqlalchemy
import logging
from src import database as db
from src import potion_config as gc
from fastapi import APIRouter, Depends, HTTPException
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
    logger.info("POST /admin/reset called.")

    try:
        with db.engine.begin() as connection:
            # Reset global_inventory to initial values
            reset_global_inventory_query = """
                UPDATE temp_global_inventory
                SET gold = 100,
                    total_potions = 0,
                    total_ml = 0,
                    red_ml = 0,
                    green_ml = 0,
                    blue_ml = 0,
                    dark_ml = 0,
                    potion_capacity_units = 1,
                    ml_capacity_units = 1;
            """
            connection.execute(sqlalchemy.text(reset_global_inventory_query))
            logger.info("global_inventory reset to initial state.")

            # Set current_quantity of all potions to 0
            reset_potions_query = """
                UPDATE temp_potions
                SET current_quantity = 0;
            """
            connection.execute(sqlalchemy.text(reset_potions_query))
            logger.info("All potions quantities reset to 0.")

            # Delete all cart_items and carts
            delete_cart_items_query = "DELETE FROM temp_cart_items;"
            connection.execute(sqlalchemy.text(delete_cart_items_query))
            logger.info("All cart_items deleted.")

            delete_carts_query = "DELETE FROM temp_carts;"
            connection.execute(sqlalchemy.text(delete_carts_query))
            logger.info("All carts deleted.")

            # Reset ledger entries
            delete_ledger_entries_query = "DELETE FROM temp_ledger_entries;"
            connection.execute(sqlalchemy.text(delete_ledger_entries_query))
            logger.info("All ledger_entries deleted.")

    except Exception as e:
        logger.exception(f"Unhandled exception in reset_shop: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    logger.info("Shop reset to initial state successfully.")
    return {"success": True, "message": "Shop has been reset to initial state."}
