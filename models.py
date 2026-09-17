from database import Base 
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey
from datetime import datetime

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column