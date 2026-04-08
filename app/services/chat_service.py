from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.schemas.chat import ChatCreate


def get_user_chats(db: Session, user_id: int):
    return (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
        .all()
    )


def create_chat(db: Session, user_id: int, data: ChatCreate):
    chat = Chat(user_id=user_id, title=data.title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_chat(db: Session, chat_id: int, user_id: int):
    return db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()


def delete_chat(db: Session, chat_id: int, user_id: int):
    chat = get_chat(db, chat_id, user_id)
    if chat:
        db.delete(chat)
        db.commit()
    return chat
