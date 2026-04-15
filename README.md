# Okayish Chat

A ChatGPT-style LLM chat app built for the WAD (Web Application Development) course.
Runs a local GGUF model on CPU — no cloud APIs needed.

**Stack:** Python · FastAPI · PostgreSQL · Redis · llama-cpp-python · plain HTML/JS SPA

---

## Prerequisites

Before anything else, make sure you have these installed:

- [Python 3.11+](https://www.python.org/downloads/) — check "Add to PATH" during install
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — needed for PostgreSQL and Redis
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — needed to compile llama-cpp-python on Windows (select "Desktop development with C++")

---

## Docker Setup (PostgreSQL + Redis)

The app uses two Docker containers instead of local database installs.
Open Docker Desktop first and wait for **Engine running** (green dot, bottom-left).

### First time — create the containers

```bash
# PostgreSQL
docker run -d --name llm-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=llm_chat \
  -p 5432:5432 postgres

# Redis
docker run -d --name llm-redis -p 6379:6379 redis
```

### Every time after restarting your PC

The containers stop when Docker closes. Start them again with:

```bash
docker start llm-postgres
docker start llm-redis
```

Verify both are running:

```bash
docker ps
```

You should see `llm-postgres` (port 5432) and `llm-redis` (port 6379) listed with status **Up**.

---

## Installation

```bash
# Clone the repo
git clone https://github.com/your-username/okayish-chat.git
cd okayish-chat

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies (llama-cpp-python takes a few minutes)
pip install -r requirements.txt
```

If `llama-cpp-python` fails to install, run this first then retry:

```bash
pip install llama-cpp-python --prefer-binary
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and edit:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/llm_chat
REDIS_URL=redis://localhost:6379
SECRET_KEY=<generate below>
GITHUB_CLIENT_ID=<from GitHub OAuth app>
GITHUB_CLIENT_SECRET=<from GitHub OAuth app>
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

**Generate a secret key:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**GitHub OAuth App** — go to [github.com/settings/developers](https://github.com/settings/developers), create a new OAuth App with:
- Homepage URL: `http://localhost:8000`
- Callback URL: `http://localhost:8000/auth/github/callback`

Copy the Client ID and Client Secret into `.env`.

---

## Add the model

Copy your `.gguf` model file into the project root and rename it to exactly `model.gguf`.
It should be at the same level as `requirements.txt`.

---

## Running the app

```bash
# 1. Make sure Docker containers are running
docker start llm-postgres && docker start llm-redis

# 2. Activate venv (if not already active)
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Apply database migrations (first time, or after schema changes)
alembic upgrade head

# 4. Start the server
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Project structure

```
okayish_chat/
├── app/
│   ├── controllers/        # FastAPI routers (auth, chat, message)
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic (auth, LLM, chat, message)
│   ├── config.py           # Settings loaded from .env
│   ├── database.py         # SQLAlchemy engine + session
│   ├── dependencies.py     # JWT auth dependency
│   ├── redis_client.py     # Redis connection
│   └── main.py             # App entry point
├── frontend/               # Static SPA (login, register, chat)
├── alembic/                # Database migrations
├── model.gguf              # Local LLM model (not committed to git)
├── .env                    # Secrets (not committed to git)
└── requirements.txt
```

---

## Architecture

**UI:** SPA (Single-Page Application) — plain HTML/CSS/JS served from `/static`

**Backend pattern:** MCS — Model · Controller · Service

**Auth flow:**
1. Register or login → receive JWT access token (30 min) + opaque refresh token (30 days)
2. Refresh token stored in Redis with TTL
3. On expiry, client calls `/auth/refresh` → old token deleted, new pair issued (rotation)
4. GitHub OAuth follows the same token flow after the OAuth callback

---

## API

Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs) once the app is running.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Register new user |
| POST | `/auth/login` | — | Login with username + password |
| POST | `/auth/refresh` | — | Rotate refresh token |
| GET | `/auth/github` | — | Start GitHub OAuth |
| GET | `/auth/github/callback` | — | GitHub OAuth callback |
| GET | `/auth/me` | 🔒 | Current user profile |
| GET | `/chats` | 🔒 | List your chats |
| POST | `/chats` | 🔒 | Create a new chat |
| DELETE | `/chats/{chat_id}` | 🔒 | Delete a chat |
| GET | `/chats/{chat_id}/messages` | 🔒 | Get message history |
| POST | `/chats/{chat_id}/messages` | 🔒 | Send a message |

---

## Troubleshooting

**`python` not recognized** — reinstall Python and check "Add to PATH"

**`docker` not recognized** — open Docker Desktop from the Start menu and wait for the green dot

**pip fails on llama-cpp-python** — run `pip install llama-cpp-python --prefer-binary`

**"No module named app"** — you're in the wrong folder or venv isn't active

**alembic fails with "connection refused"** — PostgreSQL container isn't running: `docker start llm-postgres`

**LLM replies "[Model not loaded]"** — `model.gguf` is missing from the project root or named incorrectly

**GitHub OAuth error** — check that the callback URL in your GitHub OAuth App settings is exactly `http://localhost:8000/auth/github/callback`
