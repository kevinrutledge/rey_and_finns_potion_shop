import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from src.api import auth
from src import database as db
from src.utilities import BarrelManager, StateValidator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: List[int]
    price: int
    quantity: int

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Plan barrel purchases based on future needs."""
    logger.debug(f"Processing wholesale catalog with {len(wholesale_catalog)} items")
    
    try:
        with db.engine.begin() as conn:
            # Get future needs and current state
            needs = BarrelManager.get_ml_needs(conn)
            state = StateValidator.get_current_state(conn)
            
            # Plan purchases
            purchases = BarrelManager.plan_purchases(
                needs,
                [b.dict() for b in wholesale_catalog],
                state
            )
            
            logger.info(f"Generated purchase plan for {len(purchases)} barrels")
            return purchases
            
    except Exception as e:
        logger.error(f"Failed to plan purchases: {e}")
        raise HTTPException(status_code=500, detail="Failed to plan purchases")

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """Process delivery of barrels."""
    logger.debug(f"Processing delivery of {len(barrels_delivered)} barrels")
    
    try:
        with db.engine.begin() as conn:
            # Validate resources
            state = StateValidator.get_current_state(conn)
            total_cost = sum(b.price * b.quantity for b in barrels_delivered)
            total_ml = sum(b.ml_per_barrel * b.quantity for b in barrels_delivered)
            
            if state['gold'] < total_cost:
                raise HTTPException(status_code=400, detail="Insufficient gold")
                
            if state['total_ml'] + total_ml > state['max_ml']:
                raise HTTPException(status_code=400, detail="Insufficient ML capacity")
            
            # Get current time
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            # Record visit
            visit_id = conn.execute(
                sqlalchemy.text("""
                    INSERT INTO barrel_visits (
                        time_id,
                        wholesale_catalog
                    )
                    VALUES (:time_id, :catalog)
                    RETURNING visit_id
                """),
                {
                    "time_id": time_id,
                    "catalog": [b.dict() for b in barrels_delivered]
                }
            ).scalar_one()
            
            # Process each barrel
            for barrel in barrels_delivered:
                BarrelManager.process_barrel_delivery(
                    conn,
                    barrel.dict(),
                    time_id,
                    visit_id
                )
            
            logger.info(f"Processed barrel delivery: {total_ml}ml for {total_cost} gold")
            return {"success": True}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to process barrel delivery: {e}")
        raise HTTPException(status_code=500, detail="Failed to process delivery")