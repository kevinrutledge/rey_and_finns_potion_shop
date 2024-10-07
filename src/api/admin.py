import sqlalchemy
import logging
import traceback
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
    logger.debug("No input parameters for reset endpoint.")

    try:
        with db.engine.begin() as connection:
            # Reset global_inventory
            logger.debug("Executing SQL query to reset global_inventory table.")
            reset_global_inventory_query = """
                UPDATE global_inventory
                SET gold = 100,
                    total_potions = 0,
                    total_ml = 0,
                    red_ml = 0,
                    green_ml = 0,
                    blue_ml = 0,
                    dark_ml = 0,
                    potion_capacity_units = 1,
                    ml_capacity_units = 1
                WHERE id = 1;
            """
            logger.debug(f"SQL Query: {reset_global_inventory_query.strip()}")
            connection.execute(sqlalchemy.text(reset_global_inventory_query))
            logger.info("global_inventory table has been reset.")

            # Reset current_quantity of all potions to 0
            logger.debug("Resetting potions table to default quantities.")
            reset_potions_query = """
                UPDATE potions
                SET current_quantity = 0;
            """
            logger.debug(f"SQL Query: {reset_potions_query.strip()}")
            connection.execute(sqlalchemy.text(reset_potions_query))
            logger.info("All potions' current_quantity have been reset to 0.")

            # Populate potions with default quantities
            logger.debug("Populating potions table with default potions and initial quantities.")
            for potion in DEFAULT_POTIONS:
                # Check if potion exists
                logger.debug(f"Checking existence of potion SKU: {potion['sku']}")
                result = connection.execute(
                    sqlalchemy.text(
                        """
                        SELECT potion_id FROM potions WHERE sku = :sku;
                        """
                    ),
                    {'sku': potion['sku']}
                )
                existing_potion = result.mappings().fetchone()

                if existing_potion:
                    # Update existing potion's quantity
                    logger.debug(f"Potion SKU {potion['sku']} exists. Updating quantity to {potion['current_quantity']}.")
                    connection.execute(
                        sqlalchemy.text(
                            """
                            UPDATE potions
                            SET current_quantity = :quantity
                            WHERE sku = :sku;
                            """
                        ),
                        {
                            'quantity': potion['current_quantity'],
                            'sku': potion['sku']
                        }
                    )
                    logger.info(f"Updated potion SKU {potion['sku']} to quantity {potion['current_quantity']}.")
                else:
                    # Insert new potion
                    logger.debug(f"Potion SKU {potion['sku']} does not exist. Inserting new potion.")
                    connection.execute(
                        sqlalchemy.text(
                            """
                            INSERT INTO potions (name, sku, red_ml, green_ml, blue_ml, dark_ml, total_ml, price, description, current_quantity)
                            VALUES (:name, :sku, :red_ml, :green_ml, :blue_ml, :dark_ml, :total_ml, :price, :description, :current_quantity);
                            """
                        ),
                        {
                            'name': potion['name'],
                            'sku': potion['sku'],
                            'red_ml': potion['red_ml'],
                            'green_ml': potion['green_ml'],
                            'blue_ml': potion['blue_ml'],
                            'dark_ml': potion['dark_ml'],
                            'total_ml': potion['total_ml'],
                            'price': potion['price'],
                            'description': potion['description'],
                            'current_quantity': potion['current_quantity']
                        }
                    )
                    logger.info(f"Inserted new potion SKU {potion['sku']} with quantity {potion['current_quantity']}.")

            # Clear cart_items and carts tables
            logger.debug("Deleting all records from cart_items and carts tables.")
            delete_cart_items_query = "DELETE FROM cart_items;"
            logger.debug(f"SQL Query: {delete_cart_items_query.strip()}")
            connection.execute(sqlalchemy.text(delete_cart_items_query))
            logger.info("All records from cart_items table have been deleted.")
            delete_carts_query = "DELETE FROM carts;"
            logger.debug(f"SQL Query: {delete_carts_query.strip()}")
            connection.execute(sqlalchemy.text(delete_carts_query))
            logger.info("All records from carts table have been deleted.")

            # Clear ledger_entries table
            logger.debug("Deleting all records from ledger_entries table.")
            delete_ledger_entries_query = "DELETE FROM ledger_entries;"
            logger.debug(f"SQL Query: {delete_ledger_entries_query.strip()}")
            connection.execute(sqlalchemy.text(delete_ledger_entries_query))
            logger.info("All records from ledger_entries table have been deleted.")

            # Clear customers table
            logger.debug("Executing SQL query to delete all records from customers table.")
            delete_customers_query = "DELETE FROM customers;"
            logger.debug(f"SQL Query: {delete_customers_query.strip()}")
            connection.execute(sqlalchemy.text(delete_customers_query))
            logger.info("All records from customers table have been deleted.")

            # Reset customer_visits and customers tables
            logger.debug("Deleting all records from customer_visits and customers tables.")
            connection.execute(sqlalchemy.text("DELETE FROM customers;"))
            connection.execute(sqlalchemy.text("DELETE FROM customer_visits;"))
            logger.info("All records from customer_visits and customers tables have been deleted.")

            # Reset barrel_visits and barrels tables
            logger.debug("Deleting all records from barrel_visits and barrels tables.")
            connection.execute(sqlalchemy.text("DELETE FROM barrels;"))
            connection.execute(sqlalchemy.text("DELETE FROM barrel_visits;"))
            logger.info("All records from barrel_visits and barrels tables have been deleted.")

        # After successful operations
        logger.info("Shop state has been reset successfully.")
        logger.debug("Returning success response: {'success': True}")
        return {"success": True}

    except Exception as e:
        # Capture full traceback for detailed debugging
        traceback_str = traceback.format_exc()
        logger.error(f"Error in reset endpoint: {e}\nTraceback: {traceback_str}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
