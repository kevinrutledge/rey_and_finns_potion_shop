import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api import auth
from src import database as db
from src.utilities import LedgerManager

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
                    TRUNCATE TABLE active_strategy CASCADE;
                    TRUNCATE TABLE current_game_time CASCADE;
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

            # Insert initial gold ledger entry
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT time_id
                    FROM game_time
                    ORDER BY time_id ASC
                    LIMIT 1
                """)
            ).scalar_one()

            LedgerManager.create_ledger_entry(
                conn=conn,
                time_id=time_id,
                entry_type='ADMIN_CHANGE',
                gold_change=100  # Starting gold
            )

            # Insert initial active_strategy as PREMIUM
            premium_strategy_id = conn.execute(
                sqlalchemy.text("""
                    SELECT strategy_id FROM strategies WHERE name = 'PREMIUM'
                """)
            ).scalar_one()

            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO active_strategy (strategy_id, game_time_id)
                    VALUES (:strategy_id, :game_time_id)
                """),
                {
                    "strategy_id": premium_strategy_id,
                    "game_time_id": time_id
                }
            )

            logger.info("Successfully reset game state to initial values")
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to reset game state: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset game state")