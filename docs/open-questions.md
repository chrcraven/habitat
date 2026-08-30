# Open Questions

A running list of unresolved decisions. This list is expected to grow and
shrink over time — when a question is resolved, move the decision (and
rationale) into the relevant doc (`data-model-notes.md`, `vision.md`, etc.)
and either remove it here or mark it resolved with a pointer.

## Recently resolved

Kept here briefly for context; full rationale lives in the linked docs, not
here.

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
  controls a role can't use. Property scoping
  (`Membership.properties` — leave empty for account-wide, or select
  specific properties to limit a role to just those) is stored and
  editable through the org admin portal, but **not actually enforced
  yet** — every role currently behaves as account-wide regardless of
  which properties are checked (correcting an earlier, inaccurate version
  of this note that claimed it was enforced; `org_scoping.py`'s queryset
  filtering only scopes by organization, never by
  `Membership.properties` — see `docs/manual/roles-and-permissions.md`
  and `limitations.md`, which had this right all along). An org admin
  manages both role and property scope through the in-app org admin portal
  (`/admin`, admin-only) — see `data-model-notes.md`. New members are
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

Nothing currently open here — the three items that used to live in this
section (are planned/done states reserved, task status states, task
notification mechanism) were all resolved 2026-08-29; see "Recently
resolved" above and `data-model-notes.md`.

## Accounts, orgs, and permissions

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
**Still genuinely open:**

- **Provisioning the actual bearer-token secret** (`HABITAT_FEEDBACK_TOKEN`)
  is an ops step outside this repo, not something a build session can do:
  it needs to be set (the same value) in both the target server's
  environment and whichever scheduled routine will call the pull
  endpoint. Not done yet — the endpoint exists and correctly rejects
  every request until that secret is set on the live instance.
- **Which live instance a pull routine targets** — `habitat.dev.cravenator.com`
  is the natural first target (see "Tech / infrastructure" below), but no
  scheduled routine has actually been pointed at it yet.
- **Re-confirmed still missing, 2026-08-30:** a scheduled PM check-in
  called the live `GET /api/feedback/pull/` on
  `habitat.dev.cravenator.com` directly — still returns "no token
  configured." Nothing to build here; this is purely the two-place secret
  provisioning step above, still not done.
- Whether every org member should be able to submit feedback, or just
  admins — built as "every member," per the owner's 2026-08-29 decision,
  but worth re-confirming once this sees real multi-member use.

## Public site storytelling / custom content

Raised 2026-08-29 (owner) — a bigger, multi-part feature, direction
decided but **not built** (deliberately left for a future session — this
one already shipped several other items and this is a substantial chunk
of its own). Full detail lives in `build-questions.md`, which is the
source of truth for this item until it's built and this section can be
collapsed the way the others above were; short version:

- **Authored pages + landing-page pick + "Explore" rename** — pages
  attach to an org and/or a property, authored by logged-in members
  in-app; the current auto-generated public view becomes a built-in
  "Explore" page; the org/property owner picks which page is the public
  landing page. **This first slice is fully decided and build-ready** —
  no open design questions block it.
- **Custom CSS** — constrained theme controls (recommended) vs. a raw CSS
  field; the owner's exact preference between the two is still the one
  open call here.
- **Custom HTML** — must be allowlist-sanitized server-side (e.g.
  `nh3`/`bleach`), never raw/unsanitized, on the shared public origin —
  this is a security requirement, not a style preference; flag back to
  the owner explicitly if literally-arbitrary HTML turns out to be the
  actual ask.
- **Custom scripts (JS)** — the owner has since **parked the isolated-
  origin question**: custom author JS is accepted to co-mingle on the
  app's own origin for now (an informed risk-acceptance, not an
  oversight), given Habitat is effectively single-user/low-multi-user
  today. **Revisit this specific decision** if/when multi-user orgs
  become common or the public site takes untrusted/less-trusted authors —
  the full isolated-origin checklist (separate domain, sandboxed iframe,
  CSP, cookie hardening) is preserved in `build-questions.md` precisely
  so it's a lookup, not a re-derivation, at that point.

A future build session should read `build-questions.md`'s full write-up
before starting this — it has the data-model sketch (a `Page` model,
scope field, landing-page pointer) and the exact remaining sub-decisions.
