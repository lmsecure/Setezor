from sqlalchemy.orm.session import Session
from database.models import MAC
from .base_queries import BaseQueries
from .object_queries import ObjectQueries
from mac_vendor_lookup import AsyncMacLookup
import asyncio


class MACQueries(BaseQueries):
    """Класс запросов к таблице MAC адресов
    """    
    
    model = MAC
    
    def __init__(self, objects: ObjectQueries, session_maker: Session):
        """Инициализация объекта запросов

        Args:
            objects (ObjectQueries): объект запросов к таблице с объектами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.object = objects
        
    @BaseQueries.session_provide
    def create(self, session: Session, mac: str, obj=None, **kwargs):
        """Метод создания объекта mac адреса

        Args:
            session (Session): сессия коннекта к базе
            mac (str): mac адрес

        Returns:
            _type_: объект mac адреса
        """
        # try:
        #     loop = asyncio.get_running_loop()
        #     vendor = loop.run_until_complete(AsyncMacLookup().lookup(mac=mac))
        # except:
        vendor = None
        if not obj:
            obj = self.object.create(session=session, **kwargs)
        new_mac_obj = self.model(mac=mac, vendor=vendor, _obj=obj)
        session.add(new_mac_obj)
        session.flush()
        self.logger.debug('Created "%s" object with kwargs %s', self.model.__name__, {'mac': mac})
        mac_obj = new_mac_obj
        return mac_obj
    
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'mac', 'type': '', 'required': True},
                {'name': 'object', 'type': '', 'required': False},
                {'name': 'vendor', 'type': '', 'required': False},]
        
    def foreign_key_order(self, field_name: str):
        if field_name == 'object':
            return self.object.model.object_type, self.model._obj