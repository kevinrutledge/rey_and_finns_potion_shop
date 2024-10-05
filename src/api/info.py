import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api import auth
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

# Constants for in-game time calculations
EPOCH = datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc)
TICK_INTERVAL = timedelta(hours=2)  # Every 2 real hours is 1 in-game hour
HOURS_PER_DAY = 12  # 12 in-game hours per day
DAYS_PER_WEEK = 7
IN_GAME_DAYS = [
    "Edgeday",
    "Soulday",
    "Aracanaday",
    "Hearthday",
    "Crownday",
    "Blesseday",
    "Bloomday"
]

@router.get("/current_time", summary="Get Current In-Game Time", description="Returns the current in-game day and hour.")
def get_current_time():
    """
    Share current in-game time.
    """
    logger.info("Starting get_current_time endpoint.")
    
    try:
        # Get current real-world time in UTC
        now = datetime.now(timezone.utc)
        logger.debug(f"Current real-world time (UTC): {now}")
        
        # Calculate total ticks since epoch
        total_ticks = int((now - EPOCH) / TICK_INTERVAL)
        logger.debug(f"Total ticks since epoch: {total_ticks}")
        
        # Calculate in-game hour (1 to 12)
        in_game_hour = (total_ticks % HOURS_PER_DAY) - 2
        logger.debug(f"In-game hour: {in_game_hour}")
        
        # Calculate in-game day index and name
        in_game_day_index = (total_ticks // HOURS_PER_DAY) % DAYS_PER_WEEK
        in_game_day = IN_GAME_DAYS[in_game_day_index]
        logger.debug(f"In-game day index: {in_game_day_index}, In-game day: {in_game_day}")
        
        # Prepare response
        response = {
            "day": in_game_day,
            "hour": in_game_hour
        }
        logger.info(f"Returning in-game time: {response}")
        return response
    
    except Exception as e:
        # Log exception with traceback
        logger.exception(f"Error in get_current_time: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")