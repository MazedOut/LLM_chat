# switched db queries to async
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.schemas.message import MessageOut
from app.services.llm_service import generate_response
from app.services import chat_service


# moved conversion logic from controller
async def get_messages(db: AsyncSession, chat_id: int, user_id: int):
    chat = await chat_service.get_chat(db, chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")  # moved from controller

    result = await db.execute(  # async db query
        select(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at)
    )
    msgs = result.scalars().all()

    # moved dict conversion from controller
    if msgs and isinstance(msgs[0], dict):
        return [MessageOut(**m) for m in msgs]
    return msgs


# moved chat check from controller
async def send_message(db: AsyncSession, chat_id: int, user_id: int, content: str):
    chat = await chat_service.get_chat(db, chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")  # moved from controller

    user_msg = Message(chat_id=chat_id, role="user", content=content)
    db.add(user_msg)
    await db.commit()  # async db commit
    await db.refresh(user_msg)  # async db refresh

    reply = generate_response(content)

    assistant_msg = Message(chat_id=chat_id, role="assistant", content=reply)
    db.add(assistant_msg)
    await db.commit()  # async db commit
    await db.refresh(assistant_msg)  # async db refresh

    return {
        "user_message": MessageOut.model_validate(user_msg),
        "assistant_message": MessageOut.model_validate(assistant_msg),
    }
