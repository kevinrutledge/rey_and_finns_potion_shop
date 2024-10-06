import os
import dotenv
from sqlalchemy import create_engine, event
import logging

logger = logging.getLogger(__name__)

def database_connection_url():
    dotenv.load_dotenv()
    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)

# Set session timezone to America/Los_Angeles upon connection
@event.listens_for(engine, "connect")
def set_session_timezone(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SET TIME ZONE 'America/Los_Angeles';")
        dbapi_connection.commit()
        logger.debug("Database session timezone set to 'America/Los_Angeles'.")
    except Exception as e:
        logger.error(f"Failed to set database session timezone: {e}")
        dbapi_connection.rollback()
