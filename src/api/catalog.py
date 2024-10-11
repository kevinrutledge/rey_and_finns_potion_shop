import sqlalchemy
import logging
from src import database as db
from src.utilities import Utils as ut
from src.potions import POTION_PRIORITIES
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
        # Determine current in game time
        real_time = ut.get_current_real_time()
        in_game_day, in_game_hour = ut.compute_in_game_time(real_time)
        hour_block = ut.get_hour_block(in_game_hour)
        logger.debug(f"Current Real Time: {real_time}")
        logger.debug(f"In-Game Time - Day: {in_game_day}, Hour: {in_game_hour}, Block: {hour_block}")

        # Fetch potion demands for current time
        day_potions = POTION_PRIORITIES.get(in_game_day, {}).get(hour_block, [])
        if not day_potions:
            logger.warning(f"No potion coefficients found for Day: {in_game_day}, Hour Block: {hour_block}. Using default potions.")
        
        logger.debug(f"Potion Demands for Current Time: {day_potions}")

        # Fetch all potions with current_quantity > 0
        with db.engine.begin() as connection:
            query = """
                SELECT potion_id, sku, name, price, current_quantity,
                       red_ml, green_ml, blue_ml, dark_ml
                FROM potions
                WHERE current_quantity > 0;
            """
            logger.debug(f"Executing SQL Query: {query.strip()}")
            result = connection.execute(sqlalchemy.text(query))
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

        logger.debug(f"Processed Available Potions: {available_potions}")

        # Prioritize potions based on demand
        prioritized_potions = []
        catalog_limit = 6

        for demand_potion in day_potions:
            # Match potions based on name and composition
            matching_potions = [
                potion for potion in available_potions
                if potion["name"] == demand_potion["name"] and
                   potion["potion_type"] == demand_potion["composition"]
            ]

            if matching_potions:
                potion = matching_potions[0]
                catalog_item = CatalogItem(
                    sku=potion["sku"],
                    name=potion["name"],
                    quantity=potion["current_quantity"],
                    price=potion["price"],
                    potion_type=potion["potion_type"]
                )
                prioritized_potions.append(catalog_item)
                logger.debug(f"Added to Catalog based on demand: {catalog_item}")
                if len(prioritized_potions) >= catalog_limit:
                    break

        # Fill remaining catalog slots with other available potions
        if len(prioritized_potions) < catalog_limit:
            remaining_slots = catalog_limit - len(prioritized_potions)
            logger.debug(f"Filling remaining {remaining_slots} catalog slots with other available potions.")

            # Exclude already added potions
            additional_potions = [
                potion for potion in available_potions
                if not any(p.sku == potion["sku"] for p in prioritized_potions)
            ]

            # Sort additional potions by overall demand (descending) or any other priority
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
                    potion_type=potion["potion_type"]
                )
                prioritized_potions.append(catalog_item)
                logger.debug(f"Added to Catalog as additional: {catalog_item}")

        logger.info(f"Final Catalog Items (Total: {len(prioritized_potions)}): {prioritized_potions}")

    except HTTPException as he:
        logger.error(f"HTTPException in checkout: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return prioritized_potions