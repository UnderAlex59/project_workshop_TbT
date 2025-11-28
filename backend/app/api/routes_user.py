import random
import time
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_token
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import (
    AuthResponse,
    UserCreate,
    UserIdentityResponse,
    UserLogin,
    UserOut,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _is_valid_anonymous_id(value: str) -> bool:
    return value.isdigit() and 6 <= len(value) <= 40


def generate_anonymous_user_id() -> str:
    timestamp_part = str(int(time.time() * 1000))
    random_part = "".join(str(random.randint(0, 9)) for _ in range(6))
    return f"{timestamp_part}{random_part}"


# Публичные эндпоинты (не требуют аутентификации)
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create new user (регистрация)"""
    return user_service.add_user(db, user_in)


@router.post("/login", response_model=AuthResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Аутентификация пользователя и выдача JWT токена
    """
    try:
        user = user_service.authenticate_user(
            db, login_data.username, login_data.password
        )

        # Создаем JWT токен
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        return AuthResponse(
            authenticated=True,
            user_id=user.id,
            access_token=access_token,
            token_type="bearer",
            message="Аутентификация успешна",
        )
    except HTTPException as e:
        if e.status_code == 401:
            return AuthResponse(
                authenticated=False, message="Неверный логин или пароль"
            )
        elif e.status_code == 400:
            return AuthResponse(
                authenticated=False, message="Пользователь деактивирован"
            )
        else:
            raise e



# ?????????? ????????????? ????????????, ???? ???? ?? ?? ???????????
@router.get("/identity", response_model=UserIdentityResponse)
def get_user_identity(
    current_id: str | None = Query(
        None, description="Existing anonymous user identifier to reuse if still valid"
    ),
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: Session = Depends(get_db),
):
    """
    Resolve a stable user identifier for the client. If a valid JWT is provided,
    the registered user id is returned, otherwise a numeric anonymous id is reused or generated.
    """
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("user_id") if payload else None
        username = payload.get("sub") if payload else None

        if user_id is not None:
            try:
                user_id_int = int(user_id)
            except (TypeError, ValueError):
                user_id_int = None

            user = (
                user_repository.get_user_by_id(db, user_id_int)
                if user_id_int is not None
                else None
            )
            if user and user.username == username and user.is_active:
                return UserIdentityResponse(
                    user_id=str(user.id),
                    kind="registered",
                    registered_user_id=user.id,
                )

    candidate = current_id if current_id and _is_valid_anonymous_id(current_id) else None
    anonymous_id = candidate or generate_anonymous_user_id()

    return UserIdentityResponse(
        user_id=anonymous_id, kind="anonymous", registered_user_id=None
    )



# 🔐 ЛИЧНЫЕ эндпоинты (работают с текущим пользователем)
@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user


@router.put("/me", response_model=UserOut)
def update_current_user(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user information"""
    return user_service.edit_user(db, current_user.id, user_in)


@router.delete("/me")
def deactivate_current_user(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Deactivate current user (soft delete)"""
    return user_service.deactivate_user(db, current_user.id)


@router.patch("/me/activate")
def activate_current_user(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Activate current user"""
    return user_service.activate_user(db, current_user.id)


# 🔧 АДМИНСКИЕ эндпоинты (работают с любыми пользователями по ID)
@router.get("/", response_model=list[UserOut])
def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Number of records to return"),
    active_only: bool = Query(False, description="Show only active users"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of users (только для просмотра)"""
    if active_only:
        return user_service.list_active_users(db)
    return user_service.list_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user by ID (только для просмотра)"""
    return user_service.get_user_by_id(db, user_id)
