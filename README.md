# LLM Chat

A ChatGPT-like web app built with FastAPI, PostgreSQL, Redis, and llama-cpp-python.

## Stack

- **Backend:** FastAPI, MCS architecture (Models → Controllers → Services)
- **Database:** PostgreSQL with Alembic migrations
- **Auth:** JWT (access + refresh), GitHub OAuth
- **Sessions:** Redis (30-day refresh token TTL)
- **LLM:** llama-cpp-python (local GGUF model, CPU)
- **Frontend:** SPA — vanilla HTML/CSS/JS, no framework

---

## Setup

### 1. Clone and install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
DATABASE_URL=postgresql://user:password@localhost:5432/llm_chat
REDIS_URL=redis://localhost:6379
SECRET_KEY=some-long-random-string
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

To generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. GitHub OAuth app

Go to GitHub → Settings → Developer settings → OAuth Apps → New OAuth App.

- Homepage URL: `http://localhost:8000`
- Callback URL: `http://localhost:8000/auth/github/callback`

Copy the client ID and secret into `.env`.

### 4. Start PostgreSQL and Redis

Make sure both are running locally (or via Docker):

```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_USER=user -e POSTGRES_DB=llm_chat postgres
docker run -d -p 6379:6379 redis
```

### 5. Run database migrations

```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 6. Add a model (optional)

Download a small GGUF model (e.g. TinyLlama) from HuggingFace and place it as `model.gguf` in the project root.

Without the model file the app still runs — the assistant will return a placeholder message.

### 7. Start the server

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## Project structure

```
app/
  main.py              # FastAPI app, router registration
  config.py            # Settings from .env
  database.py          # SQLAlchemy engine + session
  redis_client.py      # Redis connection
  dependencies.py      # JWT auth dependency for protected routes

  models/              # SQLAlchemy ORM models
    user.py
    chat.py
    message.py

  schemas/             # Pydantic request/response schemas
    user.py
    chat.py
    message.py

  controllers/         # Route handlers (thin, delegate to services)
    auth.py
    chat.py
    message.py

  services/            # Business logic
    auth_service.py    # JWT, bcrypt, Redis session management
    chat_service.py    # CRUD for chats
    message_service.py # CRUD for messages + calls LLM
    llm_service.py     # Lazy-loads the GGUF model, runs inference

frontend/
  index.html           # Redirects to chat or login
  login.html
  register.html
  chat.html            # Main SPA: sidebar + chat window

alembic/               # DB migrations
```

---

## Auth flow

1. **Register / Login** → server returns `access_token` (JWT, 30 min) + `refresh_token` (random, stored in Redis for 30 days)
2. **Protected requests** → send `Authorization: Bearer <access_token>`
3. **Token expired** → frontend calls `POST /auth/refresh` with the refresh token → gets new pair (refresh token is rotated on every use)
4. **GitHub OAuth** → user redirected to GitHub → callback exchanges code → server creates/finds user → redirects to frontend with tokens in query params

---

## API overview

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/auth/register` | — | Register with username + password |
| POST | `/auth/login` | — | Login, get tokens |
| POST | `/auth/refresh` | — | Refresh access token |
| GET | `/auth/github` | — | Start GitHub OAuth |
| GET | `/auth/github/callback` | — | GitHub OAuth callback |
| GET | `/chats` | ✓ | List user's chats |
| POST | `/chats` | ✓ | Create a chat |
| DELETE | `/chats/{id}` | ✓ | Delete a chat |
| GET | `/chats/{id}/messages` | ✓ | Get messages in a chat |
| POST | `/chats/{id}/messages` | ✓ | Send a message, get LLM reply |

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
