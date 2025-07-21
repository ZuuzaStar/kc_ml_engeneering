from database import Base, SessionLocal
from sqlalchemy import Column, Integer, String, func, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "public"}
    age = Column(Integer)
    city = Column(String)
    country = Column(String)
    exp_group = Column(Integer)
    gender = Column(Integer)
    id = Column(Integer, primary_key=True, name="id")
    os = Column(String)
    source = Column(String)
