from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
from config import DBConnectionConfig
from functools import wraps


class DBConnection:
    def __init__(self):
        self.engine = create_engine(f'sqlite:///{DBConnectionConfig.db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_session(self):
        return Session(self.engine)
