# Habitat

**Status: Phase 1 (single-user MVP) build in progress.** Planning docs live
in `docs/`; application code is starting to land in `backend/` and
`frontend/`. See [`CLAUDE.md`](CLAUDE.md) for a working index of decisions
and in-progress state (kept up to date across work sessions).

## What is Habitat?

Habitat is a planned web application for land management. It lets an
individual land manager — starting with a homeowner doing native plant
restoration on their own property — log and track what they're doing to a
piece of land (plantings, treatments, restoration work, wildlife
observations), and it turns that same record into something the public can
see: what's happening on this land, what's planned, and what's already been
done. The same data model and platform are meant to work whether one person
is tracking a backyard or a land trust is coordinating work across dozens of
properties and contributors, with a future API so other programs can build
on top of it.

## Project status

Planning (Phase 0) is done; the project is now in **Phase 1: single-user
MVP**. The author's own native plant restoration and yard management
project is the first real use case (dogfooding), starting with a
single-user MVP before anything about multi-tenancy, public views, or an
API is built. See [docs/roadmap.md](docs/roadmap.md) for the phased plan.

## Navigating this repo

All planning docs live in [`docs/`](docs):

- [`docs/vision.md`](docs/vision.md) — the problem, who this is for, what
  success looks like.
- [`docs/use-cases.md`](docs/use-cases.md) — concrete user stories across the
  individual, public, organizational, and API-consumer scales.
- [`docs/data-model-notes.md`](docs/data-model-notes.md) — early, unlocked
  thinking on what activity records and sighting records need to capture,
  and how accounts/ownership scale from one person to an organization.
- [`docs/tech-stack-options.md`](docs/tech-stack-options.md) — candidate
  technology stacks, evaluated against geospatial storage, map-drawing UI,
  multi-tenancy, and a future public API. Stack is decided (Django +
  GeoDjango + PostGIS, React + MapLibre GL).
- [`docs/roadmap.md`](docs/roadmap.md) — phased plan from planning through
  single-user MVP, public view, multi-tenant/organization support, API, and
  public input.
- [`docs/open-questions.md`](docs/open-questions.md) — running list of
  unresolved decisions. Check here before assuming something has been
  decided.

## Getting started (local dev)

The stack is Django + GeoDjango + PostGIS on the backend, React + MapLibre
GL on the frontend (see `docs/tech-stack-options.md`). GeoDjango needs
GDAL/GEOS/PROJ system libraries, so local dev is meant to run through
Docker rather than a bare virtualenv:

```sh
cp backend/.env.example backend/.env
docker-compose up
```

- Backend: http://localhost:8000/admin/ (run
  `docker-compose exec backend python manage.py migrate` and
  `... createsuperuser` first)
- Frontend: http://localhost:5173/

Backend code lives in `backend/apps/` (one Django app per model area:
`accounts`, `species`, `activities`, `sightings`, `tasks`). Frontend code
lives in `frontend/src/`.

## Contributing

The most useful contribution at this stage is still feedback on the docs in
`docs/` — particularly anything flagged in `docs/open-questions.md` — plus,
now that code exists, the usual: bug reports, PRs against the Phase 1 scope
in `docs/roadmap.md`.

## License

[MIT](LICENSE)
