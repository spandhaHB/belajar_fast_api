from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Get database configuration from environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")  # Default MySQL port

# MySQL connection string with explicit port
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    """
    Check if the database connection is successful
    """
    max_retries = 5
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Try to connect to the database
            with engine.connect() as connection:
                # Execute a simple query to verify connection
                connection.execute(text("SELECT 1"))
                print("\033[92m✓ Database connection successful!\033[0m")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"\033[93m! Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...\033[0m")
                print(f"Error: {str(e)}")
                time.sleep(retry_delay)
            else:
                print("\033[91m✗ Failed to connect to database after multiple attempts\033[0m")
                print(f"Final error: {str(e)}")
                return False