import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/catalog/", tags=["catalog"], summary="Get Catalog", description="Retrieve current catalog of available items.")
def get_catalog():
    """
    Retrieve current catalog of available items.
    Each unique item combination must have only single price.
    """
    logger.info("Starting get_catalog endpoint.")

    try:
        with db.engine.begin() as connection:
            # Query potions with current_quantity > 0
            logger.debug("Executing SQL query to fetch potions with current_quantity > 0.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT potion_id, sku, name, price, current_quantity,
                           red_ml, green_ml, blue_ml, dark_ml
                    FROM potions
                    WHERE current_quantity > 0
                    LIMIT 6;  -- Limit to at most 6 potions as per API spec
                    """
                )
            )
            potions = result.mappings().fetchall()
            logger.debug(f"Fetched {len(potions)} potions from database.")

            # Prepare response list
            catalog_items = []

            for potion in potions:
                logger.debug(f"Processing potion: {dict(potion)}")
                # Calculate potion_type as list [r, g, b, d]
                total_ml = (
                    potion["red_ml"]
                    + potion["green_ml"]
                    + potion["blue_ml"]
                    + potion["dark_ml"]
                )
                logger.debug(f"Total_ml for potion {potion['sku']}: {total_ml}")
                if total_ml != 100:
                    logger.warning(
                        f"Potion {potion['sku']} has total_ml {total_ml}, expected 100."
                    )
                    # Adjust ml values proportionally to sum to 100
                    factor = 100 / total_ml if total_ml > 0 else 0
                    red_ml = int(potion["red_ml"] * factor)
                    green_ml = int(potion["green_ml"] * factor)
                    blue_ml = int(potion["blue_ml"] * factor)
                    dark_ml = int(potion["dark_ml"] * factor)
                    logger.debug(
                        f"Adjusted ml values for potion {potion['sku']}: red_ml={red_ml}, green_ml={green_ml}, blue_ml={blue_ml}, dark_ml={dark_ml}"
                    )
                else:
                    red_ml = potion["red_ml"]
                    green_ml = potion["green_ml"]
                    blue_ml = potion["blue_ml"]
                    dark_ml = potion["dark_ml"]

                potion_type = [red_ml, green_ml, blue_ml, dark_ml]

                catalog_item = {
                    "sku": potion["sku"],
                    "name": potion["name"],
                    "quantity": potion["current_quantity"],
                    "price": potion["price"],
                    "potion_type": potion_type,
                }

                logger.debug(f"Adding catalog item: {catalog_item}")
                catalog_items.append(catalog_item)

            logger.info(f"Fetched {len(catalog_items)} catalog items.")

    except Exception as e:
        logger.error(f"Error in get_catalog: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_catalog endpoint.")
    logger.debug(f"Returning catalog_items: {catalog_items}")
    return catalog_items