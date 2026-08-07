# Open Questions

A running list of unresolved decisions. This list is expected to grow and
shrink over time — when a question is resolved, move the decision (and
rationale) into the relevant doc (`data-model-notes.md`, `vision.md`, etc.)
and either remove it here or mark it resolved with a pointer.

## Recently resolved

Kept here briefly for context; full rationale lives in the linked docs, not
here.

- **Public visibility default and override.** Activity and sighting
  records are public by default, and every individual record — not just an
  account- or property-wide setting — carries its own public/private flag,
  so any one record can be marked private regardless of the default. See
  `data-model-notes.md` and `roadmap.md` Phase 2. Still open: whether the
  flag is binary or has more states, who can set/change it, and the
  sharper sensitive-species default-behavior question for sightings (see
  "Public-facing behavior" below).
- **Sightings vs. interventions: separate tables, explicitly linked via a
  task.** Not merged into one record type. A sighting spawns a **task** —
  an assignable work item — and resolving that task is what links the
  sighting to a new or existing activity (e.g., a Field Bindweed sighting
  → a task → a linked treatment). See `data-model-notes.md` and
  `use-cases.md` (f) and (g). Still open: task lifecycle states, whether a
  task is a required or optional step, and link cardinality (see "Data
  model" below).
- **Account model: one Habitat instance/account = one organization or
  manager**, which may currently have one contributor or many — every
  account supports multiple users and multiple properties from creation,
  with no separate individual-vs-org account types and no migration step
  to unlock multi-user support. See `data-model-notes.md`. Still open:
  permission granularity within an account, and how much org-management UI
  a one-contributor account sees by default (see "Accounts, orgs, and
  permissions" below).
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
- **Sighting-to-activity link cardinality.** Now that the link is populated
  via a resolved task (`use-cases.md` (f), (g)), is it one-to-many or
  many-to-many — can one task/activity address several sightings, and can
  one sighting end up related to more than one activity over time (e.g.,
  an initial treatment and a follow-up)? (See `data-model-notes.md`.)
- **Task lifecycle and rules.** Exact status states (open/assigned/resolved
  at minimum, plus dismissed); whether a task is a *required* step for
  every sighting-to-activity link or an *optional* shortcut a land manager
  can bypass; whether task creation from a sighting is automatic or
  something a user triggers; how/whether assignment notifications work.
  (See `data-model-notes.md`.)
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

- **Sensitive sighting default behavior.** The per-record public/private
  flag (decided — see "Recently resolved" above) covers the mechanism, but
  not the harder question: for a sighting of a sensitive/at-risk species
  (e.g., an endangered species' exact location, where public geolocation
  data can cause real harm — poaching, disturbance, collection), should the
  private flag be auto-suggested or auto-set based on a known
  sensitive-species list, rather than relying on whoever logs the sighting
  to remember to flag it themselves? Likely needs resolving before Phase 5
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
  quality issue. Current direction: the task mechanism (see "Data model"
  above and `data-model-notes.md`) is intended to double as this
  moderation step, but that hasn't been designed in detail — e.g., does a
  publicly-submitted sighting's task get auto-assigned to someone, sit in
  an unassigned queue, or something else?

## Auth and API

- **Auth model.** Email/password, social login, magic link, something
  else? Same question for API access (API keys vs. OAuth vs. scoped
  tokens) — see `roadmap.md` Phase 4.
- **API design: REST or GraphQL (or both)?** Not evaluated in depth yet in
  `tech-stack-options.md` — worth a closer look once Phase 4 is nearer.
- **Rate limiting / access tiers for third-party API consumers?** Relevant
  once real downstream programs (use case (e)) start relying on the API.

## Automation / rules engine

- **Rule authoring.** Who can define rules — any contributor, or only
  account admins/managers? Per-property or account-wide? (See
  `data-model-notes.md`.)
- **Rule complexity vs. simplicity.** How much conditional logic is
  exposed to users vs. kept as built-in system defaults (e.g., "sighting →
  task" as the fixed Phase 1 default, with true rule configuration
  reserved for larger organizations in Phase 4)?
- **Webhook reliability.** Retries, delivery guarantees, payload
  signing/authentication, rate limiting — real integration-surface
  questions once webhooks exist, not just a data-model detail.
- **Auto-assignment vs. human review.** Does auto-linking a sighting to an
  existing planned activity ever happen with zero human review, or does it
  always still produce a task/notification for someone to confirm (even if
  pre-resolved)? A real tradeoff between convenience and the risk of
  mis-linking a sighting to the wrong planned work. (See
  `use-cases.md` (h).)

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
