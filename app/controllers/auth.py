# cleaned up controller imports
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


# moved logic to auth_service.create_user
@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await auth_service.create_user(data, db)  # calls single service function


# moved logic to auth_service.authenticate_user
@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await auth_service.authenticate_user(data, db)  # calls single service function


# moved logic to auth_service.refresh_tokens
@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    return await auth_service.refresh_tokens(data)  # calls single service function


# moved url building to service
@router.get("/github")
async def github_login():
    return RedirectResponse(auth_service.get_github_auth_url())  # calls single service function


# moved logic to auth_service.handle_github_callback
@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    url = await auth_service.handle_github_callback(code, db)  # calls single service function
    return RedirectResponse(url)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user