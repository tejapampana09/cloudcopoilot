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
    chunks = relationship("RepositoryChunk", back_populates="analysis", cascade="all, delete-orphan")

class Generation(Base):
    __tablename__ = "generations"
    
    generation_id = Column(String(255), primary_key=True, index=True)
    data = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="generations")

class RepositoryChunk(Base):
    __tablename__ = "repository_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), ForeignKey("analyses.task_id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON-serialized array of floats
    created_at = Column(DateTime, server_default=func.now())
    
    analysis = relationship("Analysis", back_populates="chunks")

