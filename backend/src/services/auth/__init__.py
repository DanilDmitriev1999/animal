from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from core.security import get_password_hash, verify_password, create_access_token
from database.models import User
from config import settings


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, first_name: str | None = None, last_name: str | None = None) -> User:
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def generate_token(user: User) -> str:
    data = {"sub": str(user.id), "email": user.email}
    return create_access_token(data, timedelta(minutes=settings.access_token_expire_minutes))
