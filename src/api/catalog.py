import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        sql_statement_select = "SELECT num_green_potions FROM global_inventory;"
        result = connection.execute(sqlalchemy.text(sql_statement_select))
        row = result.mappings().one()

        num_green_potions = row['num_green_potions']

    if num_green_potions > 0:
        return_catalog = [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        ]
    else:
        return_catalog = []

    logger.debug("catalog/ Get Catalog - out")
    logger.debug(f"Catalog: {return_catalog}")

    return return_catalog
