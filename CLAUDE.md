# CLAUDE.md

Guidance for Claude Code sessions working in this repository. Read this
first, before the docs in `docs/`, to avoid re-deriving context (and
re-spending tokens) that's already settled. Keep this file current: when a
session makes a decision, resolves an open question, or finishes a chunk of
work, update the relevant section below in the same session.

## What Habitat is

A web app for land management: an individual (starting with the author,
doing native plant restoration on their own property) logs activities and
wildlife sightings against a piece of land; the same data can be shown
publicly. One data model and platform scales from a single yard to a land
trust managing many properties and contributors, eventually with a public
API. Full narrative: `README.md` and `docs/vision.md`.

## Source of truth

- `docs/vision.md` — problem, audience, success criteria.
- `docs/use-cases.md` — concrete stories, referenced as `(a)`, `(b)`, etc.
  throughout the other docs.
- `docs/data-model-notes.md` — the data model, in prose. **Read this before
  touching any model/schema code** — it's more current and more detailed
  than any summary here.
- `docs/tech-stack-options.md` — stack evaluation and the decision.
- `docs/roadmap.md` — phased plan (Phase 0 through Phase 5).
- `docs/open-questions.md` — unresolved decisions. **Check here before
  assuming something is decided.** When a session resolves a question, move
  it from here into the relevant doc's "decided" language and delete it (or
  mark it resolved) here, per that file's own header instructions.

Docs are the durable source of truth for product/architecture decisions;
this file is the fast-load index plus session-to-session working notes.
When they conflict, the dated docs above win — fix this file to match.

## Decided (don't re-litigate — full rationale in the docs above)

- **Stack:** Django + GeoDjango + Django REST Framework, PostgreSQL +
  PostGIS, React + MapLibre GL. See `docs/tech-stack-options.md`.
- **Auth:** email/password for human users; API keys for third-party API
  consumers (Phase 4). No social login yet.
- **Account model:** one account = one organization, always multi-user-
  capable (no separate individual/org account types). Every account gets
  the same org-management UI regardless of headcount.
- **Property:** user-drawn boundary, not tied to legal parcel data. One
  account can hold multiple properties.
- **Permissions:** role-based (admin/editor/viewer-ish, exact set still
  open), roles scopable to specific properties.
- **Activity record:** drawn geometry (not a point), org-defined status
  workflow (planned/done are the only fixed points), species/treatment
  resolved against the account's own species list, photos stored in DB,
  notes, public-by-default with a per-record private flag.
- **Sighting record:** point location, same account species list, photos in
  DB, notes, public-by-default with a per-record private flag. Separate
  table from Activity (different geometry type, different lifecycle).
- **Sighting ↔ Activity link:** direct many-to-many, not gated behind a
  task.
- **Task record:** optional, simple user-to-user assignment; can reference a
  sighting or activity or nothing. Not required for the sighting-activity
  link.
- **Species list:** account-defined, not an external taxonomy (GBIF/USDA).
- **Photo/media storage:** in the database, not S3/object storage.
- **Rules engine, API, public input:** deliberately deferred to Phases 4-5 —
  do not build automation, webhooks, or public API surface in Phase 1.

## Current phase: Phase 1 — single-user MVP

Per `docs/roadmap.md`: the author can log their own activities and
sightings; no public view, no multi-tenant UI depth, no API, no rules
engine yet — even though the underlying models are org/multi-user shaped
from day one. Build the real mechanism (org, property, role, task, link),
just don't build the Phase 2+ features that consume it yet.

## Repo layout

- `docs/` — planning docs (see "Source of truth" above).
- `backend/` — Django + GeoDjango project (Phase 1 build, in progress).
- `frontend/` — React + MapLibre GL app (Phase 1 build, in progress).
- `docker-compose.yml` — local dev: Postgres+PostGIS, backend, frontend.
- `CLAUDE.md` — this file.

## Working conventions for this repo

- This is a solo-author, docs-first project. Before writing code that
  touches product behavior, check `docs/open-questions.md` — if the thing
  you're about to build is listed as open, either pick the narrowest
  reasonable default and note the assumption in this file's task log, or
  ask, rather than silently deciding for the project.
- Model changes: update `docs/data-model-notes.md` if the implementation
  reveals something the notes got wrong or didn't anticipate — the doc
  should stay accurate to the real schema, not frozen at its Phase 0 text.
- Don't build ahead of the current phase (see `docs/roadmap.md`). It's
  tempting to wire up the rules engine or public API while touching
  adjacent code — resist; note the idea in open-questions.md instead if
  it's non-obvious.
- Keep `backend/` and `frontend/` runnable via `docker-compose up` — that's
  the expected local dev path given GeoDjango's system-library
  dependencies (GDAL/GEOS/PROJ).

## How to work in this repo (once code exists)

- Backend: `docker-compose up backend db` (or `docker-compose up`), then
  `docker-compose exec backend python manage.py <command>` for
  migrations/shell/tests. See `backend/README.md` for details once it
  exists.
- Frontend: `docker-compose up frontend`, or `cd frontend && npm install &&
  npm run dev` if Node is available locally.
- Tests: backend `python manage.py test` (or pytest if/when adopted);
  frontend test runner TBD.

## Task log

Reverse-chronological. Each entry: what was done, key decisions/assumptions
made along the way, and what's left. Keep entries short — this is a pointer
for the next session, not a full changelog (git history is that).

### 2026-08-07 — Initial backend + frontend scaffolding, CLAUDE.md

- Added this file.
- Scaffolded `backend/`: Django project (`config/`) + apps `accounts`
  (custom email-based User, Organization, Property, Membership),
  `species` (account-defined Species list), `activities` (Activity,
  ActivityPhoto, ActivitySpecies through model, WorkflowState),
  `sightings` (Sighting, SightingPhoto, SightingActivityLink),
  `tasks` (Task). Models follow `docs/data-model-notes.md` directly;
  see model docstrings for field-level notes/open questions.
- GIS fields use GeoDjango (`PolygonField` for activity geometry,
  `PointField` for sighting location), SRID 4326.
- Photos stored in DB as `BinaryField` + content-type, per the decided
  storage approach — no external object storage or filesystem `MEDIA_ROOT`
  use for these.
- `WorkflowState` is per-Organization with `is_planned`/`is_done` boolean
  flags rather than a fixed enum, per the org-defined-workflow decision.
  **Assumption (not yet in open-questions.md as resolved):** a brand-new
  Organization gets seeded with a default 3-state workflow
  (Planned → In Progress → Done) via a `post_save` signal / data migration,
  so a solo user isn't forced to configure a workflow before logging their
  first activity. This answers one bullet under "Data model" in
  `docs/open-questions.md` — revisit if that default set turns out wrong.
- Scaffolded `frontend/`: Vite + React + TypeScript + MapLibre GL, with a
  minimal map view as the starting shell. No API integration yet — backend
  has no REST endpoints exposed yet either (DRF is installed but no
  serializers/viewsets/urls beyond Django admin).
- Added `docker-compose.yml` (postgis/postgis image + backend + frontend)
  and `backend/Dockerfile` so GDAL/GEOS/PROJ system deps don't have to be
  installed on the host.
- Verified the backend actually works, not just "looks right": installed
  Django + GDAL/GEOS system libs in the sandbox, ran `manage.py check`
  (clean) and `manage.py makemigrations` for real — it generated correct
  migrations for all 5 apps with no errors. Migration files are committed.
  Frontend: `npm install && npm run build` (tsc + vite) succeeds cleanly.
  Neither was run against a *live* Postgres/PostGIS instance (none
  available in this sandbox) — that's still untested.
- **Not done yet:** `migrate` against a live DB (do this first next
  session — `docker-compose up` then
  `docker-compose exec backend python manage.py migrate`); DRF
  serializers/viewsets/API urls; auth wiring (djoser or hand-rolled);
  frontend-backend integration; tests; admin site polish beyond basic
  registration; frontend has no linting configured yet. Next session should
  confirm `docker-compose up` + `migrate` works end to end, then build the
  activity-logging flow (create property → draw activity geometry → save)
  since that's the core of the Phase 1 MVP.
