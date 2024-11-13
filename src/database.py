import os
import dotenv
from sqlalchemy import create_engine

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        testing = os.environ.get('TESTING') == 'true'

        if testing:
            # Use SQLite test database
            _engine = create_engine(
                "sqlite:///:memory:",
                connect_args={"check_same_thread": False},
                isolation_level="READ COMMITTED",
                pool_pre_ping=True
            )

        else:
            dotenv.load_dotenv()
            postgres_url = os.environ.get("POSTGRES_URI")
            _engine = create_engine(
                postgres_url,
                isolation_level="READ COMMITTED",
                pool_pre_ping=True
            )
            
    return _engine
