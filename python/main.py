from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from tabulate import tabulate

Base = declarative_base()
engine = create_engine('sqlite:///ip_addresses.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


class IPAddress(Base):
    __tablename__ = 'ip_addresses'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    ip_address = Column(String)


