# Bamboo Shoot Soup Backend Scaffold

This repository contains an MVP backend scaffold using FastAPI, SQLAlchemy, Alembic, and SQLite.

## Prerequisites

- Python 3.11+

## Setup

```bash
uv sync
```

Copy environment variables:

```bash
cp .env.example .env
```

## Run API

```bash
uvicorn app.main:app --reload
```

On startup, the backend automatically runs `alembic upgrade head` against `DATABASE_URL`.

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Database Migrations

Manual upgrade to latest:

```bash
alembic upgrade head
```

Downgrade to base:

```bash
alembic downgrade base
```

## Tests

```bash
pytest -q
```
