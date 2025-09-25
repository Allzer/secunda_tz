from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
metadata = MetaData()

Base: DeclarativeMeta = declarative_base(metadata=metadata)

engine = create_engine(DATABASE_URL)
session_maker = sessionmaker(engine, expire_on_commit=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()