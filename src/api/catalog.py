import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src import database as db
from src.utilities import CatalogManager

logger = logging.getLogger(__name__)

router = APIRouter()

class CatalogItem(BaseModel):
    sku: str
    name: str
    quantity: int
    price: int
    potion_type: List[int]  # [red_ml, green_ml, blue_ml, dark_ml]

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Get available potions for sale, maximum 6 items."""
    try:
        engine = db.get_engine()
        with engine.begin() as conn:
            items = CatalogManager.get_available_potions(conn)
            
            if items:
                logger.debug(
                    f"Current catalog - available potions: "
                    f"{[(item['sku'], item['quantity']) for item in items]}"
                )
            else:
                logger.debug("Current catalog - no potions available")
            
            return [
                CatalogItem(
                    sku=item['sku'],
                    name=item['name'],
                    quantity=item['quantity'],
                    price=item['price'],
                    potion_type=item['potion_type']
                )
                for item in items
            ]
            
    except Exception as e:
        logger.error(f"Failed to generate catalog: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate catalog")