# Codex Portfolio

*I vibe coded this app from scratch just to see how far I could get without writing anything myself.*


A minimal FastAPI application for tracking cryptocurrency portfolio transactions.
=======
=======

A portfolio application split into separate backend and frontend workspaces.

## Layout

- `backend/` contains the FastAPI application, Python dependencies, and backend tests.
- `frontend/` is reserved for the future Next.js application.

## Backend Setup

```bash
cd backend
uv sync --dev
cp .env.example .env
```

Add your CoinGecko Demo API key to `backend/.env`.


=======

### Environment variables

The application reads configuration from `.env`:

```env
COINGECKO_API_KEY=your-coingecko-demo-api-key
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
ENVIRONMENT=development

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Required JWT configuration:

- `JWT_SECRET_KEY`: secret used to sign and validate access tokens. Set this to a long, random value before using authentication; it is required when `ENVIRONMENT` is `production` or `prod`.
- `JWT_ALGORITHM`: signing algorithm for JWTs. The default is `HS256`.
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: number of minutes before issued access tokens expire. The default is `30`.

## Backend Run

```bash
cd backend
uv run uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.


=======

## Authentication

The `/health` endpoint remains public and does not require a token. Transaction and portfolio endpoints require authentication with an `Authorization: Bearer <token>` header, including:

- `POST /transactions`
- `GET /transactions`
- `GET /transactions/{transaction_id}`
- `GET /portfolio/current_value`

### Register a user

Create an account with `POST /auth/register`:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "satoshi",
    "email": "satoshi@example.com",
    "password": "correct-horse-battery-staple"
  }'
```

The response includes the created user's `id`, `username`, optional `email`, `is_active` status, and `created_at` timestamp.

### Log in and receive an access token

Exchange the username and password for a bearer token with `POST /auth/login`:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "satoshi",
    "password": "correct-horse-battery-staple"
  }'
```

Example response:

```json
{
  "access_token": "<token>",
  "token_type": "bearer"
}
```

Save the returned `access_token` and send it on protected requests.

### Make a protected request

```bash
TOKEN="<token>"

curl http://127.0.0.1:8000/portfolio/current_value \
  -H "Authorization: Bearer ${TOKEN}"
```

You can use the same header when creating or reading transactions:

```bash
curl -X POST http://127.0.0.1:8000/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "symbol": "BTC",
    "coingecko_id": "bitcoin",
    "quantity": "0.01",
    "transaction_type": "buy"
  }'
```

## Backend Test

```bash
cd backend
uv run pytest
```
