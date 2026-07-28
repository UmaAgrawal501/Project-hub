# ProjectHub API (Milestone 0–1)

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill Supabase + DATABASE_URL values in .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Health

`GET /api/v1/health`

## Auth (API_CONTRACT)

- `POST /api/v1/auth/sign-up`
- `POST /api/v1/auth/sign-in`
- `POST /api/v1/auth/sign-out`
- `GET /api/v1/auth/me`
- `PATCH /api/v1/auth/me`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/change-password`

Password reset: Supabase emails a link to `PASSWORD_RESET_REDIRECT_URL`. The frontend should read the recovery access token and call `POST /auth/reset-password` with `{ "token", "password" }`.
