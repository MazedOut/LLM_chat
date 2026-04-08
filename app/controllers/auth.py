import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=auth_service.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=auth_service.create_access_token(user.id),
        refresh_token=auth_service.create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not auth_service.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(
        access_token=auth_service.create_access_token(user.id),
        refresh_token=auth_service.create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest):
    user_id = auth_service.verify_refresh_token(data.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # rotate the refresh token on every use
    auth_service.invalidate_refresh_token(data.refresh_token)

    return TokenResponse(
        access_token=auth_service.create_access_token(user_id),
        refresh_token=auth_service.create_refresh_token(user_id),
    )


@router.get("/github")
def github_login():
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        "&scope=read:user user:email"
    )
    return RedirectResponse(url)


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    # exchange code for GitHub access token
    token_resp = httpx.post(
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
    gh_user = httpx.get("https://api.github.com/user", headers=gh_headers).json()

    # try to get primary email if profile email is private
    email = gh_user.get("email")
    if not email:
        emails = httpx.get("https://api.github.com/user/emails", headers=gh_headers).json()
        email = next((e["email"] for e in emails if e.get("primary")), None)

    user = auth_service.get_or_create_github_user(
        db,
        github_id=str(gh_user["id"]),
        username=gh_user["login"],
        email=email,
    )

    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)

    # pass tokens to frontend via query params, SPA picks them up
    return RedirectResponse(
        f"/static/chat.html?access_token={access_token}&refresh_token={refresh_token}"
    )

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user