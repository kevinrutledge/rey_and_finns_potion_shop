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
    logger.debug(f"Processing wholesale catalog - available barrels: {len(wholesale_catalog)}")
    
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
            
            logger.debug(f"Planning constraints - available gold: {state['gold']}, "
                        f"available capacity: {state['max_ml'] - state['total_ml']}")
            
            purchases = BarrelManager.plan_purchases(
                needs,
                wholesale_catalog_dict,
                state
            )
            
            if purchases:
                logger.debug(f"Purchase plan - barrels: {[(p['sku'], p['quantity']) for p in purchases]}")
            else:
                logger.debug("Purchase plan - no barrels needed")

            return purchases
            
    except Exception as e:
        logger.error(f"Failed to plan purchases: {e}")
        raise HTTPException(status_code=500, detail="Failed to plan purchases")

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """Process delivery of barrels."""
    barrels_delivered_dict = [dict(barrel) for barrel in barrels_delivered]
    logger.debug(f"Processing barrel delivery - order: {order_id}, count: {len(barrels_delivered)}")
    
    try:
        with db.engine.begin() as conn:
            state = StateValidator.get_current_state(conn)
            total_cost = sum(b.price * b.quantity for b in barrels_delivered)
            total_ml = sum(b.ml_per_barrel * b.quantity for b in barrels_delivered)
            
            logger.debug(f"Delivery requirements - cost: {total_cost}, ml: {total_ml}")
            
            if state['gold'] < total_cost:
                logger.debug(f"Insufficient gold - required: {total_cost}, available: {state['gold']}")
                raise HTTPException(status_code=400, detail="Insufficient gold")
                
            if state['total_ml'] + total_ml > state['max_ml']:
                logger.debug(
                    f"Insufficient ml capacity - current: {state['total_ml']}, "
                    f"required: {total_ml}, max: {state['max_ml']}"
                )
                raise HTTPException(status_code=400, detail="Insufficient ml capacity")
            
            time_id = conn.execute(
                sqlalchemy.text("SELECT time_id FROM game_time ORDER BY created_at DESC LIMIT 1")
            ).scalar_one()
            
            visit_id = conn.execute(
                sqlalchemy.text("SELECT visit_id FROM barrel_visits ORDER BY created_at DESC LIMIT 1")
            ).scalar_one()
            
            for barrel in barrels_delivered:
                barrel_id = conn.execute(
                    sqlalchemy.text("""
                        SELECT barrel_id 
                        FROM barrel_details 
                        WHERE visit_id = :visit_id 
                        AND sku = :sku
                    """),
                    {"visit_id": visit_id, "sku": barrel.sku}
                ).scalar_one()
                
                BarrelManager.process_barrel_purchase(
                    conn,
                    dict(barrel),
                    barrel_id,
                    time_id,
                    visit_id
                )
            
            logger.info(f"Successfully processed barrel delivery for order {order_id}")
            return {"success": True}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to process barrel delivery: {e}")
        raise HTTPException(status_code=500, detail="Failed to process delivery")