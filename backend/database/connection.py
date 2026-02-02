import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from environment
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'bsk')

# Construct DATABASE_URL
# Priority: Use DATABASE_URL if explicitly set, otherwise construct from components
if os.getenv('DATABASE_URL'):
    DATABASE_URL = os.getenv('DATABASE_URL')
else:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connection pool settings from environment
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '20'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '40'))
ECHO_SQL = os.getenv('ECHO_SQL', 'false').lower() == 'true'

engine = create_engine(
    DATABASE_URL, 
    pool_size=POOL_SIZE, 
    max_overflow=MAX_OVERFLOW,
    echo=ECHO_SQL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()  # Rollback on error to prevent stuck transactions
        raise
    finally:
        db.close()
