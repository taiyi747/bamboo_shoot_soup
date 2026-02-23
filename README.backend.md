# Bamboo Shoot Soup Backend Scaffold

This repository contains an MVP backend scaffold using FastAPI, SQLAlchemy, Alembic, and SQLite.

## Prerequisites

- Python 3.11+

## Setup

```bash
python -m pip install -e ".[dev]"
```

Copy environment variables:

```bash
cp .env.example .env
```

Optional CORS override (comma-separated):

```bash
CORS_ALLOW_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

## Run API

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Database Migrations

Upgrade to latest:

```bash
alembic upgrade head
```

Downgrade to base:

```bash
alembic downgrade base
```

## Tests

```bash
pytest
```
