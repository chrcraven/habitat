# Open Questions

A running list of unresolved decisions. This list is expected to grow and
shrink over time — when a question is resolved, move the decision (and
rationale) into the relevant doc (`data-model-notes.md`, `vision.md`, etc.)
and either remove it here or mark it resolved with a pointer.

## Data model

- **Status lifecycle beyond planned/done.** Is a third state
  (in-progress) needed from the start? Is the state set fixed, or should
  organizations be able to define their own workflow states? (See
  `data-model-notes.md`.)
- **Do sightings and interventions share a data model, or stay fully
  separate?** They clearly differ in location model (point vs. geometry)
  and lifecycle (sightings have no "planned" state) — but do they share a
  common base record (account/property linkage, photos, notes,
  visibility)? (See `data-model-notes.md`.)
- **How structured should species/treatment data be?** Free text, a
  reference-backed picker (e.g., tied to a regional native plant database
  or an existing taxonomy like GBIF), or both depending on context?
- **What exactly is a "property" or "parcel"?** Does it need to map to a
  real-world legal parcel (e.g., via cadastral/GIS parcel data), or is it
  just an arbitrary user-drawn area with a name? This affects how precisely
  Habitat can integrate with external parcel/GIS data later.

## Accounts, orgs, and permissions

- **Is an individual account structurally the same as an organization of
  one, or a genuinely different account type?** Affects how much
  organization-management complexity a single homeowner ever sees.
- **How do permissions work for organizations with multiple
  contributors?** Per-property scoping? Role-based (admin/editor/viewer)?
  Does a volunteer need different permissions than staff? (See
  `use-cases.md` (d).)
- **Can an individual later be invited into / merge into an organization
  account** (e.g., a homeowner's property gets adopted into a formal
  program), and if so, what happens to their existing records and public
  page?

## Public-facing behavior

- **What's public by default, and what requires explicit opt-in?**
  Per-property toggle, per-record visibility, or something more granular
  (e.g., hide exact species/location for sensitive sightings, like rare
  species locations that shouldn't be publicized)?
- **Are sighting records ever public**, or are they private/internal data
  only, distinct from activity records which are the intended public-facing
  content? (Touched on in `roadmap.md` Phase 2 but not resolved.)
- **Licensing of public data.** If/when Habitat data is exposed publicly or
  via API, under what terms? (e.g., a specific open data license, all
  rights reserved by default with opt-in sharing, something else.) This
  matters especially for Phase 4 (API) and any citizen-science use of
  Phase 5 public input.

## Public input (Phase 5)

- **What form does public input actually take?** Candidates: sighting
  submissions from visitors, requests/suggestions on a property, feedback
  on specific completed work, structured citizen-science observations tied
  to a broader project. Not chosen yet — deliberately deferred (see
  `roadmap.md`).
- **Does public input require moderation before affecting the visible
  record?** Especially relevant for organization-managed public/quasi-public
  land, where unmoderated public submissions could be a liability or
  quality issue.

## Auth and API

- **Auth model.** Email/password, social login, magic link, something
  else? Same question for API access (API keys vs. OAuth vs. scoped
  tokens) — see `roadmap.md` Phase 4.
- **API design: REST or GraphQL (or both)?** Not evaluated in depth yet in
  `tech-stack-options.md` — worth a closer look once Phase 4 is nearer.
- **Rate limiting / access tiers for third-party API consumers?** Relevant
  once real downstream programs (use case (e)) start relying on the API.

## Tech / infrastructure

- **Final stack choice** — `tech-stack-options.md` lays out candidates but
  makes no final call. Needs to happen before or early in Phase 1.
- **Hosting/ops model** — self-hosted vs. managed services, and how that
  choice affects cost as usage scales from one user to many organizations.
- **Photo/media storage** — where photos live (object storage vs.
  database), retention, size/format handling — not addressed yet.
