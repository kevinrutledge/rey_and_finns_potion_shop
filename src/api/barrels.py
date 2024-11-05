import sqlalchemy
import logging
import json
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
    wholesale_catalog_dict = [dict(barrel) for barrel in wholesale_catalog]
    logger.debug(f"Processing wholesale catalog with {len(wholesale_catalog)} items")
    logger.debug(wholesale_catalog_dict)
    
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

            visit_id = BarrelManager.record_wholesale_catalog(
                conn, 
                wholesale_catalog_dict,
                time_id
            )
            
            needs = [dict(need) for need in BarrelManager.get_ml_needs(conn)]
            state = StateValidator.get_current_state(conn)
            
            purchases = BarrelManager.plan_purchases(
                needs,
                wholesale_catalog_dict,
                state
            )
            
            logger.debug(f"Generated purchase plan for {len(purchases)} barrels")
            logger.debug(purchases)

            return purchases
            
    except Exception as e:
        logger.error(f"Failed to plan purchases: {e}")
        raise HTTPException(status_code=500, detail="Failed to plan purchases")

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """Process delivery of barrels."""
    barrels_delivered_dict = [dict(barrel) for barrel in barrels_delivered]
    logger.debug(f"Processing delivery of {len(barrels_delivered)} barrels")
    logger.debug(barrels_delivered_dict)
    
    try:
        with db.engine.begin() as conn:
            state = StateValidator.get_current_state(conn)
            total_cost = sum(b.price * b.quantity for b in barrels_delivered)
            total_ml = sum(b.ml_per_barrel * b.quantity for b in barrels_delivered)
            
            if state['gold'] < total_cost:
                raise HTTPException(status_code=400, detail="Insufficient gold")
                
            if state['total_ml'] + total_ml > state['max_ml']:
                raise HTTPException(status_code=400, detail="Insufficient ML capacity")
            
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            visit_id = conn.execute(
                sqlalchemy.text("""
                    SELECT visit_id 
                    FROM barrel_visits 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            for barrel in barrels_delivered:
                barrel_id = conn.execute(
                    sqlalchemy.text("""
                        SELECT barrel_id 
                        FROM barrel_details 
                        WHERE visit_id = :visit_id 
                        AND sku = :sku
                    """),
                    {
                        "visit_id": visit_id,
                        "sku": barrel.sku
                    }
                ).scalar_one()
                
                BarrelManager.process_barrel_purchase(
                    conn,
                    dict(barrel),
                    barrel_id,
                    time_id,
                    visit_id
                )
            
            logger.info(f"Successfully processed delivery of {len(barrels_delivered)} barrels")
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process barrel delivery: {e}")
        raise HTTPException(status_code=500, detail="Failed to process delivery")