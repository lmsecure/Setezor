from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper

Base = declarative_base()


class MacVendor(Base):
    __tablename__ = 'mac_vendor'

    id: int = Column(Integer, primary_key=True)
    mac_prefix: str = Column(String, nullable=False)
    vendor: str = Column(String)
    address: str = Column(String)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in class_mapper(self.__class__).columns}

    def __repr__(self):
        return f"<MacVendor(id={self.id}, mac_prefix={self.mac_prefix}, vendor={self.vendor})>"