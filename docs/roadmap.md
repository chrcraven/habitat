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
organization that already supports multiple users, sees the full
organization-management UI, and uses the same role-based permission model
as any larger account (see `data-model-notes.md`); Phase 1 just doesn't
exercise most of it yet.

- Build on the chosen stack: Django + GeoDjango on PostgreSQL + PostGIS,
  React + MapLibre GL frontend (see `tech-stack-options.md`).
- Auth: email/password login for users (decided — see
  `open-questions.md`); API-key auth arrives with the API in Phase 4.
- Implement activity records: type, status (planned/done at minimum, with
  the full state set org-defined rather than fixed — see
  `data-model-notes.md`), drawn-boundary geometry, date(s),
  species/treatment details (resolved against the account's own
  self-defined species list), photos (stored in the database — decided),
  notes.
- Implement sighting records: species (same account-defined list),
  point location (device capture), timestamp, photos, notes.
- Account model: one account = one organization/manager (see
  `data-model-notes.md`). Multiple properties and multiple users are both
  supported structurally from day one — the author's account will likely
  use just one property and one contributor at first, but neither is a
  ceiling baked into the model. Property boundaries are user-drawn, not
  tied to legal parcel data.
- Sighting-to-activity linking and tasks (see `use-cases.md` (f) and (g),
  `data-model-notes.md`): a sighting can be linked directly to one or more
  activities (many-to-many), and a task can be created and assigned to a
  contributor as a separate, optional to-do. Neither is automatic in Phase
  1 — no rule wires a sighting to a task or a task to a link. That's
  exactly the manual behavior a rules engine automates later (Phase 4), so
  it's built as the real mechanism here, not a placeholder.
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
  default-behavior question (see `data-model-notes.md`) needs an answer
  first.
- The per-record public/private flag (decided — see `data-model-notes.md`)
  needs to actually exist in the UI before rollout: a way to mark any
  individual activity or sighting private, overriding the public-by-default
  stance for that one record.

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
  contributors actively using the account together, with role-based
  permissions scopable to specific properties (decided — see
  `data-model-notes.md`; exact role definitions still open, see
  `open-questions.md`).
- Task assignment becomes meaningfully used here: the same task mechanism
  from Phase 1 (already built for user-to-user assignment) gets exercised
  for real — routing a sighting-related to-do to a specific teammate
  instead of defaulting to self-assignment (`use-cases.md` (g)).
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
- A configurable rules engine, automating what's manual from Phase 1
  onward: conditions (species, location within a property or an existing
  activity's boundary) trigger actions — auto-create a task, auto-create
  the sighting-activity link, or call an external webhook (see
  `use-cases.md` (h) and `data-model-notes.md`). Webhooks are the
  push-based counterpart to the pull-based API above, aimed first at an
  organization's own internal tooling and later at third-party
  integrations.
- API access control via API keys (decided baseline — see
  `open-questions.md`); issuance/rotation mechanics and whether OAuth or
  scoped tokens get added later are still open.

## Phase 5 — Public input (mechanism TBD)

Goal: the public can contribute to the record, not just view it — closing
the loop implied by the vision, but deliberately left undefined until
earlier phases surface what's actually useful.

- What "public input" means is not decided: candidates include public
  sighting submissions, requests/suggestions tied to a property, feedback
  on completed work, or citizen-science-style structured observations.
- Likely needs moderation/review before public input affects the visible
  record, especially for organization accounts managing public or
  quasi-public land. The task mechanism from Phase 1 (`data-model-notes.md`,
  `use-cases.md` (g)) is a plausible home for that moderation step — a
  public-submitted sighting could generate a task a land manager triages
  before it becomes actionable — but that's not designed in detail yet
  (see `open-questions.md`).
- The sighting-to-activity linking built for the account owner's own use
  starting in Phase 1 becomes especially valuable here regardless — a
  public-submitted sighting, once reviewed, can be linked to the activity
  that addresses it and turn into a visible management response
  ("reported by a visitor, treated on this date").
- This phase intentionally comes last: it depends on having a stable data
  model, a working public view, and (likely) organization support already
  in place, so public contributions have somewhere real to go.
