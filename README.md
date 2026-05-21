# Codex Portfolio

*I vibe coded this app from scratch just to see how far I could get without writing anything myself.*

A minimal FastAPI application.

## Setup

```bash
uv sync --dev
cp .env.example .env
```

Add your CoinGecko Demo API key to `.env`.

## Run

```bash
uv run uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

## Test

```bash
uv run pytest
```
