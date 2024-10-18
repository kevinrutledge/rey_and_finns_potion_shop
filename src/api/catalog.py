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
            # Get current in-game day and hour
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM in_game_time
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

            # Fetch current inventory and capacities
            query = """
                SELECT gold, potion_capacity_units, ml_capacity_units, total_potions, red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory
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
                FROM potions;
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

        # Update potion prices in database
        with db.engine.begin() as connection:
            update_potion_price_query = """
                UPDATE potions
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

        # Update catalog
        catalog = pu.PotionShopLogic.update_catalog(
            potion_priorities=potion_priorities,
            potion_inventory=potion_inventory,
            max_catalog_size=6
        )
        logger.debug(f"Updated catalog: {catalog}")

        # Build the catalog items
        catalog_items = []
        for item in catalog:
            sku = item['sku']
            potion_def = pc.POTION_DEFINITIONS.get(sku)
            if not potion_def:
                logger.error(f"Potion definition for SKU {sku} not found.")
                continue

            potion_type = [
                potion_def.get('red_ml', 0),
                potion_def.get('green_ml', 0),
                potion_def.get('blue_ml', 0),
                potion_def.get('dark_ml', 0)
            ]
            potion_type_normalized = pu.Utilities.normalize_potion_type(potion_type)

            catalog_item = CatalogItem(
                sku=sku,
                name=potion_def['name'],
                quantity=item['quantity'],
                price=item['price'],
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