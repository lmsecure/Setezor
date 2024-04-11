from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import OperationalError, IntegrityError
from .models import Base, NetworkType
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
                if e.args not in  [('(sqlite3.OperationalError) table pivot already exists',), ('(sqlite3.OperationalError) view pivot already exists',)]:
                    raise
                
        Base.metadata.reflect(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        logger = logging.getLogger('sqlalchemy.engine')
        logger.setLevel(logging.INFO)
        with self.Session() as ses:
            # for tests
            # from network_structures import NetworkStruct
            # from database.models import Network
            # net = NetworkStruct(network='192.168.0.0/16')
            # ses.add(Network(network=str(net.network), start_ip=net.start_ip, broadcast=net.broadcast, mask=net.mask))
            # ses.commit()
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
