import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from src.api import auth
from src import database as db
from src.utilities import BottlerManager, TimeManager

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
            state = conn.execute(sqlalchemy.text("SELECT * FROM current_state")).mappings().one()
            logger.debug(
                f"Current state - potions: {state['total_potions']}/{state['max_potions']}, "
                f"ml: r{state['red_ml']} g{state['green_ml']} b{state['blue_ml']} d{state['dark_ml']}"
            )
            
            # Get priorities and calculate possible potions
            priorities = BottlerManager.get_bottling_priorities(conn)
            available_ml = {
                'red_ml': state['red_ml'],
                'green_ml': state['green_ml'],
                'blue_ml': state['blue_ml'],
                'dark_ml': state['dark_ml']
            }
            available_capacity = state['max_potions'] - state['total_potions']
            
            bottling_plan = BottlerManager.calculate_possible_potions(
                priorities,
                available_ml,
                available_capacity
            )
            
            logger.debug(f"Generated bottling plan for {len(bottling_plan)} potion types")

            return [
                PotionInventory(potion_type=b['potion_type'], quantity=b['quantity']) 
                for b in bottling_plan
            ]
            
    except Exception as e:
        logger.error(f"Failed to create bottling plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create bottling plan")

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: List[PotionInventory], order_id: int):
    """Process potion bottling."""
    try:
        with db.engine.begin() as conn:
            potions_delivered_dicts = [barrel.dict() for barrel in potions_delivered]

            state = conn.execute(sqlalchemy.text("SELECT * FROM current_state")).mappings().one()
            logger.debug(
                f"Processing bottling order {order_id} "
                f"with {len(potions_delivered)} potion types: {potions_delivered_dicts}"
            )
            
            # Validate resources
            total_potions = sum(p.quantity for p in potions_delivered)
            ml_needs = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            
            for potion in potions_delivered:
                ml_needs['red_ml'] += potion.potion_type[0] * potion.quantity
                ml_needs['green_ml'] += potion.potion_type[1] * potion.quantity
                ml_needs['blue_ml'] += potion.potion_type[2] * potion.quantity
                ml_needs['dark_ml'] += potion.potion_type[3] * potion.quantity
            
            if state['total_potions'] + total_potions > state['max_potions']:
                raise HTTPException(status_code=400, detail="Insufficient potion capacity")
            
            if (state['red_ml'] < ml_needs['red_ml'] or
                state['green_ml'] < ml_needs['green_ml'] or
                state['blue_ml'] < ml_needs['blue_ml'] or
                state['dark_ml'] < ml_needs['dark_ml']):
                raise HTTPException(status_code=400, detail="Insufficient ml")
            
            # Process bottling
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            
            for potion in potions_delivered:
                BottlerManager.process_bottling(conn, potion.dict(), time_id)
            
            logger.info(f"Successfully bottled {total_potions} potions for order {order_id}")
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process bottling: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process bottling")