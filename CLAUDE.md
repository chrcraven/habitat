# CLAUDE.md

Guidance for Claude Code sessions working in this repository. Read this
first, before the docs in `docs/`, to avoid re-deriving context (and
re-spending tokens) that's already settled. Keep this file current: when a
session makes a decision, resolves an open question, or finishes a chunk of
work, update the relevant section below in the same session.

## What Habitat is

A web app for land management: an individual (starting with the author,
doing native plant restoration on their own property) logs activities and
wildlife sightings against a piece of land; the same data can be shown
publicly. One data model and platform scales from a single yard to a land
trust managing many properties and contributors, eventually with a public
API. Full narrative: `README.md` and `docs/vision.md`.

## Source of truth

- `docs/vision.md` — problem, audience, success criteria.
- `docs/use-cases.md` — concrete stories, referenced as `(a)`, `(b)`, etc.
  throughout the other docs.
- `docs/data-model-notes.md` — the data model, in prose. **Read this before
  touching any model/schema code** — it's more current and more detailed
  than any summary here.
- `docs/tech-stack-options.md` — stack evaluation and the decision.
- `docs/roadmap.md` — phased plan (Phase 0 through Phase 5).
- `docs/open-questions.md` — unresolved decisions. **Check here before
  assuming something is decided.** When a session resolves a question, move
  it from here into the relevant doc's "decided" language and delete it (or
  mark it resolved) here, per that file's own header instructions.
- `docs/manual/` — the **user/admin manual**: how to actually use the app
  (signup, logging activities/sightings, roles, org admin, public site).
  Different audience than the docs above (end users, not
  contributors/architecture) — see "Keep the user manual current" below.

Docs are the durable source of truth for product/architecture decisions;
this file is the fast-load index plus session-to-session working notes.
When they conflict, the dated docs above win — fix this file to match.

## Decided (don't re-litigate — full rationale in the docs above)

- **Stack:** Django + GeoDjango + Django REST Framework, PostgreSQL +
  PostGIS, React + MapLibre GL. See `docs/tech-stack-options.md`.
- **Auth:** email/password for human users; API keys for third-party API
  consumers (Phase 4). No social login yet.
- **Account model:** one account = one organization, always multi-user-
  capable (no separate individual/org account types). Every account gets
  the same org-management UI regardless of headcount.
- **Property:** user-drawn boundary, not tied to legal parcel data. One
  account can hold multiple properties. Each also has its own
  `is_public` flag (default true), separate from the per-record flag
  below.
- **Permissions:** role-based — viewer/editor/admin, fixed set, admin also
  manages org membership — roles scopable to specific properties. Managed
  via the in-app org admin portal (`/admin`, admin-only).
- **Activity record:** drawn geometry (not a point), org-defined status
  workflow (planned/done are the only fixed points), species/treatment
  resolved against the account's own species list, photos stored in DB,
  notes, public-by-default with a per-record private flag.
- **Sighting record:** point location, same account species list, photos in
  DB, notes, public-by-default with a per-record private flag. Separate
  table from Activity (different geometry type, different lifecycle).
- **Sighting ↔ Activity link:** direct many-to-many, not gated behind a
  task.
- **Task record:** optional, simple user-to-user assignment; can reference a
  sighting or activity or nothing. Not required for the sighting-activity
  link.
- **Species list:** account-defined, not an external taxonomy (GBIF/USDA).
- **Photo/media storage:** in the database, not S3/object storage.
- **Rules engine, API, public input:** deliberately deferred to Phases 4-5 —
  do not build automation, webhooks, or public API surface in Phase 1.

## Current phase: Phase 1 — single-user MVP (now actually complete), with
## Phase 2/3 slices pulled forward

Per `docs/roadmap.md`: the author can log their own activities and
sightings; the underlying models are org/multi-user shaped from day one
(org, property, role, task, link). **As of 2026-08-14, the author
explicitly asked for a first slice of Phase 2 (public site) and Phase 3
(member/role management UI) ahead of schedule** — see that session's task
log entry below for what's built. **Same day, a follow-up session closed
out the last real Phase 1 gap:** the sighting↔activity link and Task
model existed since the first backend session but had no API or UI until
then — both are now fully wired up (see that entry). Read as: Phase 1 is
genuinely done, not just "logging works"; Phase 2/3 are no longer
entirely unstarted, but only the specific slices in those entries
exist — don't assume the rest of either phase (e.g. invite-by-email,
multi-property org depth beyond what's noted) is done just because *some*
public-site/member-management code exists now. Still no API (Phase 4) or
rules engine (Phase 4) — those remain untouched.

## Repo layout

- `docs/` — planning docs (see "Source of truth" above), including
  `docs/manual/` — the user/admin manual.
- `backend/` — Django + GeoDjango project (Phase 1 build, in progress).
- `frontend/` — React + MapLibre GL app (Phase 1 build, in progress).
- `docker-compose.yml` — local dev: Postgres+PostGIS, backend, frontend.
- `CLAUDE.md` — this file.

## Keep the user manual current

`docs/manual/` is the admin/user manual — separate from the docs above,
which are for people building Habitat, not using it. **Starting
2026-08-14, every session that changes user-facing behavior (a new page,
a changed permission, a new field on a form, a new toggle, a new
limitation resolved) must update the relevant `docs/manual/` chapter in
the same session** — don't let it drift the way a wiki would. If a whole
new area of the app is added, add a new chapter file and link it from
`docs/manual/README.md`'s chapter list. If a documented limitation gets
resolved, remove it from `docs/manual/limitations.md` as part of that
session, the same way a resolved item leaves `docs/open-questions.md`.

## Working conventions for this repo

- This is a solo-author, docs-first project. Before writing code that
  touches product behavior, check `docs/open-questions.md` — if the thing
  you're about to build is listed as open, either pick the narrowest
  reasonable default and note the assumption in this file's task log, or
  ask, rather than silently deciding for the project.
- Model changes: update `docs/data-model-notes.md` if the implementation
  reveals something the notes got wrong or didn't anticipate — the doc
  should stay accurate to the real schema, not frozen at its Phase 0 text.
- Don't build ahead of the current phase (see `docs/roadmap.md`). It's
  tempting to wire up the rules engine or public API while touching
  adjacent code — resist; note the idea in open-questions.md instead if
  it's non-obvious.
- Update `docs/manual/` alongside any user-facing change — see "Keep the
  user manual current" above.
- Keep `backend/` and `frontend/` runnable via `docker-compose up` — that's
  the expected local dev path given GeoDjango's system-library
  dependencies (GDAL/GEOS/PROJ).

## How to work in this repo (once code exists)

- Backend: `docker-compose up backend db` (or `docker-compose up`), then
  `docker-compose exec backend python manage.py <command>` for
  migrations/shell/tests. See `backend/README.md` for details once it
  exists.
- Frontend: `docker-compose up frontend`, or `cd frontend && npm install &&
  npm run dev` if Node is available locally.
- Tests: backend `python manage.py test` (or pytest if/when adopted);
  frontend test runner TBD.

## Task log

Reverse-chronological. Each entry: what was done, key decisions/assumptions
made along the way, and what's left. Keep entries short — this is a pointer
for the next session, not a full changelog (git history is that).

### 2026-08-14 (3) — Added `docs/manual/`, the admin/user manual

Explicit ask: "make an admin/user manual and keep updated as features are
added." New `docs/manual/` — separate from the existing `docs/` planning
docs (those are for people building Habitat; this is for people using it).
Ten chapters, split by area rather than one giant file: `README.md`
(index), `getting-started.md`, `properties.md`, `activities.md`,
`sightings.md`, `linking-sightings-activities.md`, `species.md`,
`tasks.md`, `roles-and-permissions.md`, `organization-admin.md`,
`public-site.md`, `limitations.md`. Written by reading the actual
frontend pages and backend views/permissions currently in the repo (not
just this task log's summaries), so it reflects real current behavior —
including things like the last-admin-lockout guard, the admin-only photo
delete vs. editor-level upload, and the fact that property-scoped roles
are stored but not yet enforced (called out explicitly in both
`roles-and-permissions.md` and `limitations.md`, not glossed over).
- **Ongoing-maintenance mechanism, not just a one-time doc:** added a
  "Keep the user manual current" section to this file requiring every
  future user-facing change to update the relevant `docs/manual/` chapter
  in the same session, mirroring how `docs/open-questions.md` and this
  task log are already kept live. Added to "Working conventions" and
  "Source of truth" too, and linked from the top-level `README.md`.
- **Not done:** no screenshots (text-only manual); doesn't cover
  self-hosting/deployment (no hosting model is decided yet — see
  `docs/open-questions.md`). Both reasonable follow-ups, not oversights.

### 2026-08-14 (2) — Sighting↔Activity linking + Task assignment, both
### wired up end to end for the first time

Follow-up session, same day — asked to "take another bite of open
items"; offered a shortlist and the author picked this one. Both
`SightingActivityLink` and `Task` have existed as models since the very
first backend session (explicitly named as Phase 1 scope in
`docs/roadmap.md`) but had zero API or UI until now — the biggest gap
between what the docs claimed Phase 1 included and what was actually
reachable in the app.

- **Sighting↔Activity link API**, symmetric from both sides:
  `GET/POST /api/sightings/<id>/links/`,
  `DELETE /api/sightings/<id>/links/<link_id>/`, and the mirror
  `/api/activities/<id>/links/` (same `SightingActivityLink` model, same
  `SightingActivityLinkSerializer` — apps/sightings/serializers.py,
  imported into apps/activities/views.py). `get_or_create` rejects a
  duplicate link with 400 rather than silently no-op'ing. Editor+ can
  create/remove a link (treated as an update to the relationship, not a
  destructive delete — unlike photo delete, which stays admin-only).
  Frontend: new `LinkedRecordsPanel` component, shared by
  `SightingFormPage` ("Linked activities") and `ActivityFormPage`
  ("Linked sightings"), edit-mode only (same gating as `PhotoUploader` —
  nothing to link before the record has an id). Candidates are scoped to
  the same property, since that's the case that's actually meaningful.
- **Task CRUD API + `/tasks` page.** `apps/tasks` gained
  serializers/views/urls for the first time — plain `OrganizationScopedViewSet`
  (same viewer/editor/admin convention as everything else), with
  `assigned_to`/`origin_sighting`/`origin_activity` all validated
  server-side against the caller's own organization (a `validate_*` per
  field on `TaskSerializer`, using the request's active membership).
  `/tasks` page: status filter, a `TaskRow` per task with inline
  assignee/status selects (auto-apply on change, same pattern as the org
  admin portal's member-role select) and a title/description edit
  toggle, plus an add-task form that can optionally tie the new task to
  an existing org-wide sighting or activity. New nav entry (between
  Species and Public site) — task assignment is org-wide, not tied to one
  property, so unlike activities/sightings it earns its own top-level
  page rather than living inside a property's map page.
- **Real bug caught by Playwright, not just read in the diff:**
  `LinkedRecordsPanel`'s "+ Link" picker was a `<form>` nested inside the
  page's own outer `<form>` (`SightingFormPage`/`ActivityFormPage` both
  wrap their whole page in one) — invalid HTML that React flagged as a
  DOM-nesting warning during a live browser run, and that browsers handle
  by silently reparenting, which broke CSS-selector-based interaction
  with the control in practice. Fixed by making the picker a plain `<div>`
  with a `type="button"` + `onClick` instead of a second `<form>` —
  general lesson, not just this component: don't nest a `<form>` inside
  another `<form>` in a page that already wraps itself in one.
- **Not done:** task notifications (assignee has to check the Tasks page,
  nothing pings them); the sighting↔activity link isn't surfaced on the
  public site; task due dates; rules-engine auto-linking (Phase 4, by
  design). All noted in `open-questions.md`.
- **Verified for real:** backend — curl-drove link creation/duplicate-
  rejection/removal from both sides, task creation with a valid assignee,
  the cross-org assignee rejection (assign to a real user who exists but
  isn't a member of *this* org → 400 from the custom validator, not just
  DRF's default PK check), status filtering, and delete. Frontend —
  Playwright end to end: created a task and changed its status inline,
  linked a sighting to an activity from the sighting's edit page and
  confirmed it shows on the activity's edit page too, unlinked from the
  activity side and confirmed it's gone from both, and (the DOM-nesting
  bug above) re-verified after the fix that the picker actually works
  and throws no console warnings. `tsc -b && vite build` and
  `manage.py check`/`makemigrations --check` are both clean.

### 2026-08-14 — Public site (per-property + per-org), org admin portal,
### member/role management, property-boundary auto-zoom fix

Five explicit asks in one session; see `docs/open-questions.md` and
`docs/data-model-notes.md` for the doc-level resolution of each, this
entry is the "what and why" summary.

- **Map auto-zoom bug fix.** `PropertyFormPage` never passed a `bounds`
  prop to `MapCanvas`, so re-opening an *existing* property to edit its
  boundary always opened at the default world view instead of zooming to
  the already-drawn shape (every other page — `PropertyMapPage`,
  `ActivityFormPage`, `SightingFormPage` — already did this correctly).
  Fixed by computing bounds from `existing.geometry` the same way the
  others do. Deliberately did *not* make the map continuously re-fit
  while actively drawing new points — would fight the user's own
  pan/zoom mid-draw; drop-pin/geolocate already handle that.
- **`Property.is_public`, new field (migration
  `accounts/0003_property_is_public.py`), default `true`.** Assumption,
  not previously in `open-questions.md`: on top of Activity/Sighting's
  existing per-record flag, a property now has its own — needed once a
  public site existed to show *something*, because an org managing one
  public property (a preserve) and one private one (the manager's own
  yard) needs to keep the latter off the public site entirely, not mark
  every record on it private one at a time. Exposed as a checkbox on
  `PropertyFormPage`, default checked.
- **Public site — two page shapes, both unauthenticated, new
  `backend/apps/public_site/` app mounted at `/api/public/`:**
  per-property (`/public/properties/<id>` — boundary, public activities,
  public sightings, photos) and per-organization
  (`/public/org/<id>` — portfolio of that org's public properties). Every
  query filters to `is_public=True` (property *and* record), and a
  private/nonexistent ID 404s rather than 403s so a guessed ID can't even
  confirm something exists. Reused the existing
  Property/Activity/Sighting serializers for the data itself; wrote
  separate `PublicActivityPhotoSerializer`/`PublicSightingPhotoSerializer`
  only because the `url` field has to point at the new AllowAny photo
  image endpoints, not the session-gated ones the authed serializers
  point at. Frontend: `PublicOrganizationPage`, `PublicPropertyPage`,
  `PublicHeader` (brand + "Log in" link back to the real app — the
  explicit ask that the public site have "a method to get to the
  backend/login"), `PublicPhotoGrid` (read-only photo grid, no
  upload/delete). Both routes sit outside `RequireAuth`/`AppShell` in
  `App.tsx`. Linked from the logged-in app's nav as "Public site" (opens
  in a new tab — different audience, not a page *in* the authed app) and
  from the org admin portal. **No slug/vanity URL** — plain numeric IDs
  for now, noted as a follow-up in `open-questions.md`.
- **Org admin portal (`/admin`, admin-only) + member/role management
  API.** New `OrganizationDetailView` (GET/PATCH org name) and
  `MembershipViewSet` (`/api/org/members/`) in `apps/accounts`: list is
  open to any member, create/update/delete require admin. **Decided
  (asked the user explicitly): a new member is added by the admin typing
  an email + setting an initial password themselves** (shared out of
  band), not a real email-invite flow — no email backend is configured
  in this project, and building one was judged out of scope for this
  session. If the email already has a Habitat account elsewhere, the
  existing user is attached to this org instead of erroring (consistent
  with the data model already supporting multi-org membership). Role and
  property scope (`Membership.properties` — modeled since Phase 1 but
  never reachable from any UI) are both editable per member, enforced by
  the existing `org_scoping.py` machinery. **Last-admin safety:** both
  demoting and removing an org's only remaining admin are rejected
  (400), so an org can't lock itself out — verified by hand (curl) that
  self-demotion fails while you're the last admin, succeeds once a
  second admin exists, and that a non-admin's role/delete calls 403.
  `/admin` is a route *inside* this app, not a link to Django's own
  `/admin` — chosen because it's automatically scoped to the caller's
  own org the same way every other page here is, where Django admin
  would need per-org queryset filtering bolted on to do the same thing
  safely, and this is also where org rename naturally lives alongside
  member management.
- **Not done:** real email-invite flow; a member can't change their own
  password after an admin sets it; sighting↔activity link isn't surfaced
  on the public site; sensitive-species-aware visibility defaults;
  slug/vanity public URLs. All added to `open-questions.md`.
- **Verified for real:** installed GDAL/GEOS/PostGIS system packages and
  a local PostgreSQL 16 + PostGIS 3 in this sandbox (none of that
  survives between sessions — next session will need to redo this, same
  as the very first backend session), ran `migrate` against it, and
  curl-drove the full new surface by hand: public org/property/activity/
  sighting endpoints (including the private-property-404s-not-403s
  behavior), org rename, add-member (both brand-new-email and
  already-has-an-account paths), role/property-scope updates, and every
  last-admin-lockout guard. Then Playwright end-to-end at a 390px
  viewport against the live backend: logged in, saw "Public site"/"Admin"
  nav links appear, confirmed the property-edit auto-zoom fix visually
  (boundary now fills the map on open instead of the world view), added
  a member through the admin portal UI and saw it appear in the list,
  then in a second unauthenticated browser context loaded the public org
  page → clicked into the public property page → confirmed the activity,
  sighting, and "Log in" link all render, and confirmed a private
  property's public URL shows a "isn't public, or doesn't exist" message
  instead of any of its data. `tsc -b && vite build` and
  `manage.py check`/`makemigrations --check` are both clean.

### 2026-08-07 — Device geolocation: drop-pin boundary drawing + opt-in
### "show my location"

- **Boundary drawing by dropping pins at the device's actual position**,
  in addition to tapping the rendered map: `ActivityFormPage` and
  `PropertyFormPage` (same drawing pattern in both, so both got it for
  consistency) now run a continuous `navigator.geolocation.watchPosition`
  (`hooks/useWatchPosition.ts`) the whole time the page is open, and a
  "📍 Drop pin here" button adds the current position as the next vertex.
  Tapping the map still works and the two methods can be mixed freely
  (verified — see below). This is for the "walk the property, drop a pin
  at each corner" workflow; it's distinct from `utils/geo.ts#getCurrentPosition`,
  the sighting form's single-shot "use my location" button.
  - Every dropped/tapped vertex now also gets its own small marker
    (`ensureCircleLayer` on a new per-point source) — previously, with
    fewer than 3 points, the draw preview showed nothing at all (a polygon
    needs 3+ points), so there was no feedback after the first tap or two.
  - `useWatchPosition` is always-on for the two *drawing* pages (that's
    the point of being there) but **opt-in** on `PropertyMapPage` (a
    *viewing* page) via a new "Show my current location on the map"
    toggle, default off, alongside the existing "show private records"
    toggle — per the explicit ask that this "should only be necessary on
    create/edit" for the always-on version.
  - Shared rendering: `mapLayers.ts#ensureUserLocationLayer` draws a
    halo+dot "you are here" marker, deliberately a different color/style
    from sightings' plain blue circles so the two don't get confused when
    both are visible on `PropertyMapPage` at once.
- **Real bug found and fixed by testing on-device-sized viewports, not
  just reading the diff:** adding a third button ("Drop pin here") to the
  bottom map-overlay row put it directly under MapLibre's attribution
  control (bottom-left, same corner) — Playwright's click reported the
  attribution's inner div "intercepts pointer events" over roughly the
  left third of the button. Fixed by raising `.map-overlay--bottom`'s
  `bottom` offset in index.css. (MapLibre's `compact: true` attribution
  renders as an already-expanded pill in this environment rather than a
  collapsed icon — possibly a headless/no-hover-state quirk; the fix
  doesn't depend on figuring out why, it just gives the button row
  permanent clearance either way.)
- **Verified for real:** Playwright with `context.geolocation` +
  `permissions: ['geolocation']` mocking a fixed device position — drop-pin
  button starts disabled and enables once the mocked position arrives;
  dropping a pin and then tapping the map to add more points both
  contribute to the same shape (mixed workflow); vertex markers render
  immediately; the property view page's location toggle actually flips
  the checkbox and (same code path as the already-verified public/private
  toggle) drives layer visibility.
- **Not done:** no accuracy-radius circle around the "you are here"
  marker (it's a fixed decorative halo, not tied to
  `GeolocationCoordinates.accuracy`); no auto-recentering of the map as
  the user's position updates while drawing (they can already tap
  MapLibre's own geolocate control, top-right, to jump to their location).

### 2026-08-07 — Edit/delete, role-based permissions, public-default
### visibility, photo upload

- **Role enforcement (resolves the CRUD half of "Exact role definitions"
  in open-questions.md):** capabilities are now viewer = read only,
  editor = read/create/update, admin = also delete. Enforced backend-side
  in `apps/accounts/org_scoping.py` (`OrganizationRolePermission`, applied
  via `OrganizationScopedViewSet`, plus `ensure_role()` for the
  function-based photo views) — the frontend only *hides* controls the
  user can't use (`frontend/src/auth/roles.ts#roleAtLeast`), it doesn't
  enforce anything on its own.
  - **Assumption:** `Membership.role` now defaults to `viewer` (was
    `admin`) — "minimal permissions until expanded by admin". Signup still
    explicitly grants the account creator `admin` over their own new org
    (unchanged); any *other* membership (today only creatable via Django
    admin — there's still no invite flow, that's Phase 3 per
    `docs/roadmap.md`) starts at viewer. Property-level role scoping
    (`Membership.properties`) is still unenforced — every role here is
    account-wide; add scoping alongside the real invite/role-management UI
    rather than bolting it on now.
  - Migration: `accounts/0002_alter_membership_role.py`.
- **Edit/delete**, all role-gated: Property, Species, Activity, and
  Sighting all now support update/delete via the API (ModelViewSet gave
  this for free) and the frontend (new Edit links + confirm-then-delete
  buttons throughout). `PropertyFormPage`/`ActivityFormPage`/
  `SightingFormPage` were each refactored into an outer
  data-loading component + an inner form that takes an `existing` record —
  handles both the `/new` and `/:id/edit` routes from one file.
  `usePolygonPoints` grew an `initial` param to seed the vertex list from
  an existing geometry.
- **Public-by-default record view:** `GET /activities/` and `/sightings/`
  take `?is_public=true|false`; `PropertyMapPage` defaults to `true`
  (public only) with a "Show private records too" toggle. This is
  visibility *within your own org's app*, not the unauthenticated Phase-2
  public page — is_public still just decides what *that* page will show
  once it exists.
- **Photo upload:** `ActivityPhoto`/`SightingPhoto` now have real
  endpoints — `GET/POST /api/activities/<id>/photos/`,
  `DELETE .../photos/<id>/`, and `GET .../photos/<id>/image/` (raw bytes,
  session-cookie authenticated, used directly as an `<img src>`; same-site
  cookies flow to it because the frontend dev server and backend are both
  `localhost`, just different ports — see the view's docstring if that
  ever needs to be a real cross-site setup). Upload is multipart
  (`MultiPartParser`), capped at 8MB/file with an image-content-type
  check; `DATA_UPLOAD_MAX_MEMORY_SIZE`/`FILE_UPLOAD_MAX_MEMORY_SIZE` raised
  to 10MB in settings.py (Django's 2.5MB default was too small for a phone
  photo). Frontend: `PhotoUploader` component (thumbnail grid + a
  `capture="environment"` file input), shown only on the *edit* forms
  (photos are nested under a saved record's id, so there's no upload UI on
  the create forms yet — create, then edit to attach photos).
- **Verified for real:** backend — a fresh curl pass proving role
  enforcement (viewer 403s on write, editor 403s on delete, admin
  succeeds), photo upload + byte-for-byte image retrieval, and the
  `is_public` filter. Frontend — Playwright end-to-end: property rename
  persists and re-prefills; activity edit reloads the original drawn
  shape correctly (`usePolygonPoints`'s `initial` seed); photo upload
  shows a thumbnail; delete (property, activity, sighting) removes the
  record and updates the list; the private-by-default toggle actually
  hides/shows the private sighting; and a `viewer`-role account sees zero
  edit/delete controls and zero FABs anywhere in the UI, confirming the
  frontend's role gating matches the backend's actual enforcement.
- **Not done:** invite flow / member management UI (Phase 3, per
  `docs/roadmap.md` — an admin can only create a second Membership via
  Django admin right now); property-level role scoping; photo upload on
  the *create* forms (edit-only for now); Activity↔Species linking is
  still read-only (carried over from last session).

### 2026-08-07 — Phase 1 API + mobile-first frontend (auth → property →
### activity/sighting logging flow works end to end)

- **Backend:** added the first real REST API surface (`/api/...`), session-
  auth only (email/password login, decided — no API keys until Phase 4).
  - `apps/accounts`: `POST /auth/signup` (creates User + Organization +
    admin Membership in one step — this is the actual onboarding path for
    a solo homeowner, not just admin/createsuperuser), `login`, `logout`,
    `me`, `GET /auth/csrf` (sets the cookie the SPA needs before its first
    POST — see the module docstring in `apps/accounts/views.py`), plus
    `PropertyViewSet`.
  - `apps/species`, `apps/activities` (`ActivityViewSet`,
    read-only `WorkflowStateViewSet`), `apps/sightings` (`SightingViewSet`)
    — each scoped to the caller's organization via a shared
    `OrganizationScopedViewSet` base (`apps/accounts/org_scoping.py`).
  - **Assumption, not yet in open-questions.md:** a user's *first*
    Membership is treated as their one active organization context —
    there's no org switcher. Fine for Phase 1 (one org per user in
    practice); revisit if/when a user belongs to more than one org.
  - Geometry fields serialize as GeoJSON via `djangorestframework-gis`
    (`GeoFeatureModelSerializer`) — added to `requirements.txt`. Frontend
    sends/receives plain GeoJSON geometries directly.
  - **Scoped out for this session:** Activity's species (M2M through
    `ActivitySpecies`, which has its own role/quantity/detail fields) isn't
    writable via the API yet — `.set()` doesn't work against a custom
    `through` model, and building the nested-write endpoint felt like its
    own chunk of work. `ActivitySerializer.species_names` is read-only for
    now. Sighting's species (a plain FK) *is* fully wired up. Next session
    should add real Activity↔Species write support (probably a small
    nested serializer + explicit create/update handling in the view) if
    that's needed before Phase 2.
  - **Verified for real, not just "looks right":** installed GDAL/GEOS/PROJ
    + a local PostgreSQL 16 + PostGIS 3 in the sandbox (no Docker daemon
    available here), ran `migrate` against live PostGIS, and drove the
    entire API by hand with `curl`: signup → CSRF → create property with a
    drawn boundary → list properties → workflow states → create species →
    create activity (polygon) → create sighting (point) → me → logout (then
    confirmed `me` correctly 403s). All passed. `manage.py check` and
    `makemigrations --check` are also clean.
- **Frontend:** rebuilt as a real mobile-first app (react-router-dom added;
  this was previously just a bare map shell).
  - Structure: `api/` (typed fetch client + CSRF handling), `auth/`
    (session context + route guard), `components/` (`MapCanvas` — the
    MapLibre wrapper, `AppShell`/`TopBar`/`BottomNav`), `hooks/`
    (`useAsync`, `usePolygonPoints`), `pages/` (Login, Signup, Properties
    list, Property new/map, Activity new, Sighting new, Species), `utils/
    geo.ts` (bbox math, geolocation wrapper).
  - **No drawing library** (mapbox-gl-draw/terra-draw etc.) — polygons are
    drawn by tapping the map to add vertices (`usePolygonPoints` +
    `MapCanvas`'s `onClick`), with Undo/Clear buttons. Simple, no extra
    dependency, and touch-friendly by construction. Revisit only if this
    proves too limited (e.g. editing an existing shape's vertices).
  - **Map zooms to fit the property** (the specific ask this session):
    `MapCanvas` takes a `bounds` prop and calls `fitBounds` when it
    changes; `utils/geo.ts#polygonBounds` computes it from the property's
    GeoJSON boundary with no turf dependency. Used on the property map page
    and pre-applied on the activity/sighting draw pages so drawing starts
    already zoomed to the right property.
  - Nav is a bottom tab bar on narrow viewports, repositioned to a left
    sidebar at `min-width: 768px` (see `.app-nav` in `index.css`). Only two
    top-level areas (Properties, Species) — activity/sighting logging lives
    inside a property's own map page (FAB buttons) rather than getting its
    own nav entry, matching Phase 1's scope.
  - **Verified for real:** `npm run build` (tsc + vite) is clean, and the
    entire flow — signup → draw+save a property → map zooms to it → draw
    an activity → capture a sighting (tap-to-place, no location permission
    needed) → both show up correctly positioned on the map and in the
    lists below it — was driven end to end with Playwright at an iPhone-12
    viewport against the live backend above, with screenshots at each
    step. Also checked the same flow renders correctly in the desktop
    sidebar layout at 1280px.
  - Two real bugs the browser run caught (fixed, not just noted): (1)
    MapLibre's default attribution control anchors bottom-right, the same
    corner as the FAB buttons — it was silently eating taps on
    "+ Activity"/"+ Sighting" once expanded; moved it to bottom-left
    (`MapCanvas.tsx`). (2) The activity form's `date_planned`/`date_done`
    side-by-side field row pushed the second date input off-screen on a
    390px-wide phone; `.field-row` now stacks below `480px`.
  - **Not done yet:** editing/deleting properties, activities, or
    sightings (create + list only); Activity's species picker (see backend
    note above); photo upload (both models support it server-side —
    `ActivityPhoto`/`SightingPhoto` — but there's no upload endpoint or UI
    yet); no frontend test runner configured; no `.env`/`VITE_API_URL`
    documented for a non-localhost deploy. Bundle-size warning from
    `maplibre-gl` on `npm run build` (~1MB unminified-gzip) — fine for now,
    code-splitting the map page would be the fix if it matters later.

### 2026-08-07 — Initial backend + frontend scaffolding, CLAUDE.md

- Added this file.
- Scaffolded `backend/`: Django project (`config/`) + apps `accounts`
  (custom email-based User, Organization, Property, Membership),
  `species` (account-defined Species list), `activities` (Activity,
  ActivityPhoto, ActivitySpecies through model, WorkflowState),
  `sightings` (Sighting, SightingPhoto, SightingActivityLink),
  `tasks` (Task). Models follow `docs/data-model-notes.md` directly;
  see model docstrings for field-level notes/open questions.
- GIS fields use GeoDjango (`PolygonField` for activity geometry,
  `PointField` for sighting location), SRID 4326.
- Photos stored in DB as `BinaryField` + content-type, per the decided
  storage approach — no external object storage or filesystem `MEDIA_ROOT`
  use for these.
- `WorkflowState` is per-Organization with `is_planned`/`is_done` boolean
  flags rather than a fixed enum, per the org-defined-workflow decision.
  **Assumption (not yet in open-questions.md as resolved):** a brand-new
  Organization gets seeded with a default 3-state workflow
  (Planned → In Progress → Done) via a `post_save` signal / data migration,
  so a solo user isn't forced to configure a workflow before logging their
  first activity. This answers one bullet under "Data model" in
  `docs/open-questions.md` — revisit if that default set turns out wrong.
- Scaffolded `frontend/`: Vite + React + TypeScript + MapLibre GL, with a
  minimal map view as the starting shell. No API integration yet — backend
  has no REST endpoints exposed yet either (DRF is installed but no
  serializers/viewsets/urls beyond Django admin).
- Added `docker-compose.yml` (postgis/postgis image + backend + frontend)
  and `backend/Dockerfile` so GDAL/GEOS/PROJ system deps don't have to be
  installed on the host.
- Verified the backend actually works, not just "looks right": installed
  Django + GDAL/GEOS system libs in the sandbox, ran `manage.py check`
  (clean) and `manage.py makemigrations` for real — it generated correct
  migrations for all 5 apps with no errors. Migration files are committed.
  Frontend: `npm install && npm run build` (tsc + vite) succeeds cleanly.
  Neither was run against a *live* Postgres/PostGIS instance (none
  available in this sandbox) — that's still untested.
- **Not done yet:** `migrate` against a live DB (do this first next
  session — `docker-compose up` then
  `docker-compose exec backend python manage.py migrate`); DRF
  serializers/viewsets/API urls; auth wiring (djoser or hand-rolled);
  frontend-backend integration; tests; admin site polish beyond basic
  registration; frontend has no linting configured yet. Next session should
  confirm `docker-compose up` + `migrate` works end to end, then build the
  activity-logging flow (create property → draw activity geometry → save)
  since that's the core of the Phase 1 MVP.
