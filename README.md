# AI Notes & Translation Microservice

## Project overview
A minimal Django + DRF microservice that allows creating text notes, translating them via an external translation API (MyMemory Translate API  by default), storing original and translated text, exposing CRUD and analytics endpoints, and demonstrating caching in Redis.

This repository is a **starter implementation** to satisfy the assignment requirements. It includes:
- Notes CRUD endpoints (create, read, update, delete)
- `/api/notes/<id>/translate/` endpoint to translate and save translated text
- `/api/stats/` endpoint for analytics
- Redis caching for recently requested translations
- Docker + docker-compose for local deployment
- Celery task definition + worker service in docker-compose (optional)

## Tech stack
- Python 3.10, Django, Django REST Framework
- PostgreSQL
- Redis (cache + Celery broker)
- Docker + Docker Compose
- MyMemory Translate API  (configurable translation backend) or fallback mock translator

## Why PostgreSQL?
PostgreSQL is reliable, supports relational features easily, and is simple to run locally via Docker. It fits the assignment requirement (Postgres or DynamoDB). For a production-grade microservice, DynamoDB could be used for horizontal scalability, but Postgres is chosen here for simplicity and relational querying.

## Quick start (local, Docker)
1. Copy `.env.example` to `.env` and edit values if desired:
   ```
   cp .env.example .env
   ```
   Ensure `DJANGO_SECRET_KEY` has a value.

2. Start services:
   ```
   docker-compose up --build
   ```
   This will run migrations and start the Django dev server on port 8000.

3. API endpoints
   - CRUD notes: `http://localhost:8000/api/notes/`
   - Translate a note (POST): `http://localhost:8000/api/notes/<id>/translate/` with JSON `{"target_language":"hi"}`
   - Stats: `http://localhost:8000/api/stats/`

Example curl to create a note:
```
curl -X POST http://localhost:8000/api/notes/ -H "Content-Type: application/json" -d '{"title":"hello","text":"This is a test","original_language":"en"}'
```

Translate:
```
curl -X POST http://localhost:8000/api/notes/1/translate/ -H "Content-Type: application/json" -d '{"target_language":"hi"}'
```

## Caching strategy
- Translations are cached in Redis using key `translation:{note_id}:{target_lang}` for 10 minutes.
- This reduces repeated external API calls for hot translations.
- Redis also configured for Django cache backend and Celery broker.

## Celery
- Celery config and `translate_note_task` are included.
- A `worker` service is defined in `docker-compose.yml`. To use, run:
  ```
  docker-compose up worker
  ```

## Design notes (HLD/LLD)
- High level: Client -> Django REST API -> PostgreSQL (notes) & Redis (cache) -> External translation API
- Low level: `Note` model stores both original and last translated text; translations_count increments on every translation.
- Endpoints: DRF ViewSet for `/api/notes/` and custom action `translate`.
- Environment variables hold credentials and endpoints.



## Files of interest
- `notes/models.py` — Note model
- `notes/views.py` — CRUD + translate + stats endpoints
- `notes/tasks.py` — Celery background task example
- `docker-compose.yml` — brings up web, db, redis, worker
- `Dockerfile` — container for Django app



## Added features (expanded)
- JWT authentication via `djangorestframework-simplejwt`. Obtain tokens at `/api/token/`.
- GraphQL endpoint at `/graphql/` with a `translateNote` mutation and `allNotes` query.
- Asynchronous translations via Celery: POST `/api/notes/<id>/translate_async/` returns a Celery task id. Check status at `/api/tasks/<task_id>/`.
- Prometheus metrics are exposed via `/metrics` (django-prometheus).
- Example Git history and GitHub Actions CI included.

## CI/CD (example)
A GitHub Actions workflow `/.github/workflows/ci.yml` is included to run lint/tests on push.

## How to demo async translation
1. Create a note via API.
2. POST to `/api/notes/<id>/translate_async/` with `{"target_language":"hi"}`.
3. Receive a `task_id`. Poll `/api/tasks/<task_id>/` for status. Once completed, translation stored on the note and cached.



## Quick API examples (cURL / Postman)

Create a note:
```
curl -X POST http://localhost:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","text":"Hello world","original_language":"en"}'
```

Translate a note (sync):
```
curl -X POST http://localhost:8000/api/notes/<NOTE_ID>/translate/ \
  -H "Content-Type: application/json" \
  -d '{"target_language":"hi"}'
```

Legacy route (assignment exact path):
```
curl -X POST http://localhost:8000/translate/<NOTE_ID>/ \
  -H "Content-Type: application/json" \
  -d '{"target_language":"hi"}'
```

Get stats:
```
curl http://localhost:8000/api/stats/
```

## Docker Compose (local demo)

Make a `.env` file from `.env.example`:
```
cp .env.example .env
# optionally edit .env to set DJANGO_SECRET_KEY and other vars
```

Start services:
```
docker-compose up --build
```

This will start:
- Django web server on port 8000
- Postgres (db)
- Redis
- Celery worker
- Flower (Celery monitoring) on port 5555

Celery result backend uses Redis (see `.env.example`) so task statuses and results are available.

## Notes about translation API key

This project is configured to use the free public instance of **MyMemory Translate API ** by default (`TRANSLATE_API_URL=https://MyMemory Translate API .com/translate`). That public instance does not require an API key for small demo usage. If you prefer to use a paid/registered provider (DeepL, Google, etc.) or a self-hosted MyMemory Translate API  instance, set `TRANSLATE_API_URL` and `TRANSLATE_API_KEY` in your `.env` accordingly.

