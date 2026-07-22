# auth.py
# Parollarni xavfsiz hash qilish (bcrypt) va JWT token yaratish/tekshirish.
# JWT_SECRET_KEY har doim .env orqali o'qiladi - kodga yozilmaydi.

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, Query, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.users_db import get_user_by_username

load_dotenv()

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 kun

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY .env faylida topilmadi")
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY .env faylida topilmadi")
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])


_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Autentifikatsiya ma'lumotlari yaroqsiz yoki muddati o'tgan",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    authorization: str | None = Header(default=None),
    query_token: str | None = Query(default=None, alias="token"),
):
    """Joriy foydalanuvchini JWT orqali aniqlaydi.

    Token ikki joydan izlanadi: Authorization: Bearer header (oddiy HTTP
    so'rovlar uchun) yoki ?token=... query parametri (WebSocket ulanishi
    uchun, brauzer WS handshake'da custom header qo'ya olmagani sabab).
    Ikkalasi ham Header/Query orqali olinadi (OAuth2PasswordBearer emas),
    chunki u ichkarida `Request` talab qiladi va WebSocket-only route'larda
    ishlamaydi."""
    header_token = None
    if authorization and authorization.lower().startswith("bearer "):
        header_token = authorization.split(" ", 1)[1].strip()

    jwt_token = header_token or query_token
    if not jwt_token:
        raise _CREDENTIALS_ERROR

    try:
        payload = decode_access_token(jwt_token)
        username = payload.get("sub")
        if username is None:
            raise _CREDENTIALS_ERROR
    except JWTError:
        raise _CREDENTIALS_ERROR

    user = get_user_by_username(username)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


async def require_admin(current_user: dict = Depends(get_current_user)):
    """`get_current_user` ustiga qurilgan: admin bo'lmagan foydalanuvchilar
    uchun 403 qaytaradi (admin panel endpoint'larini himoya qilish uchun)."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sizda admin huquqi yo'q",
        )
    return current_user
