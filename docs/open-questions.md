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
- **Property also got its own public/private flag** (`Property.is_public`,
  default `true`), on top of the per-record flag above — added when the
  Phase 2 public site was actually built, once it became clear an org
  managing one public property and one private one (e.g. a land trust's
  preserve alongside a manager's own yard) needs to keep the private one
  off the public site entirely, not rely on marking every record private
  one at a time. See `data-model-notes.md`.
- **The Phase 2 public site is built**, in two shapes: a per-property page
  and a per-organization "portfolio" page (linked from the logged-in
  app's nav as "Public site", plus a link on the org admin portal), both
  unauthenticated (`backend/apps/public_site/`) and both offering a way
  back to `/login`. URLs are plain numeric IDs
  (`/public/org/<id>`, `/public/properties/<id>`) — no slug/vanity URL
  yet, see "Tech / infrastructure" below.
- **Sightings vs. interventions: separate tables, connected by a direct
  many-to-many link — not gated behind a task.** A sighting links straight
  to one or more activities (and vice versa); a **task** is a separate,
  optional, assignable to-do (see below) that doesn't have to be involved
  at all. See `data-model-notes.md` and `use-cases.md` (f). **The link is
  now reachable from the app, not just the schema** — a "Linked
  activities"/"Linked sightings" section on each record's edit page lets
  you create or remove the link directly (`/api/sightings/<id>/links/`
  and the `/api/activities/<id>/links/` mirror of it).
- **Task model: optional, and intentionally simple in the initial
  build.** A task is plain user-to-user assignment (any contributor can
  assign a task to any other, or to themselves) — not a required step for
  linking a sighting to an activity, and not automatically created when a
  sighting is logged. See `data-model-notes.md` and `use-cases.md` (g).
  **Now has a real API + UI** — `/api/tasks/` (org-scoped CRUD, same
  viewer/editor/admin convention as everything else) and a `/tasks` page
  (list with status filter, inline status/assignee change, create form
  optionally tied to an existing sighting or activity). Still open: exact
  status states beyond the current fixed
  open/assigned/resolved/dismissed set, and notification mechanics (see
  "Data model" below) — nothing pings the assignee today, they just have
  to check the Tasks page.
- **Status lifecycle beyond planned/done: org-defined, not a fixed global
  enum.** Each account/organization can define its own workflow states
  rather than Habitat imposing one status set on everyone. See
  `data-model-notes.md`. Still open: sensible defaults for a brand-new
  account, and whether planned/done-equivalents are reserved states every
  custom workflow must map onto (see "Data model" below).
- **Species/treatment reference data: account-defined, not an external
  taxonomy.** Each account maintains its own species list, defined by
  whoever manages that account, rather than Habitat integrating an outside
  standard (GBIF, USDA PLANTS) from the start. See `data-model-notes.md`.
- **What a "property" or "parcel" is: user-drawn, not tied to a legal
  parcel.** Habitat doesn't require or validate against cadastral/parcel
  data — a property is whatever area a user draws and names, which will
  often approximate real property lines without being sourced from them.
  See `data-model-notes.md`.
- **Account model: one Habitat instance/account = one organization or
  manager**, which may currently have one contributor or many — every
  account supports multiple users and multiple properties from creation,
  with no separate individual-vs-org account types and no migration step
  to unlock multi-user support. See `data-model-notes.md`.
- **Organization-management UI: uniform for every account, regardless of
  size.** A one-person account sees the same invite/role/property-
  management UI a large organization does, rather than Habitat hiding that
  complexity for small accounts. See `data-model-notes.md`.
- **Permissions: role-based, with roles scopable to specific properties.**
  The role set is fixed at three — **viewer** (read only), **editor**
  (read/create/update), **admin** (also delete, and manage org
  membership/roles) — enforced backend-side via
  `OrganizationRolePermission`/`ensure_role`
  (`backend/apps/accounts/org_scoping.py`); the frontend only hides
  controls a role can't use. Property scoping
  (`Membership.properties` — leave empty for account-wide, or select
  specific properties to limit a role to just those) is enforced the same
  way. An org admin manages both through the in-app org admin portal
  (`/admin`, admin-only) — see `data-model-notes.md`. New members are
  added by an admin setting an initial password directly and sharing it
  out of band, not a real email-invite flow (no email backend is
  configured yet — see "Auth and API" below for that gap). **That new
  member can now change their own password afterward** via a self-service
  `/account` page (`POST /api/auth/change-password/`, requires the
  current password, keeps the session alive via
  `update_session_auth_hash`) — the admin-set password no longer has to
  be permanent.
- **Auth model: email/password for users, API keys for API access.**
  Human users log in with email/password; third-party API consumers
  authenticate with an API key rather than a user-facing login flow. See
  `roadmap.md` Phase 1 and Phase 4. Still open: whether social login or
  other user-auth options get added later, and API key issuance/rotation
  mechanics (see "Auth and API" below).
- **Photo/media storage: in the database**, not external object storage.
  See `data-model-notes.md` and "Tech / infrastructure" below for the
  operational follow-up this raises (storage growth, backups).
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

- **Default workflow states for a brand-new account.** Status states are
  org-defined (see "Recently resolved" above), but a solo homeowner
  shouldn't have to design a workflow just to log a planting — what's the
  sensible out-of-the-box default (e.g., planned → in-progress → done)
  every new account starts with, that they can customize later if they
  want to?
- **Are planned/done-equivalent states reserved?** Since the public view
  depends on the planned-vs-done distinction, does every org-defined
  workflow have to designate which of its custom states map onto
  "planned" and "done," or is that requirement looser than it sounds?
- **Task status states.** Beyond a rough open → assigned → resolved (plus
  dismissed) shape, what's the actual state set, and are they fixed or
  also org-customizable like activity states? (See `data-model-notes.md`.)
- **Notification mechanism when a task is assigned to someone.** (See
  `data-model-notes.md`.)
- **Should the public-facing view surface the sighting ↔ activity link**
  (e.g., "reported by a visitor, treated on this date")? A good showcase
  of the public-input → management-action loop, but not decided. (See
  `data-model-notes.md`.)
- **Does Habitat ship any starter species list**, or does every new
  account's species reference start completely empty? Relevant given
  species data is now account-defined rather than pulled from an external
  taxonomy (see "Recently resolved" above).

## Accounts, orgs, and permissions

- **Can a property (and its history) move from one account to another** —
  e.g., a homeowner's property gets formally adopted into a land trust's
  program? What happens to existing records, public page, and prior
  contributors' access? **Explicitly deferred** — judged too open-ended to
  resolve now; revisit if/when it becomes a real, concrete need rather than
  a hypothetical.

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
  quality issue. The task mechanism (see "Data model" above and
  `data-model-notes.md`) is a plausible fit for this, but no longer the
  only mechanism sightings flow through now that sighting-activity linking
  doesn't require a task — this needs its own look once Phase 5 is nearer.

## Auth and API

- **Whether to add social login or other user-auth options** beyond the
  decided email/password baseline (see "Recently resolved" above).
- **Real email-invite flow for new org members.** An admin can add a
  member today by setting their initial password directly and sharing it
  out of band (see "Accounts, orgs, and permissions" above) — deliberately
  chosen over building email infrastructure (SMTP backend, signed invite
  tokens) in the same session as the rest of the org admin portal. Worth
  revisiting once there's a real need to invite someone without an
  existing out-of-band channel to share a password over.
- **API key issuance and rotation mechanics** — how an account generates,
  scopes, and revokes API keys (see `roadmap.md` Phase 4).
- **API design: REST or GraphQL (or both)?** Not evaluated in depth yet in
  `tech-stack-options.md` — worth a closer look once Phase 4 is nearer.
- **Rate limiting / access tiers for third-party API consumers?** Relevant
  once real downstream programs (use case (e)) start relying on the API.

## Automation / rules engine

- **Rule authoring.** Who can define rules — any contributor, or only
  account admins/managers? Per-property or account-wide? (See
  `data-model-notes.md`.)
- **Rule complexity vs. simplicity.** How much conditional logic is
  exposed to users, given that the Phase 1 baseline has no automation at
  all (task creation and sighting-activity linking are always manual until
  a rules engine exists)? (See `data-model-notes.md`.)
- **Webhook reliability.** Retries, delivery guarantees, payload
  signing/authentication, rate limiting — real integration-surface
  questions once webhooks exist, not just a data-model detail.
- **Auto-linking vs. human review.** Does a rule auto-creating a
  sighting-activity link, or auto-assigning a task, ever happen with zero
  human review, or does it always still produce a notification for someone
  to confirm (even if the action already happened)? A real tradeoff
  between convenience and the risk of a wrong automatic link or
  assignment. (See `use-cases.md` (h).)

## Tech / infrastructure

- **Photo storage growth.** Photos are stored in the database, not
  external object storage (decided — see "Recently resolved" above). That
  keeps ops simple early on, but raises real questions once volume grows:
  database size, backup time/cost, and whether any compression or size
  limit is needed — especially at large-organization scale (many
  properties, many contributors, years of photos). Not addressed yet.
- **GIS import, not just export.** Export to GeoJSON/Shapefile/KML/
  GeoPackage is planned (see "Recently resolved" above); import of
  externally-sourced GIS data (e.g., an organization's existing parcel
  survey, a property boundary from a county GIS office) is a real future
  need but not yet scoped — likely a Phase 3/4-era concern rather than
  Phase 1.
- **Hosting/ops model** — self-hosted vs. managed services, and how that
  choice affects cost as usage scales from one user to many organizations.
- **Public URLs are plain numeric IDs**, not slugs
  (`/public/org/<id>`, `/public/properties/<id>` — see "Public-facing
  behavior" above). Fine for now; a slug (`/public/org/mira-canyon-trust`)
  would read better on a business card or shared link later.
