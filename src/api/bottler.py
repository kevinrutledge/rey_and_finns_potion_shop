import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from src.api import auth
from src import database as db
from src.utilities import BottlerManager, StateValidator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: List[int]
    quantity: int

@router.post("/plan")
def get_bottle_plan():
    """Plan potion bottling based on current resources."""
    try:
        with db.engine.begin() as conn:
            state = StateValidator.get_current_state(conn)
            logger.debug(
                f"Current state - potions: {state['total_potions']}/{state['max_potions']}, "
                f"ml: r{state['red_ml']} g{state['green_ml']} b{state['blue_ml']} d{state['dark_ml']}"
            )
            
            priorities = BottlerManager.get_bottling_priorities(conn)
            
            available_ml = {
                'red_ml': state['red_ml'],
                'green_ml': state['green_ml'],
                'blue_ml': state['blue_ml'],
                'dark_ml': state['dark_ml']
            }
            
            available_capacity = state['max_potions'] - state['total_potions']
            logger.debug(
                f"Planning constraints - available capacity: {available_capacity}, "
                f"available ml: {available_ml}"
            )
            
            bottling_plan = BottlerManager.calculate_possible_potions(
                priorities,
                available_ml,
                available_capacity
            )
            
            logger.debug(f"Generated plan - potions: {bottling_plan}")
            return bottling_plan
            
    except Exception as e:
        logger.error(f"Failed to create bottling plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bottling plan")

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: List[PotionInventory], order_id: int):
    """Process potion bottling."""
    logger.debug(f"Processing request - order: {order_id}, potions: {potions_delivered}")
    
    try:
        with db.engine.begin() as conn:
            state = StateValidator.get_current_state(conn)
            logger.debug(
                f"Initial state - potions: {state['total_potions']}/{state['max_potions']}, "
                f"ml: r{state['red_ml']} g{state['green_ml']} b{state['blue_ml']} d{state['dark_ml']}"
            )
            
            total_potions = sum(p.quantity for p in potions_delivered)
            ml_needs = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            
            for potion in potions_delivered:
                ml_needs['red_ml'] += potion.potion_type[0] * potion.quantity
                ml_needs['green_ml'] += potion.potion_type[1] * potion.quantity
                ml_needs['blue_ml'] += potion.potion_type[2] * potion.quantity
                ml_needs['dark_ml'] += potion.potion_type[3] * potion.quantity
            
            logger.debug(f"Resource requirements - potions: {total_potions}, ml needs: {ml_needs}")
            
            if state['total_potions'] + total_potions > state['max_potions']:
                logger.debug(
                    f"Insufficient capacity - current: {state['total_potions']}, "
                    f"requested: {total_potions}, max: {state['max_potions']}"
                )
                raise HTTPException(status_code=400, detail="Insufficient potion capacity")
            
            if (state['red_ml'] < ml_needs['red_ml'] or
                state['green_ml'] < ml_needs['green_ml'] or
                state['blue_ml'] < ml_needs['blue_ml'] or
                state['dark_ml'] < ml_needs['dark_ml']):
                available_ml = state['max_ml'] - state['total_ml']
                logger.debug(f"Insufficient ml - available: {available_ml}, required: {ml_needs}")
                raise HTTPException(status_code=400, detail="Insufficient ml")
            
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            for potion in potions_delivered:
                BottlerManager.process_bottling(
                    conn,
                    potion.dict(),
                    time_id
                )
            
            logger.info(f"Successfully bottled {total_potions} potions for order {order_id}")
            return {"success": True}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to process bottling: {e}")
        raise HTTPException(status_code=500, detail="Failed to process bottling")