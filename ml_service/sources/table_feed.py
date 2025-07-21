from database import Base, SessionLocal
from table_post import Post
from table_user import User
from sqlalchemy import Column, Integer, String, func, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Feed(Base):
    __tablename__ = "feed_action"
    __table_args__ = {"schema": "public"}
    action = Column(String)
    post_id = Column(Integer, ForeignKey(Post.id), primary_key=True, name="post_id")
    post = relationship("table_post.Post")
    time = Column(DateTime)
    user_id = Column(Integer, ForeignKey(User.id), primary_key=True, name="user_id")
    user = relationship("table_user.User")
