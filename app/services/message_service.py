from sqlalchemy.orm import Session

from app.models.message import Message
from app.services.llm_service import generate_response


def get_messages(db: Session, chat_id: int):
    return (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .all()
    )


def send_message(db: Session, chat_id: int, content: str):
    user_msg = Message(chat_id=chat_id, role="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    reply = generate_response(content)

    assistant_msg = Message(chat_id=chat_id, role="assistant", content=reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return user_msg, assistant_msg
