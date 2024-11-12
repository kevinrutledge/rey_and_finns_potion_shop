import os
import dotenv
from sqlalchemy import create_engine

def create_engine_with_config(testing: bool = False):
    """Create database engine with appropriate configuration"""
    if testing:
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            isolation_level="SERIALIZABLE",
            pool_pre_ping=True
        )
    else:
        dotenv.load_dotenv()
        postgres_url = os.environ.get("POSTGRES_URI")
        return create_engine(
            postgres_url,
            isolation_level="SERIALIZABLE",
            pool_pre_ping=True
        )

# Global engine
engine = create_engine_with_config(testing=False)

# Switch engine
def use_test_db():
    """Switch to SQLite test database"""
    global engine
    engine = create_engine_with_config(testing=True)
    return engine

def use_prod_db():
    """Switch back to PostgreSQL database"""
    global engine
    engine = create_engine_with_config(testing=False)
    return engine