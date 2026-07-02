from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class Analysis(Base):
    __tablename__ = "analyses"
    
    task_id = Column(String(255), primary_key=True, index=True)
    data = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="analyses")

class Generation(Base):
    __tablename__ = "generations"
    
    generation_id = Column(String(255), primary_key=True, index=True)
    data = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="generations")

class Deployment(Base):
    __tablename__ = "deployments"
    
    deployment_id = Column(String(255), primary_key=True, index=True)
    data = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="deployments")
