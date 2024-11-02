from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base, engine


class MIB(Base):
    __tablename__ = "mib"

    id = Column(Integer, primary_key=True)
    oid = Column(Integer)
    parent_id = Column(Integer)
    name = Column(String(100))

Base.metadata.create_all(bind=engine)
