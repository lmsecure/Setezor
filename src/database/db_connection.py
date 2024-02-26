from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import OperationalError
from database.models import Base, Pivot
import logging


class DBConnection:
    """класс подключения к базе
    """    
    def __init__(self, db_path: str, create_tabels: bool=True):
        """метод инициализации подключения к базе данных (sqlite)

        Args:
            db_path (str): путь до базы
            create_tabels (bool, optional): создать таблицы. по умолчанию создаются
        """        
        self.engine = create_engine(f'sqlite:///{db_path}?check_same_thread=False')
        if create_tabels:
            try:
                Base.metadata.create_all(self.engine)
            except OperationalError as e:
                if e.args != ('(sqlite3.OperationalError) table pivot already exists',):
                    raise
                
        Base.metadata.reflect(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    def create_session(self):
        """метод создания сессии коннекта к базе

        Returns:
            _type_: _description_
        """
        return scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))
