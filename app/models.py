from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from .database import Base

class Post(Base):
    __tablename__ = "pcbimg"

    id = Column(Integer, primary_key=True, nullable= False)
    title= Column(String,nullable=False)
    path_original = Column(String,nullable=False)
    path = Column(String,nullable=False)
    published =Column(Boolean,server_default='True',nullable=False)
    created_at = Column(TIMESTAMP(timezone= True),nullable=False,server_default=text('now()'))
    deleted=Column(Boolean,server_default='False',nullable=True)
    deleted_at = Column(TIMESTAMP(timezone= True),nullable=True)

    owner_id = Column(Integer,ForeignKey("users.id", ondelete="CASCADE") , nullable= False)
    model_name = Column(String, nullable=True)
    owner = relationship("User")
    
class User(Base):
    __tablename__ ="users"

    id = Column(Integer, primary_key=True, nullable= False)
    email = Column(String,nullable=False,unique=True)
    password =Column(String,nullable=False)  
    created_at = Column(TIMESTAMP(timezone= True),nullable=False,server_default=text('now()'))  
    phone_number = Column(String)