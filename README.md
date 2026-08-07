# Habitat

**Status: early planning.** No application code exists yet. This repository
currently holds only planning documentation.

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

This project is in **Phase 0: planning**. The author's own native plant
restoration and yard management project is the intended first real use case
(dogfooding), starting with a single-user MVP before anything about
multi-tenancy, public views, or an API is built. See
[docs/roadmap.md](docs/roadmap.md) for the phased plan.

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
  multi-tenancy, and a future public API. No stack has been chosen yet.
- [`docs/roadmap.md`](docs/roadmap.md) — phased plan from planning through
  single-user MVP, public view, multi-tenant/organization support, API, and
  public input.
- [`docs/open-questions.md`](docs/open-questions.md) — running list of
  unresolved decisions. Check here before assuming something has been
  decided.

## Contributing

There's no code to contribute to yet. At this stage, the most useful
contribution is feedback on the docs above — particularly anything flagged
in `docs/open-questions.md`.

## License

[MIT](LICENSE)
