import sqlalchemy
import logging
import traceback
from src import database as db
from src import potion_coefficients as po
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
    logger = logging.getLogger("admin.reset")
    logger.info("POST /admin/reset called.")
    logger.debug("Starting game state reset process.")

    try:
        with db.engine.begin() as connection:
            # Reset gold to 100 in global_inventory
            reset_gold_query = """
                UPDATE global_inventory
                SET gold = 100
                WHERE id = 1;
            """
            logger.debug(f"Executing SQL Query to reset gold: {reset_gold_query.strip()}")
            connection.execute(sqlalchemy.text(reset_gold_query))
            logger.info("Gold has been reset to 100.")

            # Remove all potions from the potions table
            delete_potions_query = """
                DELETE FROM potions;
            """
            logger.debug(f"Executing SQL Query to delete all potions: {delete_potions_query.strip()}")
            connection.execute(sqlalchemy.text(delete_potions_query))
            logger.info("All potions have been removed from the inventory.")

            # Remove all barrels from the barrels table
            delete_barrels_query = """
                DELETE FROM barrels;
            """
            logger.debug(f"Executing SQL Query to delete all barrels: {delete_barrels_query.strip()}")
            connection.execute(sqlalchemy.text(delete_barrels_query))
            logger.info("All barrels have been removed from the inventory.")

            # Delete all cart_items
            delete_cart_items_query = """
                DELETE FROM cart_items;
            """
            logger.debug(f"Executing SQL Query to delete all cart items: {delete_cart_items_query.strip()}")
            connection.execute(sqlalchemy.text(delete_cart_items_query))
            logger.info("All cart items have been removed.")
            delete_carts_query = """
                DELETE FROM carts;
            """
            logger.debug(f"Executing SQL Query to delete all carts: {delete_carts_query.strip()}")
            connection.execute(sqlalchemy.text(delete_carts_query))
            logger.info("All carts have been removed.")

            # Insert default potions into the potions table
            insert_potions_query = """
                INSERT INTO potions (sku, name, red_ml, green_ml, blue_ml, dark_ml, total_ml, price, description, current_quantity)
                VALUES (:sku, :name, :red_ml, :green_ml, :blue_ml, :dark_ml, :total_ml, :price, :description, :current_quantity);
            """
            logger.debug(f"Preparing to insert default potions.")
            for potion in po.DEFAULT_POTIONS:
                logger.debug(f"Inserting potion: {potion}")
                connection.execute(
                    sqlalchemy.text(insert_potions_query),
                    {
                        "sku": potion["sku"],
                        "name": potion["name"],
                        "red_ml": potion["red_ml"],
                        "green_ml": potion["green_ml"],
                        "blue_ml": potion["blue_ml"],
                        "dark_ml": potion["dark_ml"],
                        "total_ml": potion["total_ml"],
                        "price": potion["price"],
                        "description": potion["description"],
                        "current_quantity": potion["current_quantity"]
                    }
                )
                logger.info(f"Inserted default potion: {potion['sku']}.")

            logger.info("Default potions have been initialized.")

    except Exception as e:
        logger.error(f"Exception occurred during reset: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to reset the game state.")

    logger.info("POST /admin/reset completed successfully.")
    return {"message": "Game state has been reset successfully."}
