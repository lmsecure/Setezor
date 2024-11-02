from sqlalchemy.orm import Session, Query
from sqlalchemy import or_, and_,func, Column
from db.models import MIB

from db.database import get_session



def get(session: Session, column: str, value) -> Query[MIB]:
    return session.query(MIB).where(getattr(MIB, column) == value)

def get_full_oid(name: str, oid_type: type = int) -> str:
    session = get_session()
    digits = []
    words = []
    obj = get(session=session, column="name", value=name).first()
    if obj:
        while True:
            digits.insert(0, str(obj.oid))
            words.insert(0, obj.name)
            if not obj.parent_id:
                break
            obj = get(session=session, column="id", value=obj.parent_id).first()
        if oid_type == int:
            return '.'.join(digits)
        else:
            return '.'.join(words)

def oid2str(oid: str):
    session = get_session()
    oid = map(int, oid.split('.'))
    result = []
    objs = get(session=session, column="parent_id", value=None).all()
    for i in oid:
        id_and_name = [(obj.id, obj.name) for obj in objs if obj.oid == i]
        if id_and_name:
            result.append(id_and_name[0][1])
            objs = get(session=session, column="parent_id", value=id_and_name[0][0]).all()
        else:
            result.append(str(i))
            objs = []
    return '.'.join(result)

def get_brother_oids(name: str) -> list[str]:
    session = get_session()
    obj = get(session=session, column="name", value=name).first()
    if obj:
        brother_objs = get(session=session, column="parent_id", value=obj.parent_id).all()
        return [row.name for row in brother_objs if row.name != name]
    return []

def get_child_oids(name: str) -> list[str]:
    sesion = get_session()
    obj = get(session=sesion, column="name", value=name).first()
    if obj:
        parent_objs = get(session=sesion, column="parent_id", value=obj.id).all()
        return [row.name for row in parent_objs]
    return []