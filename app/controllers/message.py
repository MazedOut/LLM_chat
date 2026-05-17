# cleaned up controller imports
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import MessageSend, MessageOut
from app.services import message_service

router = APIRouter(prefix="/chats", tags=["messages"])


# moved logic to message_service
@router.get("/{chat_id}/messages", response_model=List[MessageOut])
async def get_messages(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await message_service.get_messages(db, chat_id, user.id)


# moved logic to message_service
@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await message_service.send_message(db, chat_id, user.id, data.content)