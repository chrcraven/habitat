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
"Single-user" describes Phase 1's actual usage, not a limit of the account
model — every account, including the author's, is structurally an
organization that already supports multiple users (see
`data-model-notes.md`); Phase 1 just doesn't build the invite/permission UI
to make use of that yet.

- Build on the chosen stack: Django + GeoDjango on PostgreSQL + PostGIS,
  React + MapLibre GL frontend (see `tech-stack-options.md`).
- Implement activity records: type, status (at minimum planned/done),
  drawn-boundary geometry, date(s), species/treatment details, photos,
  notes.
- Implement sighting records: species, point location (device capture),
  timestamp, photos, notes.
- Account model: one account = one organization/manager (see
  `data-model-notes.md`). Multiple properties and multiple users are both
  supported structurally from day one — the author's account will likely
  use just one property and one contributor at first, but neither is a
  ceiling baked into the model.
- Sighting-to-activity linking (see `use-cases.md` (f)): the author's own
  sightings can be tied to the activities that respond to them, laying the
  groundwork for the reported → responded-to loop Phase 5 depends on.
- No public-facing view yet in this phase; focus is the logging experience
  for one user.

## Phase 2 — Public view of planned + completed work

Goal: someone other than the account owner can see what's happening on the
land without an account.

- A public, map-based view of a property showing activity — visually
  distinguishing planned/upcoming work from completed work (per
  `use-cases.md` (c)).
- Activity records are public by default (decided — see
  `data-model-notes.md`); this phase is about building the view, not
  deciding whether to show it.
- Sighting data may or may not be part of the public view at this stage —
  TBD (see `open-questions.md`), and if it is, the sensitive-species
  privacy question (see `data-model-notes.md`) needs an answer first.
- A minimal private-override mechanism (at least an all-or-nothing
  visibility toggle per property or per record) is still needed before
  rollout, for anything the default-public stance shouldn't cover.

## Phase 3 — Multi-user / organization depth

Goal: the platform supports other accounts (individuals and larger
organizations), and accounts actually make use of the multi-user capacity
that's been structurally present since Phase 1, at real scale (per
`use-cases.md` (d)). This phase isn't introducing multi-user support for
the first time — every account already supports multiple users (see
`data-model-notes.md`) — it's building the invite flow, permission depth,
and contributor-management UI needed to use that in practice, plus
onboarding other accounts.

- Other individuals (and the author, if they choose) can invite additional
  contributors into their own account — no different in kind from a
  larger organization inviting staff, just fewer people.
- Other individual homeowners can create their own accounts and use
  Habitat the same way the author does.
- Larger organization accounts: multiple properties/parcels, multiple
  contributors actively using the account together, with a real permission
  model (exact shape TBD — see `data-model-notes.md` and
  `open-questions.md`).
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
- Standard GIS format export (GeoJSON, Shapefile, KML/GeoPackage) alongside
  the API's native JSON, so data can flow into QGIS/ArcGIS and similar
  tools, not just other programs (see `data-model-notes.md` and
  `tech-stack-options.md`).
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
- The sighting-to-activity link built for the account owner's own use in
  Phase 1 (`use-cases.md` (f)) becomes especially valuable here — a
  public-submitted sighting can flow into the same linking mechanism,
  turning public input into a visible management response ("reported by a
  visitor, treated on this date").
- This phase intentionally comes last: it depends on having a stable data
  model, a working public view, and (likely) organization support already
  in place, so public contributions have somewhere real to go.
