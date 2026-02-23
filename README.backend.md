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
