# cleaned up controller imports
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatOut
from app.services import chat_service

router = APIRouter(prefix="/chats", tags=["chats"])


# converted to async def
@router.get("", response_model=List[ChatOut])
async def list_chats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await chat_service.get_user_chats(db, user.id)  # calls single service function


# converted to async def
@router.post("", response_model=ChatOut)
async def create_chat(
    data: ChatCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.create_chat(db, user.id, data)  # calls single service function


# moved error handling to service
@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.delete_chat(db, chat_id, user.id)  # calls single service function
