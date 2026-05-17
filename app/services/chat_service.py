# switched db queries to async
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.schemas.chat import ChatCreate


# converted to async def
async def get_user_chats(db: AsyncSession, user_id: int):
    result = await db.execute(  # async db query
        select(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
    )
    return result.scalars().all()


# converted to async def
async def create_chat(db: AsyncSession, user_id: int, data: ChatCreate):
    chat = Chat(user_id=user_id, title=data.title)
    db.add(chat)
    await db.commit()  # async db commit
    await db.refresh(chat)  # async db refresh
    return chat


# converted to async def
async def get_chat(db: AsyncSession, chat_id: int, user_id: int):
    result = await db.execute(  # async db query
        select(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id)
    )
    return result.scalars().first()


# moved error handling from controller
async def delete_chat(db: AsyncSession, chat_id: int, user_id: int):
    chat = await get_chat(db, chat_id, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")  # moved from controller
    await db.delete(chat)  # async db delete
    await db.commit()  # async db commit
    return {"detail": "Chat deleted"}
