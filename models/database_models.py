"""
Модели базы данных для AI Learning Platform
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

# Енумы
class UserRole(PyEnum):
    STUDENT = "student"
    INSTRUCTOR = "instructor" 
    ADMIN = "admin"

class TrackStatus(PyEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"

class DifficultyLevel(PyEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ContentType(PyEnum):
    THEORY = "theory"
    PRACTICE = "practice"
    HOMEWORK = "homework"
    QUIZ = "quiz"

# Модели
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    ai_config = relationship("AIConfiguration", back_populates="user", uselist=False)
    learning_tracks = relationship("LearningTrack", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class AIConfiguration(Base):
    __tablename__ = "ai_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    model_name = Column(String(100), default="gpt-3.5-turbo")
    base_url = Column(String(255), default="https://api.openai.com/v1")
    api_key_encrypted = Column(Text, nullable=False)
    max_tokens = Column(Integer, default=2000)
    temperature = Column(Float, default=0.7)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="ai_config")

class LearningTrack(Base):
    __tablename__ = "learning_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    skill_area = Column(String(100))
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.BEGINNER)
    estimated_duration_hours = Column(Integer)
    status = Column(Enum(TrackStatus), default=TrackStatus.PLANNING)
    ai_generated_plan = Column(JSON)
    user_expectations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="learning_tracks")
    chat_sessions = relationship("ChatSession", back_populates="track")
    modules = relationship("CourseModule", back_populates="track")


class ChatType(PyEnum):
    TRACK_MANAGER = "track_manager"
    LECTURE_AGENT = "lecture_agent"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    track_id = Column(UUID(as_uuid=True), ForeignKey("learning_tracks.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_name = Column(String(255))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="chat_sessions")
    track = relationship("LearningTrack", back_populates="chat_sessions")
    chats = relationship("Chat", back_populates="session")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    chat_name = Column(String(255))
    chat_type = Column(Enum(ChatType), default=ChatType.TRACK_MANAGER)
    status = Column(String(20), default="active")
    ai_context = Column(JSON)  # Контекст для AI (настройки, предыдущий контекст)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    session = relationship("ChatSession", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    sender_type = Column(String(10), nullable=False)  # 'user' or 'ai'
    message_content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    ai_model_used = Column(String(100))
    tokens_used = Column(Integer)  # Количество использованных токенов
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Связи
    chat = relationship("Chat", back_populates="messages")

class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    track_id = Column(UUID(as_uuid=True), ForeignKey("learning_tracks.id"), nullable=False)
    module_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    learning_objectives = Column(JSON)
    estimated_duration_hours = Column(Integer)
    ai_generated_content = Column(JSON)
    status = Column(String(20), default="not_started")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    track = relationship("LearningTrack", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"), nullable=False)
    lesson_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content_type = Column(Enum(ContentType), default=ContentType.THEORY)
    content = Column(Text)
    ai_generated_notes = Column(Text)
    estimated_duration_minutes = Column(Integer)
    status = Column(String(20), default="not_started")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    module = relationship("CourseModule", back_populates="lessons")
    homework_assignments = relationship("HomeworkAssignment", back_populates="lesson")

class HomeworkAssignment(Base):
    __tablename__ = "homework_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    ai_generated_task = Column(JSON)
    due_date = Column(DateTime)
    max_score = Column(Integer, default=100)
    status = Column(String(20), default="assigned")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    lesson = relationship("Lesson", back_populates="homework_assignments")

# Функция создания таблиц
async def create_tables():
    from utils.config import settings
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
