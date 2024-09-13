from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import OperationalError, IntegrityError
from .models import Base, NetworkType
import logging


class DBConnection:
    """класс подключения к базе
    """    
    def __init__(self, db_path: str):
        """метод инициализации подключения к базе данных (sqlite)

        Args:
            db_path (str): путь до базы
            create_tabels (bool, optional): создать таблицы. по умолчанию создаются
        """        
        self.engine = create_engine(f'sqlite:///{db_path}?check_same_thread=False',pool_size=0, max_overflow=0)
        Base.metadata.create_all(self.engine)
        Base.metadata.reflect(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        logger = logging.getLogger('sqlalchemy.engine')
        logger.setLevel(logging.INFO)
        with self.Session() as ses:
            for i in NetworkType.to_create_on_start_up():
                try:
                    ses.add(i)
                    ses.commit()
                except IntegrityError:
                    ses.rollback()
        
    def create_session(self):
        """метод создания сессии коннекта к базе

        Returns:
            _type_: _description_
        """
        return scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))
