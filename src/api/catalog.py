import sqlalchemy
import logging
from src import database as db
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
    logger.info("Starting get_catalog endpoint.")
    logger.debug("No input parameters for get_catalog.")

    try:
        with db.engine.begin() as connection:
            # SQL query to fetch potions with current_quantity > 0, limited to 6
            query = """
                SELECT potion_id, sku, name, price, current_quantity,
                       red_ml, green_ml, blue_ml, dark_ml
                FROM potions
                WHERE current_quantity > 0
                LIMIT 6;
            """
            logger.debug(f"Executing SQL Query: {query.strip()}")

            result = connection.execute(sqlalchemy.text(query))
            potions = result.mappings().fetchall()
            logger.debug(f"Fetched {len(potions)} potions from the database.")

            catalog_items = []

            for potion in potions:
                logger.debug(f"Processing potion: {dict(potion)}")
                
                # Calculate total_ml to ensure it sums to 100
                total_ml = (
                    potion["red_ml"] +
                    potion["green_ml"] +
                    potion["blue_ml"] +
                    potion["dark_ml"]
                )
                logger.debug(f"Total ML for potion {potion['sku']}: {total_ml}")

                if total_ml != 100:
                    logger.warning(
                        f"Potion {potion['sku']} has total_ml {total_ml}, expected 100."
                    )
                    if total_ml > 0:
                        # Normalize the ML values to sum to 100
                        factor = 100 / total_ml
                        red_ml = int(potion["red_ml"] * factor)
                        green_ml = int(potion["green_ml"] * factor)
                        blue_ml = int(potion["blue_ml"] * factor)
                        dark_ml = int(potion["dark_ml"] * factor)
                        logger.debug(
                            f"Adjusted ML values for potion {potion['sku']}: "
                            f"red_ml={red_ml}, green_ml={green_ml}, "
                            f"blue_ml={blue_ml}, dark_ml={dark_ml}"
                        )
                    else:
                        # If total_ml is 0, set all to 0 to avoid division by zero
                        red_ml = green_ml = blue_ml = dark_ml = 0
                        logger.debug(
                            f"Set ML values to 0 for potion {potion['sku']} due to total_ml being 0."
                        )
                else:
                    red_ml = potion["red_ml"]
                    green_ml = potion["green_ml"]
                    blue_ml = potion["blue_ml"]
                    dark_ml = potion["dark_ml"]

                # Create potion_type list
                potion_type = [red_ml, green_ml, blue_ml, dark_ml]
                logger.debug(f"Potion type for {potion['sku']}: {potion_type}")

                # Assemble catalog item dictionary
                catalog_item = CatalogItem(
                    sku=potion["sku"],
                    name=potion["name"],
                    quantity=potion["current_quantity"],
                    price=potion["price"],
                    potion_type=potion_type,
                )

                logger.debug(f"Adding catalog item: {catalog_item}")
                catalog_items.append(catalog_item)

            logger.info(f"Successfully fetched {len(catalog_items)} catalog items.")

    except Exception as e:
        logger.exception(f"Error in get_catalog endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info("Ending get_catalog endpoint.")
    logger.debug(f"Returning catalog_items: {catalog_items}")
    return catalog_items