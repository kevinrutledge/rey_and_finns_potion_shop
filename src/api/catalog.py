import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
from src import game_constants as gc
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
            logger.debug(f"Executing query to fetch latest in-game time: {query_game_time.strip()}")
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise ValueError("No in-game time found in database.")

            # Fetch current inventory and capacities
            query = """
                SELECT potion_capacity_units, total_potions
                FROM global_inventory
                WHERE id = 1;
            """
            result = connection.execute(sqlalchemy.text(query))
            global_inventory = result.mappings().fetchone()

            if not global_inventory:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")

            potion_capacity_units = global_inventory['potion_capacity_units']
            total_potions = global_inventory['total_potions']
            potion_capacity_limit = potion_capacity_units * gc.POTION_CAPACITY_PER_UNIT

            # Select pricing strategy based on potion capacity units
            pricing_strategy = ut.Utils.select_pricing_strategy(potion_capacity_units)
            logger.info(f"Selected pricing strategy: {pricing_strategy}")

            # Get potion priorities for current day and pricing strategy
            potion_priorities = gc.POTION_PRIORITIES[current_in_game_day][pricing_strategy]
            logger.debug(f"Potion priorities for {current_in_game_day} and strategy {pricing_strategy}: {potion_priorities}")

            # Update potion prices in the database
            update_potion_price_query = """
                UPDATE potions
                SET price = :price
                WHERE name = :name;
            """
            for potion in potion_priorities:
                connection.execute(
                    sqlalchemy.text(update_potion_price_query),
                    {
                        "price": potion["price"],
                        "name": potion["name"],
                    }
                )
                logger.debug(f"Updated price for potion {potion['name']} to {potion['price']}.")

            # Fetch all potions with current_quantity > 0
            query_potions = """
                SELECT potion_id, sku, name, price, current_quantity,
                       red_ml, green_ml, blue_ml, dark_ml
                FROM potions
                WHERE current_quantity > 0;
            """
            logger.debug(f"Executing SQL Query: {query_potions.strip()}")
            result = connection.execute(sqlalchemy.text(query_potions))
            all_available_potions = result.mappings().fetchall()
            logger.debug(f"Total Available Potions: {len(all_available_potions)}")

            # Convert list of dicts for easier processing
            available_potions = [
                {
                    "potion_id": potion["potion_id"],
                    "sku": potion["sku"],
                    "name": potion["name"],
                    "price": potion["price"],
                    "current_quantity": potion["current_quantity"],
                    "potion_type": [
                        potion["red_ml"],
                        potion["green_ml"],
                        potion["blue_ml"],
                        potion["dark_ml"]
                    ]
                }
                for potion in all_available_potions
            ]

            # Determine number of potions to consider based on strategy
            if pricing_strategy == "PRICE_STRATEGY_SKIMMING":
                num_potions_to_consider = 3
            elif pricing_strategy == "PRICE_STRATEGY_PENETRATION":
                num_potions_to_consider = 5
            else:
                num_potions_to_consider = len(potion_priorities)

            potion_priorities = potion_priorities[:num_potions_to_consider]

            # Build the catalog items based on potion priorities
            catalog_items = []
            catalog_limit = 6

            for priority_potion in potion_priorities:
                # Match available potions based on name and composition
                matching_potions = [
                    potion for potion in available_potions
                    if potion["name"] == priority_potion["name"] and
                    potion["potion_type"] == priority_potion["composition"]
                ]

                if matching_potions:
                    potion = matching_potions[0]
                    catalog_item = CatalogItem(
                        sku=potion["sku"],
                        name=potion["name"],
                        quantity=potion["current_quantity"],
                        price=potion["price"],
                        potion_type= ut.Utils.normalize_potion_type(potion["potion_type"])
                    )
                    catalog_items.append(catalog_item)
                    logger.debug(f"Added to Catalog based on priority: {catalog_item}")
                    if len(catalog_items) >= catalog_limit:
                        break

            # Fill remaining catalog slots with other available potions if needed
            if len(catalog_items) < catalog_limit:
                remaining_slots = catalog_limit - len(catalog_items)
                logger.debug(f"Filling remaining {remaining_slots} catalog slots with other available potions.")

                # Exclude already added potions
                additional_potions = [
                    potion for potion in available_potions
                    if not any(p.sku == potion["sku"] for p in catalog_items)
                ]

                # Sort additional potions by quantity descending
                additional_potions_sorted = sorted(
                    additional_potions,
                    key=lambda x: x["current_quantity"],
                    reverse=True
                )

                for potion in additional_potions_sorted[:remaining_slots]:
                    catalog_item = CatalogItem(
                        sku=potion["sku"],
                        name=potion["name"],
                        quantity=potion["current_quantity"],
                        price=potion["price"],
                        potion_type= ut.Utils.normalize_potion_type(potion["potion_type"])
                    )
                    catalog_items.append(catalog_item)
                    logger.debug(f"Added to Catalog as additional: {catalog_item}")

    except HTTPException as he:
        logger.error(f"HTTPException in get_catalog: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in get_catalog: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    logger.info(f"Final Catalog Items (Total: {len(catalog_items)}): {catalog_items}")
    return catalog_items