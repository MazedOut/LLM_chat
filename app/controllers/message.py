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
    return await message_service.get_messages(db, chat_id, user.id)  # calls single service function


# moved logic to message_service
@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
<<<<<<< HEAD
    return await message_service.send_message(db, chat_id, user.id, data.content)  # calls single service function
=======
    chat = chat_service.get_chat(db, chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_msg, assistant_msg = message_service.send_message(db, chat_id, data.content)

    return {
        "user_message": MessageOut.model_validate(user_msg),
        "assistant_message": MessageOut.model_validate(assistant_msg),
    }
>>>>>>> 687f7962dc5e993d297690b67e234456724bdee3
