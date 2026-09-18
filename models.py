from database import Base 
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey
from datetime import datetime

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    firstname = Column(String)
    lastname = Column(String)
    hash_password = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)

class Couriers(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    Customer_id = Column(Integer, ForeignKey('users.id'),nullable=False)
    sending_from = Column(String)
    destination = Column(String)
    weight = Column(Integer)
    Bill = Column(Integer)
    is_aproved = Column(Boolean, default=False)
    assigned_rider = Column(Integer, ForeignKey("users.id"))
    is_completed = Column(Boolean, default=False)