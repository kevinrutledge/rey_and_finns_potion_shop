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
    logger.debug("catalog/get_catalog - in")

    try:
        with db.engine.begin() as connection:
            sql_statement_select = "SELECT num_green_potions FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_statement_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            logger.debug(f"Number of Green Potions: {num_green_potions}")

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
        else:
            return_catalog = []

        logger.debug("catalog/get_catalog - out")
        logger.debug(f"Catalog: {return_catalog}")

        return return_catalog

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during catalog/get_catalog")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception as e:
        logger.exception("Unexpected error during catalog/get_catalog")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
