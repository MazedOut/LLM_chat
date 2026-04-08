import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.redis_client import r

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain[:72], hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    r.setex(
        f"session:{token}",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        str(user_id)
    )
    return token


def verify_refresh_token(token: str):
    user_id = r.get(f"session:{token}")
    return int(user_id) if user_id else None


def invalidate_refresh_token(token: str):
    r.delete(f"session:{token}")


def get_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None
    return db.query(User).filter(User.id == user_id).first()


def get_or_create_github_user(db: Session, github_id: str, username: str, email: str = None):
    # existing GitHub user
    user = db.query(User).filter(User.github_id == github_id).first()
    if user:
        return user

    # deduplicate username
    base = username
    suffix = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}{suffix}"
        suffix += 1

    user = User(username=username, email=email, github_id=github_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
