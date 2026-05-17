import secrets
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.redis_client import r
from app.schemas.user import UserRegister, UserLogin, TokenResponse, RefreshRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain[:72], hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# switched redis calls to async
async def create_refresh_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    await r.setex(  # awaited async redis call
        f"session:{token}",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        str(user_id)
    )
    return token


# switched redis calls to async
async def verify_refresh_token(token: str):
    user_id = await r.get(f"session:{token}")  # awaited async redis call
    return int(user_id) if user_id else None


# switched redis calls to async
async def invalidate_refresh_token(token: str):
    await r.delete(f"session:{token}")  # awaited async redis call


# switched db queries to async
async def get_user_from_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None
    result = await db.execute(select(User).filter(User.id == user_id))  # async db query
    return result.scalars().first()


# moved register logic from controller
async def create_user(data: UserRegister, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).filter(User.username == data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()  # async db commit
    await db.refresh(user)  # async db refresh

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=await create_refresh_token(user.id),
    )


# moved login logic from controller
async def authenticate_user(data: UserLogin, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).filter(User.username == data.username))
    user = result.scalars().first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=await create_refresh_token(user.id),
    )


# moved refresh logic from controller
async def refresh_tokens(data: RefreshRequest) -> TokenResponse:
    user_id = await verify_refresh_token(data.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # rotate the refresh token on every use
    await invalidate_refresh_token(data.refresh_token)

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=await create_refresh_token(user_id),
    )


# moved github url from controller
def get_github_auth_url() -> str:
    return (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=read:user user:email"
    )


# switched db queries to async
async def get_or_create_github_user(db: AsyncSession, github_id: str, username: str, email: str = None):
    # existing GitHub user
    result = await db.execute(select(User).filter(User.github_id == github_id))  # async db query
    user = result.scalars().first()
    if user:
        return user

    # deduplicate username
    base = username
    suffix = 1
    result = await db.execute(select(User).filter(User.username == username))
    while result.scalars().first():
        username = f"{base}{suffix}"
        suffix += 1
        result = await db.execute(select(User).filter(User.username == username))

    user = User(username=username, email=email, github_id=github_id)
    db.add(user)
    await db.commit()  # async db commit
    await db.refresh(user)  # async db refresh
    return user


# moved github callback from controller
async def handle_github_callback(code: str, db: AsyncSession) -> str:
    # exchange code for GitHub access token
    async with httpx.AsyncClient() as client:  # switched to async http
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
    gh_token = token_resp.json().get("access_token")
    if not gh_token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed")

    # get GitHub user profile
    gh_headers = {"Authorization": f"Bearer {gh_token}", "Accept": "application/json"}
    async with httpx.AsyncClient() as client:  # switched to async http
        gh_user_resp = await client.get("https://api.github.com/user", headers=gh_headers)
        gh_user = gh_user_resp.json()

        # try to get primary email if profile email is private
        email = gh_user.get("email")
        if not email:
            emails_resp = await client.get("https://api.github.com/user/emails", headers=gh_headers)
            emails = emails_resp.json()
            email = next((e["email"] for e in emails if e.get("primary")), None)

    user = await get_or_create_github_user(
        db,
        github_id=str(gh_user["id"]),
        username=gh_user["login"],
        email=email,
    )

    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_token(user.id)

    # pass tokens to frontend via query params, SPA picks them up
    return f"/static/chat.html?access_token={access_token}&refresh_token={refresh_token}"
