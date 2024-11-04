import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api import auth
from src import database as db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    try:
        with db.engine.begin() as conn:
            # Clear core game state tables
            conn.execute(
                sqlalchemy.text("""
                    TRUNCATE TABLE game_time CASCADE;
                    TRUNCATE TABLE barrel_purchases CASCADE;
                    TRUNCATE TABLE ledger_entries CASCADE;
                """)
            )
            
            # Reset all potion quantities to 0
            conn.execute(
                sqlalchemy.text("""
                    UPDATE potions
                    SET current_quantity = 0
                """)
            )
            
            logger.info("Successfully reset game state to initial values")
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to reset game state: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset game state")