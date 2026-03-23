from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    file_url = Column(String)
    owner_username = Column(String)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    nickname = Column(String, default="")
    avatar = Column(String, default="")
    created_at = Column(DateTime, server_default=func.now())