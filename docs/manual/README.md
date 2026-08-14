# Habitat user & admin manual

This is the manual for people *using* Habitat — logging in, drawing
properties, recording activities and sightings, managing an organization's
members, and viewing the public site. If you're working on Habitat's code,
start at [`/CLAUDE.md`](../../CLAUDE.md) instead; the docs in [`/docs`](../)
above this folder are the product/architecture design docs. This manual
documents the app as it behaves *today*, for the people who use it.

Habitat is still early (Phase 1 of the roadmap, with a few Phase 2/3 slices
pulled forward — see `/CLAUDE.md`'s "Current phase" section). Some things
described in `/docs/vision.md` and `/docs/roadmap.md` — a real email invite
flow, sensitive-species-aware visibility, a public API — don't exist yet.
Each chapter below notes what's not built where it matters, and
[`limitations.md`](limitations.md) collects the full list in one place.

## Chapters

- [Getting started](getting-started.md) — creating an account, logging in,
  and how organizations/accounts work.
- [Properties](properties.md) — drawing a property boundary, editing it,
  the public/private flag, deleting a property.
- [Logging activities](activities.md) — recording restoration work
  (plantings, treatments, removals, etc.), the status workflow, photos.
- [Logging sightings](sightings.md) — recording wildlife observations,
  species, photos.
- [Linking sightings and activities](linking-sightings-activities.md) —
  connecting a sighting to the activity that addressed it, or vice versa.
- [Species list](species.md) — your organization's own species list.
- [Tasks](tasks.md) — simple to-do assignment between org members.
- [Roles and permissions](roles-and-permissions.md) — viewer/editor/admin,
  what each can do, and property-scoped roles.
- [Organization admin](organization-admin.md) — renaming your org, adding
  and removing members, changing roles.
- [Public site](public-site.md) — what the public can see without logging
  in, and how to control it.
- [Limitations & known gaps](limitations.md) — what Habitat doesn't do yet.

## Keeping this manual current

This manual is a checked-in part of the repo, not a wiki — it's meant to be
updated in the same session/PR that changes user-facing behavior, the same
way `/CLAUDE.md`'s task log is. See the "Working conventions" note in
`/CLAUDE.md` for the rule that governs this.

The screenshots in `images/` are generated, not hand-captured — see
[`screenshots/`](screenshots/) for the Playwright script that produces
them (`screenshots/capture.js`) and its setup instructions
(`screenshots/README.md`). Re-run it whenever a UI change makes an
existing screenshot stale, and update the script itself (don't
re-derive it from scratch next session) if the flow it walks needs to
change.
