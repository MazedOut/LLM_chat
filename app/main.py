from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.controllers import auth, chat, message

app = FastAPI(title="LLM Chat")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(message.router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    return RedirectResponse("/static/index.html")
