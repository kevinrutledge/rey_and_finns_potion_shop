import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.utilities import InventoryManager, TimeManager

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
            logger.debug(f"Retrieved inventory state - gold: {state['gold']}")
            
            return {
                "number_of_potions": state['total_potions'],
                "ml_in_barrels": state['total_ml'],
                "gold": state['gold']
            }
            
    except Exception as e:
        logger.error(f"Failed to get inventory state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get inventory"
        )

@router.post("/plan")
def get_capacity_plan():
    """Get capacity purchase plan. Called once per day."""
    try:
        with db.engine.begin() as conn:
            state = InventoryManager.get_inventory_state(conn)
            plan = InventoryManager.get_capacity_purchase_plan(conn, state)
            logger.debug(f"Generated capacity plan: {plan}")

            return CapacityPurchase(
                potion_capacity=plan['potion_capacity'],
                ml_capacity=plan['ml_capacity']
            )
            
    except Exception as e:
        logger.error(f"Failed to get capacity plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to plan capacity"
        )

@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """Process capacity purchase delivery. Called once per day."""
    try:
        with db.engine.begin() as conn:
            current_time = TimeManager.get_current_time(conn)
            
            logger.debug(
                f"Processing capacity upgrade delivery - "
                f"order: {order_id}, "
                f"potion: {capacity_purchase.potion_capacity}, "
                f"ml: {capacity_purchase.ml_capacity}"
            )
            
            InventoryManager.process_capacity_upgrade(
                conn,
                capacity_purchase.potion_capacity,
                capacity_purchase.ml_capacity,
                current_time['time_id']
            )
            
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process capacity upgrade: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process upgrade"
        )
