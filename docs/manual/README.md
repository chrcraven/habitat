# Habitat user & admin manual

This is the manual for people *using* Habitat — logging in, drawing
properties, recording activities and sightings, managing an organization's
members, and viewing the public site. If you're working on Habitat's code,
start at [`/CLAUDE.md`](../../CLAUDE.md) instead; the docs in [`/docs`](../)
above this folder are the product/architecture design docs. This manual
documents the app as it behaves *today*, for the people who use it.

Habitat is still early (Phase 1 of the roadmap, with a few Phase 2/3 slices
pulled forward — see `/CLAUDE.md`'s "Current phase" section). Some things
described in `/docs/vision.md` and `/docs/roadmap.md` — a real, deliverable
invite email (the invite flow itself exists — see [Organization
admin](organization-admin.md#adding-a-member) — but no production email
service is configured yet), sensitive-species-aware visibility, a public
API — don't exist yet. Each chapter below notes what's not built where it
matters, and [`limitations.md`](limitations.md) collects the full list in
one place.

## Chapters

- [Getting started](getting-started.md) — creating an account, logging in,
  and how organizations/accounts work.
- [Your dashboard](dashboard.md) — the landing page after logging in:
  your tasks, upcoming work, and recent activity/sighting logs.
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
- [Manage](organization-admin.md) — your properties and species list,
  plus renaming your org, adding
  and removing members, changing roles.
- [Your account](account.md) — changing your own password.
- [Public site](public-site.md) — what the public can see without logging
  in, and how to control it.
- [Limitations & known gaps](limitations.md) — what Habitat doesn't do yet.

## Keeping this manual current

This manual is a checked-in part of the repo, not a wiki — it's meant to be
updated in the same session/PR that changes user-facing behavior, the same
way `/CLAUDE.md`'s task log is. See the "Working conventions" note in
`/CLAUDE.md` for the rule that governs this.

**Every chapter links to the next one, in the order listed above** — a
`---` followed by `[← Previous](prev.md) · [Manual index](README.md) ·
[Next →](next.md)` at the bottom of each file (the first chapter has no
`← Previous`; the last, `limitations.md`, has no `Next →`), so a reader
can start at [Getting started](getting-started.md) and click straight
through the whole manual without coming back to this index. **When you add
a new chapter, splice it into this chain** — update the chapter list
above, add the new file's own prev/next footer, and fix the two
neighboring chapters' footers to point at it instead of each other.

The screenshots in `images/` are generated, not hand-captured — see
[`screenshots/`](screenshots/) for the Playwright script that produces
them (`screenshots/capture.js`) and its setup instructions
(`screenshots/README.md`). Keep the script itself accurate as soon as a
UI change would make it produce something wrong, but actually *running*
it and committing refreshed PNGs is capped at **once per calendar
date**, not once per session — see `/CLAUDE.md`'s "Keep the user manual
current" section for the reasoning and the exact rule.
