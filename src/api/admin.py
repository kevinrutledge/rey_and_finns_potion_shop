import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api import auth
from src import database as db
from src.utilities import TimeManager, LedgerManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """Reset the game state to initial values."""
    try:
        with db.engine.begin() as conn:
            # Get current time
            current_time = TimeManager.get_current_time(conn)
            logger.debug("Starting game state reset")
            
            # Clear current state
            conn.execute(sqlalchemy.text("""
                TRUNCATE TABLE active_strategy CASCADE;
                TRUNCATE TABLE current_game_time CASCADE;
                TRUNCATE TABLE ledger_entries CASCADE;
            """))
            
            # Reset potion quantities
            conn.execute(sqlalchemy.text(
                "UPDATE potions SET current_quantity = 0"
            ))
            
            # Record current time
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO current_game_time (
                        game_time_id, current_day, current_hour
                    )
                    VALUES (:time_id, :day, :hour)
                """),
                {
                    "time_id": current_time['time_id'],
                    "day": current_time['day'],
                    "hour": current_time['hour']
                }
            )
            
            # Create initial gold ledger entry
            LedgerManager.create_admin_entry(conn, current_time['time_id'])
            
            # Reset to PREMIUM strategy
            premium_id = conn.execute(
                sqlalchemy.text(
                    "SELECT strategy_id FROM strategies WHERE name = 'PREMIUM'"
                )
            ).scalar_one()
            
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO active_strategy (strategy_id, game_time_id)
                    VALUES (:strategy_id, :game_time_id)
                """),
                {
                    "strategy_id": premium_id,
                    "game_time_id": current_time['time_id']
                }
            )
            
            logger.info("Successfully reset game state")
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to reset game state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset game state")