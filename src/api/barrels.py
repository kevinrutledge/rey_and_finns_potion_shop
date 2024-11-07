import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from src.api import auth
from src import database as db
from src.utilities import BarrelManager, TimeManager

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

class BarrelPurchase(BaseModel):
    sku: str
    quantity: int

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: List[Barrel]):
    """Plan barrel purchases based on future needs and strategy constraints."""
    try:
        with db.engine.begin() as conn:
            # Convert Pydantic models to dicts
            catalog_dicts = [barrel.dict() for barrel in wholesale_catalog]

            # Log the start of planning with catalog
            logger.debug(f"Started purchase planning for {len(wholesale_catalog)} barrels: {catalog_dicts}")
            
            # Get current time and state
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            state = conn.execute(sqlalchemy.text(
                "SELECT * FROM current_state"
            )).mappings().one()
            
            # Log current state
            logger.debug(
                f"Current state - gold: {state['gold']}, "
                f"available capacity: {state['max_ml'] - state['total_ml']}"
            )
            
            # Convert Pydantic models to dicts
            catalog_dicts = [barrel.dict() for barrel in wholesale_catalog]
            
            # Record catalog
            visit_id = BarrelManager.record_catalog(
                conn, 
                catalog_dicts,
                time_id
            )
            
            # Get barrel time block
            block = conn.execute(sqlalchemy.text("""
                SELECT tb.block_id, tb.name as block_name
                FROM game_time gt
                JOIN time_blocks tb 
                    ON gt.in_game_hour BETWEEN tb.start_hour AND tb.end_hour
                WHERE gt.time_id = (
                    SELECT barrel_time_id
                    FROM game_time
                    WHERE time_id = :time_id
                )
            """), {"time_id": time_id}).mappings().one()
            
            # Calculate needs with buffers
            color_needs = BarrelManager.get_color_needs(conn, block)
            logger.debug(f"Calculated color needs: {color_needs}")
            
            # Plan and validate purchases
            purchases = BarrelManager.plan_barrel_purchases(
                conn,
                catalog_dicts,
                color_needs,
                state['gold'],
                state['max_ml'] - state['total_ml'],
                block['block_id']
            )
            
            if purchases:
                logger.info(
                    f"Planned purchases - skus: "
                    f"{[BarrelPurchase(sku=p['sku'], quantity=p['quantity']) for p in purchases]}")
            else:
                logger.debug("No barrel purchases needed")
            
            return [
                BarrelPurchase(sku=p['sku'], quantity=p['quantity']) 
                for p in purchases
            ]
            
    except Exception as e:
        logger.error(f"Purchase planning failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to plan purchases")

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: List[Barrel], order_id: int):
    """Process delivery of barrels with strategy constraints."""
    try:
        with db.engine.begin() as conn:
            # Convert Pydantic models to dicts
            barrel_dicts = [barrel.dict() for barrel in barrels_delivered]

            logger.debug(f"Processing barrel delivery order {order_id}: {barrel_dicts}")
            
            # Get current time and state
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            state = conn.execute(sqlalchemy.text(
                "SELECT * FROM current_state"
            )).mappings().one()
            
            # Validate total costs and capacity
            total_cost = sum(b['price'] * b['quantity'] for b in barrel_dicts)
            total_ml = sum(b['ml_per_barrel'] * b['quantity'] for b in barrel_dicts)
            
            logger.debug(
                f"Validating delivery - cost: {total_cost}, "
                f"ml: {total_ml}, gold: {state['gold']}"
            )
            
            if state['gold'] < total_cost:
                logger.error(
                    f"Insufficient gold for delivery - "
                    f"required: {total_cost}, available: {state['gold']}"
                )
                raise HTTPException(status_code=400, detail="Insufficient gold")
                
            available_capacity = state['max_ml'] - state['total_ml']
            BarrelManager.validate_purchase_constraints(
                conn, 
                barrel_dicts,
                available_capacity
            )
            
            # Get latest visit
            visit_id = conn.execute(sqlalchemy.text("""
                SELECT visit_id 
                FROM barrel_visits 
                ORDER BY created_at DESC 
                LIMIT 1
            """)).scalar_one()
            
            # Process each barrel
            for barrel_dict in barrel_dicts:
                barrel_id = conn.execute(sqlalchemy.text("""
                    SELECT barrel_id 
                    FROM barrel_details 
                    WHERE visit_id = :visit_id AND sku = :sku
                """), {
                    "visit_id": visit_id,
                    "sku": barrel_dict['sku']
                }).scalar_one()
                
                BarrelManager.process_barrel_purchase(
                    conn,
                    barrel_dict,
                    barrel_id,
                    time_id,
                    visit_id
                )
            
            logger.info(
                f"Completed delivery order {order_id} - "
                f"total cost: {total_cost}, total ml: {total_ml}"
            )
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process barrel delivery: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process delivery")