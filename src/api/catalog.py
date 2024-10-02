import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/catalog",
    tags=["catalog"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.get("/catalog/", tags=["catalog"], summary="Get Catalog", description="Retrieve current catalog of available items.")
def get_catalog():
    """
    Retrieve current catalog of available items.
    Each unique item combination must have only single price.
    """
    try:
        logger.debug("Fetching current catalog from global_inventory.")

        with db.engine.begin() as connection:
            # Query to fetch the number of green potions
            sql_select = "SELECT num_green_potions FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            logger.debug(f"Number of Green Potions available: {num_green_potions}")

        # Construct the catalog based on available potions
        if num_green_potions > 0:
            return_catalog = [
                {
                    "sku": "GREEN_POTION_0",
                    "name": "Green Potion",
                    "quantity": num_green_potions,
                    "price": 50,
                    "potion_type": [0, 100, 0, 0],
                }
            ]
            logger.info(f"Catalog generated with Green Potions: {return_catalog}")
        else:
            return_catalog = []
            logger.info("Catalog is empty. No potions available for sale.")

        return return_catalog

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error occurred while fetching the catalog.")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("An unexpected error occurred while fetching the catalog.")
        raise HTTPException(status_code=500, detail="Internal Server Error.")