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

- **D48 (found 2026-09-20 PM check-in) — Habitat has display names. It
  asks for one on two of its three account-creation paths, can store one
  on exactly one of them, and shows it in two places — while the person
  who owns the organization is the only one it never asks, with no way to
  ever add one.** The framing this lens inherited was that `User.email`
  is "the identity, the login, the attribution and the only display name
  there is". **The last clause is false:** `User.first_name`/`last_name`
  have existed since `accounts/0001_initial`, are delivered on every
  `UserSerializer` payload, and are rendered by `DashboardPage` (the
  greeting) and `rows.tsx` (the member row).

  Measured on the real endpoints against real PostGIS 3.4.2 /
  PostgreSQL 16 — not mirror models (the D46 lesson) — with the cache
  cleared before each request so D40's signup throttle couldn't turn a
  measurement into a 429:

  | Path | Asks for a name? | Stores one? |
  |---|---|---|
  | **Signup** (the founding user) | **No** — the form posts email, password, `organization_name` and nothing else | — |
  | Signup, with a name posted by hand | — | **Yes** — the endpoint has always accepted it; only the form doesn't ask |
  | **Add a member**, new email | **Yes** | **No** — `Invitation` has no name column at all; 201 |
  | **Add a member**, existing account | **Yes** | **No** — silently dropped; the 201 echoes back `first_name: ""` |
  | **Invitation accept** | Yes | **Yes** ✓ |

  **And there is no remedy, measured rather than assumed:**
  `PATCH /api/org/members/<id>/` with a name returns **200** and ignores
  it; `/api/auth/me/` is **405** for every write verb; there is no
  profile screen (`AccountPage` holds only "Change password") and no
  route in `apps/accounts/urls.py` that writes a user field — every
  `user.save()` in the backend is `update_fields=["password"]` or
  creation. **A name can only ever be set in the instant the account is
  created.**

  **The line that makes it matter:** the founding user is the one person
  guaranteed to exist in every organization and, per `vision.md`, the
  primary audience — so inside a single org the owner is greeted
  "Welcome back" while everyone who joined by invitation is greeted by
  name. Meanwhile **every place one human refers to another human's
  *work* uses a raw email**: nine `*_email` fields across five apps, and
  a real task row measured to carry `['assigned_to_email',
  'created_by_email']` and **zero** keys naming a person by name.

  **Severity, with what argues against it: not a security defect and not
  a leak.** Names never reach the public site (measured: org 1's public
  payload has zero `first_name` and zero `@`); the defect if anything
  stores *less*; on the invitation path the invitee is asked for their
  own name at accept time, so the admin's discarded name is only
  permanently lost if they leave it blank; and on the existing-account
  branch discarding is arguably correct — the defect there is the
  *asking*. What earns it a record is a control that looks available and
  isn't (the D13/D21 class), on the org-admin screen, with a **200** on
  the repair path.

  **Two manual bugs, recorded and deliberately not fixed** (this
  routine's scope — the 2026-09-08 (3) / 2026-09-12 (3) precedent):
  `docs/manual/limitations.md:210` asserts *"There are no display
  names"*, which is false; and `docs/manual/organization-admin.md:231`
  documents the Add-a-member form's *"First/last name (optional)"* —
  a control whose value is discarded. **The first correction is true
  whichever remedy the owner picks** (D35's property), which makes it the
  cheapest fork-free item in the queue.

  **Split. D48a — ✅ BUILT 2026-09-20 (2).** The two inputs are gone from
  `AddMemberForm`, and `first_name`/`last_name` are gone from
  `api.org.members.create`'s own parameter type, so sending one is now a
  compile error rather than a silent no-op (the shape, not just the
  absence — D38's lesson). Both manual claims corrected, plus an honest
  new `limitations.md` bullet: a name can only be set at account
  creation, and the person who starts the organization is never asked.

  **A 14th section in `apps/accounts/tests.py` (9 tests, suite 293 → 302),
  and it is this repo's one test section that does not meet its own
  "already regressed once" bar — stated in the section comment rather
  than left to be inferred.** Nothing in it fails against the pre-fix
  code, because D48a is a *frontend* change: the backend always behaved
  correctly, ignoring a name it was sent. The tests exist for the
  **attractive wrong fix**, which is the real hazard — "the form collects
  names and they're dropped, let's fix that" leads to the existing-account
  branch, which has a `User` in hand, and writing the admin's guess onto
  it renames that person **in every other organization they belong to**.
  A cross-tenant write (D12's family) reachable from a supported button.

  **Five wrong fixes built and measured; three have a sole catcher.**
  Write the posted name onto an existing account → 2 red. The
  unconditional-assign variant (`... or ""`), which *blanks* the name of
  everyone added without one — now every add — → 3 red. **`PATCH` writes
  the name → 1**, `test_patching_a_membership_does_not_rename_the_user`;
  **invitation-accept stops reading names → 1**,
  `test_the_invitee_names_themselves_at_accept`; **signup stops reading
  names → 1**, `test_signup_still_accepts_a_name`. Delete any one of
  those three and that wrong fix ships green. The last two matter because
  once the form stops sending a name, *"nothing sends `first_name` any
  more"* becomes a true-sounding reason to delete the handling from the
  only two paths that work.

  **One prediction corrected by the measurement, in the usual direction**
  (D38/D40/D45): `test_..._without_a_name_does_not_blank_theirs` was
  written as the sole catcher for the blanking variant. It is not — that
  variant also trips the posted-name test, so it fails 3 either way. What
  that test uniquely does is *distinguish* the two, and pin the property
  (adding a member never blanks a name) rather than catch a distinct fix.
  Recorded as measured rather than as the tidy table predicted.

  Storing the name on `Invitation`
  instead is *not* fork-free (a migration plus "may an admin name
  someone else?") and remains **D48b's Q1**. **D48b (the owner's, all
  three still open):** Q1
  should signup ask for a name? Q2 should a person be able to change
  their own name — or their own **email** — after the fact (the named
  successor's core: there is no path, so a contributor whose address
  changes must start a second account and split their own attribution)?
  Q3 should attribution show a name rather than a raw email — the
  question `limitations.md:210` currently explains away, and one
  **D38b's Q1/Q2/Q3 do not cover** (those are change history, photo
  uploaders and public credit), checked rather than assumed.

  Full measurement tables, the clean-audit inventory and the
  re-deferrals: `build-questions.md` (2026-09-20).

- **D47 (found 2026-09-21 PM check-in) — removing a member deletes the
  membership row and retracts nothing else, and the app refuses to create
  the state that removal leaves behind.** Measured on the real endpoints
  against real PostGIS 3.4.2 / PostgreSQL 16 (not mirror models — the D46
  lesson), by removing a real editor from a real organization:

  **What removal does close, measured rather than assumed:** every
  org-scoped endpoint 403s afterwards (`/api/tasks/`,
  `/api/activities/`, `/api/properties/`, `/api/org/members/` — four
  checked, not one), and a **new** task assigned to the removed person is
  refused with a 400 naming the rule. The boundary that matters holds.

  **What it does not touch:** the `User` row survives; their **existing
  session stays valid** (`/api/auth/me/` → 200 with `membership: null`);
  they can **log in again** (200); `GET /api/notifications/` still
  returns **200** with that organization's rows — carrying
  `organization_name`, the assigning admin's email and the task title —
  and they can still mark them read. Notifications are never purged
  (D30), so that set is readable for as long as the account exists.

  **The sharpest half, and the fork-free one.**
  `TaskSerializer.validate_assigned_to` rejects assigning a task to a
  non-member — and a task assigned *before* removal keeps pointing at
  that same non-member indefinitely, because `assigned_to` is `SET_NULL`
  on **User** deletion and removing a *Membership* is not deleting a
  User. The invariant is enforced at write time and never re-checked
  (D28/D46's shape). The organization's own UI then contradicts itself on
  one row: read mode renders *"Assigned to volunteer@example.com"* while
  the edit control — a `Combobox` resolving its value against the member
  list — cannot find that id and renders its placeholder, **"Unassigned"**.
  Nothing says the person left.

  **D28's own fix, landing where it was not aimed:** `organization_name`
  was added to notification rows so a multi-org user could tell which org
  a row came from. For a *removed* member it now labels each row with an
  organization they are no longer in — while the top bar beside it
  correctly shows none, because `TopBar` guards the org block on
  `session?.membership` and renders `NotificationsBell` outside it.

  **Severity, with what argues against it: not a security defect and not
  a leak.** No new content can reach them (assignment is refused), they
  had already received everything they can still read, and the dangling
  assignment is not silently corrupted — `tasks.update` is a narrow
  `PATCH`, so changing a row's status does not write the unresolved
  "Unassigned" back (checked, and the opposite of **D29**). **D3's shape
  on the membership axis** — a retraction that does not retract — with
  nothing private exposed.

  **Audited clean and recorded so it isn't re-derived:** attribution
  survives a departure correctly (`created_by`/`updated_by` are
  `SET_NULL` on *User* deletion and there is no user deletion, so past
  work keeps its name — the queue listed this as a loss; measured, it is
  the one part of departure that behaves); no cross-org leakage; the
  last-admin guard holds. And `notification_list`'s recipient-only filter
  **must not be "fixed"** with a membership check — that would hide a
  legitimate multi-org user's rows, which is the defect D28 fixed.

  **Split. D47a — BUILT 2026-09-19 (programmer session).** New
  `frontend/src/utils/assignee.ts` owns the rule; `Combobox` gained a
  `valueLabel` prop so a control can display a value its own options
  can't resolve; both of `TasksPage`'s renderings go through the helper;
  and the remove-member confirm counts open tasks. **No backend change,
  no migration.** Both queued traps held: the assignment is **not**
  nulled (Q2 stays undecided), and the confirm now names a number per
  D34.

  **Two things the queued framing did not have.** First, the load-bearing
  case is neither of the two states named: `TasksPage` fetches tasks and
  members as **two concurrent requests** and passed `members.data ?? []`,
  so "roster not loaded" and "roster is empty" were the same value. The
  naive fix therefore labels **every** assigned task *"no longer a
  member"* for the length of the fetch — a fix that makes the app lie
  about everyone to stop it lying about one person. Unknown had to be a
  real answer (D39's lesson); measured, that wrong fix fails 5 tests, the
  most of any variant. Second, the first working version **shipped a
  clipping defect and every assertion passed**: the qualifier was put
  inside the Combobox's input, and at 390px it rendered
  `volunteer@example.com — no lon`, because an `<input>` clips its value
  while `inputValue()` returns all of it. Caught by opening the
  screenshot, not by a test. The qualifier now lives in a wrapping
  `field-hint` note beside the control, and the browser run measures
  `scrollWidth` against `clientWidth` rather than asserting on a string.
  **D47b (owner's):** Q1 does removal retract what was already sent? Q2
  what happens to their assigned work? Q3 **can a person leave at all?**
  — measured: **no.** An editor or viewer cannot remove their own
  membership (403, `destroy` is admin-gated), there is no account
  deletion anywhere, and the last-admin guard means a **solo owner can
  never remove their own membership from their own organization**.

  **Q3 is D40b's Q2, re-framed, not a duplicate.** That question has been
  open since 2026-09-17 as an *operator* concern ("should an org or
  account ever be deletable/reclaimable?"). Asked from the **person's**
  side it is sharper, and that is the framing nobody had used — filed as
  a sharpening per D22's un-parking discipline.

  **The manual needed no correction, and the absence was written by the
  fixing session** (the D13/D24 precedent): `organization-admin.md`'s
  "Removing a member" grew from two sentences to what removal does and
  doesn't do; `tasks.md` gained "When an assignee leaves" and the flagged
  `tasks.md:4` sentence now carries the qualifier; `limitations.md`
  gained three honest bullets (nobody can leave, removal retracts no
  notifications, removal doesn't unassign). **Every factual claim added
  was verified over real HTTP rather than asserted** — including the new
  one, that re-adding the same address restores the membership and the
  task reads normally again (201, a *new* membership row for the same
  user id, so role and property scope are deliberately not remembered).

  **D47b is untouched and still the owner's.** D47a reports the state; it
  decides nothing about whether removal should retract (Q1), what should
  happen to assigned work (Q2), or whether a person can leave (Q3).

  Full write-up, the measurement tables and the re-deferrals are in
  `build-questions.md` (2026-09-21 for the finding, 2026-09-19 for the
  build).

- **D28 (found 2026-09-13 (3) PM check-in; fork-free half BUILT
  2026-09-13 (4)) — the app never names the organization you are acting
  in, and the one surface deliberately not scoped to it hands a two-org
  user another organization's task titles with nowhere to go.** Four
  independent places drop the organization dimension; each is defensible
  alone, and together they make a two-org user's app unattributable.

  **Built (the fork-free half), in two parts rather than one:** the top
  bar now names the active organization on every authenticated screen
  (labelled "Organization", its own full-width row on a phone, inline on
  desktop), *and* `NotificationSerializer` now carries `organization` +
  `organization_name`, which point 4 below shows was the actual blocker —
  the client was never sent the attribution, so no amount of frontend work
  could have displayed it. A notification from another organization now
  names that organization and does not navigate, since `/tasks` lists only
  the active org's tasks. **Q1/Q2/Q3 below remain open and untouched.**

  **One structural note for whoever takes Q1.** Rendering the org's name
  on the notification list required `select_related("organization")`, and
  `Organization` carries the `theme_header_image` blob — so the obvious
  join reintroduces **D27** (Django rebuilds a `select_related` target per
  row and does not dedupe it), invisibly, because the JSON is
  byte-identical either way. The view defers it via
  `defer_theme_image(qs, "organization")`. **Generalizable: D27's
  invariant is not self-maintaining — any new join to Organization or
  Property puts the blob back on the read path**, and only a mechanism
  test can tell the two apart.

  1. **A second membership is created silently, with one admin click.**
     `MembershipViewSet.create` (`accounts/views.py:765-775`) branches on
     whether the email already has an account. A brand-new email gets an
     `Invitation` and an emailed accept link; an email that **already has
     an account** gets `Membership.objects.create(...)` immediately — 201,
     no invitation, no email, **no `notify()` call**.
  2. **That membership can never become active.**
     `get_active_membership` takes `.first()` and
     `Membership.Meta.ordering = ["created_at", "id"]` makes that the
     **oldest**, so the added user's app is byte-identical before and
     after. The `Meta` comment (`models.py:46-52`) already names this
     scenario — but it was written for D2, which fixed the
     *nondeterminism*. **Nobody asked what the deterministic answer is for
     the user.** The fix made the wrong organization *stable* rather than
     random: strictly better, and still unreachable.
  3. **The organization's name is rendered nowhere in the authenticated
     app.** `MembershipSerializer` delivers the whole `Organization`
     object — name included — in every session payload; `TopBar` renders
     the logo and the user's email. Swept: the only places an org name
     appears are `SignupPage` (a form field), `AcceptInvitePage` and the
     two **public** pages — every one anonymous or pre-membership.
     **Confirmed live on the deployed host, read-only:** the Vite-served
     `TopBar.tsx`, `BottomNav.tsx`, `AppShell.tsx`, `DashboardPage.tsx`
     and `PropertiesPage.tsx` each contain **zero** occurrences of
     `organization`, against a positive control
     (`PublicOrganizationPage.tsx` → 10) and the 549-byte SPA-fallback
     negative control. Nothing was written to the live instance.
  4. **And the one surface deliberately *not* org-scoped cannot say which
     org it means.** `notification_list` (`notifications/views.py:18`)
     filters on `recipient` only, and its docstring says so on purpose — a
     notification is personal and should appear regardless of the active
     org. That intent is right; what follows from it today is not.
     `Notification` **has an `organization` FK**
     (`notifications/models.py:24`) and `NotificationSerializer`
     **omits it**, so the client is not merely failing to display the
     attribution — **it is never sent it**. The `message` is
     `f'You were assigned the task "{task.title}".'`, another org's
     content inside this one's chrome, and clicking it does
     `navigate("/tasks")` (`NotificationsBell.tsx:58`), which lists the
     **active** org's tasks. The task is not in it.

  **So a two-org user's bell shows another organization's task titles,
  with nothing naming that organization, and clicking one lands on a list
  that cannot contain it** — the "control that looks available and isn't"
  class (D13/D21/D23/D24), reached through a supported admin action.

  **This is the D24 shape again, and that is the reusable part.** The
  non-org-scoped notification list is a correct, deliberate,
  *forward-looking* decision, made in anticipation of multi-org. Multi-org
  never arrived, so a decision written for a future the app doesn't have
  produces, today, a notification you can't attribute and can't open. D24
  was a settled stance with an untraced consequence; this is a decision
  made **for a feature that was never built** — worth pointing at other
  forward-looking decisions here, not only settled ones.

  **Severity, not overclaimed: this is not a security defect and not a
  leak.** The recipient is a legitimate member of the other organization
  and is entitled to that task's title; no unauthorized party sees
  anything; every data queryset stays correctly scoped to the active org,
  and a sweep found no path by which another org's properties, activities,
  sightings or species reach a user acting here. What is wrong is
  attribution and actionability, not access. **Reachability, also honest:**
  it needs a genuine two-org user, and **whether any user on the
  deployment holds two memberships cannot be determined from here** —
  that needs database access, the same limit as the D6 backfill query, and
  is not implied by the two-organization count measured 2026-09-07 (3),
  which counts orgs rather than memberships. That changes the urgency, not
  the shape.

  **Split, so a build session can take the safe half without deciding a
  product question. The fork-free half: name the organization you are
  acting in — ✅ built 2026-09-13 (4).** The session payload already carries
  `membership.organization.name` on every load, so putting it in the app
  chrome is additive — no migration, no API change, no owner input. It is
  the half that answers the lens, because it makes every other symptom
  legible: an unattributed notification becomes attributable, and the one
  supported way the active org can *change* (removal from the older
  membership silently promotes the newer one) stops being silent. **It is
  also a prerequisite for the org switcher** — you cannot offer a switcher
  for something the interface never names. **The owner's half** is three
  questions that genuinely fork: **Q1** the org switcher itself (already
  queued as a feature; D28 is the argument that it has a cost *today*
  rather than only limiting a future); **Q2** whether adding an existing
  account to an organization should notify them — mechanically small,
  since `notify()` exists and `Notification.verb` is deliberately generic,
  but it **depends on Q1 and must not be taken first**, because a
  notification the recipient cannot act on is the D22 defect (an
  instruction the app gives no way to follow); **Q3** whether the admin's
  member list should say that an added existing-account member cannot
  currently see this organization — cheapest of the three, still a product
  call about what that row claims. PM recommendation: the naming half now,
  Q1 next, Q3 with it, Q2 only after Q1.

  **The manual is wrong in one place and it is left for the fixing
  session** (the D13/D19 precedent — documenting a dead end as intended
  behaviour would be the wrong fix): `docs/manual/getting-started.md:97-104`
  is titled with the question the app cannot answer ("Which organization
  am I in?") and answers it with a rule rather than anything a reader can
  check on screen, and its closing claim — *"your own account's first org
  is unaffected"* — is accurate about data and **false about what you
  see**. `limitations.md:12-14` records the lesser limitation and omits
  the notification consequence entirely.

- **D8 (found 2026-09-07 PM check-in; additive half built the same day):
  a signup that left the account name blank published the user's email
  address, and every organization is publicly readable whether or not it
  has published anything.** New signups no longer leak the address; the
  existing-row backfill (Q1) and the org-level visibility gate (Q2) are
  both still the owner's call — see the end of this bullet. Three
  facts that only matter together: `apps/accounts/views.py:105` names a
  nameless org `f"{email}'s land"`; that field is **optional** at signup
  (`SignupPage.tsx:26` — only email and password are `required`); and
  `apps/public_site/views.py:112-122` gates the public organization
  endpoints **not at all** — both `organization_detail` and
  `organization_detail_by_slug` are a bare
  `get_object_or_404(Organization, …)`, serving name, slug, theme and
  `created_at` to anyone. So a user who publishes nothing still has their
  email served unauthenticated at a stable URL, by both the numeric and
  the vanity-slug route. Verified on the live host (org id 2 is exactly
  this case; ids also enumerate — 1/2 → 200, 3/4/5 → 404, so the org
  count is discoverable). **The asymmetry is the point:** `Property`
  deliberately 404s when private so a guessed id "can't even confirm
  something exists" (the 2026-08-14 stance, still in that module's
  docstring), and `Organization` has no equivalent — the two halves of
  the same public site take opposite stances, and the ungated half is the
  one carrying an email address. **Scope, honestly:** no credentials and
  no private land data (`_organization_payload` filters `properties` to
  `is_public=True` correctly); what leaks is PII plus the existence and
  age of an account, to someone who was never told — neither the signup
  screen nor the manual says the account name is published.
  **The additive half is BUILT (2026-09-07 programmer run); the two
  forking questions stay open** — the same split D4 and D5 got.

  **Built, because it needed no decision:** signup no longer derives the
  organization name from the email. `Organization.DEFAULT_NAME`
  (`"My land"`) replaces the `f"{email}'s land"` literal, with the reason
  pinned in a comment on the constant so a later "friendlier default"
  can't quietly reintroduce it. No migration — it's a class constant, not
  a field — and **no existing row changes**, so no already-shared public
  URL breaks. The disclosure gap is closed too, in the three places that
  were silent about it: the signup field now says the name is shown
  publicly and what blank does; **Manage → Organization** says the name is
  public *and* that renaming alone doesn't change an existing public URL
  (the non-obvious half, per `models.py`'s slug rule); and the manual says
  both, plus states plainly that the org page is ungated. 7 tests in
  `apps/accounts/tests.py`, 6 of which fail against the pre-fix code.

  **Q1 — existing rows: still open, and deliberately not backfilled.** A
  backfill isn't free: `Organization.save()` regenerates a slug only
  `if not self.slug`, so renaming leaves the email-derived slug serving,
  and clearing it changes an already-shared public URL. That tradeoff is
  the owner's. **Org id 2 on the dev host is still exposed right now** and
  an admin can clear it today — but **both** the organization name *and*
  the **Public URL name** must be changed; the Manage screen now says so.

  **⚠️ Q1 re-measured 2026-09-22 (2), and for the first time the `slug`
  value itself was read rather than the payload's `@` count.** Still live
  fifteen days on. The slug is derived from the address with punctuation
  stripped, so the original is **reconstructable** from it with high
  confidence, and it occupies a slot in the one globally-unique namespace
  in the app (see D53). Address and slug both deliberately redacted from
  committed files, same reasoning as D8 itself. **Recorded as a
  correction to later summaries, not as a discovery:** this bullet's Q1
  already says renaming *"leaves the email-derived slug serving"* — it is
  the running one-line re-measurements in entries since 2026-09-07 that
  flattened it to "an email-derived organization **name**", and no run
  had actually looked at the slug. **The manual needs no correction
  either:** `organization-admin.md:51-62` already documents the exact
  two-step remedy and anticipates this case — *"if you're renaming to
  take something out of public view, do both"*. The fix was written down
  before anyone noticed it was needed. **Composes with D40:** nothing in
  the app deletes an organization, so a slug can be *changed* by its
  owner but never *freed* by the account going away — an abandoned signup
  holds its name in the shared namespace indefinitely.

  **Q2 — should `Organization` get an `is_public` gate mirroring
  `Property`? Still open, and still the larger question.** Default `True`
  preserves every existing public site but closes nothing on its own;
  default `False` closes it properly but darkens every published org until
  an admin re-enables it. Both defaults have a real cost, so a build
  session should not pick one. Recorded in `docs/manual/limitations.md` as
  a known gap rather than left undocumented, and
  `test_the_public_page_is_still_served` pins the current behaviour
  explicitly so a future reader can't mistake the passing suite for "the
  org page is gated now".

  **Re-measured 2026-09-07 (3) PM check-in, and both questions get
  smaller — this is the part to read before answering them.** The
  framing above was written from the code; measuring the live host
  changes what each question actually costs.

  - **Q1 is one row, not a policy.** The deployment holds **exactly two
    organizations** (ids 1 and 2 → 200; 3-10 → 404). Org 1 is `test`,
    unaffected. Org 2 is the only email-derived one. So "backfill
    existing rows" is a single admin action, and the tradeoff that made
    it the owner's call — *clearing a slug breaks an already-shared
    URL* — is at most one tester's own link, not a fleet of them.
    **No migration and no code are needed for it:** `OrganizationSerializer`
    accepts a blank `slug` write meaning "regenerate from the name"
    (`extra_kwargs`, and `Organization.save()` re-slugifies an empty
    slug), so changing the name *and* clearing the Public URL name on
    **Manage → Organization** fixes it today — the exact two-step the
    2026-09-07 build put on that screen. Q1 remains a question only for
    *future* rows, and new signups are already fixed.
  - **Q2 would not have protected org 2 anyway, which the earlier text
    implied it would.** That entry described the case as an account that
    "publishes nothing at all". On the live host org 2 **does** publish —
    one public property, `Shop yard`, `is_public=True`. So an
    `is_public` gate on `Organization` defaulting to `True`, or derived
    from "has this org published anything", leaves org 2 exposed exactly
    as it is now. Q2 is still a real architectural question about the
    asymmetry with `Property` — but it is **not** the remedy for the
    live exposure, and answering it should not be mistaken for closing
    it. Only Q1's rename does that.
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

- **D46 (found 2026-09-20, PM check-in — build-ready, no owner input
  needed for the `a` half): Habitat declares Django's own
  `EmailValidator` on every address it stores and has never run it once.**
  `User.email` and `Invitation.email` are both `models.EmailField`, whose
  validators run only on `full_clean()` — which appears **zero times**
  backend-wide. The usual second line of defence, a DRF serializer field,
  is also absent: **`serializers.EmailField` appears zero times**, because
  all four entry points read the raw body
  (`views.py:101` signup, `:155` login, `:265` password reset, `:811`
  member-add), each `(request.data.get("email") or "").strip().lower()`.
  So no layer validates the format of an address, anywhere.
  **Measured on the pinned Django 5.2.17**, reproducing signup's path
  verbatim on plain non-GIS models: **12 of 12 malformed strings become
  real, permanent accounts** — `not an email`, `chris@`, `@example.com`,
  `chris`, `a@b@c.com`, `chris smith@example.com`, `<script>alert(1)</script>`,
  a 312-character local part — and **11 are invalid per the validator
  already attached to that very field**.
  **The sharp half is what the browser does and doesn't cover.** The
  signup form's `<input type="email" required>` is the only check that
  exists; measured in **real Chromium**, it refuses all the malformed
  garbage and **accepts every case that actually happens to a person**:
  `chris@gmial.com` (transposed letters), `chris@example.co` (dropped
  letter), `chris@gmial` (HTML5 email validation does not require a TLD),
  someone else's real address, and the 312-char local part Django's own
  field would refuse at 254. The protection and the real-world failure
  mode barely overlap. **This inverts D44**, where a browser genuinely
  rescued the user — *"the browser papers over it"* is a claim to measure
  per case, not a property of browsers.
  **Fourth instance of "a control that is configured and does nothing"**
  after D40's `NUM_PROXIES`, D43's `AnonRateThrottle` and D45's five mail
  variables.
  **Why now:** D45's point is that SMTP is the owner's next action. The
  moment mail leaves, the reset flow is a locked-out user's only recovery
  path (no admin-set password since 2026-08-26; no self-serve fallback,
  deliberately and correctly), and by D22's equally correct
  anti-enumeration design the reply is byte-identical — so a wrong
  address is unrecoverable and the app is *required* to say nothing that
  would reveal it. Inert today because nothing is delivered, which is
  exactly the window in which it is free to fix.
  **Severity, with what argues against it:** not a live exploit, no
  escalation, no cross-org reach, nothing leaked — a bad address harms
  only the account that owns it. Header injection is **not** achievable
  (the newline case raises `BadHeaderError` at send time, measured,
  though the account is still created holding a newline) and there is no
  XSS path (one `dangerouslySetInnerHTML` in the frontend, the
  sanitized-markdown branch; React escapes the rest).
  **Nothing guards it:** zero tests touch email format, and D45's
  `habitat.W001` is about the transport, not the recipient.
  **Not done deliberately:** no signup was performed on the live host —
  it would leave a permanent, unremovable tenant (D40: no deletion path
  anywhere). What carries the measurement to the deployment instead is
  D43's probe: `/api/health/` reports revision `b78e080`, byte-identical
  to `git rev-parse HEAD`.
  **D46a — ✅ BUILT 2026-09-19 (programmer session).** New
  `apps/accounts/email_addresses.py` owns the rule and both helpers;
  `views.py` routes all four sites through them. The rule the module
  states, which is narrower than "validate at four sites": **validate
  where an address is *stored* (signup, member-add), normalize
  everywhere, and leave the paths that merely *look one up* (login,
  password reset) alone.** Those two create nothing, so there is nothing
  to keep clean — and rows written before this existed may hold a
  malformed address, which a guard there would lock out of sign-in and
  out of recovery respectively. Normalization moved into one function at
  all four sites, which makes the casing property (audited correct, but
  correct by four separate coincidences) structural. **No migration.**
  **Two inherited claims were corrected by re-measuring rather than
  transcribing**, both in the same direction — the witness was wrong, not
  the finding:
  ① *"a bare `EmailValidator()` leaves the 312-char case through
  (refused only by `max_length`)"* — **it does not**.
  `EmailValidator.__call__` refuses anything over **320** characters (RFC
  3696), so that case is caught by the validator, for a different reason
  than the one it was chosen to demonstrate. A test written with that
  witness **passes against the naive fix** and leaves the length check
  unpinned. The real gap is the band from **255 to 320**: accepted by the
  validator, longer than the column. *The witness that demonstrates a
  trap can pass for the wrong reason* — D27's lesson moved one step
  earlier, from the test to the example.
  ② *"12 of 12 become real, permanent accounts"* — true of the mirror
  models it was measured on, **not of this app**. On the real Postgres
  column an over-length address raises `DataError: value too long for
  type character varying(254)`, which is not an `IntegrityError`, is
  caught nowhere in this backend and has no DRF handler: an unhandled
  **500**. So D46a also converts a 500 into a 400 — D13/D18/D26's shape,
  in a fourth place. *A finding reproduced on a stand-in is a finding
  about the stand-in* (the 2026-09-15 (2) lesson, earned again).
  The third trap held exactly as written: the newline case was caught
  downstream at send time, after the account existed; a test now pins
  that no account is created.
  **D46b (owner's): verification itself — this is D40b's Q1**, below,
  unanswered since 2026-09-17. D46a does not answer it: format validity
  is not reachability, and `chris@gmial.com` passes everything D46a adds.
  **Its value rises rather than falls now**, because the manual can
  finally state the distinction precisely (format checked, reachability
  not), which makes the remaining gap the only one left to close.
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
- **D22 (found 2026-09-11 PM check-in; fork-free half ✅ BUILT 2026-09-11
  programmer session — the owner's half below is still open): the "forgot
  password" flow tells a
  locked-out user a reset link "has been sent" on a deployment that sends
  no email — and that page is the one screen in the app with no route to
  the caveat.** `apps/accounts/views.py:194-196` answers every request with
  *"If an account exists for that email, a reset link **has been sent**."*
  — a flat assertion of an accomplished fact. Six facts, and only together
  do they matter: (1) `settings.py:292` defaults `EMAIL_BACKEND` to the
  **console** backend, which logs and delivers nothing; (2)
  `send_password_reset_email` is **best-effort**, catching and logging its
  own exceptions, so an unreachable SMTP server yields the *same* 200 and
  the *same* sentence — **the response is byte-identical whether the mail
  was delivered, silently failed, or was written to a log file**; (3) the
  flow **deliberately has no fallback**, because handing the link back
  would be an enumeration oracle (a correct decision, and exactly what
  leaves the user nowhere to go); (4) **an admin cannot help** — there is
  no admin-side password reset since the admin-sets-a-password field was
  removed 2026-08-26, so recovery needs Django admin or the console log;
  (5) `/forgot-password` sits **outside `RequireAuth`/`AppShell`**
  (`App.tsx:64`) while the **Help** link that opens the manual lives only
  in `BottomNav.tsx:74`, *inside* `AppShell` — so the one screen where the
  caveat matters is the one screen with **no in-app route to it**; (6) the
  message never hedges, and it is the last thing the user sees before
  waiting. **The asymmetry is the sharpest framing and the fix is already
  written in this repo:** three surfaces claim an email will arrive and
  exactly one is honest — `AddMemberForm`'s success message
  (`rows.tsx:720-721`) says *"Invitation sent to X. **If the email doesn't
  arrive**, copy the link from the pending invitation below and share it
  yourself"*, while the **Resend** button twelve lines away
  (`rows.tsx:234`) says only **"Sent!"** and the reset confirmation says
  **"has been sent"**. **Severity ranked honestly:** the two invite
  surfaces have a visible fallback *on the same screen*, so a stuck admin
  can self-serve — those are wording bugs; the reset flow has none by
  design, so it is a **dead end presented as success** landing on the
  person already locked out. Confirmed live (the deployed host returns that
  exact string; probed with an **empty** email, the branch where
  `user is None`, so no token was minted and **nothing was written to the
  live instance**). **The manual is already right** —
  `getting-started.md:63-67` and `limitations.md:15-25` both say delivery
  isn't configured and the link only reaches the console log — so **no
  manual edit applies**; the fix makes the app match accurate
  documentation (the D16/D19/D20 shape). One note for the fixing session:
  `getting-started.md:59-60` **quotes the message verbatim**, so changing
  the string makes that quote stale and it must be updated in the same
  pass (the D19 precedent). **Split:** the **fork-free half** is to stop
  asserting delivery at the two un-hedged sites, using `AddMemberForm`'s
  hedge as the precedent — the anti-enumeration constraint is *not* a
  blocker, since a message can stop claiming delivery without branching on
  whether the account exists. **The owner's half** is whether a
  locked-out user gets a real way out: (a) wording only; (b) let the app
  know whether email works, following the `GET /api/feedback/config/`
  precedent — **not an enumeration oracle, because it is a property of the
  *deployment*, not of any address**; or (c) an admin-side password-reset
  action, a real feature and security decision. PM recommendation: (a)
  now, (b) next, (c) only if wanted. **This item is deliberately *not*
  blocked on the email-delivery question above** — that is why earlier
  check-ins kept leaving the resend "Sent!" un-queued, and separating them
  is the point: whatever a deployment's mail situation, a message
  asserting a delivery the server never verified is wrong, and correcting
  it needs no answer about SMTP. See `build-questions.md`, 2026-09-11 (3).

  **✅ What was built (2026-09-11 programmer session) — the wording half,
  option (a).** The reset reply is now
  `PASSWORD_RESET_REQUESTED_DETAIL`, a named constant carrying its own
  rationale, reading *"If an account exists for that email, a reset link
  has been **requested**. Email delivery isn't configured on every Habitat
  deployment — if nothing arrives, contact whoever runs this one."*
  "Requested" is precisely what the function can vouch for, and the second
  sentence gives the locked-out reader somewhere to go — which is as far
  as (a) can reach without deciding (b) or (c). The **Resend** button now
  reads "Resent" and the card shows a hedge pointing at the **Copy invite
  link** button beside it (that screen *has* a self-serve fallback, which
  is why the two surfaces are worded differently rather than identically).
  `getting-started.md`'s verbatim quote was updated in the same pass, per
  the note above, and `organization-admin.md` gained the Resend caveat.

  **The test earns its place by pinning the constraint, not the copy**
  (`PasswordResetRequestGivesOneAnswerTests`, 4 tests, section 7 of
  `apps/accounts/tests.py`). Asserting the literal string would only have
  to be edited alongside every future copy change. Instead three tests pin
  the **anti-enumeration property** — a known and an unknown address get
  byte-identical responses, the empty-string third branch lands on the
  same answer, and a token is still minted for the real address (so the
  identity isn't achieved by making both sides no-op) — and a fourth pins
  the **mechanism**, that the message doesn't state delivery as
  accomplished fact.

  **Both halves were measured, and the pairing is the point.** Against the
  real pre-fix string, **1 of 4 fails** — only the mechanism test; the
  three enumeration tests pass happily, because "has been sent" was
  equally generic and equally unbranched. Then the **plausible-but-wrong
  fix** was built (per the D17/D18 lesson): stop over-claiming delivery
  *and* be helpfully specific — "A reset link has been requested for your
  account." for a real address, "We couldn't find an account for that
  email." otherwise. That **passes the mechanism test and fails the two
  enumeration tests**. So neither half of the section is redundant: the
  mechanism test catches the original bug and is blind to the wrong fix;
  the enumeration tests catch the wrong fix and are blind to the original
  bug. **A defect and its most tempting bad fix can need entirely
  different tests** — checking only that the red path reproduces the bug
  would have left the more dangerous regression uncovered.

  **Still open, and deliberately untouched:** the owner's half — (a) is
  now done, so the live question is whether to add **(b)** an
  `email_configured` flag so the page can say the true thing rather than a
  generic hedge, or **(c)** an admin-side reset action. Also still
  unanswered and still the cheapest one-line answer in the queue:
  **does `habitat.dev.cravenator.com` actually have SMTP configured?**
  Nothing built here can determine that, which is the finding restated —
  the user can't either.

  One thing looked at and deliberately left: `ForgotPasswordPage`'s
  subtitle still says *"we'll send a link to reset your password."* That
  is forward-looking intent rather than a claim about an accomplished
  fact, and the confirmation beneath it now carries the caveat; hedging
  every string on the screen would make the page noisier without making
  it more honest.
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

- **D49 (found 2026-09-20 (4) PM check-in) — every login leaves a row in
  `django_session` forever; Django ships the one command that removes
  them and this repo runs it nowhere, eleven lines below the purge it
  *does* run. D49a is takeable and fork-free; D49b (Q1/Q2/Q3) is the
  owner's. But the lens's real answer is that this is not what is
  accumulating.**

  **Measured on the pinned Django 5.2.17 and real PostgreSQL 16.13**, with
  a settings module mirroring Habitat's in setting neither value:
  `SESSION_ENGINE` resolves to `django.contrib.sessions.backends.db` (a
  table), `SESSION_COOKIE_AGE` to **14 days**, and
  `SESSION_SAVE_EVERY_REQUEST` to `False` — so one row per **login**, not
  per request. Habitat's `login_view` calls plain
  `django.contrib.auth.login()`, so the row holds the three standard
  `contrib.auth` keys and nothing else (`session_data` averages 227
  chars; 1,000 logins measured at 679,936 bytes total relation size,
  indexes included, ≈ **680 B/row**).

  **The framing this corrects: expiry is not eviction.** The queued
  successor said *"there is no session expiry setting anywhere."*
  Sessions **do** expire — at fourteen days — and
  `docs/manual/getting-started.md:97-98` documents that accurately. An
  expired row does **not** authenticate (measured: `SessionStore.load()`
  returns `{}`). What is missing is **eviction**: the dead row stays.

  **The mechanism, measured, because the obvious guess is wrong.**
  `auth.login()` calls `cycle_key()`, which deletes the prior row — so
  five logins from a browser that still holds a valid cookie leave **1**
  row. Five logins with no prior cookie (the 14-day lapse, cleared
  cookies, a new device, a private window) leave **5**, every one orphaned
  permanently. Logout is clean: measured, it deletes the row.

  **`clearsessions` appears zero times in this repo** — not in
  `entrypoint.sh`, not in a Dockerfile, not in CI, not in any doc — and it
  is the **only** cleanup command Django ships (checked against
  `get_commands()`). Measured: it removes exactly the expired rows (6 of
  10 backdated past expiry → 6 gone, 4 untouched).

  **The asymmetry that earns it a record:** `backend/entrypoint.sh`
  already runs `purge_deleted_properties` on every boot, to honour a
  retention promise, with a comment explaining why it sits outside
  `set -e`. Eleven lines below that, the one table that grows on an action
  every user takes gets nothing, and the remedy needs no code. Same family
  as D46 (Habitat declares Django's own `EmailValidator` and never runs
  it) and D45 (six mail variables read and ignored). And **D42's lesson
  one layer on for the operator doc**: `deployment-config.md` mentions
  sessions only as *cookies*, never as *rows* — it documents everything
  adjustable and nothing that accumulates.

  **Severity, with what argues against it — this one is easy to
  overclaim.** Not a security defect (an expired row does not
  authenticate). **Not stranger-reachable:** `request.session` is touched
  by **zero** lines of application code, the only session writes being the
  four `login()` calls; confirmed read-only on the live host, where
  anonymous requests to `/`, `/api/public/organizations/1/` and
  `/api/auth/csrf/` set **no `sessionid`** — only `csrftoken`, a cookie
  rather than a row. **And it will never be a size problem.** For D32's
  own 25-contributor scenario over a year: photos **52.2 GB** (inherited
  from D32, not re-measured here) against **863 KB** of sessions — ~63,000×
  — and even a deliberately absurd session case (10 logins/user/day, 59 MB)
  is ~900× smaller. **So the honest answer to "what is quietly
  accumulating?" is photos, which is already D32 and already the owner's
  fork.** D49a is worth doing because it is one line using Django's own
  command and the pattern is already established in that same file, not
  because the bytes matter. **Not determinable from here:** whether the
  deployment runs its own `clearsessions` CronJob (its config is outside
  this repo — the D6/D28 limit).

  **Audited clean under the same lens**, recorded so it isn't re-derived:
  `PasswordResetToken` keeps **used** tokens forever (`views.py:286`
  deletes only a user's *unused* ones when they ask again) — tiny, folded
  into Q2; `Invitation` keeps expired and accepted rows — tiny;
  `Notification` never purged (already **D30's retention half**);
  soft-deleted `Property` is genuinely **bounded** by its 30-day window,
  so D36's entrypoint half is about *when*, not *whether*; `Feedback`
  keeps resolved rows; `django_admin_log` has no built-in purge and is
  negligible, since an org admin is not a Django staff user (the D38
  precedent); nothing grows per request; and D40's throttle state is
  `LocMemCache`, which dies with the pod.

  **✅ D49a BUILT 2026-09-20 (5) (programmer session).** `entrypoint.sh`
  runs `clearsessions` next to the property purge, outside `set -e`;
  `deployment-config.md` gained **"What accumulates"** (the ranking, the
  session rate, the engine table) and a fourth row in the
  replica table; `config/tests.py` gained `SessionEvictionTests` (8 tests,
  suite **302 → 310**). No migration, no frontend change, no user-facing
  change.

  **The build found a fifth instance of this repo's "configured and does
  nothing" class, latent in the fix itself.** Django's `clearsessions`
  raises `CommandError` only for an engine that raises
  `NotImplementedError` — and **none of the five shipped backends does**.
  Measured on Django 5.2.17 against real PostgreSQL with 6 expired and 4
  live rows: `db` and `cached_db` remove 6; **`cache`, `file` and
  `signed_cookies` exit 0, print nothing, raise nothing, and remove
  zero**. The `cache` case is reachable rather than theoretical —
  `deployment-config.md` already tells an operator to stand up a shared
  cache backend before scaling. So the sweep is pinned by a structural
  test (is the configured store a `db` subclass?), not just by outcome.

  **Two numbers were re-measured rather than transcribed, and one
  correction is worth keeping.** A first pass built sessions by hand and
  got **508 B/row**; writing 1,000 through Django's real `login()` gives
  **672 B/row** with `session_data` at 227 chars, reproducing the
  check-in's figure. *The hand-built stand-in under-reported by a
  third* — D46's lesson a second time, and the reason the operator doc
  quotes the `login()` number. Ratio versus photos re-derived: **64,183x**
  against sessions alone — and measuring notifications as well (303 B/row)
  put the *combined* row-shaped total at 1.6-4.6 MB a year, which
  falsified the inherited "under a megabyte" line this run had copied
  into the operator doc. Corrected before commit.

  **Eight wrong fixes measured, and the sole catcher is the weakest
  assertion in the section.** Deleting the sweep from `entrypoint.sh`,
  moving it under `set -e`, and shortening `SESSION_COOKIE_AGE` instead of
  sweeping are **each caught by exactly one test** — and it is the same
  one, a grep over a shell script. Delete it and all three ship green: a
  command that works, is covered by five passing tests, and runs nowhere.
  Also measured: `cached_db` is a *safe* change and goes 1 red (the
  deliberateness test) where `cache`/`file` go 4 — a gradient that
  distinguishes "someone chose something else" from "the sweep is now
  inert". **One prediction was wrong** in the standing D38/D40/D45/D48
  direction: `cached_db` was predicted 0 red, and the test it tripped had
  a docstring claiming a property broader than its assertion (D46's trap
  in a test name). Corrected in place rather than the memory of it.

  Original spec, kept for reference: run `clearsessions` where
  this repo already runs its other purge, and give `deployment-config.md`
  the section it lacks — what accumulates, at what rate, what removes it.
  Two notes, neither a fork: it belongs **outside `set -e`** for the
  identical reason the property purge is (that comment is already written,
  eleven lines up); and **the attractive wrong fix is to reach for
  `SESSION_COOKIE_AGE` instead**, which changes how long people stay
  logged in — a user-visible product change, and Q1 below — while removing
  not one row.

  **D49b (the owner's). Q1: how long should a session last?** Nobody has
  chosen; fourteen days is Django's inherited default and
  `deployment-config.md` exposes no knob for it — the "value that was
  never chosen, only inherited" cousin of D40's `NUM_PROXIES`. **Q2:
  should the other row accumulators get a retention policy at all?** This
  is **D30's retention half generalized** (notifications, expired
  invitations, used reset tokens), filed as one question because the
  answer is one policy. **Q3: is boot-time sweeping the right
  mechanism?** A **sharpening of the existing "a real cron for the purge"**
  item rather than a duplicate (D22's un-parking discipline, the D47b Q3
  precedent) — what is new is that there are now *two* things wanting a
  schedule.

  **The manual needs no correction, and that is the finding's shape**
  (D16/D19/D33/D38/D45/D46): `getting-started.md:97-98` is accurate, and
  `limitations.md` already documents notifications growing forever and
  photos stored full-size. The session table is invisible to end users, so
  it is an operator concern and belongs in `deployment-config.md`, exactly
  where D36's rollback, D42's database prerequisite, D43's probes and
  D45's mail config went.

- **D45 (found 2026-09-19 PM check-in) — an operator can set every SMTP
  variable this repo documents and deliver nothing, and the log they
  would check prints a complete, correct-looking email. Measured against
  the real `settings.py` on the pinned Django 5.2.17. D45a ✅ BUILT
  2026-09-18, and the run went past the docs half: the contradiction is
  now a startup warning. D45b (Q1/Q2/Q3) remains the owner's.**
  `settings.py:466` reads six email variables and
  `deployment-config.md`'s table lists all six in one row — but
  **`EMAIL_BACKEND` is the switch, and the other five are inert without
  it.** Measured: host + port + user + password + TLS + from-address all
  set, and the connection used is still the **console** backend.
  **This inverts stock Django, which is what makes it a trap:**
  `global_settings.EMAIL_BACKEND` in 5.2.17 is
  `django.core.mail.backends.smtp.EmailBackend`, so in an ordinary Django
  project setting `EMAIL_HOST` and credentials *is* how you configure
  mail. Habitat overrides that default, so the operator most likely to
  get it wrong is the one who already knows Django.
  **It fails silently, and the instrument reports success.** `send_mail`
  under the console backend **returns 1** and raises nothing, so both
  senders' `except Exception: logger.warning(...)` never fires and
  nothing records that delivery did not happen. The stdout it writes
  instead is a complete RFC-822 message carrying the operator's own
  configured `From`, the right recipient, subject and body — so an
  operator checking the container log for *"did it send?"* finds what
  reads as proof that it did. **The instrument is blind to the case under
  test**, the same family as 2026-09-14's `response.body()`,
  2026-09-13's substring filter, and 2026-09-18's `/api/health/`
  revision. **Third instance of "a control that is configured and does
  nothing"** after D40's `NUM_PROXIES` and D43's `AnonRateThrottle`.
  **The clean-audit result is what makes it precise:** a genuinely
  failing SMTP send *is* loud — a real `ConnectionRefusedError` produces
  a visible warning plus traceback on stderr, measured, despite Habitat
  setting no `LOGGING`. So the two adjacent cases have opposite signal
  quality and **the silent one is the default**. Without that contrast
  this would only be "SMTP isn't set up yet," which the docs already say
  honestly.
  **Separable second consequence:** the console backend writes a
  **working** reset link (1 hour, single use) and invitation link (7
  days) in plaintext to the container log — confirmed in the same
  measurement. Working as designed on a single-tenant dev instance, and
  `password_reset.py`'s docstring says so; it stops being fine the moment
  there is a log aggregator, a hosting provider or a second admin.
  **Why it wasn't recorded before — D22's un-parking lesson, fourth
  application.** D22 read this exact code in 2026-09-11 and its test
  comment already names the console-backend problem exactly. It then
  fixed the message shown to the **user**, correctly. Nobody asked the
  **operator**-facing half: their configuration is accepted and inert,
  the send reports success, and the log shows a correct email. The parked
  reason ("SMTP is undecided") was true of the *decision* and hid a
  *defect* sitting beside it.
  **Severity, with what argues against it:** not live breakage and not a
  security defect — SMTP has never been configured anywhere, so nothing
  is failing today that wasn't already known to be off. A latent trap on
  the path the owner's own stated next action walks; the mirror image of
  D42, which crashloops loudly where this reports success forever.
  **Not determinable from here:** whether the dev host sets
  `EMAIL_BACKEND` (its environment isn't readable — the D6/D28 limit, and
  testing it would mint a token into that host's log, deliberately not
  done).
  **Nothing guarded it** — **zero** Django system checks touched email
  configuration (grepped `django/core/checks/` in the installed 5.2.17,
  deploy checks included), D43's readiness probe says nothing about mail,
  and no test covered the backend. **That is what changed.**
  **✅ BUILT 2026-09-18 (programmer session), both the docs half and a
  guard.** Every measurement above was re-run against the real settings
  module rather than inherited, and reproduces exactly (all six variables
  set → console; `send_mail` returns 1; no exception; the operator's own
  `From`; the reset token in plaintext on stdout).
  `deployment-config.md` now breaks the one crowded table row into six
  real rows and gains an **"Email delivery"** section carrying the
  measured table, the stock-Django inversion, the log sample, and the
  credential-in-the-log note. **Beyond D45a:** new
  `apps/accounts/checks.py` raises `habitat.W001` when a mail server is
  configured while `EMAIL_BACKEND` is still the console backend —
  registered as an **ordinary** check, not a deployment one, which is the
  load-bearing decision: `manage.py check` and `manage.py migrate` both
  skip deployment checks (exactly how D7 sat unread), and `migrate` is
  what `entrypoint.sh` runs at every container start. Measured on the
  real app: the warning prints to stderr during `migrate` and the command
  still **exits 0**, so it is loud in the operator's own log without
  turning a mail misconfiguration into a crashloop. It is a **warning
  rather than an error deliberately** — whether a `DEBUG=0` boot should
  *refuse to start* on the console backend is **Q2 below**, still the
  owner's, and this does not pre-empt it. It keys only on `EMAIL_HOST`/
  `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`, never on the three settings
  with non-empty defaults, so a deployment that never configured mail is
  never warned. Pinned by 12 tests in `apps/accounts/tests.py`'s twelfth
  section (273 backend tests, up from 261); all three plausible wrong
  fixes were built and run, and the measurement **corrected the
  prediction twice** (see `build-questions.md`). **The manual needed no
  correction** — `limitations.md:24-34` and `getting-started.md:80-82`
  are both accurate and D45 falsifies neither; only that file's test
  count moved. Full write-up in `build-questions.md` (2026-09-19 for the
  finding, 2026-09-18 for the build).

- **D44 (found 2026-09-18 PM check-in) — every photo URL the API
  publishes begins `http://`, and that URL returns 404. Measured on the
  live deployment, read-only. Docs half ✅ BUILT 2026-09-18; code half
  still open, and still the owner's.**
  **Re-measured independently this run rather than inherited**, and it
  reproduces exactly: the published URL is 404 with no redirect, the
  identical path over `https://` is 200 / 1,899,250 B / `image/jpeg`,
  and the five `build_absolute_uri` call sites are confirmed present.
  **Built:** `deployment-config.md` now states the variable's *second*
  consequence — that behind a TLS-terminating proxy it decides the
  scheme of every absolute URL the API emits, not just whether
  `SECURE_SSL_REDIRECT` loops — with the measured 404/200 table, the
  note that **browsers hide this** by auto-upgrading a passive `http://`
  image subresource (which is why the app's own grids look fine and
  twelve days passed unnoticed), who is *not* rescued by that (the
  Phase 4 public API, feed readers, link checkers, image proxies,
  scripts), and the in-repo precedent that already avoids it
  (`invitations.py` building `accept_url` from `FRONTEND_URL`). The
  table row now says the same in one line. True under every remedy, so
  it pre-empts none of them.
  **Code half deliberately NOT built, with the reason stated rather than
  implied.** The PM recommendation was remedy (a) —
  `TRUST_X_FORWARDED_PROTO=1` — *after* checking the proxy overwrites
  `X-Forwarded-Proto`. **That check cannot be made from here:** with the
  flag off Django ignores the header entirely, no endpoint echoes request
  headers, and the deployment's proxy config lives outside this repo — so
  there is no observable that distinguishes "proxy sends it" from "proxy
  does not". Setting the flag without that answer is the unsafe case
  `settings.py`'s own comment names. It is also not a repo change at all:
  it is a deployment environment variable. Remedy (b) (relative URLs) is
  *wrong* for a documented supported shape — the isolated-public-origin
  deployment `PUBLIC_SITE_URL` exists for, where a relative URL resolves
  against the public site's origin rather than the API's. Remedy (c) (a
  new configured API-origin value) adds an env var that remedy (a) would
  make redundant. Three remedies with real tradeoffs and one unavailable
  measurement is a genuine design fork, so it goes to the owner rather
  than being guessed at. Original finding follows. Chasing the F1 feedback item to the
  photo it names surfaced this on the way: the public payload for
  activity 5's photo carries
  `"url": "http://habitat.dev.cravenator.com/api/public/activities/5/photos/2/image/"`.
  Fetched as given, that URL is **404** (port 80 is reachable and serves
  a JSON 404 with no redirect — the same shape D7 recorded in
  2026-09-06 (4)). The **`https://`** form of the identical path is
  **200, 1,899,250 bytes, `image/jpeg`**.
  **Mechanism, read from the code rather than inferred:**
  `TRUST_X_FORWARDED_PROTO` defaults to `0`, so `SECURE_PROXY_SSL_HEADER`
  is `None` (`settings.py:376-379`), so behind the TLS-terminating proxy
  `request.is_secure()` is False, so `request.build_absolute_uri()`
  emits `http://`. **Five call sites do this** — `public_site/
  serializers.py:33` and `:49` (public activity and sighting photos),
  `public_site/page_serializers.py:71` (a custom-HTML page's
  `document_url`), `activities/serializers.py:302` and
  `sightings/serializers.py:185` (the authenticated app's own photo
  URLs). So it is both public and authenticated, not one side.
  **The `http://` response is itself the measurement that the
  proxy-protocol chain is not wired up** — whichever half is missing
  (the flag unset, or the proxy not sending the header), the observable
  and the consequence are identical, so the finding does not depend on
  knowing which.
  **Severity, honestly, including what argues against it: no user-visible
  breakage is confirmed, and the feedback item is the evidence.** The
  user saw photos on the edit page well enough to ask to enlarge them,
  and that page renders this exact `http://` URL — so their browser
  auto-upgraded the passive mixed content to `https://`, where the
  upgrade succeeds. Modern browsers do this. **This is a latent
  correctness defect in a published contract, not a live outage**, and
  it should not be raised as urgent. What earns it a record is who is
  *not* a browser: the **Phase 4 public API** is explicitly planned and
  would hand consumers dead links; so would a feed reader, a link
  checker, an image proxy, a script, or any client that does not
  implement auto-upgrade. A browser is silently papering over it, which
  is exactly why nobody has noticed in the twelve days since the setting
  was parked.
  **The un-parking argument, and it is this finding's real contribution.**
  `TRUST_X_FORWARDED_PROTO` has been open since **D7 (2026-09-06)**,
  parked as half of a security decision — the
  `SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair. That parking
  reason was never re-tested, and the variable turns out to have a
  **second, entirely independent consequence** nobody had traced: it
  also decides the scheme of every URL the API emits. So a question
  filed as "a hardening option we have not gotten to" is in fact
  "the switch that makes our own published URLs work." **D22's
  un-parking lesson, third application** (D22 itself, then D40's re-test
  of the parked "add rate limiting" item) — *a parking reason ages, and
  nobody re-reads it.*
  **The docs half, which is fork-free and tiny.**
  `deployment-config.md:38` describes the variable as *"Lets Django read
  the original scheme from `X-Forwarded-Proto`"* and `:246-254` frames
  it purely as the partner of `SECURE_SSL_REDIRECT` — *"enable both or
  neither."* Both statements are true and the security reasoning is
  careful and correct. But an operator reading that table concludes "I
  am not using the redirect, so I do not need this" and silently
  publishes dead URLs. **The table documents one consequence of the
  variable and not the other** — the same shape as D42's finding that a
  configuration table documents everything adjustable and nothing
  required.
  **The in-repo precedent for the code fix already exists and the photo
  serializers never got it:** `accounts/invitations.py:27`'s
  `accept_url` builds its link from **`settings.FRONTEND_URL`**, a
  configured value, not from the request — which is why emailed
  invitation links are not affected by this at all. QR codes likewise
  prefer the configured origin (2026-09-02). Deriving an origin from
  configuration rather than from the request is already this repo's
  answer to this problem, applied in two places and missing in five.
  **Three remedies, and the choice is a real design question rather than
  mechanical, so a build session should state it:** (a) set
  `TRUST_X_FORWARDED_PROTO=1` — smallest correct change, fixes all five
  sites at once, and closes a queued question; **but it must first be
  verified that the proxy actually sets *and overwrites*
  `X-Forwarded-Proto`, because setting the flag without the header
  changes nothing, and trusting a header a client can set is the unsafe
  case `settings.py`'s own comment names**; (b) emit a **relative** URL,
  which needs no new config and is strictly better for the frontend
  (the production build already defaults to a relative `/api` per D5) —
  **but it breaks in the isolated-public-origin deployment
  `PUBLIC_SITE_URL` exists for**, where a relative URL resolves against
  the public site's origin rather than the API's; (c) a new configured
  API-origin value, following the `accept_url` precedent. **PM
  recommendation: (a), after the header check, plus the one-line docs
  fix regardless of which is chosen** — the docs half is true and worth
  making under every remedy.
- **D42 (found 2026-09-17 (3) PM check-in) — the deployment contract
  names 24 environment variables and never names the database, so the
  first production boot crashloops.** `docker-compose.yml`'s own header
  calls `docs/deployment-config.md` "the contract between the two"; that
  file has ten sections and states nowhere that the database must have
  the PostGIS extension, nor a version floor. **No migration creates it
  either** — `CreateExtension` and `postgis` appear **zero** times across
  every `migrations/*.py`. Dev works only because `docker-compose.yml`
  pins `postgis/postgis:16-3.4`, whose init scripts create the extension
  for you.

  **Measured on a real plain PostgreSQL 16.13** (initdb'd in the sandbox
  precisely because it has no PostGIS package — exactly what a stock
  Kubernetes Postgres operator hands you): Django's own backend probe
  `SELECT postgis_lib_version()` → `function ... does not exist`; the DDL
  `accounts/0001_initial` emits, `geometry(Polygon,4326)` → `type
  "geometry" does not exist`; and the operator's obvious fix,
  `CREATE EXTENSION postgis` → `extension "postgis" is not available`.
  `migrate` runs in `entrypoint.sh` **inside `set -e`**, so the pod
  crashloops.

  **Severity, honestly, including what argues against it:** this is
  **loud, not silent**, which is the failure shape this repo actually
  fears; it is not a security defect; and prod does not exist yet, so
  nothing is live. What earns it a record is timing — the owner's stated
  next action is "tag a version and stand up prod", this is the first
  thing that stand-up hits, and neither error message contains the word
  "install". Related absence found in the same sweep: **`createsuperuser`
  appears in zero docs**, though Django admin is the only place the
  per-tenant custom-HTML kill-switch can be set.

  **The transferable point is about the instrument:** a prerequisite is
  not a variable, so it had no row to fall into. **A configuration table
  documents everything adjustable and nothing required.**

  **Split. D42a is BUILT (2026-09-17 programmer session); D42b is still
  the owner's.** `deployment-config.md` gained two sections — **"The
  database"** (the requirement stated plainly, the measured failure table
  above, the version matrix, the `CREATE EXTENSION` step, and the
  privilege caveat that is also *why* no migration does it) and **"First
  boot"** (the five-step sequence, including `createsuperuser` and why
  skipping it locks the custom-HTML kill-switch away, and explicitly
  naming the three things still undecided rather than implying the list is
  complete). `docker-compose.yml`'s `db:` service now carries a comment
  saying its image tag is load-bearing — that pin creating the extension
  is *why* the requirement went unstated for the life of the project, so
  the note lives where the next person looking at it will be.

  **Two numbers were re-derived rather than inherited**, since the
  original write-up had none: Django 5.2.17's `minimum_database_version`
  is **PostgreSQL 14** (read from the installed code, not a doc), and
  there is **no hard PostGIS floor** in Django's PostGIS backend — it
  probes at runtime and disables individual features — so the doc says
  "match the pinned 3.4" rather than inventing a minimum. Verified end to
  end this session on PostgreSQL 16.15 / PostGIS 3.4.2 / GEOS 3.12.1.

  *D42b (owner's, unchanged):* should `accounts/0001` gain a
  `CreateExtension("postgis")`? Not obviously right — that generally
  needs superuser, and on an operator-provisioned Postgres the app role
  usually isn't one, so it would swap a clear error for a confusing
  permissions error. Only the owner knows the prod privilege model. The
  documented prerequisite now covers the case either way, so this is no
  longer blocking a first boot. Full write-up in `build-questions.md`
  (2026-09-17 (3) and the 2026-09-17 (4) BUILT entry).

- **D43 (found 2026-09-17 (3) PM check-in) — there is no health endpoint,
  and the obvious probe path returns 200 whether or not anything works.**
  `health`, `healthz`, `readyz`, `livez` and `/version` appear in **zero**
  `urls.py`. Measured on the dev host: `/healthz` → **200, 549 bytes**,
  **byte-identical to a known-nonexistent path** (control), against a real
  endpoint's 28 bytes. It is the SPA fallback — **D23's trap and D39's
  `robots.txt` finding in a third place**, this time in the one place
  whose whole job is to answer "is this working?".

  The production frontend image keeps the SPA fallback, so this carries
  into prod, and the consequence splits with only one half loud: an HTTP
  probe against the **frontend** pod is **vacuous** (every path is 200
  from nginx whether or not the backend or database is up — a green light
  that cannot go red), while a probe against the **backend** pod is a
  Django 404 and would crashloop a *healthy* pod.
  `deployment-config.md` has no probe guidance.

  **The manual already documents the fallback accurately, and that is the
  finding's shape** (D16/D19/D33/D38, not D13): `limitations.md:275-282`
  names the two consumers it misleads — a link checker and a search
  crawler. **D43 is a third nobody listed**, and the only one that decides
  whether live traffic reaches your pod. No manual sentence is falsified;
  the gap is an absence. *A known-and-documented behaviour is not the same
  as a fully enumerated one — the audience list is where these hide.*

  **This also absorbs the version-identity successor, corrected
  downward.** The inherited framing said "nothing tells a running instance
  which build it is"; measured, *image*-level identity **does** exist —
  `docker-publish.yml` passes `metadata-action`'s labels to
  `build-push-action`, whose defaults include
  `org.opencontainers.image.revision`/`.version` (verified from the
  workflow wiring; **not** confirmed against the registry, which
  rate-limited the config-blob fetch — worth one `docker inspect` at the
  first release). What is genuinely missing is *runtime-queryable*
  identity: nothing the app serves reports a version, and
  `frontend/package.json` still says `0.0.0`. **PM recommendation:** one
  `/api/health/` returning `{"status", "version"}` and touching the
  database gives Kubernetes a real probe target *and* answers "what is
  running?" — which is why these are one item, not two.

  **BUILT 2026-09-17 (programmer session), with two deliberate
  deviations from that recommendation, both recorded because each is a
  judgement call a later session could reasonably want to reverse.**

  **1. Two backend endpoints, not one.** `/api/health/` (liveness, never
  touches the database) and `/api/health/ready/` (readiness, does). The
  recommendation's single database-checking endpoint is the one a
  `livenessProbe` reaches for by name — and a failing liveness probe makes
  the kubelet **kill** the container, which does not fix a database. A
  ten-second restart would become CrashLoopBackOff that outlives it: D43's
  own "loud and wrong in the other direction" shape, reintroduced by D43's
  fix. **Measured with PostgreSQL genuinely stopped** (not mocked):
  liveness stays 200, readiness returns 503, and readiness recovers to 200
  on the first request after the database returns, with no restart.

  **2. Readiness queries `SELECT postgis_lib_version()`, not `SELECT 1`.**
  This is the join to D42: a connectivity-only check reports ready against
  the plain-PostgreSQL database D42 measured, while every request touching
  a geometry column fails. **Verified against a real PostGIS-less
  PostgreSQL database**, created for the purpose: `SELECT 1` succeeds
  there, and readiness correctly returns 503.

  **The runtime-identity half is closed too, and the mechanism matters
  more than the field.** `version` and `revision` are **baked into the
  image** by `backend/Dockerfile` from build arguments
  `docker-publish.yml` fills in from the tag and the commit — not read
  from the deployment's environment. A version somebody has to remember
  to set is a version that eventually lies, and for a field whose entire
  job is "what is running?" a confident wrong answer is the only failure
  that matters. Unset reports **`null`**, never `"unknown"` or `"dev"`:
  `latest` genuinely has no version number (zero git tags — D37), so null
  is the true answer rather than a gap, and `revision` is what identifies
  that image.

  **The frontend half is fixed and honestly bounded.** `nginx.conf` gains
  an exact-match `/healthz` returning a 3-byte `ok`, so a probe there is
  no longer byte-identical to a nonexistent path. It still only proves
  nginx is serving — and the reason is now documented rather than left to
  be discovered: **a Kubernetes probe addresses the pod directly and never
  passes through the ingress**, so from the frontend pod `/api` does not
  exist. Verified: `GET /api/health/` against the frontend container
  returns the SPA fallback, 200 with HTML.

  **The trap that will actually bite an operator was found by measuring,
  not reasoning, and it is the most valuable line in the new docs.**
  Kubernetes defaults an `httpGet` probe's `Host` header to the **pod
  IP**, which is never in `ALLOWED_HOSTS`, so Django answers **400** and
  the kubelet kills a healthy pod. Measured live with
  `ALLOWED_HOSTS=localhost,127.0.0.1`: `Host: 127.0.0.1` → 200,
  `Host: 10.42.0.7` → 400 — and at `DEBUG=0` the body is Django's generic
  "Bad Request (400)" page, which names neither the setting nor the
  rejected host, so the symptom gives you nothing to search for. The
  probe recipe in `deployment-config.md` sets the header explicitly, and a
  test pins the behaviour so that recipe is checkable rather than
  folklore.

  **The manual was checked and deliberately not changed** beyond its test
  count. `limitations.md`'s fallback bullet stays true as written — a
  mistyped address still answers 200 — and the third consumer D43 names is
  an operator, not an end user, so it belongs in `deployment-config.md`,
  where it now is.

- **D40 (found 2026-09-17 PM check-in) — `/api/auth/login/` is an
  unauthenticated CPU amplifier, and the thing making it expensive is a
  control that must not be removed.** `login_view` is `AllowAny` and
  unthrottled; `settings.py` sets no `PASSWORD_HASHERS`, so Django
  5.2.17's default `pbkdf2_sha256` at **1,000,000 iterations** applies.
  Measured on the repo's own pinned Django (median of 8):
  `check_password` **582 ms**, `make_password` **584 ms** — about **1.7
  attempts per second per core**.

  **No precondition is required, and this is verified in Django's source
  rather than assumed.** `ModelBackend.authenticate` runs
  `UserModel().set_password(password)` when the user does *not* exist,
  deliberately, "to reduce the timing difference between an existing and
  a nonexistent user (#20760)". So the full hash is paid for **any**
  email — no account, no valid address, no knowledge of the instance.

  **Confirmed live with a single request** (one bogus login naming a
  `.invalid` address — indistinguishable from a mistyped password;
  nothing was written): **1.09 s**, against a control baseline of
  0.34–0.52 s on `/api/auth/csrf/` and `/api/public/organizations/1/`.
  Subtracting leaves **~0.6 s of server CPU**, matching the local number.
  **~400 request bytes and effectively zero client CPU buy ~600 ms of
  server CPU.**

  **Why this is not the "add rate limiting" item already parked since
  2026-08-27.** That item is parked explicitly as a design question —
  *which endpoints, what limits, what store* — and that framing is what
  kept it parked for three weeks. This is D22's un-parking lesson: part
  of it does not depend on the open question. *Which endpoint* is now
  measured (login dominates every other unauthenticated path, being the
  only one running a deliberately-slow KDF). *What limit* is a constant a
  build session picks and states, the explicit D17 precedent. *What
  store* is answerable today and entangled later — see below.

  **The inversion that makes D40 a different species from every prior
  resource finding here.** D17 was fixed by **bounding the resource** —
  cap the pixels, decode less. **D40 cannot be**, because the resource
  consumption *is* the security control: a cheaper hash is weaker
  password storage for every user. There is no version of this fix that
  reduces the cost. Bounding the rate is the only remedy.

  **Store caveat, flagged in advance.** There is **no `CACHES` setting**,
  so Django's default per-process `LocMemCache` applies, and DRF's
  throttles use the Django cache. Fine on today's host — D5's
  `runserver` is one process, re-confirmed this run via
  `server: WSGIServer/0.2 CPython/3.12.14` on the login response — and it
  degrades **silently to per-worker limits** the moment a production
  image introduces more than one worker. Not a blocker now; a real
  decision the day D5 is answered.

  **The write amplifier is signup**: same 584 ms KDF plus **14 rows**
  (User, Organization, Membership, 3 `WorkflowState`s, 8 `ActivityType`s
  from the two `post_save` receivers in `apps/activities/signals.py`),
  unauthenticated and uncapped — **and nothing in the app can ever remove
  one.** There is no `OrganizationViewSet` at all (only a GET/PATCH
  detail view), no account-closure path, no user deletion outside Django
  admin, and **no email verification anywhere**. Every signup is
  permanent, unverified and free.

  **The lens in one sentence:** Habitat has six limits —
  `MAX_PHOTO_BYTES`, `MAX_THEME_IMAGE_BYTES`, `MAX_LOGO_BYTES`,
  `MAX_LOGO_PIXELS`, `CUSTOM_PAGE_HTML_MAX_BYTES`,
  `NOTIFICATION_LIST_LIMIT` — and **every one is a per-request size cap,
  not one a per-account quota or a per-time rate.** `throttle` appears
  **zero** times backend-wide; `REST_FRAMEWORK` declares no throttle
  classes; `User` has no attempt counter, lockout field or
  `email_verified` flag; quota/billing/plan/tier/seat/payment vocabulary
  returns **zero** matches. The app can say "this request is too big" and
  can never say "you have asked too many times" or "you have stored too
  much."

  **Audited clean under the same lens**, recorded so it isn't re-derived:
  the other two KDF paths — `password_reset_confirm` and
  `invitation_accept` — are protected by **entropy, not rate limiting**
  (each requires a `secrets.token_urlsafe(32)`, 256 bits), so they are
  not D40 surfaces and must not be "fixed"; `password_reset_request` runs
  **no hash at all**, and its real abuse vector (repeated sends, per-send
  cost once SMTP exists) **was already recorded in the 2026-08-27 task
  log** and is deliberately not re-filed; and `limitations.md:101`
  already records the photo half accurately.

  **Severity, honestly, including what argues against it.** Not a
  data-exposure defect and not live: no cross-org reach, no escalation,
  nothing leaked, and the host still holds exactly **two** organizations
  (re-measured read-only — ids 1/2 → 200, 3/4/5/6 → 404, unchanged).
  **What cannot be determined from here:** whether the edge layer
  rate-limits. The login response carries no rate-limit, WAF or CDN
  header and the `WSGIServer` banner shows requests reaching Django
  directly, but a limiter need not mark a *non*-limited response, and
  proving absence would require sending a burst — which this run
  deliberately did **not** do. The honest claim is that the *application*
  has no limit, not that the deployment has none.

  **✅ D40a BUILT 2026-09-17 (programmer session).** `login_view` at
  **10/min per client address**, `signup` at **5/hour**, via
  `apps/accounts/throttling.py`. Five deviations from the sketch below,
  each for a stated reason:

  - **`SimpleRateThrottle` subclasses, not `ScopedRateThrottle`.** That
    class reads its scope off a `throttle_scope` attribute of the *view*,
    and these are `@api_view` functions with nowhere clean to hang one.
  - **Not `AnonRateThrottle` either**, which returns no throttling at all
    once `request.user` is authenticated — and `signup` calls `login()`,
    so that class would leave the endpoint that creates permanent tenants
    effectively unlimited. Measured: it fails 5 of the 16 new tests.
  - **`NUM_PROXIES` defaults to 0, not DRF's `None`.** `None` keys on
    `X-Forwarded-For` when present, which the client sets — an attacker
    varies it and is never throttled, a limit that is visible in the diff
    and refuses nobody. 0 pins the key to `REMOTE_ADDR`; a proxied
    deployment sets `THROTTLE_NUM_PROXIES`. Failing too strict is loud,
    failing open is silent.
  - **The rates are module constants, not `DEFAULT_THROTTLE_RATES`** —
    the `MAX_PHOTO_BYTES` precedent, and it keeps settings.py from
    importing an app module before the app registry loads.
  - **The `LocMemCache` caveat is answered rather than pinned.** The
    owner's "Kubernetes, single containers" makes per-process state
    correct today; the production image therefore ships **one gunicorn
    worker and four threads**, since N workers would make the limit N
    times looser in-pod with no error. Not a performance compromise —
    measured, CPython's `hashlib` releases the GIL for pbkdf2, so four
    concurrent 1,000,000-iteration hashes finish in **1.23x** the wall
    time of one. `deployment-config.md`'s new "Running more than one
    replica" section names what must change before scaling.

  **Five wrong fixes were built and measured** (D38's correction applied:
  disjointness is a claim to measure, and the first draft's prediction was
  wrong twice — see the section comment in `apps/accounts/tests.py`). The
  two caught by exactly one test each are the interesting ones: a limit
  checked *after* `authenticate` returns a byte-identical 429 while
  spending the identical 600 ms, and DRF's default `NUM_PROXIES` leaves a
  throttle that does nothing. Delete either test and the wrong fix ships
  green.

  **And the defect only looking found**, seventh time in this repo's
  history: DRF's `Throttled.__init__` appends its own *"Expected available
  in N seconds."* to any detail it is given, so the first working refusal
  stated the wait twice, in two registers. Every assertion passed against
  it — each checks that advice is *present*, and nothing that looks for a
  missing thing can see a duplicated one. Found by reading a real response
  off a real gunicorn. Now pinned by two assertions.

  Original sketch, kept for the record: throttle `login_view`
  and `signup` with DRF's own `ScopedRateThrottle`, pick and state the
  constants per D17's precedent, and pin the `LocMemCache`/D5 caveat at
  the setting. Two notes: a limit tight enough to matter also catches a
  legitimate user fumbling a password, so the refusal must say *when to
  try again* rather than reading as a broken login (the D13/D21 class);
  and the throttle must key on something an attacker cannot vary freely —
  **keying on the submitted email is the attractive wrong fix**, trivially
  bypassed by varying it, and worth building to confirm a test catches
  it. **D40b (owner's):** Q1 should signup verify the email address? Q2
  should an organization or account ever be deletable/reclaimable, given
  nothing in the app can remove either? Q3 does Habitat have any concept
  of a plan, quota or tier at all — the actual "who pays" question, which
  the data model has never had an answer for. PM recommendation: D40a
  now, Q1 next (cheapest, and it bounds Q2's blast radius), Q2/Q3 once
  the hosting model is decided.

  **No manual change applied at the time, and that was the finding's
  shape** (D16/D19/D33/D38, not D13): nothing in `docs/manual/` claimed
  Habitat limits login attempts, verifies an email, or caps anything per
  account, so no sentence was falsified. What was missing was an
  *absence* — written by the fixing session, per the D13/D24 precedent:
  `getting-started.md` now describes both limits, and `limitations.md`
  gained three honest bullets (only two things are rate-limited and
  nothing is per-account; nobody checks a sign-up address is real; an
  account or organization cannot be deleted from inside the app).

- **D36 (found 2026-09-16 PM check-in) — rolling a deploy back silently
  half-works: the app reads fine and 500s the moment anyone writes.**
  D33 added four digest columns, all declared
  `CharField(max_length=64, blank=True)`
  (`accounts/models.py:159,287`, `activities/models.py:227`,
  `sightings/models.py:70`). Django emits
  `ADD COLUMN ... DEFAULT '' NOT NULL` followed by `DROP DEFAULT`, so each
  ends up **`NOT NULL` with no database default**. Old code doesn't know
  the field, omits it from its INSERT, and Postgres rejects the row.

  **Measured on real PostgreSQL 16 and the pinned Django 5.2.17**, on
  plain non-GIS models mirroring `ActivityPhoto` (the D12/D14/D18
  technique): old code **reads** every existing row correctly; old code
  **writing** a new one raises `IntegrityError: null value in column
  "image_sha256" … violates not-null constraint`.

  **The shape is the finding.** `manage.py migrate` — what
  `entrypoint.sh` runs on every boot, inside `set -e` — **exits 0**
  against a database carrying migration records that aren't on disk.
  Django applies what it knows and moves on. So the container starts
  cleanly, nothing warns that the schema is ahead of the code, browsing
  looks healthy, and **the rollback reports success**. The failure is
  deferred to the first write.

  **The two worst-affected tables aren't the photos:**
  `accounts_organization` (so **signup** breaks) and `accounts_property`
  (creating a property breaks), alongside both photo tables. It surfaces
  as a **500** — there is no custom `EXCEPTION_HANDLER` (re-verified) and
  `IntegrityError` is caught in exactly one place in the backend,
  `apps/species/views.py` (D26's fix), which is none of these paths.

  **The remedy exists, works, and is documented nowhere.** Measured as a
  full loop: down-migrate to match the rolled-back code → old code writes
  again → re-deploy the fixed image → `entrypoint.sh`'s own `migrate`
  re-applies and **every row, including those written during the rollback
  window, gets a correct digest** (checked against `hashlib`); the
  backfill's `WHERE image_sha256 = ''` guard is what makes it idempotent.
  A repo-wide sweep for rollback/down-migrate guidance returns **nothing**,
  and `docs/deployment-config.md` has eight sections on running Habitat
  and none on recovering it.

  **Audited clean under the same lens**, so it isn't re-derived: **every
  data migration in the repo is reversible** — all six `RunPython`/
  `RunSQL` operations carry a reverse, some real and some deliberate
  no-ops with the reason stated in the file. Old code reads correctly, so
  there is no corruption and nothing silently mis-served.

  **Split.** The **fork-free half** is a "Rolling back a deploy" section
  in `deployment-config.md` — reads keep working while writes 500, which
  migration each release added, and the exact down-migrate command; this
  run measured that the procedure works. The **owner's half** is whether
  `entrypoint.sh` should *detect* the schema-ahead condition and refuse to
  start, trading a silent half-outage for a loud total one. PM
  recommendation: document first, decide that after.

  **✅ The docs half was BUILT 2026-09-15 (programmer session)** — a
  "Rolling back a deploy" section in `docs/deployment-config.md`. That run
  re-measured the whole loop rather than inheriting it, and did so **on
  the real repository** (a `git worktree` at `e3db16f^`, the actual
  pre-D33 commit, against a real PostGIS database) rather than on mirror
  models — which confirmed every claim above on the genuine migrations,
  and turned up **one the check-in missed, which is the sharpest
  operational detail of the whole finding:**

  **The rolled-back image cannot perform its own down-migrate.**
  Reversing a migration requires the migration *file*, and the image you
  roll back to does not have it. Measured: `manage.py migrate activities
  0004` run from the pre-D33 code **exits 0, prints "No migrations to
  apply", and leaves the column in place** — verified against
  `information_schema` afterwards. So an operator who rolls back first and
  then tries to fix the schema gets a second, deeper layer of the same
  silent success, at precisely the moment they are most likely to believe
  the problem is solved. **The down-migrate has to run from the outgoing
  image, before the swap.** Now the load-bearing warning in that section.

  **One correction to the audit above, kept because the instrument was
  wrong in the safe direction.** "All six carry a reverse" is true, but a
  grep for `reverse_sql`/`reverse_code` does **not** establish it —
  `activities/0003` passes its reverse *positionally*, so the grep reports
  zero markers for a migration that is perfectly reversible. Re-checked
  with Django's own `sqlmigrate --backwards`, which is authoritative: all
  six reversible. A grep that can be vacuous in the reassuring direction
  is the D27/D30 substring trap in a new place.

  **Still open: the owner's half** — should `entrypoint.sh` refuse to
  start when the schema is ahead? The new finding strengthens the case
  (there are now *two* silent successes between an operator and a working
  rollback, not one), but it is still a real tradeoff and the build
  session deliberately did not pre-empt it.

- **D37 (found 2026-09-16 PM check-in) — there is nothing to roll back
  to.** Queried against Docker Hub rather than inferred from the
  workflow, which is what makes it exact:
  `cravenator/habitat-frontend` publishes **`latest` and nothing else**;
  `cravenator/habitat-backend` has `latest` plus two leftover
  commit-sha tags (`46f93e9`, `cda0015`) from 2026-08-26/27. The repo
  holds **zero git tags and zero GitHub releases**, so
  `docker-publish.yml`'s `type=semver` rule **has never fired**.

  So the frontend has **no rollback target at all**, and the backend's two
  are accidental residue — they exist only because `type=sha` was removed
  on 2026-08-27 *after* they were pushed, nothing produces new ones, and
  both predate D6, D7 and D10, so rolling back to them reintroduces every
  security fix since.

  **Stated fairly:** the owner's 2026-08-27 instruction (*"I only want
  latest from the main branch, GitHub tags/release for other tags"*)
  **already contains a durable-version mechanism**, and the existing
  workflow implements it — a `vX.Y.Z` tag builds both images as a matched
  set. It has simply never been used. This is a capability never
  exercised, not a missing one.

  **Rollback also needs a compatible *pair*, and nothing records one.**
  Conditional per-folder builds mean backend and frontend `latest` come
  from different commits (measured: backend pushed 2026-09-14T22:43Z,
  frontend 2026-09-15T10:26Z) — correct for forward deploys. But API
  shapes change: D30 turned `/api/notifications/` from a bare list into
  `{"results": [...], "unread_count": N}`, so an old frontend against a
  new backend breaks the bell. **"Roll back only the broken half" is
  therefore itself unsafe.**

  **The owner's, and it is one line: start cutting `vX.Y.Z` releases?**
  No code change needed. PM recommendation: yes — a documented rollback
  with no artifact to roll back to is still not a rollback.

  **Severity, honestly:** not a security defect, and **not live** — no
  rollback has been attempted and the affected host is the dev instance.
  A latent recovery defect, measured rather than observed. **What can't be
  determined from here:** the host's deploy config is outside this repo,
  so whether its 15-minute refresh pulls `latest` or pins a digest isn't
  visible (the D6/D28 no-access limit).


- **D35 (found 2026-09-15 PM check-in) — nothing in this repo backs
  anything up, and the reason that is expensive to fix is D33's own
  measurement.** Confirmed rather than assumed: **zero** occurrences of
  backup/`pg_dump`/`pg_restore`/`dumpdata`/snapshot anywhere outside
  prose; `.github/workflows/` holds two workflows and **neither has a
  `schedule:` trigger, so there is no scheduled job of any kind**; and
  `docs/deployment-config.md` has eight sections on how to *run* Habitat
  and none on how to *restore* it. The one `restore` in the codebase is
  soft delete's, which covers one model and is a different thing.

  **The measurement corrects the natural assumption.** "Postgres dumps
  compress, so a backup is about the size of the data" holds for ordinary
  rows and **fails for this database specifically**, because photo bytes
  don't compress (D33 measured ~2% on a real JPEG). Measured on real
  PostgreSQL 16 against 20 `bytea` rows at D32's measured 12 MP photo
  size (43,155,720 B total, verified incompressible at 0.10%):
  `pg_dump` plain — **the default** — is **2.00x** the photo bytes
  (86,313,821), because `bytea` is rendered as hex *before* compression;
  `pg_dump -Fc`, the usual advice, is **1.14x** (49,161,376); and **no
  setting reaches 1.00x**, since DEFLATE on a 16-symbol alphabet can't
  quite undo the hex expansion. Projected onto D32's 52.2 GB/year: a
  compressed backup is **59.5 GB/year** and the no-flags default is
  **104.4 GB/year**. `pg_restore` returned byte-exact data in 2.63 s for
  41 MB (~16 MB/s on this sandbox) — order-of-magnitude, an hour per
  year of photos, and nobody has a real number.

  **What a restore needs beyond the database:** `SECRET_KEY` from the
  environment, whose loss invalidates **sessions only** — invitation and
  password-reset tokens are random DB columns, not signed values, so they
  survive. Nothing else lives outside the database and the environment.

  **This is the owner's**, and downstream of the still-open hosting
  question — where dumps live, what retention, who tests a restore. **No
  code is blocked on it.** One separable sub-question: should
  `limitations.md` say plainly that Habitat itself backs up nothing?
  Unlike D32/D33's absences that sentence is true whichever remedy is
  chosen, and it is the one thing that would let a user protect
  themselves today. PM recommendation: yes.

  **✅ That sub-question only was taken 2026-09-15** (scheduled programmer
  session). `limitations.md` now states it — **and how it is worded is
  the point, because the check-in's hesitation was well founded.** It had
  recommended the sentence while noting it was the owner's call "since it
  describes a deployment they run". Those are two different claims, and
  only one of them is a session's to make: **what the *software* does is
  a fact about this repo** (nothing — no export, no dump, no restore
  path, verifiable by the sweep above), while **what any given deployment
  does is not visible from here at all.** The bullet says the first,
  explicitly declines the second, and tells the reader to ask whoever
  runs their instance rather than assume either way. So it is true
  whichever remedy the owner picks and it preempts nothing.

  **The rest of D35 is untouched and still the owner's** — whether
  Habitat grows a backup mechanism, and question 3 below, which a session
  cannot answer: *is anything backing up the dev host today?*

- **D29 (found 2026-09-13 (3) PM check-in) — a record edit writes back
  every field from the snapshot the form opened with, so a typo fix
  silently reverts a colleague's whole edit.** **There is no optimistic
  locking anywhere** — swept: zero `If-Match`, zero `ETag`, zero
  conditional writes in the backend or the client. That much was already
  known. What had not been looked at is **what a save actually sends**,
  and it is wider than "last write wins on the field you touched":
  `ActivityFormPage.handleSubmit` PATCHes `activity_type`, `status`,
  `geometry`, `date_planned`, `date_done`, `notes` and `is_public` —
  **every field, from values loaded when the page opened**. An editor who
  opened the form before a colleague saved, and only meant to fix a typo
  in the notes, silently reverts that colleague's status change, both
  dates, the public/private flag **and a redrawn boundary**.

  **The app is already inconsistent about this, which is the useful
  part.** The inline auto-apply controls the 2026-09-11 (3) check-in
  audited (`MemberRow`'s role select, `TaskRow`'s assignee and status)
  narrow-PATCH a single field; the full-page forms are the wide ones.
  **And `updated_at` is already on the wire and read by nothing** — it is
  serialized on properties, activities, sightings, pages and tasks, and no
  write path consults it. The same shape as D27 one layer up: the data
  needed is loaded, delivered, and never used.

  **The attractive wrong fix is named here in advance, because the last
  two cycles proved naming it is necessary and not sufficient.** The
  tempting move is **send only changed fields**. It would shrink the blast
  radius from the whole record to the fields actually touched, and it is
  **the D18 trap exactly**: it reduces the collision count while leaving
  the race entirely intact — two editors on the same field still silently
  last-write-wins, and the symptom stops announcing itself. A build
  session **must not take the narrowing as the fix**, and if it writes a
  mechanism test it must build the narrowing and measure what that turns
  green, per the 2026-09-13 (2) lesson that knowing the wrong fix does not
  tell you whether your tests stop it.

  **Recorded as a question, not a build-ready item** (the D5/D8/D11 call,
  not D3/D27's): the honest fix is a conditional write, and **how a
  conflict is surfaced is a product decision** — refuse with a 409 and
  reload, merge, or warn and let the user choose. PM recommendation: worth
  doing before the second editor arrives rather than after, but it is the
  owner's shape to pick.

- **D27 (found 2026-09-13 PM check-in; ✅ BUILT 2026-09-13 programmer
  session) — every list endpoint loaded the image bytes it is careful
  never to serialize; 100 sightings on a themed property cost 500 MB, and
  Django does not dedupe.** Habitat stores
  images in the database (a decided choice). Two of the four
  `BinaryField` columns sit on **main tables** —
  `Organization.theme_header_image` (`accounts/models.py:152`) and
  `Property.theme_header_image` (`:278`) — and **there is no `.defer()`
  or `.only()` anywhere in the backend** (swept: zero).

  **What makes this invisible is that the serializers are right.** Both
  carry a comment saying the banner is "never serialized as raw bytes
  over JSON" and expose a `has_theme_header_image` boolean instead;
  `ActivityPhotoSerializer` says the same about `image`. All true — and
  none of it says anything about what the *queryset* loads. Both
  `get_has_theme_header_image` implementations read
  `theme_header_image_content_type`, the small `CharField`, never the
  blob. **Swept: 8 raw-blob reads and exactly 4 photo `.image` reads,
  all twelve single-object byte-serving/upload/delete views. Not one is
  on a list path.** So the bytes are pulled from Postgres by every list
  query and consumed by none of them.

  **Measured on the repo's pinned Django 5.2.17 against mirror non-GIS
  models (the D12/D14/D18 technique), each with a `.defer()` control:**
  `get_active_membership()`'s `select_related("organization")` puts the
  org blob in the SQL of **every authenticated request** (~3× per
  request — `has_permission`, `get_queryset`, and each viewset's own
  `filter_by_property_scope`; 38 call sites, no caching — the check-in
  said 51, which counted imports and test references too); the properties
  list loads one banner per row; `activity.photos.all()` loads every
  photo's full bytes to render a list of URLs.

  **The sharpest number is the per-row duplication.**
  `SightingViewSet.queryset` is `select_related("species", "property")`
  (`sightings/views.py:40`) and `ActivityViewSet`'s adds `"property"`
  too (`activities/views.py:148`). Django does **not** dedupe the related
  object across rows — measured: 100 sightings on one property gave
  **100 distinct `Property` objects each holding its own copy of the same
  5 MB banner — 524,288,000 bytes, a 500 MB peak**, against **0.1 MB**
  with the blob deferred (**5,609×**). Both org-wide pages issuing these
  queries are **unpaginated**, so nothing bounds the row count.

  **Live magnitude, measured on the deployed host:**
  `GET /api/public/activities/2/photos/` returns **182 bytes** of JSON
  describing a **2,406,553-byte** photo the server loads in full — a
  **~13,000× amplification**, on an **anonymous** endpoint, with no rate
  limiting anywhere in the app.

  **Severity split honestly.** The **photo half is live now** (photos are
  shipped and used; today's magnitude is small — 6 public activities, 1
  photo each, 2.4 MB and 1.9 MB — and grows with photos per record,
  bounded only by the 8 MB per-photo cap). The **banner half is latent**:
  **both live orgs report `has_theme_header_image: false`**, so those
  columns are NULL and cost nothing today. Its trigger is **one supported
  click** — Manage → Theme's header-image upload.

  **Scope: DoS-shaped. No data exposure, no cross-org reach, no
  escalation** — the blob never reaches a response body, which is the part
  the serializers genuinely got right. **Nothing was written to the live
  instance**; every byte-level measurement ran locally, in-process.

  **Build-ready, not a question** — `.defer()` on the list paths, no
  product fork, and the twelve-site sweep is what proves it safe. The
  byte-serving views build their own lookups, independent of the viewset
  querysets. **The attractive wrong fix is named and measured:**
  `.only("id", "name", …)`, or deferring both `theme_*` columns, makes
  the serializer touch a deferred field and Django re-queries **per
  row** — **1 query becomes 21** at 20 properties, **returning
  byte-identical JSON**, so an outcome test cannot tell the fixes apart.
  Needs a **mechanism test** (`assertNumQueries`, or asserting the column
  is absent from the generated SQL) with the naive fix built and shown to
  fail it, per the D16/D17/D18/D26 convention.
  `defer("property__theme_header_image")` is the form that works across a
  `select_related` — confirmed in the control, not assumed. Full write-up
  in `build-questions.md` (2026-09-13).

  **✅ Built 2026-09-13, and the check-in's framing held on every point.**
  New `backend/apps/accounts/blobs.py` owns the invariant, the column
  list and both ways of getting it wrong; `defer_theme_image` /
  `defer_photo_image` are called at **18 sites** — every list path, every
  anonymous public-site lookup that doesn't serve bytes, plus
  `get_active_membership` and the purge sweep. The two views that *do*
  serve banner bytes keep their own plain lookups. **No migration, no
  frontend change** (the API contract is untouched). **150/150 backend
  tests**, up from 135.

  **Measured end to end through the real endpoint, not on mirror models:**
  `GET /api/sightings/` with 100 sightings on one 5 MB-bannered property
  peaks at **525.3 MB pre-fix and 0.9 MB post-fix**, and the response
  bodies of all six affected endpoints are **byte-identical** either way
  (hashed with timestamps normalised — a first pass compared the clock
  and reported a spurious difference).

  **One thing the check-in did not anticipate, and it is the reason the
  fix is 13 explicit calls rather than one line in `PropertyManager`:**
  centralising it there is impossible. A `select_related` join never
  consults the related model's default manager, so a manager-level defer
  would miss the per-row duplication — the sharpest case of the three.
  That is the same Django semantic `apps/public_site/views.py` has to get
  right for soft delete, biting from the opposite direction.

  **Two hazards found while building, neither in the check-in's list.**
  (1) `property_theme_image` and `organization_theme_image` reach their
  object through querysets this change touched, so they would have paid a
  silent per-request deferred load; both now opt back in explicitly
  (`_public_property_or_404(..., with_theme_image=True)`, and a named
  `values_list` on the org side) rather than relying on attribute magic.
  (2) The genuinely dangerous one: **saving an instance with deferred
  fields could have written the blob column back as NULL**, making an
  ordinary rename silently erase a banner. Django narrows the UPDATE to
  loaded columns, so it does not — but that is a Django internal, and the
  failure mode is invisible, so it is pinned by three tests
  (rename a property, rename the org, soft-delete and restore).

  **The naive fix was built and measured, per the D17/D18/D22/D26
  convention — and the first version of this section did not catch it.**
  Against `.only("id", "name", …)` all 15 tests passed, because the
  content-type assertion covered one queryset instead of all three and
  the query-count test grepped for the *blob* column while the naive
  fix's per-row lookups are for the *content type* beside it. Both were
  rewritten (count all queries at 1 row vs 13 rows and compare; assert
  the content-type column at every site), and the naive fix now fails
  exactly those two — **72 queries for 13 properties where the real fix
  takes 12** — while the other 13 stay green. Against the real pre-fix
  code **6 of 15 fail**, all six of them mechanism tests; the nine
  outcome tests pass both ways by design, which is the honest shape when
  a defect changes no response.

  **A measurement trap worth keeping:** `"theme_header_image" in sql` is
  True *even when the blob is deferred*, because
  `theme_header_image_content_type` contains it as a substring. Any
  presence check on these columns must match whole names.

- **D23 (found 2026-09-12 PM check-in; ✅ BUILT 2026-09-12 programmer
  session, both halves): every dead end in the app routed to the login
  screen, so "that address doesn't exist" and "you must log in" were the
  same screen.**
  `App.tsx:156` ends the route table with
  `<Route path="*" element={<Navigate to="/" replace />} />`, and `/` is
  inside `RequireAuth`, which sends an anonymous visitor to `/login`
  (`RequireAuth.tsx:11`). The login screen rendered is byte-identical to a
  legitimate visit, so **nothing distinguishes a mistyped address from a
  locked door** — D21's misattribution one layer up, in routing rather
  than in an error message.
  **Two independent halves, needing different fixes.** (1) An address that
  doesn't exist is reported as a login requirement — and this lands on
  someone who may have **no account at all**, since the public site is the
  unauthenticated half of the product, so the screen they get is one they
  can neither use nor pass. (2) A valid but gated address is diagnosed
  correctly and then **lost**: `RequireAuth` discards the destination and
  all four post-auth paths hardcode `navigate("/", { replace: true })`
  (`LoginPage:26`, `SignupPage:27`, `AcceptInvitePage:76`,
  `ResetPasswordPage:42`). `useLocation` appears **once** in the whole
  frontend (`FeedbackButton`, for `page_path`), so there is no return
  mechanism to repair.
  **Both `replace` calls make the address unrecoverable** — measured, not
  assumed: after the bounce the URL bar reads `/login` and **Back** returns
  `/login` again from a history with a real prior entry, so a user cannot
  reread their own typo to correct it.
  **The asymmetry is that this repo already knows it and already holds the
  fix.** `PublicHeader`'s docstring rejects linking its brand to `/`
  precisely because *"'/' is the login-gated app, so sending a public
  visitor there would drop them on a login screen"* — the catch-all does
  the thing that comment exists to prevent. `RecordNotFound` (built for
  D14) is the right pattern and is wired to three pages' malformed `:id`
  params but not to the global 404. And the open-redirect guard half 2
  needs is written in `apps/feedback/views.py:27` (`_clean_page_path`):
  leading `/` required, scheme and `//host` refused.
  **Related, and it makes the loop closed:** the five unauthenticated
  screens link only to each other, and `MANUAL_URL` lives only in
  `BottomNav.tsx:14`, inside `AppShell`, inside `RequireAuth`. So D22's
  newly-shipped *"contact whoever runs this one"* has no destination — a
  sweep for `contact`/`support@`/`mailto:` across `frontend/src` and
  `docs/manual/` returns one hit, `getting-started.md:66`, saying the same
  thing. **Who that is, is the owner's to answer** and is the one piece of
  D23 a session cannot supply.
  **Scope stated honestly:** no data exposure, no cross-org reach, no
  escalation, no 500s — a navigation/recovery defect, the D13/D14/D19/D20/
  D21 class. The deep-link half is self-recoverable (friction); the
  mistyped-public-URL half is not, and is the one that matters. Sessions
  last Django's default **two weeks** (`SESSION_COOKIE_AGE` unset) and
  `NotificationsBell` navigates in-app, so half 2's trigger is bookmarks
  and links shared between org members, not notifications.
  **Verified** against the repo's own built bundle served locally with SPA
  fallback and no backend — a failed `/api/auth/me/` is exactly the
  `anonymous` state under test, and only the route table varies. **The
  control is what makes it meaningful:** a nonexistent org slug is *not*
  redirected and renders the public page's own error state, so the bounce
  is specific to unmatched routes. Browser access to the live host was
  impossible this run (the agent proxy closed every Chromium tunnel, code
  1006, while `curl` worked) — a harness limit, not an app fact. Nothing
  was written to the live instance.
  **What was built.** Half 1: a real `NotFoundPage`, mounted on the
  catch-all and deliberately **outside `RequireAuth`** so it can never
  bounce. It **renders in place rather than redirecting**, which is what
  makes the typo rereadable, and it echoes the attempted address as text
  with a way on chosen per audience — dashboard/properties for a member,
  a login link plus a "check the address for a typo" note for an
  anonymous visitor, who is the one the old behaviour stranded. Half 2:
  `RequireAuth` now captures the destination as `?next=`, and **all four
  post-auth navigations and all five `status === "authenticated"` guards**
  honour it, as do the links *between* the auth screens (login → signup →
  forgot-password → reset), without which the return works from whichever
  screen the bounce happened to land on and silently not the others. The
  flagged wording asymmetry was fixed in the same pass:
  `PublicOrganizationPage`'s org-root error now reads *"This organization
  isn't public, or doesn't exist."* — the other three *"Couldn't load this
  page"* sites are the genuinely-different "a well-formed request failed"
  case `RecordNotFound`'s docstring distinguishes, and were left alone.
  **The open-redirect guard is the part worth reading, because porting the
  in-repo precedent verbatim is not safe.** `utils/returnTo.ts` refuses a
  value whole rather than cleaning it, and guards *harder* than
  `_clean_page_path` — that value is displayed, this one is navigated to.
  Measured with a same-origin control rather than argued from spec: against
  `https://habitat.dev.cravenator.com`, `//evil.com`, `/\evil.com` and
  `/<TAB>/evil.com` **all four resolve to `https://evil.com/`** (a browser
  normalizes a backslash in a path, and strips tab/newline/CR *before*
  parsing, so a control character can assemble a `//` that isn't literally
  in the string). **The naive port — `_clean_page_path`'s three checks,
  copied across — passes 29 of 36 unit cases and leaves all four of those
  open.** So the backslash and control-character checks are load-bearing,
  not belt-and-braces.
  **Verified.** 36/36 unit cases on the sanitizer; **33/33 in real Chromium
  at 390px** against the built bundle served locally with SPA fallback and
  no backend — 25 anonymous, plus 8 for the **authenticated** branch, which
  that harness cannot reach at all (it is permanently `anonymous`) and so
  needed a stand-in `/api/auth/me/`; without it half the new page would
  have shipped never once rendered. Against the real pre-fix code **13 of 24 fail** and reproduce
  the defect verbatim: `/pubic/test` → `http://localhost:4178/login`, and
  **Back lands on `about:blank`** — stronger than the check-in measured,
  because `replace` consumed the only history entry, so the typo is gone
  entirely rather than merely unreachable. Nine tests pass both ways
  deliberately and two groups of them earn their place separately: the
  four hostile-`?next=` tests pass pre-fix (there is no `?next=` at all to
  abuse) and are **exactly the ones that catch the naive fix** — the D22
  lesson reproduced, where the defect and its most tempting bad fix need
  different tests; and the org-slug control proves the bounce was specific
  to unmatched routes rather than blanket behaviour.
  **Two honest notes.** This is a *client-side* not-found: the deployment
  serves the SPA from a catch-all, so the HTTP status stays 200 and a link
  checker still won't see a dead address — recorded in `limitations.md`
  rather than quietly fixed, since it is a serving-layer concern. And
  **neither half is pinned by a test** — there is still no frontend test
  runner — so if the catch-all regresses, nothing catches it.
  Full write-up in `build-questions.md` (2026-09-12).

- **D20 (found 2026-09-11 PM check-in; ✅ BUILT 2026-09-11 programmer
  session): the delete-a-property dialog tells
  you to recover it from a menu that doesn't exist.** Both confirmation
  dialogs — `frontend/src/pages/PropertiesPage.tsx:25` and
  `frontend/src/pages/PropertyMapPage.tsx:240` — read *"An admin can
  restore it from Admin → Recently deleted within 30 days."* **"Admin"
  became "Manage" on 2026-09-03** (owner decision, same change that moved
  Properties/Species/Public site under it); there is no "Admin" entry in
  the nav any more. So the app's single most destructive control states
  its recovery path in terms of a menu the user cannot find.

  **This is wayfinding, not data loss, and shouldn't be read as more.**
  Nothing is unrecoverable: the section still exists, one nav entry over,
  under the *same* inner label ("Recently deleted"), and `/admin` still
  redirects to `/manage` for anyone with an old bookmark. But the dialog
  names a **menu path**, not a URL, so the redirect doesn't help the
  person scanning a nav bar for the word "Admin". Severity is the
  placement, not the consequence — it is the one sentence a user reads at
  the exact moment they are about to destroy something.

  **The manual is already right, which is this finding's shape** (as with
  D16 and D19, and the opposite of D13): `docs/manual/properties.md:150`
  says *"An admin can restore it from **Manage → Recently deleted**"*, and
  every one of the ~12 other `Manage → …` references across the manual is
  correct too. So the fix makes the app match documentation that is
  already accurate — **no manual edit applies.**

  **Swept, so it can't be half-fixed** (the "four filters, not two"
  precedent): every `→` in `frontend/src` was examined. Exactly **two**
  are stale, both above. Every other occurrence is either a code comment
  that already says "Manage →" correctly (`AccountPage.tsx:9`,
  `AcceptInvitePage.tsx:17`) or a non-path arrow ("All tasks →", the
  seeded `Planned → In Progress → Done`). Two words, two files.

  **Confirmed live on the deployment**, not just in the checkout: the dev
  host serves the frontend through Vite, and
  `GET /src/pages/PropertiesPage.tsx` returns the real module containing
  `restore it from Admin → Recently deleted`. The negative control
  (`/src/pages/NoSuchFileXyz.tsx`) returns the SPA fallback HTML rather
  than a module, so the first response is the genuine file — the
  2026-09-08 lesson that a 200 proves nothing on this host was applied
  rather than re-learned. **Nothing was written to the live instance.**

  **Build-ready, no owner answer needed** (the D6/D13/D14/D16/D19 call,
  not D5/D8/D11's): replace "Admin" with "Manage" in the two strings.

  **Built 2026-09-11.** Both strings now read "Manage → Recently deleted",
  verified in the built bundle (two occurrences, one per dialog; zero of
  the old string). The reasoning is pinned in a comment **on the dialog in
  `PropertiesPage.tsx`**, with a pointer to it from its twin, because the
  change that would undo this is a future nav rename — and that person is
  reading the dialog, not this file. The comment names both label sources
  (`BottomNav.tsx` for "Manage", `manage/sections.ts` for "Recently
  deleted") and states why the `/admin → /manage` redirect doesn't cover
  it. **No manual edit, no migration, no screenshot** — and **no test**,
  since there is still no frontend test runner; if this regresses, nothing
  catches it.

- **D21 (found 2026-09-11 programmer session; ✅ BUILT same session): on
  the deployed host, an error with no JSON body of its own showed the user
  *nothing at all* — and on a list page it rendered as "you have no
  data".** `handleResponse` fell back to `Response.statusText` when a
  non-2xx answer wasn't JSON. **HTTP/2 and HTTP/3 removed the reason
  phrase from the protocol**, so per the Fetch spec `statusText` is the
  empty string for any response that didn't arrive over HTTP/1.1 — and
  `habitat.dev.cravenator.com` negotiates **h2** (measured:
  `http_version=2` on both `/` and `/api/auth/csrf/`). So
  `ApiError.message` was `""`.

  **The empty string is what makes it a defect rather than a cosmetic
  gap**, because every error render in the app is guarded on the message's
  own truthiness — `{error && <p className="form-error">{error}</p>}`, 20+
  sites. An empty message renders no element. A failed save was
  indistinguishable from a button that does nothing: the D13 symptom,
  arriving by a different route.

  **The sharpest framing is the list pages, where it doesn't merely go
  silent — it misattributes.** `useAsync` stores `err.message` too
  (`hooks/useAsync.ts:37`), so a failed load left `error === ""`, which
  makes `{!loading && !error && (…)}` **true**. `SpeciesPage` then renders
  its whole normal body against `data === null` and reaches its empty
  state. The screen says the list is empty; the truth is that it could not
  be loaded. That is the error-message honesty lens' actual target — an
  app stating a cause that is not the real one — and it was found by
  pointing that lens where the 2026-09-11 check-in said to point it.

  **Measured, not argued, and the measurement is the controlled kind.**
  Two local TLS servers differing in **nothing but ALPN** (`http/1.1` vs
  `h2`), the same 404 `text/html` and 503 `text/plain` bodies, fetched
  from real Chromium and run through `client.ts`'s own `errorMessage`
  copied verbatim: h1 → `"Not Found"`, h2 → `""` → **user sees nothing at
  all**. The dev host's own `/api/nosuchendpoint/` was confirmed to be
  exactly this shape (404, `text/html`, h2) before building anything.

  **Which real responses hit it:** the edge proxy's 5xx while the backend
  restarts — which this deployment does **on a 15-minute schedule**, so
  this is a recurring live condition, not a hypothetical — plus Django's
  `DEBUG=False` 500 page and a 404 on a mistyped API path. All answer
  `text/html` or `text/plain`.

  **Fixed** by deriving the fallback from `status` alone
  (`statusFallback`), in **both** sites that depended on `statusText`
  (`handleResponse` and `postForBlob` — a sweep confirms there are exactly
  two, the "four filters, not two" precedent). **It deliberately does not
  keep `statusText` when non-empty:** doing so would make the message
  depend on the transport, so local dev (h1) would show text while
  production (h2) showed none — which is precisely how this stayed
  invisible for the life of the deployment. The reason phrase is a fixed
  restatement of the status code, so nothing is lost by never reading it.
  502/503/504 get "try again in a moment" because that advice is true for
  them and misleading for a 400; everything else gets one honest line.

  **Verified including the regression guard**, which matters more here
  than the red path: a fix that clobbered real DRF messages would be worse
  than the bug. Both DRF shapes — `{"detail": …}` and the field-level
  `{"is_done": [...]}` — come back **unchanged on both protocols**; only
  the no-message case changed, and it changed from nothing to something.
  `npm ci`, `tsc -b`, `vite build` clean, and both new strings confirmed
  in the built bundle. **No backend change, so no PostGIS stack was stood
  up and no backend run is claimed.** **No test pins this** — no frontend
  test runner exists — stated plainly rather than left to be inferred.

  **Recorded, deliberately NOT fixed:** a `fetch` that rejects outright
  (offline, DNS failure) is a `TypeError`, not an `ApiError`, and surfaces
  the browser's own "Failed to fetch". Technical, but non-empty and not
  misattributing, so it is a different and much weaker item than this one.

- **D19 (found 2026-09-10 (5) PM check-in; ✅ BUILT 2026-09-10 (6)): the
  checkbox that publishes an activity to the open internet was captioned
  "no public view exists yet in Phase 1", and it is ticked by default.**
  `frontend/src/pages/ActivityFormPage.tsx:327` renders
  `Show on the public view (no public view exists yet in Phase 1)` next to
  the `is_public` checkbox, which defaults to `true`
  (`existing?.properties.is_public ?? true`, line 72). The public view has
  existed since **2026-08-14**. So the app affirmatively tells the user
  that the control does nothing, while that control is in fact the flag
  that publishes the record — geometry, dates, notes and species — to an
  anonymous visitor at a stable URL.

  **This is not an access-control defect and shouldn't be read as one.**
  Every filter is correct: `property_activities`
  (`apps/public_site/views.py:213`) requires `is_public=True` and resolves
  the property through `_public_property_or_404`, so the two-condition rule
  (public *and* not soft-deleted) holds. Nothing is published that wasn't
  flagged. The defect is **informed consent**: the only on-screen
  explanation of what the flag does is a denial that it does anything, and
  the denial is reassuring in exactly the direction that causes harm.

  **The asymmetry is the sharpest framing — three of four say it
  correctly.** `SightingFormPage.tsx:267` ("Show on the public site"),
  `PropertyFormPage.tsx:206` and `QuickLogPage.tsx:410` are all truthful.
  Only the activity form carries the stale Phase-1 parenthetical, and it is
  attached to the record type that carries drawn geometry, both dates and
  free-text notes.

  **Live on the deployment, not theoretical.** The anonymous endpoint
  `/api/public/properties/1/activities/` returns **5 activities, 3 of them
  carrying notes** — all `is_public: true`. (Only field *lengths* were
  read; the note text was deliberately not copied into this repo, same
  reasoning as D8's redacted address.) Property 2 publishes 0 activities,
  3 → 404.

  **A sweep, so this isn't half-fixed later:** every other `Phase 1` /
  `not yet` / `doesn't exist yet` string in `frontend/src` is a **code
  comment**, not a rendered string. Line 327 is the only one a user ever
  sees. Isolated to one line.

  **Build-ready, no fork:** replace the parenthetical with what the flag
  actually does, matching the three siblings' wording. **The default must
  NOT be changed in the same pass** — public-by-default with a per-record
  private flag is a decided project stance (see "Decided" in `CLAUDE.md`),
  so a build session flipping it would be deciding a product question on
  its own authority. The narrow item is the caption.

  **No manual edit applies, and that is the finding's shape** (same as
  D16): `docs/manual/activities.md:36` already quotes the label as *"Show
  on the public view"* and calls it "the same public/private mechanism as a
  property or a sighting" — i.e. **the manual documents the truthful
  behaviour and the screen contradicts it.** Fixing the caption makes the
  manual's existing quote literally correct rather than needing new prose.
  Two notes for the fixing session: consider whether `activity-new.png`
  shows the checkbox (if it does, the screenshot becomes actively wrong
  once the label changes, not merely stale — unverified here); and the
  manual nowhere enumerates *which* fields a public record publishes, notes
  included, which is the weaker sibling of this item and the natural thing
  to add to `public-site.md` in the same pass.

  **✅ Built 2026-09-10 (6).** The label now reads **"Show on the public
  site"**, matching all three siblings. The default was deliberately left
  alone, per the guardrail above.

  **The wording call the check-in left implicit: "site", not "view".** The
  check-in reasoned that keeping *"Show on the public view"* would make
  `activities.md`'s existing quote literally correct with no manual edit.
  That is true but it optimises the wrong thing — `public site` is the
  app's vocabulary everywhere else (the nav entry, all three sibling
  labels, nine manual chapters), and `public view` survived *only* in this
  stale label and two lines of prose. Making one form's label the lone
  holdout of a second vocabulary is how the next drift starts. So the label
  matches the siblings and the manual's quote was updated instead — a
  one-line edit, versus a permanent inconsistency.

  **Both of the check-in's two notes were resolved, and the first came back
  the opposite way to what it feared.** `activity-new.png` **and**
  `activity-edit.png` were opened and read: both are cropped at the Notes
  field, several controls above the checkbox, which is not in frame in
  either. So **no screenshot goes from stale to wrong**, and no regeneration
  is needed — the case the cap policy exists to catch does not arise here.
  The second note was taken: `public-site.md` gains a new **"What a public
  record publishes"** section enumerating the fields that actually travel
  for an activity and a sighting, verified field-by-field against
  `ActivitySerializer.Meta.fields` and `SightingSerializer.Meta.fields`
  rather than recalled — the public endpoints reuse the app's own
  serializers, so *every* field on them publishes. It calls out the two
  things easiest to miss: **notes are published in full** (there is no
  private-notes field on either record type), and **the exact location is
  published** with no fuzzing, which is the part that matters for a
  sensitive sighting.

  **Verified on the shipped artifact, not just the source.** `tsc -b` and
  `vite build` clean; the built bundle then contains **zero** occurrences of
  the old caption and **zero** of the string `public view` anywhere, against
  two occurrences of `Show on the public site` (this form and the sighting
  form). The render path was checked rather than assumed, per D13's lesson:
  the checkbox sits above every conditional branch in the component
  (`savedId` short-circuits at line 197, the first `{existing && (` is at
  line 340), so it renders on create and edit alike. **No backend file
  changed, so no PostGIS stack was stood up and no backend run is claimed.**
  There is still no frontend test runner, so this defect is not pinned by a
  test — stated plainly rather than left to be inferred from a green suite.

- **D18 (found 2026-09-10 (3) PM check-in; ✅ BUILT 2026-09-10 (4)): the
  "that species is already linked" guard had nothing in the database behind
  it, so two concurrent adds created a duplicate row — and from then on
  every add for that pair was an unhandled 500, until someone deleted a row
  by hand.** **Fixed** by adding
  `UniqueConstraint(fields=["activity", "species"], name="unique_activity_species")`
  to `ActivitySpecies.Meta`, with migration
  `activities/0004_unique_activity_species` deduping first (keep the lowest
  id) and adding the constraint in **one** migration so a half-applied
  state can't exist. The view is unchanged apart from a defensive
  `MultipleObjectsReturned → 400`: the constraint alone makes the existing
  400 correct, because it hands `get_or_create` back its recovery branch.

  **The dedupe half was verified against a database that actually held
  duplicates**, which the check-in recorded as uncheckable from here. It
  isn't: rolling `activities` back to 0003 on a local PostGIS instance
  makes the pre-D18 state reachable, three rows for one pair were created
  through the ORM (which is D18 in one line — the ORM accepts them because
  a `UniqueConstraint` is enforced by the *database*), and re-applying 0004
  reported `removing 2 duplicate ActivitySpecies row(s)`, kept the
  lowest-id row **with its own role/quantity**, left an unrelated pair
  untouched, and the constraint then refused a fresh duplicate. The reverse
  path was exercised too. What remains genuinely unknown is only whether
  the *deployment* holds duplicates — likely not, but the migration doesn't
  assume it.

  **The naive fix was built and measured, per D17's lesson.** An
  application-level `.exists()` re-check with no constraint takes the suite
  from 6 failures to 4: it makes the sticky 500 disappear while leaving the
  race and the duplicate rows completely intact — arguably worse than the
  bug, because the corruption goes silent. Every outcome test about the
  *symptom* is satisfied by it; only the mechanism tests
  (`test_the_database_itself_refuses_a_duplicate_pair`,
  `test_the_constraint_is_declared_on_the_model`) catch it.

  **One consequence worth knowing, because it closes a workaround:** D13's
  `apps/species/views.py` counts *distinct activities* precisely because
  duplicates could exist, and its test *constructed* that state on purpose.
  The constraint makes that fixture impossible, so the test now asserts the
  stronger fact (the duplicate is refused) and the view's comment no longer
  claims there is no constraint. `distinct()` stays — counting activities
  is what the message claims to do, and that shouldn't silently depend on a
  constraint declared in another app.

  Original finding, kept for reference:
  `activity_species_list`'s POST path (`apps/activities/views.py:315`) does
  `ActivitySpecies.objects.get_or_create(activity=…, species=…)` and
  returns 400 on `created is False`. But `get_or_create` is only race-safe
  when a unique constraint backs it — it is a plain SELECT-then-INSERT that
  takes no lock — and `ActivitySpecies.Meta` carries **only
  `verbose_name_plural`** (`apps/activities/models.py:187-188`).

  **The asymmetry is the sharpest framing, because the sibling link model
  gets it right.** `SightingActivityLink` — the other link model in the
  same feature family, created through `get_or_create` at *two* call sites
  (`apps/activities/views.py:276`, `apps/sightings/views.py:154`) — carries
  `UniqueConstraint(fields=["sighting", "activity"])`
  (`apps/sightings/models.py:88-93`). A sweep of every model settles how
  isolated this is: **eight uniqueness constraints exist across the
  codebase** (`User.email`, `Organization.slug`, `Property`,
  `Membership`, `Invitation.token`, `PasswordResetToken.token`,
  `WorkflowState`, `ActivityType`, `Page` ×2, `Species`,
  `SightingActivityLink`), and `ActivitySpecies` is the **only** model that
  states a uniqueness rule in a user-facing error message with nothing in
  the database enforcing it.

  **The constraint is the guard's mechanism, not hygiene on top of it** —
  this is the part a quick read inverts. `get_or_create`'s own
  implementation is `try: get() except DoesNotExist: try: create() except
  IntegrityError: get()`. So **with** a constraint, the loser of a race has
  its INSERT rejected, `get_or_create` catches the `IntegrityError`,
  re-reads, and returns `created=False` — the endpoint's 400 fires
  correctly even under concurrency. **Without** one, that recovery branch
  is unreachable: the second INSERT simply succeeds, `created` is `True`,
  and the endpoint answers 201. The guard fails **open**, silently.

  **Reproduced on the repo's own pinned Django 5.2.17**, on plain non-GIS
  models mirroring both link models' exact shapes (the D12/D14 technique),
  interleaving the two requests the way two concurrent POSTs actually run:

  | Step | `ActivitySpecies` (no constraint) | `SightingActivityLink` (constraint) |
  | --- | --- | --- |
  | A's SELECT | not linked | not linked |
  | B's SELECT | not linked | not linked |
  | A's INSERT | 201 | 201 |
  | B's INSERT | **201 — accepted** | `IntegrityError` → refused |
  | rows for the pair | **2** | 1 |

  **The persistent damage is what makes this worth recording, and it is
  worse than the duplicate row.** Once two rows exist, the *next* POST for
  that pair no longer reaches the 400 — `get_or_create`'s own `get()`
  raises `MultipleObjectsReturned` (`get() returned more than one
  ActivitySpecies -- it returned 2!`). Its MRO is
  `MultipleObjectsReturned → Exception`: not an `APIException`, not a
  Django `ValidationError`, and there is **no custom `EXCEPTION_HANDLER`**
  anywhere (re-verified, not inherited from D13's finding), so DRF's
  handler returns `None` and it reaches the user as a **500**. Unlike D13's
  transient 500, this one is *self-inflicted and sticky*: the bad row
  persists, so the endpoint stays broken for that pair. Two smaller
  symptoms: `ActivitySerializer.species_names` is
  `[s.common_name for s in obj.species.all()]` over the M2M *through* this
  table, so the species renders twice — and that field is served
  **unauthenticated by the public site** (the D12 comment says so at the
  call site); and an activity can simultaneously claim one species as both
  `planted` and `treated_target` with different quantities.

  **The missing constraint has already cost this codebase a workaround,
  which is the strongest evidence it should exist.**
  `apps/species/views.py:61-68` counts **distinct activities** rather than
  through-rows, with a comment saying exactly why: *"ActivitySpecies has no
  unique constraint on (activity, species) — only the POST path's
  get_or_create keeps it to one row per pair."* D13 noticed the absence and
  correctly worked around it for *counting*; nobody then asked whether the
  thing doing the keeping actually holds under concurrency. It doesn't.

  **Scope, stated honestly rather than inflated.** Editor-gated;
  **needs genuine concurrency**, and a naive double-click is *not* it —
  `ActivitySpeciesPanel` disables its Add button while a request is in
  flight (`disabled={busy || selected === ""}`), so the realistic triggers
  are two editors on the same activity, two browser tabs (the `busy` flag
  is per-component, not shared), a network-layer retry, or direct API use.
  **No data exposure, no cross-org reach, no privilege escalation**, and it
  is **self-recoverable** — the panel lists both rows with a Remove button
  each, and the PATCH/DELETE path addresses rows by `link_id`, so it never
  hits the ambiguity. Same low-severity 500-hygiene/integrity class as D13
  and D14. **Nothing was written to the live instance**; every measurement
  ran locally, in-process.

  **Framed as build-ready, not a question** (the D12/D13/D14/D16/D17 call,
  not D5/D8/D11's): add
  `UniqueConstraint(fields=["activity", "species"])` to
  `ActivitySpecies.Meta`, which makes the existing 400 correct under a race
  with no change to the view at all. Two build notes, neither a fork:
  (1) the migration must **dedupe first** or `AddConstraint` fails on a
  database that already holds duplicates — recommendation is keep the
  lowest id and delete the rest, reporting what it removed, in one
  migration so a half-applied state can't exist (the `activities/0003`
  precedent); duplicates are unlikely on the current two-org deployment but
  the migration must not assume it, and **this cannot be checked from here**
  (no database access — the same limitation as the D6 backfill query).
  (2) Worth also handling `MultipleObjectsReturned` → 400 defensively, so a
  pre-existing duplicate that the dedupe somehow misses degrades to the
  honest error rather than a 500.

  **Recorded but deliberately NOT queued — a related, weaker gap that is a
  design question rather than a bounded fix.**
  `WorkflowStateSerializer` and `ActivityTypeSerializer` reject duplicate
  names **case-insensitively** (`name__iexact`,
  `apps/activities/serializers.py:38` and `:115`), while their database
  constraints are on `fields=["organization", "name"]` — **case-sensitive**
  in PostgreSQL. So the app's stated rule is stricter than the enforced one,
  and a race between "Seeding" and "seeding" leaves an org with two types it
  would never have been allowed to create sequentially. Much weaker than
  D18: **no 500** (those serializers use `.filter()`, not `.get()`, so
  multiple matches are handled), no persistent breakage, and the race needs
  two people submitting differently-cased spellings of one name at the same
  moment. Closing it properly means a `Lower()`-based functional constraint
  *and* a decision about what happens to existing differently-cased rows —
  a product call, not a mechanical change. **Recommendation: not now**;
  recorded so a future run doesn't re-derive it.

- **D17 (found 2026-09-10 PM check-in; BUILT 2026-09-10 programmer
  session): the QR center-image upload was the app's only image input with
  no size cap, no type check and no pixel limit — a 77 KB file cost the
  server ~470 MB of memory, and a *viewer* could send it.**
  `_qr_response` (`apps/accounts/views.py:544-546`) does
  `request.FILES.get("logo")`, then `logo.read()`, then hands the bytes to
  `make_qr_png`, which calls
  `Image.open(io.BytesIO(logo_bytes)).convert("RGBA")` — with nothing
  guarding any step. **The asymmetry is the sharpest way to hold it:
  Habitat has five image inputs and this codebase already solved this four
  times.** Activity photos, sighting photos and both theme banners each
  call `validate_image_upload` *and* an explicit byte cap
  (`MAX_PHOTO_BYTES` = 8 MB, `MAX_THEME_IMAGE_BYTES` = 5 MB); the QR logo
  calls neither. It is also the only one of the five carrying **no role
  gate** — `organization_qr_code`/`property_qr_code` have no `ensure_role`,
  so they fall through to `IsAuthenticated` and the lowest role in the app
  can reach them.

  **Measured against the repo's real `qrcodes.py` on the pinned Pillow
  12.3.0**, not reasoned about: 9000×9000 (**77 KB**) → HTTP 200, **+468 MB
  peak RSS**, 3.9 s CPU; 12000×12000 (137 KB) → 200, +484 MB;
  20000×20000 (380 KB) → correctly 400. **The middle of that range is the
  finding.** The tempting reading is "Pillow protects us", and above 2×
  `MAX_IMAGE_PIXELS` it genuinely does — it raises, the existing
  `except Exception → ValueError` catches it, and the view returns a clean
  400 (which is what the 2026-09-06 (3) check-in correctly observed about
  an *undecodable* image, never having asked about a decodable but
  enormous one). But that guard only engages above 89,478,485 pixels:
  **a 9000×9000 image is under the limit, so nothing warns and nothing
  raises**, and it still costs half a gigabyte. The protection is real and
  irrelevant — you simply stay beneath it.

  **`DATA_UPLOAD_MAX_MEMORY_SIZE` looks like a cap and is not one.**
  Measured on Django 5.2.17's real `MultiPartParser`: 25 MB as a *text*
  field → `RequestDataTooBig`; 25 MB as a *file* field → accepted; 200 MB
  as a file field → accepted. It deliberately excludes file uploads, which
  is exactly why the other four endpoints carry their own `image.size >`
  check — and `settings.py:132-137`'s own comment says so outright. The
  principle was understood at three call sites; this path never got it.

  **Scope, honestly:** DoS-shaped resource exhaustion — no data exposure,
  no cross-org reach, no escalation, and the endpoint is authenticated, so
  not an unauthenticated hole. Nothing was uploaded to the live instance.
  What makes it worth recording anyway is that the trigger needs no
  sophistication and is available to the *least* privileged role, and the
  live host runs threaded `runserver` (see D5), so concurrent requests each
  allocate. Note also that an edge proxy's body-size limit bounds only the
  200 MB half — the 77 KB row passes any such limit untouched, which is
  why the **pixel dimension, not the byte count, is the load-bearing
  check**.

  **Recommended fix (no fork, so a build session should take it):**
  `Image.open()` is lazy — it parses the header and exposes `.size`
  *without* decoding — so the guard is cheap and exact: open, reject on
  `w * h` over a conservative ceiling, and only then `.convert("RGBA")`.
  Pair that with a byte cap and the `validate_image_upload` call the other
  four inputs already make, so all five agree. Nothing legitimate comes
  near the limit: the logo is thumbnailed to 25% of the QR's width, a few
  hundred pixels. The build session picks and states the two constants, the
  way `MAX_PHOTO_BYTES` and `MAX_THEME_IMAGE_BYTES` already are. **Distinct
  from app-wide rate limiting** (absent since 2026-08-27, still unqueued),
  which is a design question rather than a bounded fix.

  **Two `docs/manual/limitations.md` inaccuracies found alongside it,
  recorded not fixed** per that check-in's scope: its testing bullet says
  "90 tests across six areas" where the suite is now **98** (accounts 53,
  activities 8, feedback 10, public_site 7, species 10, config 10) and has
  gained a concurrency section the area list doesn't name; and its
  image-formats bullet ends "the picker only offers the accepted formats",
  which the QR picker (`QrCodePanel.tsx:60`, `accept="image/*"`)
  contradicts — an SVG there is refused only because Pillow can't decode
  it, giving a generic error instead of the format message. The second
  becomes true as written the moment D17 adds the `validate_image_upload`
  call, so the fixing session is the natural one to correct it.
  **Both are now fixed** — see below.

  **BUILT (2026-09-10 programmer session).** The recommendation was taken
  as written, with the guard split across the two layers by responsibility
  rather than piled into one: the *view* owns what an upload may be
  (`MAX_LOGO_BYTES` = 5 MB and `validate_image_upload`, both checked
  **before** `logo.read()`, so an oversized body is refused without being
  pulled into memory), and `qrcodes.py` owns what a *decode* may cost
  (`MAX_LOGO_PIXELS` = 16,000,000, checked on `Image.open().size` before
  `.convert()`). No migration — view and validation logic only.

  **The two constants, with why those numbers.** 5 MB is
  `MAX_THEME_IMAGE_BYTES`, asserted equal to it by a test: a center image
  is the same class of asset as a theme banner (an org's own brand mark),
  so the two should not disagree about what "too big to send" means.
  16 megapixels is deliberately generous — the logo is thumbnailed to ~25%
  of the QR's width, so even a full-resolution phone photo (~12 MP) passes
  — while sitting well below Pillow's own 89,478,485 threshold, which is
  what keeps *our* guard the one that fires rather than leaving the gap
  beneath Pillow's. Both properties are pinned by tests so a later session
  tightening or loosening them has to change a test that says why.

  **Re-measured independently before fixing** (the check-in's numbers were
  not taken on trust), driving the repo's real `make_qr_png`: 9000×9000
  → 200, **+313 MB**, 2.68 s; 12000×12000 → 200 with only a *warning*,
  +482 MB; the `MultiPartParser` half reproduced exactly (25 MB text →
  `RequestDataTooBig`, 200 MB file → accepted). Post-fix the same 9000×9000
  case is **400 at +0.0 MB and 0.01 s** — the decode never happens — and
  the worst case the cap still *allows* (4000×4000) costs +62.8 MB / 0.5 s,
  which is the honest bound now in place. My byte figures differ from the
  check-in's because the two runs generated their test images differently;
  the shape and the conclusion are identical.

  **One refinement beyond the recommendation.** Pillow's own
  `DecompressionBombError` fires at `open()` for the extreme tail our check
  never gets to see, and was previously answered with "Could not read the
  center image." It now returns the *dimensions* message instead: it is the
  same user mistake, just larger, and the two guards compose, so they
  should say the same thing.

  **Deliberately NOT changed: the missing role gate.** The check-in noted
  these are the only image endpoints without `ensure_role`. That is
  documented as intentional at the call site — a QR code exposes nothing
  that isn't already on the public site — and D17 is a resource-exhaustion
  finding, fixed by bounding the resource, not by narrowing who may ask.
  Adding a gate here would be a silent product change; a test pins the
  viewer's access so that "fix" goes red instead of shipping quietly.
  App-wide rate limiting remains a separate, still-unqueued design
  question.
- **D16 (found and BUILT 2026-09-09 programmer session): the "an
  organization always keeps one account-wide admin" guard could be raced,
  leaving an organization with zero — the exact state it exists to
  prevent, and one nothing in the app can recover from.**
  `MembershipViewSet.partial_update` and `.destroy` both counted the
  organization's account-wide admins and then wrote, with nothing held
  between the two, and `settings.py` sets no `ATOMIC_REQUESTS`, so each
  statement autocommitted on its own. Two admins demoting *each other* at
  the same moment both read a count of 2, both passed the guard, and both
  wrote.
  **No attacker is needed and the consequence is permanent.** Two admins
  tidying up membership at once — or one admin with two tabs — is enough,
  and they'd be locking *themselves* out, so this is a footgun rather than
  an attack. Afterwards the organization cannot be renamed, cannot manage
  account-wide members, cannot invite, and cannot work its feedback queue:
  `_account_wide_admin_count`'s own docstring already said "nothing in the
  app can recover from that".
  **Verified by reproducing it, not by reasoning about it.** Two threads
  against a real Postgres, each demoting the other's account-wide admin:
  pre-fix both return **200** and the organization is left with **zero**
  account-wide admins.
  **Fixed** by taking a `select_for_update()` row lock on the
  Organization inside `transaction.atomic()` on both paths, and re-reading
  the membership inside the lock. Two details worth not re-deriving: the
  lock has to be on the *organization* row rather than the membership rows
  (the rows a competing request changes aren't the ones this request
  read, so locking what you read wouldn't help), and it can't be
  `select_for_update()` on the count query itself — that query is a
  `DISTINCT` over a join, and Postgres rejects `FOR UPDATE` with both.
  Creating a membership can't lower the count, so it doesn't take the lock.
  **No migration.** 12 new tests (`apps/accounts/tests.py`, a fifth
  section) — 8 fail against the pre-fix code; the 4 sequential ones pass
  both ways deliberately, guarding against a "fix" that makes the guard
  fire when it shouldn't, which is the failure mode D10 already hit on
  this exact guard once.
  **The manual needed no edit and that is the point:**
  `roles-and-permissions.md` already told users an organization "can never
  end up with zero account-wide admins". The defect was that the code
  didn't hold the invariant the docs asserted; the fix makes the existing
  sentence true rather than requiring new prose.

- **D15 (found 2026-09-09 PM check-in, BUILT 2026-09-09 programmer
  session): `PropertyMapPage`'s pinned-record count included pins from a
  property you're no longer looking at, so the hint could read "Showing 3
  of 2".**
  **Built**, together with its public-site sibling. Both pages now key on
  the property's identity, so changing property remounts and resets the
  per-property state instead of carrying it across.
  `PublicPropertyPage` carried the identical shape and was fixed in the
  same pass — its key is deliberately the property identity *only*, not
  the whole route, because the page nav switches between Explore and that
  property's authored pages without leaving the property, and remounting
  there would tear down the map and drop a visitor's pins for a property
  they never left.
  **Reproduced in a real browser before fixing**, since it is unreachable
  through the UI: with a temporary, uncommitted switch link standing in
  for the property switcher that would trigger it, the pre-fix build shows
  *"Showing 3 of 1 on the map"* and a "Clear all" button with zero pinned
  cards; the fixed build shows "Showing 1 of 1" and no stray button. The
  same run also **confirms the check-in's correction**: only the current
  property's own record is listed, so nothing cross-property is drawn.
  The original description of the item is kept below for the record.

  <details><summary>As originally recorded (the correction is the
  valuable part)</summary>
  This is the item D14's build session left behind, re-examined — and
  **both halves of how that note described it are wrong**, which is the
  main reason this is recorded rather than just inherited.
  **The carryover itself is real.** `PropertyMapPage` holds `pinnedIds`
  in component state and its wrapper deliberately does not key on the
  property id, so React Router reuses the component when `:id` changes and
  the set survives.
  **But the stated consequence — "their ids can collide" — cannot
  happen.** `Activity` and `Sighting` declare no custom primary key
  (`apps/activities/models.py:100`, `apps/sightings/models.py:15`), so
  their ids are Django `AutoField` values, **globally unique across the
  table rather than per property**. A pin key `activity-5` names an
  activity belonging to the property it was pinned on and can never match
  a different record elsewhere. And the map filter iterates the *current*
  property's own features (`PropertyMapPage.tsx:173-177`), so a stale key
  matches nothing: **nothing cross-property can ever be drawn, and there
  is no data leak.**
  **The real symptom is a count bug the note misses.** `shownIds` is
  `new Set(pinnedIds)` plus the focused id (`:157-161`), and `:440`
  renders `shownIds.size` — the raw size, stale pins included. Pin two
  records on property 1, open property 2, and the hint reads *"Showing 3
  of 2 on the map"*, a numerator larger than its own denominator, while
  one record is actually drawn. "Clear all" is gated on
  `pinnedIds.size > 0` (`:447`), so it also appears with no card showing a
  Pinned badge.
  **It is unreachable through the UI today, so this is latent, not
  live.** Checked rather than assumed: the only in-app link to
  `/properties/:id` is `PropertiesPage.tsx:70`, and every `navigate()` to
  a property page comes from a *different* route (`QuickLogPage:287`,
  `SightingFormPage:171/184`, `PropertyFormPage:121`,
  `ActivityFormPage:189/202`), each of which mounts `PropertyMapPage`
  fresh; `PropertyMapPage` itself only navigates to `/properties`
  (`:239`). No path changes `:id` while the page stays mounted. It becomes
  real the day someone adds a property switcher or a property-to-property
  link — the same "latent sibling" shape as the
  `SightingActivityLinkSerializer` note recorded under D12. **The org
  switcher already queued under "Accounts, orgs, and permissions" is
  exactly that trigger**, so pairing the two is the natural move.
  **Recommendation, and it is not the one in the code comment.** That
  comment (`PropertyMapPage.tsx:47-52`) rejects `key={propertyId}` because
  remounting "would also reset the pinned-record set, which is a behaviour
  change this fix has no business making". Fair as a scope call for D14's
  run, but the concern is largely unfounded — **resetting pins when the
  property changes is the correct behaviour, not a side effect to avoid**,
  since the carryover is the bug. Either fix works; the targeted one is to
  prune `pinnedIds` to the current `itemIds` (or intersect at
  `shownIds`), which fixes the count *and* the stray "Clear all" without
  changing mount behaviour.
  **Scope stated honestly:** cosmetic, unreachable today, and the smallest
  thing any of these check-ins has recorded — recorded at that size rather
  than inflated. Its value is mostly the correction: the note as written
  would have sent a build session hunting an id collision that cannot
  exist. No manual change applies — `docs/manual/properties.md`'s
  "Showing X of Y on the map" description is accurate for every state a
  user can actually reach.
  </details>

- ✅ **D14 (found 2026-09-08 (3) PM check-in, BUILT 2026-09-08 (4)
  programmer run): a non-numeric query param reached the database layer
  and 500'd, and the ordinary UI sent one on any mistyped property URL.**
  `/properties/abc` is a real route; `PropertyMapPage` does
  `Number(id)` with **no NaN guard** and immediately fires four requests,
  and `withQuery` (`api/client.ts:185-190`) skips only `undefined`, so the
  literal string `NaN` goes on the wire. **Verified empirically on the
  repo's own pinned Django 5.2.17 / DRF 3.15.2** by reproducing each call
  site's shape on plain non-GIS models: `?property=NaN` returns **500**
  from the activities, sightings and pages endpoints, while
  `?property=999` (valid but matching nothing) correctly returns 200 and
  `/api/properties/NaN/` correctly returns **404**. So one mistyped URL
  produces three 500s and a generic error where "no such property" is the
  truth.
  **The clearest framing is that DRF already ships the fix and four call
  sites don't use it.** `rest_framework.generics.get_object_or_404`
  exists for exactly this — it catches `(TypeError, ValueError,
  ValidationError)` and raises `Http404`, and its docstring says so —
  whereas `django.shortcuts.get_object_or_404` catches only
  `DoesNotExist`. That is precisely why the DRF detail route is fine and
  `apps/pages/views.py:57` is not: it imports Django's (`:15`).
  **Scope stated honestly:** no data exposure, no cross-org reach, no
  escalation — all four endpoints are session-authenticated and a valid
  id from another org already returns nothing correctly. This is
  500-hygiene and a bad error message, the same low-severity class as
  D13, which was still worth building.
  **Narrowed by a sweep:** every URL *path* parameter in the repo uses an
  `<int:>`, `<slug:>` or `<str:token>` converter, so all ~40 path-param
  `get_object_or_404` call sites are protected at URL resolution. The
  exposure is only the four query params, which have no converter:
  `apps/activities/views.py:167-168` and `apps/sightings/views.py:51-52`
  (`?property=`), `apps/pages/views.py:51-60` (`?property=`, via Django's
  helper) and `apps/tasks/views.py:33-35` (`?assigned_to=`). Checked and
  **not** affected: `?status=`, `?is_public=`, and `?blooming_on=` —
  which already returns a 400 on bad input and is the in-repo precedent.
  **Built as recommended, and the sub-question was answered with a rule
  rather than a preference.** The PM note left "400 vs 404 vs ignore" for
  the build session to state; the rule chosen is **match what a
  valid-but-nonexistent id already does at that call site**. On a
  *filter* (`?property=` on activities/sightings, `?assigned_to=` on
  tasks) a valid id matching nothing deliberately returns 200 with an
  empty list, so 404 would be the wrong shape and **400** is the honest
  answer — matching `?blooming_on=`. On the *lookup* in
  `apps/pages/views.py`, which resolves the param to a real Property and
  already 404s for a cross-org id, a malformed id is "no such property",
  so it stays a **404** and simply switches to DRF's
  `get_object_or_404`. New shared helper `apps/accounts/query_params.py`
  (`int_query_param`) holds the parsing and the reasoning; it returns
  `None` for both absent and empty, and callers test `is not None`, so an
  explicit `?property=0` still filters exactly as before.
  **Both halves were built, and the frontend one is the root cause.** New
  `frontend/src/utils/ids.ts` (`parseRouteId`) and a shared
  `RecordNotFound` component; `PropertyMapPage`, `ActivityFormPage` and
  `SightingFormPage` each guard their route params *before* any request
  is issued, so a mistyped URL now says "that property doesn't exist"
  instead of firing four requests and showing a generic failure.
  `parseRouteId` also rejects negative and fractional values, not just
  non-numeric ones — every id here is a positive integer key, and
  `Number("-3")` is a perfectly good number that no row will ever match.
  **Verified both ways.** 8 new tests in a fourth section of
  `apps/accounts/tests.py` (90/90 with the suite, up from 82); stashing
  *only* the four view files while leaving the tests and helper ran them
  against the real pre-fix code — **5 of 8 fail, 13 subtest errors**, the
  raw `ValueError: Field 'id' expected a number but got 'NaN'` in the
  traceback, i.e. the 500 itself. The 3 that pass both ways are
  deliberate and say so in their own docstrings: one guards against
  "fixing" the 500 by making the filters strict about existence, one that
  the param still actually filters, one that `?property=` (empty) still
  means no filter. Then 19 Playwright checks in Chromium at 390px against
  a live stack: four malformed URL shapes each show the not-found
  message, issue **no** malformed request at all, and produce no 5xx —
  with a real property still saving, opening, and firing its normal
  property-scoped requests. Zero 500s in the backend log across the run.
  No migration (view logic only).
  **One adjacent thing spotted while building and deliberately NOT fixed,
  recorded so it isn't re-derived:** `PropertyMapPage` keeps its
  pinned-record set in component state, and React Router reuses the same
  component when navigating from one property to another, so pins carry
  over — and since the pin keys are `activity-<id>`/`sighting-<id>`, a
  pinned id from the first property can collide with a real record on the
  second. A one-word `key={propertyId}` fixes it, but that resets pins as
  a side effect and is a behaviour change D14 has no business making, so
  it is left as its own small item for a future session.
  **⚠️ Corrected 2026-09-09 (PM check-in) — see D15 below. The carryover
  is real, but the collision described here cannot happen** (`Activity`
  and `Sighting` ids are global `AutoField` values, so a pin from one
  property can never match a record on another, and the map filter reads
  over the current property's own features anyway), **the actual symptom
  is a different one** (the "Showing X of Y" count includes stale pins and
  can exceed its own total), **and it is unreachable through the UI
  today**. Read D15 rather than this paragraph before acting on it.
  **Fixed 2026-09-09 (2) as D15**, on this page and on its public-site
  sibling, by keying each on the property's identity so a property change
  remounts rather than carrying the pins across.
  **A sweep during the build found three *more* unguarded `Number()`
  conversions than the finding named, and established they are benign —
  recorded so nobody re-reads them as missed D14 sites.**
  `PropertyFormPage`, `PublicPropertyPage` and `PageFormPage` also convert
  a route parameter without a guard, but none can produce a 500: the first
  two feed **path** parameters, whose `<int:>` converters make a
  non-numeric fail route resolution and 404, and `PageFormPage`'s
  `propertyId` only reaches a `backTo` link and a POST **body** field,
  where DRF's `PrimaryKeyRelatedField` answers 400. That is the same
  reasoning that made the detail routes safe in the original finding. So
  D14's three pages really were the whole 500 surface. Guarding these
  three as well would be a small consistency/UX improvement (a proper
  "doesn't exist" instead of "couldn't load"), deliberately not taken
  here to keep the fix to the defect.
- ✅ **D12 (found 2026-09-08 PM check-in, BUILT 2026-09-08 programmer
  run): an editor could attach *another organization's* species to their
  own activity, by id, through the PATCH half of the activity-species
  endpoint.** Fixed as recommended — `species` is now in
  `read_only_fields`, with the reasoning kept on the field rather than at
  the call site, since the change that would undo this is someone making
  it writable again. Pinned by `apps/activities/tests.py` (the repo's
  **fifth** test module, 9 tests); 4 of them fail against the pre-fix
  code, including one that reproduces the cross-tenant denial verbatim —
  org B could not delete its own species because org A's row referenced
  it. The three that pass both ways are deliberate guards against a
  "fix" that breaks the endpoint's real job (role/quantity/detail must
  still save) or that stops honouring the POST path's org check.
  A comment was also added to `SightingActivityLinkSerializer`, the one
  latent sibling this run's check-in flagged: it leaves `sighting` and
  `activity` writable and is safe *only* because nothing writes through
  it, so the comment says what adding a PATCH route would recreate.
  **Original finding, kept for the record:**
  `ActivitySpeciesSerializer` (`apps/activities/serializers.py:123`)
  lists `species` in `fields` with `read_only_fields = ["activity"]` —
  so `species` is a writable, auto-generated `PrimaryKeyRelatedField`
  that queries the **whole** `Species` table. `activity_species_detail`
  (`apps/activities/views.py:337`) then does
  `ActivitySpeciesSerializer(link, data=request.data, partial=True)`
  with **no serializer context and no organization check**.
  **The two halves of the same endpoint disagree**, which is the
  clearest way to hold this: the POST path immediately above it
  (`views.py:313`) does `get_object_or_404(Species, id=...,
  organization=activity.organization)` and rejects exactly the id the
  PATCH path accepts.
  **This is the same class of defect the 2026-09-01 session fixed** for
  `ActivitySerializer.property/status/activity_type` and
  `SightingSerializer.property/species` — it survived that pass because
  it lives in a *through-model* serializer used only by a function-based
  view, not on a `ModelViewSet`. A sweep this run confirms it is the
  **only** remaining instance (`data=request.data` appears twice in
  non-test code; the other is `OrganizationSerializer` against the
  caller's own org).
  **Verified empirically**, on the repo's own pinned Django 5.2 / DRF
  3.15, by reproducing the exact serializer shape on plain non-GIS
  models: the PATCH validates, saves, and the response body returns the
  other org's `species_name`. Three consequences, in severity order:
  (1) **cross-org disclosure** — org B's species common names are
  readable by id enumeration, and `ActivitySerializer.species_names` is
  served **unauthenticated** by the public site
  (`apps/public_site/views.py:216`), so a foreign species name can be
  republished on org A's public page; (2) **a cross-tenant denial with
  no in-app remedy** — `ActivitySpecies.species` is `on_delete=PROTECT`,
  so org A's row now blocks org B from deleting its *own* species, via
  a row org B can neither see nor remove; (3) data integrity, since an
  activity's recorded species is no longer necessarily from the account's
  own list.
  **Scope stated honestly:** the endpoint is `ensure_role(EDITOR)`-gated,
  so this needs an editor account in *some* organization — a
  cross-tenant primitive, not an unauthenticated hole. Nothing suggests
  exploitation, and **nothing was written to the live instance to test
  it**, deliberately.
  **Framed as a build item, not a question** (the D3/D6/D7/D9 call, not
  D5/D8/D11's) — there is no product fork. **PM recommendation: add
  `species` to `read_only_fields`.** That is the tighter of the two fixes
  and it was checked against the client contract rather than assumed:
  `frontend/src/api/client.ts:569` types `update`'s payload as
  `Partial<{ role; quantity; detail }>` — **the frontend never PATCHes
  `species` at all** — so read-only breaks nothing, and changing an
  activity's species stays remove-and-re-add through the POST path,
  which already validates. (Validating in place is the alternative; it
  is strictly more code for a capability no caller uses.) The
  reproduction confirmed both that read-only closes the hole and that
  role/quantity/detail still PATCH normally.
- ✅ **D13 (found 2026-09-08 PM check-in, BUILT 2026-09-08 programmer
  run): deleting a species that is in use returned a 500, not an
  explanation.** Fixed by mirroring `ActivityTypeViewSet.destroy`, with
  the difference the check-in called out: the count spans **two**
  relations, so the message names sightings and activities separately
  ("2 sightings and 1 activity still use this species"). Pinned by
  `apps/species/tests.py` (the repo's **sixth** test module, 9 tests);
  9 of the 18 new tests across both modules error out against the
  pre-fix code with the raw `ProtectedError`.
  **One implementation nuance the check-in's recommendation didn't
  anticipate, found while building:** `ActivitySpecies` has **no** unique
  constraint on `(activity, species)` — only the POST path's
  `get_or_create` keeps it to one row per pair — so counting through-rows
  would overstate how many activities an admin has to go and fix. The
  guard counts **distinct activities** instead, and a test pins it.
  **A frontend gap was found and fixed in the same pass, without which
  the backend fix would not have reached anyone:** `SpeciesRow`'s
  `handleDelete` set an error message that the non-editing render path
  never displayed (the `{error && …}` line existed only inside the
  `editing` branch), so a refused delete would have looked like a button
  that silently did nothing. Verified in a real browser at 390px: the
  refusal renders, wraps inside the card, and the species stays listed.
  **Original finding, kept for the record:** `SpeciesViewSet`
  (`apps/species/views.py`) has **no `destroy()` override**, and neither
  does `OrganizationScopedViewSet`. Both foreign keys into `Species` are
  `PROTECT` — `ActivitySpecies.species` (`activities/models.py:177`) and
  `Sighting.species` (`sightings/models.py:29`) — so deleting a species
  that any sighting or activity references raises `ProtectedError`.
  **Verified: DRF does not convert it.** `ProtectedError` subclasses
  `IntegrityError`, not `APIException`, and
  `rest_framework.views.exception_handler` returns `None` for it, so it
  propagates to Django as an unhandled 500; there is no custom
  `EXCEPTION_HANDLER` in `config/settings.py` and no `ProtectedError`
  handling anywhere in the codebase.
  **What makes this worth recording rather than shrugging at: the same
  file's two sibling viewsets already fixed exactly this, twice, and
  said so in comments.** `WorkflowStateViewSet.destroy` and
  `ActivityTypeViewSet.destroy` (`activities/views.py:65` and `:125`)
  both guard their own `PROTECT` FK and return a 400 naming how many
  records are in the way. `Species` is the third per-org reference list
  and the only one without the guard. Reachable from the ordinary
  Delete button on the species page (admin role).
  **No fork; recommendation: mirror `ActivityTypeViewSet.destroy`** —
  count the referencing sightings and activities and return a 400
  saying so. Note for whoever builds it: the count spans **two**
  relations, not one, so the message should name both.
  **Doc consequence, deliberately not made now:** `limitations.md` says
  deleting a species is "immediate and permanent" and `species.md`
  describes Delete with no caveat — neither mentions that an in-use
  species can't be deleted at all. The session that adds the guard
  should write that text, because it will then be true; documenting the
  current 500 as intended behaviour would be the wrong fix.
- **D10 (found and fixed 2026-09-07 (4)): deleting a property turned a
  property-scoped member into an account-wide one — a property-scoped
  *admin* could take over the organization by deleting its own
  property.** `org_scoping.scoped_property_ids` read a membership's scope
  through `membership.properties`. A related manager inherits the
  *related* model's default manager, and `Property`'s hides soft-deleted
  rows — so once every property a membership was scoped to had been
  deleted, the scope came back empty, and **empty is this module's
  encoding for "account-wide access to the whole organization"**. The
  same one-word mistake sat in the invitation-accept path (an invitation
  whose property was deleted before it was accepted created an
  account-wide member) and, inverted, in the lockout guard, which asked
  `membership.properties.exists()` while `_account_wide_admin_count`
  asked it with a join — a join bypasses the manager, so the count was
  right and the per-membership check was wrong, and once they disagreed
  the guard refused to let anyone demote or remove that admin at all.
  **Severity, measured rather than argued:** the trigger is not an attack
  but the ordinary "Delete property" button, and DELETE is admin-gated
  and scope-filtered — so a property-scoped admin was authorised to
  delete its *own* property and thereby promote itself. Verified through
  the real HTTP endpoints against the pre-fix code: after that one
  request the caller got **200 on renaming the organization**, could
  reach the org's genuine account-wide admins, and could hand out
  account-wide scope. No second actor, no race, no waiting. A scoped
  viewer/editor gained read/write over every other property in the org.
  **Fixed** by reading the stored scope out of the **join table** in one
  shared helper (`org_scoping.stored_scope_ids`) wherever scope is
  *determined* — `scoped_property_ids`, both membership serializers (so
  the frontend agrees with the API rather than offering controls it
  refuses), and the two invitation paths — and by giving the lockout
  guard and the member list the same single definition of "account-wide".
  **A note for anyone tempted to simplify this back:
  `properties(manager="all_objects")` was the first fix and it is not
  sufficient.** A `prefetch_related("properties")` is populated through
  the default manager and then answers the `manager=` call from its own
  cache, silently restoring the bug — and the org admin console's member
  list prefetches exactly that. Caught by a test rather than by reading
  the diff, and pinned by `test_the_scope_read_survives_a_prefetch`. Least privilege
  falls out of it: the deleted property is still excluded from data on
  the way out, so such a member correctly sees **nothing** rather than
  everything, and gets exactly its old access back on restore. No
  migration — permission logic only. 14 tests in
  `apps/accounts/tests.py`, 8 of which fail against the pre-fix code.
- **D11 (found 2026-09-07 (4), NOT fixed — needs an owner decision): once
  the 30-day purge runs, a scope that pointed only at purged properties
  becomes genuinely account-wide.** D10's fix keeps a membership scoped
  while its properties are *soft*-deleted, but `purge_due_properties`
  hard-deletes the property, which cascades the join-table rows away. At
  that point the membership has no scope rows at all — and "no scope
  rows" is exactly what the model uses to mean account-wide, so the
  escalation is no longer distinguishable from a legitimately
  account-wide membership. **Verified, not assumed:** after a purge the
  probe membership reports `is_scoped=False` and `ensure_account_wide_admin`
  **allows** it. **Stated honestly: D10's fix reduces this from immediate
  and silent to delayed and bounded — it does not close it.** The window
  is now 30 days, during which a restore or a re-scope fixes it, rather
  than the instant the delete lands. Not fixed here because every option
  is a real fork and this is the D5/D8 shape, not the D3/D6/D7 one:
  (a) demote such a membership to viewer at purge time, (b) delete the
  membership outright, or (c) add an explicit field so "scoped to
  nothing" is representable at all, which is the structurally correct
  answer and also a migration plus a backfill whose default is itself a
  decision. **PM recommendation: (c)**, because (a) and (b) both silently
  change someone's access as a side effect of a retention timer, and only
  (c) makes the ambiguity that caused D10 unrepresentable. Worth pairing
  with a warning on the delete dialog naming members scoped only to that
  property — additive, and useful whichever option wins.
- **D9 (found 2026-09-07 (3), fixed 2026-09-07 (4)): the feedback pull
  endpoint's bearer token was compared with `!=`, not a constant-time
  compare.** Fixed with `django.utils.crypto.constant_time_compare`, plus
  10 tests in a new `apps/feedback/tests.py`. The scope stated when it was
  recorded still stands and is not retroactively inflated: this was
  hardening, not a live hole. Only one of those 10 tests fails against the
  pre-fix code — a timing channel has no functional symptom, so that test
  pins the *mechanism* rather than a result; the other nine are there for
  the invariant that would actually matter, **an unset token denies
  everything**, which nothing had asserted before. Original write-up:
  `apps/feedback/auth.py#ensure_feedback_token` does
  `request.headers.get("Authorization") != f"Bearer {token}"`. Python's
  string `!=` short-circuits on the first differing byte, so the
  comparison's duration carries information about how much of the secret
  a guess got right. **Scope stated honestly, because this is the easy
  one to overclaim:** it is a hardening item, not a live hole — the
  endpoint is reached over HTTPS across the public internet, where
  network jitter swamps the handful of nanoseconds involved, and a
  practical extraction would need an enormous, very obvious volume of
  requests. Nothing suggests exploitation, and the rest of that module is
  right (an unset token denies rather than allowing everything, which is
  the failure that would actually matter). **Recorded as a build item,
  not a question** — the D3/D6/D7 call rather than D5/D8's: the fix has
  no fork. Django ships
  `django.utils.crypto.constant_time_compare`, which exists for exactly
  this, and swapping it in is one line plus an import with no behaviour
  change for a correct or an incorrect token. Worth flagging for the
  *next* build session specifically because it is, at the moment, the
  **only** queued item that needs no owner answer — the previous six
  programmer runs each had to source their own work.
- **D7: the deployed site's cookies were not marked `Secure` — found and
  fixed 2026-09-06.** The app is served over HTTPS, but `settings.py`
  contained no transport-security settings at all, so Django's defaults
  applied and both the session and CSRF cookies went out with **no
  `Secure` attribute**. Verified against the live host rather than
  reasoned about: `Set-Cookie: csrftoken=…; Path=/; SameSite=Lax` with no
  `Secure`, **no `Strict-Transport-Security` header**, and **port 80
  reachable** (it answers 404 for both `/` and `/api/...`, and issues no
  HTTPS redirect). That is the whole chain — a browser holding a Habitat
  session that is induced to make any plain `http://` request to the host
  (an `http://` image on any page, a stale bookmark, a typed address)
  puts `sessionid` and `csrftoken` on the wire in cleartext, where an
  on-path observer can read them and act as that user. The server
  answering 404 does not help: the cookies are in the *request*.
  **Scope stated honestly:** this needs an attacker positioned on the
  network path *and* something to trigger one plaintext request, so it is
  a real transport weakness rather than a remotely-exploitable hole, and
  nothing suggests it was exploited.
  **Why it survived:** Django's own `manage.py check --deploy` had been
  reporting exactly this (`security.W012`, `security.W016`) for as long
  as the deployment has existed — but those checks do not run as part of
  plain `manage.py check`, which is what CI runs, so nothing ever
  surfaced them.
  **Fixed** by an environment-driven transport-security block whose
  cookie flags default to `not DEBUG`, so a deployment already running
  `DEBUG=0` (as this one is — confirmed by the live host serving Django's
  `DEBUG=False` 404 page) gets the safe posture with no configuration
  edit. `config/tests.py` now asserts the defaults in both directions and
  runs Django's deploy checks against a resolved `DEBUG=0` configuration.
  See `docs/deployment-config.md`, "Transport security".
  **Left deliberately to the deployment, not decided here:**
  `SECURE_HSTS_SECONDS` (off by default — a browser remembers HSTS and it
  cannot be recalled within its `max-age`, so it is a commitment with a
  tail rather than a code default; **recommended: set it to `31536000`**)
  and `SECURE_SSL_REDIRECT` + `TRUST_X_FORWARDED_PROTO`, which must be
  enabled as a pair or the proxy in front of the app produces an infinite
  redirect loop. Both are one-line env changes for whoever owns the
  deployment.
- **Photo storage growth — measured 2026-09-14 (3), after sitting here
  unquantified since Phase 1.** Photos are stored in the database, not
  external object storage (decided — see "Recently resolved" above). That
  keeps ops simple early on, but raises real questions once volume grows:
  database size, backup time/cost, and whether any compression or size
  limit is needed — especially at large-organization scale (many
  properties, many contributors, years of photos). **The numbers now
  exist:** a 12 MP phone photo measures **2.16 MB** at JPEG q85 (Pillow
  12.3.0, the pinned version), the enforced cap is **8 MB**, and there is
  **no quota and no per-record count limit**. At 10 photos/visit twice
  weekly that is **2.1 GB/year for one person** and **52.2 GB/year for a
  25-contributor land trust** — of *database*, and therefore of backup.
  This question is no longer open for want of measurement; what remains
  open is the decision, split into **D32** and **D33** below.
- **D32 — the app stores full-resolution photos it has no way to display.
  Found 2026-09-14 (3). Needs an owner decision.** Nothing resizes an
  upload (both endpoints `image.read()` the bytes verbatim), no derivative
  is ever generated, and `photo.url` is referenced in exactly two places —
  `PhotoUploader.tsx:58` and `PublicPhotoGrid.tsx:27` — both `<img src>`
  inside an **84×84** `.photo-thumb` box. There is no lightbox, modal or
  anchor anywhere, so **the full resolution is never rendered at any size
  by any code path.** Measured: the grid needs **16,885 B** at DPR 3
  against the **2,157,786 B** stored — **128× the bytes and 192× the
  pixels**. Stated without overclaiming: the bytes *are* reachable via the
  browser's own "open image in new tab", which D6 deliberately preserved
  by declining `Content-Disposition: attachment`; what is missing is any
  in-app route. **The fork, which is why this is the owner's:** derive a
  thumbnail and *keep* the original (fixes transfer, storage unchanged),
  or downscale on upload (fixes storage, but **irreversibly discards**
  detail a restoration record may want years later). A build session must
  not settle that alone.
- **D33 — no cache validator on any image the app serves, so no request
  could ever be conditional. Found 2026-09-14 (3), ✅ BUILT 2026-09-14 (4).**
  **What shipped:** a stored `..._sha256` column beside each of the four
  blob columns (migrations `accounts/0014`, `activities/0005`,
  `sightings/0002`, each schema + backfill in one), written by
  `images.store_image` so bytes/type/digest cannot drift; `serve_image` in
  `apps/accounts/images.py` answering `If-None-Match` with a 304; and all
  **eight** paths switched to it. `Cache-Control: private, no-cache`
  uniformly — deliberately no `max-age`/`immutable` anywhere, see the
  sub-question below. **Measured on a live server, 6-photo page × 20
  views: 42,271,274 B → 2,113,614 B (20.0×), 114 × 304.**
  **The reason the digest is a stored column rather than a hash of the
  body: the metadata-only lookup is the half that matters.** Hashing
  inside `image_response` returns a correct 304 and cuts transfer while
  still reading the whole blob out of Postgres on every request — built
  and measured, it fails **4 of 107** tests and every outcome test passes.
  **Three wrong fixes were built, and they fail on disjoint tests:** the
  body-hashing one above (only the blob-column mechanism test); strong
  `If-None-Match` comparison (**only** `test_a_weak_validator_still_matches`,
  1 of 107); and `public, max-age=31536000, immutable` (only the
  shared-cacheable header test — the *retraction* test passes against it,
  because its failure is that the request never arrives, which is
  unobservable server-side). **A guess the measurement corrected:** JPEG
  photos were assumed incompressible, making the weak-ETag case exotic. A
  real 359 KB JPEG compresses ~2%, enough for `GZipMiddleware` to keep the
  compressed response — so the server really does hand out `W/"..."` and
  the strong-comparison fix would re-send **every photo, every time**.
  D27's substring trap was live again: the failure prints
  `{'image', 'image_sha256'}`, so `"image" in sql` matches both ways.
  Original finding follows.
  `image_response` (`apps/accounts/images.py`) returns
  `HttpResponse(bytes(data), content_type=...)` and nothing else — no
  `ETag`, no `Last-Modified`, no `Cache-Control`. A grep across the whole
  backend finds **one** cache header in total, the custom-HTML document's
  deliberate `no-cache`; `ConditionalGetMiddleware` is absent from
  `MIDDLEWARE`. This covers all **eight** serving paths D6 enumerated.
  `image_response` (`apps/accounts/images.py`) returns
  `HttpResponse(bytes(data), content_type=...)` and nothing else — no
  `ETag`, no `Last-Modified`, no `Cache-Control`. A grep across the whole
  backend finds **one** cache header in total, the custom-HTML document's
  deliberate `no-cache`; `ConditionalGetMiddleware` is absent from
  `MIDDLEWARE`. This covers all **eight** serving paths D6 enumerated.
  **Verified on the deployment against the strongest available control —
  the other half of the same host:** the Vite-served frontend returns
  `cache-control` *and* `etag`, the Django API (`server: WSGIServer/0.2`)
  returns neither, so nothing in between is stripping them. **Then
  measured in real Chromium**, three endpoints differing only in headers,
  same page loaded five times in one profile: bare → **5 requests, 0
  conditional, 320 KB**; `ETag` + `immutable` → 1 request, 64 KB; `ETag` +
  `no-cache` → 5 requests but 3 × 304 and 128 KB. So every page view
  re-downloads every photo in full *and* re-reads every blob out of
  Postgres. **What makes the fix easy:** photos are immutable — the routes
  are `GET`/`POST`/`DELETE` with no `PATCH` anywhere — so a strong `ETag`
  over the bytes needs no invalidation scheme. **One sub-question flagged
  rather than left to be discovered, because it is D3 resurfacing:** the
  eight paths are not homogeneous. Theme banners are *replaced in place*,
  so `immutable` is wrong for them; and a public photo can be
  **retracted** (its property going private or being deleted), so a
  shared-cacheable `public, max-age=<large>` there would re-open exactly
  the gap D3 closed — a cached copy nothing in the app can reach.
  Recommendation: `private, no-cache` + `ETag` on anything publicly
  retractable, which the measured row shows still cuts full bodies 3×
  while keeping every request conditional.
- **D32 and D33 compound, and neither is pagination.** A 6-photo property
  page viewed 20 times a month transfers **246.9 MB** today; caching alone
  makes it 12.3 MB (20×), thumbnails alone 1.9 MB (128×), **both 98.9 KB
  (2,556×)**. Each alone leaves the other's waste entirely intact — the
  same shape as D30/D31's bound-plus-compression compounding to ~545×.
  **Severity honestly:** neither is a security defect and the deployment
  holds **zero photos** today (checked, read-only), so these are measured
  projections of a real slope, not a live incident. Whether any
  *authenticated* org has photos can't be determined from here — the same
  no-database-access limit as the D6 backfill.
  **⚠️ Corrected 2026-09-18 (PM check-in): the "zero photos" measurement
  above was true when taken and is now false, and D32's projection has
  been validated against a real photo.** The deployment holds at least
  **two** photos — activity 2 and activity 5 on property 1, both public,
  uploaded 2026-09-10 (four days *before* D32 was written, so this is a
  measurement error, not drift). The one on activity 5 is
  **1,899,250 B**, within **12%** of D32's synthetic 12 MP projection of
  2,157,786 B — so the estimate that made this item's case holds up
  against reality. **How the original zero was reached, because the trap
  generalises and this run walked straight into it too:** photos are a
  separate **sub-resource** (`/api/public/activities/<id>/photos/`), not
  a field on the record, so counting `feature["properties"]["photos"]`
  over the activities list returns 0 for every record — it is counting a
  key that **does not exist**. The key set is
  `{activity_type, …, species_names, status, …}` with no `photos` in it.
  A count over an absent key is indistinguishable from a count of zero,
  which is **D27/D30's substring trap in a new form**: the instrument
  reported the reassuring answer because it was not looking at anything
  at all. *Before believing a zero, assert that the thing you counted is
  present.*
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
- **Nothing ran the repo's tests — found 2026-09-05, ✅ the additive half
  BUILT the same day; the gating half is still the owner's call.**
  `.github/workflows/tests.yml` now runs, on every push to `main`, every
  pull request, and on manual dispatch: `manage.py check`,
  `makemigrations --check --dry-run`, and `manage.py test` against a real
  `postgis/postgis:16-3.4` service container, plus `npm ci`, `tsc -b` and
  `vite build` for the frontend. It needs **no repository secrets and no
  hosting decision**, so it is green or red on its own merits from the
  first run.
  **Each guard was verified to fail, not just to pass** — a suite whose
  red path nobody has seen is the same class of problem as a suite nobody
  runs. Stripping the four `property__deleted_at__isnull=True` guards from
  `apps/public_site/views.py` produces 5 failures (so this workflow would
  genuinely have caught D3); an unmigrated model change exits 1 from
  `makemigrations --check` and writes no stray migration file; a type
  error exits 1 from `tsc -b` rather than being skipped by its incremental
  build cache.
  **Still open, deliberately: whether `build-and-push` should `needs:` this
  workflow.** Gating means a red commit stops publishing `latest`; not
  gating means the badge goes red while the image ships anyway. The PM
  recommendation is **gate it** — publishing an image from a commit known
  to be broken is worse than publishing nothing, and `latest` is what a
  deployment pulls — but the owner has deliberately tuned that workflow
  twice (the tag policy 2026-08-27, the conditional builds 2026-08-28), so
  its publish behaviour is not being changed under them without a yes.
  `tests.yml` carries a comment saying exactly this and how to wire the
  gate when the answer comes. The original finding follows, kept because
  the shape of it is the reusable part:
  `apps/public_site/tests.py`
  (added 2026-09-04, the repo's first backend tests, written precisely
  because that invariant had already regressed silently once) has **never
  executed in CI**, because `.github/workflows/` holds exactly one file
  and it only builds and pushes Docker images: no test job, no
  `manage.py test`/`check`/`makemigrations --check`, no `tsc -b`/`vite
  build`, and no `pull_request` trigger. Neither Dockerfile validates
  anything either — the backend image installs GDAL, pip-installs and
  copies source; the frontend image runs `npm install` and `npm run dev` —
  so a commit that fails `manage.py check` or `tsc -b` publishes exactly as
  cleanly as one that passes. Verified against real Actions history, not
  inferred: run #73, the commit that *introduced* the tests, built and
  pushed `cravenator/habitat-backend:latest` in 23 seconds without running
  them; 73 runs, all green, none of which has ever run a test.
  **The shape is the same as the unperformed purge above, one week later:**
  the repo acquired a guarantee and never acquired anything that performs
  it. Severity stated honestly — nothing is broken today, because every
  session verifies for real against a live PostGIS stack before pushing,
  which is a stronger check than 7 tests; the risk is a suite nobody runs
  rotting into a suite nobody trusts, "the repo has tests" reading as "the
  repo is covered," and a future session making a small change without
  standing up a full stack having no floor under it.
  **Unlike mechanism (i) for the purge above, this needed no secrets and no
  hosting decision**, which is why a build session could take it without
  asking. **Verified against the real thing:** Tests run #1 is green, and
  its log shows `Found 7 test(s)` → `Ran 7 tests` → `OK` rather than a
  vacuous pass. Full write-up in `build-questions.md` (2026-09-05).
- **Both workflows will eventually break on GitHub's Node 20 deprecation —
  found 2026-09-05 by the first real CI run, not fixed.** The runner
  reports `actions/checkout@v4` and `actions/setup-python@v5` target Node
  20 and are being forced onto Node 24. **A warning, not a failure** —
  everything passes today — so it wasn't "fixed" reflexively on a guess
  about which version to pin. It applies to `docker-publish.yml` equally
  (same `actions/checkout@v4`, plus the `docker/*` actions), so it is one
  small maintenance pass across both files, worth doing when major-version
  bumps for those actions are actually available.
  **Re-checked 2026-09-22: there is nothing to do here from inside a
  session, and the reason is worth writing down.** Every action in both
  workflows is already at a current major — `checkout@v4`,
  `setup-node@v4`, `setup-python@v5`, `paths-filter@v3`,
  `docker/*@v3/v5/v6` — so the pass is blocked on *newer majors existing*,
  which cannot be established from here: it would mean reading
  repositories outside this session's GitHub scope. The in-scope way to
  settle it is to read a recent CI run's log and see whether the
  deprecation warning is still emitted and what it now names. Current
  state remains a warning, not a failure.
- **The live instance is served by two development servers, and no
  production image exists — found 2026-09-05 (3), needs an owner answer
  before it can be built.** Checked against the live host rather than the
  repository, which is why five prior check-ins reading the same files
  missed it. `https://habitat.dev.cravenator.com/api/auth/csrf/` returns
  `server: WSGIServer/0.2 CPython/3.12.14` — Django's `manage.py
  runserver`, which its own docs say in bold not to use in production —
  and the frontend serves `/@vite/client` and `/src/main.tsx` (200,
  `text/javascript`) with the React Refresh HMR preamble in its HTML, so
  it is the Vite dev server compiling source per request rather than a
  built bundle. **This was predicted:** the 2026-08-26 session that added
  `docker-publish.yml` recorded that a production frontend image was "a
  real follow-up *if these images are meant to actually run somewhere*",
  and two days later they were pointed at this host. The conditional
  fired; the follow-up never did — the same shape as the unperformed
  purge and the unrun tests, except the gap is in the repo, so there is
  no production image to deploy even if someone wanted to.
  **Severity stated honestly:** `DEBUG` is verified **off** (a
  nonexistent path returns Django's plain production 404, not the debug
  page), TLS terminates in front of it, the security headers are present,
  the served source isn't secret (public repo), and `package-lock.json`
  pins Vite **5.4.21** — past the 5.4.15 fixes for the `/@fs`
  path-traversal issues that matter for an exposed dev server. So this is
  posture and performance, not a known exploit. What it costs: the
  mobile-first frontend ships unminified per-request modules on exactly
  the bad-connection phone use case it exists for, `runserver` has no
  concurrency or supervision story underneath photo endpoints that stream
  bytes out of the database, and whenever hosting is decided the work
  isn't "point it at the images" because they don't exist.
  **✅ BOTH HALVES NOW ANSWERED AND BUILT (2026-09-17).** Q1: the owner
  decided this host **stays dev, permanently**, and production gets its
  own domain — so `runserver` and the Vite dev server are correct here and
  are **not a defect for a later session to "fix"**. Q2: the owner
  approved production stages, and they are built. Each Dockerfile now
  builds two images selected by `--target`, with `production` last so an
  untargeted `docker build` yields the safe one:

  - **backend** — `gunicorn` (not uvicorn: nothing in this app is async,
    so an ASGI server buys nothing) with **one worker and four threads**,
    plus **whitenoise** and a `collectstatic` run at build time. There was
    no `STATIC_ROOT` at all before this, which is not cosmetic: Django
    admin is the only place the per-tenant custom-HTML kill-switch can be
    set, and at `DEBUG=0` its CSS and JS 404 with nowhere to serve them
    from.
  - **frontend** — multi-stage `vite build`, output served by nginx as
    static files, with SPA fallback, `immutable` on the content-hashed
    `/assets/` and `no-cache` on `index.html`. It deliberately does **not**
    proxy `/api`; the deployment's ingress routes `/api`, `/admin` and
    `/static` to the backend. Naming a backend host in the image is
    exactly what would stop it being deployment-neutral.
  - **the dev images are kept**, selected by `target: dev` in
    `docker-compose.yml`, so local development is byte-identical.

  **The correction that made the frontend half more than a Dockerfile
  change:** `VITE_*` values are substituted at *build* time, so a naive
  multi-stage build bakes one deployment's URLs into the published image —
  which collides with the owner's release plan (tag once, deploy that
  artifact) and with this repo's own rule that an environment-specific
  value becomes a variable the deployment overrides. Measured: the marker
  string is present in `dist/assets/*.js` and `import.meta.env` appears
  **zero** times in the output, so no ConfigMap can reach it. `client.ts`
  therefore defaults a *production* build to a **relative** `/api`. The
  published bundle contains **zero** occurrences of `http://localhost:8000`
  against a control string that is present.

  **Whitenoise and GZipMiddleware both want the slot after
  `SecurityMiddleware`**, and the ordering is decided rather than
  accidental: whitenoise second, gzip third, because whitenoise answers a
  static request in its *request* phase, so second means gzip never
  re-compresses bytes `CompressedManifestStaticFilesStorage` already
  compressed once at collectstatic time. Pinned by a test, because the
  response is identical either way and only the CPU differs.

  **Verified without a Docker daemon** (there is none in these sandboxes,
  the same limit as 2026-09-05 (4)), by exercising every step the
  Dockerfiles perform: `collectstatic` against an unreachable
  `POSTGRES_HOST` (it opens no database connection — which is what makes
  a build-time collect possible), then the real gunicorn CMD serving the
  API, Django admin at `DEBUG=0` with hashed static filenames, whitenoise
  returning the pre-compressed copy, and the shipped `nginx.conf` under a
  real nginx against a real `vite build`. Then the whole production shape
  — nginx + gunicorn behind one origin — driven in Chromium: **9/9**,
  including that every API request is same-origin and none goes to
  `localhost:8000`. **`.github/workflows/tests.yml` now builds both
  `production` targets on every push and PR** (no push, no secrets), which
  is the part a session cannot do locally and which also means the first
  `vX.Y.Z` tag exercises a new *publish* rather than a new *build*.

  Original framing, kept for the record — **left as a question rather than
  a build item**, unlike the last two
  findings: a production Dockerfile needs a static-server choice, a
  WSGI/ASGI choice, a worker count, a static-files strategy
  (`collectstatic`/whitenoise — nothing here does that today) and a
  decision about whether the dev images stay for local `docker-compose`,
  all downstream of this same hosting question. It is also possible this
  is already an informed choice — the host is named `dev`. Full write-up
  and the recommended shape in `build-questions.md` (2026-09-05 (3)).
  **The one part of D5 that needed no owner answer is now built
  (2026-09-05 (4)): the images are reproducible, and no `.env` reaches an
  image layer.** `frontend/Dockerfile` copied only `package.json` and ran
  `npm install`, never the lockfile, so the published image's dependency
  set was not reproducible and was **not the set CI tests** (CI uses
  `npm ci`) — green CI did not imply a green image. It now copies
  `package-lock.json` too and runs `npm ci`. **The drift was measured, not
  assumed:** resolving this same `package.json` fresh on 2026-09-05
  produced **37 differently-versioned packages** against the committed
  lockfile — `react-router-dom` 6.30.4 vs 6.30.6 among them — on the same
  machine within the same hour. Vite itself happened to match (5.4.21
  both ways), so the "past the 5.4.15 path-traversal fixes" claim above
  holds for the image too — but by luck rather than by construction,
  which is exactly what pinning removes.
  Both contexts also gained a **`.dockerignore`** (there was none). The
  backend's excludes `.env`, which matters because `docker-compose.yml`
  *requires* a `backend/.env`, so on any machine following the documented
  local-dev path that file exists with a real `SECRET_KEY` and database
  password and `COPY . .` would bake it into a layer. Published images
  were never affected (`.env` is gitignored, and Actions builds from a
  clean checkout) — locally built ones were. The frontend's excludes
  `node_modules`, which would otherwise land on top of the clean tree
  `npm ci` just installed, in a later layer, possibly built for another
  platform. Verified that **no tracked file in either context is
  excluded** (82 frontend / 122 backend, zero), that `.env.example`
  survives the negation, and that `npm ci` → `tsc -b` → `vite build` →
  `npm run dev` all succeed against the lockfile-exact tree.
  **Everything else in D5 is untouched and still needs Q1/Q2 answered** —
  these are still the dev images, still running `runserver` and Vite's
  dev server.
- **D6: an uploaded photo could be an SVG, and the app served it back as
  `image/svg+xml` — executable script on the app's own origin** (found
  2026-09-06 PM check-in; **built the same day** — see
  `build-questions.md`'s two 2026-09-06 entries). All four upload
  endpoints validated with the same copied one-liner —
  `if not (image.content_type or "").startswith("image/")` — against
  `image.content_type`, which is the **client-supplied** multipart part
  header, not anything derived from the bytes. `image/svg+xml` passed,
  and all eight serving paths echoed the stored value straight back,
  including the `AllowAny` public-site twins.
  **Fixed in both halves, because either alone would be incomplete:**
  new `apps/accounts/images.py` holds one allowlist (`image/png`,
  `image/jpeg`, `image/webp`, `image/gif`) that all four upload
  endpoints now call, and `image_response()` — used by all eight serving
  paths — serves the *allowlisted* value rather than the stored string,
  so a row written before the fix cannot still steer a response header.
  That second half is what makes the database's existing contents stop
  mattering: an already-stored SVG is now served
  `application/octet-stream`, which renders as nothing in an `<img>` and
  downloads rather than executes on navigation.
  **The sub-question was answered rather than guessed:**
  `Content-Disposition: attachment` was **not** added, per the PM
  recommendation — the two halves above close the hole completely, and it
  would change what "open image in new tab" does for legitimate photos.
  The **backfill check was not run**: this session has no access to the
  live database, and the dev host was down throughout the run. It is now
  informational rather than remediation, precisely because the serving
  fix makes a stored bad value inert — still worth running once by
  whoever has database access:
  `SELECT DISTINCT content_type` on `activities_activityphoto` and
  `sightings_sightingphoto`, plus the two
  `theme_header_image_content_type` columns.
  **Why an allowlist on the declared type is enough without sniffing the
  bytes:** `nosniff` is on (Django's default), so SVG bytes uploaded
  under a declared `image/png` are served as `image/png` and the browser
  will not sniff its way back to SVG. The two are load-bearing together,
  and `apps/accounts/tests.py` pins that header so the dependency is
  stated rather than assumed.
  **Covered by 16 new tests** (`python manage.py test apps.accounts`),
  four of which were confirmed to fail against the pre-fix code and pass
  after it.
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

  **Re-confirmed and sharpened 2026-09-17 (owner, live):** *"will remain
  dev. Production will be hosted on another domain."* This **closes D5's
  Q1** — the dev host is not meant to be production-shaped, permanently,
  so its `runserver` + Vite dev server is correct there and is not a
  defect to fix. It is a re-confirmation of the 2026-08-29 split rather
  than new information, with one thing added: "eventually" is now
  "permanently separate", so no future session should propose migrating
  the dev host toward production shape.

  **What this re-scopes rather than closes** — recorded so the next
  session doesn't read "hosting answered" as "these are done":

  - **D5's Q2 (a production image) is now *needed*, not blocked.** It was
    deferred because it sat downstream of an undecided hosting model. A
    separate production domain means the dev-oriented Dockerfiles cannot
    serve it, so nginx-vs-`vite preview`, gunicorn-vs-uvicorn, worker
    count and `collectstatic`/whitenoise become live build questions —
    just aimed at the prod target, not this host.
  - **D37 (no version tags, `latest` only) gets sharper, not softer.** A
    production domain pulling `latest` is precisely the configuration
    where an unreviewed push reaches users, and where D37's finding
    (nothing to roll back *to*, since only `latest` exists for the
    frontend) actually bites. The `vX.Y.Z` mechanism already exists in
    `docker-publish.yml` and has never fired.
  - **D35 (backups) and D36 (rollback) narrow to production.** Whether
    the *dev* host is backed up or can be rolled back is now a
    don't-care; both questions are real only for the prod target, and
    both stay the owner's.
  - **D40a's throttle store becomes a genuine two-environment fork.**
    Dev is one `runserver` process, where the default per-process
    `LocMemCache` is fine. Production may run multiple workers, where the
    same code silently becomes a per-worker limit N times looser than it
    reads. So the throttle must either declare a shared cache or refuse
    to pretend — it cannot be written as if one environment exists.
  - **A real cron for the property purge** is a prod concern; the
    boot-time sweep in `entrypoint.sh` remains adequate for dev.

  **All three follow-ups answered the same day (owner, live):** prod does
  **not exist yet** — *"once I have a good candidate I'll tag the docker
  image with a version and stand up prod"*; hosting is **self-hosted**,
  *"a server in my basement"*, operated by the owner; and prod runs the
  **same published images**, *"released from a recent build using
  releases and tags in GitHub"*.

  So the hosting model is now decided end to end: **self-hosted, owner-
  operated, two domains, released by GitHub tag.** This also answers the
  long-open **"whoever runs this one"** (nineteen check-ins) — it is the
  owner, for both deployments, which makes it a contact string in
  `deployment-config.md` rather than a product question.

- **D41 (found 2026-09-17, from the owner's own release plan) — tagging
  a version and standing prod up from it would put Django's `runserver`
  and Vite's dev server on the public internet.** Not a defect in what
  exists (the dev host is meant to be dev); the plan and the images
  simply don't meet. Verified by reading both Dockerfiles:
  `frontend/Dockerfile` ends `CMD ["npm", "run", "dev"]` and
  `backend/Dockerfile` ends `CMD ["python", "manage.py", "runserver",
  "0.0.0.0:8000"]`. The frontend file's own header calls itself a "Local
  dev / dev-instance image" and defers the production-image question to
  the owner — correct while hosting was undecided, **and that deferral
  has now expired.**

  **It compounds with three things already measured:** D40 (login costs
  ~600 ms CPU unthrottled, and `runserver` has no worker pool, so a core
  sustains <2 attempts/sec — on basement hardware); **D5 Q2's specifics
  remain unanswered** (gunicorn vs uvicorn, static serving, workers,
  `collectstatic`/whitenoise) and are now the blocking work; and **the
  release path has never executed once** — measured **zero git tags** and
  zero GitHub releases, so `type=semver` has never fired and the first
  `vX.Y.Z` push exercises an untested workflow path at the moment it is
  needed. A dry run on a throwaway tag is cheap insurance.

  **The CI gate stops being a nicety.** `build-and-push` declares only
  `needs: changes`, not `tests.yml`, so a tag push publishes regardless
  of whether the 220 backend tests pass — and under this plan that image
  *becomes production*. Still formally unanswered; flagged, not assumed.

  **PM recommendation for D5 Q2:** production-stage the two existing
  Dockerfiles rather than adding new ones — backend gunicorn (nothing
  here is async, so uvicorn buys nothing) plus whitenoise; frontend a
  multi-stage `vite build` served as static files; keep the dev images
  for `docker-compose`, selected by build target.

  **Self-hosting sharpens D35 rather than closing it:** no managed
  provider means no snapshots anyone else takes, and D32's 52.2 GB/year
  of photos plus D35's 59.5 GB/year compressed backup land on a disk in
  the same building as the server — which is not a backup. The dev host
  has already shown the failure mode: the 2026-09-06 outage was a power
  outage.
- **Vanity slug URLs — implemented 2026-08-29.** See "Recently resolved"
  above for the shape as built and the sub-question calls made. (Org slug
  globally unique; property slug unique per-org; auto-generate with
  collision suffix; admin-editable with validation; numeric IDs kept for
  backward compatibility.)
- **D53 (found 2026-09-22 (2) PM check-in) — Habitat has three slug
  namespaces in the public URL space, protects two of them with reserved
  words, and the unprotected one is `Property`.** `Organization.save()`
  passes `reserved=RESERVED_ORG_SLUGS` and `OrganizationSerializer`
  checks it; `Page.save()` passes `reserved=RESERVED_PAGE_SLUGS` and
  `PageSerializer` checks it; **`Property.save()` passes no `reserved=`
  at all and `PropertySerializer.validate_slug` checks only per-org
  uniqueness.** The same asymmetry shape as D26 (two siblings carry the
  guard, the third doesn't).

  **Measured on react-router 6.30.6** with the real route table
  transcribed from `frontend/src/App.tsx` in order, run through
  `matchRoutes` — not reasoned from its ranking rules. The two literal
  segments the router places above `:propertySlug` are `explore` and
  `pages`, and **the two collisions are disjoint and complementary**: a
  property slugged `explore` loses its **root** (`/public/<org>/explore`
  renders the *organization's* Explore portfolio) and keeps its children;
  a property slugged `pages` keeps its **root** and loses its children
  (`/public/<org>/pages/<x>` resolves to the *organization's* authored
  page `<x>`). Controls in the same run: an ordinary property slug
  resolves correctly at all three of root/explore/pages.

  **The dangerous half is `pages`, not `explore`.** `explore` fails
  visibly — the visitor lands somewhere obviously not the property.
  `pages` fails invisibly: if the org has a page with that slug, the
  visitor is served a different, real page with a **200 and no error
  anywhere**. D52's family — confidently wrong beats broken.

  **The backend is not implicated.** Django resolves
  `o/<org>/explore/` to `property_detail_by_slug` correctly, because
  those patterns differ in segment *count*. The API can serve the
  property; the app's own URL cannot reach it — so it is a frontend
  routing defect whose fix belongs where the slug is minted.

  **The router's own comment says the opposite, in the reassuring
  direction.** `App.tsx:76-80` states that the literal segments ranking
  higher than `:propertySlug` means *"a property can't accidentally
  shadow these"* — the mechanism is right and the conclusion is
  backwards: that ranking is what shadows the **property**. D19's class
  (a comment denying what its own code does), D46's (a correct
  observation applied to the wrong option).

  **Scope, honestly:** not a security or tenancy defect — every shadowing
  case stays **inside one organization** (its own Explore, its own page),
  so nothing crosses an org boundary and nothing private is exposed. The
  numeric fallback `/public/properties/<id>` keeps working. Likelihood is
  genuinely low: it needs a property *named* "Explore" or "Pages", or an
  admin typing that slug into the Public URL name field by hand. What
  earns it a record is that it is wholly unguarded, the fix mirrors two
  siblings, and the comment covering it asserts the case is handled.
  **Not determinable from here:** whether any deployment holds such a
  row (the standing D6/D28 database-access limit).

  **D53a — BUILT 2026-09-22 (programmer session).** New
  `RESERVED_PROPERTY_SLUGS = {"explore", "pages"}` in
  `apps/accounts/slugs.py`, passed as `reserved=` in `Property.save()`
  and checked in `PropertySerializer.validate_slug` with its own
  message; `App.tsx`'s comment corrected. No migration. Seventeen tests
  (section 18 of `apps/accounts/tests.py`), suite 358 → 375.
  **Re-measured rather than transcribed**, and against the version that
  actually ships: the lockfile pins react-router **6.30.4**, not the
  6.30.6 a fresh resolve gave the check-in. The disjoint-and-
  complementary result reproduces exactly. The minted fallbacks were
  measured too rather than assumed — `explore-2` and `pages-2` resolve
  correctly at root, `/explore` and `/pages/<x>` alike.
  **Four wrong fixes built and measured** (red out of 17): not built at
  all **10**; `reserved=RESERVED_PAGE_SLUGS` **6**; serializer check only
  **5**; `save()` `reserved=` only **5**; reserved refusal reusing the
  uniqueness message **2**. That last is seen only by assertions about
  *wording* — no status code and no row differs — and it **had** a sole
  catcher, measured at 1, until re-reading the new tests adversarially
  found D46's vacuous-witness shape in two of them and the fix for one
  incidentally caught it as well. D49a's "weak and load-bearing are not
  opposites".
  **The correction worth keeping is to this run's own test.** The
  route-table test — the one that exists so a future
  `/public/:orgSlug/gallery` route cannot re-open this silently — first
  compared the parsed segments against `RESERVED_PROPERTY_SLUGS`, and
  **passed against the named trap**, because swapping the *usage* to
  `RESERVED_PAGE_SLUGS` leaves the constant correct and merely stops
  consulting it. *A guard over a set nothing is required to use is the
  "configured and does nothing" family (D40, D43, D45, D46, D49) living
  in a test.* Re-anchored to behaviour — both layers, per parsed
  segment — it now catches three of the four.
  **Build note (3) resolved as stated rather than assumed: no data
  migration.** A property already slugged `explore`/`pages` keeps it;
  `save()` only mints when the slug is empty. Renaming is a live URL
  change and whether any deployment holds such a row is still not
  determinable from here. `limitations.md` documents the residue and the
  numeric fallback; a test pins the choice so a later "be consistent"
  pass goes red rather than silently rewriting a published URL.

  Original build notes, kept for reference — four, none a fork:
  (1) **the set is `{"explore", "pages"}`, not `RESERVED_PAGE_SLUGS`** —
  Page's set is `{"explore"}` only, because a page slug sits deeper in
  the URL where `pages` is harmless, so importing the sibling constant
  looks like reuse and leaves the *more dangerous* half live; build that
  variant and confirm a test catches it (D17's rule); (2) correct
  `App.tsx`'s comment in the same pass; (3) existing rows aren't fixed by
  a validator — renaming one can only improve matters, but it is a live
  URL change, so state the call rather than assume it; (4) a
  reserved-word refusal wants its own message, distinct from the
  uniqueness one (`Organization`'s pair is the precedent).

  **D53b — the owner's half, and it re-opens D24 rather than filling a
  gap.** Should two organizations ever be able to mean the same plant?
  Every reference list is per-org by construction, and D24 decided the
  species list starts empty with no external taxonomy. That is coherent
  for the single-org case this project has; what it costs at two orgs and
  up is the open question, and because answering it reverses a decision
  it is not a build-session default. Filed as a re-opening, not a
  duplicate (D22's un-parking discipline).

  **Audited clean under the same lens**, recorded so it isn't
  re-derived: all three reference lists (`Species`, `WorkflowState`,
  `ActivityType`) derive from `OrganizationScopedViewSet`, so reads are
  filtered and creates stamped, and the two seeded lists are seeded
  per-org by `post_save` receivers — no cross-org reach anywhere.
  `RESERVED_ORG_SLUGS` genuinely works (verified: `/public/org/1` still
  matches the numeric route), so `App.tsx:70-75`'s comment is **correct**
  — only the one below it is not. And the org-slug collision message is
  **not** an enumeration oracle: every org slug is already anonymously
  resolvable at `/public/<slug>` (there is no org-level `is_public`
  gate — that is D8's Q2), so the validator discloses nothing the public
  site does not.

- **QR code generator for public URLs — implemented 2026-08-29.** See
  "Recently resolved" above for what was built and the sub-question calls
  (server-side PNG via `qrcode`+Pillow; offered on both the org admin
  portal and each public property page; center-logo embedding at
  error-correction level H).
- **D30 — the notification bell re-downloads an unbounded, never-purged
  history every 60 seconds to render 20 rows** (found 2026-09-14 PM
  check-in; **BUILT 2026-09-14 (2)**, both halves — the retention question
  below stays open and is the owner's).
  `notification_list` returns *every* notification the recipient has ever
  received (`_readable` filters on `recipient` only — no limit, no unread
  filter, no pagination); nothing ever purges them (the repo's one
  management command is `purge_deleted_properties`); `NotificationsBell`
  polls it every 60s with **no `open` guard**, from `TopBar`, so on every
  authenticated screen; and it then renders `.slice(0, 20)`. Measured at
  307 B/row: 1,000 lifetime notifications = 304 KB/poll = **143 MB per
  8-hour day, per open tab**, to show 20 rows; 5,000 = 717 MB/day.
  **The distinguishing property is that this cost is paid whether or not
  anyone opens the app** — unlike a list page, which is expensive once, on
  visit. **The attractive wrong fix is naming itself in advance:** slicing
  the queryset silently breaks the unread badge, because `unreadCount` is
  *derived client-side* from the full list
  (`NotificationsBell.tsx:67`) rather than sent by the server — D28's
  "never delivered vs. not displayed" lesson in a new place. The fix is
  two-part: bound the list **and** send an exact `unread_count`. Whether
  old notifications should be *purged* rather than merely un-fetched is a
  separate retention question and is **the owner's** — see
  `build-questions.md` (2026-09-14).
  **As built:** `NOTIFICATION_LIST_LIMIT = 20` (a named constant carrying
  its own rationale), and the response is now
  `{"results": [...], "unread_count": N}` where the count is a separate
  `COUNT(*)` over *all* the caller's unread rows, unaffected by the bound.
  The client renders every row it is sent rather than slicing again, so
  the bound and the number of visible rows are one quantity instead of two
  that can drift — which is how the gap opened. **Re-measured
  independently rather than inherited:** 251 B/row here (the check-in's
  307 B used a longer message), so 1,000 lifetime notifications cost
  251 KB/poll = **115 MB per 8-hour day** pre-fix. Post-fix, with D31's
  compression, a poll is **461 bytes on the wire regardless of history
  size** — 4,992 → 461 measured through real HTTP — so the same case is
  **0.23 MB/day**, and the payload is now flat rather than growing.
  **`Notification.Meta.ordering` gained `-id`** (migration
  `notifications/0002`, `AlterModelOptions`, no table rewrite): `created_at`
  alone is not a *total* order, and that only became a correctness problem
  once a LIMIT was applied over it — two rows sharing a microsecond tie and
  the database may return either, so two identical requests could disagree
  about which rows are in the newest 20. Same shape as D2.
  **Three wrong fixes were built and measured, not just named**, and the
  result is that they are caught by *disjoint* tests: (a) slice and leave
  the badge alone — caught by the exactness test; (b) count the rows you
  just sliced, which looks like it honours the contract because the field
  exists — caught **only** by the test comparing the count against
  `len(results)`; (c) slice in Python after fetching, which returns the
  identical 20 rows while still reading and serializing the whole history —
  **byte-identical response**, caught **only** by the mechanism test
  asserting the `LIMIT` is actually issued. Each is blind to precisely what
  the others catch.
- **D31 — nothing is compressed, and the dominant compressed cost on the
  org-wide lists is geometry those pages never draw** (found 2026-09-14 PM
  check-in; **the compression half BUILT 2026-09-14 (2)**; the geometry
  half re-deferred, see below). The live host returns
  **no `content-encoding`** even when gzip is explicitly offered, and
  `GZipMiddleware` is absent from `MIDDLEWARE` — 7.0x is available for one
  line. Separately, geometry is **43% of the raw activities payload but
  92% of the compressed one** (coordinates are high-entropy digits that
  barely compress, while repetitive keys vanish), and **three of the four
  unfiltered org-wide callers read none of it** — `ActivitiesPage` and
  `TasksPage` contain no occurrence of `geometry`, and `DashboardPage`'s
  only hit is the word inside a comment. Only `SightingsPage` needs it,
  for its map, and a sighting's point is 73 B. Measured at 10,000
  activities: 6.1 MB raw -> 868 KB gzipped -> **62 KB gzipped without
  geometry (99%)**. One sub-question stated rather than left to be
  discovered: Django warns `GZipMiddleware` enables **BREACH** where a
  body carries a secret — no CSRF token appears in any body (checked),
  and the one token-bearing body is the admin-only
  `InvitationSerializer.accept_url`. **This reorders the standing
  pagination question rather than adding to it — see the queue-state
  section below.**
  **As built (compression half):** `GZipMiddleware` added to `MIDDLEWARE`,
  positioned directly below `SecurityMiddleware` — `process_response` runs
  bottom-up, so a middleware listed *early* compresses *late*, after
  everything below has finished writing the body, which is Django's own
  documented ordering and what keeps CorsMiddleware's headers intact.
  Measured **10.8x on real HTTP** (4,992 → 461 bytes on the notifications
  list), better than the check-in's 7.0x because the bounded payload is
  more repetitive.
  **The BREACH sub-question is answered rather than accepted, and the
  answer is better than the check-in assumed:** the pinned Django
  *mitigates* BREACH rather than merely exposing it —
  `GZipMiddleware.max_random_bytes` is 100, so every compressed response
  carries a random-length pad, which is exactly the defence against a
  compression-ratio oracle. That is a property of the Django version, not
  of this repo, so it is pinned by a test: a downgrade past it removes the
  grounds for the setting and should go red rather than quietly proceed.
  Enabled everywhere, no per-view exemption. Two things checked rather
  than assumed while enabling it: the middleware returns the original
  response when compression doesn't shrink it, so the DB-stored photo
  endpoints pass through unbloated (pinned by a test), and `Vary:
  Accept-Encoding` is set so a shared cache can't hand compressed bytes to
  a client that never asked.
  **The geometry half is deliberately NOT built.** It needs a query param
  on the two list endpoints and a way for `GeoFeatureModelSerializer` to
  omit the geometry that defines its own output shape — and those
  serializers are shared with the public site, so the blast radius is
  wider than the change looks. It is a real design call plus a real
  re-verification burden (public site, both maps, both form pages), and
  this run had already shipped the two fork-free items with full
  verification. Re-deferred rather than half-built or shipped
  under-verified. **Its value is undiminished and now easy to state: the
  two built items already take a 1,000-notification poll from 251 KB to
  461 bytes, and compression alone takes a 10,000-row activities load from
  6.1 MB to 868 KB; dropping unrendered geometry is the next 14x on top of
  that** (868 KB → 62 KB).
  **As built (geometry half, 2026-09-21 (5)) — after six consecutive
  check-ins recommended it and five sessions re-deferred it for scope.**
  `?geometry=omit` on the two authenticated list endpoints, opt-in,
  `list`-only. New `backend/apps/accounts/geometry.py` owns the rule, the
  parameter and a `without_geometry()` factory; both viewsets defer the
  column **and** swap in a serializer that never reads it. Wired up on
  the five callers that draw nothing (`ActivitiesPage`, `DashboardPage`,
  `TasksPage`, and both form pages' link pickers); **`SightingsPage` and
  `PropertyMapPage` deliberately keep geometry**, because they plot it.
  **Re-measured on real HTTP rather than inherited**, with 6-vertex
  polygons at 7-decimal precision: at 10,000 activities **6.42 MB raw →
  680 KB gzipped → 117 KB with geometry omitted (82.8% of the compressed
  payload)**. The inherited raw figure (6.1 MB) reproduces; the
  compressed ones differ because the original was measured against the
  live host's own 4-5 vertex rows, so quote whichever fixture you mean.
  **Both halves are required and each alone is a distinct wrong fix** —
  five were built and measured (table in `build-questions.md`). The one
  that is invisible in the response body is *serializer swapped, defer
  forgotten*: correct output, every coordinate still read out of Postgres,
  caught by exactly one test.
  **`Property` was deliberately left out, and joined 2026-09-22.**
  `Property.boundary` is nullable and `PropertiesPage` renders exactly
  that distinction ("Boundary drawn" / "No boundary drawn yet"), so
  omitting it would collapse *not sent* into *not drawn* — D47's lesson.
  Making it safe needed a database-annotated `has_boundary`, because a
  Python check reads the deferred column and reopens the per-row-query
  trap.
  **As built (2026-09-22):** `annotate_has_boundary` in
  `geometry.py`, a `has_boundary` field on `PropertySerializer`, and
  `?geometry=omit` on `PropertyViewSet.list`. Wired up on the **six**
  callers that draw nothing (`PropertiesPage`, `DashboardPage`,
  `ActivitiesPage`, `SightingsPage`, and Manage's Members and
  Recently-deleted sections); **`QuickLogPage` deliberately keeps the
  shapes**, since it infers which property a dropped pin landed on.
  **No migration.**
  **The design changed mid-build because a test said so.** The first
  version annotated every action; an annotation is evaluated when the row
  is *fetched*, so on an `update` it described the property as it was
  **before** the write — a PATCH that drew a boundary answered
  `has_boundary: false`. So: annotate exactly where the column is
  deferred, and have the serializer **prefer the loaded column**, asking
  the annotation only when the column is deferred. The reverse of the
  obvious order, and the only one that cannot go stale. *A derived column
  is a snapshot of the row at fetch time — anywhere the row is then
  mutated, it is a stale answer that looks authoritative.*
  **The inherited framing is corrected rather than confirmed.** D31 said
  "the lever is on activities regardless: an org has a handful of
  properties". True in absolute terms, and it understates the proportion:
  measured on real HTTP with hand-drawn 30-vertex perimeters, **303 B
  gzipped per row → 31 B**, i.e. **89.8% of the compressed payload at 20
  properties** and 97.1% at 200×80 — above activities' 82.8%, because a
  property row carries little else besides its boundary. One property row
  costs about **4.5 activity rows** (against D31's 68 B 6-vertex
  fixture), so twenty properties cost roughly ninety activities — on six
  screens rather than three. The difference is vertex count, not record
  type; say which fixture you mean.
  **D27's substring trap in a new form, and section 15's matcher is
  unusable here.** The real SQL emits both
  `"accounts_property"."boundary"::bytea` (reading it) and
  `"accounts_property"."boundary" IS NOT NULL` (the annotation asking
  about it) — so `has_boundary` **mentions the very column it exists to
  avoid reading**, and a whole-name match fails against the correct fix
  while passing against the wrong one. `_selects_column_value` matches
  the cast instead.
  **The frontend guard is weaker than D31's, and that was measured.**
  On a lean row `polygonBounds(row.geometry)` and `row.geometry.coordinates`
  are both compile errors, but **`row.geometry ? … : …` compiles** — and
  that is precisely this change's own regression, which would silently
  label every property undrawn. `null` is falsy and testing it is legal
  TypeScript. D31's guard looked stronger only because non-null geometry
  gives nobody a reason to truthiness-test it. There is still no frontend
  test runner, so the client half is pinned by nothing.
  **The frontend guard is a type, not a convention:**
  `WithoutGeometry<F>` narrows `geometry` to `null`, so a *defensive*
  `g ? g.coordinates : null` — what a careful developer writes, and what
  would otherwise compile and silently draw nothing — is a compile error
  (`Property 'coordinates' does not exist on type 'never'`, proven with a
  throwaway probe). Its honest limit, also measured: assigning a lean row
  where a full `Activity` is expected still compiles, because `null` is
  assignable to `PolygonGeometry | null`.

- **D52 — a record logged before Habitat recorded who logged it cannot be
  saved: the PATCH is a 500, and the edit commits anyway** (found
  2026-09-21 (5) while building D31's geometry half, **not caused by
  it** — reproduces with that change stashed; BUILT the same session).
  `created_by_email` sources a nullable FK; DRF's `Field.get_attribute`
  consults `default` **before** `allow_null`, and `get_default()` raises
  `SkipField` whenever the serializer is partial — which is exactly what
  a PATCH is. DRF's own `Serializer.to_representation` catches that;
  **`GeoFeatureModelSerializer.get_properties` is a reimplementation of
  the same loop that omits the `except`**, so it propagates to an
  unhandled 500 (the D13/D18/D26/D46 shape, a fifth time). Needs all
  three of a nullable dotted source, a geo serializer and a partial
  request — so Activity and Sighting only.
  **Reachability, measured from this repo's own history rather than
  assumed:** `perform_create` only started writing `created_by` on
  **2026-09-13** (`80631f3`), and D38 put `created_by_email` on the
  authenticated serializers on **2026-09-16**. Every activity and
  sighting logged before 13 September therefore 500s the moment anyone
  opens it and saves. **Confirmed live on the deployment, read-only, without
  writing anything:** the public activities endpoint exposes
  `created_at`, and **all six public activities on property 1 predate
  2026-09-13** (oldest 2026-08-26, newest 2026-09-11). **No migration
  anywhere backfills `created_by`** — checked; only the initial schema
  migrations mention the column — so every one of those rows still has a
  NULL author and 500s on save today. Only *public* rows are readable
  anonymously, so six is a floor rather than a total (the standing
  D6/D28 limit).
  **Worse than a 500, measured end to end against a real server:**
  `UpdateModelMixin.update` saves and *then* renders, and this project
  sets no `ATOMIC_REQUESTS`, so the response is a 500 **and the edit is
  committed**. The app saves your change and tells you it failed; a user
  who retries re-applies a snapshot that D29 makes stale.
  **As built:** `attribution_field` declares `allow_null=True` instead of
  `default=None` — one keyword, and **the option the original note
  explicitly ruled out**. Measured (table in `attribution.py`): a *bare*
  read-only field really does raise, which is what that note observed;
  it then used that to reject `allow_null`, which is the only one of the
  four declarations that works on both a GET and a PATCH. Adding a
  `default` back alongside it silently restores the bug, because
  `default` is checked first — pinned by a test. D46's shape: the trap
  was named and the witness was wrong.

## App feedback / build workflow

**2026-09-25 (PM check-in) pulled `[]`** — the **eighty-first** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so
the `[]` is a real empty queue rather than a broken endpoint. Nothing
reported broken, so nothing was escalated as a blocker.

**2026-09-24 (3) (programmer session) pulled `[]`** — the **eightieth**
pull, both negative controls re-run (tokenless → 403, wrong token →
403), so the `[]` is a real empty queue rather than a broken endpoint.
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-24 (2) (PM check-in) pulled `[]`** — the **seventy-ninth**
pull, both negative controls re-run (tokenless → 403, wrong token →
403), so the `[]` is a real empty queue rather than a broken endpoint.
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-23 (2) (programmer session) pulled `[]`** — the
**seventy-eighth** pull, both negative controls re-run (tokenless → 403,
wrong token → 403), so the `[]` is a real empty queue rather than a
broken endpoint. Nothing reported broken, so nothing was escalated as a
blocker.

**2026-09-24 (PM check-in) pulled `[]`** — the **seventy-seventh** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so
the `[]` is a real empty queue rather than a broken endpoint. Nothing
reported broken, so nothing was escalated as a blocker.

**2026-09-23 (programmer session) pulled `[]`** — the **seventy-sixth**
pull, both negative controls re-run (tokenless → 403, wrong token → 403),
so the `[]` is a real empty queue rather than a broken endpoint. Nothing
reported broken, so nothing was escalated as a blocker.

**2026-09-23 (PM check-in) pulled `[]`** — the **seventy-fifth** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so
the `[]` is a real empty queue rather than a broken endpoint. Nothing
reported broken, so nothing was escalated as a blocker.

**2026-09-22 (3) (programmer session) pulled `[]`** — the
**seventy-fourth** pull, both negative controls re-run (tokenless → 403,
wrong token → 403), so the `[]` is a real empty queue rather than a
broken endpoint. Nothing reported broken, so nothing was escalated as a
blocker.

**2026-09-22 (2) (PM check-in) pulled `[]`** — the **seventy-third** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so the
`[]` is a real empty queue rather than a broken endpoint. Nothing reported
broken, so nothing was escalated as a blocker.

**2026-09-22 (programmer session) pulled `[]`** — the **seventy-second**
pull, both negative controls re-run (tokenless → 403, wrong token → 403).
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-21 (5) (programmer session) pulled `[]`** — the
**seventy-first** pull, both negative controls re-run (tokenless → 403,
wrong token → 403). Nothing reported broken, so nothing was escalated as
a blocker.

**2026-09-21 (4) (PM check-in) pulled `[]`** — the **seventieth** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so the
`[]` is a real empty queue rather than a broken endpoint. Nothing reported
broken, so nothing was escalated as a blocker.

**2026-09-21 (3) (programmer session) pulled `[]`** — the **sixty-ninth**
pull, both negative controls re-run (tokenless → 403, wrong token → 403).
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-21 (2) (PM check-in) pulled `[]`** — the **sixty-eighth** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so the
`[]` is a real empty queue rather than a broken endpoint. Nothing reported
broken, so nothing was escalated as a blocker.

**2026-09-20 (5) (programmer session) pulled `[]`** — the **sixty-seventh**
pull, both negative controls re-run (tokenless → 403, wrong token → 403).
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-20 (4) (PM check-in) pulled `[]`** — the **sixty-sixth** pull,
both negative controls re-run (tokenless → 403, wrong token → 403), so the
`[]` is a real empty queue rather than a broken endpoint. Nothing reported
broken, so nothing was escalated as a blocker.

**2026-09-20 (2) (programmer session) pulled `[]`** — the **sixty-fifth**
pull, both negative controls re-run (tokenless → 403, wrong token → 403).
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-20 (PM check-in) pulled `[]`** — the **sixty-fourth** pull, both
negative controls re-run (tokenless → 403, wrong token → 403), so the `[]`
is a real empty queue rather than a broken endpoint. Nothing reported
broken, so nothing was escalated as a blocker.

**2026-09-19 (2) (programmer session) pulled `[]`** — the **sixty-third**
pull, both negative controls re-run (tokenless → 403, wrong token → 403).
Nothing reported broken, so nothing was escalated as a blocker.

**2026-09-21 (PM check-in) pulled `[]`** — the **sixty-second** pull, both
negative controls re-run (tokenless → 403, wrong token → 403). The steady
state; nothing reported broken, so nothing was escalated as a blocker.

**2026-09-19 (programmer session) pulled `[]`** — the **sixty-first**
pull, both negative controls re-run. Recorded here for completeness: that
run logged it in its queue-state entry and not in this section, so the
sequence had a gap.

**2026-09-20 (PM check-in) pulled `[]`** — the **sixtieth** pull, both
negative controls re-run (tokenless → 403, wrong token → 403). The steady
state; nothing reported broken, so nothing was escalated as a blocker.

**2026-09-18 (3) (programmer session) pulled `[]`** — the **fifty-ninth**
pull, both negative controls re-run (tokenless → 403, wrong token → 403).
The steady state; nothing reported broken, so nothing was queued as a
blocker.

**2026-09-19 (PM check-in) pulled `[]`** — the **fifty-eighth** pull,
both negative controls re-run (tokenless → 403, wrong token → 403). The
steady state, one cycle after F1 shipped.

**2026-09-18 (2) (programmer session) pulled `[]`** — the
**fifty-seventh** pull, both negative controls re-run (tokenless → 403,
wrong token → 403). Back to the steady state one pull after the
fifty-sixth broke a forty-one-pull silence. **Feedback 15 (F1) was built
this session**, one day after it was submitted — the shortest
report-to-shipped turnaround in this project's history, which is worth
recording as evidence the pipeline is doing its job rather than merely
existing.

**2026-09-18 (PM check-in) pulled ONE REAL ITEM** — the **fifty-sixth**
pull, and the first non-empty one since **feedback 14 on 2026-09-11**,
ending a **forty-one-pull** silence. Both negative controls re-run
(tokenless → 403, wrong token → 403).

> **id 15** · org *Craven Household* · `test@gmail.com` ·
> `page_path: /properties/1/activities/5/edit` · 2026-09-17T23:23:16Z
> — *"I should be able to click on photos to view a larger version"*

**Recorded as F1 below and triaged in `build-questions.md`; marked synced
after recording.** Three things about it are worth keeping separately from
the request itself:

- **`page_path` earned its keep for the third time.** The path names
  activity **5** on property **1** — which is what let this run go and
  measure *the actual photo the user was looking at* rather than reason
  about photos in general. Without it the item is "photos are too small
  somewhere."
- **The user independently reported a limitation the manual already
  documents.** `limitations.md:95-101` says plainly that there is no
  click-to-enlarge and names the browser's own "open image in new tab" as
  the way to the detail. So the manual is accurate and needs no
  correction (the D16/D19/D33/D38 shape). What the report adds is
  *evidence the gap is felt*: a documented limitation that a user files
  feedback about has stopped being theoretical, which is a prioritisation
  signal no audit lens can produce.
- **It is the viewing half of D32, and that half was never actually
  forked.** See F1.

**2026-09-17 (4) (programmer session) pulled `[]`** with both negative
controls re-run (tokenless → 403, wrong token → 403) — the **fifty-fifth**
pull and the steady state.

**2026-09-17 (3) (PM check-in) pulled `[]`** with both negative controls
re-run (tokenless → 403, wrong token → 403) — the **fifty-fourth** pull
and the steady state.

**2026-09-16 (3) (programmer session) pulled `[]`** with both negative
controls re-run (tokenless → 403, wrong token → 403) — the
**forty-ninth** pull and the steady state.

**2026-09-16 (2) (PM check-in) pulled `[]`** with both negative controls
re-run (tokenless → 403, wrong token → 403) — the **forty-eighth** pull
and the steady state.

**2026-09-15 (2) (programmer session) pulled `[]`** with both negative
controls re-run (tokenless → 403, wrong token → 403) — the
**forty-seventh** pull and the steady state.

**2026-09-16 (PM check-in) pulled `[]`** with both negative controls
re-run (tokenless → 403, wrong token → 403) — the **forty-sixth** pull
and the steady state.

**2026-09-15 (programmer session) pulled `[]`** with both negative
controls re-run (tokenless → 403, wrong token → 403) — the **forty-fifth**
pull and the steady state.

**2026-09-15 (PM check-in) pulled `[]`** with both negative controls
re-run (tokenless → 403, wrong token → 403) — the **forty-fourth** pull
and the steady state. No investigation needed; an empty pull against a
healthy, still-authenticating endpoint is the normal result.

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
the steady state, not a signal to go looking for a fault. **The 2026-09-04
(4) programmer run and the 2026-09-05 check-in each pulled `[]` too — six
consecutive.** The 2026-09-05 run also confirmed the endpoint still
*rejects* a tokenless call with a 403, so an empty pull is a real empty
queue rather than a silently-degraded auth path returning nothing.
**The 2026-09-05 (3) check-in pulled `[]` as well — eight consecutive**,
with the same tokenless-403 confirmation repeated. Eight empty pulls in a
row is the steady state; the loop is idle because the queue is empty, not
because it is broken. **The 2026-09-05 (4) programmer run pulled `[]`
too — nine consecutive.** **The 2026-09-06 check-in pulled `[]` as
well — ten consecutive**, with both negative controls re-run this time:
a tokenless call and a call bearing a *wrong* token each returned 403,
so a 200 carrying `[]` is a genuinely empty queue and not an auth path
that has quietly started accepting anything. **The 2026-09-06 (2)
programmer run could not pull at all** — the dev host was down for that
whole session (a power outage, owner-confirmed), so that run neither
continued nor broke the streak. **The 2026-09-06 (3) check-in pulled `[]`
with both negative controls re-run — the eleventh empty pull**, against a
recovered host. So exactly one *run* is missing from the sequence, not a
pull result. **The 2026-09-06 (4) programmer run pulled `[]` as well,
both negative controls re-run (tokenless → 403, wrong token → 403) — the
twelfth.** **The 2026-09-07 check-in pulled `[]` too, both negative
controls re-run — the thirteenth.** **The 2026-09-07 programmer run
pulled `[]` too, both negative controls re-run — the fourteenth.**
**The 2026-09-07 (3) check-in pulled `[]` too, both negative controls
re-run (tokenless → 403, wrong token → 403) — the fifteenth.**
**The 2026-09-07 (4) programmer run pulled `[]` too — the sixteenth**,
this time also exercising the endpoint's auth from the inside: the new
`apps/feedback/tests.py` asserts the correct token is accepted and that
a missing, wrong-but-same-length, prefix, scheme-less or unconfigured
token is refused, so the negative controls now have a checked-in
counterpart rather than being re-run by hand every session.
**The 2026-09-08 check-in pulled `[]` too, both negative controls re-run
(tokenless → 403, wrong token → 403) — the seventeenth; the 2026-09-08
programmer run that followed it pulled `[]` again with both controls
re-run, the eighteenth; the 2026-09-08 (3) check-in pulled `[]` with both
controls re-run as well, the nineteenth; the 2026-09-08 (4) programmer
run pulled `[]` with both controls re-run, the twentieth; the 2026-09-09
check-in pulled `[]` with both controls re-run, the twenty-first; the
2026-09-09 (2) programmer run pulled `[]` with both controls re-run, the
twenty-second; the 2026-09-10 check-in pulled `[]` with both controls
re-run, the twenty-third; the 2026-09-10 (2) programmer run pulled `[]`
with both controls re-run, the twenty-fourth; the 2026-09-10 (3) check-in
pulled `[]` with both controls re-run, the twenty-fifth; the 2026-09-10 (4)
programmer run pulled `[]` with both controls re-run, the twenty-sixth; the
2026-09-10 (5) PM check-in pulled `[]` with both controls re-run, the
twenty-seventh; the 2026-09-10 (6) programmer run pulled `[]` with both
controls re-run, the twenty-eighth; the 2026-09-11 PM check-in pulled `[]`
with both controls re-run, the **twenty-ninth**; the 2026-09-11 programmer
session pulled `[]` with both controls re-run, the **thirtieth**; the
2026-09-11 (3) PM check-in pulled `[]` with both controls re-run, the
**thirty-first**.**

**The streak ended on 2026-09-11 (4): the programmer run pulled two real
items (ids 13 and 14), the first non-empty pull since 2026-09-03.** Both
were triaged and built the same run (see `build-questions.md`, 2026-09-11
(4)) and then marked synced. Worth recording because the preceding note
had become a standing assumption: thirty-one empties in a row is a
*steady state*, not a dead pipeline, and the moment a user typed something
it came straight through. The mechanism didn't need attention; it needed
a user. Also worth knowing for the next reader: **item 14 turned out to be
two requests in one sentence** — a fork-free half (see "Logged-in app UX")
and a data-model question — so a single feedback id does not necessarily
map to a single build item.

**The 2026-09-12 PM check-in pulled `[]` with both negative controls
re-run — the thirty-second pull, and the first empty one since the streak
broke.** One real batch in thirty-two runs is now the observed rate rather
than an inference from a single streak: empty is the steady state, and the
one non-empty pull came from somebody using the app, not from the
mechanism changing.

**The 2026-09-12 programmer run pulled `[]` too, with both negative
controls re-run (tokenless → 403, wrong token → 403) — the
thirty-third.** **The 2026-09-12 (3) PM check-in made it the
thirty-fourth**, same two controls, same result. **The 2026-09-12 (4)
programmer run made it the thirty-fifth**, again `[]` with tokenless and
wrong-token both 403 — the steady state, needing no investigation.
**The 2026-09-13 PM check-in made it the thirty-sixth**, same two
controls, same result. **The 2026-09-13 programmer run made it the
thirty-seventh**, same two controls, same result. **The 2026-09-13 (3)
PM check-in made it the thirty-eighth**, same two controls, same result.
**The 2026-09-13 (4) programmer run made it the thirty-ninth**, same two
controls, same result. **The 2026-09-14 PM check-in made it the
fortieth**, same two controls, same result. **The 2026-09-14 (2)
programmer run made it the forty-first**, same two controls, same result.
**The 2026-09-14 (3) PM check-in made it the forty-second**, same two
controls, same result. **The 2026-09-14 (4) programmer run made it the
forty-third**, same two controls, same result.

Worth stating once rather than re-deriving each run: a long run of
consecutive empty pulls against a demonstrably working endpoint is the
pipeline's normal state, not a fault. The signal to watch for is a
*non-empty* pull; an empty one needs no further investigation beyond the
negative controls that prove the endpoint still authenticates.

**`Feedback.page_path` (built 2026-09-02) is confirmed working, and paid
for itself in one cycle.** All six 2026-09-03 items arrived carrying the
screen they were sent from (`/`, `/admin`, `/quick-log`), and it changed
the triage rather than just decorating it: one item reads as a vague "too
much on one page" until its `/admin` path makes it specific, and another
is identifiable as being about the day-old quick-log flow rather than the
long-standing forms only because of its path.

**Pull log:** the 2026-09-17 programmer run made the **fifty-third**
pull — `[]`, with both negative controls re-run (tokenless → 403, wrong
token → 403), so the empty result is a real empty queue rather than a
broken credential. (The 2026-09-17 PM check-in made the fifty-second, the
same way.) Unchanged steady state since the 2026-09-11 batch; an empty
pull needs no further investigation.

**Still genuinely open:**

- Whether every org member should be able to submit feedback, or just
  admins — built as "every member," per the owner's 2026-08-29 decision,
  but worth re-confirming once this sees real multi-member use.
- No scheduled routine is formally set up to poll this on a recurring
  cadence yet — today it's pulled ad hoc by whichever PM check-in happens
  to run. Not a blocker (the check-in routine already does it each time),
  just worth noting if a tighter feedback loop is ever wanted.

## Logged-in app UX

- **D61 (found 2026-09-25 PM check-in) — the only wait Habitat bounds is
  the one for the GPS.** Measured across all of `frontend/src`:
  `AbortController` **0**, `AbortSignal` **0**, `AbortSignal.timeout`
  **0**, per-request timeout **0**. The only `timeout:` values anywhere
  in the app are **geolocation's** — `utils/geo.ts#getCurrentPosition`
  at **10 s** and `hooks/useWatchPosition` at **15 s**, both with
  explicit error handlers that surface `err.message`. ***So the
  subsystem that works with no connection is bounded, and the one that
  does not is unbounded.***
  - `fetch` has no default timeout. A request that stalls — the dead
    zone, the captive portal, the connection that is "connected" and
    carrying nothing — leaves the submit button in its `disabled` +
    "Saving…" state **indefinitely**, with no cancel and no way to tell
    a slow link from a dead one.
  - **The worst case is the photo upload**, which is also the largest
    payload the app sends (8 MB cap) and the one most likely to be sent
    from a field. `PhotoUploader` renders `"Uploading…"` and disables
    the control; there is no progress, no byte count and no cancel — and
    `fetch` **structurally cannot** report upload progress, so this is a
    real limit of the chosen API rather than an oversight.
  - **Correction to an inherited claim.** The 2026-09-09 entry records
    that `useAsync` "cancels on unmount *and* on a dependency change".
    Measured, it sets a `cancelled` flag that suppresses the **state
    update**; the request itself runs to completion, because nothing in
    the app constructs an `AbortController`. Correct about the React
    behaviour, and not the same statement as cancelling the request —
    which is the one this lens needed.
  - **Also measured, and coherent rather than half-built:** there is no
    web app manifest, no `frontend/public/` directory at all, no service
    worker, no PWA tooling and no `theme-color`/`apple-mobile-web-app-*`
    meta. Habitat cannot be installed to a phone home screen and has no
    offline shell. Recorded so a future sweep does not file each absence
    separately: they are one decision nobody has made.
  - **Q1 (the owner's): should a request time out, and at what?** Not
    free in either direction — a bound short enough to help someone in a
    dead zone will abort a large photo upload that would have succeeded
    on a slow link.

- **D62 (found 2026-09-25 PM check-in) — the species step can wedge the
  one flow built for standing in a field, and the only escape destroys
  the capture.** `utils/species.ts#resolveSpeciesId` matches a typed name
  against `known` — *"the org's species list as already loaded by the
  caller"*, a snapshot — and **never re-reads it after creating**. Its
  own docstring states the contract this breaks: *"An existing name is
  reused rather than re-created… Typing a name you already have should
  select it, not fail and not quietly fork the list in two — there is no
  species merge tool to clean that up afterwards."*
  - **Trigger A (both callers): any failure between the species write
    and the record write.** The species `POST` succeeds; the sighting
    `POST` fails; the form correctly keeps its state and shows an error.
    Press Save again and `resolveSpeciesId` re-runs against the **same
    stale snapshot**. Both branches from there are bad, and both were
    confirmed against the backend rather than assumed:
    - retry with the **same** text → `SpeciesSerializer
      .validate_common_name` matches exactly, refuses, and the user is
      shown **"You already have a species with that name."** *while
      trying to save a sighting*, about a species they believe they just
      failed to save. Every subsequent Save does the same. **Wedged.**
    - retry with **different casing** → D26's guard is deliberately
      case-*sensitive* (its own comment: `"crabgrass"` alongside
      `"Crabgrass"` is *"verified, 201"*), so the write succeeds and
      **forks the species list permanently**, with no merge tool. The
      exact outcome the helper exists to prevent.
  - **Trigger B (`QuickLogPage` only): the species list has not loaded
    yet.** It passes `species.data ?? []` and **nothing gates the detail
    step on the fetch**, so `known` is `[]` while the request is in
    flight — and the picker's `noOptionsLabel` reads *"No species in your
    list yet — add one below."*, which is false. This needs **no failure
    at all**, only a slow fetch, which is the normal case on a phone in a
    field. It self-heals once the fetch lands.
  - **The asymmetry is the finding, and it is D26's shape.**
    `SightingFormPage` gates on `species.loading` and renders the form
    only once `species.data` exists. Same shared helper, two callers,
    one waits and one does not — **and the one that does not is the
    field-capture flow.** D47a's lesson ("ask what a list's empty value
    means") applied at one site and missed at the other.
  - **The escape is the cost.** Nothing recovers the wedge except a
    reload, which re-reads the list — and loses the dropped point and the
    typed notes, because nothing is persisted and `beforeunload` is
    **0** app-wide.
  - **Takeable and fork-free**, split so the smaller half can ship
    alone — see the queue-state subsection below.

- **D63 (found 2026-09-25 PM check-in) — 21 screens report a failed
  load; exactly one offers to retry it.** Measured per file: 21 render a
  *"Couldn't load…"* message and only `PropertiesPage` pairs it with a
  control (`onClick={reload}`, labelled **Retry**). Everywhere else a
  failed load is terminal for that screen — the user navigates away and
  back, or reloads the page. `useAsync` already exposes `reload`, so the
  affordance exists and is wired up at one of twenty-one sites. Small,
  fork-free, and the wording is already established two files away.

- **D64 (found 2026-09-25 PM check-in) — the app answers "no signal" in
  two registers, and picks the less useful one for the work that
  matters.** A dropped connection raises a plain `TypeError`, not an
  `ApiError`, and the app splits on that distinction **49 ways one way
  and 8 the other**:
  - **49 sites** test `err instanceof ApiError`, so a `TypeError` falls
    through to the house string. **11 of them say "Something went
    wrong."** — and four of the eleven are the record-creation paths:
    `QuickLogPage`, `SightingFormPage`, `ActivityFormPage`,
    `PropertyFormPage`. ***So the app's most generic message is what a
    user gets for losing signal while saving the work this app exists to
    capture.***
  - **8 sites** test `err instanceof Error`, which a `TypeError`
    satisfies — and one of the eight is **`useAsync`**, i.e. every load
    error on all 21 screens. Those show the **browser's own raw text**,
    which differs per browser ("Failed to fetch", "Load failed",
    Firefox's own wording), e.g. *"Couldn't load properties: Failed to
    fetch"*.
  - **This corrects the framing the lens invites.** It is not that
    Habitat never mentions connectivity — it mentions it inconsistently,
    in raw untranslated browser text, and **the register is inversely
    related to what the action cost the user**: a read that can simply be
    repeated gets the informative string, and a write that cannot gets
    the one that says nothing.
  - **Q1 (the owner's): should Habitat detect and name a connectivity
    failure at all?** Not free: `navigator.onLine` reports link-layer
    state, not reachability, so it returns `true` on a captive portal and
    in a dead zone with a bar of signal — a "you appear to be offline"
    banner built on it is wrong exactly when it matters.

- **Q (the owner's, and the one that reframes the rest): does Habitat
  intend to work without a connection?** Measured, nothing in the client
  persists anything anywhere — `localStorage`, `sessionStorage`,
  IndexedDB and `serviceWorker` are all **0** — so a sighting typed in a
  preserve exists only in React state until the `POST` succeeds. The
  answer decides whether what remains is *"add a timeout and a retry"* or
  *"build a sync queue"*, and it is the question every other item in this
  sweep is downstream of. `docs/vision.md`'s subject is someone doing
  restoration work on their own land, and quick log exists specifically
  for standing in a preserve — so the app's own use case puts the user
  where connectivity is worst, which is the argument for asking rather
  than defaulting.

- **D56 (found 2026-09-24 (2) PM check-in; BUILT 2026-09-24 (3)) —
  `Combobox` gives no reliable indication of what Enter will select.**
  All four pieces shipped: `useId()`-generated option ids with
  `aria-activedescendant` + `aria-controls`; the active option scrolled
  into view; the highlight changed from `--color-bg` (**1.07:1**) to a
  solid `--color-primary` fill with white text (**5.99:1**, measured from
  rendered pixels in a real browser, against SC 1.4.11's 3.0:1); and the
  option is now the `<li>` itself rather than a `<button>` inside it.
  **Two defects were found while building that the check-in could not
  have seen from reading code, and both are recorded in
  `build-questions.md` (2026-09-24 (3)):**
  - The obvious `scrollIntoView({ block: "nearest" })` **scrolls an
    ancestor**, not the list. On the form pages the combobox sits inside
    `.map-page-scroll`, so ArrowDown scrolled the whole page region (the
    list's own `scrollTop` stayed 0) and dragged the control up the
    viewport. The shipped fix sets `list.scrollTop` by hand, which cannot
    touch any ancestor.
  - That then slid a different option under a **stationary** mouse
    pointer, and the browser fires `mouseenter` for that — so hover
    clobbered the keyboard's active index and ArrowDown could not get
    past row 7 of 20. `onMouseEnter` is now `onMouseMove`: a pointer that
    has not moved produces no mousemove, so hover-to-activate still works
    for a real mouse user and scrolling can no longer masquerade as hover.
  ⚠️ **The measurement that matters most: neither of those is catchable
  one variable at a time.** Reverting the scroll alone scores 23/23 and
  reverting the hover alone scores 23/23; only the genuine naive
  implementation — both at once, which is what anyone would actually
  write — goes red, on exactly one check. See `build-questions.md`.
  Original finding, kept for reference:
  Full measurement in
  `build-questions.md` (2026-09-24 (2)). **Takeable and fork-free** — the
  ARIA combobox pattern is a specification and "scroll the active option
  into view" is not a product preference; no owner call, no backend, no
  migration. Nine call sites across eight files: a sighting's species, a
  task's assignee, quick log's property, every linked record, the species
  filter. It is simultaneously the most carefully built component in the
  app (`role="combobox"`, `aria-expanded`, `aria-autocomplete`,
  `role="listbox"`, `role="option"`, `aria-selected`; arrow keys, Enter
  and Escape all work) and the one carrying this lens's worst defect.
  Four measured pieces, all of the same one action:
  1. **The active-option highlight is invisible.**
     `.combobox__option--active { background: var(--color-bg); }` —
     `#f7f7f5` on `--color-surface` `#ffffff`, computed at **1.07:1**
     against WCAG 2.1 SC 1.4.11's 3.0:1 non-text minimum. It is the
     *sole* visual cue for which option Enter will take.
  2. **Past roughly the sixth row it is not on screen at all.** No
     `scrollIntoView` on the active option, while `.combobox__list` is
     `max-height: 14rem; overflow-y: auto` and up to `MAX_VISIBLE = 50`
     rows render. ↓ past the visible window moves the highlight into the
     clipped region and the list does not follow.
  3. **↑/↓ announce nothing.** No `aria-activedescendant`, no `id` on any
     option, no `aria-controls`, no `id` on the `<ul role="listbox">`.
     `activeIndex` drives a CSS class and nothing else, and DOM focus
     correctly stays on the input — so with no active-descendant pointer
     a screen reader cannot know the highlight moved.
  4. **`<li role="option">` contains a `<button>`** — per ARIA an
     `option` takes text content, not interactive descendants.
  **So the control is fully keyboard-drivable with no dependable way,
  visual or announced, to know what you are about to choose** — and the
  audience it hits hardest is the **sighted keyboard user**, which is not
  who this lens would have predicted.
  **Build notes, measured in advance.** `0 of 9` call sites pass `id`
  (the prop is optional and unused), so the fix must generate ids
  internally (`useId()`) rather than require them of callers — otherwise
  `aria-activedescendant` points at nothing on every existing site and
  ships inert, this repo's most-repeated failure mode (D40, D43, D45,
  D46, D49, D53). **Do not "fix" it by focusing the option**:
  `aria-activedescendant` exists so focus can stay on the input, and
  moving it to the `<button>` breaks typing — the attractive wrong fix,
  worth building to confirm a check catches it. The contrast and the
  missing scroll are **separate** defects with separate symptoms: fixing
  the colour leaves the off-screen case, fixing the scroll leaves an
  on-screen highlight nobody can see.

- **D57 (found 2026-09-24 (2) PM check-in; D57a BUILT 2026-09-24 (3),
  D57b still open) — no error message in Habitat is ever announced.**
  **D57a shipped** as `components/Announcer.tsx`: one always-mounted live
  region (in fact two — see below) mounted in `App.tsx` *outside*
  `<Routes>`, so it survives navigation and covers the public site too,
  plus a `useAnnounce()` hook wired to the five destructive paths D55a
  shipped. Each announces **the same string it renders**, which on almost
  every real failure is D21's `statusFallback` rather than the
  hand-written fallback — verified byte-for-byte in a browser against a
  non-JSON 503, and separately against a dropped connection, which is the
  one shape that reaches the new wording.
  **Two implementation notes worth keeping:**
  - **There are two regions, written to alternately.** A screen reader
    generally does not re-announce a region set to the text it already
    holds, so failing twice identically would announce once. Alternating
    (and blanking the other) guarantees a real text change every time.
    Verified in a browser: the same failure repeated lands in the *other*
    slot.
  - **`.visually-hidden` clips to 1px; it must not use `display: none` or
    `visibility: hidden`**, either of which removes the region from the
    accessibility tree and announces nothing while looking entirely
    correct in the DOM. Asserted in the browser run.
  ⚠️ **On the named wrong fix, measured rather than argued.** Building it
  (`role="alert"` on the conditionally-mounted error, no always-mounted
  region) shows that **after the failure the DOM is indistinguishable**:
  both the real fix and the wrong fix leave a `role="alert"` carrying
  exactly the right text. Whether it is *announced* is not observable
  from the DOM at all. The only thing that separates them is the
  **pre-failure** state — was a region already in the document for a
  screen reader to have been watching — which is D33's lesson (when the
  consequence lands somewhere you have no instrument, move the assertion
  to what you can see). **D57b remains the owner's**, and D57a
  deliberately does not pre-empt it: failures only, so Q1 is untouched.
  Original finding, kept for reference:
  **72 `form-error` render sites across 37 files**,
  and `aria-live`, `role="alert"` and `role="status"` are each **0**
  app-wide. There is no live region anywhere in the application.
  **This composes directly with the last two weeks' work, which is what
  makes it specific rather than generic:** D21 (2026-09-11) exists so
  every failure carries a non-empty message, and **D55a (2026-09-23 (2))**
  exists so the five destructive deletes that destroy the user's own
  records stop failing silently. For a screen-reader user **neither
  changed anything** — the message mounts into the DOM unannounced, so a
  failed delete is still silent, which is exactly the defect D55
  described, for the user who cannot see the screen. The 2026-09-24
  check-in measured the app's whole recovery story as *"one undo and an
  error message"*; under this lens that story is **visual-only**.
  **The attractive wrong fix, named in advance:** all 72 sites are
  **conditionally mounted** (`{error && <p className="form-error">…</p>}`),
  so adding `role="alert"` at each — which looks exactly like the fix —
  is unreliable at most of them, because a live region inserted at the
  same moment its text arrives is missed by many screen-reader/browser
  pairs. The region must already be in the DOM and have its text change.
  A session that measures nothing will ship 72 edits that work on its own
  machine and not on a user's.
  - **D57a — takeable, fork-free, bounded:** one always-mounted live
    region plus the hook that feeds it, wired to the **five destructive
    paths D55a shipped**. That completes D55a rather than starting
    something new, and proves the mechanism on the smallest surface that
    matters most.
  - **D57b — the owner's.** Q1: should *success* and status messages
    announce too (`Saved`, `Copied!`, `Resent`), or only failures? An
    over-eager region is its own accessibility defect. Q2: do all 72
    sites get it, in one pass or as each file is next touched? Q3: should
    a route change announce the new page at all? There is **one**
    `.focus()` call in the app (`PhotoLightbox`'s) and no route-change
    focus management, so a keyboard user following a link lands on
    `<body>`.

- **D58 (found 2026-09-24 (2) PM check-in; `role="button"` half BUILT
  2026-09-24 (3), `onFocus` half still the owner's) — the pinnable card
  is focusable, actionable, and announces neither.**
  **Shipped in both files:** `role="button"` **plus `aria-pressed`**, and
  the accessible name is now **stable** (`Pin X to the map`) rather than
  flipping its own verb between Pin/Unpin. That pairing is deliberate: a
  toggle expresses state through `aria-pressed`, and a `role="button"`
  whose *name* changes instead leaves a screen-reader user hearing a new
  name with no state at all. Verified in a browser on both the
  authenticated and the public card.
  ⚠️ **Tradeoff, stated rather than left to be discovered:** a `<ul>`
  wants `listitem` children, so this costs the list's "N items" framing
  to buy "button, pressed". Wrapping the content in a real `<button>` is
  not available — the authenticated card contains Edit and Delete, and
  interactive elements cannot nest.
  **The `onFocus` half is untouched and remains the owner's call.**
  Original finding, kept for reference — the combined
  activity/sighting list on `PropertyMapPage` and `PublicPropertyPage`
  renders each record as
  `<li tabIndex={0} aria-label="Pin X to the map" onClick onKeyDown>`.
  - **No `role`.** An `<li>` with an `aria-label` announces as a *list
    item* with that label; nothing says it is actionable, so nothing
    suggests pressing Enter. **`role="button"` is fork-free** and rides
    along with any other frontend change here.
  - **No `onFocus` — confirmed absent in both files.** `focusedId` comes
    solely from `useFocusedListItem`, an `IntersectionObserver` over a
    band 12–108px from the top of the scroll container, so **keyboard
    focus does not drive the map**: a keyboard user Tabs through the
    cards, the focus ring moves, and the record plotted on the map does
    not follow. Tabbing scrolls a card to the *nearest* edge rather than
    into a band near the top, so the two notions disagree
    systematically. Note the naming collision that hides this:
    `.card--focused` means *scrolled into the trigger band*, **not** *has
    keyboard focus*, and only the former is plotted. **Whether keyboard
    focus should move the map is the owner's call.**
  - **Not established:** the *size* of the disagreement — that needs a
    browser, and this check-in ran none.

- **D59 (found 2026-09-24 (2) PM check-in; BUILT 2026-09-24 (3)) — the
  one place the naming convention lapses.** All four controls now carry
  an `aria-label`: `Role`, `Quantity`, `Detail (optional)` on the add
  row, and a **per-species** ``Detail for ${link.species_name}`` on each
  linked row (one renders per species, so a static name would not say
  which — the `manage/rows.tsx` precedent). Verified in a browser by
  computing each control's accessible name from **label/aria-label
  only, with placeholder deliberately excluded**, since a placeholder
  passing for a name is the whole defect. Original finding:
  Small and fork-free.
  `components/ActivitySpeciesPanel.tsx` has four controls with no label
  and no `aria-label`: the role `<select>` at `:181` (a `<select>` has no
  placeholder, so it has **no accessible name at all**), the Qty
  `<input>` at `:188`, the Detail `<input>` at `:195`, and an existing
  link's Detail `<input>` at `:149` — all placeholder-only. D26's shape:
  the **species** picker on that same row got an `aria-label` and its
  three siblings did not. A placeholder is not a label; it is not
  reliably announced and it disappears once the field has a value.
  **The fix is already written in this repo, two files away:**
  `BloomRangeFields` wraps a `<label>` **and** gives each `<select>` its
  own `aria-label`, because one label cannot name two controls.
  `pages/manage/rows.tsx`'s inline-rename inputs are the other precedent
  (a dynamic ``aria-label={`Name for the ${type.name} activity type`}``).

- **D60 (raised 2026-09-24 (2) PM check-in) — the owner's questions
  behind D56–D59.**
  1. **Does Habitat have an accessibility commitment at all?** Nothing in
     the repo states one. A land trust taking public funding may be
     required to meet WCAG 2.1 AA; a homeowner logging their own yard is
     not. The answer decides whether D56–D59 are a conformance backlog or
     four small quality fixes, and it is not a build-session default.
  2. **Is anyone using this with assistive technology, or keyboard-only?**
     Not determinable from here (the standing D6/D28 database-access
     limit) — the only way to know is to ask.
  3. **Should the public site hold a higher bar than the app?** It is the
     surface strangers reach and the one whose audience Habitat does not
     control. D39's Q2 already asked what crawlers should see; the same
     argument extends to a visitor using a screen reader.

- **D55 (found 2026-09-24 PM check-in) — every administrative delete in
  the app reports its failures; the five that destroy the user's own
  records report nothing at all.** Full measurement in
  `build-questions.md` (2026-09-24).
  **The framing measurement:** Habitat's entire answer to "something went
  wrong" is one undo and a message. Soft delete covers `Property` only
  (D34); there is **no change history on any model**; `If-Match`/`ETag`
  on writes/409 are **zero occurrences** app-wide; `ATOMIC_REQUESTS` is
  unset (8 explicit `transaction.atomic()` blocks, all in
  `accounts`/`purging`); nothing is backed up (D35). So the error message
  *is* the recovery story — which is why D21 (2026-09-11) mattered.
  **⚠️ Extended 2026-09-24 (2):** that framing is right and it has a
  further step nobody had taken. If the error message *is* the recovery
  story, then the story only reaches whoever can see it — and **D57**
  measured that no error message in the app is in a live region, so
  D55a's fix reaches a screen-reader user not at all. D57a is the
  bounded half that completes this one.
- **The defect.** Sweeping all 18 destructive actions a user can trigger,
  **per handler** rather than by grep window: 12 render an error, 1
  swallows with a stated reason (`PropertyMapPage.handleDeletePage`), and
  **5 have no `catch` at all** — delete a property (`PropertiesPage:47`
  *and* `PropertyMapPage:249`), delete an activity (`:274`), delete a
  sighting (`:281`), and delete a photo
  (`PhotoUploader.handleDelete`, reached from three mount points).
  **Those five are exactly the ones that destroy the user's own
  land-management records**; every administrative delete — members,
  invitations, reference lists, pages, feedback — reports. **D21's fix
  cannot reach them:** it exists so a failure is legible, and these never
  ask for a message.
  Three sharpenings: `PhotoUploader` **has** the `error` state and
  renders it, and only its *upload* path sets it (D26's shape, one fix in
  the component rather than three at the mount points);
  `handleDeleteProperty` **navigates away on success**, so the "the list
  shows nothing changed" argument that justifies the deliberate swallow
  fails there — not-navigating is indistinguishable from a dead button,
  right after a dialog saying this destroys the property and its records;
  and the *same* operation (delete a page) reports from Manage and
  swallows from the property page.
  **Reachable, named rather than assumed:** the backend image refreshes
  on a 15-minute schedule (a recurring 502/503 window, per D21), a second
  tab or admin gives a 404, and a role changed while the page is open
  gives a 403 on a Delete button that is still rendered.
  **Severity honestly:** not a security defect, no exposure, nothing
  destroyed that shouldn't be — the failure is that a delete *didn't*
  happen and nobody is told. Against it: the buttons are admin-gated in
  the UI matching the backend; the list not changing is *some* feedback;
  seventy-seven pulls, no complaint. Not determinable from here: whether
  any org has hit one (the D6/D28 database-access limit). **No browser
  run and nothing written to the live instance** — established by reading
  the handlers, so the fixing session should reproduce one.
  **The manual needs no correction** (D16/D19/D33/D38/D45/D46):
  `limitations.md` and `properties.md` describe what a delete *does* and
  make no claim about what happens when one fails. The gap is an
  **absence**, left for the fixing session on the D13/D24 precedent.
  **Split. D55a — BUILT 2026-09-23 (programmer session).** All five paths
  now report, in the `err instanceof ApiError ? err.message : "Couldn't
  …"` shape the twelve siblings establish. All four build notes honoured:
  `PhotoUploader` fixed in the component (its three mount points'
  `onDelete` props were checked — none catches, so there was no
  double-reporting to design around); `handleDeletePage`'s deliberate
  swallow left alone and its asymmetry recorded in `limitations.md`
  instead; **both** twin property-delete handlers done; no retry
  affordance added (that is D55b's Q1, and `limitations.md` now says so).
  Messages are **keyed to the row that failed**, not page-level — by
  property id on `PropertiesPage`, and by the combined list's own item
  key (`activity-5`/`sighting-5`, not a bare id, which would show an
  activity's failure on the sighting carrying the same number) on
  `PropertyMapPage`.
  **One layout note worth keeping:** `PropertiesPage`'s row is
  `.card card--row` — the card *is* the flex row, with
  `align-items: center` — so an error `<p>` added as a third top-level
  child lands inside its `space-between` layout. The link and the error
  share one existing `.card__stack` instead, which is the same move
  `SpeciesRow` already made (its own comment records the identical
  defect: *"a refused delete looked like a button that did nothing"*).
  Measured rather than eyeballed: the row grows 64px → 87px when the
  message shows and the Delete button's vertical centre stays at the
  row's centre (32 → 44), so the alignment is byte-identical.
  ⚠️ **And a correction to what the user actually reads.** The new
  fallback strings are reachable **only** when the failure is not an
  `ApiError` — i.e. a dropped connection. On every ordinary refusal
  `handleResponse` builds an `ApiError` whose message is the server's own
  `detail`, and on a non-JSON 5xx (the real 15-minute-refresh window) it
  is D21's `statusFallback` — *"The server is temporarily unavailable
  (HTTP 503). Try again in a moment."* So **D55a's contribution is that
  anything renders at all; the wording on the common paths is D21's.**
  Found by a red assertion that turned out to be the harness's
  expectation, not the app's behaviour — all three shapes are now driven
  separately in the browser run.
  **D55b (the owner's):** Q1 is a message enough, or should a failed
  destructive action offer to try again? Q2 **D29 proper** — should the
  app detect a concurrent edit, and how should it say so? Q3 does Habitat
  want a change history at all (**D38b's Q1 re-reached from the recovery
  side**; D54b's Q3 wants the same table — a sharpening, not a duplicate,
  per D22's un-parking discipline).
- ⚠️ **Correction to D29 (2026-09-24): it is recorded as one page and is
  seven write sites.** D29 has said *"`ActivityFormPage` PATCHes every
  field from the snapshot it opened with"* since 2026-09-13. Measured
  across all 18 `.update()` call sites, **seven** write the whole
  snapshot — `ActivityFormPage` (7 fields), `SightingFormPage` (5),
  `PropertyFormPage` (5), `PageFormPage` (5), `SpeciesPage` (5),
  `ThemeEditorPanel` (4, on both org and property), `TasksPage`'s edit
  toggle (2) — and **eleven** correctly send only what changed. Same
  inversion as D55: the app writes narrowly everywhere it configures
  itself and whole-record exactly where the user's work lives.
  **The widest field was never named: `Page.body`** — an entire authored
  public document, and two people editing one is the likely case, not the
  exotic one. `Species.description` is public-facing too.
  **And the field that would let the client notice is already delivered:**
  `updated_at` is on **five** models (`Property`, `Activity`, `Sighting`,
  `Page`, `Task`), served on all five serializers, declared on **six**
  frontend types, and read by **zero** lines of frontend code outside
  `types.ts` — D27/D28/D38's "delivered, never used" shape again. Two
  asymmetries to cost before building: **`Species` and `Organization`
  have no `updated_at` column at all**, so two of the seven could not
  detect a conflict without a migration; and **D38 shipped *who* last
  edited and not *when*** (`AttributionNote` takes no timestamp), so the
  half that would warn anyone is the half left behind.

- **D54 (found 2026-09-23 PM check-in) — nothing in Habitat knows that a
  date has passed, so "Planned / upcoming activities" is every not-done
  activity, ranked stalest-first and capped at five.** Full measurement
  in `build-questions.md` (2026-09-23).
  **The framing measurement:** the backend reads the clock **nine**
  times. Six write "now" into a column; the three that *compare* are the
  purge deadline and two token expiries — **all three are the app's own
  housekeeping, and not one is about the user's land-management work.**
  Re-measured rather than transcribed: `TruncYear`/`TruncMonth`/
  `TruncWeek`/`TruncDate`/`ExtractYear`/`ExtractMonth`/`date__year`/
  `__range` are **0** outside migrations and tests, and the only
  `__gte`/`__lte` are the bloom filter (seasonal, year-*less* by
  construction) and `purging.py:73`.
- **The defect.** `DashboardPage.tsx:33-35`'s `isUpcoming` is
  `!activity.properties.is_done` — it never looks at a date. The section
  it drives is headed *"Planned / upcoming activities"*, sorted
  **ascending** by `date_planned`, capped at `TODO_LIMIT = 5`. Swept:
  `date_planned` is never compared to anything anywhere; `overdue`,
  `past due`, `due_date`, `is_late` return **zero** hits across
  `backend/apps` and `frontend/src`; and of the **22** `validate*`
  methods in the backend, none is about a date. **Measured by running
  the app's own comparator and cap** over a nine-activity org (six
  slipped, two genuinely ahead): **0 of the 2 upcoming items are
  visible.** The ascending sort ranks the most overdue first, so the cap
  fills from the stalest end — *the section degrades in exactly the
  direction that matters: the more work slips, the more completely it
  hides what is actually coming.* Not a wrong set; the right set, ranked
  so its own heading stops being true.
- **Two things make it harder to get out of:** the section is the only
  one of the dashboard's four with **no link out** ("Your tasks" carries
  `All tasks →`), and the escape hatch shares the blind spot —
  `ActivitiesPage`'s Status filter is `is_done` again, and that page
  does **no sorting at all**, so it inherits the API's `-recorded_at`.
- **Confirmed live and read-only, nothing written.** Property 1's four
  not-done public activities today: **one dated 25 days in the past,
  zero dated in the future, three undated** — so on the owner's own
  account the "Planned / upcoming" section contains nothing that is
  upcoming, and the public property page shows an anonymous visitor
  `Planned: 2026-08-29` as a current plan. Only public rows are
  anonymously readable, so this is a **floor, not a total** (D6/D28).
- **Severity, honestly, including what argues against it:** not a
  security defect, no exposure, no 500, nothing lost. **The manual is
  accurate** (the D16/D19/D33/D38/D45/D46 shape, not D13) —
  `dashboard.md:21-24` says *"activities that aren't marked done yet …
  soonest-planned-first"*, exactly true, and `:31-34` already
  anticipates the cap. The gap is an **absence**, left for the session
  that changes the behaviour (D13/D24 precedent). And the half that cuts
  the other way: **including slipped work in "what still needs doing" is
  arguably right** — the defect is that nothing distinguishes the two,
  that the ranking favours the stalest, and that the cap then hides the
  future. A restoration org may also date loosely ("seeding, spring
  2026"), which is exactly why *"is overdue a concept?"* is the owner's
  call, not a build-session default. Needs ~5 slipped activities, so a
  small org never sees it; seventy-five pulls, no complaint.
- ✅ **D54a — BUILT 2026-09-23** (programmer session). The heading is now
  **"Planned / in progress activities"** and the section carries
  `All activities →`. No backend, no migration, no test-count change
  (375/375 unmoved — nothing backend was touched). Three things worth
  keeping:
  - **The wording was reused, not invented.** *"Planned / in progress"*
    is already the app's name for this exact `!is_done` set in **two**
    user-visible places — `ActivityStatusLegend` (the map key) and
    `ActivitiesPage`'s Status filter, which is where the new link goes,
    so a reader who clicks through and narrows sees the identical words.
    The queue framing only anticipated aligning the heading with the
    *manual*; the app already had the vocabulary, which is a stronger
    reason and was found by grepping rather than assumed.
  - **The layout claim was measured, and it corrected this run's own
    first read.** Seeing the 390px screenshot, the two-line heading
    looked like something the change had introduced. Measured at the real
    computed font, the row leaves **230px** beside the link and the
    **old** heading was already **400px** — so it wrapped before this
    change too; the link taking its own line is the entire delta. Nor
    would trimming help: *"Planned / in progress"* is 288px and still
    wraps; only a newly-invented short phrase (*"Still to do"*, 132px)
    fits inline, and that would add a fourth name for a set the app
    already names twice. Reuse beat tidiness, and the numbers are pinned
    in the JSX comment so it isn't re-derived. Nothing clips at
    320/390/1280px.
  - **The code's own vocabulary was the source and was fixed too.**
    `isUpcoming(a) === !a.is_done` is what made the caption feel true, so
    it is now `isDone`, used in both directions by the two complementary
    sections — which also removes a double negative and makes their
    complementarity visible at the call sites.
  - **Deliberately unchanged:** the ascending sort and `TODO_LIMIT`. The
    defect reproduces exactly as measured — verified in-browser against a
    seeded nine-activity org, five rows all with **past** planned dates
    and **neither** genuinely-upcoming activity visible. D54a stopped the
    heading claiming otherwise; whether the ranking itself should change
    is D54b's Q2 and stays the owner's.
- **D54b — the owner's.** Q1: should a planned date having **passed** be
  a concept at all — mark it, rank it, or neither? (The
  future-`observed_at` note below belongs here too.) Q2: should the
  sort-and-cap change so genuinely upcoming work cannot be hidden — and
  if a slipped item should rank *first*, is the cap what gives? Q3, the
  lens's own question: should Habitat be able to answer **"what did we
  do here last season", "is this working", "how has this changed"**?
  There is no date bucketing at all today, and `docs/vision.md`'s
  subject is *restoration* — a claim about change over time. Composes
  with **D50b's Q1** and **D32**. PM recommendation: D54a first, then
  Q1 (one call, unblocks Q2, independent of hosting/SMTP); Q3 should not
  be designed before Q1 is answered.
- **Three corrections and one clean audit, recorded so they aren't
  re-derived.** (1) An early grep read `Activity.Meta` as having **no
  ordering** — a truncated `-A 8` window; it declares
  `ordering = ["-recorded_at"]`. *A grep window that ends mid-block
  reports an absence it never looked for.* (2) The two record types
  order by **different kinds of time** — `Sighting` by `-observed_at`
  (when it happened), `Activity` by `-recorded_at` (when it was typed
  in), so an activity logged today for last spring's work sorts as the
  newest work. (3) `Activity` carries **two** `auto_now_add` timestamps,
  `recorded_at` and `created_at`; it orders by `recorded_at`, which
  appears in **no serializer** (only `admin.py`'s `list_display`), while
  the API serves `created_at` — harmless today, but the ordering key and
  the served timestamp are different fields and would diverge silently
  if either were backfilled. **Clean:** the classic date-only
  off-by-one **does not occur** (every `toLocaleDateString()` is on a
  `DateTimeField`; `date_planned`/`date_done` render as raw ISO);
  `toLocalDateTimeInputValue` round-trips UTC↔local correctly;
  `byRecency`'s lexical ISO sort is correct; `Notification`'s
  `["-created_at", "-id"]` still holds; and the bloom validator
  **deliberately declines** to compare its two ends because a bloom
  period may wrap the year — *the app's one piece of date reasoning is a
  correct refusal to compare dates.* One reachable consequence of zero
  date validation, recorded not filed: nothing stops `observed_at` being
  in the future, and `Sighting` orders by it, so a typo'd year pins a
  sighting to the top of the Sightings page permanently.
- **D51 (found 2026-09-21 (4) PM check-in) — Habitat's notification
  system has exactly one event, and configuring email would not change
  what it can say.** Full measurement in `build-questions.md`
  (2026-09-21 (4)).
  **The correction is the contribution, and it changes what to build
  first.** The queued framing attributes the absent-user gap to the
  missing *channel* — mail leaves nowhere (D45), the bell is in-app only.
  Measured, **the channel is the smaller half.** `Notification.Verb` has
  exactly **one** member (`TASK_ASSIGNED`); `notify()` has exactly **two**
  call sites, both in `apps/tasks/views.py`, both the *same* transition
  (assigned-to-someone-other-than-you, on create and on update);
  `CHANNELS` is a genuinely pluggable one-element list. So the
  architecture anticipated channels and **nobody ever added events** —
  and **configuring SMTP, the owner's own stated next action (D45b's Q1),
  would put exactly one sentence on the wire: "you were assigned a
  task."** The cheap half (more events) is independent of the undecided
  half (channels), and the ordering implied by the queue is backwards.
- **The asymmetry that makes it matter:** the one thing Habitat notifies
  about is a *convenience* — work you would see on your own Tasks page
  anyway. The one thing it can never undo — a property's 30-day
  destruction of every activity, sighting and photo on it — is silent
  from the moment you confirm the delete until the rows are gone. Four
  deadlines are enforced and none is announced: `Property.PURGE_AFTER`
  (30 days, **irreversible**), `Invitation.EXPIRY` (7 days),
  `PasswordResetToken.EXPIRY` (1 hour), and the session's inherited 14
  days (D49). Reassignment *away* from you notifies nobody; a task being
  completed notifies nobody.
- **Severity, honestly, including what argues against it: nothing is
  broken and no claim is false.** The delete dialog names the 30-day
  window at the moment you confirm, so nobody is ambushed. **The app is
  well-built for a user who is present** — `purge_at` is served *and*
  rendered as a correct per-property countdown with a correct singular
  case (checked specifically, because D28's "delivered, never displayed"
  trap is this repo's most-repeated finding and it does **not** apply
  here). Seventy pulls, no complaint. Not determinable from here:
  whether any org has a second admin or a genuinely absent member (the
  standing D6/D28 database-access limit).
- **Sizing note for whoever builds it, because it cuts both ways.** The
  data at the moment of destruction already exists and is discarded:
  `purge_due_properties()` returns a `PurgedProperty` per row removed
  (name, org, `deleted_at`, sighting-row count), and **two of its three
  callers throw it away** — `PropertyViewSet.deleted` and `.restore`
  both call it for effect only; only the management command reports.
  But `Property` records `deleted_at` and **no `deleted_by`** (the
  attribution gap D38 recorded for this exact model), so "tell the person
  who deleted it" is not representable without a migration.
- **The manual needs no correction, and that is this finding's shape**
  (D16/D19/D33/D38/D45/D46). `tasks.md` documents the 20-row bell, that
  the badge counts *all* unread, and that **Mark all read** clears beyond
  the twenty; `limitations.md:166-178` documents in-app-only
  notifications, the never-purged history, and that there is *"no
  notification archive to page back through"*; `properties.md:165-172`
  documents the purge and its sweep timing. All accurate. **Recorded so
  it is not re-derived as a discovery:** the >20 unreachability is a
  known, documented limitation, not a new finding.
- **Split. There is no fork-free half, and saying so is the honest
  answer** — *which* events should notify, and whether an irreversible
  purge should warn first, are both product decisions. **D51's questions
  are the owner's:** Q1 should anything other than task assignment create
  a notification — and specifically, should the 30-day purge warn before
  it fires? Q2 should a notification ever leave the app (this is D45b's
  Q1 re-framed from the *event* side, filed as a sharpening rather than a
  duplicate, per D22's un-parking discipline)? Q3 is the bell's 20-row
  window with no archive the right permanent shape, or does an absent
  user need somewhere to catch up?

- **D50 (found 2026-09-21 (2) PM check-in) — an organization cannot see
  what it has. The app counts six things, and five of them exist to
  explain why you can't delete something.** Full measurement in
  `build-questions.md` (2026-09-21 (2)).
  **Two corrections to the queued framing, both load-bearing.** First,
  *"`Count`/`aggregate`/`annotate` appear zero times"* is true —
  and **vacuous**, because that grep cannot see `.count()`, which appears
  **six** times: `unread_count` (a badge, D30), and five refusals — the
  workflow-state, activity-type and species delete guards, and the
  account-wide-admin lockout guard. The capability is present and pointed
  entirely at saying no. *D27/D30/D46's vacuous-grep trap, this time in
  the lens's own framing.* Second, the org-wide lists are unpaginated, so
  the browser already holds every row, and **four screens already render
  a count** (`ActivitiesPage`, `SightingsPage`, `SpeciesPage`,
  `PropertyMapPage`) — the framing named five missing counts and was
  wrong about three.
  **Genuinely absent**, verified per screen: properties, members, tasks,
  photos, and anything about size. **Confirmed live, read-only, with both
  controls** (549-byte SPA fallback as the negative; `No properties yet`
  as the positive): the deployed `PropertiesPage.tsx` carries **zero**
  `Showing` lines where `ActivitiesPage.tsx` carries one.
  **The inversion that makes it matter:** `PublicOrganizationPage`
  tells an anonymous visitor *"1 public property"* (measured on org 1)
  while the organization's own Properties page tells its owner nothing —
  **a stranger is handed a number the owner's screen withholds.**
  **The photo half is structurally different and is the one that
  matters.** Photos are reachable only per record, and no serializer
  exposes a count, so an org-wide total needs one request per record —
  not unrendered, *unobtainable*. The only place the app counts photos is
  **D34's delete dialog**, so **the app counts your photos exactly once:
  at the moment it destroys them.** Composes with **D32** (52.2 GB/year
  measured): the organization storing that has no screen that would say
  so.
  **Severity, honestly:** not a security defect, not a leak, nothing
  broken, and three of the five missing counts are free. Sixty-eight
  pulls have produced no complaint. What earns it a record is the D32
  composition, and that the counts which *are* shown sit on the screens
  needing them least. **The manual needs no correction** (the
  D16/D19/D33/D38/D45/D46 shape) — `dashboard.md` describes the dashboard
  accurately and `limitations.md`'s nearby bullet is about **quotas**, a
  different and true claim.
  **Split. D50a (takeable, fork-free, no backend, no migration):** render
  the counts already loaded — properties, members, tasks — in the house
  wording four screens establish. **Three traps, all measured:**
  (1) every such count is `list.length`, correct *only* because the lists
  are unpaginated — the day pagination lands each one silently becomes
  "how many we fetched", which is **D30's own finding aimed at a feature
  that doesn't exist yet**, and the reason to prefer D30's server-sent
  `unread_count` as the precedent rather than the `.length` ones;
  (2) `MembersSection`'s list is already filtered for a property-scoped
  admin, so a count from it must not claim org-wide truth; (3)
  `PropertiesPage` reads through the soft-delete-filtering manager, so a
  property count excludes recently-deleted rows — correct, and worth
  stating so it isn't "fixed". **D50b (the owner's):** Q1 an org-wide
  "what do we have" screen, or just per-list counts? Q2 **should photos
  and storage be countable** — the only part that answers D32, and the
  only one needing new API surface? Q3 is this admin-only or visible to
  every member?
  **✅ D50a BUILT 2026-09-21 (3) (programmer session)** — as a shared
  `frontend/src/utils/counts.ts#countLabel`, called from five screens.
  Frontend only; no backend, no migration; suite unmoved at 310/310.
  **Re-measuring the inherited claims rather than transcribing them
  produced two corrections, and both widened the item.**
  **Correction A: three of the "four screens [that] already render a
  count" only render it once you narrow the list.** `ActivitiesPage:191`
  is gated on `narrowed` and `SpeciesPage:304` on `filter.trim()`, so on
  arrival — the state every visit starts in — both show *nothing*. Only
  `SightingsPage` states an unfiltered total, and `PropertyMapPage`'s is
  about pinning on one property's map. So the check-in's Correction 2 was
  wrong in the same direction it was correcting: an org could not answer
  "how many activities do we have" without typing something first. Both
  now show a total unfiltered and keep "Showing X of Y." when narrowed —
  the "four filters, not two" rule, since it is one defect on adjacent
  screens of one family.
  **Correction B, and the sharper one: trap 1 understates itself — two of
  the five screens narrow their list *server-side*, so the lie pagination
  would introduce is already reachable today by clicking a control.**
  `TasksPage`'s `?status=` and `SpeciesPage`'s blooming-today are both
  answered by the API, so with either set the loaded list is not the
  organization's total and a bare "N tasks."/"N species." is false —
  measured, not reasoned: an org with 40 species and 3 in bloom would
  have been told it has 3. So those two name what they counted ("2 open
  tasks.", "1 species blooming today.") and offer no "of N" they do not
  have, while the three client-side screens (properties, members,
  activities) state a plain total. Fixing `SpeciesPage`'s gate also
  closed a live gap: ticking blooming-today narrowed the list *and
  removed the count*, which is exactly what `SightingsPage`'s own comment
  records avoiding.
  **Trap 2 was verified end to end rather than reasoned about** — a real
  property-scoped admin was invited, accepted, and their Members screen
  reads "1 member scoped to your properties." while the org has 2.
  **Trap 3 is a comment on the count**, not user copy: the exclusion of
  soft-deleted rows is correct and is written down so it isn't "fixed"
  into `all_objects`.
  **Two adjacent falsehoods fixed in the same pass, both D21's
  false-cause class and both on `TasksPage`:** it told anyone whose
  *filter* matched nothing "No tasks yet." — including an org with plenty
  of open tasks that had just selected Resolved — and it said the same
  thing after a *failed* load, directly under the error saying the list
  couldn't be read. The first now names the filter; the second is keyed on
  the data rather than on `!loading`, which is what the other list screens
  already did and this one didn't. Both are pinned by browser checks.
  **`countLabel` takes the list, not its length, and answers `null` when
  it isn't loaded** — the `data?.length ?? 0` every call site would
  otherwise reach for reports "0 properties" both mid-fetch and after a
  failed load, which is D47's lesson (empty ≠ absent) and D21's, in the
  one place they would be reintroduced by copy-paste.
  **Verified:** 32/32 checks in real Chromium at 390px against a live
  PostGIS stack, driving each state (singular, plural, zero, both
  server-side filters, the combination of search + server filter, the
  scoped admin, and a deliberately failed load), plus screenshots read
  rather than only asserted on.
  **Stated plainly: pinned by no test** — there is still no frontend test
  runner, so a regression here would be caught by nothing.
  **D50b's Q1/Q2/Q3 deliberately untouched**, and D50a does not pre-empt
  them: it adds no screen and no API surface, and the photo half remains
  unobtainable by construction.

- **F1 — click a photo to see it larger. User-requested (feedback 15,
  2026-09-17), found/measured 2026-09-18 PM check-in, ✅ BUILT
  2026-09-18 (programmer session).** Shipped as a shared
  `components/PhotoLightbox.tsx` — one module holding both the thumbnail
  trigger and the overlay, used by *both* grids (`PhotoUploader`,
  `PublicPhotoGrid`), on the D6/D34 "don't copy the decision into two
  sites" precedent. Native `<dialog>` + `showModal()` rather than a
  hand-rolled div, so the browser owns Escape, the focus trap, focus
  restoration to the trigger, and **top-layer rendering** — the last one
  is not theoretical, since a `position: fixed` feedback widget sits on
  every authenticated screen and a 2026-09-02 session already had to fix
  that widget clipping a primary action. Both sub-questions the check-in
  said to state rather than guess were answered as it recommended:
  next/previous across the record's photos (clamped at both ends rather
  than wrapping, since the "2 of 3" counter makes a disabled arrow
  clearer than a silent loop), and Escape plus a focus trap. **D32 was
  not touched** — no derivative, no migration, no new endpoint.
  **The defect found while building, which is the part worth keeping.**
  Clicking Next to the last photo *disables* Next; a disabled `<button>`
  cannot hold focus, so the browser drops focus to `<body>`, which is
  **outside** the dialog — a keydown there never bubbles through it, so
  the arrow keys silently died and the only way back was to Tab. Escape
  kept working throughout, which is exactly what makes it easy to miss:
  that one is the browser's, handled on the dialog itself. Fixed twice
  over — arrow keys bound on the *document* (safe because a modal dialog
  makes everything else inert) and focus handed back to whichever arrow
  is still live.
  **Measured rather than asserted, and it corrected this run's own
  claim** (the D38/D40 rule). Each fix was built alone: the document
  listener alone leaves focus stranded (**3 red**); the focus fix alone
  passes **all 40**, including every key test, because restoring focus
  also restores the bubbling path. So **nothing catches the document
  listener on its own**, and two guesses at a case that would — clicking
  the photo, clicking the control bar — both came back green, because
  Chromium keeps focus inside a modal when you click a non-focusable
  child. It stays anyway for a reason specific to this repo: there is
  **no frontend test runner**, so those 3 red tests are a one-off
  measurement and not a standing guard, and without it the arrow keys
  work only as a side effect of the focus effect — the exact coupling
  that produced the bug.
  **Verified** with 55 assertions in real Chromium against a live stack
  (PostGIS 3.4.2 + PostgreSQL 16), seeded through the real API: 40 at
  390px on the authenticated and public paths, plus 15 covering a
  **portrait** photo (what a phone camera actually produces — renders
  900×1600 at its own ratio with the control bar clear of it), the
  single-photo path (no counter, no arrows, `alt="Photo"`), 320px, and
  1280px. The backdrop was confirmed to cover the whole viewport by
  comparing rendered pixels before and after opening — uniform 0.12×
  brightness at the top bar *and* the bottom nav — rather than by eye.
  **Deliberately not swept in:** photo captions/alt text (there is no
  field to populate them from — recorded as a new limitation instead)
  and showing `captured_at`, which the API already delivers and nothing
  displays.
  **⚠️ Corrected 2026-09-22: `captured_at` is a dead field, not an
  undisplayed one.** "Delivered and nothing renders it" frames this as a
  display gap. Measured — **zero** assignments anywhere in the backend
  outside the model declaration — so it is `NULL` on every photo on every
  deployment, and rendering it would render nothing, forever. The
  "configured and does nothing" family (D40's `NUM_PROXIES`, D43's
  `AnonRateThrottle`, D45's mail variables, D46's unrun validator, D49's
  `clearsessions`), this time in a *field*. Populating it means reading
  EXIF at upload time, which puts photo bytes through Pillow — the
  decompression surface D17 established does **not** currently extend to
  photos. That is a real decision with a security dimension, so it is the
  owner's, and it is a prerequisite rather than a nice-to-have: there is
  nothing to display until something writes it. Original finding follows. The report is accurate
  and was verified rather than recorded at face value: `photo.url` is
  referenced in exactly two places — `PhotoUploader.tsx:58` and
  `PublicPhotoGrid.tsx:27` — each a bare `<img src>` inside an **84×84**
  `.photo-thumb`, and a sweep for `lightbox`/`<dialog>`/`modal`/
  `showModal` across all of `frontend/src` returns **zero**. Neither
  `<img>` is wrapped in an anchor and neither has a click handler, so
  there is no route to the full image from inside the app at all.
  **The measurement that decides how to rank this, taken against the
  photo the feedback actually names** (activity 5, property 1, org 1 —
  reached anonymously, read-only, nothing written): the stored JPEG is
  **1,899,250 B**, and `.photo-thumb img` is `object-fit: cover` at
  84×84. So the app **already downloads all 1.9 MB to paint a 252×252
  centre crop** at DPR 3 — D32 measured that box as needing ~16,885 B,
  making this **~112× the bytes required** — and then offers no way to
  see the image it just downloaded. **Therefore a lightbox costs zero
  additional image bytes**: it re-requests the same URL, which is
  already in cache, and D33's validator is live on it — measured on the
  deployment, `etag:
  "3c292bf5593d6279d90f73aeecd8734f23dca3a644afe7b5f75addb80a373bc0"`,
  `cache-control: private, no-cache`, and a conditional re-request
  returns **304 with 0 bytes**. The most-requested thing in the app is
  also the cheapest. **`object-fit: cover` is the half that makes it
  more than a nicety:** the thumbnail is *cropped*, not merely shrunk,
  so on a landscape photo of a restoration site most of the frame is
  not visible anywhere in Habitat.
  **Why this does not need D32's answer, which is the triage point:**
  D32's fork is derive-a-thumbnail-and-keep vs. downscale-on-upload —
  a decision about *what is stored*. F1 changes only what is
  *displayed*, adds no derivative, needs no migration and no new
  endpoint, and D6 deliberately declined `Content-Disposition:
  attachment` so the bytes are already anonymously reachable — a
  lightbox exposes nothing new on either the authenticated or the public
  path. **D32 stays open and untouched; its fork is not a blocker for
  this.** Whichever way D32 is eventually answered, the lightbox is the
  surface that displays the result.
  **Two sub-questions a build session should state rather than guess,
  neither a fork:** whether the overlay supports next/previous across a
  record's photos (recommendation: yes, the grid already has the list),
  and keyboard/focus handling — Escape to close and a focus trap, since
  this is the app's first overlay of any kind and there is no precedent
  in `index.css` to copy. **One thing it will encounter:** both grids
  render `alt=""`, which is correct for decoration and wrong for
  content; there is no caption field to populate it from, so improving
  it is its own (small) question, deliberately not queued here.
- **D39 (found 2026-09-16 (4) PM check-in; D39a BUILT 2026-09-16 (5);
  D39b's Q1/Q2/Q3 still the owner's) — the public/private filter is built end to end,
  from the database column to a typed client parameter, and the two
  screens whose job is finding records pass it nothing.** The queue's
  framing was "there is no inventory anywhere," which is true and
  understates it: the capability isn't missing, it's finished and unused.
  `filter_is_public` (`org_scoping.py:316`) implements
  `?is_public=true|false`; both viewsets call it; both serializers carry
  `is_public`, so it is **delivered on every row**; and
  `api.activities.list(propertyId?, filter)` takes a typed
  `ListFilter.isPublic`. `ActivitiesPage`/`SightingsPage` call
  `api.activities.list()` with no argument, render the flag **zero**
  times, and omit it from the search haystack — `grep -n "public"` over
  both files returns nothing. **D28's "delivered, never displayed" (as
  D38 found for attribution), one layer further along**, so the fix is a
  badge plus an existing parameter, not a feature. Everything that *does*
  mark the flag marks the exception — a "Private" badge
  (`PropertiesPage:81`, `PropertyMapPage:533`) or "(hidden)" for a page —
  so **public, the default on all four models, is the unmarked state**,
  and only on the per-property screen. Four verified absences alongside:
  **no count of anything** (`Count`/`aggregate`/`annotate` appear zero
  times in the backend outside migrations and tests); **no publish
  timestamp** anywhere, so "what did we publish, and when" is
  unanswerable from the data even in principle; **nothing addresses
  crawlers** (no `robots.txt` tracked, no `frontend/public/` directory at
  all, no `X-Robots-Tag`, no sitemap — and the live `/robots.txt` returns
  **200 with the SPA's `index.html`**, the D23 fallback trap, which a
  crawler reads as no restrictions); and **the public site can't be the
  inventory** — from outside because the 404-not-403 stance (deliberate
  and correct) makes private indistinguishable from absent, and from
  inside because of the compounding case below. **The sharpest half:** a
  record on a *private* property keeps `is_public=True` and is merely
  invisible — verified that **no cascade** writes a record's flag when a
  property's changes — so the public site shows what *is* published and
  never what *would* publish, and one checkbox republishes all of it at
  once with no count, review or confirmation. **It also raises D29:**
  `ActivityFormPage` PATCHes every field from its opening snapshot,
  `is_public` among them, so the one flag controlling publication is
  among the fields a colleague's typo fix silently reverts. **Severity,
  honestly:** not a leak and not a security defect — every filter is
  correct, D3's retraction and D33's revalidation both hold; live
  exposure measured read-only at 2 public properties, 6 public activities
  and 3 public sightings, nothing written. And the half that argues
  *down*: discoverability today is genuinely low (an unSSR'd SPA whose
  shell carries one static `<title>Habitat</title>`, no meta description,
  no inbound links), so this is **not** "it's already on Google" — it is
  that nobody has decided, nothing is written down, and the org cannot
  see or control it. **D39a, fork-free and needing no owner input:**
  badge public/private on both org-wide lists, add it to the filter
  control beside the existing status filter, and count it in the existing
  "Showing X of Y" hint — marking **both** states explicitly, since
  marking only the exception is right on a record's own page and wrong on
  the screen that exists to answer "what of ours is public?" **D39b, the
  owner's:** Q1 a real *Manage → Public exposure* screen covering the
  would-publish case D39a can't; Q2 whether Habitat should tell crawlers
  anything (a real fork — a land trust wants its preserve indexed, a
  homeowner almost certainly doesn't); Q3 whether flipping a property
  public should name a number, *"Publish this property? 14 activities and
  9 sightings become visible to anyone"* — **PM recommendation yes**, it
  is the cheapest thing that closes the compounding case and D34 already
  proved the shape. Full detail, including the clean-audit list and the
  quick-log near-miss, in `build-questions.md` (2026-09-16 (4)).
  **BUILT 2026-09-16 (5), and the build changed the spec in one
  load-bearing place.** A two-state Public/Private badge — what "badge
  public/private on every row" literally asks for — **would have been a
  new false claim**, because it marks a record "Public" that the
  two-condition rule does not publish. So the shipped badge has four
  states, not two: **Public**, **Private** (the record's own flag is
  off), **Property private** (flagged public, property isn't — the
  compounding case, visible per row), and **Not public** (a
  property-less sighting, which has no public route at all since the
  public site serves sightings only per property). The check-in assigned
  the would-publish case to D39b's Q1 as something D39a "can't cover";
  it is in fact coverable per row and in a count, because both pages
  already fetch the property list for their own `propertyName()` — so
  Q1's remaining value is a single org-wide screen spanning properties
  and pages too, not the record-level view. **The typed `isPublic`
  parameter was deliberately not used:** a server-side filter collapses
  the denominator (`6 of 9` becomes `6 of 6`), and the denominator is the
  answer this screen exists to give; it would also make the map on
  `SightingsPage` and the "All N sightings are plotted" line disagree
  with each other. Client-side also keeps it the same mechanism as the
  status filter beside it. Shipped: `frontend/src/utils/publicVisibility.ts`
  (the rule, the four states, the wording, and *unknown* as a real answer
  — the property list resolves after the record list, and guessing it
  renders a wrong badge), a **Visibility** select on both pages, an
  exposure line (*"1 of 4 activities are on the public site."*) and a
  separate would-publish line naming a number (D34's shape applied to
  publication). `is_public` is deliberately **not** in the search
  haystack — a note containing the word "public" would then read as a
  visibility hit, and the select can't produce a false positive. **No
  backend change, no migration**; backend suite unmoved at 220/220.
  **Found and fixed while building, pre-existing:** `SightingsPage`
  renders a property-less sighting as a bare `<div>`, so it never got
  `.card__link`'s flex-column layout and ran its title and detail
  together on one line — verified pre-existing by hiding badges and
  re-reading the row, and fixed with a shared `.card__stack`.
  `DashboardPage`'s own property-less branch is deliberately inline (it
  carries an explicit space and dash) and was left alone.
- **D38 (found 2026-09-16 (2) PM check-in; D38a BUILT 2026-09-16 (3)
  programmer session — D38b's Q1/Q2/Q3 still open) — the app records who
  created, edited and linked every record, on eight fields, and showed a
  person exactly one of them: the one about its own bug reports.** Habitat does
  not lack attribution *data*. It writes it on every relevant call site
  across six models and then drops it one layer before anyone could use
  it. Five fields are **never delivered** (absent from the serializer):
  `Activity.created_by`, `Activity.updated_by`, `Sighting.created_by`,
  `Page.created_by`, `SightingActivityLink.linked_by`. Two are
  **delivered and never displayed** — `Task.created_by_email` and
  `Invitation.invited_by_email` are declared in the frontend's own
  `src/api/types.ts` and appear in **zero** components. One works:
  `Feedback.submitted_by_email`, rendered in the org admin's Feedback
  section. That is D28's "not displayed vs. never delivered" distinction
  with **both halves in one feature**, the first time this project has
  found them together.

  **The sharpest line is a matched pair split one line apart, twice.**
  `ActivitySerializer.Meta.fields` carries `created_at` and `updated_at`
  and neither `created_by` nor `updated_by`;
  `SightingActivityLinkSerializer` carries `linked_at` and not
  `linked_by`. **The timestamp travels, the person doesn't.**
  `Activity.updated_by` is the only "who last touched this" field in the
  whole application, is written on every PATCH, and has never left the
  database. Confirmed live and read-only against the deployed host's
  anonymous public activities payload — both timestamps present, neither
  attribution field; nothing was written to the live instance.

  **Severity, honestly: not a security defect and not a leak** — it errs
  conservative, which is the right instinct (see the trap below). Whether
  any org actually has a second editor can't be determined from here (the
  D6/D28 no-database-access limit). What earns it a record is what it
  composes with: **D29** (the activity form PATCHes every field from the
  snapshot it opened with, so a typo fix silently reverts a colleague's
  status change, both dates, the public flag and a redrawn boundary),
  **D34** (deletes outside `Property` are immediate and cascading) and
  **D35** (nothing is backed up). So the app silently overwrites or
  destroys a colleague's work, **has recorded exactly who did it**, and
  discards that at the serializer.

  **The trap, and it is D8 through a different door:** the obvious
  two-line fix publishes a member's email to the open internet.
  `apps/public_site/views.py:249,265` serve `ActivitySerializer` and
  `SightingSerializer` to `AllowAny`, so adding `created_by_email` to
  either field list puts a real person's address on every public activity
  and sighting — and it is **invisible in the diff**, since the change is
  in `apps/activities/` and the consequence lands in `apps/public_site/`.
  D27/D28's shape: the invariant is a property of each *response*, not of
  the model. So the fix must be **opt-in for the authenticated path**, not
  a strip in `public_site` — a strip is an opt-out that the next public
  endpoint inherits.

  **Two sub-questions answered in advance rather than left to be found.**
  "Should a viewer see who edited?" needs no owner call: any member can
  already enumerate every member's email via `GET /api/org/members/`
  (`MembershipViewSet.list` carries no `ensure_role`, unlike `create` and
  `partial_update` beside it — audited and **intentional**, deliberately
  not queued). And email-vs-name needs no call either: `invited_by_email`
  and `submitted_by_email` are the in-repo precedent.

  **The cheapest single improvement in the cluster:** `Notification` has
  no actor field at all, and its one message is passive — *"You were
  assigned the task X."* — built at a call site holding
  `self.request.user` at that moment.

  **Split.** The **fork-free half (D38a)** surfaces the attribution that
  already exists, on the authenticated path only, in the opt-in shape
  above: creator and last editor on an activity/sighting, the creator on a
  task, and the actor in the assignment notification. No migration, no
  owner input. The **owner's half (D38b)** is three questions: **Q1** — is
  "created by X, last edited by Y" enough, or does Habitat want a real
  **change history** (what changed, not just who last touched it)? That is
  the actual audit-log question, and it is what D29 would need, since
  knowing who reverted your boundary doesn't tell you what it was.
  **Q2** — should photos record an uploader? (`ActivityPhoto`/
  `SightingPhoto` have no attribution at all, and photos are what D32
  measured as unrederivable and D34's prompt destroys; a migration, so a
  separate item.) **Q3** — should any of this ever be public, e.g. a land
  trust crediting a volunteer? Today's "no" is an accident rather than a
  decision. PM recommendation: D38a now, Q1 before anything larger is
  designed, Q2 alongside whatever touches photos next, Q3 left alone until
  asked for. Full working, the eight-field table and the clean-audit
  inventory in `build-questions.md` (2026-09-16 (2)).

  **Method note, because it changed the answer:** the inherited framing
  was "there is no audit log anywhere," which points at a large build. The
  measured answer is that the data is already being written — so the first
  fix is five serializer fields and a message string. **Check whether the
  data is already there before designing the feature.**

  **✅ D38a BUILT 2026-09-16 (3).** The opt-in shape was taken:
  attribution lives on three new `…WithAttribution` serializer subclasses
  (`Activity`, `Sighting`, `SightingActivityLink`) that only the
  authenticated, org-scoped views name, with the rule and the three ways
  to get it wrong pinned in a new `apps/accounts/attribution.py`. The
  observable that makes it opt-in rather than opt-out:
  **`apps/public_site/views.py` is unmodified** by the fix. The frontend
  types carry the same split — `PublicActivity`/`PublicSighting` build on
  the base field interfaces, so rendering a member's email on a public
  page is a **compile error** (proven with a throwaway probe, not
  asserted). Surfaced on both edit forms, each link row, the task row, and
  the assignment notification, which now names who assigned it.

  **All three wrong fixes were built and measured**, and the result
  corrects the "disjoint tests" framing the check-in and the first draft
  of the tests both used — they are caught by a *nested ladder*, and what
  matters is which test is the only thing stopping each:

  | wrong fix | email-search | key-set | base-class | measured |
  |---|---|---|---|---|
  | 1 — fields on the base serializer | FAIL | FAIL | FAIL | 5 of 126 fail |
  | 2 — strip in `public_site` | pass | pass | **FAIL** | **2 of 126 fail** |
  | 3 — context flag emitting nulls | pass | **FAIL** | FAIL | 3 of 126 fail |

  **Fix 2 is the one to dwell on: it fails nothing that reads a
  response.** Every authenticated outcome test, both email searches, the
  key-set test and the entire `apps.public_site` suite pass against it,
  because its public response body is byte-identical to the real fix's.
  Only a test that asks the *class* rather than the response catches it —
  D33's lesson (when the consequence happens somewhere you have no
  instrument, move the assertion to something you can see) applied to a
  consequence that lands in code that does not exist yet. Fix 1 was also
  confirmed to be a real leak, not a theoretical one: the anonymous
  payload came back carrying `"created_by_email":"author@example.com"`.

  **A D27 instance found while building, and fixed in the same pass.**
  Both link-list querysets `select_related("activity__property")` to serve
  `activity_property_name`, with no `defer_theme_image` — so every link on
  a themed property was loading that property's banner bytes again. Missed
  by the 2026-09-13 sweep, which is **D28's point exactly**: the invariant
  is a property of each query, so it is not self-maintaining and every new
  join has to be checked. Found only because the `linked_by` join was
  being added to those same two lines.

  **Measured, not assumed:** the activity list costs **8 queries with the
  attribution joins and 32 without** (12 rows × 2 fields = 24 extra
  lookups), on an endpoint D30/D31 established is org-wide and
  unpaginated. The joins are safe only because `User` carries no
  `BinaryField` — pinned by a test rather than left as reasoning, so a
  future blob on `User` goes red here instead of in production.

  **Still open: D38b's Q1 (real change history), Q2 (photo uploaders) and
  Q3 (public credit).** Also deliberately untouched: `Page.created_by`,
  which is D38's fifth never-delivered field but has no UI surface that
  would show it, and the eight models with no attribution column at all.

- **D34 (found 2026-09-15 PM check-in) — the one delete a user can undo
  is the only one that explains itself; the two that cascade to photos
  and can never be undone get four words each.** `deleted_at` exists on
  **exactly one model** (`Property`); every other delete is a plain
  `ModelViewSet.destroy`. That much `limitations.md` already records.
  What nobody had lined up is the **wording**: deleting a property warns
  *"…An admin can restore it from Manage → Recently deleted within 30
  days, after which it's removed for good."*, while deleting an activity
  asks **"Delete this activity?"** and a sighting **"Delete this
  sighting?"** — neither containing the word "permanent".

  **The cascade is what lifts it above a wording nit.** `ActivityPhoto`
  and `SightingPhoto` are both `on_delete=CASCADE`, so those four words
  destroy every photo attached — and D32 established that photos are the
  bulk of the database *and the only thing in it that cannot be
  re-derived*. The least informative prompt sits on the most destructive
  act in the app.

  **The severity framing inverts the usual one.** Delete is `ADMIN`-gated,
  which is a real protection for a land trust and **protects Habitat's
  founding user not at all** — the author doing restoration on their own
  property (`vision.md`) *is* the admin. The gate is strongest where the
  data is least at risk.

  **The manual is accurate and needs no correction — that is the
  finding's shape** (the D16/D19/D20/D33 case). `limitations.md:156-161`
  says these deletes are "immediate and permanent" and then closes:
  *"The one thing standing between you and an accidental permanent delete
  is the confirm prompt, so read it."* **The manual credits the prompt as
  the safeguard, and for an activity or sighting the prompt doesn't
  mention permanence.** The honesty lens one layer up from D19: not a
  caption that denies what it does, but a documented safeguard that
  under-delivers on the job the documentation assigns it.

  **Split.** The **fork-free half** is making the two dialogs say what
  they do — additive, no migration, no API change, and it makes an
  existing manual sentence true. **The owner's half** is whether
  activities and sightings get soft delete at all, which is the item
  re-deferred 2026-08-28 as genuinely ambiguous (which models, retention,
  who restores, cascade). The wording fix must not be mistaken for it.

  **✅ The wording half was BUILT 2026-09-15** (scheduled programmer
  session). The owner's soft-delete half is untouched and still open.

  **What shipped, and the one design call worth knowing.** A shared
  `frontend/src/utils/deleteConfirm.ts#confirmDeleteMessage` rather than
  two strings at two call sites — the original D6 defect was one
  content-type check copy-pasted into four upload sites and wrong in all
  four, and this is that shape one layer up: the two dialogs were four
  words each *precisely because* nobody had read them side by side.

  **The dialog names a photo count, not "and any attached photos".** That
  is the whole value of the fix: a number is what makes someone stop,
  where a blanket clause reads as boilerplate when there are none and
  badly understates it when there are twelve. So:
  *"Delete this activity? Its 3 photos are deleted too. This can't be
  undone."*, and with no photos simply *"Delete this activity? This can't
  be undone."*

  **Where the count comes from is the load-bearing decision.** It is
  fetched **on click**, from the `…/photos/` endpoint that already
  exists — deliberately **not** added to the list serializer. Putting a
  `Count` aggregate on `ActivitySerializer`/`SightingSerializer` would
  land it on exactly the unfiltered org-wide endpoints D30 and D31
  measured as the app's volume problem, paying a join-and-group-by on
  every row to populate a dialog nobody has opened. One request at the
  moment of deleting costs nothing a user can perceive.

  **The `null` path is not an afterthought.** If the count lookup fails
  the dialog still warns, with the hedged wording (*"Any photos attached
  to it are deleted too"*) — a failed count must never block the delete
  **or make it look safe**. Exercised in a browser by aborting the
  request, not reasoned about.

  **Verified three ways.** All four branches of the builder (0 / 1 / n /
  null) driven directly — the singular case matters, because *"Its 1
  photos"* is exactly the slip D30 shipped and only caught by looking.
  Then the cascade itself, through the real HTTP endpoints: the dialog
  reads 3 and 1, **exactly 3 and 1 photo rows are destroyed**, and the
  record then 404s — so the number the prompt names is the number that
  actually dies. Then real Chromium at 390px against a live stack: all
  three dialogs verbatim, including that the zero-photo sighting prompt
  **does not mention photos at all**.

  **The manual needed no correction and that is still the finding's
  shape** — `limitations.md` already credited the confirm prompt as the
  safeguard, so this makes an existing sentence true rather than adding a
  claim. Its bullets now also record what the prompt says, and that a
  species or task delete is *still* only a bare "Delete … ?".

  **Not pinned by a test** — there is still no frontend test runner, so a
  regression in this wording would be caught by nothing. Stated plainly
  rather than left to be inferred from a green backend suite.

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

- **D24 — a brand-new account cannot log a sighting from quick log, the
  flow built for logging sightings in the field (found 2026-09-12 (3),
  ✅ BUILT 2026-09-12 (4)).** `QuickLogPage`'s detail step requires a species
  (`Sighting.species` is a `ForeignKey` with no `null=True`/`blank=True`,
  and the page refuses client-side with *"Pick a species for this
  sighting."*), and its picker is **read-only against the org's list** —
  which a new org's is empty.

  **The asymmetry is exact.** Two `post_save` receivers in
  `apps/activities/signals.py` seed every new Organization with **3
  workflow states** and **8 activity types**. **Nothing seeds species** —
  no signal, no data migration (both checked). So quick log's **activity**
  path works on day one and its **sighting** path cannot complete at all.
  `QuickLogPage` lines 127-137 even default the two *seeded* pickers and
  leave the *unseeded* one blank; nobody asked what an empty unseeded list
  does.

  **The empty species list is not the defect** — it is a decided owner
  stance (2026-08-28: *"Starter species list … stays empty, no starter
  list"*). The untraced consequence is that the one create flow needing a
  species has no way to make one. **So the fix must NOT be a starter list**
  — that would reverse an owner decision (the D19 guardrail).

  **The fix already exists at the sibling site.** Of the two
  sighting-creation callers, `SightingFormPage` carries **"Or add a new
  species"** (free text → `api.species.create` → use it,
  `resolveSpeciesId`) and words its refusal honestly: *"Pick a species, or
  type a new one."* Quick log has neither. Its message is therefore an
  instruction the screen gives no way to follow — the **D22 defect class
  verbatim**. It lands harder than a wording bug because leaving to add a
  species **discards the capture** (no draft persistence, by decision), and
  the trigger is the simplest first action in the app: one tap.

  Confirmed live read-only against the Vite-served modules, with the
  549-byte SPA-fallback negative control re-run; nothing was written to the
  live instance. **Build-ready, no owner input needed** — recommendation is
  create inline rather than link out, since following a link is what costs
  the capture. Full detail, including the inherited duplicate-name wrinkle,
  in `build-questions.md` (2026-09-12 (3)).

  **Built** as the recommendation said — inline, not a link out. The
  resolve-or-create step is now a shared `utils/species.ts#resolveSpeciesId`
  used by **both** sighting-creation sites rather than copied into the
  second one: a sighting's species is a required FK, so what that function
  does is the difference between logging what you just saw and a dead end,
  and the two entry points must not drift on it. The refusal now reads
  *"Pick a species, or type a new one."* — naming what the screen actually
  offers. **No starter list was added**, per the guardrail.

  Verified against a live stack in real Chromium at 390px, on the defect's
  own scenario: a brand-new account whose species list is confirmed `[]`
  places one point, types a name, and the sighting **and** the species are
  both created. 13/13 checks (the 14th "failure" was my own Playwright
  route pattern missing `tile.openstreetmap.org` — every failing request
  was a basemap tile).

  **Two things came from looking at the screen rather than the
  assertions**, the third and fourth times that has been what caught
  something here. (1) The longer placeholder I gave the picker
  **clipped** at 390px (*"…or add new be"*) — shortened to *"Search, or
  add new below…"* at both sites and re-measured at 390px and 320px. (2) A
  320px "check" reported a 356px input, which is impossible — the `sed`
  setting the viewport hadn't matched, so it had re-measured 390px. Same
  family as the 2026-09-12 "assertion that passed while testing the wrong
  page": **an impossible number is the tell that the harness, not the app,
  is what you measured.**

- **D25 — the Quick log button is the app's only ungated create control
  (found 2026-09-12 (3), ✅ BUILT 2026-09-12 (4)).** `DashboardPage.tsx:131` renders
  it behind `{!nothingYet && …}` with no role check; the file imports
  `isPropertyScoped` and **not `roleAtLeast`**. Nine other files compute an
  editor gate — including `PropertyMapPage`, whose per-property **+
  Sighting**/**+ Activity** FABs are gated at line 292 — so a **viewer**
  sees the button, walks the capture, fills the form, and is refused by the
  backend on save. Confirmed live with a control (`DashboardPage`: 0
  `roleAtLeast`; `PropertyMapPage`: 3). **Much weaker than D24:** the
  backend refuses correctly, so nothing is created, nothing leaks and there
  is no escalation — it is the "a control that looks available and isn't"
  class (D13/D21), and viewer-only, where D24 hits every new account.
  Build-ready: `roleAtLeast(role, "editor")`, matching the nine siblings.

  **Built**, one line plus the import. Verified with the control that
  matters: a real invited **viewer** session, on an org that **has** a
  property, does not see the button — so it is hidden by the *role* gate
  and not by the pre-existing empty-state gate, which is the only way this
  test could otherwise pass for the wrong reason — while the admin on the
  same data still sees it.

- **D26 — adding a species you already have was an unhandled 500 (found
  *and* built 2026-09-12 (4), while building D24).** `Species.Meta` carries
  `UniqueConstraint(["organization", "common_name"])`, but `organization`
  is supplied by the viewset and never by the request body, so DRF never
  builds its auto-generated unique-together validator, and nothing
  converted the resulting `IntegrityError` — it subclasses neither
  `APIException` nor Django's `ValidationError`, DRF's `exception_handler`
  returns `None` for it, and there is no custom `EXCEPTION_HANDLER`.
  **Exactly D13's shape, in the same app**, and reachable from the ordinary
  Add form on the species page by typing a name twice.

  **Measured, not inferred:** `POST {"common_name": "Crabgrass"}` twice
  against a live backend returned **201 then 500**. It was found because
  D24 routes a **second** caller into that path — from a mobile capture
  flow with no draft persistence, where a 500 costs the user the point they
  just placed. Shipping D24 without this would have widened a live 500.

  **Fixed in two layers, because they are not the same guard.** A
  `validate_common_name` gives the good message; an `IntegrityError` →
  400 in `perform_create`/`perform_update` covers the window between the
  check and the write (a stale client list, two tabs, two members). The
  validator alone would be a nicer message over an unchanged failure mode.

  **The check matches exactly where its two siblings match `__iexact`, and
  that is deliberate.** Mirroring them would *also* start rejecting
  "crabgrass" beside "Crabgrass" — settling the name-uniqueness casing
  question this file has deliberately left open since 2026-09-10 ("needs a
  `Lower()` constraint **and** a decision about existing rows — a product
  call") as a side effect of a 500 fix. Verified the case variant still
  returns 201.

- **The client is deliberately stricter than the server here, and it is
  worth knowing which is which.** `resolveSpeciesId` reuses an existing
  name **case-insensitively**, so the logging forms never fork a list into
  "Crabgrass"/"crabgrass" — there is no merge tool to undo that. The API
  still accepts the pair from the species page. That asymmetry is a UI
  convenience, **not** an answer to the open casing question, and is
  recorded in `limitations.md` rather than left to be discovered.

**Two more user-feedback items arrived 2026-09-11** (ids 13 and 14, the
first non-empty pull since 2026-09-03) and both were built the same run,
one of them only in part:

- **Activities nav icon (feedback id 13) — ✅ BUILT 2026-09-11.**
  *"Activities icon in the menu should be something related to activity,
  not a plant."* It was 🌾, which named the *subject* of the work rather
  than the work, and doubled up with Sightings 🦋 as a second nature glyph
  on the two adjacent entries most easily confused (both are org-wide
  record lists). Now 🛠️. 🪏 would have been more literal but is Unicode 16
  (2024) with patchy device coverage. Measured rather than eyeballed at
  390/375/320px: no nav overflow, no box overlap, no clipped label at any
  of them. The bar is visually dense at 320px — seven labels packed
  edge to edge — but that is pre-existing and unchanged by swapping a
  glyph, since label widths didn't move. **Recorded, not queued:** whether
  the nav should abbreviate or go icon-only below some breakpoint is a
  design call, not a defect.

- **Seeing one species across every property (feedback id 14) — fork-free
  half ✅ BUILT 2026-09-11; the grouping question is open.** *"Would it be
  possible to link several sightings together? For example, I want to see
  all crabgrass sightings, as points. Not sure how that would work, maybe
  a species filter or some sort of super sighting?"*

  **Reading it precisely is what split it.** A species filter already
  existed — the Sightings page's search box has matched common and
  scientific name since 2026-09-03 — so the missing piece was never
  filtering. It was that **sightings could only be seen as points inside a
  single property**: `PropertyMapPage` is the only sightings map in the
  app, so one species growing across three properties had nowhere it could
  be viewed at once. That is the literal request ("as points"), it needs
  no new concept, and it is what was built: the Sightings page is now a
  `.page--map` whose map plots `filtered`, not `all`. Typing "crabgrass"
  is what makes it "all crabgrass sightings, as points" — the existing
  search box became the map's control rather than gaining a second one.
  No new API surface; it reuses `MapCanvas`, `ensureCircleLayer` and the
  same `#2f5fc9` a sighting already has on its property's map, so a point
  means the same thing on both screens.

  Decisions made while building, recorded rather than assumed: the map is
  **hidden entirely when the org has no sightings** (a 50vh empty map
  would crowd out the "log your first one" prompt) and on a failed load
  (a map showing nothing would imply the org genuinely has none — the
  exact misattribution D21 fixed elsewhere). A search matching nothing
  **keeps** the map rather than tearing it down mid-keystroke.

  **Still open — the "super sighting" half, and it is a real data-model
  question, not a UI one:** what a group *is* (user-made, or derived from
  a species?), whether a sighting can be in more than one, what happens to
  a group when a member sighting is deleted or its species changes, and
  whether groups reach the public site. Nothing built here forecloses any
  of it. A cheaper intermediate the owner may prefer: turn the free-text
  search into a **structured species picker**, which gets "all crabgrass"
  exactly right without inventing a record type — worth asking before
  anyone designs grouping.

  **Sibling deliberately not built:** the Activities page has no
  equivalent org-wide map. Activities are drawn polygons, not points, so
  it needs status styling and a legend, and nobody asked for it — this
  repo's "four filters, not two" sweep rule is about a *defect* appearing
  in N places, not about widening a feature request. Recorded in
  `limitations.md`.

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
  - ⚠️ **Sharpened 2026-09-25 (PM check-in), per D22's un-parking
    discipline: the stated parking reason has changed, though it has not
    yet been met.** *"Revisit if anyone actually loses work to it"*
    framed the loss as caused by **backing out** — a deliberate user
    action, which is also how `dashboard.md` and `limitations.md`
    correctly describe it. **D62 adds a path where losing the capture is
    the only available recovery**, not a choice: once the species step
    wedges, nothing clears it but a reload, and the reload is what
    destroys the dropped point and the typed notes. Eighty-one feedback
    pulls have still produced no report of anyone losing work, so this is
    **not** a claim the condition is satisfied — it is that the condition
    is no longer only about back-navigation. Filed as a sharpening, not a
    duplicate.
  - ⚠️ **Retracted 2026-09-26 (programmer session): the path that made
    losing the capture *involuntary* is closed.** D62a and D62b both
    shipped, and a browser run confirms the wedge end to end — the first
    save fails (the message a user actually reads is D21's house string,
    *"Something went wrong."*), pressing **Save** again succeeds, and
    exactly one species row exists afterwards. So this bullet is back to
    its original scope: losing a capture again requires **backing out**,
    a deliberate action, which is what the manual has always said. The
    parking reason stands as first written, and the item stays parked.
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

**Refilled 2026-09-05 (PM check-in), with one item — and emptied again the
same day.** **D4's additive half is built** (see "Tech / infrastructure"
above): `.github/workflows/tests.yml` now runs the backend suite against
real PostGIS and typechecks/builds the frontend, on every push to `main`
and every pull request. As with D3, a build session could take it without
asking because it needs no secrets and no hosting decision. Its one
carved-out sub-question — whether `build-and-push` should gate on it —
was **not** decided by that session and remains the owner's, the same way
B2 was carved out of the 2026-09-03 authorization.

**So the queue is once again empty of authorized work**, which is the
honest state to report rather than manufacturing work to fill a run. What
remains is unchanged and still blocked on the same things: **B2 is now
seven days unanswered and the contextual menu six**, both re-raised
compactly rather than re-argued; whether CI should gate the image publish
is a new one-line yes/no; due dates on tasks and the org switcher are
product calls; a real cron for the purge waits on the hosting model;
server-side search/pagination is recommended *not yet*; quick-log draft
persistence waits on someone actually losing work to it.

**Still empty after 2026-09-05 (3) (PM check-in), and the one new finding
does not refill it.** That run found D5 — the live instance is served by
Django's `runserver` and Vite's dev server, with no production image in
the repo to replace them (see "Tech / infrastructure" above) — but
deliberately recorded it as a **question, not a build-ready item**, the
opposite call from D3 and D4. Those two needed no secrets and no hosting
decision; a production image needs a static-server choice, a WSGI/ASGI
choice, a static-files strategy and a call on whether the dev images stay
for local `docker-compose`, all of which sit downstream of the undecided
hosting model. So the queue still holds **nothing a build session may take
on its own**, and the blockers are unchanged: **B2 is now eight days
unanswered and the contextual menu seven**; the publish gate, and now Q1
(is this host meant to be production-shaped?), are one-line yes/nos; the
rest are product calls, hosting-blocked, recommended *not yet*, or waiting
on someone actually being hurt. The Node 20 action-deprecation pass waits
on major-version bumps being available.

**Still empty after 2026-09-05 (4) (programmer run), which built the one
piece of D5 that carried no decision.** That run triaged this file and
`build-questions.md` in full and found, as the check-in before it
predicted, nothing authorized. Rather than stop there or manufacture
work, it took **D5's additive half** — `npm ci` from the committed
lockfile, and a `.dockerignore` for each build context so no `.env`
reaches an image layer — on exactly the reasoning that let D4's additive
half ship the day before: it needs no secrets, no hosting decision, and
changes no runtime behaviour. **D5's actual question is untouched.** No
production image was written, `docker-publish.yml` is unmodified, and the
two dev servers on the live host are still there; Q1 (is that host meant
to be production-shaped?) and Q2 (what shape should production images
take?) are still the owner's, and a build session answering them alone is
exactly what `CLAUDE.md`'s boldness carve-out forbids.
**So the queue is empty again**, with the blockers unchanged and one day
older: **B2 is now nine days unanswered and the contextual menu eight**;
the publish gate and Q1 are one-line yes/nos; due dates on tasks and the
org switcher are product calls; a real cron for the purge waits on the
hosting model; server-side search/pagination is recommended *not yet*;
quick-log draft persistence waits on someone actually losing work to it;
the Node 20 pass waits on major-version bumps being available.

**Refilled 2026-09-06 (PM check-in), then emptied again the same day.**
That run found **D6** — every image-upload endpoint accepted
`image/svg+xml` on the strength of a client-supplied header, and every
serving path echoed that header straight back, so a stored photo could be
executable script on the app's own origin. It was recorded as a **build
item, not a question** — the same call D3 and D4 got, and the opposite of
D5 — and **the 2026-09-06 programmer session built it**, answering the
one narrow sub-question explicitly (no `Content-Disposition`, and the
backfill check reduced to informational by the serving-side fix; see
"Tech / infrastructure" above).

**So the queue is once again empty of work a build session may take on
its own.** Every remaining item is blocked on the same things it was
before: B2 and the contextual menu need a yes/no; the publish gate and
D5's Q1 are one-line yes/nos; due dates on tasks and the org switcher are
product calls; a real cron for the purge waits on the hosting model;
server-side search/pagination is recommended *not yet*; quick-log draft
persistence waits on someone actually losing work to it; the Node 20 pass
waits on major-version bumps being available.

**Refilled and emptied again on 2026-09-06 (4), the same way — and this
is now the sixth run running.** That programmer session triaged this file
and `build-questions.md` in full, found (as the morning check-in
predicted) nothing it was authorized to build, and sourced its own item
rather than stopping: **D7**, the deployed site's cookies carrying no
`Secure` attribute (see "Tech / infrastructure" above). It fits the same
test D3, D4's additive half, D5's additive half and D6 all met — no
secret to provision, no hosting decision, no product fork in the fix, and
a defect verifiable against the running host. The three settings that
*would* have needed an owner call (`SECURE_HSTS_SECONDS`,
`SECURE_SSL_REDIRECT`, `TRUST_X_FORWARDED_PROTO`) were deliberately left
off by default and documented as the deployment's to make.

**The pattern is worth stating plainly because it has not changed:** five
consecutive programmer runs have each had to find their own work, and
each found a real defect by the same move — check a claim the docs or the
deployment make against what the code actually does. That the move keeps
working is a comment on how little of this app has been audited, not a
substitute for the queue being answered. **Three one-line answers (B2,
the contextual menu, the CI publish gate) would give the next run
something the owner actually chose.**

**A blocker was found this run that is not a queue item at all:** the dev
host `habitat.dev.cravenator.com` was **down for the entire session** —
its edge answered `503 upstream connect error … connection timeout` on
port 80 while port 443 reset the TLS handshake, across the 10:15 refresh
boundary and beyond (~20 minutes of continuous failure). **The owner
confirmed the cause live: a power outage** — not a deploy, image or
application fault, and unrelated to the same day's D6 commit. Recorded so
the next run knows it was already reported and diagnosed rather than
newly broken.

**A note on the day counts above, so the next run doesn't propagate
them:** the running tallies for B2 and the contextual menu drifted — they
were incremented once per check-in run rather than once per day, which is
why they read two → four → six → eight → nine across a span of days that
was actually much shorter. The verifiable anchors: **B2 was raised
2026-09-03** (feedback id 12) and **the contextual menu was parked
2026-09-03**. As of 2026-09-06 that is three days for both. This file
should quote the anchor dates from here on, not a tally.

**Re-confirmed empty 2026-09-06 (3), and the pattern is now the finding.**
That check-in ran the usual audit pass — take a claim the docs assert and
check it in the code — across four previously-unexamined areas and found
**no new defect**, the first check-in in six that hasn't produced one.
What it confirmed instead is recorded in `build-questions.md`'s
2026-09-06 (3) entry so none of it is re-derived: the public site's
authored-page paths *are* guarded against a soft-deleted property (and
the reason is that `Property.objects` is declared before `all_objects`,
which is what makes `_default_manager` the filtering one — reverse those
two lines and D3 silently reopens everywhere); `apps/notifications` has
no mark-read IDOR; tasks staying account-wide for a property-scoped
member matches the manual exactly; and the QR logo picker's `image/*`
is safe because an undecodable image becomes a 400, not a 500.

**The queue-state finding is that this is now five runs running.** Each
of the last four programmer sessions found nothing authorized here and
had to source its own additive item — D3, D4's additive half, D5's
additive half, D6. D6 was the last item carrying no decision, so that
source is exhausted: **a programmer run firing next would triage this
file correctly and find nothing it may build.** The three one-line
questions (B2, the contextual menu, the publish gate) are what would
change that.

**The dev host recovered.** `GET /` and `/api/auth/csrf/` both 200 on
2026-09-06 (3), and the host is confirmed to be running the D6 commit:
`GET /src/utils/images.ts` (a file that did not exist before `936a30c`)
returns the real module through Vite's dev server. That proves the
*frontend* half directly; the backend half has no unauthenticated
observable, and confirming it would mean uploading to the live instance,
which the check-in deliberately did not do.

**Still empty after 2026-09-07 (PM check-in) — and D8 does not refill
it.** That run confirmed the 2026-09-06 (4) programmer session's D7 fix
is **live on the host**, not merely merged: the CSRF `Set-Cookie` now
carries `Secure`, where yesterday it did not. HSTS remains absent, which
is correct — D7 left it as an owner call deliberately.

The run's audit pass found **D8** (see "Accounts, orgs, and permissions"
above): a blank account name at signup becomes `<email>'s land`, and the
public organization endpoints have no gate at all, so a user who
publishes nothing still has their email served unauthenticated. It is
recorded as a **question, not a build-ready item** — the same call D5 got
and the opposite of D3/D4/D6 — because the fix has a genuine fork (what
the new default should be, whether existing rows are backfilled given
that a rename leaves the old slug serving, and whether `Organization`
gains an `is_public` gate at all). A build session picking either side
unprompted is what `CLAUDE.md`'s boldness carve-out forbids.

**So this is the sixth consecutive run** in which a programmer session
firing next would triage this file correctly and find nothing it may
build. The list of one-line answers that would change that has grown by
two: B2, the contextual menu, the publish gate, **and now HSTS plus the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair left open by D7**.
D8's Q1/Q2 are a slightly larger call but of the same kind.

**Update — the 2026-09-07 programmer run, and the pattern is now
six-for-six.** That run confirmed the prediction above exactly: it
triaged all eleven items and found nothing authorized, so — like the five
before it — it **sourced its own work**, this time by taking D8's
*additive half* (the piece carrying no decision) and leaving Q1 and Q2
untouched. That is the D4/D5 shape, not a build session answering the
owner's open questions, and the split is recorded in the D8 bullet above.

Worth stating plainly, because it is now the steady state rather than a
run of bad luck: **six consecutive programmer runs have had to invent
their own item.** Each produced real work (D3, D4's half, D5's half, D6,
D7, D8's half), but every one of them was a session *finding* something
rather than the queue *supplying* it — and the additive halves are
getting thinner, because the fork-free pieces are the ones being taken
first. The next run may well find no additive half left. Answering any of
the one-line questions above would change that immediately.

**Update — 2026-09-07 (3) PM check-in: the queue is no longer empty, by
one item.** The prediction directly above (that the next run may find no
additive half left) was close to right, and this run's job was to stop it
being true. Its audit pass covered two areas no previous check-in had
opened — the **invitation and password-reset token flows**, and the
**feedback app** — and produced one build-ready item and one clean
result.

- **`D9` is the new item, and it is deliberately framed as build-ready
  rather than as a question** (see "Tech / infrastructure" above): the
  feedback pull endpoint compares its bearer token with `!=` instead of a
  constant-time compare. One line plus an import, no fork, no migration,
  no owner answer. It is **the only queued item a build session may
  currently take without asking**, which is the whole reason it is worth
  recording rather than shrugging at — its severity is low and stated as
  such, but a run that would otherwise have to invent its own work now
  has one thing it may simply do.
- **The invitation and password-reset flows audited clean**, recorded so
  it isn't re-derived: the invitee's email comes from the invitation row,
  never from the request body, so a token holder can't redirect an invite
  to an address of their choosing; expiry is enforced on the preview
  *and* the accept path, and on the reset confirm; the reset token is
  one-time (`used_at`) and its lookup filters on that; both flows answer
  a bad, used and expired token identically, so neither becomes an
  enumeration oracle; and both write inside `transaction.atomic()`.

**D8's two questions both got smaller, and that is this run's most useful
output** — see the re-measurement appended to the D8 bullet above. Q1 is
**one row** on the only deployment (exactly two orgs exist), fixable
today from Manage → Organization with no migration and no code, so the
"a backfill breaks already-shared URLs" tradeoff that made it the
owner's call barely bites. And Q2 **would not have protected the exposed
org anyway**, because that org publishes a property — so answering Q2
must not be mistaken for closing the live exposure. Only Q1's rename
does that.

**Emptied again 2026-09-07 (4) (programmer run) — and this is the first
time in seven runs the queue actually supplied the work.** D9 was
recorded that morning precisely so a build session would have something
it could take without asking, and this run took it: constant-time compare
plus the first `apps/feedback/tests.py`. That closes the one authorized
item, so the queue holds nothing a build session may take on its own
again, and the blockers are unchanged — B2 and the contextual menu (both
anchored 2026-09-03), the publish gate, HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair, D5's Q1/Q2, D8's
Q1/Q2, due dates on tasks, the D6 backfill query, the org switcher, a
real cron for the purge, server-side search/pagination (*not yet*),
quick-log draft persistence, and the Node 20 pass.

**But the run did not stop at D9, and the reason is worth recording: D9
was a one-line hardening item, and taking only it would have been a thin
session.** Continuing into an audit pass — of `org_scoping.py`, the
module every scoped queryset in the app derives from, which no previous
check-in had opened — produced **D10** (see "Tech / infrastructure"
above), which is the most severe defect these audits have found: an
ordinary "Delete property" click promoted a property-scoped admin to a
full account-wide one, **self-service, with no second actor**. It was
built the same run because it is the D3/D6/D7 shape rather than D5/D8's
— the intent is unambiguous (a membership with scope rows is scoped;
"account-wide" was never meant to be something you could fall into), the
fix needs no migration, and it is reversible by construction.

**D11 is the piece deliberately left, and it is a genuine fork**, not a
tidy-up: after the 30-day purge hard-deletes the properties, the scope
rows cascade away and the membership becomes account-wide *for real*.
D10's fix bounds that to the retention window rather than the instant of
deletion, which is a real reduction and is not the same as a closure. The
three options and a recommendation are in the D11 bullet; picking one is
a one-paragraph answer, not a design exercise.

**Pattern note, since six-for-six was recorded here as the steady
state:** it is now seven runs, and this one is the first where the queue
supplied *an* item — but still not enough of one to fill a session. The
useful reading is not "the queue works now" but that **a check-in
auditing a module the previous ones hadn't opened is what keeps producing
the substantial items** (D3, D6, D7, D8, D10 all came that way, not from
the queue). `org_scoping.py` is now audited; the modules still never
opened by any check-in are `apps/activities/`, `apps/sightings/` and
`apps/species/` beyond their cross-org FK validation.

**Refilled 2026-09-08 (PM check-in) — and the pattern above predicted
where.** That run audited the last three never-opened modules, exactly
the ones the paragraph above names, and found **two build-ready items in
them**: **D12** (an editor can attach another organization's species to
their own activity through the PATCH half of the activity-species
endpoint — the POST half of the *same endpoint* rejects the identical
id) and **D13** (deleting an in-use species returns an unhandled 500,
where the same file's two sibling viewsets already guard the identical
`PROTECT` FK and return a 400). Both are in "Tech / infrastructure"
above with a recommendation, and **neither needs an owner answer** —
they are the D3/D6/D7/D9 shape, not D5/D8/D11's. So for the first time
in eight runs **the queue holds enough for a programmer session to take
without asking**, and D12 should go first: it is the only one of the two
that crosses an organization boundary.

That is six audit-sourced findings to one queue-sourced one (D9), which
makes the reading firmer rather than weaker: **the audit is the queue's
actual refill mechanism.** With `apps/activities/`, `apps/sightings/` and
`apps/species/` now opened, the backend modules no check-in has audited
are down to `apps/tasks/` and `apps/pages/`; on the frontend, nothing has
ever been audited as a module rather than incidentally.

**Emptied again, same day (2026-09-08 programmer run).** Both D12 and
D13 were built, in that order, and the queue is once more empty of
anything a build session may take without an owner answer. So the
eight-run pattern holds with one refinement worth recording: **the
refill lasted exactly one run.** An audit-sourced item is consumed by
the next programmer session, which then has to source its own again
unless another module gets audited first. The two remaining
never-audited backend modules (`apps/tasks/`, `apps/pages/`) and the
never-audited frontend are therefore the queue's only known reserve.

**Unchanged and still the owner's**, one day older: B2 and the contextual
menu (both anchored 2026-09-03); whether CI should gate the image
publish; HSTS and the `SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO`
pair (**confirmed still off today** — no `Strict-Transport-Security`
header on the live host); D5's Q1/Q2; D8's Q1/Q2; **D11**; due dates on
tasks; the D6 backfill query; the org switcher; a real cron for the
purge; server-side search/pagination (*not yet*); quick-log draft
persistence; the Node 20 pass.

**Refilled again 2026-09-08 (3) (PM check-in), by one item — and the
refill mechanism has now run out of backend.** That run audited
`apps/tasks/` and `apps/pages/`, the last two backend modules no
check-in had opened, exactly as the paragraph above predicted it would.
Both were **clean on their own terms** (the pages module's custom-HTML
sandbox, kill-switch and soft-delete guards all hold; the tasks module's
org checks and notification transition logic are correct — details in
`build-questions.md`'s 2026-09-08 (3) entry so they aren't re-derived).

The finding instead came from a pattern cutting across five modules:
**D14** (see "Tech / infrastructure" above), where a non-numeric query
param reaches the database layer and returns an unhandled 500 — sent by
the app itself as the literal string `NaN` whenever a property URL is
mistyped. It was recorded as **build-ready, needing no owner answer**, so
the queue held exactly one item a build session could take without
asking, and D14 was it.

**Update, 2026-09-08 (4) programmer run: D14 is built, and the queue is
empty of authorized work again — the same one-run refill as the previous
cycle.** That is now the established rhythm rather than a coincidence: a
check-in finds one or two items, the next programmer run takes them, and
the queue is bare again. Every one of the fourteen items listed below and
in `build-questions.md` still needs an owner answer, a product call, or a
hosting decision, so a programmer run firing next would triage the queue
correctly and find **nothing it may build** — the position five of the
last nine runs have been in. The one-line answers that would change that
are unchanged and listed in that file's re-deferral table.

**The structural point is more important than the item.** With
`apps/tasks/` and `apps/pages/` now audited, **there is no unaudited
backend module left** — and six of the eight substantial findings to date
(D3, D6, D7, D8, D10, and now D14's cross-module pattern) came from a
check-in opening a module nobody had opened before. That mechanism is
exhausted on the backend. The only surface it has left is **the frontend,
which has never been audited as a module** rather than incidentally —
which is also where D14's root cause turned out to live. A future
check-in looking for the next item should start there. **Still true after
D14 shipped:** that build guarded three route-parameter call sites and
added `utils/ids.ts`, but it did not *audit* the frontend — it fixed the
three sites the finding already named. The module remains unexamined, and
is the only place the audit-refill mechanism has left to go.

**Done 2026-09-09 (PM check-in) — the frontend was audited, and the
refill mechanism is now exhausted everywhere.** That audit came back
**clean**: the single `dangerouslySetInnerHTML` is the server-sanitized
markdown branch only (the `html` branch frames a sandboxed document and
never inlines); there is no `.innerHTML`/`eval`/`new Function` anywhere
in `src`, and no `localStorage`/`sessionStorage` at all; `canAccess` in
`pages/manage/sections.ts` really is the single gate both the menu and
each sub-page consult; `useAsync` cancels on unmount *and* on a
dependency change, so a slow response can't overwrite a newer one; every
one of the 19 files with a submit handler disables its button while a
request is pending; and the D13 pattern — an error set into state that no
render path shows — was checked per *distinct* error variable (8 in
`rows.tsx`, 8 render sites, all on the unconditional path) rather than by
raw counts. Details in `build-questions.md`'s 2026-09-09 entry so they
aren't re-derived.

**It produced exactly one item, D15 (see "Tech / infrastructure"), and it
is small and latent** — a stale-pin count bug on `PropertyMapPage` that
no in-app navigation can currently trigger. It is build-ready and needs
no owner answer, but it does not meaningfully refill the queue.

**So the structural point above now applies to the whole repo: there is
no unopened module left, backend or frontend.** Six of the nine
substantial findings to date came from that one move, and it has nowhere
left to go. A future check-in wanting to refill this queue needs a
*different* mechanism — re-auditing against a changed threat model,
driving the live host as a user rather than reading it, or the owner
answering one of the standing questions. Worth saying plainly rather than
letting the next run rediscover it: the honest report may increasingly be
"nothing new", and that is a real state, not a failed run.

**Update, 2026-09-09 (2) programmer session — the successor mechanism was
tried and it works.** That run built D15 (and its public-site sibling,
which the check-in hadn't noticed carried the identical shape), then, with
no module left to open, audited the **existing** code under a threat model
none of these check-ins had applied: **concurrency**. Every prior audit
asked "is this check correct?"; this one asked "can two requests interleave
between the check and the write?" It produced **D16** immediately — the
last-account-wide-admin guard is check-then-act with nothing held between,
and racing it leaves an organization permanently unadministrable.

**So the refill mechanism is not exhausted, it has changed shape**, and
this is worth recording precisely because the entry above predicted the
opposite. Auditing *modules* is done; auditing the same code under a
*new question* is not. Concurrency is now spent as a question, but the
same move has obvious successors nobody has applied — resource
exhaustion and rate limiting (there is no rate limiting anywhere in the
app, noted since 2026-08-27), failure and partial-write behaviour, and
ordering/idempotency. Each is a lens over code that has already been read,
not a module waiting to be opened.

**Refilled by one item, 2026-09-10 (PM check-in), and the successor
mechanism is now confirmed rather than merely proposed.** That run applied
the next lens on the list above — **resource exhaustion** — and it
produced **D17** (see "Tech / infrastructure") on the first surface it
examined: the QR center-image upload, the only one of the app's five image
inputs with no size cap, no type check and no pixel limit, where a 77 KB
file costs ~470 MB of server memory and the lowest role in the app can
send it. It is **build-ready and needs no owner answer** — the
D6/D13/D14/D16 shape — so a programmer run firing next has exactly one
item it may take without asking.

**The method is the more durable result.** The 2026-09-09 check-in
concluded the refill mechanism was spent because no unopened module
remained; the programmer run that followed corrected that to "changed
shape, not exhausted" and demonstrated it with concurrency (D16). This is
the second data point, from a *different* lens over the same already-read
code, and it landed immediately. Two applications, two findings, makes it
a repeatable move rather than one lucky reframe — so "audit the same code
under a question nobody has asked" should be treated as the standing
technique, and the honest-"nothing new" outcome the 2026-09-09 entry
braced for has not arrived yet. **Lenses still unapplied: failure and
partial-write behaviour, and ordering/idempotency.** Note that app-wide
**rate limiting** — absent since it was flagged 2026-08-27 and never
revisited — is deliberately *not* queued alongside D17: "add rate
limiting" is a design question (which endpoints, what limits, what
store), not a bounded fix, so it needs an owner's shape before a build
session can take it.

**Emptied again after one run, 2026-09-10 (2) programmer session.** That
run took D17 — the queue's only takeable item — and re-deferred the other
fourteen with stated reasons. **This is now the settled rhythm rather
than a coincidence:** a check-in applies a lens and refills the queue by
one or two items; the programmer run that follows takes them and empties
it. Three cycles running (D12/D13, D14, D15/D16, now D17), so a build
session should expect to source its own item roughly as often as it finds
one waiting, and the lens list above is where it should look. Two lenses
remain unapplied: **failure and partial-write behaviour**, and
**ordering/idempotency**.

**Refilled by one, 2026-09-10 (3) check-in — and the lens list is now
spent, with the last two applied together.** That run took both remaining
lenses in one pass, because they turn out to be the same question asked
from two sides: *what does a half-finished or repeated write leave
behind?* It produced **D18** (see "Tech / infrastructure"), which is
build-ready and needs no owner answer, so a programmer run firing next has
exactly one item it may take without asking. **Three applications, three
findings** (concurrency → D16, resource exhaustion → D17, failure/
idempotency → D18) confirms the technique rather than merely repeating it.

**Emptied again by the 2026-09-10 (4) programmer run, after exactly one
run — the fourth consecutive cycle with that rhythm.** D18 is built; the
other fifteen items are re-deferred with stated reasons in
`build-questions.md`, every one still blocked on an owner answer, a product
call, the hosting model, or database access to the deployment. **The queue
is now empty of authorized work with no lens left to apply and no unopened
module**, which is a genuinely new state: the previous three refills each
came from a named lens, and that list is spent. The next check-in needs a
changed threat model, driving the live host as a user, or an owner answer —
and "nothing new" is a real outcome, not a failed run. The standing
one-line owner answers (B2, the contextual menu, CI gating the image
publish, HSTS and the redirect/proxy-header pair) are now the cheapest way
to refill it.

**Refilled by one, 2026-09-10 (5) check-in — and the changed threat model
the paragraph above asked for is what produced it.** The lens applied was
not another way to attack the code but a different question entirely:
**does the app tell the user the truth about what it is doing?** Auditing
rendered strings rather than control flow found **D19** on the first
surface examined — the checkbox that publishes an activity to the open
internet is captioned "no public view exists yet in Phase 1" and ticked by
default, while five real activities sit published on the deployment right
now. Worth recording as a *mechanism*, not just a result: every one of the
nineteen findings to date came from asking whether the code is correct;
none had asked whether the interface is honest, and the two questions have
almost no overlap — D19 sits on code whose filters are all correct and
which several prior audits read without pausing, because there was nothing
wrong with them. **The honesty lens is the successor to the spent
correctness lenses**, and it is barely started: only one form's labels were
examined. Adjacent surfaces for the next check-in: what the other
destructive or publishing controls claim (delete dialogs, the invite flow,
the theme/QR panels), and whether any *empty state* or hint asserts
something no longer true.

**Queue state after this run: one takeable item (D19), fork-free.** The
sixteen previously-deferred items are unchanged and every reason still
holds. `docker-publish.yml` and `tests.yml` were also audited — the first
CI-as-a-threat-surface pass this project has done — and came back clean of
anything queueable; the two hygiene notes are in `build-questions.md` with
an explicit recommendation **not** to queue either.

**Update, 2026-09-10 (6) programmer session: D19 built; the queue is empty
of authorized work again after exactly one run — the fifth consecutive
cycle.** The same rhythm as D14, D15/D16, D17 and D18: a check-in applies a
lens and refills by one or two, the next programmer run empties it. All
sixteen other items were re-triaged and re-deferred with stated reasons
(table in `build-questions.md`); none has become takeable, because each is
still blocked on an owner answer, a product call, a hosting decision, or
deployment access.

**What that run adds to the mechanism note above is that the honesty lens
survives contact with a build.** D19 was the lens's first application, and
it held up end to end: the finding was real, the fix was genuinely one
line, and the *manual* half of it turned out to be the larger and more
useful piece of work — enumerating what a public record actually publishes
is something nineteen correctness findings never surfaced, because nothing
about it is a bug. The successor surfaces the check-in named (delete
dialogs, the invite flow, the theme/QR panels, empty states) remain
unexamined and are still the cheapest next move — with one refinement worth
recording: **the lens should be pointed at what a control's caption
*promises* as well as what it denies.** D19 was a denial ("nothing happens
here") and was caught by searching for absence-claiming strings; a caption
that *overstates* a guarantee ("this can't be undone", "only you can see
this") would not match that search at all, and is the same defect class.

**Update, 2026-09-11 programmer session: D20 built, and the lens's third
application (error messages) produced D21 — so the refill mechanism has
now changed shape twice rather than running out.** The 2026-09-10 (4)
entry called the lens list "spent with no unopened module left", and that
was true of *modules*; it was wrong about questions. Asking a new question
of already-read code has now produced three findings in four runs (D19
captions, D20 nav paths, D21 error messages), and D21 is the first of them
to be a genuine **misattribution** rather than a stale string — the screen
says "no species" when the truth is "the request failed."

**The durable lesson from D21 is about where to point a lens, not about
HTTP.** The bug lived in `client.ts`, a file audited repeatedly and correct
on every axis anyone had previously asked about — types, CSRF, the DRF
unpacking fixed on 2026-09-03. It was only visible once the question
became *"what does the user actually end up seeing?"*, and only reproducible
once the environment was matched: **on HTTP/1.1, which is what local dev
serves, the bug does not exist at all.** A defect that is invisible in
development and universal in production will not be found by reading the
diff, and was not. Prefer a controlled experiment that varies one
environmental axis over reasoning about a spec.

**Where to point it next.** Error messages are now spent as a lens. The
unexamined surfaces are the ones where the app reports *success*: a
confirmation that fires before the server has confirmed anything. The
2026-09-11 check-in already found one un-queued instance of exactly this
(the resend-invite button's "Sent!", which asserts delivery that
`send_invitation_email` silently swallows the failure of), and noted it
was entangled with the open real-email question — but the *class* is
broader than that one button and has never been swept.

**What came back clean under those lenses is recorded so it is not
re-derived.** Every multi-step write that matters is already properly
atomic: `signup`, `invitation_accept` and `password_reset_confirm` each
wrap their multi-row creates in `transaction.atomic()`, and — the one that
would matter most, given D10 established that *empty scope encodes
account-wide* — `membership.properties.set(...)` sits inside the
transaction at **all three** call sites (both `MembershipViewSet.create`
branches and `_apply_membership_update`), so a failure between creating a
membership and writing its scope cannot leave a fail-open account-wide
member. The purge is per-property atomic and its
`Sighting.objects.filter(...)` is not exposed to the D10 manager trap
(`Sighting` declares no custom default manager). `notify()` is deliberately
outside the task's own commit, which is the right failure direction — a
notification channel failing must not lose the task. And **D17's own
ordering question, asked of the other four image endpoints, comes back
clean**: activity photos, sighting photos and both theme banners each run
`validate_image_upload` *then* the byte cap *then* `.read()`, so no guard
runs after the work it prevents. Two lower-value partial-write surfaces
were considered and deliberately not queued: the reorder path issues N
sequential PATCHes with no transaction, but normalizes to array indices
and is therefore self-healing on the next move (its own docstring says
so), and a POST that commits before a later step fails has no idempotency
key anywhere in the app — both cosmetic at today's scale.

**The refill mechanism now genuinely needs a new source.** With the three
named lenses spent and no unopened module left, the next check-in should
expect either a changed threat model, driving the live host as a user, or
an owner answer to be what produces the next item — and "nothing new"
remains a real outcome rather than a failed run.

**Refilled by one, 2026-09-11 check-in — the honesty lens's second
application, aimed exactly where the last entry said to aim it.** That
entry's refinement was to point the lens at what a caption *promises*, not
only at what it denies, since a denial ("nothing happens here") is found by
searching for absence-claiming strings while an overstated guarantee is
not. Applied to the four named surfaces — delete dialogs, the invite flow,
the theme/QR panels, and empty states — it produced **D20** (see "Tech /
infrastructure"): the two property-delete confirmations tell the user to
recover their property from *"Admin → Recently deleted"*, a menu renamed to
**Manage** on 2026-09-03. Build-ready and fork-free, so a programmer run
firing next has exactly one item it may take without asking.

**D20 is deliberately recorded as small, and the calibration matters more
than the item.** It is wayfinding, not data loss — the section still
exists one nav entry over under the same inner label, and `/admin` still
redirects. What earns it a record is placement: it is the single sentence a
user reads at the moment they destroy something, and it is wrong about how
to undo that. Recording it at its true size rather than inflating it is the
point; the queue is more useful when an item's stated severity can be
trusted.

**The more interesting result is what came back clean, because it says the
lens is closer to spent than its first outing suggested.** Recorded so it
is not re-derived: the four *other* `→` menu paths in the frontend are code
comments that already say "Manage →" correctly; every `is_public` caption
is truthful post-D19 (`SightingFormPage`, `PropertyFormPage`, `QuickLogPage`
and `SpeciesPage`'s "Shown publicly" hint all say plainly what they do);
every empty state examined is accurate, including two that could easily not
have been — `FeedbackSection`'s "No feedback submitted yet" holds because
the admin list applies **no status filter**, so a synced item still shows
(had it filtered to `new`, an admin would see "none submitted" while their
org had submitted plenty), and `DeletedSection`'s "Nothing deleted in the
last 30 days" holds for what it lists. And the app's one genuine *security*
promise to a user is not merely accurate but exemplary:
`PageFormPage.tsx:148` tells a custom-HTML author their code "can't reach
your account, but it **can** affect whoever visits this page" — it states
the guarantee *and* its limit, and that limit was verified end to end in a
real browser on 2026-09-02 (3).

**Two things were found and deliberately NOT queued**, with the reasoning
recorded so a later run doesn't re-litigate them. (1) The *resend*-invite
button flashes **"Sent!"**, asserting delivery, while the add-member form
in the same section correctly hedges ("If the email doesn't arrive, copy
the link") — with no SMTP configured, `send_invitation_email` logs and
swallows the failure, so "Sent!" can be false. It is an inconsistency worth
knowing about, but the button did attempt a send, and the honest fix is
entangled with the still-open real-email question rather than being a word
swap. (2) `DeletedSection`'s empty state is **scope-filtered** — the
`deleted` endpoint applies `filter_by_property_scope`, so a property-scoped
admin can read "Nothing deleted in the last 30 days" while the organization
does hold deleted properties outside their scope. It asserts about the org
while meaning "none you can restore." Both are real; neither is worth a
build session's time today. **Recommendation: not now, for both.**

**One thing checked and found accurate rather than corrected:**
`limitations.md`'s testing bullet claims "122 tests across six modules",
and the methods were **counted, not trusted** — 64 + 21 + 10 + 7 + 10 + 10
= 122 across exactly six modules. The retention promise was also checked
and holds: the delete dialog's "after which it's removed for good" could
have overstated a guarantee, since no cron runs the purge, but
`docs/manual/properties.md:159` already discloses the real mechanism
precisely ("a property may sit a short while past day 30 before the rows
actually go … it's gone before the list is drawn"). That is the manual
being *more* honest than it had to be, and it is why this is not a second
finding.

**Where to point the lens next, since the named surfaces are now used up.**
The honesty question has been asked of captions and empty states; it has
**not** been asked of *error messages* — what the app says went wrong, and
whether the stated cause is the real one. A message that misattributes a
failure sends the user to fix the wrong thing, which is the same defect
class as a caption that misstates a menu. That, or an owner answer, is the
cheapest next refill.

**Everything else is unchanged and still blocked on the same things:** B2
and the contextual menu (both anchored 2026-09-03) need a yes/no; whether
CI should gate the image publish, and HSTS plus the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair, are one-line
decisions for whoever owns the deployment; D5's Q1/Q2, D8's Q1/Q2 and D11
are real forks each already carrying a PM recommendation; due dates on
tasks and the org switcher are product calls; the D6 backfill query needs
database access to the deployment; a real cron for the purge waits on the
hosting model; server-side search/pagination is recommended *not yet*;
quick-log draft persistence waits on someone actually losing work to it;
the Node 20 pass waits on major-version bumps being available.

**Update, 2026-09-11 (3) PM check-in: the success-reporting lens was swept
and produced D22** (see "Auth and API") — the "forgot password" flow tells
a locked-out user a reset link "has been sent" on a deployment that sends
no email, and `/forgot-password` is the one screen in the app with no route
to the caveat, because the **Help** link lives inside `AppShell` and that
page sits outside it. **One takeable item: D22's fork-free half** (stop
asserting delivery at the two un-hedged sites); its second half — whether a
locked-out user gets a real way out — is a genuine three-way fork for the
owner and is queued as such.

**The mechanism note this run adds is about *un-parking*, not about
finding.** The resend-invite "Sent!" had been visible to several check-ins
and was each time left un-queued as "entangled with the open real-email
question" — a fair call, since a build session cannot decide SMTP. Sweeping
the class is what separated the two concerns: **the wording is independent
of the delivery decision.** Whatever a deployment's mail situation, a
message asserting a delivery the server never verified is wrong, and
correcting it needs no answer about SMTP. Worth generalizing: when an item
sits un-queued because it is entangled with an open question, check whether
*part* of it actually depends on that question — here the entanglement was
assumed rather than tested, and it had parked a real defect for several
runs.

**What came back clean, recorded so it is not re-derived — the class is
narrow: it is only the email claims.** Every inline auto-apply control is a
*controlled* component bound to server data rather than optimistic local
state (`MemberRow`'s role select and property checkboxes read
`membership.role`/`membership.properties`; `TaskRow`'s assignee and status
read `task.assigned_to`/`task.status`), so a failed PATCH snaps the control
back to the server's value instead of leaving the screen showing a change
that never happened — which is precisely the defect this lens hunts, and it
is absent. Both reorder callers reload on **failure as well as success**,
so a normalizing pass that dies partway re-reads the server.
`PhotoUploader` keeps no local list. `AccountPage`'s "Password updated."
and `PostSavePhotoStep`'s "Your X is saved." both follow a real server
confirmation; `FeedbackButton`'s "your feedback was sent" is true (it
reached Habitat's own database, which is what this routine pulls from); and
"Copied!" is set only after `clipboard.writeText` resolves, with a
`window.prompt` fallback when it rejects.

**Where to point it next.** Success reporting is now spent as a lens. The
successor is a real gap rather than a guess, and D22 surfaced it by
accident: **every audit to date has looked at the app from the inside —
code, strings, endpoints. None has asked what a user who is *stuck* can
actually do.** A locked-out user has no route to Help, no "contact whoever
runs this instance", and no documentation path anywhere on the
unauthenticated screens. That is the same defect class as an empty error
message — a dead end the app never names — and it has never been swept.

**Refilled by one, 2026-09-12 check-in — the stuck-user lens swept, and it
produced D23 on its first application** (see "Tech / infrastructure").
Every unmatched address in the app resolves to the login screen, so a
mistyped URL and a locked door are literally the same screen; and a valid
gated address is diagnosed correctly and then discarded, because nothing
captures the destination. Build-ready in both halves, so a programmer run
firing next has exactly one item it may take without asking.

**The sweep confirmed the check-in's own hypothesis and then went one
further than it.** It predicted a locked-out user has no route to Help and
no "contact whoever runs this instance" — both true, verified per screen:
the five unauthenticated pages link only to each other, and `MANUAL_URL`
sits inside `AppShell`. What it could not have predicted is that **the fix
shipped the same day made the gap load-bearing**: D22's new reset message
tells the user to *"contact whoever runs this one"*, and a sweep for any
contact route across `frontend/src` and `docs/manual/` returns a single
hit, saying the same thing. A correct fix now issues an instruction the
app gives no way to follow — which is why "who is that?" is recorded as
the owner question with the best value-to-effort ratio in the queue.

**The calibration note, since this repo's queue is only useful if stated
severities can be trusted:** D23 is navigation and recovery, not data
loss — no exposure, no cross-org reach, no escalation, no 500s. Its two
halves are deliberately *not* ranked equally: the deep-link half is
friction a logged-in user can work around, while the mistyped-public-URL
half is a genuine dead end, because it lands on a visitor with no account
and hands them a login form. Only the second one answers the lens's own
question.

**The refill mechanism changed shape a third time, and this is the
clearest instance yet.** The 2026-09-10 (4) entry called the lens list
spent "with no unopened module left"; that was true of modules, and the
three successors since (captions, error messages, success reporting) were
all still questions about *code*. This one is a question about a **person
in a predicament**, and it found a defect sitting in `App.tsx` — a file
every frontend audit has read, correct on every axis previously asked of
it. **Named successor, same family:** this run covered the user who is
*lost*; the user who is **new** is unexamined — what someone actually hits
between signing up and having any data, where every list is empty and
several screens exist only to be filled.

**Emptied again by the 2026-09-12 programmer run, after exactly one run —
the seventh consecutive cycle.** D23 was built in both halves and the
other nineteen items re-deferred with their existing reasons, so the queue
holds no authorized work again. Two things about this cycle are worth
keeping rather than filing as a repeat:

**The stuck-user lens survived contact with a build, and its cheap half
was the valuable one.** Half 1 is a new page and a one-line route swap;
half 2 touches ten call sites and a sanitizer. Half 1 is the half that
answers the lens — it is the one an account-less visitor hits — which is a
useful corrective to ranking work by how much of it there is.

**The open-redirect guard is the run's transferable finding, and it is a
new shape for this repo.** Every prior "don't half-fix it" lesson here has
been about *coverage* — four filters not two, eight serving paths not two.
This one is about **an in-repo precedent being the wrong thing to copy**:
`_clean_page_path` is correct for its own job and, ported verbatim into a
redirect, leaves four measured off-site redirects open. Reusing an
existing guard is normally the right instinct; it is only safe when the
new use has the same threat model, and *displayed* versus *navigated to*
is not the same threat model. Worth asking of the next reuse, not just
the next sweep.

**Refilled by the 2026-09-12 (3) PM check-in with TWO fork-free items
(D24, D25) — the first time in eight cycles the queue holds more than one
takeable thing.** The new-user lens the previous entry named was applied
and it produced both. Three things worth keeping:

**The lens found an ordering dependency, not a missing empty state.** The
empty states are genuinely well-tended — several carry comments from prior
sessions, and `DashboardPage` already gates Quick log on having a property.
The gate is correct and still lets D24 through, because it keys on
properties and nothing else. What no audit had asked is **which reference
lists a new account starts with**, and the answer is asymmetric: workflow
states and activity types are seeded per org, species deliberately is not.

**A decided product stance had an untraced consequence, and that is a new
shape here.** "No starter species list" is a real owner decision and stays
one; what nobody followed through was that the only create flow requiring a
species has no way to create one. Prior findings came from asking whether
code is correct (D1-D18), whether the interface is honest (D19-D22), or
what a stuck user can do (D23). This one came from asking **what a decision
costs downstream** — worth pointing at other settled decisions, since a
stance can be right and still leave a flow unfinished.

**Named successor for the lens:** the new-user path is now examined at its
*start*. What is still unexamined is the account that has grown — the
second property, the second member, the hundredth sighting: where the app's
client-side filtering, its single-org assumption (`get_active_membership`'s
first membership), and its unpaginated list endpoints all first bite. That
is the same territory as the long-deferred server-side search/pagination
item, which has been re-deferred as "not yet" eight times without anyone
measuring where "yet" actually is.

**Emptied again by the 2026-09-12 (4) programmer run — the eighth
consecutive cycle, but the first that cleared TWO items and found a third
on the way.** D24 and D25 are both built, the other nineteen re-deferred
with their existing reasons. What is worth keeping from this cycle:

**Building a fix routed traffic into an adjacent live 500, and that is how
D26 was found.** D24's whole point is letting quick log create a species,
which made `api.species.create` reachable from a second caller. Asking
"what does this path do when it fails?" turned up an unhandled
`IntegrityError` — D13's exact shape, in the same app, live on the
deployed host since the species page existed. **Generalizable: when a
change adds a caller to an existing endpoint, audit that endpoint's
failure modes as part of the change**, not as a separate lens later. The
new caller is what makes an old failure mode matter.

**The naive-fix measurement paid off a fourth time, and split cleanly.**
Against the real pre-fix code 5 of 9 tests fail with the raw
`IntegrityError` in the traceback. Against the *attractive* wrong fix —
mirror the two sibling guards' `__iexact`, validator only — those 5 all
pass, and **only the two tests built for it fail**: the constraint test
(that fix would have settled the owner's open casing question as a side
effect) and the mechanism test (it leaves the race a 500). Each half is
blind to exactly what the other catches. A smaller failure count still is
not evidence a fix works.

**A fix can be tempted into answering an open question by accident.** The
obvious way to write D26's guard is to copy its siblings; copying them
would have quietly closed the name-uniqueness casing item this file has
deliberately left to the owner since 2026-09-10. The guard against that is
not vigilance, it is a test that asserts the open behaviour still holds —
`test_a_differently_cased_name_is_still_accepted` fails loudly if a later
tidy-up "restores consistency". Worth copying wherever a fix sits next to
a deferred product call.

**Named successor is unchanged and now overdue:** the account that has
**grown** — the second property, the second member, the hundredth
sighting, where client-side filtering, the single-org assumption and the
unpaginated list endpoints first bite. This run did not touch it.

**Refilled by one, 2026-09-13 PM check-in — the overdue lens swept, and it
found what it was pointed at.** **D27** (see "Tech / infrastructure"
above) is the only takeable item; the other nineteen are re-deferred with
their existing reasons, one corrected (quick-log draft persistence loses
the boost D24 gave it, since D24 closed the dead end that made a discarded
capture expensive).

**The lens worked, and what it caught is worth generalizing.** Every prior
finding here came from asking whether the code is *correct*. D27 is
correct code: the serializers never put image bytes in a response body,
and each one says so in a comment that is accurate. What nobody asked is
what the *queryset* loads — so the bytes are pulled from Postgres by every
list path and read by none of them. **A comment that truthfully describes
what a serializer does can be the reason nobody checks the layer beneath
it.** The tell was structural rather than behavioural: two `BinaryField`
columns on main tables, and zero `.defer()`/`.only()` in the whole
backend.

**And the "grown account" framing is what made it measurable rather than
theoretical.** At one property and six records nothing here hurts; the
defect is defined by its slope, not its current value. The decisive
measurement was not "is the blob loaded" but "is it loaded *per row*" —
100 sightings, 100 separate copies of the same 5 MB banner, because
`select_related` does not dedupe. Ask for the slope, not the reading.

**Named successor:** the account that has grown still has two untouched
axes, and this run only took the third. **The single-org assumption**
(`get_active_membership`'s "first membership wins" — the org switcher is
queued as a *feature*, but nothing has audited what a genuinely two-org
user experiences today) and **the second member** (concurrent editing of
the same record — there is no optimistic locking anywhere, so two editors
on one activity silently last-write-wins). Neither has ever been swept.

**Emptied again by the 2026-09-13 programmer run — the ninth consecutive
cycle.** D27 is built (see "Tech / infrastructure"), the other nineteen
re-deferred with their existing reasons. Three things from this cycle
worth keeping:

**The check-in named the attractive wrong fix, and the first version of
the test section still failed to catch it.** That is the sharpest
argument yet for actually *building* the naive fix rather than reasoning
about it: knowing what the wrong fix is does not tell you whether your
tests stop it. Both gaps were subtle and in the same direction — the
content-type assertion covered one queryset of three, and the query-count
test grepped for the blob column while the naive fix's per-row lookups
are for the *content type* beside it. Measure, then fix the tests.

**The in-repo trap the check-in did not have: this fix cannot be
centralised.** The obvious home for it is `PropertyManager`, which
already filters soft-deleted rows — and it would silently miss the worst
case, because a `select_related` join never consults the related model's
manager. That same semantic is the one `public_site` has a long comment
about for soft delete. **It is worth asking, of any manager-level
invariant in this repo, whether a join can walk around it.**

**And a fix whose whole point is "load less" has a matching failure mode:
writing less.** Deferring a column raises the question of what a `save()`
on that instance then writes. Django gets it right, so nothing broke —
but the wrong answer would have been an ordinary rename silently erasing
a banner, with no error and no test noticing. Pinned rather than trusted.

**Named successor is unchanged** — the two axes above are still untouched,
and this run did not take either.

**Refilled by one, 2026-09-13 (3) PM check-in — the first of the two
remaining "grown account" axes swept.** **D28** (see "Accounts, orgs, and
permissions" above) is the only takeable item, and only its **fork-free
half**: name the organization the user is acting in. **D29** (see "Tech /
infrastructure") came out of the same run's sweep of the *second* axis and
is deliberately **not** takeable — how a concurrent-edit conflict is
surfaced is a product decision. The other twenty items are re-deferred
with their existing reasons, one changed: **the org switcher is no longer
purely additive capability**, because D28 shows it has a cost today.

**What the lens caught, and why it is a new shape here.** D24 found a
*settled* decision (no starter species list) with an untraced consequence.
D28 is the sibling case: a **forward-looking** decision — notifications are
scoped to the recipient, not the active org, explicitly so they work
"regardless of which org happens to be active" — made in anticipation of
multi-org support that was never built. The intent is right and the code
is correct; what it produces today is a notification a two-org user cannot
attribute (the org name is nowhere in the app, and the serializer does not
even send it) and cannot open (the click lands on the active org's task
list). **Worth pointing the next lens at other decisions written for
features that don't exist yet**, not only at settled ones.

**And the sharpest single detail is worth carrying forward on its own.**
`Notification` *has* an `organization` FK. The view doesn't filter on it,
the serializer doesn't send it, and the app never names the active org —
**four independent places drop the same dimension**, each defensible
alone. When a finding looks like "the UI just doesn't show X", check
whether X survives the serializer, because "not displayed" and "never
delivered" are different defects with different fixes.

**Emptied again, 2026-09-13 (4) programmer run — the tenth consecutive
cycle.** The one takeable item was taken: D28's fork-free half is built
(both parts — the chrome *and* the serializer attribution that turned out
to be the real blocker), and the other twenty items were re-deferred with
their existing reasons. Q1/Q2/Q3 and D29 remain the owner's.

**The build produced one lesson the check-in could not have, and it is
about D27 rather than D28.** Naming the organization on the notification
list needs a join to `Organization`, which carries a `theme_header_image`
blob — so the obvious implementation reintroduces D27 exactly, silently,
because the response body is byte-identical either way. **D27's invariant
is not self-maintaining: it is a property of each query, so every new
`select_related` to a blob-bearing table re-opens it.** Both plausible
wrong fixes here (join-without-defer, and attribution-without-join) return
correct JSON and are caught by *disjoint* mechanism tests — neither can
see what the other catches, the D22 lesson in a new place. Measured rather
than argued: built both, and each failed exactly the one test written for
it.

**Named successor:** the second member axis is now *swept* but not
*closed* — D29 records it and hands the shape to the owner. What remains
genuinely unexamined under the grown-account lens is **volume**: the
unpaginated org-wide list endpoints and the client-side filters over them.
D27 measured the per-row blob cost and explicitly did **not** measure the
slope; server-side search/pagination has now been re-deferred as "not yet"
**ten times without anyone establishing where "yet" is**. A check-in that
measured it — row counts on the deployment, payload size, time to first
paint on `/activities` and `/sightings` — would turn a ten-times-deferred
judgement call into a number, and that is the cheapest remaining way to
refill this queue with something decidable.

**Refilled by two, 2026-09-14 PM check-in — the volume lens swept, and the
measurement reordered the question rather than answering it.** **D30** and
**D31's compression half** are both takeable with no owner input; D31's
geometry half is takeable but larger. The other twenty-one items are
re-deferred — and **one re-deferral reason has changed for the first time
in ten cycles.**

**Server-side search/pagination is still "not yet", but no longer for
want of a measurement.** The slope is measured now, and it ranks
**fourth of four levers**: bounding the notification poll (D30), enabling
`GZipMiddleware`, and dropping geometry the list pages never draw each
beat it, and the first two need no design call whatsoever. Compression
plus dropping unrendered geometry takes a 10,000-row Activities load from
**6.1 MB to 62 KB (99%)** — moving the wall out by roughly two orders of
magnitude *before* anyone designs a page size. Pagination is still the
right eventual answer; it is not the next one. Do D30 and D31, then
re-measure.

**The generalizable half is about where a cost hides.** Every prior
volume intuition here was about *rows on a page*. Both findings are about
neither: D30's cost is paid on a **timer**, by a component nobody
opened, on a list that grows even when the land does not — and D31's
dominant term only becomes dominant **after** compression, because
high-entropy coordinates barely compress while the repetitive keys around
them vanish. **Compression does not shrink a payload uniformly; it
changes which field is the payload.** Ask what the cost is *per unit
time*, not only per row, and measure the composition *after* the cheap
fix, not before it.

**And the D28 lesson recurred in a new place, which is why D30 names its
wrong fix up front.** The obvious bound — slice the queryset — leaves a
byte-valid response and a silently wrong unread badge, because that count
is *derived client-side* from the full list rather than sent. "Derived
from data you are about to stop sending" is the same defect family as
"never delivered", and it is invisible in the response body either way.

**Named successor:** volume is now swept on the **read** path. The
**write** path at volume is untouched — photos are `BinaryField`s in
Postgres by decision, 8 MB each, with no quota, no count limit and no
purge, and "Photo storage growth" has sat in this file since Phase 1
without anyone measuring what a year of field photography does to the
database or to a backup. Same shape as this run: a decided tradeoff whose
slope nobody has put a number on.

**Emptied of fork-free work again, 2026-09-14 (2) programmer run — the
eleventh consecutive cycle.** Both takeable items were taken: **D30 in
full** (the bound *and* the exact `unread_count`, plus the `-id` ordering
tiebreaker a LIMIT turns out to require) and **D31's compression half**.
**D31's geometry half was re-deferred with a stated reason** rather than
half-built — it needs `GeoFeatureModelSerializer` to omit the geometry
that defines its own output shape, on serializers shared with the public
site, so its blast radius is wider than the diff looks and its
re-verification cost is real. The other twenty-one items keep their
existing reasons.

**Measured end to end on real HTTP, and the combined result is larger than
either half:** a 1,000-notification poll went from **251 KB to 461 bytes**
(~545x), and the payload is now **flat with respect to history size**
rather than growing — which is the property that actually matters, since
the slope was the finding. Compression alone measured **10.8x**, above the
check-in's 7.0x, because a bounded payload is more repetitive than an
unbounded one. **So the two cheapest levers compound rather than merely
add**, and pagination has moved further away still.

**The build's own lesson is about what a test's *filter* can silently
discard, and it is D27's substring trap in a new costume.** The mechanism
test for D30 excluded the count query with `"COUNT" not in sql` — and the
row query joins `accounts_organization`, in which **"ACCOUNTS" contains
"COUNT"**. The filter threw away the very query the test existed to
inspect, and the test then reported that nothing had read the rows at all.
It failed loudly and was fixed to match `COUNT(*)`; **the same slip in an
assertion phrased the other way round would have passed forever.** D27's
rule was "match whole column names, not substrings"; the general form is
**a substring check inside a test's own filter is as dangerous as one
inside its assertion, and much harder to notice, because a
wrongly-narrowed filter usually still leaves something to assert on.**

**One check-in assumption improved on rather than inherited: the BREACH
question did not need to be an owner call.** The check-in framed it as
"accept the risk or exclude the view". Reading the pinned Django's actual
`GZipMiddleware` source shows a third, better answer — it already pads
compressed responses with up to 100 random bytes, which *is* the BREACH
mitigation. So the decision is "enabled, and mitigated by the framework",
pinned by a test so a downgrade past that mitigation goes red. **Read the
implementation of the thing you are about to enable; the standing warning
about it may predate its fix.**

**Refilled by one fork-free item, 2026-09-14 (3) PM check-in.** This run
swept the successor the last two entries named — the **write** path — and
found **D32** and **D33** above. **D33 is the takeable one** (cache
validators on the eight image paths: no fork, and photo immutability is
already guaranteed by the absence of any `PATCH` route). **D32 is the
owner's** — derive-and-keep versus downscale-on-upload, where the second
irreversibly discards detail. D31's geometry half remains takeable but
larger. **Recommended order: D33 first.**

**The finding's shape is worth keeping separately from the finding.** The
last two runs measured the **read** path and concluded pagination ranks
fourth of four. This run measured the **write** path and found the same
pattern one layer down: the expensive thing is not the number of records
but *how much of each record travels, and how many times*. D32 and D33 are
orthogonal — caching alone is 20×, thumbnails alone 128×, both together
**2,556×** — exactly the compounding D30/D31 showed. **Three consecutive
lenses have now found that the cheap, un-designed lever beats the
expensive, designed one**, which is itself the argument for measuring
before designing.

**One stale owner question retired rather than re-asked:** the standing
re-deferral table still lists **D31's BREACH call** as a one-line owner
decision, but the same day's build session *answered* it (the pinned
Django's `max_random_bytes` is the mitigation, now pinned by a test — see
the paragraph immediately above). It is off the owner list. Worth doing
deliberately: a queue that keeps asking answered questions spends the
owner's attention buying nothing, and this is the second bookkeeping drift
of that kind (the day-count drift corrected 2026-09-06 was the first).

**Emptied again by the 2026-09-14 (4) programmer run — the twelfth
consecutive cycle.** That run took D33 end to end (stored digest column,
`serve_image`, all eight paths, three migrations with SQL backfills,
25 tests, 20.0× measured on a live server). **D32 stays the owner's** and
**D31's geometry half stays takeable but larger** — re-deferred with its
existing reason, which is unchanged: it needs `GeoFeatureModelSerializer`
to omit the geometry that defines its own output shape, on serializers
shared with the public site, plus a query param and three callers.

**A lesson from D33 that generalizes past caching, and is the sharpest
version yet of a point this log keeps making.** The three plausible wrong
fixes here fail on **disjoint, single-test** boundaries — one mechanism
test each, with every outcome test green against all three. What makes it
sharper than D28's pairing is the third one: `public, max-age=…,
immutable` is caught **only** by an assertion about the header string,
because its failure mode is *that the request never arrives*, and a server
cannot observe a request it never receives. The retraction test — the one
that looks like it is guarding exactly this — passes against it. **When a
defect's consequence happens somewhere you have no instrument, the
assertion has to move to the thing you can see, even when that feels like
testing a constant.**

**And a guess that measurement corrected, which is the reason to measure
rather than reason.** The weak-ETag case was written up as exotic, on the
assumption that JPEG bytes don't compress so `GZipMiddleware` would leave
a strong validator. A real 359 KB JPEG compresses ~2% — enough for the
middleware to keep the compressed response — so `W/"..."` is the **normal**
case for a photo, and the strong-comparison wrong fix would have re-sent
every photo in the app on every view while passing any test that forgot to
send `Accept-Encoding`.

**Named successor for the lens:** the write path is now swept for
*volume*, but not for *durability*. **Nothing in this repo backs anything
up.** `docs/deployment-config.md` says how to run the app and nothing
anywhere says how to restore it — no dump schedule, no retention, no
tested restore. The photos measured above are precisely what makes that
matter: they are the bulk of the database by design, they are the one
thing in it that cannot be re-derived from anywhere else, and a land trust
at 52 GB/year has a restore-time problem nobody has looked at.

**Refilled by one fork-free item, 2026-09-15 PM check-in.** This run swept
the successor the last three entries named — **durability** — and found
**D34** and **D35** above. **D34's wording half is the takeable one**
(make the activity and sighting confirm dialogs say that the delete is
permanent and takes the photos with it): no fork, no migration, and the
manual already asserts the safeguard it would create. **D35 is the
owner's** and is downstream of the undecided hosting model. D34's
soft-delete half stays the owner's too, and is the same ambiguous item
re-deferred 2026-08-28. D31's geometry half remains takeable but larger.
**Recommended: D34's wording half first** — the cheapest item in the
queue that reduces the chance of permanent data loss.

**The two findings compose, which is why they were reported together:
D34 is the most likely way data actually gets destroyed, and D35 is the
reason it would be gone for good.** Neither is a live incident — the
deployment holds zero photos — so these are measured latent risks, not an
outage.

**A shape worth keeping, and it is the honesty lens moved up a level.**
D19 found a caption that denied what it did. This run found something
harder to search for: a **documented safeguard that under-delivers on the
job its documentation assigns it.** No string here is false — the manual
is accurate and the prompts are accurate as far as they go. The defect is
in the *gap between what the manual credits the prompt with and what the
prompt says*, which no grep over rendered strings would surface, because
you have to read the doc and the dialog against each other. Point the
lens at anything else the docs describe as a protection.

**Named successor:** durability is now swept for *loss* but not for
*correctness under recovery*. Three migrations with SQL backfills landed
2026-09-14 (D33), and `entrypoint.sh` runs `migrate` automatically on
every boot — so rolling an image back meets a database already rolled
forward, and Django has no automatic down-migration. **Nothing in this
repo describes how to roll a bad deploy back**, and no session has asked.

**Emptied again 2026-09-15** (scheduled programmer session) — the
**thirteenth consecutive cycle** of a check-in refilling by one or two
and the next programmer run clearing it. **D34's wording half** shipped
with the photo count in it, and **D35's separable doc sub-question** was
taken with its claim narrowed to what the software does (see both bullets
above). Everything else was re-deferred with its existing reason.

**D31's geometry half was re-deferred for the third time — but the reason
is now sharper than "larger", and that is worth more than the deferral.**
The obvious implementation is `.defer("geometry")` on the org-wide
querysets. **Checked against the installed `rest_framework_gis` source
rather than assumed:** `GeoFeatureModelSerializer.to_representation`
(serializers.py:136-140) reads `self.Meta.geo_field` **unconditionally**
whenever it is set. So deferring the column without also stopping the
serializer reading it produces a **per-row lazy load of the geometry** —
strictly *worse* than not deferring at all, on the exact endpoints the
change exists to speed up, **and the response body is byte-identical
either way**. That is D27 reopening through a new door, and it is
precisely the D28 shape: the attractive wrong fix is invisible in the
response and can only be caught by a query-count or query-column
mechanism test. Whoever takes this should write that test **first**, and
build the naive version to confirm the test actually fails against it
(the D27/D30 lesson — naming the wrong fix is not the same as testing
against it). The blast radius is also wider than the earlier note said:
not three callers but **five call sites across three files**
(`ActivitiesPage`, `TasksPage` ×2, `DashboardPage` ×2), with
`SightingsPage`, `PropertyMapPage` and both form pages genuinely needing
the geometry. Value is undiminished: 868 KB → 62 KB on a 10,000-row load.

**Refilled by one fork-free item, 2026-09-16 PM check-in.** This run swept
the successor the last two entries named — durability's *correctness under
recovery* half — and found **D36** and **D37** above. The queue's framing
was right that nothing describes how to roll a deploy back, and it turned
out to be the smaller half of what is there: **a rollback reports success
and then 500s on the first write** (D36), and **for the frontend there is
no image to roll back to at all** (D37).

**D36's fork-free half is the takeable one** — a "Rolling back a deploy"
section in `deployment-config.md`. No fork, no migration, no code, and
**this run measured that the procedure it would describe actually works**
end to end, including that rows written during the rollback window are
correctly backfilled on re-upgrade. **D36's `entrypoint.sh`-should-refuse
half and D37 are both the owner's.** D31's geometry half remains takeable
but larger. **Recommended: D36's docs half first.**

**Emptied again 2026-09-15 (2) (programmer session) — the fourteenth
consecutive cycle.** That run took D36's docs half, the single takeable
item, and re-deferred the rest. **The lesson it brought back is about
re-measuring an inherited finding rather than transcribing it:** the
check-in's measurements were all correct, but it had measured them on
*mirror models*, and re-running the same loop on the **real repository**
(a worktree at the genuine pre-D33 commit) surfaced a step the mirror
could not have shown — **the rolled-back image cannot run its own
down-migrate**, and reports success while doing nothing. A finding
reproduced on a stand-in is a finding about the stand-in; the procedure
you intend to *document* has to be run against the thing it describes.

**Queue state after the 2026-09-16 (3) programmer run: empty of fork-free
work again — the fifteenth consecutive cycle.** That run took D38a, and
found and fixed a D27 instance beside it (both link-list querysets joined
`Property` without deferring its banner — missed by the 2026-09-13 sweep,
and found only because the `linked_by` join landed on those same two
lines). **Recommended next: D31's geometry half**, still the largest
measured lever with a number attached (868 KB → 62 KB at 10,000 rows),
with both its trap and its true blast radius documented in advance.

**Two things from that run worth carrying forward.** First, **"caught by
disjoint tests" is a claim to measure, not to assert** — D38a's three
wrong fixes turned out to form a nested ladder rather than a partition,
and the useful question is which single test is the only thing stopping
each one. Second, and more transferable: **the wrong fix that reads
identically from the outside is the dangerous one.** Stripping attribution
in `public_site` produces a byte-identical public response to the real
fix, so no assertion about any response can tell them apart; what
distinguishes them is whether the class the *next* public endpoint reaches
for is safe by default. The observable that settles it is which files the
diff touches — opt-in leaves `public_site` unmodified.

**Queue state after the 2026-09-16 (2) check-in: refilled by one takeable
item — D38a — with three owner questions (D38b's Q1/Q2/Q3) beside it, and
D31's geometry half still takeable but larger.** **Recommended order:
D38a first** — it is smaller than D31's geometry half, needs no migration
and no owner answer, and it is the one item whose value rises with every
other open defect (D29's silent last-write-wins is materially worse while
the app discards the record of who did the writing). D31's geometry half
stays the largest *measured* lever; D38a is the cheapest *correctness-of-
record* one. The fifteenth consecutive cycle in which a check-in refills
by one or two and the next programmer run empties it.

**The refill came from pointing the lens at what the database already
holds rather than at what the code does** — a variation worth keeping,
since D38 sits on fields several prior audits read straight past because
nothing about them is wrong.

**Queue state after the 2026-09-15 (2) run: empty of fork-free work, with
D31's geometry half still takeable but larger.** That run scoped it rather than
guessing at the cost, and the scope is wider than "five call sites" makes
it sound: all three `GeoFeatureModelSerializer`s
(`PropertySerializer`, `ActivitySerializer`, `SightingSerializer`) are
each shared between the authenticated viewset **and** the public site
(`public_site/views.py:106,206,249,265`), so changing what they emit
changes anonymous output too, and re-verification means the public site,
both maps and both form pages in a browser. Still the largest measured
lever with a number attached (868 KB → 62 KB at 10,000 rows), and still
carrying the documented `Meta.geo_field` trap.

**The two compose, which is why they went to the owner together: D36 is
why a rollback wouldn't work, and D37 is why you couldn't attempt one in
the first place.** Neither is live — no rollback has been tried, and the
host is the dev instance.

**A method note worth keeping, because it changed the answer.** D37 was
first derived from `docker-publish.yml`'s tag policy, which says `latest`
on main and semver on a tag — from which the natural conclusion is "only
`latest` exists, for both images." **Querying Docker Hub returned
something different**: the backend also carries two commit-sha tags from
before `type=sha` was removed, and the frontend carries none. The
asymmetry is pure accident, and only looking showed it. Same family as
D28's "read the implementation of what you are enabling" — *read the
registry, not the workflow that writes to it.*

**Named successor:** recovery is now swept for the *deploy* axis but not
the *data* one. D35 established nothing backs the database up; this run
established nothing can put an *image* back. Untouched by either: whether
anything could put a **single record** back. Soft delete covers `Property`
and nothing else, every other delete is immediate and cascading (D34), and
there is no audit log anywhere — so nothing in the app can answer "what
did this row look like yesterday, and who changed it?" The permissions
model assumes multiple editors; nothing records which one acted.

**Refreshed 2026-09-16 (4) (PM check-in).** The queue was empty of
fork-free work for the fifteenth consecutive cycle; this run refilled it
by one. The lens was the successor the last two entries named —
**exposure awareness**, i.e. what the app shows an org about its own
publishing rather than about its records — and it produced **D39** (see
"Logged-in app UX"). **Queue state: one takeable item (D39a), three owner
questions (D39b's Q1/Q2/Q3), and D31's geometry half still takeable but
larger. Recommended: D39a first**, then D39b's Q3.

**Emptied again 2026-09-16 (5) (programmer run), the sixteenth
consecutive cycle.** D39a shipped; D39b's Q1/Q2/Q3 and D31's geometry
half were re-deferred with their reasons (table in `build-questions.md`).
**Two lessons from the build worth carrying:**

1. **A spec that names the states can still name the wrong number of
   them.** "Badge public/private on every row" is two states; the
   two-condition rule has four, and shipping two would have put a
   "Public" badge on records the public site does not serve — a new
   false claim on the very screen built to stop that. The tell was
   asking what the badge *asserts*, not what the field *holds*.
2. **Measure which wrong fix each test stops, don't assert it** (D38's
   correction, re-applied). Both plausible wrong fixes were built. The
   two-state badge fails **7** of 487 unit cases; the guess-on-unknown
   fix fails **3**; the sets are disjoint. The measurement that matters
   is the other direction: **~470 of the cases — every one about
   wording, counting and filtering — pass against a badge that lies.**
   A large green suite said nothing about the defect that mattered.

**And one that is about looking, not testing.** All 30 browser checks
passed while the property-less sighting row rendered
`CrabgrassNot publicNo property — 6/1/2026` on a single line. Opening the
screenshot is what caught it; the run-together was then shown to be
**pre-existing** by hiding every badge and re-reading the row (that row
renders a bare `<div>`, so it never had `.card__link`'s column layout).
Sixth time in this repo's history that reading the image, not the
assertions, found the defect — and the A/B is what kept the fix honest
about whose bug it was.

**The method note that changed this finding's size, and it generalizes:
check how far the capability already goes before sizing the fix.** The
inherited framing ("no inventory anywhere") pointed at a new screen. The
measured answer is that the public/private filter is complete from the
model column through `filter_is_public` to a typed `ListFilter.isPublic`
on the client, and the two pages that need it pass no argument — so D39a
is a badge and an existing parameter. Same family as D22's un-parking
lesson and D38's "check whether the data is already there": **test
whether the absence you are about to build for is actually an absence.**

**A second note, about what argues against your own finding.** The honest
severity here required measuring the thing that makes it *smaller* — the
public site is an unSSR'd SPA with one static title and no inbound links,
so "already indexed" would have been an overclaim. Recorded because a
lens that only collects confirming evidence produces findings that don't
survive the owner's first question.

**Named successor:** exposure is now swept for what the app *shows*. What
no lens has asked is what the app *costs* — Habitat has no notion of a
limit anywhere. There is no quota on photos (D32 measured 52.2 GB/year
for a 25-contributor org), no cap on properties, records, members or
species, no rate limiting (flagged 2026-08-27, never revisited beyond
D17's single endpoint), and no plan, billing or tier concept in the data
model at all. Every prior lens has asked whether a thing works; none has
asked what happens when an org uses a lot of it, or who pays.

**Refreshed 2026-09-17 (PM check-in).** The queue was empty of fork-free
work for the sixteenth consecutive cycle; this run refilled it by one.
The lens was the successor named directly above — **cost, and who pays** —
and it produced **D40** (see "Tech / infrastructure"). **Queue state: one
takeable item (D40a), three owner questions (D40b's Q1/Q2/Q3), plus the
carried-over D39b Q1/Q2/Q3 and D31's geometry half. Recommended: D40a
first**, then D40b's Q1.

**The method note worth keeping, because it un-parked a three-week-old
item.** "Add rate limiting" has sat unqueued since 2026-08-27, parked
explicitly as a design question — *which endpoints, what limits, what
store*. The parking was honest and it was also load-bearing: nobody
re-tested whether all three parts were actually blocked. **They were
not.** Measuring one endpoint answered "which" (login dominates by orders
of magnitude, being the only unauthenticated path running a slow KDF),
D17's own precedent answers "what limit" (a build session picks and
states the constant), and "what store" is answerable today and only
becomes a decision when D5 is. This is D22's un-parking lesson applied a
second time, and it generalizes: **an item parked as "a design question"
should be re-tested for whether every part of it is really blocked — the
parking reason ages, and nobody re-reads it.**

**A second note, about the shape of the fix.** Every prior
resource-exhaustion finding here was fixed by *bounding the resource*
(D17 capped pixels; D30 capped rows; D31 compressed). D40 cannot be,
because the expense **is** the security control — a cheaper password hash
is weaker password storage. When the cost you want to reduce is the thing
protecting you, the only lever left is the rate. Worth checking, on the
next such finding, which of the two shapes it is before reaching for the
familiar one.

**Named successor:** this run swept what a *stranger* can spend. Nobody
has swept what a **legitimate member** can spend on the org's behalf —
and the composition is already half-documented: D32 measured photos at
52.2 GB/year for a 25-contributor org, there is no quota (`limitations.md`
says so), no count cap on properties, records, members or species, and
D35 established nothing backs any of it up. So the open question is not
"can one member fill the database" (they can) but **what an organization
can see or control about its own consumption** — today, nothing: there is
no count of anything anywhere in the backend (`Count`/`aggregate`/
`annotate` appear zero times outside migrations and tests, per D39), so
an org cannot answer "how much are we storing?" any more than it could
answer "what are we publishing?" before D39a.

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


## Build queue state — the standing authorization pays out

**2026-09-17 (programmer run).** The owner's standing authorization
("as I answer, they can be released to build") produced its first items
that actually release work, and this run took all of them:

- **D5's Q2 — the production image.** Answered "yes" to the PM
  recommendation, so released. Built end to end: production stages in
  both Dockerfiles, gunicorn + whitenoise + `collectstatic`, a multi-stage
  `vite build` behind nginx, the dev images kept and selected by
  `target: dev`, and `client.ts` defaulting a production build to a
  relative `/api` so the published image is deployment-neutral.
- **D40a — rate limits on the two hashing endpoints.** Fork-free by the
  ordinary triage rule, and its one entangled sub-question (the throttle
  store) was answered by "Kubernetes, single containers".
- **The support contact.** The hosting answers established that the owner
  operates both deployments, which turns "contact whoever runs this one"
  from a wording choice into a per-deployment config value —
  `HABITAT_SUPPORT_CONTACT`, blank-default so nothing changes by
  upgrading.
- **The "Running more than one replica" section** the Kubernetes answer
  called for, in `deployment-config.md`, naming exactly what has to change
  before `kubectl scale` is safe.

**What this run deliberately did not take**, each re-deferred with its
reason in `build-questions.md`: D37 (whether to cut a version tag is the
owner's, and the *mechanism* is now genuinely ready rather than dormant);
the **CI publish gate**, still formally unanswered and sharper than ever
now that a tag publishes production — a build-only job was added instead,
which validates the images without changing publish behaviour; HSTS and
the `SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair, both now
concrete since prod sits behind the owner's own reverse proxy; D35
(backups, narrowed to prod and made *harder* by self-hosting, not easier);
D36's entrypoint half; D40b's Q1/Q2/Q3; D39b, D38b, D34's soft-delete
half, D32, D31's geometry half, D29, D28's Q1/Q2/Q3, D8's Q1.

**A method note, because it is the second time in three runs:** the
headline defect of this session was found by *reading a real response off
a real server*, not by a failing test. DRF appends its own "Expected
available in N seconds." to a custom throttle message, so the refusal said
the wait twice — and every assertion passed, because each one checks that
some advice is *present*, and nothing that looks for a missing thing can
see a duplicated one. Seventh time in this repo's history that looking,
rather than asserting, caught it.

**Named successor:** with the production image built, the next thing
nobody has examined is what a *release* actually is here. The mechanism
now exists end to end — tag, build, publish, deploy — and has never run
once: zero git tags, zero GitHub releases, no changelog, no version
number anywhere in the repo (`frontend/package.json` says `0.0.0`), and
nothing that tells a running instance which build it is. An operator
standing prod up cannot ask the app what version it is running, and a
rollback (D36) is a procedure with no list of things to roll back to.

### 2026-09-17 (3) PM check-in — that successor was swept, and it was the smaller half

**Result: two new items, D42 and D43** (both under "Tech /
infrastructure" above), and one correction. The framing above is right
that no release has ever run — re-measured, still zero git tags local and
remote, still zero GitHub releases, still `0.0.0`, still no changelog.
But *"nothing tells a running instance which build it is"* turned out to
be **two claims of which only one holds**: the published image does carry
`org.opencontainers.image.revision`/`.version` via `metadata-action`, so
image-level identity exists and only *runtime-queryable* identity is
missing — which folds into D43 rather than standing alone.

**The larger half was not version identity at all.** Asking what a
release actually does on arrival found that the first production boot
**crashloops on a database prerequisite the deployment contract never
states** (D42), and that the obvious Kubernetes health probe **returns
200 forever because it hits the SPA fallback** (D43). Both are
pre-launch, neither is live, and both are cheap.

**Queue state: two takeable items — D42a (documentation only, fork-free)
and D43's endpoint. Recommended: D42a first**, since the owner's stated
next action is the stand-up that D42 blocks. The standing authorization
is still **spent** — no owner answer has been recorded since 2026-09-17,
so nothing here is released to build.

**Both were built the same day by the 2026-09-17 (4) programmer session,
emptying the queue of fork-free work for the eighteenth consecutive
cycle.** Two things that run is worth carrying forward rather than
re-deriving:

- **Measurement changed the design once, mid-build.** The health module
  was first written as DRF views with `renderer_classes([JSONRenderer])`
  pinned so the body could not depend on the caller's `Accept` header. It
  can't — instead DRF answers `Accept: text/html` with **406 Not
  Acceptable**, so a monitor sending a browser-ish Accept header would
  have been told a healthy pod was unhealthy. Leaving DRF's renderer list
  alone instead serves the *browsable-API HTML page* from a health
  endpoint. Both are wrong, and the fix was to stop using DRF for these
  two views at all — which turned out to be the better design for a
  second, larger reason: **a probe should depend on as little of the app
  as possible.** Measured: adding a global `DEFAULT_THROTTLE_CLASSES` of
  5/min to `REST_FRAMEWORK` fails **zero** probe tests, because plain
  Django views never enter DRF's dispatch. The most likely future change
  that would break a probe structurally cannot.
- **A duplicated header is invisible to a suite that checks for missing
  ones.** The frontend `/healthz` block first used `add_header
  Content-Type` on top of a `return` that already sets it, and served
  **two identical `Content-Type` headers** — which RFC 9110 lets a
  recipient treat as malformed, on the one endpoint an intermediary polls
  to decide whether the pod is healthy. Status, body, byte count and
  content type all passed against it. Found by reading the raw headers,
  and CI now *counts* header occurrences rather than matching them. **D40's
  doubled "Expected available in N seconds" in a second place**, and the
  eighth time in this repo's history that looking, not asserting, caught
  it.
- **One wrong fix turned out to be inert rather than wrong**, which is a
  worse outcome and worth recognising by name. "Rate limit the probes with
  `AnonRateThrottle`" reads like a security improvement and throttles
  **nothing at all**: that class reads its rate from
  `DEFAULT_THROTTLE_RATES["anon"]`, which this project does not set, so
  `rate` is None and `allow_request` returns True unconditionally. **D40's
  `NUM_PROXIES` finding — a throttle that refuses nobody — in a second
  place.** Anyone adding a throttle class here must set its rate in the
  same change, and the test that looks like it guards this passes against
  the inert version for the wrong reason (measured: it fails only against
  a throttle with a real rate).

**Named successor, replacing the one above:** every lens to date has
looked at Habitat as *software*. This run was the first to look at it as
*a thing somebody has to stand up*, and found two gaps in the first ten
minutes. The axis is not exhausted — nobody has walked the whole path
from `git tag v1.0.0` to a working login on a new domain and written down
what it takes: DNS, TLS, the database, secrets, the first superuser, the
first organization, and **SMTP, still console-only**, which on a real
deployment means a locked-out user has no self-serve recovery and an
invited member never receives their link. That walkthrough is the
successor; D42 and D43 are simply the first two things it would have
found.

### 2026-09-18 PM check-in — the queue refilled from a *user*, not a lens, for the second time in this project's history

**Result: two takeable items — F1 (user-requested) and D44's docs half —
plus D44's code half, which is takeable once one header check is done.**
The queue had been **empty of fork-free work for eighteen consecutive
cycles**; it is not any more, and the way it refilled is the thing worth
recording.

**The refill did not come from an audit lens.** Eighteen cycles of
lens-driven sweeps had produced no fork-free work; one person using the
app produced a build-ready item in one sentence. That has now happened
**twice** — the other was 2026-09-11 (4), when feedback 13/14 broke a
thirty-one-pull silence. Both times the preceding entries had described
the lens mechanism as spent, and both times what actually refilled the
queue was somebody using Habitat. **The lesson is not that the lenses
are worthless** — they produced D27 through D43, including two live
security-adjacent defects — but that they and real usage find
*disjoint* things, and the project has exactly one source of the second
kind. It is worth more than its volume suggests.

**The method note, because it changed what got recorded:** the feedback
named a page path, so this run went and measured *that photo* rather
than reasoning about photos generally. That produced the number the
whole triage turns on — the grid already downloads 1,899,250 B to paint
a 252×252 crop, so the requested feature costs **zero** additional bytes
(304, 0 bytes, measured) — and it surfaced **D44** entirely as a side
effect, because looking at the real photo meant looking at the real URL.
*Following a report to the specific record it names is not a
formality.*

**Two corrections this run made to its own inherited material,** both
kept because the traps recur: D32's "the deployment holds zero photos"
is false (see the ⚠️ on that item) and the way it was reached — counting
a key that does not exist — is the trap this run also walked into on its
first attempt; and the browser measurement that would have settled
whether `http://` photo URLs break rendering **failed for harness
reasons** (the sandbox proxy could not load the Vite dev server's CSS,
so the SPA never rendered, and a MITM cert needed `ignoreHTTPSErrors` on
`newContext` — the 2026-09-10 lesson). That question is therefore
recorded as *undetermined by direct measurement*, with the feedback item
itself standing as the real-world evidence that browsers rescue it.
Stated plainly rather than quietly omitted.

**Recommended order: F1 first** — it is the only item in the queue a
*user* asked for, it needs no owner input, it costs no bytes, and its
one real risk is scope creep into D32, which the item's own write-up
fences off. Then **D44's docs half** (one sentence, true under every
remedy), then D44's code half once the `X-Forwarded-Proto` check is
done.

**Named successor, unchanged and untaken:** the walkthrough from
`git tag v1.0.0` to a working login on a new domain. D42a and D43 built
two of its steps; DNS, TLS, secrets delivery and **SMTP** remain.

### 2026-09-18 (2) programmer session — both takeable items built; the queue is empty of fork-free work again

**Built: F1 in full, and D44's docs half.** D44's code half is
re-deferred with a reason that is new rather than inherited — the
`X-Forwarded-Proto` check the recommended remedy depends on **cannot be
made from here at all** (with the flag off Django ignores the header, no
endpoint echoes request headers, and the proxy config is outside this
repo), the remedy is a deployment environment variable rather than a repo
change, and the two alternatives each have a real cost — so it is a
genuine fork for the owner, not a thing this session declined to finish.

**The fifty-seventh feedback pull returned `[]`**, both negative controls
re-run (tokenless → 403, wrong token → 403). So F1 stood as the only
user-sourced item, one day after it arrived.

**Two lessons from building F1, both about measurement correcting the
person doing it:**

- **A fix can be *necessary* and still be caught by nothing.** F1's
  keyboard defect got two fixes. Built alone, the focus fix passes the
  entire 40-assertion suite — including every arrow-key test, because
  restoring focus also restores the event path the keys travel. The
  document-level listener is therefore caught by **zero** tests on its
  own, and two attempts to construct a case that would catch it (clicking
  the photo, clicking the control bar) both came back green. It was kept
  regardless, and the reason is specific to this repo rather than
  general: **there is no frontend test runner**, so a red test here is a
  one-off measurement and not a standing guard. Where a suite would
  ordinarily protect an invariant, the code has to. Note this cuts
  *against* D43's "a control that catches nothing may be doing nothing" —
  both are true, and which applies depends on whether anything is left
  watching after the session ends.
- **Two wrong guesses in a row, both corrected by running it.** This run
  predicted the two fixes would be caught by disjoint tests (they are
  nested), and then predicted clicking the photo would strand focus (it
  does not — Chromium keeps focus inside a modal when you click a
  non-focusable child; the strand is specific to an element *leaving the
  focus order*). **D38's standing correction, applied twice in one
  session.**

**And the render was looked at, not just asserted on** — the ninth time
in this repo's history that mattered. The screenshot is what shows the
finding in one frame: the lightbox displays a 3:1 photo's left, middle
and right thirds while the thumbnails below it show only the middle,
which *is* F1's argument. The backdrop's coverage was then checked by
comparing rendered pixels before and after opening (uniform 0.12×
brightness at the top bar *and* the bottom nav) rather than by eye,
because a white page showing through 12% black reads as "bright" in a
screenshot and would have looked like a gap in the backdrop.

**Queue state: empty of fork-free work again**, one cycle after the
user-sourced refill. The standing authorization remains spent. The
takeable-item list is now D44's code half (blocked on an owner answer),
and everything else unchanged.

**Update, 2026-09-18 (3) (programmer session): the queue's one takeable
item (D45a) was taken, and the run went past it.** The docs half was
built as specified, and the guard the check-in flagged "worth considering
in the same pass" was built too, with the naive-fix measurement that flag
explicitly asked for — `apps/accounts/checks.py`, `habitat.W001`, 12 new
tests. The queue is **empty of fork-free work again**, and the standing
authorization remains **spent**: D45b's Q1/Q2/Q3, D44's code half and
D8's Q1 all still need an owner answer.

**Also re-measured this run, read-only, and unchanged:** **D8's Q1 is
still live** — org 2's public payload is still an email-derived
organization name, **twelve days** after D8 recorded it. The address
stays redacted from committed files, same reasoning as D8 itself.
Separately noted, not a defect: **org 1 has been renamed** from `test`
to *"Craven Household"* while its public slug is still `test`, which is
`Organization.save()` working exactly as designed (`if not self.slug`)
and exactly as `organization-admin.md` warns — recorded only so a future
run does not read it as drift, and because the owner may not realise the
public URL did not follow the rename.

A future build session should read `build-questions.md`'s full write-up
before starting this — it has the data-model sketch (a `Page` model,
scope field, landing-page pointer) and the exact remaining sub-decisions,
plus the relocation-scope architecture note above.

### 2026-09-19 PM check-in — the queue refilled by sweeping the successor four entries had named

**One takeable item (D45a), three new owner questions.** The standing
authorization remains **spent** — no owner answer recorded since
2026-09-17, so nothing is released to build.

**The sweep was the one four consecutive entries kept naming** — not "does
Habitat work" but "can somebody other than the owner stand it up," and
specifically its largest named gap: **SMTP, still console-only.** The
queue's framing was that SMTP is *undecided*, a hosting call nobody has
made. True, and the smaller half: there is also a **fork-free defect on
the path to deciding it** (D45a above).

**Two method notes worth keeping, both about what makes a finding
precise rather than merely large:**

- **The clean-audit result was load-bearing, not a footnote.** Measuring
  that a *real* SMTP failure is loud (a visible warning plus traceback on
  stderr, despite no `LOGGING` setting) is what turns "SMTP isn't
  configured" — which the docs already say honestly — into a defect: the
  two adjacent cases have **opposite** signal quality, and the silent one
  is the default. A sweep that had only confirmed the bad case would have
  reported something the manual already covers.
- **Un-parking, fourth application of D22's own lesson.** D22 read this
  exact code and its test comment already names the console-backend
  problem. It fixed what the **user** is told. Nobody asked what the
  **operator** is told. A parking reason ages, and nobody re-reads it —
  here the parked reason was true of the *decision* and hid a *defect*
  beside it. Worth asking of every other item parked as "blocked on an
  undecided question": is *part* of it actually independent?

**Also re-measured this run, read-only, and unchanged:** **D8's Q1 is
still live** — org 2 still publishes an email-derived organization name,
**thirteen days** on. The address stays redacted from committed files,
same reasoning as D8 itself.

**Deployment signal, applied rather than re-learned:** `/api/health/`
still reports `3574e748`, and that is **correct** — the F1 commit was
frontend-only, so the backend image correctly did not rebuild. F1 was
confirmed live the way yesterday's entry prescribed instead: the
Vite-served `PhotoLightbox.tsx` is 28,549 bytes against the 549-byte
SPA-fallback negative control.

**Named successor:** this run swept the **outbound** channel. Nobody has
swept the **inbound** one. Habitat accepts a signup from any address with
no verification of any kind (recorded at `limitations.md:321`, and as
D40b's Q1, still unanswered) — so every account, organization and emailed
link in the system is addressed to a string nobody has ever confirmed
belongs to anyone. D45 asks whether mail *leaves*; the unasked question is
whether the address it leaves for is real, and what that means now that
the reset flow is the only recovery path a locked-out user has.

### 2026-09-20 PM check-in — the successor was swept, and it was again the smaller half

**One takeable item (D46a), one owner question (D46b, which is D40b's Q1
resurfacing with a deadline attached).** The standing authorization
remains **spent** — no owner answer recorded since 2026-09-17, so nothing
is released to build.

**The sweep was the inbound channel, named as successor by the last two
entries.** The queue's framing was that this is an open *decision* —
should signup verify the address (D40b's Q1), with the gap honestly
recorded at `limitations.md:322`. True, and the smaller half: underneath
the decision sits a **fork-free defect**, D46a. Same shape as D45 two
days ago, and as D22 before it — **third consecutive run where the parked
reason was true of the decision and hid a defect beside it.** That is no
longer a coincidence; it is the most reliable way this project has found
new work. Ask it of every parked item.

**Three method notes worth keeping:**

- **Check whether the declared control actually executes.** D46 was found
  by asking not "is there validation?" (there is — `EmailField` carries
  `EmailValidator`) but "does any code path reach it?" (no — nothing
  calls `full_clean()`, and no serializer sees the input). That is the
  **fourth** instance of *a control that is configured and does nothing*,
  after D40's `NUM_PROXIES`, D43's `AnonRateThrottle` and D45's five mail
  variables. Four instances in eight days is a lens, not a run of bad
  luck: point it at anything this repo *declares*.
- **"The browser papers over it" is a claim to measure per case.** D44
  established a browser silently rescuing the user, and it was the honest
  reading there. Measured here in real Chromium, the same instinct is
  **backwards**: `type="email"` refuses every malformed string and
  accepts every mistake a person actually makes — including a domain
  typo, a missing TLD, and a 312-character local part. Don't inherit the
  previous finding's shape; run the cases.
- **Measure what argues against your own finding.** The honest severity
  here required establishing what is *not* reachable — header injection
  (`BadHeaderError`, measured) and XSS (one `dangerouslySetInnerHTML`,
  the sanitized branch) — and that the casing trap a reader would
  suspect first **does not exist**, checked at all four sites rather than
  inherited.

**Also re-measured this run, read-only, and unchanged:** **D8's Q1 is
still live** — org 2 still publishes an email-derived organization name,
**fifteen days** on. The address stays redacted from committed files.

**Deployment signal:** `/api/health/` reports revision `b78e080`,
**byte-identical to `git rev-parse HEAD`** — so the host runs D45's own
commit, and the local measurement transfers to the deployment without
writing anything to it. That mattered here: confirming D46 on the live
host would have meant creating a permanent, unremovable tenant.

**Named successor:** every lens from D40 on has asked what a **stranger**
or an **operator** can do. Nobody has asked what happens when a **member
leaves**. There is no account deletion, no user deletion and no way to
remove an organization (`limitations.md:327`); a *membership* can be
removed but the login survives it; and D38's attribution columns are all
`SET_NULL`, so a departure silently unnames that person's past work
rather than crediting it to someone gone. The unasked question is what an
organization owes a departing contributor, and what it keeps — which is
also the first question a land trust with volunteers will ask.

### 2026-09-21 PM check-in — the successor was swept, and the framing was again the smaller half

**Swept the successor the last three entries named: what happens when a
member leaves.** The queue framed it as an inventory of **absences** — no
account deletion, no user deletion, no way to remove an organization, a
membership removable while the login survives it, `SET_NULL` attribution
that unnames a departing contributor. Every item true, and the framing is
again the smaller half: underneath the missing features sits **D47**, a
defect that needs no policy decision to name, because the app already
refuses to create the state that removal leaves behind. Full bullet under
"Accounts, orgs, and permissions"; measurement table in
`build-questions.md`.

**One inherited claim corrected by measuring it.** The queue said
`SET_NULL` attribution "silently unnames a departing contributor's past
work". It does not: `SET_NULL` fires on **User** deletion, there is no
user deletion anywhere in the app, and removing a *Membership* leaves
`created_by`/`updated_by` intact. Attribution is the one part of
departure that behaves correctly — measured, and recorded so the next
lens doesn't re-file it as a loss.

**Method note, because it changed the answer: check whether an invariant
is *re-checked*, not just whether it is enforced.** The inherited framing
pointed at missing features and would have produced an owner question and
nothing takeable. D47a came from asking a different question of code that
was already correct — *this validator fires on write; what re-runs it?*
Nothing does. Same family as D22's un-parking lesson and D39's "check how
far the capability already goes before sizing the fix".

**Second note, on not adding to the pile:** D47b's Q3 is **D40b's Q2**
re-framed from the person's side rather than the operator's, and is filed
as a sharpening of it, not a new question. A queue that re-asks a
question it already holds spends attention buying nothing.

**Queue state: one takeable item (D47a), three owner questions (D47b),
one of which sharpens an existing one.** The standing authorization
remains **spent**.

**Named successor:** every lens from D40 on has asked what someone *can
do* — a stranger, an operator, a member, a departing member. Nobody has
asked what the app does when a person is **two people**. `User.email` is
the identity, the login, the attribution and the only display name there
is (there are no display names at all —
`docs/manual/limitations.md:189`), and there is **no way to change your
own email** — the Account page holds only "Change password", checked this
run. So a contributor whose address changes has one route, a new account,
which splits one person's attribution across two identities with nothing
connecting them and no way to merge.

### 2026-09-19 programmer session — D46a built; the queue is empty of fork-free work again

**Built: D46a**, the one takeable item the check-in left. New
`apps/accounts/email_addresses.py`; no migration; **293/293** backend
tests (up from 273). Full write-up, the measurement tables and the
re-deferrals are in `build-questions.md`.

**The shipped rule is narrower than the queued one, and deliberately so.**
The item said "all four sites plus `Invitation.email`"; what shipped
validates only the two sites that **store** an address (signup,
member-add) and has the two that **look one up** (login, password reset)
normalize and nothing more. The queued reason for exempting login — that a
distinguishable refusal is an enumeration oracle — is weaker than it
looks, since a malformed address cannot have an account and so refusing it
distinguishes nothing about accounts. The load-bearing reason is
**lock-out**: rows written before today may hold a malformed address, and
a guard on sign-in shuts those accounts out of the only path still open to
them while one on password reset shuts them out of recovery. That reason
covers reset too, which the queued framing did not.

**Two inherited claims were corrected by re-measuring** — both recorded
against the D46 bullet above, and the first is this run's real
contribution: the 312-character witness the trap was written around is
refused by Django's own validator (which caps at 320, not 254), so a test
built on it **passes green against the naive fix** — demonstrated, not
argued. And the over-length case is an unhandled **500** on the real
Postgres column, not the `201` a mirror-model measurement reported,
confirmed against a live server at `DEBUG=0`.

**Queue state: empty of fork-free work.** The standing authorization is
still **spent**. The one owner question this run leaves is **D46b /
D40b's Q1** — whether signup verifies the address at all — and its value
is now higher rather than lower: the manual can finally state the
distinction precisely (format checked, reachability not), which makes
reachability the only part of the gap left open.

**App feedback:** `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **sixty-first** pull, the steady state.
Nothing reported broken on the dev host.

**Named successor, carried unchanged from the check-in and untouched by
this run:** what happens when a **member leaves** — no account deletion,
no user deletion, no way to remove an organization, a membership that can
be removed while the login survives it, and `SET_NULL` attribution that
silently unnames a departing contributor's past work.

## Build queue state — D49a built; the queue is empty of fork-free work
## again, and the fix carried a silent-no-op form inside it

**2026-09-20 (5) (programmer session).** Dev host healthy before and
after; both of D43's probes answer, readiness reports `"database": "ok"`.
**The revision it reports, `0c97b2d`, is correct rather than stale —
verified, not asserted:** `git log -1 -- backend/` is exactly `0c97b2d`
and all three commits since touch only `CLAUDE.md`, `build-questions.md`
and this file. The 2026-09-18 (2) lesson applied rather than re-learned,
for the eighth run running. `GET /api/feedback/pull/` returned `[]` with
both negative controls — the **sixty-seventh** pull. **Nothing reported
broken**, so nothing was escalated as a blocker.

The check-in left exactly one takeable item, **D49a**, and this run took
it. Everything else is re-deferred with reasons in `build-questions.md`.
Every inherited measurement was re-checked against the real code and all
of it reproduces.

**The transferable finding is that the fix had the defect's own shape
inside it.** D49's family is "a control that is configured and does
nothing" — and `clearsessions` is inert on three of Django's five session
backends, exiting 0 and printing nothing on each. Django's
`NotImplementedError` branch handles a case no shipped backend takes. So
the build pinned the *mechanism* (is the configured store one that can
evict?) rather than trusting the outcome tests, which would have gone red
with a message pointing at the wrong thing. **D45's lesson — its own fix
could have re-committed D7's gap — in a second place.**

**And a stand-in under-reported again.** A hand-built session measured
508 B/row; 1,000 written through the real `login()` measured **672 B/row**.
D46 recorded a stand-in that under-reported severity; this is the same
error in a size estimate, and the fix is the same — use the real path.

**Method note: measure which single test stops each wrong fix, not how
many go red.** Three of the eight variants here are caught by exactly one
test, and it is the weakest assertion in the section (a grep over a shell
script). That is an argument for keeping it, not for strengthening it —
nothing else in a Python suite can reach a shell script, and without it a
correct, well-tested command runs nowhere.

**Queue state: empty of fork-free work again.** The standing authorization
remains **spent**. **Recommended next: D31's geometry half** — still the
largest measured lever with a number attached (868 KB → 62 KB at 10,000
rows), and deliberately not squeezed in beside D49a this run: it changes
three `GeoFeatureModelSerializer`s **shared with `public_site`**, so it
alters anonymous output and needs browser re-verification of the public
site, both maps and both form pages. Then **D49b's Q1**, which is a single
value and the only one of the three a user would feel.

## Build queue state — refilled by one takeable item (D49a), and the lens's
## real answer was that the big accumulator is already on the queue

**2026-09-20 (4) (PM check-in).** Dev host healthy; both of D43's probes
answer, readiness reports `"database": "ok"`. **The revision it reports,
`0c97b2d`, is correct rather than stale — verified, not asserted:**
`git log -1 -- backend/` is exactly `0c97b2d`, and the single commit since
touches only `CLAUDE.md`. The 2026-09-18 (2) lesson applied rather than
re-learned, for the seventh run running. `GET /api/feedback/pull/`
returned `[]` with both negative controls re-run — the **sixty-sixth**
pull. **Nothing reported broken**, so nothing was escalated as a blocker.

**This run swept the successor the last three entries named** — what the
app does when nobody does anything for a long time. It produced **D49**
(see "Tech / infrastructure") and, more usefully, a reframing.

**The framing correction: expiry is not eviction.** The queued successor
said *"there is no session expiry setting anywhere."* Measured on the
pinned Django 5.2.17, sessions **do** expire at fourteen days — the
manual documents it accurately — and an expired row does **not**
authenticate. What is missing is eviction: the dead row stays, one per
login, at ~680 bytes, with `clearsessions` (the only cleanup command
Django ships) run nowhere in this repo.

**The ranking, which is the more valuable half.** The lens implied
something significant was hiding among four row-shaped accumulators.
Measuring all of them put the real answer somewhere already recorded: for
a 25-contributor org over a year, **photos are 52.2 GB (D32) against 863
KB of sessions — ~63,000×**, and even an absurd session case is ~900×
smaller. Every row-shaped accumulator in this app, combined, is under a
megabyte a year. **So the thing quietly accumulating is photos, and that
is already D32, already measured, already the owner's fork.** D49a is
worth building because it is one line and closes the last unbounded table
with a shipped remedy — not because the bytes matter, and this entry says
so rather than letting the table imply otherwise.

**Queue state: one takeable item (D49a), three owner questions (D49b),
with D31's geometry half still takeable but larger.** The standing
authorization remains **spent** — no owner answer recorded since
2026-09-17. **Recommended: D49a first** (one line, no decision), then
**D49b's Q1**, the only one of the three a user would feel.

**Method note, because it changed the answer: rank the accumulators
before designing for any of them.** Measuring all of them shrank the new
finding to one line of shell and pointed at an item already on the queue.
Same family as D39's *"check how far the capability already goes before
sizing the fix"* and D48's *"measure the remedy, not just the defect."*

**Named successor:** every lens from D40 on has asked what someone *can
do*, or what accumulates. None has asked **what an organization can see
about itself**. An org cannot answer "how many members, properties,
activities, sightings, photos do we have?" from anywhere in the app —
`Count`/`aggregate`/`annotate` appear **zero** times in the backend
outside migrations and tests (D39 established this for publication
specifically; D39b's Q1 parked the org-wide view). D39a made *exposure*
visible per record; the same argument applies to everything else, and it
composes with D32: an organization storing 52.2 GB of photos a year has
no screen anywhere that would tell it so.

**Still open, deliberately:** **D49b's Q1/Q2/Q3**; D48b's Q1/Q2/Q3; D47b's
Q1/Q2/Q3; D46b/D40b's Q1; D45b's Q1/Q2/Q3; D44's code half; D42b; D37;
whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D40b's Q2/Q3;
D39b's Q1/Q2/Q3; D38b's Q1/Q2/Q3; **D8's Q1** (not re-measured this run —
last confirmed live 2026-09-20 (PM)); D36's entrypoint half; D34's
soft-delete half; D35's substance; **D32** and D30's retention half (now
also D49b's Q2); **D31's geometry half**; D28's Q1/Q2/Q3 and **D29**;
D22's second half; the "super sighting" grouping question; B2 and the
contextual menu; D5's remaining ops steps; D11; due dates on tasks; the D6
backfill query; the org switcher; a real cron for the purge (now also
D49b's Q3); server-side search/pagination; quick-log draft persistence;
the Node 20 pass; rate limiting beyond D40a; the name-uniqueness casing
gap; photo captions/alt text and displaying `captured_at`.

## Build queue state — D48a built; the queue is empty of fork-free work again

**2026-09-20 (2) (programmer session).** Dev host healthy; both of D43's
probes answer, readiness reports `"database": "ok"`. **The revision it
reports, `3e8ee3f`, is correct rather than stale — verified, not
asserted:** `git log -1 -- backend/` is exactly `3e8ee3f`, and all five
commits since touch only `docs/`, `frontend/`, `CLAUDE.md` and
`build-questions.md`. The 2026-09-18 (2) lesson applied rather than
re-learned, for the sixth run running. `GET /api/feedback/pull/` returned
`[]` with both negative controls re-run — the **sixty-fifth** pull.
**Nothing reported broken**, so nothing was escalated as a blocker.

**The check-in left exactly one takeable item, D48a, and this run took
it.** Everything else is re-deferred with reasons in
`build-questions.md`. The standing authorization remains **spent**.

**A latent harness bug found on the way, and it is the more reusable
half of this run.** `capture.js` waited on
`text=are on the public site` before shooting the two list screenshots.
That string only matches the **plural** branch of D39a's exposure line,
and the walkthrough creates exactly *one* activity and *one* sighting —
so the page says *"Your only activity is on the public site."* and the
wait could never succeed. It was added 2026-09-16 by the session that
built D39a, which **did not re-run the script** (its regen allowance was
already spent that day), so it sat broken until this run's regen tripped
over it. **A regen gap means the script rots silently** — this repo's own
2026-09-02 lesson, second instance.

**Loosening it to `text=on the public site` would have been worse, and
that is the part worth keeping.** The Visibility filter's own
`<option>Not on the public site</option>` contains that substring and is
**not** gated on the properties request, so the wait would resolve
instantly and silently stop waiting for the thing it exists to wait for —
a wait that looks correct and observes nothing. **D27's substring trap in
a wait condition**, after D30 found it in a filter and D46 in a witness.
Fixed by scoping to the summary paragraph itself
(`p.muted:has-text("on the public site")`), which is the element the gate
actually controls. Verified end to end: full 21-image run, exit 0.

**Consequence worth recording: `activities-list.png` and
`sightings-list.png` had never been captured with D39a's badges at all.**
The images D39a shipped predate its own UI change, so the chapters have
been describing badges and a Visibility filter that no screenshot showed
since 2026-09-16. Both now show them.

**2026-09-20 (PM check-in).** Dev host healthy; both of D43's probes
answer. **The revision it reports, `3e8ee3f`, is correct rather than
stale, and this run verified that rather than asserting it** —
`git log -1 -- backend/` is exactly `3e8ee3f`, and all four commits since
touch only `docs/`, `frontend/`, `CLAUDE.md` and `build-questions.md`.
The 2026-09-18 (2) lesson applied rather than re-learned, for the fifth
run running. `GET /api/feedback/pull/` returned `[]` with both negative
controls re-run — the **sixty-fourth** pull.

**The lens was the successor the last three entries named — what the app
does when a person is two people — and it refilled the queue by one
takeable item.** See **D48** under "Accounts, orgs, and permissions".

**Queue state: one takeable item (D48a), three owner questions (D48b).**
The standing authorization remains **spent**. **Recommended: D48a
first** — it costs nothing, needs no decision, and corrects a sentence in
the manual that is false today.

**Method note, because it changed the answer: check whether the
capability exists before designing around its absence.** The inherited
framing said there is no display name; the measured answer is that there
is one, on two of three creation paths, with no remedy on the third. The
*direction* is what is new — three of the last four sweeps found a queue
framing that understated a **defect**, and this one found a framing that
understated a **capability**. Both are the same error: describing the
code from the docs instead of from the code. Same family as D22's
un-parking lesson and D39's "check how far the capability already goes
before sizing the fix".

**Second method note: measure the remedy, not just the defect.** The
reassuring assumption here is "an admin can fix it later." Driving the
real endpoints showed `PATCH /api/org/members/<id>/` answering **200**
while ignoring the name, `/api/auth/me/` **405** for every write verb,
and no profile route anywhere — so the honest finding is not "the name
is dropped" but "the name is dropped and nothing can ever put it back."
That is a different item with a different severity, and only the
measurement separates them.

**Named successor:** every lens from D40 on has asked what someone *can
do* — a stranger, an operator, a member, a departing member, a person who
is two people. None has asked what the app does when **nobody does
anything for a long time**. There is no session expiry setting anywhere,
notifications are never purged (D30), invitations expire at 7 days but
expired rows are never cleaned up, soft-deleted properties purge only on
a container boot that may not happen (D36's entrypoint half), and the
only scheduled work in the whole deployment is a 15-minute image refresh.
What does a Habitat instance look like after a year of ordinary use, and
what is quietly accumulating in it?

**Still open, deliberately:** **D48b's Q1/Q2/Q3**; D47b's Q1/Q2/Q3;
D46b/D40b's Q1; D45b's Q1/Q2/Q3; D44's code half; D42b; D37; whether CI
should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D40b's Q2/Q3;
D39b's Q1/Q2/Q3; D38b's Q1/Q2/Q3; **D8's Q1** (re-measured read-only this
run — still live, thirteen days on); D36's entrypoint half; D34's
soft-delete half; D35's substance; **D32** and D30's retention half;
**D31's geometry half**; D28's Q1/Q2/Q3 and **D29**; D22's second half;
the "super sighting" grouping question; B2 and the contextual menu; D5's
remaining ops steps; D11; due dates on tasks; the D6 backfill query; the
org switcher; a real cron for the purge; server-side search/pagination;
quick-log draft persistence; the Node 20 pass; rate limiting beyond
D40a; the name-uniqueness casing gap; photo captions/alt text and
displaying `captured_at`.

## Build queue state — D47a built; the queue is empty of fork-free work again

**2026-09-19 (2) (scheduled programmer session).** The 2026-09-21 PM
check-in left exactly one takeable item, **D47a**, and this run took it.
Everything else in `build-questions.md` is re-deferred with a stated
reason (table in that file's BUILT entry).

**Shipped:** `frontend/src/utils/assignee.ts` (the rule, the four states
and the wording), a `valueLabel` prop on `Combobox`, both of
`TasksPage`'s assignee renderings routed through the helper, and a
remove-member confirm that counts open tasks. **No backend file changed,
no migration.** Suite unmoved at **293/293**; `check` and
`makemigrations --check` clean.

**Two lessons worth keeping, both of which changed the code rather than
just the comment.**

**1. The state that mattered most was not one of the two the queue
named.** D47 is "member" vs. "former member". But `TasksPage` fetches
tasks and members as two concurrent requests and passed
`members.data ?? []`, which makes *not loaded* and *no members*
indistinguishable — so the obvious implementation marks **every** assigned
task "no longer a member" for the length of the fetch. That is strictly
worse than the defect: it lies about everyone in order to stop lying
about one person. Measured, it fails 5 of 51 unit cases, the most of any
variant built. **D39's "unknown has to be a real answer", reached from a
different direction — and the general form is: before consuming a list to
decide something, ask what its empty value means.**

**2. A rendering defect shipped through a green suite, and only looking
found it.** The first working version put the qualifier inside the
Combobox's input, where at 390px it rendered `volunteer@example.com — no
lon`. Every assertion passed, because `inputValue()` returns the whole
value however little of it is painted — *the instrument is blind to the
case under test*, the same family as 2026-09-14's `response.body()` and
2026-09-13's substring filter. An `<input>` clips by construction, so its
visible width can never be relied on to carry meaning: the control now
answers *who* and a wrapping `field-hint` note answers *what changed*.
The browser run was then changed to **measure** `scrollWidth` against
`clientWidth` rather than assert on a string, so the defect has a real
guard rather than a proxy one.

**Five wrong fixes were built and run** (collapse-null-to-empty **5**
red; note-only-in-read-mode **3**; qualifier-only-in-the-control **2**;
borrow the delete dialog's "can't be undone" **2**; qualifier back inside
the input **2**). Stated honestly: **the unit suite did not find the
clipping defect** — the screenshot did, and the two tests that now catch
it were written afterwards and check a string, not pixels.

**Red path, in a real browser.** Against the real pre-fix code, with the
member genuinely removed through the UI, 4 of 24 checks fail and
reproduce D47 verbatim: the Combobox reads empty (placeholder
"Unassigned") while the read-mode text on the **same row** reads
"Assigned to volunteer@example.com". Two controls, one row, two answers.

**Queue state: empty of fork-free work.** The standing authorization
remains **spent**. **D47b's Q1/Q2/Q3 are untouched** — D47a reports the
state and decides none of them.

**Named successor, carried unchanged:** what the app does when a person
is **two people** — `User.email` is the identity, the login, the
attribution and the only display name there is, and there is no way to
change your own email (the Account page holds only "Change password"), so
a contributor whose address changes has one route: a new account, which
splits their attribution across two identities with nothing connecting
them and no way to merge.

**Deployed and confirmed live 2026-09-19 at 22:45:34 UTC**, the first
15-minute boundary after the push; Tests #76 and docker-publish #150 both
green. Frontend-only, so the backend job's steps were **all skipped** and
`/api/health/` correctly still reports revision `3e8ee3f` — the
2026-09-18 (2) lesson applied rather than re-learned, for the fourth run
running. The signal used instead: `/src/utils/assignee.ts` served as a
real **14,348-byte** module against the **549-byte** SPA-fallback
negative control. **Nothing was created or removed on the live host** —
confirming D47a there would mean removing a real member from a real
organization, so the scenario was driven against a local stack and the
live check limited to what can be read.

## Build queue state — D50a built; the queue is empty of fork-free work
## again, and the count that was hardest to get right is the one a control
## can falsify today

**2026-09-21 (3) (programmer session).** Dev host healthy before and
after; both of D43's probes answer, readiness reports `"database": "ok"`.
**The revision it reports, `c1a8256`, is correct rather than stale —
verified, not asserted:** `git log -1 -- backend/` is exactly `c1a8256`
and the one commit since is docs-only. `GET /api/feedback/pull/` returned
`[]` with both negative controls re-run — the **sixty-ninth** pull.
**Nothing reported broken**, so nothing was escalated as a blocker. Local
`main` was **38 behind** at `a3f59b1` while the assigned branch
`claude/adoring-curie-chs4wn` already sat at `origin/main`; moved to
`main` per `CLAUDE.md`'s standing rule, checking
`git rev-parse --abbrev-ref HEAD` rather than only the SHAs — the
2026-09-13 (2) trap, avoided for the thirty-second run running.

**The check-in left exactly one takeable item, D50a, and this run took
it.** Everything else is re-deferred with reasons in `build-questions.md`.

**The method note worth keeping is that re-measuring an inherited
*correction* found it wrong in the direction it had just corrected.** The
check-in's Correction 2 said four screens already render a count; three of
them render it only once the list is narrowed, so the unfiltered state —
the one every visit starts in — showed nothing. Checking a claim that has
already been checked once is not redundant when the first check moved the
answer.

**And the trap that mattered most was a *weaker* version of the one
recorded.** Trap 1 warned that `list.length` becomes a lie the day
pagination lands. Two screens narrow server-side **today**, so the lie is
already one click away — measured on `TasksPage` and `SpeciesPage`, and
the reason those two name what they counted instead of stating a total.
*A future risk is worth checking for a present instance of itself.*

**One harness lesson, recorded because it cost a round trip and is this
repo's own trap in a new place.** The first verification run reported 5
failures on screens where the feature was rendering correctly: the
harness picked the count line by matching the *noun* ("species",
"member"), and each page's intro paragraph contains that word, so it read
the intro and reported the count missing. **D30's over-broad-filter trap
living in a test's own selector** — D30 found a filter that was too
narrow and discarded the thing it existed to inspect; this is the mirror
image, and it is the more flattering failure, because it accuses the code
rather than the harness. The anchored matcher (`^\d+ ` or `^Showing `) is
what a count line actually looks like.

**Queue state: empty of fork-free work again.** The standing
authorization remains **spent**. **Recommended next: D31's geometry
half** — still the largest measured lever with a number attached
(868 KB → 62 KB at 10,000 rows), unchanged by this run; then **D50b's
Q2**, the only queued item that touches D32's 52.2 GB/year.

**Named successor, carried unchanged from the check-in:** every lens from
D40 on has asked what someone can *do*, what *accumulates*, or what an
org can *see*. None has asked what Habitat does when a user is **not
sitting in front of it** — every notification is in-app only (D28/D30),
the bell polls on a 60-second timer and exists only while a tab is open,
mail leaves nowhere (D45), and a task assigned to someone who never logs
in again is seen by nobody.

## Build queue state — refilled by one takeable item (D50a), and the
## lens's real answer was that the capability exists and is pointed at
## refusals

**2026-09-21 (2) (PM check-in).** Dev host healthy; both of D43's probes
answer, readiness reports `"database": "ok"`. **The revision it reports,
`c1a8256`, is byte-identical to `git rev-parse HEAD`** — the host is
running this exact commit, so no staleness question arises this run.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **sixty-eighth** pull. **Nothing reported broken**, so
nothing was escalated as a blocker. Local `main` was **37 behind**;
`git rev-parse --abbrev-ref HEAD` was checked, not just the SHAs — the
2026-09-13 (2) trap, avoided for the thirty-first run running.

This run swept the successor the last three entries named — **what an
organization can see about itself** — and produced **D50** plus two
corrections to the queued framing, which are the contribution.

**Method note, because it changed the answer twice: a grep that returns
zero is a claim about the grep.** The queued sentence — `Count`,
`aggregate` and `annotate` appear zero times — is *literally true* and
materially misleading, because none of those three can see `.count()`.
There are six, and five of them exist to explain why you can't delete
something. **D27's substring trap, D30's over-narrow filter and D46's
vacuous witness, now in a fourth place: the framing of a lens.** That is
the hardest version to catch, because a lens is never run against a
control.

**Second method note, and it is D48's, repeated because it keeps paying:
check how far the capability already goes before sizing the fix.** The
framing named five things an org can't count; three of them
(activities, sightings, species) it already can, because the lists are
unpaginated and four screens already render a count from them. The item
shrank from "build a metrics screen" to "three `.length`s and a line of
copy", plus one genuinely separate question about photos.

**The one line worth carrying forward:** the public organization page
tells an anonymous stranger how many properties the organization has,
and the organization's own Properties page tells its owner nothing.

**Queue state: one takeable item (D50a), three owner questions (D50b).**
The standing authorization remains **spent** — no owner answer has been
recorded since 2026-09-17, so nothing is released to build.
**Recommended: D50a first** (no decision, no backend, no migration), then
**D50b's Q2**, which is the only part of this that touches the 52.2 GB a
year D32 measured. **D31's geometry half remains the largest measured
lever with a number attached** (868 KB → 62 KB at 10,000 rows) and is
unchanged by this run.

**Named successor.** Every lens from D40 on has asked what someone can
*do*, what *accumulates*, or what an org can *see*. None has asked what
Habitat does when a user is **not sitting in front of it** — every
notification is in-app only (D28/D30), the bell polls on a 60-second
timer and exists only while a tab is open, mail leaves nowhere (D45), and
a task assigned to someone who never logs in again is simply never seen
by anyone. The app can record work for a person; it has no way to reach
one.

## Build queue state — the successor was swept, and the channel turned out
## to be the smaller half: there is nothing to send

**2026-09-21 (4) (PM check-in).** Dev host healthy; both of D43's probes
answer, readiness reports `"database": "ok"`. **The revision it reports,
`c1a8256`, is correct rather than stale — verified, not asserted:**
`git log -1 -- backend/` is exactly `c1a8256`, so none of the three
commits since touched the backend. The 2026-09-18 (2) lesson applied
rather than re-learned, for the tenth run running.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **seventieth** pull. **Nothing reported broken**, so nothing
was escalated as a blocker. The assigned branch
`claude/hopeful-rubin-hkonoe` already sat at `origin/main` (`e1d4200`)
while local `main` was **41 behind** at `a3f59b1`; moved to `main` per
`CLAUDE.md`'s standing rule, checking `git rev-parse --abbrev-ref HEAD`
rather than only the SHAs — the 2026-09-13 (2) trap, avoided for the
thirty-third run running.

**This run swept the successor the last four entries named** — what
Habitat does when a user is **not sitting in front of it**. It produced
**D51** and two corrections, and the corrections are the contribution.

**Correction 1, and it reorders the owner's own next action: the queued
framing blames the channel, and the channel is the easy half.** The
framing is that mail leaves nowhere (D45) and the bell is in-app only —
both true. Measured, the deeper fact is that **there is almost nothing to
send.** `Notification.Verb` has exactly **one** member; `notify()` has
exactly **two** call sites, both the same transition; `CHANNELS` is a
pluggable list with one entry. The abstraction anticipated channels and
nobody added events. **So configuring SMTP — D45b's Q1, the owner's
stated next action — would not make Habitat able to reach anyone about
anything that matters.** That is a cheap thing to learn now and an
expensive thing to learn after wiring a mail server.

**Correction 2, the D48 lesson again: check how far the capability
already goes before designing around its absence.** Two things this run
expected to find missing are already built, and both were checked
specifically because they are this repo's most-repeated traps. `purge_at`
is **delivered *and* rendered** — a correct per-property countdown with a
correct singular case — so D28's "delivered, never displayed" does not
apply. And the bell's 20-row window, the never-purged history and the
fact that **Mark all read** clears rows you were never shown are **all
already documented**, precisely, in `tasks.md` and `limitations.md`.
Reporting either as a discovery would have been wrong.

**Method note worth keeping, because it nearly produced a false
negative.** A grep for `60_000` against the deployed, Vite-served
`NotificationsBell.tsx` returned **0**, which reads as "the poll is
gone". esbuild had rewritten the numeric separator to **`6e4`**. This is
the 2026-09-20 (3) lesson (Vite strips comments) one step further:
**a source-string grep against a served module is a comparison with
transformed output, and numeric literals are rewritten too.** The
positive control (`Mark all read`, 1 hit) and the 549-byte SPA-fallback
negative control are what kept it honest.

### 2026-09-23 (2) (programmer session) — D55a built; the queue is empty
### of fork-free work again, and the wording a user reads on the common
### paths turns out to be D21's, not this change's

Read `docs/open-questions.md` and `build-questions.md` per the triage
rule; the check-in below left exactly one takeable item and this run took
it. Everything else is re-deferred with reasons in `build-questions.md`.
Dev host healthy before and after; both of D43's probes answer, readiness
reports `"database": "ok"`, and the revision it names (`9296cb9`) is
**correct rather than stale — verified, not asserted**:
`git log -1 -- backend/` is exactly `9296cb9` and the one commit since
touches only `CLAUDE.md`, `build-questions.md` and this file.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run (tokenless → 403, wrong token → 403) — the **seventy-eighth**
pull. **Nothing reported broken**, so nothing was escalated as a blocker.

**Shipped: three files, frontend only. No backend, no migration, no new
test** — the suite is unmoved at 375/375, the expected baseline, and that
was run rather than asserted.

**Method note 1 — a red assertion is a reason to check the harness
first, and here it corrected the write-up rather than the code.** The
first browser run went 16/21, and all five failures asserted that the
*new fallback wording* reached the user. It does not, and should not:
`handleResponse` wraps every HTTP refusal in an `ApiError` carrying the
server's own `detail`, and a non-JSON 5xx carries D21's `statusFallback`
instead. The new strings are reachable **only** through a dropped
connection, which is the one shape that raises a plain `TypeError`. So
D55a's contribution is that *anything* renders; the wording on the common
paths is D21's, and the harness now drives all three shapes separately
(JSON `detail`, non-JSON 503, aborted request) on each path. Stating this
matters because the natural summary — "these five deletes now say
`Couldn't delete that property.`" — is false for almost every real
failure.

**Method note 2 — check what a layout class actually is before adding a
child to it.** `PropertiesPage`'s row is `.card card--row`, where the
card *is* the flex row (`align-items: center`), not a column containing
one. An error `<p>` added as a third top-level child lands inside its
`space-between` layout. `SpeciesRow` had already solved this by keeping
its error inside the row's first flex child, and `.card__stack` already
exists for exactly that; the fix reuses both rather than restructuring a
shipped row. Verified by measurement, not eye: the row grows 64px → 87px
when the message shows while the Delete button's vertical centre tracks
the row's centre (32 → 44), at both 390px and 1280px.

**Method note 3 — two harness self-inflicted failures worth recording,
because both read as app bugs.** The success-path section deletes real
records, so it destroyed the fixtures a later section needed (fixed by
ordering the destructive checks last); and a run failed at *seeding* with
a `KeyError` that was really **D40's signup throttle** (5/hour) returning
429 — the documented trap, and the throttle lives in `LocMemCache`, so
restarting the backend clears it. `pkill -f` matched its own shell again
(exit 144), the standing trap.

**Queue state: empty of fork-free work again.** The standing
authorization remains **spent**. **Recommended next: D54b's Q1** — is a
passed planned date a concept at all? One product call, unblocks Q2,
independent of the undecided hosting/SMTP question. Then **D55b's Q1**,
which D55a deliberately did not pre-empt.

**Named successor, carried unchanged:** what Habitat is like to use
**without a mouse, a large screen, or good eyesight** — `aria-`, `role=`,
focus management and `alt` text have never been swept as a group.

### 2026-09-24 (3) (programmer session) — D56, D57a, D58a and D59 built;
### the queue is empty of fork-free work again, and the two defects that
### mattered most were invisible to any single-variable measurement

Scheduled "programmer" session. Scheduler assigned
`claude/adoring-curie-hvurix`, which already sat at `origin/main`
(`7fc9adf`) while local `main` was **3 behind** at `54a5537`; moved to
`main` per `CLAUDE.md`'s standing rule, and
`git rev-parse --abbrev-ref HEAD` was checked rather than only the SHAs.
Dev host healthy; both of D43's probes answer, readiness reports
`"database": "ok"`. `GET /api/feedback/pull/` returned `[]` with both
negative controls — the **eightieth** pull. **Nothing reported broken.**

**The check-in left three takeable items and this run took all three,
plus D58's `role="button"` half** — 375/375 backend tests unmoved (run,
not asserted, since "no backend file changed" is a claim worth checking),
`check` and `makemigrations --check` clean against real PostGIS 3.4.2 +
PostgreSQL 16.15, `npm ci`/`tsc -b`/`vite build` clean, and **67 checks
in real Chromium at 390px** against a live stack seeded through the real
API. This is the browser run the check-in explicitly said it had not
done, and it changed the diff twice.

**Method note 1 — the finding that generalizes furthest: a
single-variable revert can be green while the naive implementation is
red.** D56's scroll fix had two defects, and each was measured alone:
reverting only the scroll (`scrollIntoView` instead of setting
`list.scrollTop`) scores **23/23**; reverting only the hover
(`onMouseEnter` instead of `onMouseMove`) scores **23/23**. Only both at
once — which is what anyone would actually write first, and did — goes
red, on **exactly one** check. So this repo's standing discipline of
building each wrong fix and reading what goes red is **not sufficient on
its own**: measuring one axis at a time certified the broken combination
as fine. Build the naive implementation *as a whole*, not a ladder of
single reverts.

**Method note 2 — the sole catcher is a D30-shaped test, and the test
that looks like it guards this passes.** The check that caught the
combination is *"aria-activedescendant changes as ArrowDown walks the
list"*, i.e. a comparison of **successive** values. The check that reads
as the obvious guard — *"the active option is inside the visible box"* —
**passes against the broken build**, because a highlight that never
moved is trivially visible. Asserting a property of one observation
cannot see a value that stopped changing.

**Method note 3 — for D57a, the DOM cannot tell the two fixes apart.**
Measured: after a failed delete, both the real fix and the named wrong
fix (`role="alert"` on the conditionally-mounted error) leave a
`role="alert"` carrying byte-identical text. Whether it is *announced* is
not observable from the DOM at all. The only separation is the
**pre-failure** state — D33's lesson, in a new place.

**Two harness traps, both recorded because both read as app bugs.**
Playwright's glob `*` does not cross `/`, so `**/api/properties/*` never
matched `/api/properties/1/` and a "failed delete" test **really deleted
the fixture** (restored through the app's own Manage → Recently deleted
endpoint, with its activity and sighting intact). The harness now asserts
the interception count before relying on it. And a species hardcoded by
name goes stale the moment a previous run links it, since the panel
filters out already-linked species — it now picks whatever is on offer.

**Deliberately NOT done:** D57b's Q1/Q2/Q3, D58's `onFocus` half, and
D60's Q1/Q2/Q3 — all genuine product forks and the owner's. The other 71
`form-error` sites are untouched: D57a proves the mechanism on the five
paths that matter most, and whether the rest get it in one pass is Q2.

**Recorded, not fixed (out of scope, kept minimal):** once a value is
selected with Enter, DOM focus stays on the `Combobox` input, so clicking
it again does not re-fire `onFocus` and the list does not reopen. Keyboard
users recover (ArrowDown/Enter reopen it). Pre-existing and unchanged by
this work.

**Queue state: empty of fork-free work again.** The standing
authorization remains **spent**. **Recommended next: D60's Q1** — does
Habitat have an accessibility commitment at all? It costs one sentence
and decides whether what remains is a conformance backlog or a handful of
quality fixes. **Named successor, carried unchanged:** what Habitat
assumes about the **network** — `navigator.onLine`, `serviceWorker`,
`localStorage` and IndexedDB are all **0** in `frontend/src`, so a
sighting typed standing in a preserve exists only in React state until
the POST succeeds.

### 2026-09-24 (2) (PM check-in) — queue state

**This run swept the successor the last three entries named** — what
Habitat is like to use **without a mouse, a large screen, or good
eyesight**. It produced **D56–D60**, a large clean-audit inventory, and
two corrections. Dev host healthy; both of D43's probes answer, readiness
reports `"database": "ok"`. The revision it names, `9296cb9`, is
**correct rather than stale — verified, not asserted**:
`git log -1 -- backend/` is exactly that, and the two commits since are
frontend and docs. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **seventy-ninth** pull. **Nothing reported
broken**, so nothing was escalated as a blocker.

**Method note 1 — measure what the app has, not what the queue implies it
lacks.** The inherited framing ("`aria-`, `role=`, focus management and
`alt` text have never been swept as a group") invites the conclusion that
they are absent. Counted: 28 `aria-label`, 10 `aria-hidden` (**all**
correctly decorative), 94 `<label>` (**every one** wrapping its input),
and `alt=` on **every `<img>` in the app**. So this is a well-tended
surface with two specific holes — and one component, `Combobox`, carries
both the best ARIA work in the app and the worst defect this lens found.
The genuine zeros are the findings: `aria-live`/`role="alert"`/
`role="status"` and `aria-activedescendant`/`aria-controls`, all **0**.

**Method note 2 — `aria-current` is emitted, by the library, and a grep
says otherwise.** `aria-current` returns **0** across the frontend, which
reads as "the nav never says which page you are on." Measured against the
**pinned** `react-router-dom` 6.30.4 source rather than recalled:
`NavLink` sets `ariaCurrentProp = "page"` and emits
`ariaCurrent = isActive ? ariaCurrentProp : undefined`. The app does
announce it; the library supplies it. **A false finding was one grep
away** — the D43/D53 family inverted: a control absent from app code and
present in behaviour. *Check the dependency before filing the absence.*

**Method note 3 — a count of one naming mechanism is not a count of
names, and this is D46's trap in the choice of grep.** Only **3 of 9**
`<Combobox>` call sites pass `aria-label`, which looks like six unnamed
controls on a `role="combobox"` input that sits in a `<div>` rather than
a `<label>`. It is not: **7 of the 9 are wrapped in
`<label className="field"><span>…</span>`**, and a `<label>` names its
first labelable descendant at any depth; the other 2 both pass
`aria-label`. **All nine have an accessible name.** The right trap was
identified (accessible naming) and the wrong instrument picked for it —
D27's substring, D30's over-narrow filter, D46's vacuous witness and
D49a's test name, now in the *instrument selection* itself. The tell was
available two steps earlier: the labels audit had already established
that this app names things by wrapping.

**Audited clean, recorded so it isn't re-derived** (each is something a
naive sweep files as a defect, and none is one): `htmlFor: 0` is the
wrong instrument, since all 94 labels wrap; **no `outline: none`
anywhere** in 1,870 lines of CSS, so browser focus rings are intact
app-wide (the commonest defect of this kind, and Habitat does not have
it); landmarks present (`<nav aria-label="Primary">`, 5 `<main>`, 2
`<header>`, 29 `<h1>`), which lowers the cost of the missing skip link
for a screen-reader user though not for a keyboard-only sighted one;
**`prefers-reduced-motion` is absent and that is correct**, because there
are **zero** `transition:` and **zero** `animation:` rules, so filing its
absence would be vacuous; 46 of 49 `font-size` declarations are `rem`
with no root override, so text scales with the user's own preference;
**the palette passes WCAG AA on every pair carrying text**, computed
rather than eyeballed, tightest `--color-muted` at **4.63:1** — so *"good
eyesight"*, the third leg of this lens, is the leg the app already
handles, and "the colours are too light" would have been a wrong finding;
`PhotoLightbox`'s native `<dialog>` + `showModal()` gives the browser
Escape, the focus trap and focus restoration; `BottomNav` is exemplary
(every emoji `aria-hidden`, text label beside it);
`NotificationsBell`'s toggle carries a dynamic unread-count
`aria-label` and its **lack** of `aria-expanded` is deliberately not
filed, since the 60-second poll makes this the one surface where not
announcing a change is right; `BloomRangeFields` is the in-repo precedent
for naming a control *set*; and **the twin divergence on the pinnable
card is clean** — `PropertyMapPage`'s keydown guards with
`e.target !== e.currentTarget` and `PublicPropertyPage`'s does not, which
is D26's shape and **harmless here, verified rather than assumed**,
because the public card contains no nested interactive element while the
authenticated one wraps Edit/Delete in
`card__actions onClick={(e) => e.stopPropagation()}`.

**Stated rather than left to be inferred: no browser run.** Every claim
is from reading code, the stylesheet and the pinned dependency source,
plus arithmetic on the palette. No screen reader was driven, no keyboard
navigation exercised, nothing written to the live instance. The contrast
ratios are exact; the *behavioural* claims (the highlight leaving the
viewport, D58's focus/map disagreement) follow from the code but were not
watched happening, and the fixing session should reproduce each in a real
browser first — the D55 precedent, where a browser run corrected the
write-up rather than the diff.

**The manual needs no correction — and this entry's own first draft got
that wrong.** It claimed `docs/manual/` never mentions a screen reader.
It does, exactly once, at `limitations.md:145-149`, and **accurately**:
the photo-caption bullet says a screen reader "can only announce its
position (*Photo 2 of 3*) and never its content," which is precisely what
`PhotoLightbox` renders. `accessib`, `assistive`, `WCAG` and `keyboard`
appear **zero** times. So the coverage is **accurate but incidental** —
accessibility surfaces once, as a side effect of a photo-metadata
finding, never as a subject. The gap is an **absence**, left for the
fixing session on the D13/D24 precedent, with one note on wording: the
honest bullet is not "Habitat is inaccessible" but the specific measured
thing, since most of what a reader would assume is missing is present.

**Queue state: three takeable items, all fork-free — the first refill in
several cycles.** Recommended order by what each unblocks rather than by
size: **D56** first (self-contained, one component, nine call sites
benefit, and its worst symptom lands on a sighted keyboard user rather
than only on assistive-technology users); then **D57a**, which completes
D55a where it stopped one step short; then **D59**, the smallest, with
its fix already written two files away. **D58's `role="button"`** rides
along with any of them. **D58's `onFocus` half and D60's Q1/Q2/Q3 are the
owner's.** The standing authorization remains **spent**.

**Named successor, spot-measured rather than guessed at.** Eight lenses
running have asked what someone can *do*, what *accumulates*, what an org
can *see*, what reaches a person who is away, what two organizations
share, what the app does with time, what it does when it is wrong, and
now who can use it at all. None has asked **what Habitat assumes about
the network** — which matters because the app is built for someone
standing in a field with a phone, the worst connectivity any user will
ever have. Measured across `frontend/src`: `navigator.onLine` **0**,
`offline` **0**, `serviceWorker` **0**, `localStorage` **0**,
`sessionStorage` **0**, IndexedDB **0**; `retry` appears twice. **Nothing
in the client persists anything, anywhere, and nothing knows whether it
has a connection.** So a sighting typed in a preserve exists only in React
state until the POST succeeds, quick log's draft has no persistence
(already recorded), and the dropped connection is the one failure shape
whose wording D55a actually reaches (a plain `TypeError` rather than an
`ApiError` — see that entry's own correction). The successor question is
whether work logged out of signal survives at all, and it composes with
**D55b's Q1**: *offer to try again* means something very different when
the answer is "you have no signal" rather than "the server returned 503."

### 2026-09-24 (PM check-in) — queue state

**This run swept the successor the last two entries named** — what
Habitat does when it is **wrong**. It produced **D55** plus a correction
to D29's recorded scope, and one correction to this run's own instrument.
Dev host healthy; both of D43's probes answer, readiness reports
`"database": "ok"`, and the revision it names (`9296cb9`) is **correct
rather than stale — verified, not asserted**: `git log -1 -- backend/` is
exactly that, and the four commits since touch only `frontend/`, `docs/`
and the two log files. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **seventy-seventh** pull. Nothing reported
broken.

**Method note 1 — measure what the app *has*, not what the queue already
says it lacks.** This lens could have been answered from the queue alone
(no audit trail, no soft delete outside `Property`, nothing backed up,
last-write-wins) — all true, all already recorded, and inert as a
finding. Measuring the recovery mechanisms that *are* present says
something the absences do not: there is one undo and a message, so the
error message **is** the recovery story — and it is missing on exactly
the five paths that destroy the user's own records.

**Method note 2 — a proximity check is not a containment check, and this
is D27's trap in a new place.** The first sweep read a ±13-line window
around each destructive call and asked whether `catch` appeared in it. It
reported `catch=Y` for three handlers that have **no error handling at
all** — the window spanned the *neighbouring* function, which does. After
D27 found this in a column name, D30 in a filter, D46 in a witness, D49a
in a test name, `Property`'s geometry half in a sibling expression and
D53 inside a guard, this is it in a **context window crossing a function
boundary**, and the failure direction is the reassuring one. Caught only
by reading the handler bodies; the corrected sweep also showed that three
bare `await … .remove()` calls are **not** defects, because the child
component they are passed to owns the `catch` — a sweep that stopped at
the call site would have filed five false instances alongside the five
real ones.

**Method note 3 — re-measure the scope of an inherited item, not just its
claim.** D29 has read as an `ActivityFormPage` problem since 2026-09-13
and is **seven** write sites, whose widest field — an authored page body
— was never named. The claim was right; the blast radius was recorded at
one seventh of its size.

**Queue state: one takeable item (D55a), three owner questions (D55b).**
The standing authorization remains **spent**. **Recommended: D55a first**
— no decision, no migration, no backend change, and it restores the one
recovery mechanism the app relies on to the five places it is missing.
Then **D54b's Q1**, unchanged.

**Named successor:** seven lenses have now asked what someone can *do*,
what *accumulates*, what an org can *see*, what reaches a person who is
away, what two organizations share, what the app does with time, and what
it does when it is wrong. None has asked **what Habitat is like to use
without a mouse, a large screen, or good eyesight** — `aria-`, `role=`,
focus management and `alt` text have never been swept as a group; D47a
already found a rendering defect every assertion passed (a clipped
`<input>`), and both D33 and the photo lightbox recorded that a photo has
no caption or alt text a screen reader could announce. The app is built
for someone standing in a field; nobody has asked who cannot use it
there.

### 2026-09-23 (programmer session) — D54a built; the queue is empty of
### fork-free work again, and the layout worry it raised was pre-existing

Read `docs/open-questions.md` and `build-questions.md` per the triage
rule; the check-in below left exactly one takeable item and this run took
it. Everything else is re-deferred with reasons in `build-questions.md`.
Dev host healthy before and after; both of D43's probes answer, readiness
reports `"database": "ok"`, and the revision it names (`9296cb9`) is
**correct rather than stale — verified, not asserted**:
`git log -1 -- backend/` is exactly that, and the two commits since are
docs-only. `GET /api/feedback/pull/` returned `[]` with both negative
controls re-run — the **seventy-sixth** pull. Nothing reported broken.

**Method note 1 — look at the render, then measure what looking
suggested.** The 21 browser assertions all passed while the 390px
screenshot showed the heading wrapping to two lines with the link on a
third, visibly clumsier than the `Your tasks` sibling it was modelled on.
That *looked* like a regression this change introduced. Measuring the
candidates at the real computed font says otherwise: **230px** available
beside the link, and the **old** heading was **400px** — already wrapping
before the change. The delta is one line for the link, not the wrap.
*Looking found the question; only measuring answered it*, and the answer
reversed the conclusion looking had suggested. Both halves were needed:
the assertions would never have raised it, and the screenshot alone would
have mis-attributed it.

**Method note 2 — a red assertion is the harness until proven
otherwise.** One check failed reporting **zero** `<option>`s on a page
with three `<select>`s. Not an app bug: `ActivitiesPage` gates its filter
block on `!loading && !error && all.length > 0`, and the assertion read
the DOM on `h1` alone, racing the data load. Same shape as the
2026-09-16 (5) `.badge` race. The same trap was then found *latent in a
committed asset* — `capture.js` settled the dashboard shot with a fixed
`waitForTimeout(600)` across four independent fetches, which is how a
regen quietly captures a screenshot missing a section; it now waits on
the section itself.

**Method note 3 — reuse the vocabulary that exists before coining one.**
The queue framed the fix as aligning the heading with the *manual*. A
grep found something better: *"Planned / in progress"* is already the
app's own name for this exact `!is_done` set, in the map legend **and**
in the Status filter on the very page the new link points at. That also
decided the layout trade — a shorter invented heading would fit on one
line and would be a fourth name for a set the app already names twice.

**A doc inaccuracy found by reading the regenerated image**, not by
grepping: `dashboard-populated.png`'s alt text claimed "Recent
activities" listed an activity. It never can in the walkthrough —
`capture.js` creates one not-done activity and that section shows
**done** ones only, so it has read "No completed activities yet" since
Recent went done-only (2026-09-03). Corrected to describe the actual
image.

**Queue state: empty of fork-free work again.** The standing
authorization remains **spent**. **Recommended next: D54b's Q1** — is a
passed planned date a concept at all? One product call, it unblocks Q2,
and it is independent of the undecided hosting/SMTP question. **D51's
Q1** is unchanged behind it. The named successor below is untouched by
this run.

### 2026-09-23 (PM check-in) — queue state

**This run swept the successor the last two entries named** — what
Habitat does with **time**. It produced **D54** plus three corrections,
and one of the corrections is to this run's own working.

**Method note 1 — measure how often the code asks the question, not
whether the feature exists.** The lens could have been answered with
"there is no reporting", which is true and inert. Counting the clock
reads instead gave the finding its shape: **nine** in the whole backend,
six of them stamps, and **all three comparisons are the app's own
housekeeping** — the purge deadline and two token expiries. The app asks
what time it is only to expire things belonging to itself. That framing
is what made the dashboard the place to look.

**Method note 2 — run the app's own logic over a fixture rather than
reasoning about the comparator.** `isUpcoming` is `!is_done`, the sort
is ascending, the cap is five. Reading those three facts suggests "some
overdue items will be mixed in". Running them says something stronger
and exact: with six slipped and two genuinely ahead, **0 of 2 upcoming
items are visible**, because the ascending sort fills the cap from the
stalest end. *The section degrades in exactly the direction that
matters.* The reasoning and the measurement do not agree, and only one
of them is checkable.

**Method note 3 — a grep window that ends mid-block reports an absence
it never looked for.** An early `-A 8` read `Activity.Meta` as having no
`ordering` at all, which would have been D2's shape and a much bigger
claim than the truth (`ordering = ["-recorded_at"]`, one line past the
window). Caught by re-reading the file rather than the grep. D27's
substring trap and D30's over-narrow filter, now in the size of a
context window — and the third run running where auditing the clean case
is what kept a finding honest.

**Queue state: one takeable item (D54a), three owner questions (D54b).**
The standing authorization remains **spent**. **Recommended: D54a
first** — it costs nothing, decides nothing, and it is the *overstating*
caption that the 2026-09-10 (6) entry named as the untried half of D19's
honesty lens. Then **D54b's Q1** (is a passed planned date a concept at
all?), which is one product call, unblocks Q2, and is independent of the
undecided hosting/SMTP question. **D51's Q1** is unchanged and still the
cheapest of the older standing questions.

**Named successor.** Six lenses running have asked what someone can
*do*, what *accumulates*, what an org can *see*, what reaches a person
who is away, what two organizations share, and now what the app does
with time. None has asked **what Habitat does when it is wrong** — there
is no audit trail of *changes* (D38 shipped who created and last edited
a record, deliberately not a history), `ActivityFormPage` still PATCHes
every field from the snapshot it opened with so a colleague's edit is
silently reverted (**D29**, unbuilt), soft delete covers `Property` and
nothing else (**D34**), and nothing anywhere backs up (**D35**). So the
app can tell you *who* last touched a record and can never tell you
*what it said before*. D54's Q3 wants history for reporting; this asks
for it as a correction mechanism — and the two would be the same table.

### 2026-09-22 (2) (PM check-in) — queue state

**This run swept the successor the last four entries named** — what
happens when two organizations need the same thing — and produced
**D53** plus one correction. The correction is to this log's own
bookkeeping, and the finding inverts the successor's own framing.

**Method note 1 — the lens's answer was that the lens was pointed at the
wrong thing, and establishing that took measuring the clean case.** The
framing was that per-org reference lists are the problem. Measured, they
are isolated, correct, and the one change that would alter them reverses
**D24's decided stance**. The app has exactly **two** globally shared
namespaces — `User.email` and `Organization.slug` — and they behave in
opposite ways on collision (refused vs. silently suffixed), both
defensibly. The defect is in a **third** namespace nobody protected.
*Auditing what is clean is what located what isn't.*

**Method note 2 — measure the router, don't reason about its ranking
rules.** Running the real route table through `matchRoutes` produced a
result no reading predicts: the two collisions are **disjoint and
complementary** — `explore` loses a property's root and keeps its
children, `pages` keeps the root and loses the children. The first
reading of this finding had both failing the same way. And the case that
matters most — `pages` serving a *real organization page* with a 200 —
is only visible once you read the resolved `params`, not just which
route won.

**Method note 3 — a running summary can lose a fact the original
recorded.** D8's own bullet has always said renaming *"leaves the
email-derived slug serving"*. Every re-measurement since 2026-09-07
checked the payload's `@` count and reported "an email-derived
**name**", so the slug half quietly dropped out of the running summary
while staying true in the source. This run read the live slug for the
first time: it is reconstructable, and it sits in the one global
namespace. *A fact restated often enough gets shortened; re-read the
original, not the last summary.* The manual, meanwhile, needed no
correction — it already documents the exact two-step remedy and
anticipates this case.

**Queue state: one takeable item (D53a), one owner question (D53b).**
The standing authorization remains **spent**. **Recommended: D53a
first** — no migration, no decision, and it mirrors two siblings — then
**D51's Q1**, unchanged as the cheapest of the standing owner questions
and independent of the undecided hosting/SMTP question.

**Named successor, and it was spot-measured rather than guessed at:**
every lens from D40 on has asked what someone can *do*, what
*accumulates*, what an org can *see*, what reaches a person who is away,
and now what two organizations share. None has asked what Habitat does
with **time**. Every record carries dates — `date_planned`, `date_done`,
`observed_at`, `created_at` — and the backend contains exactly **two**
date-range queries, neither of them about a record's history:
`species/views.py:67-69`'s bloom filter (seasonal, and year-*less* by
construction, since bloom endpoints are stored as MMDD) and
`purging.py:73`'s retention deadline. `TruncYear`, `TruncMonth`,
`ExtractYear`, `date__year` and `__range` appear **zero** times across
the whole backend outside migrations and tests. The dashboard sorts and
displays dates; nothing buckets or compares across periods. So the app
can show you what is planned and what was logged, and cannot answer "what
did we do here last season", "is this working", or "how has this changed"
— and `docs/vision.md`'s subject is *restoration*, which is a claim about
change over time. It records history faithfully and can ask nothing of
it. Composes with D50b's Q1 (no org-wide "what do we have" screen) and
D32 (photos are the one unrederivable record of what a site looked like,
and nothing puts two of them side by side).

### 2026-09-22 (3) (programmer session) — queue state

**Built: D53a** — the one takeable item the check-in above left.
`Property.slug` now carries the reserved-word set its two siblings have,
at both layers. Everything else is re-deferred with reasons in
`build-questions.md`.

**Method note 1 — re-measure against the version that ships, not the one
a fresh resolve gives.** The check-in measured react-router **6.30.6**;
`package-lock.json` pins **6.30.4**. The disjoint-and-complementary
result reproduces exactly on the pinned version, so the finding stands —
but the two numbers are different claims and only one of them is about
this deployment. The 2026-09-05 (4) lesson (a fresh resolve of the same
`package.json` moved 37 packages) in a measurement rather than an image.

**Method note 2, and the one worth carrying: a self-maintaining test can
guard a constant nothing is required to use.** The route-table test
exists so a future `/public/:orgSlug/gallery` cannot re-open D53 in
silence — D28's non-self-maintaining lesson, applied before the fact. Its
first version read the route table correctly and then compared the
parsed segments against `RESERVED_PROPERTY_SLUGS`, and **passed against
the named trap**: swapping the *usage* to `RESERVED_PAGE_SLUGS` leaves
the constant itself correct and simply stops consulting it. That is
D40's `NUM_PROXIES`, D43's `AnonRateThrottle`, D45's mail variables and
D46's unrun validator — "configured and does nothing" — appearing inside
a *test*, where it is harder to see, because the test names the right
thing and asserts a true fact about it. Only building the wrong fix
found it. *Anchor a guard to the behaviour, not to the value the
behaviour is supposed to consult.*

**Method note 3 — the sole catcher was the assertion that looks least
like one.** Four wrong fixes, and the one with exactly one catcher
(reusing the uniqueness message) is caught by a test that checks the
refusal does not contain the word "already". No status code differs, no
row differs; the only thing wrong is that the app tells the admin
something false and unactionable. D49a's "weak and load-bearing are not
opposites", second instance.

**Queue state: empty of fork-free work again.** The standing
authorization remains **spent**. **Recommended next: D51's Q1** —
whether anything other than task assignment should notify, and whether
the irreversible 30-day purge should warn before it fires; the cheapest
of the standing owner questions and independent of the undecided
hosting/SMTP question.

**Named successor, carried unchanged:** what Habitat does with **time** —
see the check-in above for the measurement.

### 2026-09-22 (programmer session) — queue state

**Built: `Property`'s geometry half** — the one item the previous
check-in left recorded-but-unbuilt, and the last of the three geo lists
to stop sending shapes nobody draws. Everything else is re-deferred with
reasons in `build-questions.md`.

**Method note 1 — a derived column is a snapshot, so it goes stale the
moment the row is written to.** The first version annotated
`has_boundary` on every action, which reads as the safer choice ("then it
is always there"). An annotation is evaluated at *fetch* time, so on an
`update` it answered about the row as it was **before** the write: a
PATCH that drew a boundary returned `has_boundary: false`. Found by a
test written for an unrelated wrong fix, not by reading the diff. The fix
inverts the obvious precedence — the serializer prefers the **loaded
column** and asks the annotation only when the column is deferred, since
the loaded value can never be stale. D52's family (a value correct only
on the read path) from a new direction.

**Method note 2 — D27's substring trap, now as a second expression over
the same column.** `has_boundary` compiles to
`"accounts_property"."boundary" IS NOT NULL`, so the annotation mentions
the exact column it exists to avoid reading. Section 15's whole-name
matcher therefore fails against the correct fix **and** passes against
the wrong one — wrong in both directions at once. D27 was a longer column
name, D30 an over-narrow filter, D46 a vacuous witness; this is a second
*expression*. The fix matches the `::bytea` cast that distinguishes
reading a value from testing it.

**Method note 3 — two of five wrong-fix rows first measured a crash, and
the whole run measured nothing at all before that.** Removing a field
from `Meta.fields` while leaving it declared makes DRF refuse outright,
so those rows reported a misconfiguration rather than the variant.
Separately, killing a hung child left its parent loop alive, so two
copies of the harness patched the same files concurrently and produced
five plausible, *identical* rows — a clean-looking result from a dirty
start (D49a's "a uniform result across variants that should differ is the
tell", in a second place). The harness now asserts both files are
byte-identical to a pristine snapshot before patching.

**Stated plainly: the frontend half is pinned by nothing, and the type is
weaker here than D31's.** Measured with a probe carrying its own canary:
on a lean row, plotting it or reaching into `.coordinates` are compile
errors, but **`row.geometry ? … : …` compiles** — and that is exactly
this change's own regression, which would label every property undrawn
in silence. `null` is falsy and testing it is legal TypeScript.

**Two corrections to other queued items, recorded rather than built:**
`captured_at` is a **dead** field (never written anywhere, so displaying
it would display nothing) rather than an undisplayed one, and populating
it is an owner decision with a security dimension; and the Node 20 pass
is blocked on information outside this session's repo scope, with the
in-scope way to settle it recorded.

**Queue state: empty of fork-free work again.** The standing
authorization remains **spent**. **Recommended next: D51's Q1** — should
anything other than task assignment notify, and should the irreversible
30-day purge warn before it fires. It is the cheap half of the standing
successor and does not depend on the undecided hosting/SMTP question.

**Named successor, carried unchanged:** what happens when two
organizations need the **same** thing — every reference list is per-org
and starts empty or from a seeded default, so two land trusts restoring
the same prairie maintain two unrelated species lists, and nothing in the
data model can express that they mean the same plant.

### 2026-09-21 (5) (programmer session) — queue state

**Built: D31's geometry half, and D52, which was found on the way in.**
The check-in before this one left no takeable item and recommended
D31's geometry half as the next thing; this run took it. Everything else
is re-deferred with reasons in `build-questions.md`.

**Method note 1 — re-measure before quoting, and say which fixture.**
D31's inherited figure (6.1 MB → 868 KB → 62 KB at 10,000 activities)
was measured against the live host's real rows. Re-measured here on real
HTTP with 6-vertex polygons: 6.42 MB → 680 KB → **117 KB**. The raw
number reproduces almost exactly; the compressed ones do not, because
what compresses is a property of the coordinates, not of the code. Both
are true of their own fixture. The headline survives either way —
geometry is **82.8%** of the compressed payload here, 92% there.

**Method note 2 — the wrong fix that is invisible in the body was not
the one this session predicted.** The section comment first claimed
`.defer()`-alone was the dangerous one, "catchable only by a query
count". Measured: it is byte-identical to *doing nothing*, which is
exactly why the plain outcome tests catch it first (5 red). The
genuinely invisible variant is **serializer swapped, defer forgotten** —
correct output, every coordinate still read out of Postgres, **1 test
red**. Corrected in place rather than in memory, the standing
D38/D40/D45/D48 direction, now five sessions running.

**Method note 3 — a test that hits an unrelated 500 is a finding, not an
obstacle.** D52 surfaced as three errors in D31's own new section. The
temptation is to work around it (seed a `created_by` and move on); the
D26 precedent says audit the endpoint instead. Stashing the D31 change
and re-running reproduced it, which is what turned "my test is awkward"
into "editing any record logged before 13 September is a 500 that
commits anyway".

**Named successor, carried unchanged from the check-in:** nobody has
asked what happens when **two organizations need the same thing** —
every reference list is per-org and starts empty or from a seeded
default, so two land trusts restoring the same prairie maintain two
unrelated species lists and nothing in the data model can express that
they mean the same plant.

**Queue state after this run: empty of fork-free work again**, with one
new item recorded rather than built — `Property`'s own geometry half,
which needs a database-annotated `has_boundary` first (see D31 above).
The standing authorization remains **spent**. **Recommended next:**
**D51's Q1** (should anything other than task assignment notify, and
should the 30-day purge warn before it fires) — the cheap half of the
successor, independent of the undecided hosting/SMTP question.

**Queue state: no takeable item, and that is the honest answer rather
than a failed run.** *Which* events should notify, and whether an
irreversible purge should warn first, are genuine product forks — a
build session picking them unilaterally is exactly what `CLAUDE.md`'s
boldness carve-out forbids. The standing authorization remains **spent**.
**Recommended next: D31's geometry half** — still the largest measured
lever with a number attached (868 KB → 62 KB at 10,000 rows) and
unchanged by this run; then **D51's Q1**, which is the cheap half of the
successor and does not depend on the undecided hosting/SMTP question.

**Named successor.** Five lenses running have asked what someone can
*do*, what *accumulates*, what an org can *see*, and now what reaches a
person who is away. None has asked what happens when two organizations
need the *same* thing — every reference list in the app is per-org and
starts empty or from a seeded default (species deliberately empty,
workflow states and activity types seeded per org), so two land trusts
restoring the same prairie maintain two unrelated species lists, and
nothing in the data model can express that they mean the same plant.
D24 established the empty species list is a decided stance; nobody has
asked what it costs once there is more than one organization.

### 2026-09-25 (PM check-in) — queue state

Routine "resolve open questions" run, project-manager scope only (its own
trigger: identify, notify, record/queue — don't write, edit or push code,
and don't trigger the next build; no live human joined). Scheduler
assigned `claude/hopeful-rubin-klv4ve`, which already sat at
`origin/main` (`0ede005`) while local `main` was **5 behind** at
`54a5537`; moved to `main` per `CLAUDE.md`'s standing rule, and
`git rev-parse --abbrev-ref HEAD` was checked rather than only the SHAs —
the 2026-09-13 (2) trap, avoided for the forty-fourth run running.

Dev host healthy; both of D43's probes answer, readiness reports
`"database": "ok"`. **The revision it reports, `9296cb9`, is correct
rather than stale — verified, not asserted:** `git log -1 -- backend/` is
exactly `9296cb9` and the commits since are frontend and docs.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **eighty-first** pull. **Nothing reported broken.**

**This run swept the successor the last three entries named** — what
Habitat assumes about the **network**. It produced **D61–D64** and three
corrections, and the corrections are the contribution.

**Correction 1, and it is the framing: the app is not silent about
connectivity — it is inconsistent about it, in the wrong direction.**
The inherited framing (nothing persists, nothing knows whether it has a
connection) is true and invites the conclusion that a dropped connection
is invisible. Measured, the app splits **49 / 8** on `instanceof
ApiError` vs `instanceof Error`, and a dropped connection is a plain
`TypeError`. So the 49 fall to a house string (11 of them *"Something
went wrong."*, four of those the record-creation paths) while the 8 —
including **`useAsync`**, i.e. every load error on all 21 screens — show
the browser's own raw text. ***The register is inversely related to what
the action cost the user.*** See D64.

**Correction 2: an inherited claim about `useAsync` is about the state
update, not the request.** The 2026-09-09 entry records that it "cancels
on unmount"; measured, `AbortController` is **0** app-wide, so the flag
it sets suppresses the `setState` and the request runs to completion.
Correct about React, and not the statement this lens needed.

**Correction 3, small but worth not re-deriving: `retry` is not two
occurrences of one thing.** The inherited spot-check recorded *"`retry`
appears twice"*. Measured, one is a **code comment** about basemap tiles
and the other is a **UI button** — so there is exactly **one** retry
affordance in the whole app, which is D63.

**The sharpest single line, and the one that summarises the posture:**
the only wait Habitat bounds is the one for the **GPS** (10 s and 15 s,
both with error handlers), and every network request is unbounded
(`AbortController` 0, `AbortSignal.timeout` 0). The subsystem that works
with no connection is bounded; the one that does not is not.

**Severity, honestly, including what argues against all of it.** None is
a security defect, an exposure or a 500; nothing already saved is at
risk; a user with signal hits none of it; D62's second trigger
self-heals once the fetch lands; and eighty-one pulls have produced no
complaint. What earns them a record: `docs/vision.md`'s subject works on
their own land and quick log exists for standing in a preserve, so the
app's own use case puts the user where connectivity is worst; and D62 is
a composition of three individually-correct shipped things (D24's inline
species creation, D26's deliberately case-sensitive guard, and the
absence of any draft) that is invisible in the diff of any one of them.
**Not determinable from here:** whether anyone uses Habitat somewhere
with genuinely bad signal. That has to be asked.

**Stated plainly rather than left to be inferred: no browser run.** Every
claim is from reading the code plus a read-only confirmation that the
deployed modules match it — `useAsync.ts` (4,320 B) carries the
`instanceof Error`, `species.ts` (4,587 B) carries the stale `known.find`,
and `QuickLogPage.tsx` (73,695 B) carries **2** occurrences of
`species.data ?? []`, all against the 549-byte SPA-fallback negative
control. The *behavioural* claims (the wedge, the stalled button) follow
from the code and were not watched happening; the fixing session should
reproduce each in a real browser first — the D55 precedent, where a
browser run corrected the write-up rather than the diff. **Nothing was
written to the live instance.**

**The manual needs no correction, and that is the finding's shape**
(D16/D19/D33/D38/D45/D46). `offline` and `connection` appear **zero**
times across `docs/manual/`, so no sentence is falsified; the existing
draft bullets (`dashboard.md:99`, `limitations.md:112`) and the failed-
delete bullet (`limitations.md:239`) are all accurate. The gap is an
**absence**, left for the fixing session (D13/D24), with one wording
note: both draft bullets frame the loss as caused by **backing out**, a
deliberate action, and D62 adds a path where it is the only recovery.

**Queue state: three takeable items, all fork-free — the queue refills.**
Recommended by what each unblocks rather than by size:
1. **D62a** — gate `QuickLogPage`'s detail step on the species fetch and
   stop `noOptionsLabel` claiming an empty list while it is loading.
   `SightingFormPage` is the in-repo precedent, two files away. Smallest,
   and it is the trigger that needs no failure at all.
2. **D62b** — make `resolveSpeciesId` honour its own documented contract
   under retry: on a duplicate-name refusal, re-read the list and match
   rather than propagating a species error onto a sighting save. **Build
   note, and it is the trap:** the re-read match must be
   case-*insensitive*, as the helper already is, or the fix re-forks the
   list on exactly the retry it exists to handle.
3. **D63a** — a Retry on load errors, in the wording `PropertiesPage`
   already establishes. Twenty of twenty-one screens; `useAsync` already
   exposes `reload`.

> ✅ **All three built 2026-09-26** (programmer session). See that day's
> `build-questions.md` entry for the measurements. Three notes worth
> carrying, because two of them correct text above:
>
> - **Build note 2 named the right trap and the wrong place, and only
>   building the variants showed it.** Re-reading *after* a refusal —
>   the literal instruction — leaves the **fork** live, because the
>   backend *accepts* a differently-cased duplicate (201): there is no
>   refusal to recover from, so a catch block never runs on that path at
>   all. Measured over nine cases: pre-fix 3 red, after-400-only **2**,
>   before-create-only **1**, case-sensitive re-read 2. The re-read that
>   closes both retries is the one **before** creating; the one after a
>   refusal earns its place only against a genuine two-client race.
>   D46's shape (a correct observation applied to the wrong option), in
>   a build note.
> - **D63a was 21 sites, not 20, and the fix is a component.** A ternary
>   per screen would have been the same bet this repo keeps losing (D6,
>   D26, D34, D47a, D50a): a copy is only ever as complete as the line
>   the author's eye landed on. `components/LoadError.tsx` owns the
>   sentence and the button, so the next screen that loads something
>   inherits both or neither. Measured in the built bundle: **one**
>   `"Retry"` string literal against **21** `onRetry=` call sites.
> - **A 22nd screen was found during the sweep and it was worse than a
>   missing button:** `DashboardPage` read **no `.error` at all** across
>   four fetches, so a failed properties load reported itself as an
>   answer — *"No properties yet. Draw your first boundary to get
>   started."* on the landing page, with a "+ New property" button under
>   it. D21's false-cause class, and exactly what D50a fixed on
>   `TasksPage`, reached from the other direction: the message that
>   would have contradicted the empty state was never rendered at all.
>   Fixed in the same pass, with the three section empty states guarded
>   on `!error` as well as `!loading`.

**The owner's, and deliberately not defaulted:** D61's Q1 (should a
request time out, and at what — a bound short enough to help in a dead
zone aborts a large upload that would have succeeded); D64's Q1 (should
the app name a connectivity failure at all, given `navigator.onLine`
reports link-layer state and is wrong exactly when it matters); and the
one the other two are downstream of — **does Habitat intend to work
without a connection?** That decides whether the rest is "a timeout and
a retry" or "a sync queue", and it reframes the long-parked quick-log
draft-persistence item. The standing authorization remains **spent**.

**Named successor, spot-measured rather than guessed at:** eight lenses
have now asked what someone can *do*, what *accumulates*, what an org can
*see*, what reaches a person who is away, what two organizations share,
what the app does with time, what it does when it is wrong, what it is
like without a mouse or good eyesight, and now what it assumes about the
network. None has asked **what Habitat is like the second time you use
it** — whether anything the app learns about a person is carried
forward. Measured: `localStorage`/`sessionStorage` **0**, so no filter,
sort, map position, collapsed section or unsent draft survives a reload;
`SpeciesPage`, `ActivitiesPage`, `SightingsPage` and `TasksPage` each
reset every filter on every visit; the map refits its bounds from
scratch; and there is no per-user preference of any kind in the data
model. Every visit to Habitat is a first visit, and nobody has asked
whether that is right.
