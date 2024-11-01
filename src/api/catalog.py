import sqlalchemy
import logging
from src import database as db
from src import potion_utilities as pu
from src import potion_config as pc
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()

class CatalogItem(BaseModel):
    sku: str
    name: str
    quantity: int
    price: int
    potion_type: List[int]  # [red_ml, green_ml, blue_ml, dark_ml]


@router.get("/catalog/", tags=["catalog"], summary="Get Catalog", description="Retrieve current catalog of available items.")
def get_catalog():
    """
    Retrieve current catalog of available items.
    Each unique item combination must have only single price.
    """
    logger.info("GET /catalog/ endpoint called.")
    try:
        with db.engine.begin() as connection:
            # Fetch current in-game time
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM temp_in_game_time
                ORDER BY created_at DESC
                LIMIT 1;
            """
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise HTTPException(status_code=500, detail="No in-game time found in database.")

            # Fetch global inventory
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units, total_potions, red_ml, green_ml, blue_ml, dark_ml
                FROM temp_global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            global_inventory = result.mappings().fetchone()

            if not global_inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            gold = global_inventory['gold']
            potion_capacity_units = global_inventory['potion_capacity_units']
            ml_capacity_units = global_inventory['ml_capacity_units']
            potion_capacity_limit = potion_capacity_units * pc.POTION_CAPACITY_PER_UNIT
            ml_capacity_limit = ml_capacity_units * pc.ML_CAPACITY_PER_UNIT

            ml_inventory = {
                'red_ml': global_inventory['red_ml'],
                'green_ml': global_inventory['green_ml'],
                'blue_ml': global_inventory['blue_ml'],
                'dark_ml': global_inventory['dark_ml'],
            }

            # Fetch current potion inventory
            query_potions = """
                SELECT sku, current_quantity
                FROM temp_potions;
            """
            result = connection.execute(sqlalchemy.text(query_potions))
            potions = result.mappings().all()
            potion_inventory = {row['sku']: row['current_quantity'] for row in potions}

            # Determine pricing strategy
            current_strategy = pu.PotionShopLogic.determine_pricing_strategy(
                gold=gold,
                ml_capacity_units=ml_capacity_units,
                potion_capacity_units=potion_capacity_units
            )
            logger.info(f"Determined pricing strategy: {current_strategy}")

            # Get potion priorities
            potion_priorities = pu.PotionShopLogic.get_potion_priorities(
                current_day=current_in_game_day,
                current_strategy=current_strategy,
                potion_priorities=pc.POTION_PRIORITIES
            )

            # Update potion prices in database based on priorities
            update_potion_price_query = """
                UPDATE temp_potions
                SET price = :price
                WHERE sku = :sku;
            """
            for potion in potion_priorities:
                connection.execute(
                    sqlalchemy.text(update_potion_price_query),
                    {
                        "price": potion["price"],
                        "sku": potion["sku"],
                    }
                )
                logger.debug(f"Updated price for potion {potion['sku']} to {potion['price']}.")

            # Update catalog based on priorities and inventory
            catalog = pu.PotionShopLogic.update_catalog(
                potion_priorities=potion_priorities,
                potion_inventory=potion_inventory,
                max_catalog_size=6
            )
            logger.debug(f"Updated catalog: {catalog}")

            # Collect all SKUs in catalog
            catalog_skus = [item['sku'] for item in catalog]

            # Fetch updated potion details from database
            query_potion_details = """
                SELECT sku, name, red_ml, green_ml, blue_ml, dark_ml, price
                FROM temp_potions
                WHERE sku IN :skus;
            """
            # Handle single SKU case by ensuring it's a tuple
            if len(catalog_skus) == 1:
                skus_tuple = (catalog_skus[0],)
            else:
                skus_tuple = tuple(catalog_skus)
            result = connection.execute(
                sqlalchemy.text(query_potion_details),
                {'skus': skus_tuple}
            )
            potion_details = {row['sku']: row for row in result.mappings().all()}

            # Build catalog items using fetched potion details
            catalog_items = []
            for item in catalog:
                sku = item['sku']
                if sku not in potion_details:
                    logger.error(f"Potion details for SKU {sku} not found in database.")
                    continue

                row = potion_details[sku]
                potion_type = [
                    row['red_ml'],
                    row['green_ml'],
                    row['blue_ml'],
                    row['dark_ml']
                ]
                potion_type_normalized = pu.Utilities.normalize_potion_type(potion_type)

                catalog_item = CatalogItem(
                    sku=sku,
                    name=row['name'],
                    quantity=item['quantity'],
                    price=row['price'],  # Use updated price from database
                    potion_type=potion_type_normalized
                )
                catalog_items.append(catalog_item)
                logger.debug(f"Added to Catalog: {catalog_item}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_catalog: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_catalog: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"Final Catalog Items (Total: {len(catalog_items)}): {catalog_items}")
    return catalog_items