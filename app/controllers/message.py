from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message import MessageSend, MessageOut
from app.services import chat_service, message_service

router = APIRouter(prefix="/chats", tags=["messages"])


@router.get("/{chat_id}/messages", response_model=List[MessageOut])
def get_messages(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = chat_service.get_chat(db, chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return message_service.get_messages(db, chat_id)


@router.post("/{chat_id}/messages")
def send_message(
    chat_id: int,
    data: MessageSend,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = chat_service.get_chat(db, chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_msg, assistant_msg = message_service.send_message(db, chat_id, data.content)

    return {
        "user_message": MessageOut.model_validate(user_msg),
        "assistant_message": MessageOut.model_validate(assistant_msg),
    }
