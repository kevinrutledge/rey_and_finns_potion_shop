import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from src.api import auth
from src import database as db
from src.utilities import BarrelManager, TimeManager

logger = logging.getLogger('test_barrels.barrels')
#logger = logging.getLogger(__name__)

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
        engine = db.get_engine()
        with engine.begin() as conn:
            # Convert Pydantic models to dicts
            catalog_dicts = [barrel.dict() for barrel in wholesale_catalog]

            # Log wholesale catalog
            logger.debug(f"Wholesale catalog: {catalog_dicts}")
            
            # Get current time
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            
            # Record catalog first
            visit_id = BarrelManager.record_catalog(
                conn, 
                catalog_dicts,
                time_id
            )
            
            logger.debug(f"Recorded wholesale catalog with visit_id: {visit_id}")
            
            # Plan purchases
            purchases = BarrelManager.plan_barrel_purchases(
                conn,
                catalog_dicts,
                time_id
            )
            
            return [
                BarrelPurchase(sku=p['sku'], quantity=p['quantity']) 
                for p in purchases
            ]
            
    except Exception as e:
        logger.error(f"Purchase planning failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to plan purchases"
        )

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: List[Barrel], order_id: int):
    """Process delivery of barrels with strategy constraints."""
    try:
        engine = db.get_engine()
        with engine.begin() as conn:
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

            # Process barrels in batch
            BarrelManager.process_barrel_purchases(
                conn,
                barrel_dicts,
                time_id,
                visit_id,
                order_id
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