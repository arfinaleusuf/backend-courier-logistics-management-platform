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
    created_at = Column(DateTime, default=datetime.now)


class Couriers(Base):
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('users.id'),nullable=False)
    sending_from = Column(String)
    destination = Column(String)
    receiver_name = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    bill = Column(Float)
    is_aproved = Column(Boolean, default=False)
    assigned_rider = Column(Integer, ForeignKey("users.id"),nullable=True, default=None)
    is_completed = Column(Boolean, default=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.now)

class PasswordResetOtp(Base):
    __tablename__ = "password_reset_otp"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp = Column(String,nullable=False)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
