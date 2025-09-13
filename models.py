from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from services.database import Base

class ProjectType(str, Enum):
    PERSONAL = "personal"
    ORDER = "order"

class ProjectStatus(str, Enum):
    IDEA = "idea"
    AGREEMENT = "agreement"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String, index=True)
    type = Column(SQLEnum(ProjectType), default=ProjectType.PERSONAL)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.IDEA)
    deadline = Column(DateTime, nullable=True)
    cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    project = relationship("Project", back_populates="tasks")

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)