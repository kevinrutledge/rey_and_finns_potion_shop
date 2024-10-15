import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth

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
    """
    Share current time and record it in database.
    """
    logger.info("Endpoint /info/current_time called.")
    logger.debug(f"Received timestamp: current day: {timestamp.day}, current hour: timestamp.hour")

    try:
        with db.engine.begin() as connection:
            # Prepare SQL query to insert in-game time
            insert_query = """
                INSERT INTO in_game_time (in_game_day, in_game_hour)
                VALUES (:in_game_day, :in_game_hour)
                RETURNING time_id;
            """

            # Execute query with provided timestamp data
            result = connection.execute(
                sqlalchemy.text(insert_query),
                {
                    "in_game_day": timestamp.day,
                    "in_game_hour": timestamp.hour
                }
            )
            # Fetch generated time_id
            time_id = result.scalar()
            logger.info(f"Inserted in_game_time record with time_id: {time_id}")

    except Exception as e:
        logger.exception(f"Exception occurred in post_time: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    # Return successful response
    logger.debug("Returning response: OK")
    return {"success": True}