"""
Database connection setup (Postgres/MySQL via SQLAlchemy).

Ek DATABASE_URL environment variable set karo .env me, jaise:
    Postgres: DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/aivoa
    MySQL:    DATABASE_URL=mysql+pymysql://user:password@localhost:3306/aivoa

Local testing ke liye agar Postgres/MySQL abhi setup nahi hai, SQLite bhi chalega:
    DATABASE_URL=sqlite:///./aivoa.db
(SQLite sirf dev/testing ke liye — final submission me Postgres/MySQL use karna,
 jaisa assignment me mandatory hai.)
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aivoa.db")

# SQLite needs this extra connect_arg; Postgres/MySQL don't.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
