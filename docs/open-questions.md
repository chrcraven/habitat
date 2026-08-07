# Open Questions

A running list of unresolved decisions. This list is expected to grow and
shrink over time — when a question is resolved, move the decision (and
rationale) into the relevant doc (`data-model-notes.md`, `vision.md`, etc.)
and either remove it here or mark it resolved with a pointer.

## Recently resolved

Kept here briefly for context; full rationale lives in the linked docs, not
here.

- **Public visibility default.** Activity records are public by default.
  See `data-model-notes.md` and `roadmap.md` Phase 2. Still open: any
  private/override mechanism, and the sharper sensitive-species privacy
  question for sightings (see "Public-facing behavior" below).
- **Sightings vs. interventions: separate tables, explicitly linked.** Not
  merged into one record type, but sightings can be linked to the
  activities that respond to them (e.g., a Field Bindweed sighting linked
  to its treatment). See `data-model-notes.md` and `use-cases.md` (f).
  Still open: link cardinality and schema (see "Data model" below).
- **Account model: one Habitat instance/account = one organization or
  manager**, which may represent a single individual ("organization of
  one") or a full multi-property, multi-contributor organization. No
  separate individual-vs-org account types. See `data-model-notes.md`.
  Still open: permission granularity within an account, and how much
  org-management UI a one-person account sees by default (see "Accounts,
  orgs, and permissions" below).
- **Species/treatment data: structured, reference-backed direction.**
  Species should resolve against a reference list/taxonomy rather than
  staying free text, with free text as a fallback/detail field. See
  `data-model-notes.md`. Still open: which reference source(s) to use.
- **Geospatial engine: PostgreSQL + PostGIS**, decided rather than just
  converged-on, with GIS interoperability (GeoJSON/Shapefile/KML/GeoPackage
  export, and eventually import) as an explicit requirement so Habitat data
  can be used in QGIS/ArcGIS and similar tools. See `data-model-notes.md`
  and `tech-stack-options.md`. Still open: import support beyond export.
- **Application framework: Django + GeoDjango, React + MapLibre GL**,
  chosen over the Node/TypeScript and Supabase alternatives, largely on the
  strength of GeoDjango's built-in GIS interoperability and Django REST
  Framework's fit for the Phase 4 public API. See `tech-stack-options.md`.

## Data model

- **Status lifecycle beyond planned/done.** Is a third state
  (in-progress) needed from the start? Is the state set fixed, or should
  organizations be able to define their own workflow states? (See
  `data-model-notes.md`.)
- **Sighting-to-activity link schema.** Now that sightings and activities
  are separate, explicitly linked record types (`use-cases.md` (f)), what's
  the link's cardinality (one-to-many, many-to-many)? Is linking ever
  suggested/automatic, or always manual? Does a linked sighting's status
  change once addressed? (See `data-model-notes.md`.)
- **Which species reference source(s) to use** for the now-structured
  species/treatment fields — a regional native plant database, an existing
  taxonomy (GBIF, USDA PLANTS), something else, or a combination depending
  on region? (See `data-model-notes.md`.)
- **What exactly is a "property" or "parcel"?** Does it need to map to a
  real-world legal parcel (e.g., via cadastral/GIS parcel data), or is it
  just an arbitrary user-drawn area with a name? This affects how precisely
  Habitat can integrate with external parcel/GIS data later, and how
  meaningful GIS import (bringing in an existing parcel survey) can be.

## Accounts, orgs, and permissions

- **How do permissions work for organizations with multiple
  contributors?** Per-property scoping? Role-based (admin/editor/viewer)?
  Does a volunteer need different permissions than staff? (See
  `use-cases.md` (d).)
- **How much organization-management UI does a one-person account see by
  default?** The account model is uniform (see "Recently resolved" above),
  but a single homeowner shouldn't be confronted with invite/role-management
  screens they'll never use.
- **Can a property (and its history) move from one account to another** —
  e.g., a homeowner's property gets formally adopted into a land trust's
  program? What happens to existing records, public page, and prior
  contributors' access?

## Public-facing behavior

- **Sensitive sighting privacy.** Sightings are public by default like
  activities, but reports of sensitive/at-risk species (e.g., an
  endangered species' exact location) are a known case where public
  geolocation data can cause real harm (poaching, disturbance, collection).
  Does this need a private/obscured-location option, and is it
  per-sighting, per-species (an auto-flagged sensitive-species list), or an
  account-manager judgment call? Likely needs resolving before Phase 5
  public input, and possibly before general Phase 2 rollout if the account
  owner already logs sensitive sightings. (See `data-model-notes.md`.)
- **Licensing of public data.** If/when Habitat data is exposed publicly or
  via API, under what terms? (e.g., a specific open data license, all
  rights reserved by default with opt-in sharing, something else.) This
  matters especially for Phase 4 (API), any GIS-format export/import (see
  "Tech / infrastructure" below), and any citizen-science use of Phase 5
  public input.

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

- **GIS import, not just export.** Export to GeoJSON/Shapefile/KML/
  GeoPackage is planned (see "Recently resolved" above); import of
  externally-sourced GIS data (e.g., an organization's existing parcel
  survey, a property boundary from a county GIS office) is a real future
  need but not yet scoped — likely a Phase 3/4-era concern rather than
  Phase 1.
- **Hosting/ops model** — self-hosted vs. managed services, and how that
  choice affects cost as usage scales from one user to many organizations.
- **Photo/media storage** — where photos live (object storage vs.
  database), retention, size/format handling — not addressed yet.
