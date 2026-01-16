# Astro-Soulmate Backend

FastAPI-based backend for AI Relationship Simulator.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI (Async)
- **Database:** PostgreSQL 17 + pgvector
- **ORM:** SQLModel
- **Auth:** JWT (python-jose + bcrypt)
- **AI:** Google Gemini 1.5 Flash
- **Astrology:** kerykeion

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 4. Start PostgreSQL
docker-compose up -d

# 5. Run server
python main.py
```

API docs available at: **http://localhost:8000/docs**

## API Endpoints

### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `GET /auth/me` - Current user info

### Boyfriends (Protected)
- `POST /boyfriends` - Create AI boyfriend
- `GET /boyfriends` - List your boyfriends
- `GET /boyfriends/{id}` - Get boyfriend details
- `DELETE /boyfriends/{id}` - Delete boyfriend

### Chat (Protected)
- `POST /chat` - Chat with boyfriend
- `GET /chat/sessions` - List chat sessions
- `GET /chat/sessions/{id}` - Get session details
- `DELETE /chat/sessions/{id}` - Delete session

## Security

- Passwords hashed with bcrypt
- JWT tokens for authentication
- User isolation (can't access other users' data)
- Protected routes require `Authorization: Bearer <token>` header
