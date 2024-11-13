import sqlalchemy
from sqlalchemy import create_engine, event
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timezone
from src.database import get_engine

# SQLite Configuration Functions
def get_test_db_url() -> str:
    """Get SQLite database URL for testing."""
    return "sqlite:///:memory:"

def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better datetime handling."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def sqlite_timestamp_converter(val):
    """Convert timestamps to timezone-aware datetime objects."""
    if val is None:
        return None
    return datetime.fromtimestamp(float(val), tz=timezone.utc)

def regexp(pattern, value):
    """SQLite REGEXP implementation."""
    try:
        return bool(re.search(pattern, value)) if value is not None else False
    except Exception:
        return False

# SQL Statement Cleaning and Conversion
def clean_sql_statement(statement: str) -> str:
    """Clean individual SQL statement by removing comments and normalizing whitespace."""
    # Remove comments
    statement = re.sub(r'--.*$', '', statement, flags=re.MULTILINE)
    statement = re.sub(r'/\*.*?\*/', '', statement, flags=re.DOTALL)
    
    # Clean up whitespace
    statement = re.sub(r'\s+', ' ', statement.strip())
    
    # Ensure proper statement termination
    if statement and not statement.endswith(';'):
        statement += ';'
    
    return statement

def clean_statement(stmt: str) -> str:
    """Trim leading and trailing whitespace."""
    stmt = stmt.strip()
    if not stmt.endswith(';'):
        stmt += ';'
    return stmt

def convert_postgres_to_sqlite(sql: str) -> str:
    """Convert PostgreSQL syntax to SQLite compatible syntax."""
    # Remove comments
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Define PostgreSQL to SQLite syntax mappings
    replacements = {
        # Data types
        "SERIAL PRIMARY KEY": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "BIGSERIAL PRIMARY KEY": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "SERIAL": "INTEGER",
        "BIGSERIAL": "INTEGER",
        "TIMESTAMPTZ": "TIMESTAMP",
        "BOOLEAN": "INTEGER",
        "INTEGER[]": "TEXT",
        "DECIMAL(10,2)": "REAL",
        "INTERVAL": "TEXT",
        "JSONB": "TEXT",
        "BIGINT": "INTEGER",
        
        # Functions and keywords
        "NOW()": "CURRENT_TIMESTAMP",
        "true": "1",
        "false": "0",
        "GENERATED ALWAYS AS IDENTITY": "",
        " CASCADE": "",
        " USING btree": "",
        "DEFERRABLE": "",
        "INITIALLY DEFERRED": "",
        
        # Timestamp handling
        "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP": 
            "TIMESTAMP NOT NULL DEFAULT (STRFTIME('%s', 'NOW'))",
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP":
            "TIMESTAMP DEFAULT (STRFTIME('%s', 'NOW'))"
    }
    
    # Apply replacements
    for pg_syntax, sqlite_syntax in replacements.items():
        sql = sql.replace(pg_syntax, sqlite_syntax)
    
    # Handle regex patterns
    sql = re.sub(
        r"CHECK\s*\(\s*sku\s*~\s*'\^([^']+)\$'\s*\)",
        r"CHECK (sku REGEXP '\1')",
        sql
    )
    sql = re.sub(
        r"([a-zA-Z_]+)\s*~\s*'([^']+)'",
        r"\1 REGEXP '\2'",
        sql
    )
    
    return sql

# Table Creation Handling
def fix_create_table(match) -> str:
    """Fix CREATE TABLE statement with proper constraint handling."""
    table_name = match.group(1)
    content = match.group(2)
    
    # Parse content handling nested parentheses
    lines = []
    current = []
    paren_count = 0
    
    for char in content:
        if char == '(':
            paren_count += 1
            current.append(char)
        elif char == ')':
            paren_count -= 1
            current.append(char)
        elif char == ',' and paren_count == 0:
            lines.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    if current:
        lines.append(''.join(current).strip())
    
    # Clean and validate lines
    cleaned_lines = []
    has_pk = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if 'PRIMARY KEY AUTOINCREMENT' in line.upper():
            if not has_pk:
                has_pk = True
                if not line.rstrip().endswith(','):
                    line = line.rstrip() + ','
            else:
                line = line.upper().replace('PRIMARY KEY AUTOINCREMENT', 'UNIQUE')
        elif line.upper().startswith('PRIMARY KEY'):
            if has_pk:
                line = line.upper().replace('PRIMARY KEY', 'UNIQUE')
        
        if not line.rstrip().endswith(',') and line != lines[-1]:
            line = line.rstrip() + ','
        
        cleaned_lines.append(line)
    
    return f"CREATE TABLE {table_name} (\n    " + \
           ",\n    ".join(line.rstrip(',') for line in cleaned_lines) + \
           "\n);"

def validate_create_table(statement: str) -> str:
    """Validate and fix CREATE TABLE statement with special case handling."""
    match = re.match(r'CREATE TABLE (\w+)\s*\((.*)\);?$', statement, re.DOTALL)
    if not match:
        return statement
        
    table_name = match.group(1)
    
    # Special case handling for specific tables
    special_cases = {
        'active_strategy': """
            CREATE TABLE active_strategy (
                active_strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INT REFERENCES strategies(strategy_id),
                activated_at TIMESTAMP DEFAULT (STRFTIME('%s', 'NOW')),
                game_time_id INT REFERENCES game_time(time_id),
                UNIQUE(strategy_id, game_time_id)
            );
        """,
        'barrel_details': """
            CREATE TABLE barrel_details (
                barrel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                visit_id INT REFERENCES barrel_visits(visit_id),
                sku TEXT NOT NULL CHECK (
                    sku REGEXP '(SMALL|MEDIUM|LARGE)_[A-Z]+_BARREL'
                ),
                ml_per_barrel INT NOT NULL CHECK (
                    (sku LIKE 'SMALL_%' AND ml_per_barrel = 500) OR
                    (sku LIKE 'MEDIUM_%' AND ml_per_barrel = 2500) OR
                    (sku LIKE 'LARGE_%' AND ml_per_barrel = 10000)
                ),
                potion_type TEXT NOT NULL,
                price INT NOT NULL CHECK (price > 0),
                quantity INT NOT NULL CHECK (quantity > 0),
                color_id INT REFERENCES color_definitions(color_id),
                UNIQUE(visit_id, sku)
            );
        """
    }
    
    if table_name in special_cases:
        return clean_statement(re.sub(r'\s+', ' ', special_cases[table_name].strip()))
    
    return statement

# Statement Processing
def split_sql_statements(sql: str) -> list:
    """Split SQL content into individual statements."""
    # Remove comments
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Split the statements
    statements = []
    current_statement = ''
    for line in sql.split('\n'):
        line = line.strip()
        if not line:
            continue
        current_statement += ' ' + line
        if line.endswith(';'):
            statements.append(current_statement.strip())
            current_statement = ''
    if current_statement.strip():
        statements.append(current_statement.strip())
    return statements

# Database Setup
def setup_test_db(engine):
    """Initialize test database with schema and test data."""
    try:
        # Load SQL files
        project_root = Path(__file__).parent.parent
        schema_path = project_root / "schema.sql"
        insert_path = project_root / "block_potion_priorities_insert.sql"
        
        if not all(p.exists() for p in [schema_path, insert_path]):
            raise FileNotFoundError("Required SQL files not found")
            
        # Read schema
        with open(schema_path) as f:
            schema_sql = f.read()
        
        # Split statements
        all_statements = split_sql_statements(schema_sql)
        
        # Convert statements
        converted_statements = [convert_postgres_to_sqlite(stmt) for stmt in all_statements]
        
        # Categorize statements
        drop_statements = []
        create_statements = []
        other_statements = []
        for stmt in converted_statements:
            if stmt.upper().startswith('DROP TABLE'):
                drop_statements.append(stmt)
            elif stmt.upper().startswith('CREATE TABLE'):
                create_statements.append(stmt)
            else:
                other_statements.append(stmt)
        
        # Reorder drop statements based on dependencies
        table_order = [
            'ledger_entries',
            'cart_items',
            'carts',
            'customers',
            'customer_visits',
            'block_potion_priorities',
            'barrel_purchases',
            'barrel_details',
            'barrel_visits',
            'active_strategy',
            'strategy_time_blocks',
            'strategy_transitions',
            'potions',
            'strategies',
            'current_game_time',
            'game_time',
            'color_definitions',
            'time_blocks',
            'capacity_upgrade_thresholds'
        ]
        
        ordered_drops = []
        for table in table_order:
            pattern = re.compile(rf'DROP TABLE IF EXISTS {table}\b', re.IGNORECASE)
            drop_stmt = next((stmt for stmt in drop_statements if pattern.search(stmt)), None)
            if drop_stmt:
                ordered_drops.append(drop_stmt)
        
        # Add any remaining drops
        remaining_drops = [stmt for stmt in drop_statements if stmt not in ordered_drops]
        ordered_drops.extend(remaining_drops)
        
        # Execute statements
        with engine.begin() as conn:
            # Execute drops
            for statement in ordered_drops:
                try:
                    conn.execute(sqlalchemy.text(statement))
                except Exception as e:
                    print(f"Error executing drop statement: {statement}")
                    raise
            # Execute creates
            for statement in create_statements:
                try:
                    if statement.upper().startswith('CREATE TABLE'):
                        statement = validate_create_table(statement)
                    conn.execute(sqlalchemy.text(statement))
                except Exception as e:
                    print(f"Error executing create statement: {statement}")
                    raise
            # Execute others
            for statement in other_statements:
                try:
                    conn.execute(sqlalchemy.text(statement))
                except Exception as e:
                    print(f"Error executing statement: {statement}")
                    raise
        
        # Process inserts
        with open(insert_path) as f:
            insert_sql = f.read()
        sqlite_inserts = convert_postgres_to_sqlite(insert_sql)
        insert_statements = split_sql_statements(sqlite_inserts)
        with engine.begin() as conn:
            # Check if game_time already has data
            result = conn.execute(sqlalchemy.text(
                "SELECT COUNT(*) FROM game_time"
            )).scalar()
            
            # Only insert if table is empty
            if result == 0:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO game_time
                    (time_id, in_game_day, in_game_hour, bottling_time_id, barrel_time_id)
                    VALUES
                    (1, 'Hearthday', 0, 4, 5),
                    (2, 'Hearthday', 2, 5, 6),
                    (3, 'Hearthday', 4, 6, 7),
                    (4, 'Hearthday', 6, 7, 8),
                    (5, 'Hearthday', 8, 8, 9),
                    (6, 'Hearthday', 10, 9, 10),
                    (7, 'Hearthday', 12, 10, 11),
                    (8, 'Hearthday', 14, 11, 12),
                    (9, 'Hearthday', 16, 12, 13),
                    (10, 'Hearthday', 18, 13, 14),
                    (11, 'Hearthday', 20, 14, 15),
                    (12, 'Hearthday', 22, 15, 16),

                    -- CROWNDAY
                    (13, 'Crownday', 0, 16, 17),
                    (14, 'Crownday', 2, 17, 18),
                    (15, 'Crownday', 4, 18, 19),
                    (16, 'Crownday', 6, 19, 20),
                    (17, 'Crownday', 8, 20, 21),
                    (18, 'Crownday', 10, 21, 22),
                    (19, 'Crownday', 12, 22, 23),
                    (20, 'Crownday', 14, 23, 24),
                    (21, 'Crownday', 16, 24, 25),
                    (22, 'Crownday', 18, 25, 26),
                    (23, 'Crownday', 20, 26, 27),
                    (24, 'Crownday', 22, 27, 28),

                    -- BLESSEDAY
                    (25, 'Blesseday', 0, 28, 29),
                    (26, 'Blesseday', 2, 29, 30),
                    (27, 'Blesseday', 4, 30, 31),
                    (28, 'Blesseday', 6, 31, 32),
                    (29, 'Blesseday', 8, 32, 33),
                    (30, 'Blesseday', 10, 33, 34),
                    (31, 'Blesseday', 12, 34, 35),
                    (32, 'Blesseday', 14, 35, 36),
                    (33, 'Blesseday', 16, 36, 37),
                    (34, 'Blesseday', 18, 37, 38),
                    (35, 'Blesseday', 20, 38, 39),
                    (36, 'Blesseday', 22, 39, 40),

                    -- SOULDAY
                    (37, 'Soulday', 0, 40, 41),
                    (38, 'Soulday', 2, 41, 42),
                    (39, 'Soulday', 4, 42, 43),
                    (40, 'Soulday', 6, 43, 44),
                    (41, 'Soulday', 8, 44, 45),
                    (42, 'Soulday', 10, 45, 46),
                    (43, 'Soulday', 12, 46, 47),
                    (44, 'Soulday', 14, 47, 48),
                    (45, 'Soulday', 16, 48, 49),
                    (46, 'Soulday', 18, 49, 50),
                    (47, 'Soulday', 20, 50, 51),
                    (48, 'Soulday', 22, 51, 52),

                    -- EDGEDAY
                    (49, 'Edgeday', 0, 52, 53),
                    (50, 'Edgeday', 2, 53, 54),
                    (51, 'Edgeday', 4, 54, 55),
                    (52, 'Edgeday', 6, 55, 56),
                    (53, 'Edgeday', 8, 56, 57),
                    (54, 'Edgeday', 10, 57, 58),
                    (55, 'Edgeday', 12, 58, 59),
                    (56, 'Edgeday', 14, 59, 60),
                    (57, 'Edgeday', 16, 60, 61),
                    (58, 'Edgeday', 18, 61, 62),
                    (59, 'Edgeday', 20, 62, 63),
                    (60, 'Edgeday', 22, 63, 64),

                    -- BLOOMDAY
                    (61, 'Bloomday', 0, 64, 65),
                    (62, 'Bloomday', 2, 65, 66),
                    (63, 'Bloomday', 4, 66, 67),
                    (64, 'Bloomday', 6, 67, 68),
                    (65, 'Bloomday', 8, 68, 69),
                    (66, 'Bloomday', 10, 69, 70),
                    (67, 'Bloomday', 12, 70, 71),
                    (68, 'Bloomday', 14, 71, 72),
                    (69, 'Bloomday', 16, 72, 73),
                    (70, 'Bloomday', 18, 73, 74),
                    (71, 'Bloomday', 20, 74, 75),
                    (72, 'Bloomday', 22, 75, 76),

                    -- ARCANADAY
                    (73, 'Arcanaday', 0, 76, 77),
                    (74, 'Arcanaday', 2, 77, 78),
                    (75, 'Arcanaday', 4, 78, 79),
                    (76, 'Arcanaday', 6, 79, 80),
                    (77, 'Arcanaday', 8, 80, 81),
                    (78, 'Arcanaday', 10, 81, 82),
                    (79, 'Arcanaday', 12, 82, 83),
                    (80, 'Arcanaday', 14, 83, 84),
                    (81, 'Arcanaday', 16, 84, 1),
                    (82, 'Arcanaday', 18, 1, 2),
                    (83, 'Arcanaday', 20, 2, 3),
                    (84, 'Arcanaday', 22, 3, 4)
                """))
            
            # Check if current_game_time needs initialization
            result = conn.execute(sqlalchemy.text(
                "SELECT COUNT(*) FROM current_game_time"
            )).scalar()
            
            if result == 0:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO current_game_time (
                        game_time_id, current_day, current_hour
                    )
                    SELECT time_id, in_game_day, in_game_hour
                    FROM game_time 
                    WHERE time_id = 1
                """))

            for statement in insert_statements:
                try:
                    conn.execute(sqlalchemy.text(clean_statement(statement)))
                except Exception as e:
                    print(f"Error executing insert statement: {statement}")
                    raise
    except Exception as e:
        print(f"Database setup failed: {str(e)}")
        raise

def create_test_db():
    """Create and configure SQLite test database."""
    # Register timestamp converter
    sqlite3.register_converter("TIMESTAMP", sqlite_timestamp_converter)
    
    # Create engine with timezone handling
    engine = get_engine()
    
    # Configure pragmas
    event.listen(engine, 'connect', set_sqlite_pragma)
    
    # Initialize database
    setup_test_db(engine)
    return engine