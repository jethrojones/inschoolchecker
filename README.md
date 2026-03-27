# District Status Checker

District Status Checker is a monorepo MVP for determining whether a public school district is in session on a given date using public district web pages, alerts, and calendar PDFs.

## Stack

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + SQLAlchemy
- Data: PostgreSQL + Redis
- Jobs: Celery
- Storage: local snapshot store with S3-compatible configuration surface
- Local infrastructure: Docker Compose

## Repository Layout

```text
apps/
  api/                  FastAPI app, services, and tests
  web/                  Next.js app
packages/
  shared-types/         Shared TypeScript API/domain types
infrastructure/         Dockerfiles and docker-compose
migrations/             SQL migration files
```

## Local Setup

1. Copy `.env.example` to `.env`.
2. Start infrastructure:

```bash
docker compose -f infrastructure/docker-compose.yml up --build
```

3. Apply the initial migration:

```bash
psql "$DATABASE_URL" -f migrations/001_init.sql
```

4. Run the frontend and API locally if you prefer not to use containers.

API:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Web:

```bash
npm install
npm run dev:web
```

## Architecture Notes

- `POST /api/check` uses a synchronous best-effort flow so the user gets an immediate answer.
- Discovery fetches only the homepage and a bounded set of high-value candidates.
- Results are evidence-first. If evidence is conflicting or weak, the system returns `unclear`.
- Source snapshots are stored with metadata so each inference can be audited.
- Manual overrides supersede inferred results for the matching district and date.

## Core Backend Modules

- `app/services/url_safety.py`: URL normalization, SSRF controls, domain canonicalization
- `app/services/fetcher.py`: respectful HTTP fetching, robots handling, snapshot storage
- `app/services/discovery.py`: candidate extraction, ranking, CMS fingerprint hints
- `app/services/parser.py`: HTML/PDF parsing and date candidate extraction
- `app/services/normalizer.py`: rule-based status mappings
- `app/services/inference.py`: precedence, conflict resolution, and explanation building
- `app/services/checker.py`: request orchestration and persistence

## Testing

Run API tests with:

```bash
cd apps/api
pytest
```

The tests cover URL safety, source discovery ranking, HTML/PDF parsing behavior, label normalization, and inference precedence/conflicts. A small golden fixture set is included under `apps/api/tests/fixtures`.

