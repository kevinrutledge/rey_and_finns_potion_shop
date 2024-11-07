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
        if not TimeManager.validate_game_time(timestamp.day, timestamp.hour):
            logger.error(
                f"Invalid game time values - day: {timestamp.day}, hour: {timestamp.hour}"
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid game time values"
            )
        
        with db.engine.begin() as conn:
            TimeManager.record_time(conn, timestamp.day, timestamp.hour)
            logger.info(f"Successfully recorded time - day: {timestamp.day}, hour: {timestamp.hour}")
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record time: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record time")