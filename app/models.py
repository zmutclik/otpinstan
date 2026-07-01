import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(100), nullable=False, default="123456")
    api_key = Column(String(200), nullable=False, default="")
    server = Column(String(10), nullable=False, default="s5")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    orders = relationship("Order", back_populates="user", lazy="dynamic")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    service = Column(String(20), nullable=False)
    country = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    otp_code = Column(String(20), nullable=True)
    otp_updated_at = Column(DateTime, nullable=True)
    client_status = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    username = Column(String(50), ForeignKey("users.username"), nullable=False, index=True)

    user = relationship("User", back_populates="orders")
