import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;"))
        num_green_potions = result.mappings().one()['num_green_potions']

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

    logging.debug("catalog/ Get Catalog - out")
    logging.debug(f"Catalog: {return_catalog}")

    return return_catalog
