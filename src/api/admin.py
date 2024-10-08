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
            # Drop tables in reverse order of dependencies
            logger.debug("Dropping existing tables if any.")
            drop_tables_query = """
                DROP TABLE IF EXISTS ledger_entries CASCADE;
                DROP TABLE IF EXISTS cart_items CASCADE;
                DROP TABLE IF EXISTS carts CASCADE;
                DROP TABLE IF EXISTS customers CASCADE;
                DROP TABLE IF EXISTS customer_visits CASCADE;
                DROP TABLE IF EXISTS potions CASCADE;
                DROP TABLE IF EXISTS global_inventory CASCADE;
                DROP TABLE IF EXISTS barrels CASCADE;
                DROP TABLE IF EXISTS barrel_visits CASCADE;
            """
            logger.debug("Executing DROP TABLE queries.")
            connection.execute(sqlalchemy.text(drop_tables_query))
            logger.info("All existing tables have been dropped.")

            # Recreate tables with corrected DDL
            logger.debug("Creating new tables with corrected schema.")

            create_tables_query = """
            -- Barrel Visits Table (Parent)
            CREATE TABLE barrel_visits (
                barrel_visit_id BIGSERIAL PRIMARY KEY,
                visit_time TIMESTAMPTZ NOT NULL,
                wholesale_catalog JSON,
                in_game_day VARCHAR,
                in_game_hour INT
            );

            -- Barrels Table (Reference Barrel Visits)
            CREATE TABLE barrels (
                barrel_id BIGSERIAL PRIMARY KEY,
                barrel_visit_id BIGSERIAL NOT NULL,
                sku VARCHAR NOT NULL,
                ml_per_barrel INT NOT NULL,
                potion_type VARCHAR(10) NOT NULL,
                price INT NOT NULL,
                quantity INT NOT NULL
            );

            -- Global Inventory Table (Independent)
            CREATE TABLE global_inventory (
                id BIGINT PRIMARY KEY,
                gold INT DEFAULT 100,
                total_potions INT DEFAULT 0,
                total_ml INT DEFAULT 0,
                red_ml INT DEFAULT 0,
                green_ml INT DEFAULT 0,
                blue_ml INT DEFAULT 0,
                dark_ml INT DEFAULT 0,
                potion_capacity_units INT DEFAULT 1,
                ml_capacity_units INT DEFAULT 1
            );

            -- Potions Table (Independent)
            CREATE TABLE potions (
                potion_id BIGSERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                sku VARCHAR NOT NULL UNIQUE,
                red_ml INT NOT NULL,
                green_ml INT NOT NULL,
                blue_ml INT NOT NULL,
                dark_ml INT NOT NULL,
                total_ml INT NOT NULL,
                price INT NOT NULL,
                description TEXT,
                current_quantity INT NOT NULL
            );

            -- Customers Table (References Visits)
            CREATE TABLE customers (
                customer_id BIGSERIAL PRIMARY KEY,
                visit_id BIGINT REFERENCES visits(visit_id),
                customer_name VARCHAR NOT NULL,
                character_class VARCHAR NOT NULL,
                level INT NOT NULL
            );

            -- Customer Visits Table (Parent)
            CREATE TABLE customer_visits (
                visit_id BIGSERIAL PRIMARY KEY,
                visit_time TIMESTAMPTZ NOT NULL,
                customers JSON,
                in_game_day VARCHAR,
                in_game_hour INT
            );

            -- Carts Table (References Customers)
            CREATE TABLE carts (
                cart_id BIGSERIAL PRIMARY KEY,
                customer_id BIGINT REFERENCES customers(customer_id),
                in_game_day VARCHAR,
                in_game_hour INT,
                created_at TIMESTAMPTZ NOT NULL,
                checked_out BOOLEAN DEFAULT FALSE,
                checked_out_at TIMESTAMPTZ,
                total_potions_bought INT DEFAULT 0,
                total_gold_paid INT DEFAULT 0,
                payment VARCHAR
            );

            -- Cart Items Table (References Carts and Potions)
            CREATE TABLE cart_items (
                cart_item_id BIGSERIAL PRIMARY KEY,
                cart_id BIGINT REFERENCES carts(cart_id),
                potion_id INT REFERENCES potions(potion_id),
                quantity INT NOT NULL,
                price INT NOT NULL,
                line_item_total INT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );

            -- Ledger Entries Table (References Potions)
            CREATE TABLE ledger_entries (
                ledger_entry_id BIGSERIAL PRIMARY KEY,
                change_type VARCHAR NOT NULL,
                sub_type VARCHAR,
                amount INT NOT NULL,
                ml_type VARCHAR,
                potion_id INT REFERENCES potions(potion_id),
                description TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
            """
            logger.debug("Executing CREATE TABLE queries.")
            connection.execute(sqlalchemy.text(create_tables_query))
            logger.info("All tables have been created with corrected schema.")

            # Insert default values into global_inventory table
            insert_default_values_query = """
                INSERT INTO global_inventory (id, gold, total_potions, total_ml, red_ml, green_ml, blue_ml, dark_ml, ml_capacity_units, potion_capacity_units)
                VALUES (:id, :gold, :total_potions, :total_ml, :red_ml, :green_ml, :blue_ml, :dark_ml, :ml_capacity_units, :potion_capacity_units)
            """
            logger.debug(f"Preparing to insert default values for global_inventory.")
            connection.execute(
                sqlalchemy.text(insert_default_values_query),
                {
                    "id": 1,
                    "gold": 100,
                    "total_potions": 0,
                    "total_ml": 0,
                    "red_ml": 0,
                    "green_ml": 0,
                    "blue_ml": 0,
                    "dark_ml": 0,
                    "ml_capacity_units": 1,
                    "potion_capacity_units": 1
                }
            )
            logger.info("Inserted default values into global_inventory.")

            # Insert default potions into potions table
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
        raise HTTPException(status_code=500, detail="Failed to reset game state.")

    logger.info("POST /admin/reset completed successfully.")
    return {"message": "Game state has been reset successfully."}
