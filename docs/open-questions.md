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
  **Left as a question rather than a build item**, unlike the last two
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
