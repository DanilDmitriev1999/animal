from sqlalchemy import Column, Integer, String, Boolean, Enum, TIMESTAMP, func

from .config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(Enum('user', 'admin', 'instructor', name='user_role'), default='user')
    ai_personality = Column(Enum('friendly', 'professional', 'casual', 'motivating', name='ai_personality'), default='friendly')
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP(timezone=True))

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"
