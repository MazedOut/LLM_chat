from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatOut
from app.services import chat_service

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=List[ChatOut])
def list_chats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return chat_service.get_user_chats(db, user.id)


@router.post("", response_model=ChatOut)
def create_chat(
    data: ChatCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return chat_service.create_chat(db, user.id, data)


@router.delete("/{chat_id}")
def delete_chat(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = chat_service.delete_chat(db, chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"detail": "Chat deleted"}
