import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from src import database as db
from src.utilities import TimeManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """Record current game time and check for strategy transition."""
    try:
        logger.debug(f"Recording time - Day: {timestamp.day}, Hour: {timestamp.hour}")
        
        with db.engine.begin() as conn:
            strategy_changed = TimeManager.record_time(conn, timestamp.day, timestamp.hour)
            
            logger.info(
                f"Time recorded{' - Strategy changed' if strategy_changed else ''}"
            )
            
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to record time: {e}")
        raise HTTPException(status_code=500, detail="Failed to record time")