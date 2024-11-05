import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.utilities import InventoryManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

@router.get("/audit")
def get_inventory():
    """Get current inventory state."""
    try:
        with db.engine.begin() as conn:
            state = InventoryManager.get_inventory_state(conn)
            
            logger.debug(
                f"Current state - Potions: {state['total_potions']}, "
                f"ML: {state['total_ml']}, Gold: {state['gold']}"
            )
            
            return {
                "number_of_potions": state['total_potions'],
                "ml_in_barrels": state['total_ml'],
                "gold": state['gold']
            }
            
    except Exception as e:
        logger.error(f"Failed to get inventory state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get inventory state")

@router.post("/plan")
def get_capacity_plan():
    """Get capacity purchase plan."""
    try:
        with db.engine.begin() as conn:
            state = InventoryManager.get_inventory_state(conn)
            return InventoryManager.get_capacity_purchase_plan(conn, state)
            
    except Exception as e:
        logger.error(f"Failed to get capacity plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to get capacity plan")

@router.post("/deliver/{order_id}")
def deliver_capacity(capacity_purchase: CapacityPurchase, order_id: int):
    """Process capacity purchase delivery."""
    logger.debug(
        f"Processing capacity upgrade - "
        f"Potion: {capacity_purchase.potion_capacity}, "
        f"ML: {capacity_purchase.ml_capacity}"
    )
    
    try:
        with db.engine.begin() as conn:
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            InventoryManager.process_capacity_upgrade(
                conn,
                capacity_purchase.potion_capacity,
                capacity_purchase.ml_capacity,
                time_id
            )
            
            return {"success": True}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to process capacity upgrade: {e}")
        raise HTTPException(status_code=500, detail="Failed to process capacity upgrade")