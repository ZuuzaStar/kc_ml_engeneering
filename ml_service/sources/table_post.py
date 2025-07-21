from database import Base, SessionLocal
from sqlalchemy import Column, Integer, String, func, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Post(Base):
    __tablename__ = "post"
    __table_args__ = {"schema": "public"}
    id = Column(Integer, primary_key=True, name="id")
    text = Column(String)
    topic = Column(String)
