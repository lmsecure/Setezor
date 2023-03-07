from sqlalchemy.orm.session import Session
from sqlalchemy.sql import or_
from database.models import L3Link, IP
from .base_queries import BaseQueries
from .ip_queries import IPQueries
from copy import deepcopy


class L3LinkQueries(BaseQueries):
    """Класс запросов к таблице L3 связей
    """    
    
    model = L3Link

    def __init__(self, ip: IPQueries, session_maker: Session):
        """_summary_

        Args:
            ip (IPQueries): объект запросов к таблице с IP адресами
            session_maker (Session): генератор сессий
        """        
        super().__init__(session_maker)
        self.ip = ip
        
    @BaseQueries.session_provide
    def create(self, session: Session, child_ip: str, parent_ip: str, child_mac: str=None, parent_mac: str=None,
                         child_name: str=None, parent_name: str=None, start_ip: str=None):
        """Метод создания объекта связи на l3 уровне.
        При этом, если добавляем более подробный путь, менее подробный удаляется

        Args:
            session (Session): сессия коннекта к базе
            child_ip (str): ip дочернего узла
            parent_ip (str): ip родительского узла
            child_mac (str, optional): mac дочернего узла. Defaults to None.
            parent_mac (str, optional): mac родительского узла. Defaults to None.
            child_name (str, optional): доменное имя дочернего узла. Defaults to None.
            parent_name (str, optional): доменное имя дочернего узла. Defaults to None.
            start_ip (str, optional): ip адрес узла, с которого производилось сканирование (запущенно приложение) . Defaults to None.

        Returns:
            _type_: объект связи на l3 уровне 
        """
        child_obj = self.ip.get_or_create(session=session, ip=child_ip, mac=child_mac, domain_name=child_name)
        parent_obj = self.ip.get_or_create(session=session, ip=parent_ip, mac=parent_mac, domain_name=parent_name)
        if start_ip == child_ip or child_ip == parent_ip:
            return None
        start_obj = session.query(self.ip.model).filter(self.ip.model.ip == start_ip).first() if start_ip else None
        """ Проверим существует ли более короткий маршрут
        если существует, то удалим его
        """
        if start_obj and parent_ip != start_ip:
            exist_short_link = session.query(self.model).filter(self.model.child_ip == child_obj.id, self.model.parent_ip == start_obj.id).first()
            if exist_short_link:
                self.logger.debug(f'Delete more short "{self.model.__name__}" with kwargs',  {'child_ip': exist_short_link._child_ip.ip, 'parent_ip': exist_short_link._parent_ip.ip})
                session.delete(exist_short_link)
        long_way_check = self.check_existing_long_way(session=session, target_obj=child_obj, start_obj=(start_obj if start_obj else parent_obj))
        if long_way_check:
            return None
        link_obj = self.model(child_ip=child_obj.id, parent_ip=parent_obj.id)
        session.add(link_obj)
        session.flush()
        self.logger.debug(f'Created "{self.model.__name__}" with kwargs', {'child_ip': link_obj._child_ip.ip, 'child_mac': link_obj._child_ip._mac.mac, 'child_name': link_obj._child_ip.domain_name, 
                          'parent_ip': link_obj._parent_ip.ip, 'parent_mac': link_obj._parent_ip._mac.mac, 'parent_name':link_obj._parent_ip.domain_name})
        return link_obj
    
    @BaseQueries.session_provide
    def check_existing_long_way(self, session: Session, target_obj: IP, start_obj: IP):
        
        def recursive_search(ses: Session, tar_obj: IP, parent_obj: IP, known_ips: list):
            if self.check_exists(session=ses, query=ses.query(self.model).filter(self.model.__table__.c.get('parent_ip') == parent_obj.id, self.model.__table__.c.get('child_ip') == tar_obj.id)):
                return True
            result = [False]
            for link in ses.query(self.model).filter(self.model.parent_ip == parent_obj.id).all():
                if link._child_ip.ip not in known_ips:
                    result.append(recursive_search(ses=ses, tar_obj=tar_obj, parent_obj=link._child_ip, known_ips=deepcopy(known_ips + [parent_obj.ip])))
            return any(result)
        
        res = None
        if not self.check_exists(session=session, query= session.query(self.model).filter(or_(self.model.child_ip == target_obj.id, self.model.parent_ip == target_obj.id))):
            return False
        res = recursive_search(ses=session, tar_obj=target_obj, parent_obj=start_obj, known_ips=[])
        return res
    
    @BaseQueries.session_provide
    def get_or_create(self, session: Session, child_ip: str, parent_ip: str, child_mac: str=None, parent_mac: str=None,
                      child_name: str=None, parent_name: str=None, start_ip: str=None, to_update: bool=False, **kwargs):
        child_obj = session.query(self.ip.model).filter(self.ip.model.ip == child_ip).first()
        parent_obj = session.query(self.ip.model).filter(self.ip.model.ip == parent_ip).first()
        if child_obj and parent_obj:
            exist = session.query(self.model).filter(self.model.child_ip == child_obj.id, 
                                                     self.model.parent_ip == parent_obj.id).first()
            if exist:
                
                if to_update:
                    self.update_by_id(session=session, id=exist.id, to_update={'child_ip': child_obj.id, 'parent_ip': parent_obj.id})
                self.logger.debug('Get "%s" with kwargs %s', self.model.__name__, {'child_ip': child_ip, 'parent_ip': parent_ip, 'child_mac': child_mac, 
                                                                               'parent_mac': parent_mac, 'child_name': child_name, 'parent_name': parent_name, 
                                                                               'start_ip': start_ip})
                return exist
            
        return self.create(session=session, child_ip=child_ip, child_mac=child_mac, child_name=child_name, 
                            parent_ip=parent_ip, parent_mac=parent_mac, parent_name=parent_name, start_ip=start_ip)

    @BaseQueries.session_provide
    def get_vis_edges(self, session: Session) -> dict:
        """метод генерации ребер для построения топологии сети на веб-морде

        Args:
            session (Session): сессия коннекта к базе

        Returns:
            dict: словарь ребер
        """        
        return [edge.to_vis_edge() for edge in session.query(self.model).all()]
    
    @BaseQueries.session_provide
    def update_by_id(self, session: Session, id: int, to_update: dict, merge_mode='replace'):
        l3link_obj = session.query(self.model).filter(self.model.id == id).update(to_update)
        session.flush()
        
    def get_headers(self) -> list:
        return [{'name': 'id', 'type': '', 'required': False},
                {'name': 'child_ip', 'type': '', 'required': True},
                {'name': 'parent_ip', 'type': '', 'required': True}]
        
    def foreign_key_order(self, field_name: str):
        if field_name == 'child_ip':
            return self.ip.model.ip, self.model._child_ip
        elif field_name == 'parent_ip':
            return self.ip.model.ip, self.model._parent_ip