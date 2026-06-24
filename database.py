import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uptime.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_session():
    return SessionLocal()
