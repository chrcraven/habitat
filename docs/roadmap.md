# Roadmap

A rough phased plan. Phases are sequential in emphasis, not necessarily
strictly sequential in execution — some overlap is expected. Nothing here
is a committed timeline; there are no dates attached yet.

## Phase 0 — Planning (current phase)

- Define the problem, audience, and success criteria (`vision.md`).
- Write concrete use cases across the individual, public, organizational,
  and API-consumer scales (`use-cases.md`).
- Think through the data model at a conceptual level, without locking a
  schema (`data-model-notes.md`).
- Survey candidate tech stacks against Habitat's specific requirements,
  especially geospatial handling (`tech-stack-options.md`).
- Capture open questions rather than force premature decisions
  (`open-questions.md`).
- Output of this phase: this repository's documentation. No application
  code.

## Phase 1 — Single-user MVP

Goal: the author can log their own native plant restoration and yard
management activity and get real value from it, replacing ad hoc tracking.

- Pick a tech stack (informed by, not necessarily identical to, the
  candidates in `tech-stack-options.md`).
- Implement activity records: type, status (at minimum planned/done),
  drawn-boundary geometry, date(s), species/treatment details, photos,
  notes.
- Implement sighting records: species, point location (device capture),
  timestamp, photos, notes.
- Single-user account model (even if designed to later generalize to
  organizations — see `data-model-notes.md`).
- No public-facing view yet in this phase; focus is the logging experience
  for one user.

## Phase 2 — Public view of planned + completed work

Goal: someone other than the account owner can see what's happening on the
land without an account.

- A public, map-based view of a property showing activity — visually
  distinguishing planned/upcoming work from completed work (per
  `use-cases.md` (c)).
- Sighting data may or may not be part of the public view at this stage —
  TBD (see `open-questions.md`).
- Some notion of what's public vs. private needs to exist by this point,
  even if minimal (e.g., an all-or-nothing visibility toggle per property
  or per record, rather than granular controls).

## Phase 3 — Multi-user / organization support

Goal: the platform supports more than one account, and accounts that need
multiple properties and multiple contributors (per `use-cases.md` (d)).

- Other individual homeowners can create their own accounts and use Habitat
  the same way the author does.
- Organization accounts: multiple properties/parcels under one account,
  multiple users contributing, with some permission model (exact shape
  TBD — see `data-model-notes.md` and `open-questions.md`).
- Public views need to work at both the single-property and
  organization-portfolio level.

## Phase 4 — API for other programs

Goal: third-party programs can consume Habitat data programmatically (per
`use-cases.md` (e)).

- A documented, versioned public API — deliberately not just exposing
  whatever auto-generated API the chosen backend happens to produce (see
  `tech-stack-options.md`).
- Supports both small-scale (single individual's data, with permission) and
  large-scale (organization portfolio) consumption.
- Geospatial querying/filtering exposed through the API (e.g., "activity
  within this area"), not just record-by-ID lookups.
- Some form of API access control (keys, OAuth, scoped tokens) — mechanism
  TBD.

## Phase 5 — Public input (mechanism TBD)

Goal: the public can contribute to the record, not just view it — closing
the loop implied by the vision, but deliberately left undefined until
earlier phases surface what's actually useful.

- What "public input" means is not decided: candidates include public
  sighting submissions, requests/suggestions tied to a property, feedback
  on completed work, or citizen-science-style structured observations.
- Likely needs moderation/review before public input affects the visible
  record, especially for organization accounts managing public or
  quasi-public land.
- This phase intentionally comes last: it depends on having a stable data
  model, a working public view, and (likely) organization support already
  in place, so public contributions have somewhere real to go.
