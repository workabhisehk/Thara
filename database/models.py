"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from database.connection import Base


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class PillarType(str, enum.Enum):
    """Pillar/category type enumeration."""
    WORK = "work"
    EDUCATION = "education"
    PROJECTS = "projects"
    PERSONAL = "personal"
    OTHER = "other"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Work hours configuration
    work_start_hour = Column(Integer, default=8)
    work_end_hour = Column(Integer, default=20)
    weekend_start_hour = Column(Integer, default=10)
    weekend_end_hour = Column(Integer, default=18)
    
    # Settings
    timezone = Column(String, default="UTC")
    check_in_interval = Column(Integer, default=30)  # minutes
    is_active = Column(Boolean, default=True)
    is_onboarded = Column(Boolean, default=False)
    
    # Google Calendar
    google_calendar_connected = Column(Boolean, default=False)
    google_refresh_token = Column(Text, nullable=True)
    google_access_token = Column(Text, nullable=True)
    google_token_expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    clarifications = relationship("Clarification", back_populates="user", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user", cascade="all, delete-orphan")
    learning_feedback = relationship("LearningFeedback", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    """Task model."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pillar = Column(SQLEnum(PillarType), nullable=False, index=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    due_date = Column(DateTime, nullable=True, index=True)
    estimated_duration = Column(Integer, nullable=True)  # minutes
    actual_duration = Column(Integer, nullable=True)  # minutes
    
    # Scheduling
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    calendar_event_id = Column(String, nullable=True)  # Google Calendar event ID
    
    # Dependencies
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional flexible data
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    depends_on = relationship("Task", remote_side=[id])


class CalendarEvent(Base):
    """Google Calendar event model."""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    google_event_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    timezone = Column(String, nullable=True)
    
    location = Column(String, nullable=True)
    attendees = Column(JSON, nullable=True)  # List of attendee emails
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String, nullable=True)
    
    # Link to task if scheduled
    linked_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_synced_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    linked_task = relationship("Task", foreign_keys=[linked_task_id])


class Conversation(Base):
    """Conversation/message history model."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    message_id = Column(Integer, nullable=False)  # Telegram message ID
    text = Column(Text, nullable=False)
    is_from_user = Column(Boolean, nullable=False)  # True if from user, False if from bot
    
    # Context
    intent = Column(String, nullable=True)
    entities = Column(JSON, nullable=True)  # Extracted entities
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")


class Habit(Base):
    """Recognized user habits and patterns."""
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    pattern_type = Column(String, nullable=False)  # e.g., "task_completion_time", "preferred_work_hours"
    pattern_data = Column(JSON, nullable=False)  # Pattern details
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_observed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="habits")


class Analytics(Base):
    """Analytics and metrics."""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    date = Column(DateTime, nullable=False, index=True)
    pillar = Column(SQLEnum(PillarType), nullable=True, index=True)
    
    # Metrics
    tasks_completed = Column(Integer, default=0)
    tasks_created = Column(Integer, default=0)
    tasks_overdue = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)  # minutes
    
    # Readiness scores
    readiness_score = Column(Float, nullable=True)  # 0.0 to 1.0
    upcoming_deadline_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics")


class Clarification(Base):
    """Pending clarification questions."""
    __tablename__ = "clarifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    question = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)  # Context about what needs clarification
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    is_resolved = Column(Boolean, default=False)
    answer = Column(Text, nullable=True)
    
    # Priority for asking (higher = more urgent)
    priority = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)
    last_asked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="clarifications")


class LearningFeedback(Base):
    """User feedback for learning and adaptation."""
    __tablename__ = "learning_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    feedback_type = Column(String, nullable=False)  # e.g., "suggestion_rating", "plan_feedback"
    context = Column(JSON, nullable=False)  # What the feedback is about
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="learning_feedback")

