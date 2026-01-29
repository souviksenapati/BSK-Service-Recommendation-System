import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default
# Defaulting to the one seen in setup_db.py for now, but user should configure .env
DEFAULT_DB_URL = 'postgresql://postgres:Souvik%402004%23@localhost:5432/bsk'
DATABASE_URL = os.getenv('DATABASE_URL', DEFAULT_DB_URL)

engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)
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
