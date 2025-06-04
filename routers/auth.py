"""
Роутер аутентификации
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging

from models.database import get_db
from models.database_models import User, UserRole, AIConfiguration
from utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic модели
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime

class GuestUserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_guest: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class GuestToken(BaseModel):
    access_token: str
    token_type: str
    user: GuestUserResponse

# Утилиты для паролей
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Утилиты для JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Получение текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if user_id.startswith("guest_"):
        try:
            guest_uuid = uuid.UUID(user_id.replace("guest_", ""))
            result = await db.execute(select(User).where(User.id == guest_uuid))
            user = result.scalar_one_or_none()
            if user:
                return user
        except Exception:
            pass
        raise credentials_exception
    
    # Для обычных пользователей ищем в БД
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Получение текущего пользователя из JWT токена (опционально, без ошибок если токена нет)"""
    
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    # Если это гостевой пользователь
    if user_id.startswith("guest_"):
        try:
            guest_uuid = uuid.UUID(user_id.replace("guest_", ""))
            result = await db.execute(select(User).where(User.id == guest_uuid))
            user = result.scalar_one_or_none()
            return user
        except Exception:
            return None
    
    # Для обычных пользователей ищем в БД
    try:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        return user
    except Exception:
        return None

# Эндпоинты
@router.post("/register", response_model=Token)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    # Проверяем, существует ли пользователь с таким email
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Создаем нового пользователя
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=UserRole.STUDENT
    )
    
    db.add(new_user)
    await db.flush()  # Получаем ID пользователя
    
    # Создаем конфигурацию AI по умолчанию
    ai_config = AIConfiguration(
        user_id=new_user.id,
        model_name=settings.default_openai_model,
        base_url=settings.default_openai_base_url,
        api_key_encrypted="default",  # В продакшене должно шифроваться
        max_tokens=2000,
        temperature=0.7
    )
    
    db.add(ai_config)
    await db.commit()
    
    # Создаем JWT токен
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(new_user.id)}, expires_delta=access_token_expires
    )
    
    # Формируем ответ
    user_response = UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role.value,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )
    
    logger.info(f"User registered: {new_user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Вход пользователя в систему"""
    
    # Находим пользователя по email
    result = await db.execute(select(User).where(User.email == user_credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Создаем JWT токен
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Формируем ответ
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@router.post("/guest-login", response_model=GuestToken)
async def guest_login(db: AsyncSession = Depends(get_db)):
    """Вход в гостевом режиме без регистрации"""
    
    # Создаем временный ID для гостя
    guest_uuid = uuid.uuid4()
    guest_id = f"guest_{guest_uuid.hex}"
    
    # Создаем запись пользователя в БД
    hashed_password = get_password_hash(uuid.uuid4().hex)
    new_user = User(
        id=guest_uuid,
        email=f"guest_{guest_uuid.hex[:8]}@guest.com",
        password_hash=hashed_password,
        first_name="Гость",
        last_name="Пользователь",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()

    # Создаем JWT токен для гостя
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": guest_id}, expires_delta=access_token_expires
    )
    
    # Формируем гостевого пользователя
    guest_user = GuestUserResponse(
        id=guest_id,
        email=new_user.email,
        first_name="Гость",
        last_name="Пользователь",
        role="student",
        is_guest=True
    )
    
    logger.info(f"Guest user logged in: {guest_id}")
    
    return GuestToken(
        access_token=access_token,
        token_type="bearer",
        user=guest_user
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    
    # Если это гостевой пользователь
    if current_user.email.startswith("guest_"):
        return UserResponse(
            id=str(current_user.id),
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            role=current_user.role.value,
            is_active=current_user.is_active,
            created_at=datetime.utcnow()
        )
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    ) 