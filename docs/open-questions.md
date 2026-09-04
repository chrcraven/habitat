# Open Questions

A running list of unresolved decisions. This list is expected to grow and
shrink over time — when a question is resolved, move the decision (and
rationale) into the relevant doc (`data-model-notes.md`, `vision.md`, etc.)
and either remove it here or mark it resolved with a pointer.

## Recently resolved

Kept here briefly for context; full rationale lives in the linked docs, not
here.

- **Workflow states are editable in-app** (built 2026-09-03). The
  Phase 1 read-only endpoint became writable with a *Manage → Workflow
  states* section: add, rename, reorder, delete, and set which state
  starts an activity and which counts as finished. An org can't lose its
  last finished-flagged state, or its last state at all. See
  `data-model-notes.md` ("Status workflow").
- **Activity types can be reordered** from the app (built 2026-09-03) —
  the `order` field was writable all along; only the affordance was
  missing.
- **The create forms offer photos after saving** (built 2026-09-03),
  matching what quick log already did, via one shared component.
- **DRF field-level validation errors are readable** (fixed 2026-09-03).
  The API client only ever unpacked `{"detail": ...}`, so every
  serializer validation error in the app reached the user as raw JSON.
  Found by looking at a screenshot of the new workflow-state guard, not
  by a failing assertion.

- **All five 2026-09-02 user-feedback items — decided by the owner, then
  built the same day.** These were the first real content the feedback
  pipeline ever produced; the owner authorized the set with *"build these
  in the next build session."* Full detail in `build-questions.md`
  (2026-09-02 (8)) and `data-model-notes.md`:
  - **Activity types are org-defined** (`ActivityType`, a per-org table
    mirroring `WorkflowState`; `Activity.activity_type` is now a PROTECT
    FK; migration `activities/0003` backfills existing rows). The
    display half went with it: `name` is both the stored value and the
    label, so there is no slug left to render, and the API serves
    `activity_type_name` alongside the id. Editable from the org admin
    console. **Still open, noted not solved:** no UI to *reorder* types
    (creation order), and workflow *states* are still not editable.
  - **`Species.notes` renamed to `Species.description`**, plus an annual
    bloom range (`bloom_start`/`bloom_end`, MMDD, wrap-aware) and a
    server-side `?blooming_on=` filter. Surfaces on a public sighting,
    per the owner's *"more info on the public site when viewing the
    sightings."* The rename was the right call precisely because the
    field was **already public** under a name that implied otherwise.
    **Consequence worth knowing:** a species now has no private notes
    field at all — recorded in `docs/manual/limitations.md`.
  - **Quick log**, the geometry-first capture flow, on the dashboard.
  - **The logo links home** — `/` in the app, the org's own public root
    on the public site.
  - **Feedback records the screen it was sent from** (`page_path`), in
    both the admin's list and the cross-org pull payload.
- **Property-scoped admin's reach into the org admin console — narrowed
  (decided by the owner 2026-09-02, implemented the same day).** A
  property-scoped admin's member/role management is now limited to
  members whose own property scope sits entirely inside the admin's own;
  org-level actions with no property dimension (org rename, public URL
  slug, org theme/header image, org-level pages, the feedback queue)
  stay with account-wide admins. The exact boundary was settled at build
  time along the lines the decision record asked for, and recorded in
  `data-model-notes.md` ("Permissions"): full containment rather than
  partial overlap; an account-wide member is never reachable by a scoped
  admin; adding a member is allowed but must be scoped inside the
  admin's own properties (no account-wide member, and no widening an
  existing one past the admin's scope — which is also what stops a
  scoped admin widening *itself*); pending invitations follow the same
  rule as the memberships they'll become. **One related correctness fix
  came with it:** the "an org needs at least one admin" lockout guard now
  counts *account-wide* admins specifically — a property-scoped admin
  can no longer rename the org or manage account-wide members, so an
  organization left holding only scoped admins would have had no
  in-app way back. See `docs/manual/roles-and-permissions.md` and
  `organization-admin.md` for the user-facing description.
- **`HABITAT_FEEDBACK_TOKEN` provisioned; feedback pull/mark-synced loop
  confirmed live end-to-end (2026-09-02, owner).** The owner set the
  bearer token on both the `habitat.dev.cravenator.com` server and this
  scheduled routine's own environment, then submitted a real test
  `Feedback` item through the app to exercise the whole path. This PM
  check-in verified it for real, not just that the token is accepted:
  `GET /api/feedback/pull/` returned the test item (org "test",
  `test@gmail.com`, "This is a test feedback item...") with `status:
  "new"`; `POST /api/feedback/pull/mark-synced/` marked it synced; a
  follow-up pull returned `[]`, confirming the incremental-fetch dedup
  (see `data-model-notes.md`'s "App feedback" section) actually excludes a
  synced item rather than just being spec'd to. This closes the last
  ops-only gap the feedback pipeline (built 2026-08-29) had — the pipeline
  is now fully operational, not just "built." The test item's own content
  was a pipeline smoke test ("Use this to test the full end to end loop
  for feedback"), not a feature request — nothing to queue from it.
- **Soft delete — Property only, 30-day retention, admin-restorable,
  cascading — implemented (2026-08-29).** Owner decision: scope is
  Property only (not Activity/Sighting/Species/Task individually);
  retention is 30 days; restore is admin-only via a "Recently deleted"
  view on the org admin portal; a soft-deleted property's activities/
  sightings are hidden too during the window, and everything is hard-
  deleted together at day 30. See `data-model-notes.md` ("Property /
  parcel") for the implementation shape
  (`Property.deleted_at`, `purge_deleted_properties` management command).
- **Task status states — confirmed as-is (2026-08-29).** The existing
  fixed set (open/assigned/resolved/dismissed) stays fixed, not
  org-customizable. No model change.
- **Task assignee notification — in-app now, pluggable channels —
  implemented (2026-08-29).** Ships as an in-app notification (bell icon
  + unread badge in the top bar) behind a channel-dispatch abstraction, so
  an email channel (once real SMTP exists) can be added later without
  reworking the call site. See `data-model-notes.md` ("Notifications").
- **Are planned/done-equivalent states reserved? Left as-is (2026-08-29).**
  No formal requirement that a custom workflow designate reserved
  planned/done states — the public map's styling stays driven by each
  state's own `is_done` flag. No change.
- **In-app feedback pipeline — implemented (2026-08-29).** Every org
  member can submit feedback via a floating button (gated behind
  `HABITAT_FEEDBACK_ENABLED`); no server-side AI summarization — an
  external scheduled routine pulls unreviewed feedback directly via a
  bearer-token-authenticated retrieval endpoint and does its own triage.
  See `data-model-notes.md` ("App feedback") and "App feedback / build
  workflow" below for what's still open (the credential's actual
  provisioning, which instance to target).
- **Real email delivery / SMTP — stays console-only for now (2026-08-29,
  owner decision).** No provider chosen; revisit when real outbound mail
  is actually needed. See "Auth and API" below.
- **Hosting domains — prod vs. dev split decided (2026-08-29, owner
  decision).** Prod will eventually live at `habitat.cravenator.com`;
  `habitat.dev.cravenator.com` (already confirmed live) is the dev
  environment, not the prod target. Provider/self-hosted-vs-managed/
  cost-scaling remain open — see "Tech / infrastructure" below.
- **Nav logo — "four seasons" mark, implemented (2026-08-29).** The owner
  picked the "Habitat — four seasons" set from a published design canvas;
  the app now shows the seasonal variant matching today's date (Spring/
  Summer/Fall/Winter) rather than one fixed mark, replacing the old "🌿
  Habitat" emoji+text placeholder in both the authenticated app's top bar
  and the public site's header. Two build-session defaults, cheap to
  change: **meteorological season boundaries** (Mar-May/Jun-Aug/Sep-Nov/
  Dec-Feb), not exact solstice/equinox dates; **Northern Hemisphere**
  (the author's own context) — revisit with a location-aware version if
  Habitat ever serves Southern-Hemisphere properties. See
  `frontend/src/utils/logo.ts` and `frontend/src/components/Logo.tsx`.
- **Per-property QR code "not in place" report — investigated
  (2026-08-29).** The feature was already on `main`; the actual issue was
  UX, not a missing feature or an undeployed build: the whole QR section
  silently disappeared (no explanation at all) when a property isn't
  public, and the panel itself defaulted to a collapsed, easy-to-miss
  `<details>`. Fixed: an inline explanation ("this property isn't public
  yet...") when the property is private, and the panel now starts
  expanded (`open`) when it is public.
- **Vanity slug URLs for the public site — implemented (2026-08-29).** Each
  organization now has a globally-unique `slug` (`/public/<org-slug>`) and
  each property a slug unique within its org
  (`/public/<org-slug>/<property-slug>`), matching the decided shape.
  Sub-question calls made while building: slugs auto-generate from the
  name (slugify + `-2`/`-3` suffix on collision) so every row is
  immediately reachable, and are admin-editable on the org admin portal /
  property edit form (that path validates uniqueness and rejects a clash,
  and rejects a reserved org slug like `org`/`properties`/`public`/`api`);
  the old numeric-ID URLs (`/public/org/<id>`, `/public/properties/<id>`)
  are kept working for backward compatibility rather than redirected. A
  data migration backfilled slugs for pre-existing orgs/properties. See
  `data-model-notes.md`, `apps/accounts/slugs.py`, and the manual
  (`organization-admin.md`, `properties.md`, `public-site.md`).
- **QR code generator for public URLs — implemented (2026-08-29).** Ships
  alongside the vanity slugs above. Server-side PNG generation (`qrcode` +
  Pillow, `apps/accounts/qrcodes.py`) at `POST /api/org/qr/` and
  `POST /api/properties/<id>/qr/` — each takes the public-site origin
  (`base_url`, which the backend can't infer since the SPA is on a
  different origin) plus an optional `logo` image, and returns an image/png
  of a code pointing at that org/property's public page. **Center-logo
  embedding is included**: error-correction level H plus a white-padded
  center paste, verified (via zbar) to still decode with the logo over it.
  Offered on the org admin portal (org code) and each public property's
  page (property code) via a shared `QrCodePanel`, with an optional
  center-image picker and a live preview/download. Sub-question calls:
  server-side (per the owner), both placements, PNG download, logo embedded
  now.
- **Sensitive-sighting default visibility: an organization's own call, set
  per property — not auto-detected from a sensitive-species list.**
  (2026-08-28, owner decision.) Rather than Habitat maintaining or
  inferring which species are sensitive and auto-flagging sightings of
  them, an admin sets a per-property default (e.g. "default new sightings
  on this property to private") and every sighting on that property
  starts from that default, same as today's own per-record flag still
  lets any one record be overridden either way. See
  `data-model-notes.md`. **Implemented (2026-08-28)** —
  `Property.sightings_public_by_default` (migration
  `accounts/0006_property_sightings_public_by_default`), applied at
  sighting-create time in `SightingViewSet.perform_create` when the
  request doesn't explicitly set `is_public` itself, exposed as a
  checkbox on `PropertyFormPage`, and seeded into `SightingFormPage`'s own
  checkbox for a brand-new sighting on that property.
- **Should the public-facing view surface the sighting↔activity link?
  Yes** (2026-08-28, owner decision) — e.g. "reported by a visitor,
  treated on this date." **Implemented (2026-08-28)** — the public
  `property_activities`/`property_sightings` views annotate each feature
  with `linked_sighting_ids`/`linked_activity_ids` (only ever including
  the other side when it's also public), and `PublicPropertyPage` renders
  them as "Reported sightings: …" / "Treated by: …" lines.
- **Starter species list: none — every new account's species list starts
  completely empty.** (2026-08-28, owner decision.) No change needed;
  this was already the existing behavior, just confirmed rather than
  left open.
- **Default workflow states for a brand-new account: the existing
  Planned → In Progress → Done seed is fine.** (2026-08-28, owner
  decision, confirming the assumption made when this was first built —
  see the 2026-08-07 `CLAUDE.md` task-log entry.) No change needed.
- **Licensing of public data: leave unlicensed (all rights reserved by
  default) for now.** (2026-08-28, owner decision.) Revisit once a real
  Phase 4 API or Phase 5 public-input program makes licensing terms
  actually matter to someone consuming the data.
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
  yet, see "Tech / infrastructure" below. **The map itself now visually
  distinguishes planned/in-progress work from completed work** (dashed
  orange vs. solid green, with a legend) — the specific Phase 2 roadmap
  requirement (`roadmap.md`) that was still open even after the rest of
  the public site shipped; the same styling also applies to the
  logged-in `PropertyMapPage`, not just the public one. Based on
  `ActivitySerializer`'s new `is_done` field rather than a three-way
  planned/in-progress/done split, sidestepping the still-open "are
  planned/done-equivalent states reserved" question below.
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
  controls a role can't use. Property scoping (`Membership.properties` —
  leave empty for account-wide, or select specific properties to limit a
  role to just those) is stored and editable through the org admin
  portal, and — as of 2026-09-01 — **actually enforced**: a scoped
  membership's list/retrieve/update/delete on Property, Activity,
  Sighting, and Page (the public-site authoring model) is filtered to
  its own properties (`org_scoping.py`'s `scoped_property_ids`/
  `property_accessible`/`filter_by_property_scope`), and creating a new
  one requires the target property to be in scope. A scoped membership
  can't create a brand-new Property or org-level Page at all (nothing to
  scope them to yet — an admin creates one and adds the member to it),
  nor a property-less Sighting (it would be invisible to every scoped
  member, itself included). Species/Task/WorkflowState stay account-wide
  regardless of scope — none of them have a Property FK, so there's
  nothing to scope them by. **The org admin console was narrowed to
  match on 2026-09-02** (see the entry above); see
  `data-model-notes.md` for the full shape and
  `docs/manual/roles-and-permissions.md`/`limitations.md` for the
  user-facing description (which had this right — "stored but not
  enforced" — until this session closed the gap). **A related, previously
  unvalidated cross-org gap was found and fixed along the way**, not
  property-scoping itself but the plain organization boundary:
  `Activity`/`Sighting`'s `property` fields (and `Sighting`'s `species`
  field) accepted *any* row regardless of which organization it belonged
  to, letting one org's editor plant a fabricated activity/sighting on a
  *different* org's public property page (the public site derives a
  property's activities/sightings straight off that FK). Fixed with the
  same `validate_<field>`-against-the-caller's-org pattern
  `TaskSerializer`/`PageSerializer` already used for their own FKs. An
  org admin manages both role and property scope through the in-app org
  admin portal (`/admin`, admin-only) — see `data-model-notes.md`. New
  members are
  added by an admin either way: **if their email already has a Habitat
  account, they're attached to the org immediately**; **if it's a
  brand-new email, adding them now creates a pending Invitation and
  emails an accept link** (`Invitation` model + `POST /api/org/members/`
  branching on whether the email exists, `GET/POST
  /api/invitations/<token>/(accept/)`, admin-only
  `GET/DELETE /api/org/invitations/` to list/revoke pending ones) rather
  than the admin setting a password directly — see "Auth and API" below
  for the real-email-delivery caveat this still has. A pending invitation
  can also be **resent** (`POST /api/org/invitations/<id>/resend/`,
  admin-only) — refreshes its 7-day expiry and re-sends the same accept
  link, so one that expired unused doesn't have to be revoked and
  recreated from scratch. **That new member can also change their own
  password afterward** via a self-service `/account` page
  (`POST /api/auth/change-password/`, requires the current password,
  keeps the session alive via `update_session_auth_hash`) — and if they
  forget it entirely (so can't supply the *current* password that
  requires), a separate **"forgot password" flow**
  (`POST /api/auth/password-reset/` + `.../confirm/`, both `AllowAny`)
  emails a one-hour, one-time reset link instead. The request endpoint
  always returns the same generic response regardless of whether the
  email has an account, so it can't be used to enumerate registered
  addresses — see "Auth and API" below for why (unlike the invite flow)
  this one has no admin-UI fallback for a case where the email never
  arrives.
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

The three items that used to live here (are planned/done states reserved,
task status states, task notification mechanism) were all resolved
2026-08-29. Two more arrived 2026-09-02 from real user feedback, were
decided the same day, and were **built 2026-09-02** — see "Recently
resolved" below and `build-questions.md`'s 2026-09-02 (8) entry.

Nothing is open here right now.

## Accounts, orgs, and permissions

- **Which organization a multi-org user acts in — the floor is built
  (2026-09-04), the org switcher is still open.** The defect found by the
  same day's PM check-in (an unordered `user.memberships...first()` in
  `apps/accounts/org_scoping.py` against a `Membership.Meta` that declared
  constraints but no `ordering`, so a two-org user's active organization —
  and with it every scoped queryset in the app — could change between
  requests whenever a membership row was updated) is **fixed**:
  `Membership.Meta.ordering = ["created_at", "id"]`, migration
  `accounts/0013_alter_membership_options`. "Your first membership" now
  means the oldest one, deterministically, which is what
  `docs/manual/limitations.md` and `getting-started.md` already told
  users — the code just didn't guarantee it. No behavior change for a
  single-org user, which is everyone today.
  **Still open: the org switcher itself** — letting a multi-org user
  choose which organization they're acting in (store the choice in the
  session, fall back to the ordered-first membership). That's the
  "revisit if/when a user belongs to more than one org" note from
  2026-08-07, still never revisited; it touches the one function every
  scoped queryset in the app goes through, so it's a feature, not a
  follow-up to the fix above. Deliberately left open rather than
  built alongside the floor.
- **Can a property (and its history) move from one account to another** —
  e.g., a homeowner's property gets formally adopted into a land trust's
  program? What happens to existing records, public page, and prior
  contributors' access? **Explicitly deferred** — judged too open-ended to
  resolve now; revisit if/when it becomes a real, concrete need rather than
  a hypothetical.

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
- **Real email delivery isn't configured.** The org-invite flow and the
  password-reset flow (both — see "Recently resolved" above) send real
  mail through Django's `send_mail`, but `settings.EMAIL_BACKEND`
  defaults to the console backend (just logs the message) since no SMTP
  provider is chosen yet — tied to the undecided "Hosting/ops model"
  below. Until that's picked, the invite accept link shown/copyable in
  the admin UI is the actual delivery mechanism for invites; the
  password-reset link has no such UI fallback (returning it directly
  would let the endpoint be used to check who has an account — see
  `apps/accounts/password_reset.py`), so that flow is only really
  exercisable today by reading the server's console output.
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
- **The 30-day purge the app promises users is now actually performed —
  built 2026-09-04** (found the same day by that morning's PM check-in:
  `docs/manual/properties.md` told users a deleted property is removed for
  good after 30 days, and nothing in the repo ever ran
  `purge_deleted_properties` — no cron, no workflow, no entrypoint step,
  no compose service; so soft-deleted properties were retained
  indefinitely, and a user deleting a property to be rid of its data
  didn't).
  Of the three candidate mechanisms, **two are built and the third is
  deliberately not:** the purge logic moved out of the management command
  into `apps/accounts/purging.py`, which is now called (a) **on backend
  startup** from `backend/entrypoint.sh`, sweeping the whole database on
  every container start/redeploy and non-fatal so a purge failure can't
  stop the app booting, and (b) **lazily** by `PropertyViewSet.deleted`
  and `.restore`, scoped to the caller's own organization — which also
  makes the "Recently deleted" list honest about its own window (an
  expired property is swept before the list is drawn, so it can't be
  listed *or* restored from a stale tab). The management command still
  works unchanged and is still idempotent.
  **(i), a scheduled GitHub Actions workflow, was considered and not
  built:** it needs a target URL and a bearer-token secret provisioned in
  the repository, neither of which a session can do, and it would fail
  loudly on every scheduled run until they were — so it would trade a
  silent gap for a noisy one. The two mechanisms above need no
  configuration at all. **A real cron is still the thing to add** if a
  deployment wants purging at a specific hour rather than "on the next
  restart or the next admin visit"; nothing built here gets in its way.
  That remains genuinely blocked on the hosting model below.
- **Deleting a property did not retract its already-published photos —
  found 2026-09-04, ✅ BUILT the same day.** The fix is four filters in
  `apps/public_site/views.py` (`property__deleted_at__isnull=True` on both
  record helpers *and* both cross-property link helpers) plus
  `apps/public_site/tests.py`, the repo's first backend tests, which pin
  the behavior and the Django semantic underneath it. Verified against a
  live PostGIS database: 7 tests, and the same suite fails with 5
  failures against the pre-fix code, so it is a real regression guard
  rather than a restatement of current behavior. **Scope was wider than
  first recorded:** the two link helpers
  (`_public_linked_sighting_ids`/`_public_linked_activity_ids`) leaked
  too, because a Sighting↔Activity link is not constrained to one
  property — nothing in `SightingActivityLinkSerializer` enforces that,
  and it even serves `activity_property_name` — so a *live* property's
  activity could keep naming a deleted property's sighting id in its
  public link list. Confirmed against the pre-fix code, which returned
  the id where the fixed code returns `[]`. The original finding, kept
  because the reasoning is what matters for the next person:
  `apps/public_site/views.py` had no `deleted_at` guard anywhere, while
  the authenticated `ActivityViewSet`/`SightingViewSet` and even their
  function-based photo/link helpers all have one.
  `_public_activity_or_404` and `_public_sighting_or_404` gate on
  `is_public=True, property__is_public=True`; a related-field filter is a
  plain SQL join and **does not** apply `Property.objects`' soft-delete
  filter, and a soft-deleted property still has `is_public=True`. So after
  a delete the public page 404s and the org portfolio omits the property,
  but `/api/public/activities/<id>/photos/(<id>/image/)` and the two
  sighting equivalents keep serving its photos to anonymous callers.
  The inversion is the clearest statement of it: flipping a property
  *private* does cut those photos off; deleting it does not — the stronger
  action retracts less. Only already-public records on an already-public
  property are affected, so this is a failure to retract published data
  rather than exposure of anything private; the window is now roughly the
  30-day retention period thanks to the purge fix above, and was
  indefinite before it. Verified empirically (Habitat's exact manager
  shape reproduced on plain models in a throwaway Django project — the
  guarded query excludes the row, the current one returns it), not just
  read. Cause: soft delete shipped 2026-08-29 and covered the whole
  authenticated app carefully, but `apps/public_site/` (built 2026-08-14)
  was never opened. Its module docstring stated the invariant as
  "everything is scoped to `is_public=True`" — one condition where there
  are two — and `data-model-notes.md` asserted soft delete hid a property
  from "the app, the public site, everywhere"; both have been corrected,
  since a doc that states the wrong invariant is part of how this
  survived three weeks.
- **Hosting/ops model** — self-hosted vs. managed services, and how that
  choice affects cost as usage scales from one user to many organizations.
  (2026-08-26: a GitHub Actions workflow now builds and publishes the
  backend/frontend Docker images to Docker Hub on push to `main`, a
  version tag, or manual dispatch — see `.github/workflows/
  docker-publish.yml`. That's just an image-publishing step, not a
  hosting decision; the images it builds are still the same dev-oriented
  Dockerfiles `docker-compose.yml` uses locally, so this question stayed
  open until the entry below.)
- **Dev hosting domain decided and confirmed live: `habitat.dev.cravenator.com`**
  (2026-08-28, owner decision, confirmed running the same day). This
  answers *where* a real, reachable instance lives — the "some live
  instance to target" dependency the app-feedback pipeline needed (now
  built — see "Recently resolved" above). **Reachability from an
  automated session: confirmed working (2026-08-28, re-confirmed
  2026-08-29 — both `GET /` and `GET /api/auth/csrf/` reachable via plain
  HTTP, and this session confirmed the *source* served there already
  includes same-day work, e.g. the QR feature).** The `WebFetch` tool
  specifically still can't reach it (separate allowlist from the general
  sandbox proxy) — not a blocker for an API-polling pipeline, which uses
  a direct HTTP call instead, but worth knowing.
  **Prod/dev split decided (2026-08-29, owner):** prod will eventually
  live at `habitat.cravenator.com`; `habitat.dev.cravenator.com` above is
  the dev environment, not the prod target. **Still open:** hosting
  *provider*, self-hosted vs. managed, cost/scaling — the owner has
  explicitly deferred these; don't resurface the provider/cost question
  every session, it's deliberately parked, not forgotten.
- **Vanity slug URLs — implemented 2026-08-29.** See "Recently resolved"
  above for the shape as built and the sub-question calls made. (Org slug
  globally unique; property slug unique per-org; auto-generate with
  collision suffix; admin-editable with validation; numeric IDs kept for
  backward compatibility.)
- **QR code generator for public URLs — implemented 2026-08-29.** See
  "Recently resolved" above for what was built and the sub-question calls
  (server-side PNG via `qrcode`+Pillow; offered on both the org admin
  portal and each public property page; center-logo embedding at
  error-correction level H).

## App feedback / build workflow

**Built 2026-08-29** — see "Recently resolved" above and
`data-model-notes.md` ("App feedback") for the shape as implemented.
**Token provisioned and the full pull loop confirmed live, 2026-09-02** —
see "Recently resolved" above for the record. **The pipeline delivered
real content for the first time on 2026-09-02**: a PM check-in pulled five
genuine feature requests/bug reports (not the earlier smoke test), triaged
them, and marked them synced — see `build-questions.md`'s 2026-09-02 (6)
entry. The loop this feature was built for now demonstrably works
end to end, from a user typing into the app to a queued, triaged build
item. **A second batch of six items arrived 2026-09-03** and was triaged
the same way — see `build-questions.md`'s 2026-09-03 entry. The loop is
now a routine part of how work reaches the queue, not a one-off.
**The 2026-09-03 (2) check-in pulled `[]`** — the first empty pull since
the pipeline started producing real content, which is the expected
steady state rather than a fault: both prior batches were triaged, built,
and marked synced. Worth knowing for whoever reads a `[]` next and
wonders whether the token broke: the same run confirmed the endpoint
still authenticates and the dev instance still serves. **2026-09-04
pulled `[]` too** — two consecutive empty pulls, same conclusion, and the
dev instance was re-confirmed reachable on that run as well. **The
2026-09-04 (2) programmer run and the 2026-09-04 (3) check-in each pulled
`[]` as well — four consecutive**, with the endpoint still authenticating
and the instance still serving each time. Four empty pulls in a row is
the steady state, not a signal to go looking for a fault.

**`Feedback.page_path` (built 2026-09-02) is confirmed working, and paid
for itself in one cycle.** All six 2026-09-03 items arrived carrying the
screen they were sent from (`/`, `/admin`, `/quick-log`), and it changed
the triage rather than just decorating it: one item reads as a vague "too
much on one page" until its `/admin` path makes it specific, and another
is identifiable as being about the day-old quick-log flow rather than the
long-standing forms only because of its path.

**Still genuinely open:**

- Whether every org member should be able to submit feedback, or just
  admins — built as "every member," per the owner's 2026-08-29 decision,
  but worth re-confirming once this sees real multi-member use.
- No scheduled routine is formally set up to poll this on a recurring
  cadence yet — today it's pulled ad hoc by whichever PM check-in happens
  to run. Not a blocker (the check-in routine already does it each time),
  just worth noting if a tighter feedback loop is ever wanted.

## Logged-in app UX

Both items here (the geometry-first "quick log", and the logo not being a
link home) were decided and **built 2026-09-02** — see "Recently
resolved" below. **Six more user-feedback items arrived 2026-09-03**, four
of them landing here; full triage in `build-questions.md`'s 2026-09-03
entry. **Five of those six were authorized and built 2026-09-03** (the
scheduled programmer run that same day) — the navigation restructure, the
Manage section, the two new pages, the auth-screen logo, the dashboard
fix, the admin submenu and the quick-log photo step. What remains open
here is B2 (the logo mark as the "h"), the parked contextual menu, and the
two deliberately-deferred items at the bottom.

- **Navigation restructure — half decided (2026-09-03, feedback id 8).**
  *"Properties, species, public site should go under admin... By default
  home, tasks, activities, and sightings."*
  - **✅ Decided by the owner, live, 2026-09-03: build two new org-wide
    pages, Activities and Sightings** — *"I'm asking for two pages to
    help manage those two things."* Verified against `App.tsx` that
    neither route exists today (both live only inside a property), so
    this is a real feature, not a menu edit. **It also settles feedback
    id 10's second half** (*"found and edited on their respective pages
    using a search/filtering function"*) — the two items are one feature.
    **Built 2026-09-03**: `/activities` and `/sightings`, each a
    client-side-filtered list linking to the existing per-property edit
    form.
  - **✅ Decided (owner, live, 2026-09-03): "Admin" becomes a "Manage"
    section**, visible to every member, with the admin-only surfaces
    still role-gated *inside* it. This was the question because the nav
    entry is `isAdmin`-gated today, so moving Properties and Species
    under it as-is would have hidden them from the viewers and editors
    who use them daily. The gate moves inward rather than disappearing —
    backend role checks are unchanged, and this should be built together
    with the admin-console submenu below, since the section list *is* the
    role-filtered menu. **Built 2026-09-03**, together with the submenu:
    `/manage` is a role-filtered menu of sub-routes, `/admin` redirects to
    it, and the per-section gate lives in one place
    (`pages/manage/sections.ts`) that both the menu and each sub-page's own
    guard consult. Verified against a viewer, an editor, a
    property-scoped viewer and a property-scoped admin.
  - **⏸️ Parked (owner, live, 2026-09-03): the contextual menu.**
    Confirmed as genuinely contextual nav (the menu's contents changing
    with the current page) and deliberately deferred — *"maybe we should
    park for a hot minute."* The nav stays flat. Worth revisiting after
    the two new pages exist, since until there are org-wide
    Activities/Sightings lists there is no global view for a
    property-context menu to contrast with.
    **⚠️ That precondition has now been met (noted 2026-09-03 PM
    check-in): both pages shipped the same day this was parked.** So the
    stated reason for parking it has expired — re-raised to the owner as
    "unpark, or keep parked?" rather than left to sit on a condition
    that's already true. Keeping it parked is a fine answer; the point is
    that it should now be a live choice. `limitations.md`'s "the nav is
    the same on every page" stays accurate either way.
- **Should the logo mark become the "h" in "habitat"? — needs the owner
  (2026-09-03, feedback id 12).** Checked the artwork: each seasonal SVG
  is a vertical stem plus a shoulder arch, i.e. already structurally a
  lowercase "h", so this is typographic execution rather than a
  redesign. Needs a yes/no because it's the brand and because the
  foliage overshoots the ascender line. Should ship together with the
  auth-screen logo fix below, since both touch every brand surface.
  **Still unanswered as of the 2026-09-03 PM check-in, and now the only
  unbuilt piece of that six-item feedback batch** — it was excluded from
  the owner's *"Build next run"* authorization precisely because it had
  no answer, and the programmer run respected that (the wordmark is
  untouched). One consequence of the delay: it was meant to ship *with*
  the auth-screen logo fix, which has now shipped without it, so
  building it means a second pass over the same five screens.
- **Built 2026-09-03 (was: build-ready, no decision needed):** the five
  unauthenticated screens (login, signup, forgot/reset password, accept
  invite) still render the old `🌿 Habitat` placeholder — the 2026-08-29
  logo work covered only `TopBar`/`PublicHeader`; the dashboard counts
  planned activities as "recent" (they appear in two sections at once)
  and shows five rather than the requested three; the org admin console
  is one 1061-line page with eight sections and wants a submenu; and
  quick log should offer a photo step after saving rather than
  navigating straight away. All four shipped in that day's programmer
  run.
- **Still open, deliberately deferred rather than decided:** whether a
  half-finished quick-log capture should persist as a draft. Built with
  no persistence, which is the recommended first-pass default, not a
  final answer — revisit if anyone actually loses work to it.
- **Also open:** whether the phone screen-space complaint that motivated
  quick log is fully answered by it. The capture screen gives the map the
  whole viewport, which was the concrete fix; whether the *existing*
  fixed-height `.page--map` split-scroll layout still needs its own pass
  is best judged from use rather than guessed at now.

## Build queue state — three of the four candidates are now built

Recorded by the 2026-09-03 (2) PM check-in and updated by the 2026-09-03
(3) programmer run, which built three of the four candidates below plus
the manual bug. The **owner's "Build next run" authorization remains
spent** — that batch shipped 2026-09-03 and nothing has re-authorized it.
The work below was taken up under the programmer routine's *own*
triggering instructions ("incorporate this feedback into the codebase and
commit directly to main"), which is what `CLAUDE.md`'s working
conventions treat as that session's scope; it is not a claim that the
owner's earlier authorization stretched further.

- ✅ **A workflow-state editor** — BUILT 2026-09-03 (3). `/manage/workflow-states`,
  writable endpoint, reorder, and the flagged lockout guard. The
  sub-question this file said not to guess at was answered
  asymmetrically: `is_done` is guarded on both un-flag and delete because
  nothing downstream can infer it, while `is_planned` is not, because
  both its readers already fall back to the first state. See
  `data-model-notes.md` ("Status workflow") for the reasoning.
- ✅ **Activity-type reordering** — BUILT 2026-09-03 (3), and it was
  indeed frontend-only: `order` was already writable. Shared with the
  workflow-state editor (`pages/manage/reorder.ts`), as this file
  suggested. A move rewrites every changed row's `order` rather than
  swapping a pair, because nothing guarantees the stored values are
  distinct — swapping two equal ones is a no-op that reads as a broken
  button.
- ✅ **Photos on the regular create forms** — BUILT 2026-09-03 (3). The
  quick-log photo step was extracted into a shared
  `PostSavePhotoStep` component and all three create flows now use it,
  so there's one copy rather than three that drift.
- ⏳ **Server-side search/pagination for `/activities` and `/sightings`**
  — still open, deliberately re-deferred. Both filter client-side, the
  same tradeoff `SpeciesPage` takes — correct for today's scale, and the
  first thing to break as data accumulates, more so than `SpeciesPage`
  because these two are org-wide. Not built because it's a real design
  call (which endpoints gain query params, what page size, whether the
  existing client-side filters stay as a fallback) rather than a
  mechanical change, and nothing is currently hurting.

**Still needing the owner, unchanged by this run:** B2 (should the logo's
mark become the "h" in "habitat" — never answered, so never built), and
whether to unpark the contextual menu now that its stated precondition
(org-wide Activities/Sightings pages) has been met.

**Refreshed 2026-09-04 (PM check-in).** Both questions above are still
unanswered — B2 for two days, the contextual menu for one. With three of
the four candidates built, the menu for the next programmer run was
rebuilt from the code rather than from the task log, and the two
best-defined items on it are the defects that run found: the unscheduled
purge (see "Tech / infrastructure" above) and `Membership.Meta.ordering`
(see "Accounts, orgs, and permissions" above). Server-side
search/pagination is carried over but now **shaped into a yes/no** —
DRF's own `SearchFilter` + `PageNumberPagination` on the two org-wide
viewsets, page size 50, existing client-side filters kept as in-page
refinement — with the recommendation still being *not yet*, since nothing
is hurting and the stock-DRF shape stays cheap to adopt later. One new
candidate needing a product yes/no: **due dates on tasks** (listed in
`limitations.md`, called a deliberate Phase 1 simplification in
`apps/tasks/models.py`, and unassigned to any later phase in the
roadmap). Full menu in `build-questions.md` (2026-09-04, Q3).

**Refreshed again 2026-09-04 (3) (PM check-in).** Both defects that run
found are now built (the purge, and `Membership.Meta.ordering`), so the
queue turned over again. **The best-defined item in the repo is now D3 —
a deleted property's photos are still served publicly** (see "Tech /
infrastructure" above). It is unusual for this queue in that it closes a
live gap rather than adding capability, and unlike the two questions below
it **needs no owner input**: the fix mirrors a guard the authenticated
app already applies in four places. A programmer run should take it
without asking. The rest of the menu is unchanged and each item is either
recommended *not yet* (server-side search/pagination) or waiting on the
owner (due dates on tasks; the org switcher) or on the hosting model (a
real cron for the purge) or on someone actually being hurt by it
(quick-log draft persistence). **B2 is now four days unanswered and the
contextual menu three** — both re-raised compactly rather than re-argued.

**Emptied again 2026-09-04 (4) (programmer run).** D3 is built, so **the
queue now holds nothing a build session may take on its own.** Every
remaining item is blocked on something a session can't supply, and the
blockers are the same ones as the last two turnovers: **B2 (five days
unanswered) and the contextual menu (four days)** both need a yes/no from
the owner; due dates on tasks and the org switcher are product calls; a
real cron for the purge is blocked on the hosting model; server-side
search/pagination is recommended *not yet*; quick-log draft persistence is
waiting on someone actually losing work to it. A programmer run firing
next would triage this file correctly and find nothing authorized —
which is the same state 2026-09-03 (3) recorded, and the honest one to
report rather than manufacturing work to fill the run.

## Public-site content policy

- **No content policy or terms say what an author may publish** on their
  public pages — opened by the custom-HTML/JS build (2026-09-02). The
  sandbox is a real technical control and it holds: author script runs on
  a unique opaque origin, so it can't reach Habitat's cookies, another
  tenant's content, or the embedding page. What it deliberately does
  *not* address is an author misleading their **own** page's visitors
  (impersonation, fabricated claims, deceptive forms). Today's only
  remedy is `Organization.custom_html_allowed`, a Django-admin
  kill-switch — after the fact, per tenant. This is a policy question for
  the owner, not a build item: **no code is waiting on it**, and the
  feature ships off by default regardless.

## Public site storytelling / custom content

Raised 2026-08-29 (owner) — a bigger, multi-part feature. **The first
slice (authored pages + Explore rename + landing-page pick) is built
(2026-08-30)**, and **the custom-CSS piece (constrained theme controls)
is now built too (2026-08-31)** — see `data-model-notes.md`'s "Authored
pages" and "Constrained theme controls" sections for the implementation
shape. **Custom HTML/JS — decided (owner, 2026-09-02, live): isolated-origin
sandbox**, superseding the earlier 2026-08-29 "park it, accept the
on-origin risk" call — **and built the same day** (see the bullet list
below and `data-model-notes.md`'s "Custom HTML/JS pages"). With that, the
whole storytelling feature family — authored pages, theming, custom
HTML/JS — is built. What remains is ops (DNS/TLS/serving path for the
isolated public origin) and one policy question (a content policy for
author-published content), both noted below.

**Scope, finalized 2026-09-02 (live, after a back-and-forth — see the full
exchange for the reasoning): relocate the ENTIRE existing public site to
the new isolated subdomain, not just future custom-HTML/JS content.**
The owner's first instinct was "can existing and start over," which
would have meant throwing away and redesigning the whole feature set;
walked through the alternative — **keep every already-built feature and
its data model exactly as-is (Explore view, vanity slugs, QR codes,
authored pages, theme controls), just change which origin serves
them** — and the owner confirmed that's the intended scope: relocation,
not a rewrite. So the next build session's job is a *move* (the public
site starts being served from `public.habitat.dev.cravenator.com`-shaped
instead of the app's own origin) plus *then* adding real custom-HTML/JS
authoring on top, not a redesign of what already works. Full detail lives
in `build-questions.md`, including an architectural note worth reading
before that build starts: moving the *whole* public site off the app's
origin may satisfy the original per-page sandboxed-iframe requirement on
its own (the thing that needed isolating was the app's session cookies,
and those already can't reach a different origin) — a build session
should evaluate whether a nested iframe sandbox per authored page is
still needed once the whole site already lives off-origin, rather than
building both layers by default.

Short version of what's now resolved vs. still open:

- **Authored pages + landing-page pick + "Explore" rename — ✅ BUILT
  2026-08-30.** A new `Page` model (`backend/apps/pages/`) scoped to an
  organization or one of its properties; markdown body, rendered and
  sanitized server-side at read time (never raw author HTML — see
  `data-model-notes.md`); `Organization.landing_page`/
  `Property.landing_page` pick which page (or the built-in Explore,
  unchanged, if left unset — the default for every existing org/property)
  shows at the public URL root. Authoring UI on the org admin portal
  (org-level pages) and each property's own page (property-level pages),
  editor+ to write, same role convention as everywhere else. Public site
  gained a page nav (Explore + authored public pages) on both the org
  portfolio and property pages. Verified end to end, including that a
  `<script>`/`javascript:` payload in a page's markdown source is
  stripped by the time it reaches a visitor (see that session's `CLAUDE.md`
  entry for the exact curl/Playwright coverage).
- **Custom CSS — ✅ BUILT 2026-08-31: constrained theme controls**, not a
  raw CSS field (per the PM recommendation the owner went with). A fixed,
  safe set of knobs — primary/background/accent color, a font choice, a
  header image — mapped to scoped CSS custom-property overrides, settable
  independently per-org and per-property (a property falls back to its
  org's value, field by field, for anything it leaves blank), editor+ to
  set via a new "Theme" section on the org admin portal and each
  property's own page. No raw-CSS escape hatch, per the decision — see
  `data-model-notes.md`'s "Constrained theme controls" section for the
  implementation shape (fields, the hex-validator-as-security-control,
  the CSS-custom-property mechanism, the header-image endpoints) and that
  session's `CLAUDE.md` entry for verification coverage.
- **Custom HTML + custom scripts (JS) — ✅ DECIDED (owner, 2026-09-02,
  live) and ✅ BUILT the same day.** `Page.content_format` (`markdown` |
  `html`) selects the format; an `html` page's document is served at its
  own URL under `Content-Security-Policy: sandbox allow-scripts` and
  embedded in an `<iframe sandbox="allow-scripts">` — no
  `allow-same-origin` in either place — so author script runs on a unique
  opaque origin with no cookies, no storage, and no reach into the
  embedding page or the app. Off by default
  (`HABITAT_CUSTOM_PAGE_HTML`), with a per-tenant kill-switch
  (`Organization.custom_html_allowed`, Django-admin only) and a 512 KB
  size cap. See `data-model-notes.md` ("Custom HTML/JS pages") for the
  shape and `deployment-config.md` for how to turn it on.
  **One queued sub-question answered while building:** the checklist
  asked whether the per-page nested iframe is still needed once the whole
  public site moves off-origin — **yes, kept**, because the decided shape
  is a *single shared* public subdomain, so without it every tenant's
  authored content would share one origin with every other tenant's; the
  sandbox is also what lets the feature work correctly on a deployment
  that hasn't relocated the public site yet. Consequently the feature is
  deliberately not gated on `PUBLIC_SITE_URL` — relocation is defence in
  depth, not the thing providing isolation.
  **Still open (policy, not code):** no content policy/TOS says what an
  author may publish. The sandbox stops author script reaching Habitat or
  other users; it doesn't stop an author misleading their own page's
  visitors, which the kill-switch answers only after the fact. Also still
  open by choice: per-tenant origin isolation (see the single-shared
  subdomain decision below).
  Original decision record follows. Walked
  through the three options in plain language (allowlist-sanitized HTML;
  raw HTML/CSS on the shared origin; a sandboxed frame on an isolated
  origin) — owner picked the sandboxed-isolated-origin approach. This
  covers both custom HTML and custom JS together (a sandboxed origin is
  what makes arbitrary JS safe to allow at all, so there's no longer a
  separate "HTML only, no JS" middle option to weigh once this is the
  chosen shape) and **supersedes the 2026-08-29 "park it, co-mingle on the
  app origin" decision** below — that earlier call was made assuming the
  isolated-origin work was deferred indefinitely; the owner has now chosen
  to actually build the isolation instead of accepting the on-origin risk.
  **Two of the "decisions to make first" from the isolated-origin
  checklist (`build-questions.md`) are also now settled, both live
  2026-09-02:**
  - **Domain shape: a subdomain, not a separate registrable domain** —
    e.g. `public.habitat.dev.cravenator.com`. Confirmed technically
    workable, not just assumed: `backend/config/settings.py` never
    overrides `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN`, so both are
    already Django's default host-only cookies, meaning a subdomain
    genuinely won't receive the app's session/CSRF cookies. No new domain
    purchase needed — a DNS record + a normal (non-wildcard) TLS cert
    under the existing `cravenator.com` domain is enough.
  - **Single shared user-content subdomain, not per-tenant subdomains** —
    owner's own reasoning: avoids needing a wildcard cert/DNS (which
    per-tenant subdomains would require) "so I don't have to buy another
    domain" [sic — the per-tenant wildcard route doesn't literally require
    *buying* a new domain, but does add real DNS/TLS complexity under the
    existing one; the practical effect the owner is choosing is the
    simpler single-subdomain path either way]. One shared subdomain used
    by every org's authored content still gets the core security win
    (isolating the sandbox from the logged-in app) — it just doesn't
    additionally isolate tenants from each other, which per-tenant
    subdomains would add later if ever needed.
  **The application half is built (2026-09-02) and the
  relocation is now a configuration change, not a code change.** Owner's
  own direction, correcting an earlier read that this was blocked on ops:
  *"like the existing codebase, I'd use configmaps to override defaults"*
  — so the public site's origin joins `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`
  and friends as an environment variable with a default that preserves
  today's behavior (`PUBLIC_SITE_URL` on the backend,
  `VITE_PUBLIC_SITE_URL` on the frontend; blank = served from the app's own
  origin, exactly as now). Setting them relocates the public site: every
  public link and QR code the app hands out points at the isolated origin
  instead. `CSRF_TRUSTED_ORIGINS` was also split from `CORS_ALLOWED_ORIGINS`
  so the public origin can *read* `/api/public/...` without being trusted
  for state-changing requests against the app — which is the whole point of
  isolating it. Full recipe in `docs/deployment-config.md`. **What's left is
  genuinely ops**, not repo work: the DNS record, a TLS certificate for the
  public hostname, and serving the frontend build at it. The
  sandboxed-iframe/CSP layer from the original checklist is deliberately
  *not* built — per the architecture note above, moving the whole public
  site off-origin may already satisfy what the per-page iframe was for;
  that should be re-evaluated once the origin actually exists rather than
  built speculatively.
  - **Resolved 2026-09-02 (see the scope note above):** relocation, not a
    rewrite and not an additive second layer — the whole public site
    (already-built pieces included) moves to the isolated subdomain.

A future build session should read `build-questions.md`'s full write-up
before starting this — it has the data-model sketch (a `Page` model,
scope field, landing-page pointer) and the exact remaining sub-decisions,
plus the relocation-scope architecture note above.
