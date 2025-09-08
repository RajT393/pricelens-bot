# test_db.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL not found in environment variables. Check your .env file.")

print(f"Using DATABASE_URL: {DATABASE_URL}")

# Create engine and test connection
try:
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        print("✅ Database connection successful!", result)
except Exception as e:
    print("❌ Database connection failed:", e)
