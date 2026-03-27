# District Status Checker

District Status Checker is a monorepo MVP for determining whether a public school district is in session on a given date using public district web pages, alerts, and calendar PDFs.

## Cheapest Deployable Stack

For a low-traffic pilot, the cheapest practical setup is:

- Frontend: GitHub Pages via GitHub Actions on push
- API: Render free web service
- Database: Render free Postgres
- Redis/background jobs: omitted for initial deployment

This keeps the app deployable without requiring a paid plan while preserving the current backend architecture.

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

## Deploying Cheaply

### Frontend on GitHub Pages

1. In GitHub, enable Pages for this repository and set the source to GitHub Actions.
2. Add a repository variable named `NEXT_PUBLIC_API_BASE_URL` with your deployed API URL, for example `https://inschoolchecker-api.onrender.com`.
3. Push to `main`. The workflow at [`.github/workflows/deploy-pages.yml`](/Users/jethrojones/jethro/lifelab/projects/inschoolchecker/.github/workflows/deploy-pages.yml) builds a static export and publishes it to Pages.

The published site will typically be:

`https://jethrojones.github.io/inschoolchecker/`

### API on Render Free

1. Create a new Blueprint deployment in Render and point it at this repository.
2. Render will detect [`render.yaml`](/Users/jethrojones/jethro/lifelab/projects/inschoolchecker/render.yaml).
3. Provision the free web service and free Postgres instance.
4. After the first deploy, run the SQL migration in [`migrations/001_init.sql`](/Users/jethrojones/jethro/lifelab/projects/inschoolchecker/migrations/001_init.sql) against the Render Postgres database.
5. Set `CORS_ALLOWED_ORIGINS` to your GitHub Pages origin if you change the default hostname.

### Cost Notes

- GitHub Pages: free
- Render free web service: free for hobby/testing with platform limits
- Render free Postgres: free for hobby/testing with platform limits
- No Redis is required for the initial pilot deployment because background jobs are not required for basic checks

## Architecture Notes

- `POST /api/check` uses a synchronous best-effort flow so the user gets an immediate answer.
- Discovery fetches only the homepage and a bounded set of high-value candidates.
- Results are evidence-first. If evidence is conflicting or weak, the system returns `unclear`.
- Source snapshots are stored with metadata so each inference can be audited.
- Manual overrides supersede inferred results for the matching district and date.
- For free-tier deployment, Redis and Celery are optional and can be deferred until recurring refresh jobs are needed.

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
