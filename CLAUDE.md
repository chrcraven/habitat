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
then — both are now fully wired up (see that entry). **2026-08-26 added a
real org-invite-by-email flow** (see that entry) — a brand-new member now
gets an emailed accept link rather than an admin-set password, though
real email *delivery* still isn't configured (see `open-questions.md`).
Read as: Phase 1 is genuinely done, not just "logging works"; Phase 2/3
are no longer entirely unstarted, but only the specific slices in these
entries exist — don't assume the rest of either phase (e.g.
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

The manual's screenshots (`docs/manual/images/`) are generated by a
checked-in, reusable Playwright script — `docs/manual/screenshots/capture.js`
(setup instructions in that directory's `README.md`). **When a UI change
makes an existing screenshot stale, update `capture.js` to match** (it's
a project asset to maintain, not a scratch script to throw away after one
session) so the *script* is never left out of date. Confirmed working end
to end as of 2026-08-14 in this project's sandbox environment
specifically — see that session's task log entry for the exact setup
steps that got a live backend+frontend+PostGIS running here, since
`docker-compose` alone doesn't work in this sandbox (see the script's
README for why and the fallback).

**Actually *running* `capture.js` and committing refreshed PNGs is
capped at once a day, not once a session** (decided 2026-08-14, after
the first couple of sessions that did it made the cost obvious):
spinning up a full backend+frontend+PostGIS stack just to regenerate
images is expensive relative to the size of most single-session UI
changes, and most individual changes don't visibly move an existing
screenshot anyway. So: keep `capture.js` itself accurate every session
that needs it, but only actually run it and commit new PNGs **once
per calendar date**, covering whatever's accumulated since the last
run — check `git log -1 --format=%cd --date=short -- docs/manual/images/`
before running it again same-day. If a change makes a screenshot
actively *wrong* (not just slightly stale — e.g. a renamed button the
screenshot still shows, a removed page) and today's regen already
happened, say so in the task log entry rather than running it twice in
one day; the next day's regen (or the next session that touches
screenshots) picks it up. Manual *text* isn't subject to this cap — it's
cheap to edit and stale/wrong prose is worse than a slightly-outdated
screenshot, so keep updating chapter text in the same session per the
rule above regardless of when screenshots last ran.

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

- Backend: `docker-compose up backend db` (or `docker-compose up`) applies
  any pending migrations automatically on container start (see
  `backend/entrypoint.sh`) — no separate manual `migrate` step for normal
  dev. After changing models, still run
  `docker-compose exec backend python manage.py makemigrations` yourself
  (entrypoint only *applies* migrations, it doesn't generate them), then
  restart/recreate the backend container to pick them up. Use
  `docker-compose exec backend python manage.py <command>` for
  shell/tests/one-off commands. See `backend/README.md` for details once it
  exists.
- Frontend: `docker-compose up frontend`, or `cd frontend && npm install &&
  npm run dev` if Node is available locally.
- Tests: backend `python manage.py test` (or pytest if/when adopted);
  frontend test runner TBD.

## Task log

Reverse-chronological. Each entry: what was done, key decisions/assumptions
made along the way, and what's left. Keep entries short — this is a pointer
for the next session, not a full changelog (git history is that).

### 2026-08-26 (2) — CI: build/publish Docker images to Docker Hub

Explicit ask: "docker build and publish using GitHub action to a docker
hub repo." Added `.github/workflows/docker-publish.yml` — a matrix job
that builds both `backend/Dockerfile` and `frontend/Dockerfile` and
pushes them to Docker Hub as `chrcraven/habitat-backend` and
`chrcraven/habitat-frontend` (namespace/two-images/trigger choices
confirmed with the author rather than assumed). Triggers: push to
`main` (tags `latest` + short commit SHA), a `v*.*.*` tag push (adds a
semver tag), and `workflow_dispatch` for a manual run. Uses
`docker/login-action` + `docker/metadata-action` + `docker/build-push-
action` with GitHub Actions layer caching (`type=gha`, scoped per
image so backend/frontend caches don't collide).
- **Requires two repo secrets that this session could not create**
  (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` — a Docker Hub access token,
  not the account password): documented in a comment at the top of the
  workflow file. The workflow will fail at the login step until those
  are added under Settings → Secrets and variables → Actions.
- **Deliberately just a publish step, not a hosting decision** — the
  Dockerfiles it builds are the same dev-oriented ones
  `docker-compose.yml` already uses locally (frontend still runs `npm
  run dev`, not a production build behind e.g. nginx); see the note
  added to `docs/open-questions.md`'s "Hosting/ops model" entry. Didn't
  build a production-mode frontend Dockerfile (multi-stage build +
  static server) as part of this — that's a real follow-up if these
  images are meant to actually run somewhere, but it's a separate,
  bigger decision than "wire up CI to publish what already exists."
- **Not verified against a live Docker Hub push** (no credentials
  available in this sandbox to actually exercise the login step) — the
  workflow YAML was reviewed by hand against the `docker/*-action`
  versions' documented interfaces; the first real push will be the
  actual end-to-end test, once the two secrets above are added. `sh`-
  level syntax isn't applicable here (it's YAML/Actions config, not a
  script), so there's no local equivalent to `manage.py check` to run
  against it.
- **Not done:** no separate workflow for pull-request-only build-
  without-push validation (a PR currently doesn't get an image-builds
  check); no image scanning/SBOM step; no multi-arch (amd64+arm64)
  build — single-platform (the GitHub-hosted runner's native arch) for
  now.

### 2026-08-26 — Real org-invite-by-email flow (Phase 3)

Explicit ask: "continue the match to the next phase." A re-read of
`docs/roadmap.md`/`open-questions.md` against what's built found Phase 2
essentially complete (see 2026-08-25 entries below) and the biggest
remaining, concretely-scoped Phase 3 gap called out repeatedly in this
log and in `open-questions.md`'s "Auth and API" section since 2026-08-14:
adding a brand-new member meant an admin setting their initial password
directly and sharing it out of band. Replaced that with a real invite:
an admin still fills in the same "Add a member" form, but a brand-new
email now gets a pending `Invitation` and an emailed accept link instead
of an admin-chosen password.

- **Backend:** new `Invitation` model (`apps/accounts/models.py`) — org,
  email, role, property scope (M2M, mirrors `Membership.properties`),
  `invited_by`, an unguessable `token` (`secrets.token_urlsafe`),
  `accepted_at`, and a 7-day expiry via an `is_expired` property (no
  scheduled cleanup job — an expired-but-unaccepted row just stops being
  acceptable, same as a revoked one). `MembershipViewSet.create`
  (`POST /api/org/members/`) now branches: an email that already has a
  Habitat account is attached immediately as before (no invite needed,
  they can already log in); a brand-new email creates an `Invitation`
  and calls `send_invitation_email` instead of creating the `User`
  itself. New admin-only `GET/DELETE /api/org/invitations/(<id>/)` to
  list/revoke pending ones, and public (`AllowAny`)
  `GET /api/invitations/<token>/` (preview: org name/role/email, 404 on
  bad/expired/accepted — same "don't confirm what's behind an ID" stance
  as the public site) + `POST /api/invitations/<token>/accept/` (creates
  the `User` + `Membership` together, logs them in — the "join an
  existing org" counterpart to `signup`'s "create a new org").
- **No real email delivery is decided yet** (tied to the still-open
  "Hosting/ops model" question) — `EMAIL_BACKEND` defaults to Django's
  console backend (env-var overridable to real SMTP), so the invitation
  email typically won't actually arrive anywhere yet. Rather than block
  the whole feature on that, `InvitationSerializer.accept_url` is always
  returned by the API and always shown in the admin UI with a **Copy
  invite link** button — the same "share this yourself, out of band"
  fallback the old password-based flow relied on, just a link instead of
  a password now. `send_invitation_email` catches and logs its own
  failures rather than 500ing the request, for the same reason.
- **Frontend:** `AddMemberForm` on `OrgAdminPage` dropped the "Initial
  password" field entirely; a new "Pending invitations" section (between
  Members and Add-a-member) lists each pending invite with Copy-link and
  Revoke actions. New `/accept-invite/:token` route + `AcceptInvitePage`
  (outside `RequireAuth`, like `/login`/`/signup`) — previews the org/role,
  collects name + a new password, and calls a new `acceptInvitation` on
  `AuthContext` (same shape as `signup`: sets the session and logs in).
  A bad/expired/used token shows one friendly error rather than the raw
  404 detail text.
- **Real bug caught by testing at a phone viewport, not just reading the
  diff:** the pending-invitation card's two actions (Copy link + Revoke)
  overflowed the card on a 390px viewport — every other `.card__actions`
  user in this app has only one button and fit fine, so `.card__row`
  never needed to wrap before. Added a `.card__row--wrap` modifier
  (`flex-wrap: wrap`, same idea as `.activity-species-add`'s existing
  wrap rule) rather than changing `.card__row` globally.
- **Docs:** `docs/manual/organization-admin.md` (rewrote "Adding a
  member" + new "Pending invitations" section),
  `docs/manual/getting-started.md` (new "Joining an existing
  organization" section + screenshot), `docs/manual/limitations.md` and
  `docs/manual/README.md` (both had explicit "no real invite flow"
  language — replaced with "the flow exists, real email delivery
  doesn't"). Moved the resolved open question from `open-questions.md`'s
  "Auth and API" list into "Recently resolved," and added a new "Auth and
  API" bullet for the email-delivery gap this still has (also blocks a
  "forgot password" flow, noted there too).
- **Screenshots:** updated `capture.js`'s org-admin step to actually
  invite a member first (so "Pending invitations" has something in it),
  and added a new step that opens the resulting accept link in a second,
  unauthenticated browser context (`AcceptInvitePage` redirects an
  already-authenticated session away, so the main walkthrough page can't
  be reused for it) for a new `accept-invite.png`. Ran it for real — first
  regen today (last was 2026-08-25), so within the once-per-calendar-date
  cap; `org-admin.png` would otherwise have gone from slightly-stale to
  actively wrong (it showed a password field that no longer exists).
- **Verified for real:** installed GDAL/GEOS/PostGIS system packages and a
  local PostgreSQL 16 in this sandbox (same fallback prior sessions
  documented), ran `manage.py check`/`makemigrations`/`migrate` clean
  (one new migration, `accounts/0004_invitation.py`), then curl-drove the
  full surface: existing-email immediate-attach still works, new-email
  invite creation (confirmed the console-backend-logged email body
  matches the returned `accept_url` exactly), duplicate-pending-invite
  rejection, admin-only list/revoke (403 for a non-admin, 204 + gone from
  the list for an admin), the accept endpoint (weak-password rejection,
  successful accept creates the user/membership/session together,
  re-accepting the same token 404s, an already-existing email at accept
  time 400s), property-scoped invitations carrying their scope through to
  the resulting membership, and a bad token 404ing on the preview
  endpoint. Frontend: `tsc -b` and `vite build` clean. Playwright
  end-to-end (mobile viewport, two browser contexts — admin and invitee):
  signed up as an org, invited a new email, confirmed the pending
  invitation card and the "Invitation sent" banner, opened the accept
  link in a fresh unauthenticated context, joined, confirmed the invitee's
  session/org/role, confirmed the admin's reloaded member list shows them
  as an accepted member with the pending entry gone, created and revoked
  a second invitation, confirmed a bad token shows the friendly error
  page, and (the real bug above) confirmed the pending-invitation card's
  two buttons render on-card instead of overflowing after the CSS fix.
- **Not done:** no resend for an expired/still-pending invitation (revoke
  + re-invite covers it manually); no scheduled cleanup of
  expired-and-never-accepted `Invitation` rows (harmless clutter, not a
  security issue — an expired token already fails to accept); real SMTP
  configuration (env vars exist, nothing sets them yet); "forgot
  password" reset flow (same missing email infrastructure).

### 2026-08-25 (3) — Phase 2 map now distinguishes planned vs. completed work

Explicit ask: "Force phase 2 where we have not yet" — a re-read of
`docs/roadmap.md` against what's actually built turned up one concrete,
still-open piece of Phase 2 despite the public site otherwise being live
(2026-08-14 entry below): the roadmap's map-based-view goal explicitly
calls for "visually distinguishing planned/upcoming work from completed
work," and both `PropertyMapPage` (authenticated) and `PublicPropertyPage`
(public) were still rendering every activity in one flat orange fill
regardless of status — the workflow-state name was there in the record
list below the map, but nothing on the map itself. Closed that gap.

- **Backend:** `ActivitySerializer` gained a read-only `is_done` field
  (`source="status.is_done"`) alongside the existing `status_name` —
  deliberately just the one boolean, not also mirroring `is_planned`:
  treating every not-done state (including an org's custom "In Progress"-
  type states) as "not done yet" for this purpose avoids taking a side on
  the still-open "are planned/done-equivalent states reserved" question
  (`docs/open-questions.md`). No migration — derived from the existing
  `WorkflowState.is_done` field, not a new column.
- **Frontend:** `mapLayers.ts#ensureActivityStatusLayers` replaces the
  single fill+line pair with two filtered fill/line layer pairs (done
  vs. not-done) — MapLibre doesn't support data-driven `line-dasharray`,
  so a dashed "not done" outline needed two real layers rather than one
  data-driven one. Done = solid green, not-done = dashed orange. New
  shared `ActivityStatusLegend` component (a small map-corner overlay)
  explaining the two styles, added to both `PropertyMapPage` and
  `PublicPropertyPage` — same visual language on both, per
  `open-questions.md`'s now-updated "Recently resolved" note.
- **Real bug found (and fixed) while verifying this, not otherwise
  related to the styling work:** `MapCanvas`'s bounds-fitting effect
  gated on `map.loaded()` (whether the *current viewport's tiles* have
  finished loading) and, when false, registered `map.once("load", fit)`.
  `"load"` only ever fires once per map. `PropertyMapPage` renders
  `MapCanvas` immediately and fetches the property separately (unlike
  the form pages, which already wait for their `existing` record before
  rendering); by the time the property fetch resolved and `bounds`
  became non-null, the map's one-shot `"load"` event had already fired
  and been consumed on mount, so that new `.once("load", fit)`
  registration would wait forever — the map silently stayed at its
  default world-view zoom, forever, for exactly the page that most needs
  to show a zoomed-in property. Confirmed with `git stash` that this
  predates this session (not something the map-styling change
  introduced). Fixed by tracking "has the style's one-time load event
  already fired" in its own ref (`loadedRef`), independent of the
  tile-loading-state `loaded()` check, and gating on that instead.
  Re-verified the property/activity/sighting *drawing* pages (which
  don't hit this race, since they already wait for their existing record
  before mounting the map) still auto-zoom to an existing boundary
  correctly after the fix.
- **Docs:** updated `docs/manual/properties.md` (map legend under
  "Viewing a property") and `docs/manual/public-site.md` (same, for the
  public property page) with the new planned/done map styling.
  `docs/open-questions.md`'s "Recently resolved" public-site bullet now
  notes the map styling as the piece of Phase 2 that closes.
  `docs/manual/screenshots/capture.js` didn't need changes — it doesn't
  select on layer colors, so the existing steps still work; **did not**
  re-run it and regenerate PNGs this session, since
  `docs/manual/images/` was already regenerated once today (the
  password-change session, entry below) and the once-per-calendar-date
  cap applies. `property-map-with-records.png` and `public-property.png`
  are now slightly stale (flat orange fill vs. the new done/planned
  split) but not *wrong* — the activities/boundary they show are still
  accurate — so this is exactly the "leave it for the next regen" case
  the cap's own carve-out describes, not a reason to run it twice today.
- **Verified for real:** installed GDAL/GEOS/PostGIS system packages and
  a local PostgreSQL 16 in this sandbox (same fallback prior sessions
  used), ran `manage.py check`/`makemigrations --check` clean (no schema
  change, as expected), then curl-drove a fresh org/property/two
  activities (one per each of the seeded Planned/Done workflow states)
  and confirmed `is_done` comes back correctly on both the authenticated
  `/api/activities/` list and the public
  `/api/public/properties/<id>/activities/` endpoint. Frontend: `tsc -b`
  and `vite build` clean. Playwright end-to-end against the live
  backend: confirmed the map on both `PropertyMapPage` and
  `PublicPropertyPage` renders the dashed-orange/solid-green split with
  the legend visible (screenshotted both), and — after finding and
  fixing the `MapCanvas` bug above — that the authenticated page's map
  now actually zooms to the property (it silently didn't, before the
  fix, confirmed via `git stash` on the same test). Also re-verified the
  property/activity edit (existing-boundary) pages still auto-zoom
  correctly post-fix.

### 2026-08-25 (2) — Activity↔Species write support (role/quantity/detail)

Closed the last real gap called out repeatedly in this log since the very
first API session (2026-08-07): `ActivitySpecies` (the through model
linking an Activity to one or more Species, with `role`/`quantity`/
`detail` per species) had existed since Phase 1's first backend session
but was API-read-only — `ActivitySerializer.species_names` could only
*display* names, because Django M2M `.set()` doesn't work against a
custom `through` model and nested-write handling was scoped out at the
time. This was the one concrete "not done" item from that session that
never actually got picked up in any later one.

- **Backend:** new `GET/POST /api/activities/<id>/species/` and
  `PATCH/DELETE /api/activities/<id>/species/<link_id>/`
  (`activity_species_list`/`activity_species_detail` in
  `apps/activities/views.py`, `ActivitySpeciesSerializer` in that app's
  `serializers.py`) — same shape as the existing Sighting↔Activity link
  endpoints (`activity_links`/`activity_link_detail`): a plain
  function-based view pair rather than a nested serializer, editor+ to
  create/update/remove (treated as an update to the relationship, not a
  destructive delete — same convention as the sighting/activity link),
  `get_or_create` rejects a duplicate species-on-this-activity with 400,
  and the species argument is validated against the caller's own
  organization (404s, not 400s, on a cross-org id — matches
  `_get_activity_in_scope`'s existing pattern). `ActivitySerializer.
  species_names` is unchanged and stays read-only — it's a display
  convenience now backed by the same M2M, not the write path.
- **Frontend:** new `ActivitySpeciesPanel` component (own file, not
  folded into `LinkedRecordsPanel` — this one needs role/quantity/detail
  per row, not just a label + unlink button), shown on
  `ActivityFormPage` in edit mode only (same gating as `PhotoUploader`/
  `LinkedRecordsPanel`) between the Photos and Linked-sightings sections.
  Each linked species is its own card with inline role/quantity/detail
  controls that save immediately on change (`api.activities.species.
  update`, auto-apply — same convention as the org admin portal's
  role selects and `TaskRow`'s inline fields) and a Remove button; an
  "add species" row below picks from the org's species list, filtered to
  exclude species already linked (same `options` convention as
  `LinkedRecordsPanel`), as a `<div>` not a nested `<form>` (that
  session's DOM-nesting lesson still applies — this panel also lives
  inside `ActivityFormPage`'s own outer `<form>`). Also added the
  `species_names` summary (already served by the API, previously
  unused in any UI) to each activity's row on `PropertyMapPage`'s list —
  "Species: X, Y" — since there was no reason to leave it invisible now
  that the underlying data is actually populated through the app.
- **Docs:** updated `docs/manual/activities.md` with a new "Species"
  subsection under "Editing an activity". No `open-questions.md` change —
  this was a task-log-tracked implementation gap, not a listed open
  product question.
- **Verified for real:** installed PostGIS + GDAL/GEOS system packages
  and a local PostgreSQL 16 in this sandbox (same fallback prior sessions
  used — the `libmysqlclient21` package `libgdal34t64` depends on 404'd
  from the `noble-security` pocket specifically; pinning the older
  `noble`-pocket version, `8.0.36-2ubuntu3`, unblocked the rest of the
  install). `manage.py check` and `makemigrations --check` both clean (no
  model change this session — the model already existed). curl-drove the
  new endpoints directly: create/list/duplicate-rejection(400)/patch/
  delete, confirmed `species_names` on the activity reflects live
  additions, a viewer-role 403 on POST, and a cross-org species id 404.
  Frontend: `tsc -b && vite build` clean. Playwright end-to-end (mobile
  viewport, live backend): signed up, added two species to the org list,
  drew a property and an activity, opened the activity's edit page,
  added both species with different roles/quantities/detail text, edited
  one's quantity inline, removed the other, reloaded the page and
  confirmed the remaining link and its edited quantity persisted
  server-side (not just local state), and confirmed the property page's
  activity list shows the "Species: …" summary. No console errors beyond
  the expected aborted-basemap-tile noise (see prior sessions) and no
  React DOM-nesting warnings.

### 2026-08-25 — Self-service password change (`/account`)

Picked up from `docs/open-questions.md`'s "Auth and API" list: a member
added via the org admin portal (admin sets their initial password
directly, no email invite flow — see that session's entry above) had no
way to change it themselves afterward. Closed that gap.

- **Backend:** `POST /api/auth/change-password/` (`change_password` in
  `apps/accounts/views.py`, same module as the other auth views) —
  requires the caller's current password (`check_password`, rejects with
  400 if wrong — stops a hijacked-but-not-logged-out session from locking
  the real owner out), validates the new one through Django's standard
  `validate_password`, then `set_password` + `update_session_auth_hash`
  so the request doesn't invalidate the caller's own session mid-flow.
  Uses the existing `IsAuthenticated` default permission — no new
  permission class needed.
- **Frontend:** new `/account` page (`AccountPage.tsx`) — just the
  password-change form for now, not a broader account-settings page
  (name/email editing wasn't asked for). Reachable two ways: the
  caller's email in `TopBar` is now a link to it (desktop/tablet widths
  only — `.top-bar__email` is `display:none` below 480px, an existing
  rule), and a new "Account" entry in `BottomNav` alongside
  Properties/Species/Tasks/Admin, which is what actually makes it
  reachable on a phone-width viewport — the first Playwright pass caught
  this the top-bar-only link would've been unreachable on mobile before
  the nav entry was added.
- **Docs:** removed "member can't change their own password" from
  `open-questions.md` and `docs/manual/limitations.md`; added
  `docs/manual/account.md` (linked from that manual's `README.md`) and
  updated `organization-admin.md`'s member-adding note to point at it.
- **Screenshots:** added an `account.png` capture step to
  `docs/manual/screenshots/capture.js` (had to re-navigate to `/admin`
  afterward before the existing "View public site" step, since that link
  only lives on the admin page and the new step had navigated away from
  it — a real bug the first run caught). Regenerated all of
  `docs/manual/images/` — first regen since 2026-08-14, so within the
  once-per-calendar-date cap.
- **Verified for real:** installed GDAL/GEOS/PostGIS + a local PostgreSQL
  16 natively in this sandbox (same fallback prior sessions used — no
  Docker daemon here either), ran `manage.py check` and
  `makemigrations --check` clean (no model changes this session, as
  expected), then curl-drove the new endpoint against a live server:
  wrong-current-password rejection, weak-new-password rejection (Django's
  validators), a successful change, confirmed the session stayed valid
  immediately after (a follow-up `/auth/me/` still 200s — proves
  `update_session_auth_hash` worked), then logged out and confirmed the
  *new* password logs in while the *old* one now fails, and confirmed an
  unauthenticated request 403s. Frontend: `tsc -b` and `vite build`
  clean; Playwright end to end at both a 390px mobile viewport and 1280px
  desktop — reached `/account` via the bottom-nav link (mobile) and the
  top-bar email link (desktop), exercised all three form error states
  (wrong current password, mismatched confirmation, weak password) plus
  the success path, confirmed the session survives the change, and
  confirmed logging back in works with the new password and fails with
  the old one.
- **Not done:** no "forgot password" / email-based reset flow (still no
  email backend configured, same gap as the invite flow); no way to
  change your own email; no password-strength meter on the form beyond
  the server-side validator's error text.

### 2026-08-14 (5) — Backend container runs migrations on startup

Explicit ask: "can migrations be run as a part of startup?" Yes — added
`backend/entrypoint.sh`, wired in as the image's `ENTRYPOINT`
(`backend/Dockerfile`; `CMD` is unchanged, still `runserver` for dev). On
every backend container start it: (1) polls `POSTGRES_HOST`/`POSTGRES_PORT`
(same env vars `settings.py` already reads) until the socket accepts a
connection, so `docker-compose up` doesn't race the `db` service's own
startup, then (2) runs `python manage.py migrate --noinput`, then
(3) `exec`s the container's real command. This removes the manual
`docker-compose exec backend python manage.py migrate` step every past
session's task-log entry has had to call out by hand.
- **Scope, deliberately narrow:** applies pending migrations only — it does
  *not* run `makemigrations` (that still requires a human/session decision
  after a model change, same as today) and it's dev-oriented: running
  `migrate` unconditionally from every container boot is fine for this
  project's single dev instance but would race if the image were ever run
  as >1 replica. Left a comment pointing at `docs/open-questions.md`
  ("Hosting/ops model") in the script itself rather than solving
  production migration strategy now — that's undecided and out of scope
  per this session's ask.
- Updated "How to work in this repo" above to match (migrate is now
  automatic; makemigrations still isn't).
- **Verified for real**, not just read: installed PostgreSQL 16 + PostGIS 3
  + GDAL/GEOS natively in this sandbox (same fallback prior sessions
  documented — the `postgis/postgis` image pull is still blocked by this
  sandbox's registry proxy, confirmed again this session with both
  `docker compose up db` and a plain `docker build` on `python:3.12-slim`
  both hitting the same CloudFront 403), then ran `entrypoint.sh` itself
  (not just eyeballed it) against that live Postgres in a venv: first run
  applied all 25 pending migrations across every app and then handed off
  to `manage.py check` (clean); second run correctly reported "No
  migrations to apply" (idempotent); pointed at a deliberately-wrong port
  to confirm the wait loop actually retries instead of crashing (killed
  via `timeout`, exit 124, not a script error). `sh -n` syntax-checked the
  script. Did not get to build the actual Docker image end-to-end (blocked
  by the same registry issue as above) — the entrypoint logic itself is
  fully exercised above, and the Dockerfile edit is a small, low-risk
  `COPY`/`chmod`/`ENTRYPOINT` addition on top of that.

### 2026-08-14 (4) — Screenshot regen cadence capped at once/day

Explicit ask: manual screenshot regeneration shouldn't happen on every
session, at most once a day. Updated the "Keep the user manual current"
section above (and the two places that echoed its old per-session
wording — `docs/manual/README.md`, `docs/manual/screenshots/README.md`)
to split the rule in two: keeping `capture.js` itself accurate stays
same-session (cheap, just editing the script), but actually *running*
it and committing new PNGs is now capped at once per calendar date,
checked via `git log -1 --format=%cd --date=short -- docs/manual/images/`.
Manual *text* updates are explicitly exempted from this cap — still
same-session, since stale/wrong prose is worse than a slightly-outdated
screenshot and editing markdown doesn't need the expensive stack
spin-up that's the actual reason for the cap. No code/doc-content
changes this session beyond this policy edit.

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
- **Follow-up same day: added real screenshots.** Installed PostgreSQL 16
  + PostGIS natively in the sandbox (not Docker — the compose stack's
  `postgis/postgis` image pull was blocked by the network proxy; Docker
  itself works here if `dockerd` is started first, just not that
  particular registry blob host) plus GDAL/GEOS, ran the backend and
  frontend dev servers for real, and drove the full flow with Playwright
  (signup → draw a property → log an activity and a sighting → link them
  → species/tasks/org-admin/public-site) against the live app, screenshotting
  each step into `docs/manual/images/`. Basemap tiles
  (`tile.openstreetmap.org`) aren't reachable from this sandbox either, so
  the map screenshots show drawn shapes/markers on a blank background
  rather than real OSM imagery — routed those tile requests to abort
  immediately (`page.route(...).abort()`) rather than let MapLibre retry
  forever; doesn't affect what the screenshots demonstrate. 14 screenshots
  across 9 chapters (some images are reused where the UI genuinely is
  identical, e.g. the Photos/Linked-records panel looks the same on an
  activity's edit page as a sighting's).
- **Not done:** doesn't cover self-hosting/deployment (no hosting model is
  decided yet — see `docs/open-questions.md`); screenshots are English-only,
  desktop-sidebar layout only (no mobile-bottom-nav screenshot).
- **Follow-up same day (explicit ask: "persist and improve in future
  sessions"):** the screenshot script was scratchpad-only (outside the
  repo, gone at session end) — moved it into the repo for real, at
  `docs/manual/screenshots/` (`capture.js` + `package.json` +
  `README.md`), so it's a maintained project asset instead of something
  every future session has to reinvent from the images alone. Along the
  way, made it independent of this specific sandbox run: auto-detects a
  Chromium binary under `PLAYWRIGHT_BROWSERS_PATH` instead of a
  hardcoded path with a version number in it
  (`chromium-1194/chrome-linux/chrome`), takes `BASE_URL`/`OUT_DIR`/
  `SKIP_TILE_ABORT` env var overrides, and each screenshot call has a
  `MANIFEST` comment naming which manual chapter(s) embed it. Wrote up
  both ways to get a live stack for it to run against (`docker-compose`,
  and the native-Postgres+PostGIS fallback this sandbox actually needed)
  in `screenshots/README.md` rather than only in this task log, since
  that's where a future session doing the re-run will actually be
  looking.
- **Verified for real, not just "should work":** re-ran the exact
  documented flow end to end from a clean-ish state — restarted the
  backend/frontend dev servers, `cd docs/manual/screenshots && npm
  install && node capture.js` — and confirmed it reproduced all 14
  screenshots against the moved script with no path/selector fixes
  needed. (11 of the 14 came out byte-different from the previous run
  purely because the account email/timestamps embedded in the UI are
  randomized per run — `login.png`/`public-org.png`/`public-property.png`
  were byte-identical, as expected for pages with no per-run user data.
  Diffed one of the changed ones (`org-admin.png`) visually side-by-side
  with the previous version to confirm the only difference really is the
  random email, not a layout regression.)

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
