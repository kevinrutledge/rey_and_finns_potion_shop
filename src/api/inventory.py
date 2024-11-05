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
                f"Current state - gold: {state['gold']}, "
                f"potions: {state['total_potions']}/{state['max_potions']}, "
                f"ml: {state['total_ml']}/{state['max_ml']}"
            )
            
            return {
                "number_of_potions": state['total_potions'],
                "ml_in_barrels": state['total_ml'],
                "gold": state['gold']
            }
            
    except Exception as e:
        logger.error(f"Failed to get inventory state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get inventory state")

@router.post("/plan")
def get_capacity_plan():
    """Get capacity purchase plan."""
    try:
        with db.engine.begin() as conn:
            state = InventoryManager.get_inventory_state(conn)
            logger.debug(
                f"Planning capacity - current units: potions {state['potion_capacity_units']}, "
                f"ml {state['ml_capacity_units']}"
            )
            
            plan = InventoryManager.get_capacity_purchase_plan(conn, state)
            
            if plan['potion_capacity'] > 0 or plan['ml_capacity'] > 0:
                logger.debug(
                    f"Capacity plan - potion units: {plan['potion_capacity']}, "
                    f"ml units: {plan['ml_capacity']}"
                )
            else:
                logger.debug("Capacity plan - no upgrades needed")
                
            return plan
            
    except Exception as e:
        logger.error(f"Failed to get capacity plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get capacity plan")

@router.post("/deliver/{order_id}")
def deliver_capacity(capacity_purchase: CapacityPurchase, order_id: int):
    """Process capacity purchase delivery."""
    logger.debug(f"Processing capacity upgrade - order: {order_id}")
    
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
            
            state = InventoryManager.get_inventory_state(conn)
            total_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000
            
            if state['gold'] < total_cost:
                logger.debug(f"Insufficient gold - required: {total_cost}, available: {state['gold']}")
                raise HTTPException(status_code=400, detail="Insufficient gold for capacity upgrade")
            
            InventoryManager.process_capacity_upgrade(
                conn,
                capacity_purchase.potion_capacity,
                capacity_purchase.ml_capacity,
                time_id
            )
            
            logger.info(
                f"Successfully upgraded capacity - potion units: {capacity_purchase.potion_capacity}, "
                f"ml units: {capacity_purchase.ml_capacity}"
            )
            return {"success": True}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to process capacity upgrade: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process capacity upgrade")