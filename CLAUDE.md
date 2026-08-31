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

**All development — automated or otherwise — happens on the `main` branch
(owner directive, 2026-08-29).** Commit and push directly to `main`. This
holds *even when a session's startup instructions assign it some other
branch* (scheduled/programmer routines often get handed a fresh
`claude/...` branch by the scheduler): that per-session branch assignment
does **not** override this rule — develop on `main` regardless. The
earlier "…unless notated in the opening prompt of a session" carve-out is
retired precisely because it let a per-session branch silently win over
`main`, which is not what the owner wants. If a session genuinely *cannot*
push to `main` (the harness hard-blocks it), don't quietly develop on the
assigned branch and move on — say so and ask, rather than deciding for the
project. The durable fix for a routine that keeps handing out a feature
branch lives in the scheduler/session config on claude.ai, outside this
repo — a session can't change that for future runs, so flag it to the
owner if it recurs.

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

**Every chapter also links to the next one** (decided 2026-08-27) — a
`---` plus `[← Previous](...) · [Manual index](README.md) · [Next →](...)`
footer at the bottom of each chapter file, forming one linear path from
`getting-started.md` through `limitations.md` that matches
`docs/manual/README.md`'s chapter list order, so a reader isn't required
to bounce back to the index between every chapter. **A new chapter must be
spliced into this chain**, not just linked from the index — see
`docs/manual/README.md`'s own "Keeping this manual current" section for
the exact mechanics.

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
- **Take big bites, and be bold (owner directive, 2026-08-29).** Within
  what a session is actually scoped/authorized to build (a programmer
  routine's own instructions, or an explicit live "build this"), the
  owner wants ambition, not timidity: prefer shipping a *whole* feature —
  backend + frontend + docs + verification — over a thin slice of one,
  and prefer clearing *several* well-scoped queued items in a session
  over stopping at one. Don't half-build to be safe: if a queued item is
  decided and unblocked, build it end to end; if two or three are, do
  them all. Make the reasonable sub-decisions yourself and record them
  (per the open-questions bullet above) rather than stalling for
  permission on every small choice. The 2026-08-29 session (two full
  features — vanity slugs and the QR generator — in one sitting) is the
  intended bar. **This does not override the real guardrails**, which
  exist precisely so boldness stays safe: still don't build ahead of the
  phase or past a session's actual scope (the queue/PM-only rule below);
  still take a genuinely *ambiguous* design question (soft delete's
  retention/cascade shape is the standing example) to the owner rather
  than guessing; still verify for real before calling it done. Bold means
  "take the big, well-defined chunk and finish it," not "skip the
  checks" or "decide the open product questions unilaterally."
- Update `docs/manual/` alongside any user-facing change — see "Keep the
  user manual current" above.
- Keep `backend/` and `frontend/` runnable via `docker-compose up` — that's
  the expected local dev path given GeoDjango's system-library
  dependencies (GDAL/GEOS/PROJ).
- **Not every scheduled/automated session is the same routine — the
  owner runs more than one, and at least one of them (a "programmer"
  routine) is explicitly meant to implement and push code.** There is no
  blanket "scheduled = queue-only" rule; a scheduled task's own stored
  instructions (outside this repo, on claude.ai) are what set its scope
  each run, the same as any other task. What *is* a durable rule: **a
  session whose own triggering instructions scope it to gathering/
  clarifying/recording/queuing (e.g. "don't trigger the next build")
  stays in that scope for its whole lifetime, including once a live human
  joins mid-session — a live request doesn't silently upgrade it to
  "build this," no matter how detailed or spec-like that request reads.**
  Building still happens in that case — just recorded as a queued item
  (`docs/open-questions.md`/`build-questions.md`) for a session actually
  scoped to implementation, unless the live human gives *explicit* build
  authorization in the moment ("build this now," not just a detailed
  description of what they want). One explicit authorization covers only
  what was explicitly authorized, not the rest of that session's
  requests. (2026-08-28: a session that began as a scheduled "compile
  open questions, don't trigger a build" task implemented and pushed a
  real feature mid-session on an inferred, not explicit, read of a live
  request — see that day's task-log entries. The owner kept the shipped
  code but flagged the fix; an earlier version of this bullet
  overcorrected into a blanket "all scheduled sessions are queue-only"
  claim, which the owner also corrected — this is the reworded version.)
- **A queue/PM-scoped session recording items isn't enough on its own —
  a build session has to actually read them.** The other half of the
  rule above: any session doing implementation work must open
  `build-questions.md` (which says this at its own top too) as part of
  its scoping, before writing code, and triage every not-yet-built item
  there — build it, ask the owner if it's ambiguous, or explicitly
  re-defer it with a stated reason. Don't work only from whatever
  prompted that session while leaving the queue file unread — a queued
  item nobody reads is the same as one that was never recorded.
  (2026-08-28, explicit owner instruction, after several items had just
  been queued in that day's sessions.)

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

### 2026-08-31 — Scheduled PM check-in: no new open questions, feedback
### token still not provisioned, custom-CSS decision still outstanding

Routine "resolve open questions" run, project-manager scope only (no live
human joined). Re-read `docs/open-questions.md` and `build-questions.md`
in full; `main` and this session's assigned branch were both already at
`f5c866d` (the 2026-08-30 (2) session's last commit), so there was
nothing new to reconcile between them, and no code was written or pushed
this run beyond the doc updates below.

**Re-verified rather than assumed:** curl'd `habitat.dev.cravenator.com`
directly — reachable (`GET /` and `GET /api/auth/csrf/` both 200, as in
prior sessions). Called its live `GET /api/feedback/pull/` — still
returns "no token configured," same as the 2026-08-30 check. This
session's own environment has no `HABITAT_FEEDBACK_TOKEN` set either.
So `HABITAT_FEEDBACK_TOKEN` remains unprovisioned three days after the
feedback pipeline shipped, and this routine's own "collect any user
feedback from testing" step is still a confirmed no-op. Also
spot-checked `GET /api/feedback/config/` unauthenticated — it correctly
403s (any *logged-in* member can check it; it isn't meant to be a public
read), so that's expected behavior, not a new bug.

**One genuinely open item remains, restated rather than newly found:**
the public-site custom-CSS shape (constrained theme controls vs. a raw
CSS field) — still the one call blocking the storytelling feature's
custom-content layer; the pages/Explore/landing foundation itself is
already built and needs no further owner input. Sent a push notification
this run (unlike the 2026-08-30 PM session, which found the same feedback-
token gap but nothing else outstanding) specifically re-raising both this
CSS decision and the still-unprovisioned token, since both have now gone
unresolved for several days without an answer — not because anything
changed today. Updated `build-questions.md` (new "2026-08-31" section)
and `docs/open-questions.md` (feedback-token bullet now notes two
consecutive re-confirmations). No code, migrations, or manual changes —
nothing user-facing changed.

### 2026-08-31 (2) — Live follow-up: owner decided the custom-CSS shape

Same session as the PM check-in above; the owner responded live to the
push notification's CSS question. Walked through the constrained-vs-raw
tradeoff (already written up in `build-questions.md`); **owner decided:
constrained theme controls**, not a raw CSS field — no raw-CSS escape
hatch for now. This is a decision-recording exchange, not a build
authorization — the owner didn't say "build this," so per this session's
own scheduled-task scope (project-manager only) and `CLAUDE.md`'s
"Working conventions" rule (a queue-scoped session stays queue-scoped for
its whole lifetime absent explicit build authorization), nothing was
built or pushed as code this session. Recorded the decision in
`build-questions.md` ("CSS overrides on the public site" — now marked
✅ DECIDED, shape = constrained theme controls, status = build-ready
pending "build this") and `docs/open-questions.md` ("Public site
storytelling / custom content" — the custom-CSS bullet now shows the
decided shape; the section's intro now says the whole custom-content
layer is build-ready, not just partially decided). **Every design call
blocking the storytelling feature's custom CSS/HTML/JS layer is now
settled** (isolated-origin parked 2026-08-29, custom-CSS shape decided
today) — the only remaining gate before a build session picks it up is
the owner's explicit go-ahead.

### 2026-08-30 (2) — Scheduled programmer session: built the "public site
### storytelling" first slice (authored pages, Explore rename, landing page)

Scheduled "programmer" session (same day as the PM check-in below, which
ran first and found nothing new — confirmed `main` was still at `3149cf5`
before starting). Read `docs/open-questions.md` and `build-questions.md`
per this file's own triage rule; the one substantial decided-but-unbuilt
item left in the queue was the "public site storytelling" feature's first
slice (direction fully decided 2026-08-29, explicitly re-deferred by that
day's programmer session as "a substantial chunk of its own"). Built it
end to end — model + API + both authoring UIs + public rendering — per
this file's "take big bites" directive, rather than another partial pass.

**Backend:** new `apps/pages` app — `Page` model (`backend/apps/pages/
models.py`), scoped to an Organization (`property` null) or one of its
Properties; markdown `body`, rendered to sanitized HTML at *read* time
(`apps/pages/rendering.py` — Python-Markdown then `bleach` to a fixed tag/
attribute allowlist) rather than ever storing/serving raw author HTML —
picked as the content format specifically to sidestep the larger,
still-undecided "custom HTML" stored-XSS question for this slice; slug
auto-generates and is unique per scope (org-level vs. one property's own
pages), with `"explore"` reserved for the built-in virtual Explore page
(not a stored row). `Organization.landing_page`/`Property.landing_page`
(nullable FK to `Page`, `SET_NULL`) pick which page shows at the public
URL root — null (unchanged for every existing org/property) means
Explore; validated server-side to be one of that exact scope's own pages,
and a landing page that gets unpublished falls back to Explore rather
than breaking the root URL. Authoring API: `GET/POST /api/pages/` (+
`?property=<id>` to scope to a property) and `/api/pages/<id>/`,
editor+ to write, same `OrganizationScopedViewSet`/role convention as
everywhere else. Public site (`apps/public_site`): org/property payloads
gained `pages` (public pages, for the nav) and `landing_page_slug`; new
`GET /api/public/o/<org>/pages/<slug>/` and `.../<property>/pages/<slug>/`
return a page's sanitized `body_html`, never the raw markdown.

**Frontend:** `PageFormPage.tsx` (one component handles all four authoring
routes — `/admin/pages/new(/:pageId/edit)` for org-level,
`/properties/:id/pages/new(/:pageId/edit)` for property-level) — plain
title/URL-name/Markdown-textarea/visibility form, no rich-text or HTML
editor (matches the markdown-only content format). New "Pages" section +
"Landing page" `<select>` on `OrgAdminPage` (org-level) and
`PropertyMapPage` (property-level, editor+ only, next to the existing QR
code panel). New `PublicPageNav` component (Explore + every public
authored page) rendered on both `PublicOrganizationPage` and
`PublicPropertyPage`, which both also gained a `forcePage="explore"` prop
(wired to new `/explore` routes) and branch on route/landing-page state to
show either the built-in Explore content (unchanged) or an authored
page's `body_html` via `dangerouslySetInnerHTML` (safe here specifically
because it's the server's own already-sanitized output, never
author-supplied text rendered directly). No existing route or URL shape
changed — a brand-new org/property with no authored pages renders
byte-identical to before this session.

**Real bug found and fixed while curl-testing, not just read in the
diff:** DRF auto-generates a `UniqueTogetherValidator` from
`Page.Meta`'s conditional `UniqueConstraint`s (org+slug when
property-is-null, property+slug otherwise) — DRF can't express the
"only applies when property is null" condition, and worse, its
`enforce_required_fields` force-requires *every* field in the matched
constraint on every write, which made `property` a required field even
for creating an org-level page (where omitting it is the entire point).
Fixed by overriding `PageSerializer.get_unique_together_validators()` to
return `[]` — `validate_slug`'s own hand-written check already enforces
uniqueness correctly for both scopes and doesn't have this problem.
**Second bug, also found by testing, not reading:** `PageViewSet
.get_queryset()`'s `?property=` scoping (meant for `list`) was also
applying to `retrieve`/`update`/`destroy`, which have no such query param
on their URLs — this 404'd every PATCH/DELETE on a property-scoped page.
Fixed by only applying that filter when `self.action == "list"`.

**Docs:** `docs/data-model-notes.md` (new "Authored pages" subsection
under "Public-facing site"), `docs/open-questions.md` and
`build-questions.md` (first slice marked built, custom CSS/HTML/JS layer
left queued and unchanged — custom CSS's constrained-vs-raw call is still
the one open question blocking it), `docs/manual/public-site.md` (new
"Authored pages and the landing page" section), `docs/manual/
organization-admin.md` (new "Pages" section), `docs/manual/properties.md`
(property-level Pages section), `docs/manual/limitations.md` (new
"no custom CSS/HTML/JS on pages yet" bullet, framed as a deliberate,
still-open decision, not a bug).

**Verified for real:** installed PostGIS/GDAL/GEOS system packages and a
local PostgreSQL 16 in this sandbox (same fallback prior sessions
documented), ran `makemigrations`/`migrate`/`makemigrations --check`
clean. Curl-drove the full new surface directly: org-level and
property-level page create/list/update/delete, the reserved-slug
rejection, both landing-page validations (org page rejected as a
property's landing page and vice versa), unpublishing a page falling the
landing page back to Explore (confirmed via the public payload) and the
page 404ing on its own detail URL once unpublished, `SET_NULL` on
deleting a page that was a property's landing page, and — the actual
security property this design exists for — a `<script>alert(1)</script>`
+ `[link](javascript:alert(2))` payload in a page's markdown source
coming back with the script content stripped to plain text and the
`javascript:` href removed by the time it reaches `GET
/api/public/o/.../pages/<slug>/`. Frontend: `tsc -b` and `vite build`
clean. Full Playwright run (installed `playwright@1.62.1` in the
scratchpad, `/opt/pw-browsers` Chromium) against the live backend+
frontend: signup → create a property → author an org-level page from
`/admin` → set it as the landing page → confirmed the public org root URL
now renders that page's content (not the property list) with the
`<script>` tag gone from the rendered HTML → confirmed "Explore" in the
page nav still reaches the original property-list view at `/explore` →
authored a property-level page → confirmed the property's public page nav
and the authored page both render correctly. No unexpected console
errors beyond the documented sandbox basemap-tile noise.

**Not built — explicitly still queued, not silently skipped:** the
custom CSS/HTML/JS layer on top of this (see `docs/open-questions.md`,
"Public site storytelling / custom content") — custom CSS's
constrained-controls-vs-raw-field question is still a genuine open call
for the owner, not a build-session default; multi-block/gallery page
content beyond one markdown body; drag-to-reorder pages (the `position`
field exists and is respected, nothing sets it besides `0` yet).
Screenshots not regenerated — today's once-per-calendar-date allowance
was already available (last regen 2026-08-29) but nothing existing went
*wrong* (the new Pages sections are additive, below the fold, and
`capture.js` selects nothing this touched) — left for the next regen per
this file's own cap policy.

### 2026-08-30 — Scheduled PM check-in: no new open questions, feedback
### token still not provisioned

Routine "resolve open questions" run, project-manager scope only (no live
human joined — nothing to escalate an inferred build request from this
time). Re-read `docs/open-questions.md` and `build-questions.md` in full;
`main` and this session's assigned branch were both already at `65239f2`
(the 2026-08-29 (2) session's last commit), so there was nothing new to
reconcile between them. Found no new open questions or blockers — the
2026-08-29 sessions already resolved everything that was answerable, and
the two items still genuinely open (public-site custom-CSS shape;
explicit build authorization for the storytelling-pages first slice)
were already recorded and didn't need re-litigating, just restating.

**Concretely re-verified rather than assumed:** curl'd
`habitat.dev.cravenator.com` directly from this session — reachable
(`GET /` and `GET /api/auth/csrf/` both 200, as in prior sessions) — then
called its live `GET /api/feedback/pull/`, which still returns "no token
configured." So `HABITAT_FEEDBACK_TOKEN` remains unprovisioned two days
after the feedback pipeline shipped, and this routine's own "collect any
user feedback from testing" step is a confirmed no-op until that secret
is set in both the server's environment and this scheduled routine's own
environment config on claude.ai — an ops step outside any session's
reach, flagged to the owner via push notification this run (not just
written here). Updated `build-questions.md` (new "2026-08-30" section)
and `docs/open-questions.md` ("App feedback / build workflow") with this
finding. No code, migrations, or manual changes — nothing user-facing
changed.

### 2026-08-29 (2) — Scheduled programmer session: soft delete, task
### notifications, in-app feedback pipeline, QR fix, four-seasons logo

Scheduled "programmer" session, same calendar date as the "Dev run"
session below (whose branch had accumulated a full day's worth of
decision-recording commits, all already merged to `main` by the time this
session started — confirmed `main`==HEAD before doing anything). Read
`build-questions.md` per its own top-of-file instruction and triaged
every decided-but-unbuilt item; built the five that were genuinely
build-ready, investigated and fixed the one flagged bug report, and
explicitly left the large storytelling/custom-content feature queued
(see "Not built" below) rather than half-building it alongside everything
else.

**1. Soft delete — Property only, 30-day retention, admin-restorable,
cascading** (`accounts/0009_property_deleted_at`). `Property.deleted_at`
+ a `PropertyManager` whose default `objects` queryset filters it out —
every existing caller (the app, the public site) already goes through
`Property.objects`, so this "just works" without touching them;
`Property.all_objects` is the unfiltered escape hatch for the admin
restore view and the purge command. `ActivityViewSet`/`SightingViewSet`
each gained a join-filter (`property__deleted_at__isnull=True`, with an
OR for Sighting since its `property` FK is optional) so a soft-deleted
property's records disappear from every normal list too, not just the
property itself. New admin-only `GET /api/properties/deleted/` +
`POST /api/properties/<id>/restore/`, a "Recently deleted" section on the
org admin portal, and `apps/accounts/management/commands/
purge_deleted_properties.py` — hard-deletes a property's sightings
*explicitly* first (since `Sighting.property` is `SET_NULL`, not
`CASCADE` — leaving them behind, orphaned, would contradict the decided
"all associated records" cascade), then the property itself (whose
activities cascade automatically). No scheduler wired up for the purge
command yet — run manually until the hosting/ops question settles enough
to know where a cron-equivalent would live.

**2. Task assignee notifications, pluggable channels** — new
`apps/notifications` app. `Notification` model (generic `verb`/`message`,
not task-specific, so a future event type is a new choice + call site,
not a schema change) + `events.py`'s `Channel`/`notify()` dispatch —
`InAppChannel` is the only implementation today; a future `EmailChannel`
(once real SMTP exists) plugs in by appending to `CHANNELS`.
`TaskViewSet.perform_create`/`perform_update` dispatch on
assign/reassign, skipping self-assignment (nothing to tell you that you
don't already know). `GET /api/notifications/` (scoped to the
*recipient*, not an active org — a notification is personal) +
mark-read/mark-all-read. Frontend: `NotificationsBell.tsx` — a 🔔 in
`TopBar` with an unread-count badge, a dropdown listing recent
notifications, polling every 60s (no websocket infra in this project).

**3. In-app feedback pipeline** — new `apps/feedback` app. `Feedback`
model with a three-stage lifecycle (`new` → `synced` → `resolved`) so
"already pulled by the external routine" and "actually addressed" don't
get conflated. `GET/POST /api/feedback/` (submit — any org member; the
GET is admin-only, this org's own items), `POST /api/feedback/<id>/
resolve/` (admin). The cross-org retrieval surface for an external
scheduled routine — `GET /api/feedback/pull/` (defaults to `?status=new`)
+ `POST /api/feedback/pull/mark-synced/` — is **bearer-token
authenticated**, not session-based (`apps/feedback/auth.py`,
`HABITAT_FEEDBACK_TOKEN` setting): picked the PM-recommended option (a
single shared secret checked as an `Authorization: Bearer` header) over
a service-account login, since it's simplest and doesn't pull Phase-4
API-key thinking forward prematurely. An unset token always denies —
never "any request is fine." The whole feature (submission UI +
retrieval) is gated behind `HABITAT_FEEDBACK_ENABLED`
(`GET /api/feedback/config/` tells the frontend whether to render the
floating "Send feedback" button at all) so it can stay off by default and
be turned on only where wanted. Org admins get a lightweight review list
+ resolve button on the org admin portal so they don't have to query the
database directly. **Not done — ops, not code:** the actual
`HABITAT_FEEDBACK_TOKEN` secret needs provisioning on a real target
instance and in whatever scheduled routine ends up pulling from it; no
routine has been pointed at this yet.

**4. Per-property QR code "not in place" report — investigated, root
cause was UX not a missing/undeployed feature.** Confirmed via the live
dev instance's served Vite source (fetched `/src/pages/
PropertyMapPage.tsx` directly over HTTP — this sandbox's egress to
`habitat.dev.cravenator.com` is open, see the 2026-08-28 entries below)
that the QR code already existed there, ruling out "not yet redeployed."
Real issue: the whole section rendered *nothing at all*, with zero
explanation, when a property isn't public — and even when public, it
defaulted to a collapsed `<details>` easy to miss entirely. Fixed both:
an inline "this property isn't public yet, mark it public to get a code"
message instead of silence, and the panel now starts expanded.

**5. Nav logo — the "four seasons" mark.** Read the owner's published
Claude Design canvas (`action: "read"` on the artifact URL from
build-questions.md) — the raw HTML comes back wrapped in this session's
own frame-runtime scaffold, so the actual canvas content had to be
recovered from the tool's saved full-HTML file (a JSON-escaped string
inside a `<script>` tag) rather than the summarized response. Extracted
the four seasonal SVGs (artboard 7a-7d: Spring/Summer/Fall/Winter) into
`frontend/src/assets/logo-{spring,summer,fall,winter}.svg` (fixing the
canvas's `sc-camel-view-box` attribute back to a real `viewBox` for a
valid standalone SVG). New `utils/logo.ts#currentSeason()` (meteorological
boundaries — Mar-May/Jun-Aug/Sep-Nov/Dec-Feb — and Northern Hemisphere,
both cheap-to-change build-session defaults per the spec) +
`components/Logo.tsx` (icon + "habitat" wordmark, wordmark color matching
each season's canvas styling) — swapped into both `TopBar` and
`PublicHeader` in place of the old "🌿 Habitat" emoji+text placeholder.

**Not built — explicitly re-deferred, not silently skipped:** the public
site "storytelling" feature (authored pages + Explore rename + landing-
page pick, plus custom CSS/HTML/JS) — direction is decided and detailed
in `build-questions.md`, but it's a substantial feature on its own and
this session already shipped five other items; the isolated-origin
question specifically is *also* now resolved (owner parked it — custom
content co-mingles on the app's own origin as an informed risk
acceptance) so nothing there is blocking a future build, it just wasn't
this session's to take on too. Left queued in both `build-questions.md`
and a new `docs/open-questions.md` section ("Public site storytelling /
custom content") rather than half-built.

**Docs:** `docs/open-questions.md` (moved all five resolved items into
"Recently resolved," removed the now-stale "Data model" section entries,
updated "Hosting/ops model" for the prod/dev domain split, rewrote "App
feedback / build workflow" now that it's built, added the new
storytelling-feature section), `docs/data-model-notes.md` (Property/soft
delete, new "Notifications" and "App feedback" sections), `build-
questions.md` (every built item marked, original spec text kept for
reference), manual chapters `properties.md` (soft-delete + QR-hint
wording), `tasks.md` (notifications), `organization-admin.md` (Recently
deleted + Feedback sections), `limitations.md` (removed the now-resolved
vanity-slug-URL and task-notification limitations, added the new
property-only-soft-delete and feedback-gated-by-default notes),
`getting-started.md` (nav bullet for the bell + feedback button).

**Verified for real:** installed PostGIS/GDAL (`postgresql-16-postgis-3`,
`gdal-bin`, `libgdal-dev`) and a local PostgreSQL 16 in this sandbox (same
fallback prior sessions used), ran `makemigrations`/`migrate`/
`makemigrations --check` clean throughout. Curl-drove every new endpoint
directly: soft-delete → confirmed properties/activities/sightings all
vanish from every list → restore → confirmed everything reappears →
backdated `deleted_at` 31 days and ran the purge command for real →
confirmed the property, its activity, and its sighting are all actually
gone from the DB; task assignment/reassignment notifications (confirmed
exactly 2 notifications for 2 real reassignments, not 3, since a
self-reassignment correctly didn't notify) and mark-read/mark-all-read;
feedback submit → admin list → resolve, and the bearer-token pull/
mark-synced surface (confirmed 403 with no token and with a wrong one,
confirmed a synced item drops out of the next `?status=new` pull).
Frontend: `tsc -b` and `vite build` clean throughout. Full Playwright run
(installed `playwright@1.62.1` in the scratchpad, `/opt/pw-browsers`
Chromium) against the live backend+frontend: signup → logo image loads
with a nonzero natural width (not a broken reference) → notifications
bell renders its empty state → feedback widget submits and shows a
success message → created a property, saw the exact delete-confirm copy,
soft-deleted it, confirmed it's gone from the properties list → found it
in the org admin portal's "Recently deleted," restored it, confirmed the
section itself disappears when nothing's left in it and the property
reappears on `/properties` → confirmed a public property's QR panel
renders open by default and a private property shows the inline hint
instead. No unexpected console errors beyond the documented sandbox
tile/network noise (basemap tiles and this sandbox's proxy don't mix —
see prior sessions).

**Screenshots:** not regenerated — `docs/manual/images/` was already
regenerated once today (the "Dev run" session, per `git log -1 --format=%cd
--date=short -- docs/manual/images/`), so today's once-per-calendar-date
allowance was already used. The logo swap makes the top-bar/public-header
screenshots slightly stale (a different brand mark in the same position/
role) but not actively wrong the way a removed or renamed control would
be — left for the next regen, per this file's own cap policy.

### 2026-08-29 — "Dev run" → programmer session: built vanity slug URLs,
### then the QR code generator (both queued in build-questions.md)

Session started as "do a dev run" (brought the full stack up from a cold
sandbox — PostGIS/GDAL + local Postgres 16 + venv + frontend — and
verified the app end to end via curl + Playwright; no code changes in that
first pass). The owner then said "keep development iterating," which is
explicit build authorization, so this became a programmer session. Read
`build-questions.md` and built its two top decided-but-unbuilt items, on
branch `claude/dev-run-yo5pas` (this session's assigned branch).

**1. Vanity slug URLs (commit 1).** Org gets a globally-unique `slug`;
property gets a `slug` unique within its org (`UniqueConstraint` on
`(organization, slug)`). Auto-generated from the name on `save()` with a
`-2`/`-3` collision suffix (`apps/accounts/slugs.py`); reserved org slugs
(`org`, `properties`, `public`, `api`, …) can't shadow the numeric public
routes. Migrations `0007` (schema) + `0008` (backfill existing rows).
Serializer slug validation (uniqueness, reserved words; blank = regenerate
from name). Slug-resolving public endpoints `/public/o/<org>/` and
`/public/o/<org>/<prop>/` sharing the numeric views' bodies; **numeric-ID
URLs kept working** (not redirected) for backward compat — verified in a
browser that react-router still routes `/public/org/1` correctly.
Frontend: new `/public/:orgSlug` + `/public/:orgSlug/:propertySlug`
routes, public pages resolve by slug-or-numeric, links use slugs, **Public
URL name** editors on the org admin portal + property edit form.

**2. QR code generator (commit 2).** Owner picked: server-side PNG, offered
on **both** org admin + property page, **center-logo embedding built now**.
`apps/accounts/qrcodes.py` (`qrcode`+Pillow, added to `requirements.txt`),
`POST /api/org/qr/` and `POST /api/properties/<id>/qr/` — take the
public-site origin (`base_url`, which the backend can't infer since the SPA
is a different origin) + an optional `logo` image, return image/png.
Error-correction level H + a white-padded center paste, **verified with
zbar that the logo-covered code still decodes**. Shared `QrCodePanel`
(logo picker + live preview + download) on `OrgAdminPage` and, gated on
`is_public`, `PropertyMapPage`.

**Verified for real** (same sandbox stack): backend `check` /
`makemigrations --check` clean throughout; curl-drove every new endpoint
(slug resolution, admin slug edit + uniqueness/reserved rejection, numeric
back-compat, QR generation plain + logo + bad-input 400s) and decoded the
QR PNGs with zbar; frontend `tsc -b && vite build` clean; Playwright drove
signup → property → org/property slug edit → public site via slug →
numeric back-compat → QR generate/preview/logo on both pages, no page or
console errors.

**Docs:** `open-questions.md` (both items → "Recently resolved"),
`data-model-notes.md` (slug fields), `build-questions.md` (both marked
built), manual `organization-admin.md` / `properties.md` / `public-site.md`.
**Screenshots:** regenerated once for the slug work (within the
once-per-calendar-date cap — last was 2026-08-28). The QR UI is new but
additive/below-the-fold, so no existing screenshot went *wrong*; a
dedicated QR screenshot is left for the next regen (cap already used
today) — QR is documented in manual text meanwhile, no broken image links.

**Not built / re-deferred** (still in `build-questions.md`): soft delete
(genuinely ambiguous — which models/retention/restore/cascade), in-app
feedback pipeline (sync half still blocked on hosting), nav-layout real
logo asset. QR's center-image is per-generation upload, not a stored org
logo — a persistent org-logo store would be its own feature.

### 2026-08-28 (14) — Programmer session: triaged build-questions.md,
### built six of its queued/decided items

Scheduled "programmer" session (per this file's own "not every scheduled
session is queue-only" rule — this one's trigger explicitly scopes it to
implementing and pushing code). Opened `build-questions.md` per its own
top-of-file instruction and triaged every not-yet-built item before
writing code, same as entry (9) requires. Built the well-scoped,
already-decided items; explicitly re-deferred the large new-feature ones
rather than half-building them (see below) — commits went straight to
`main`, per this file's 2026-08-28 (2) branch policy.

**Built:**

1. **Sensitive-sighting per-property default visibility** (`open-
   questions.md` #3, decided 2026-08-28, previously unimplemented) —
   `Property.sightings_public_by_default` (migration
   `accounts/0006_property_sightings_public_by_default`), applied in
   `SightingViewSet.perform_create` when the request doesn't explicitly
   set `is_public` itself, exposed as a checkbox on `PropertyFormPage`,
   and seeded into `SightingFormPage`'s own checkbox for a *new* sighting
   on that property (an existing one keeps its own saved value).
2. **Public site now surfaces the sighting↔activity link** (`open-
   questions.md` #8, decided 2026-08-28) — `property_activities`/
   `property_sightings` in `apps/public_site/views.py` each annotate
   their features with `linked_sighting_ids`/`linked_activity_ids`,
   filtered so a link only ever appears when the *other* side is also
   public (and on a public property) — a public visitor can never infer
   a private record's existence via a link to it. `PublicPropertyPage`
   renders "Reported sightings: …" / "Treated by: …" lines.
3. **Property view: checkbox → tap-to-pin.** Removed the per-record
   checkbox on `PropertyMapPage`/`PublicPropertyPage`'s combined list;
   tapping/clicking anywhere on a card (its Edit/Delete buttons stop
   propagation, so those still work) toggles that card's pin, shown via
   a "📌 Pinned" badge and a distinct border/tint when pinned-but-not-
   focused. Keyboard-accessible (`tabIndex` + Enter/Space).
4. **Fixed the last-item scroll-focus bug** in `useFocusedListItem` — the
   trigger band sits near the top of the scroll container, so an item
   shorter than roughly `containerHeight - offset - bandHeight` (commonly
   the last one) could never be scrolled far enough to enter it. Now
   force-focuses the last item once the container is actually scrollable
   and scrolled to its max `scrollTop`. **Non-obvious part:** this can't
   be applied inline in the scroll handler, or even one
   `requestAnimationFrame` later — both were tried and still lost the
   race against the band `IntersectionObserver`'s own (wrong, for this
   item) notification for that same scroll, which arrives slightly later
   and silently clobbers an inline/rAF override right back. A short
   trailing debounce (reset on every scroll event) reliably lands after
   that settles. Verified with a 16-record list at a short viewport
   (forces real scrolling): the true last item becomes focused at max
   scroll, while a short list that fits without scrolling still defaults
   to the first/newest item (a `scrollable` guard exists specifically so
   the fix doesn't regress that case — caught in testing, see below).
5. **Species list search/filter** — a plain filter input above
   `SpeciesPage`'s list (client-side substring match, same reasoning as
   `Combobox.tsx`'s own filtering), with a "Showing X of Y" hint and a
   "no species match" empty state.
6. **Nav layout reflow** (partial — see "Not done" below) — the desktop
   sidebar (`.app-nav`) now starts below the top bar
   (`top: var(--topbar-height)` instead of `top: 0`) instead of
   overlapping its top-left corner (confirmed the overlap was real,
   pre-fix, by measuring both elements' rendered boxes); the mobile
   `.top-bar` brand now centers top-middle via a 3-column grid (empty
   spacer / brand / account block) rather than `justify-content: center`,
   which would've drifted off-center next to the account block's own
   width.

**Explicitly re-deferred, not built** (per `build-questions.md`'s own
triage instruction — ambiguous or oversized items get a stated reason,
not silence):

- **Soft delete** — genuinely ambiguous (which models, retention, who
  restores/where, cascade behavior are real open design questions, not
  implementation details this session should pick unilaterally without
  the owner). Re-queued as-is.
- **Vanity slug URLs** and **QR code generator** — not ambiguous, but
  each a real chunk of work (model fields + migrations + uniqueness/
  collision handling + routing changes, respectively a QR library
  integration) that deserves its own session rather than being squeezed
  in alongside everything else above. Re-queued as-is.
- **In-app feedback → build-workflow pipeline** — building just the
  in-app submission half without the automated-sync half (still blocked
  on the open "Hosting/ops model" question) would leave submissions with
  nowhere to go; re-queued as one item rather than half-built.
- **Nav layout logo:** the reflow (#6 above) is done, but no real logo
  image asset exists — this only repositions the existing "🌿 Habitat"
  emoji+text brand. An actual image logo is a separate follow-up once
  one exists.

**Docs:** `docs/open-questions.md` (moved #3/#8 into "Recently
resolved"), `docs/data-model-notes.md` (Sighting/Property/public-site
sections), `build-questions.md` (marked items built or re-deferred with
reasons), `docs/manual/properties.md` (new property checkbox, tap-to-pin
description), `docs/manual/public-site.md` (linked-record display, tap-
to-pin wording), `docs/manual/sightings.md` (per-property default
wording), `docs/manual/species.md` (search box), `docs/manual/
limitations.md` (removed the now-resolved sighting↔activity-link and
sensitive-visibility limitations, reworded the latter to describe what's
still actually missing — automatic species-based detection/fuzzing, not
manual per-property control, which now exists).

**Screenshots:** ran `capture.js` for real — first regen today (last was
2026-08-27), so within the once-per-calendar-date cap. Needed no script
changes (no selector referenced the removed checkbox or the old
two-section layout). All 17 images regenerated; spot-checked
`property-map-with-records.png`, `public-property.png` (now shows
"Treated by: planting" under the linked sighting — confirms the new
public-link feature end-to-end, not just via API), and `species.png`
(shows the new Search box).

**Verified for real:** installed PostGIS/GDAL/GEOS system packages and a
local PostgreSQL 16 in this sandbox (same fallback prior sessions
documented), ran `makemigrations`/`migrate`/`makemigrations --check`
clean, then curl-drove the sensitive-visibility default (omitted
`is_public` → picks up the property's default; explicit `is_public` →
always wins) and the public link annotations (linked a public and a
private sighting to the same public activity; public API returned only
the public one in `linked_sighting_ids`). Frontend: `tsc -b` and
`vite build` clean throughout. Playwright against the live backend
(headless Chromium at `/opt/pw-browsers`, since this sandbox has no
network path to the usual download host): confirmed desktop sidebar/
top-bar boxes now meet exactly with no gap or overlap (`61px`/`61px`);
confirmed the mobile brand's center is within a sub-pixel of the
viewport's actual center; confirmed tap-to-pin toggles the "📌 Pinned"
badge on and back off and that clicking Edit/Delete doesn't also toggle
it; confirmed the last-item scroll-focus fix with an 8-then-16-item list
at a short viewport (real scrolling required) while re-confirming a
short, non-scrollable list still defaults to the first item (this
caught a real regression in an earlier version of the fix, which is why
the `scrollable` guard exists — see above); confirmed the public
property page renders "Treated by: …" / would render "Reported
sightings: …" for the reverse case. No console errors/React warnings
beyond the expected aborted-basemap-tile noise documented in prior
sessions.

### 2026-08-28 (13) — Egress opened up mid-session; confirmed live access
### for real, plus a new incremental-fetch requirement

Follow-up to entry (12): the owner opened up this session's egress
policy for `habitat.dev.cravenator.com` mid-session. Re-tested rather
than taking it on faith — `curl` now reaches both the frontend (`200`,
real Habitat dev-server HTML) and the live API
(`/api/auth/csrf/` → `200`, `{"detail":"CSRF cookie set"}`). Confirms
mechanism 2 (a scheduled routine polling an API endpoint) is genuinely
viable, not just theoretical, once that endpoint exists. One remaining
detail: the `WebFetch` tool still can't reach the domain (separate
allowlist from the general sandbox proxy `curl` uses) — noted but not a
blocker, since the actual pipeline would use a direct HTTP call, not
`WebFetch`.

Also recorded a new explicit requirement from the owner: the sync
shouldn't re-fetch every `Feedback` row every run — items need a
status/lifecycle (`new` → `synced` → `resolved`/`answered`, sketched,
not decided in detail) so the pull step naturally excludes anything
already synced, without conflating "already recorded in
`build-questions.md`" with "the underlying request is actually
resolved" — those are different states. Doc-only (`build-questions.md`,
`docs/open-questions.md`) — still this session's queue-only scope, no
code.

### 2026-08-28 (12) — Confirmed the domain is live; found this session's
### sandbox can't reach it (real finding, not theoretical)

Owner confirmed `habitat.dev.cravenator.com` (entry (11)) is already
running, and asked whether feedback there could be exposed by URL to a
Claude routine. Answer is architecturally yes, but tested it for real
rather than just answering in the abstract: tried reaching that domain
directly from this session via both a raw HTTPS request (through the
sandbox's own egress proxy — got `CONNECT tunnel failed, response 403`)
and the `WebFetch` tool (`EGRESS_BLOCKED`). Both rejected by *this
session's own* network egress policy, not a DNS/server problem on
Habitat's end. Recorded as a concrete, verified blocker (not a guess) on
the app-feedback pipeline item in `build-questions.md`, plus a matching
note in `docs/open-questions.md`'s hosting entry — whoever builds that
pipeline needs the scheduled routine's environment network policy opened
up for this domain first (see
https://code.claude.com/docs/en/claude-code-on-the-web for where that's
configured). No code this entry — investigation + doc updates only,
consistent with this session's queue-only scope.

### 2026-08-28 (11) — Dev hosting domain decided: habitat.dev.cravenator.com

Owner decision, partially answering the long-open "Hosting/ops model"
question: a real instance will live at `habitat.dev.cravenator.com`.
Recorded in `docs/open-questions.md` (new bullet right after the
existing Docker-publish note) and cross-referenced from
`build-questions.md`'s app-feedback pipeline item, which needed exactly
this ("some live instance to target"). **Does not fully resolve
"Hosting/ops model"** — self-hosted-vs-managed, prod-vs-dev-only, and
cost/scaling are all still open — and it's **not yet confirmed whether a
server is already live behind this domain** or whether standing one up
(DNS, TLS, actually running the published Docker images, wiring real
SMTP) is itself queued work; asked the owner to confirm. No code this
entry — still this session's queue-only scope.

### 2026-08-28 (10) — App feedback must reach the workflow automatically,
### not via a manual DB check

Owner clarified entry (9)'s loop doesn't go far enough for the in-app
feedback item specifically: they don't want to manually query the
database to see what's been submitted — new `Feedback` rows have to
reach `build-questions.md` on their own. Added this as an explicit
requirement on that queued item (both `docs/open-questions.md` and
`build-questions.md`), with three candidate mechanisms (a management
command run on a schedule, an API endpoint a scheduled Claude routine
like this one's own trigger polls, or a CI job) and one flagged real
dependency: none of this can run against a live database until Habitat
is actually hosted somewhere reachable — still blocked on the open
"Hosting/ops model" question. Doc-only, no code.

### 2026-08-28 (9) — Closed the loop: a build session must actually read
### the queue

Owner wanted a guarantee that everything queued today (and going
forward) actually reaches evaluation before the next build, not just
sits recorded and unread. Added the other half of the queue/build split
established in entries (5)/(6): `build-questions.md` now opens with an
explicit instruction that any implementation session must read it and
triage every open item before writing code; `CLAUDE.md`'s "Working
conventions" gained the matching durable rule. Doc-only, no code —
consistent with this session's own queue-only scope.

### 2026-08-28 (8) — Corrected entry (7): app feedback is not Phase 5
### public input

Entry (7) below wrongly framed the new in-app feedback item as
overlapping/tying into the Phase 5 "Public input" open question. Owner
corrected this: the feedback area is for feedback **on the Habitat app
itself, from its own logged-in users** (bug reports, UX friction,
feature ideas) — Phase 5 public input is visitor-submitted
land-management data (sightings/observations) on the *public* site.
Different audience, different purpose, no real overlap. Un-conflated
both docs: removed the feedback bullet from `docs/open-questions.md`'s
"Public input (Phase 5)" section and gave it its own new "App feedback /
build workflow" section instead; reworded `build-questions.md`'s queued
write-up to drop the "decide together with Phase 5" framing and make the
submitter explicitly "a logged-in org member," not a public/anonymous
visitor. The security recommendation from entry (7) (auto-trust tied to
real auth, not a text-string marker) is unchanged — still correct
regardless of which feature this is. No code this entry.

### 2026-08-28 (7) — Queued a 6th item: in-app feedback → build
### instructions loop, with a flagged trust/auth concern

Owner asked whether an in-app feedback area (possibly AI-powered) could
write updates into a repo markdown file for the next build to read,
gated so anything not carrying the owner's initials ("CC") requires
human review first. Discussed rather than just recorded, then queued —
same PM-only scope as entry (6):

- **Real security flag, not just a design nitpick:** a bare "contains
  the string CC" check is spoofable by anyone who types it into a
  feedback form (including an anonymous public-site visitor, if public
  submission is ever allowed) — recommended the auto-trust gate be tied
  to *how* something was submitted (authenticated as the org
  owner/admin) rather than *what the text says*. "— CC" is still a fine
  convention for the owner to hand-mark endorsed entries when curating
  `build-questions.md` directly — that's the owner editing a repo file,
  not untrusted input claiming its own trust.
- **Overlaps the already-open "Public input" Phase 5 question** (what
  form public input takes, whether it needs moderation) — cross-
  referenced both directions (`docs/open-questions.md` ↔
  `build-questions.md`) rather than tracking it as a fully separate
  feature, since "who can submit, does it need review" is the same
  question in both.
- Full sketch (model shape, unreviewed-queue default, where an AI
  summarization pass would fit) in `build-questions.md`. Not built —
  queued, no code this entry.

### 2026-08-28 (6) — Queued five items for the next build (no code this
### entry — this session stays in the scope its own trigger set)

Owner explicitly asked to *queue* these for a future build session, not
implement them now — matches this session's own scope (see entry (5))
and the "Working conventions" rule it added: gather/record/queue, don't
build, unless explicitly told to build *this session*. Recorded in
`build-questions.md`'s new "Queued 2026-08-28 (owner directive)" section
— full detail there, short version here:

1. Property view: drop the per-record checkbox, pin a record by
   pressing/tapping its card instead (in addition to scroll-focus).
2. **Bug**: the last item(s) in the property view's combined list can
   never be scrolled into focus — root-caused (not just noted) to
   `useFocusedListItem`'s trigger band sitting near the top of the
   scroll container, which the last card(s) can't always reach even at
   max scroll if they're shorter than `containerHeight - offset -
   bandHeight`. See `build-questions.md` for the fix direction.
3. Soft delete — hide instead of hard-delete, recoverable later. Real
   scope questions not yet decided (which models, retention, who
   restores, cascade behavior) — flagged, not resolved.
4. Species list page needs a search/filter — no scope questions here,
   just not built; the existing `Combobox` filter pattern is the likely
   model.
5. Nav layout: desktop sidebar should start below a dedicated top-left
   logo area instead of running the full viewport height (currently
   overlaps `TopBar`'s top-left corner); mobile brand should center at
   the top instead of sitting left-aligned. No logo asset exists yet —
   flagged as an open question for whoever picks this up.

No code touched this entry. No `docs/manual/` update applies (nothing
user-facing changed — these are all still-queued).

### 2026-08-28 (5) — Corrected entry (4): not all scheduled routines are
### queue-only

Entry (4) below overcorrected: it wrote a blanket "a session that starts
as scheduled/automated is project-manager mode only" rule. The owner
pointed out this is false — they run more than one scheduled routine,
and at least one ("a programmer routine") is explicitly meant to
implement and push code. Reworded the "Working conventions" bullet: the
actual rule is per-session-instructions, not per-trigger-type — a
session scoped by its own triggering instructions to gather/clarify/
record/queue (like the open-questions routine that started this day's
session) stays in that scope for its whole lifetime including once a
live human joins, rather than being upgradeable by an inferred read of a
detailed live request; a session actually scoped to implementation just
implements, same as always. No code changes.

### 2026-08-28 (4) — New rule: scheduled sessions are project-manager mode
### only, for their whole lifetime

Follow-up to entry (3) below: after that mid-session implementation
shipped, the owner flagged that this session began as a scheduled
"compile open questions, don't trigger a build" task and should have
stayed queue-only for its entire lifetime, not just its first turn —
the property-view feature in (3) should have been recorded as a queued
spec (like the vanity-slugs/QR-generator items in entry (2)) rather than
built and pushed. **Owner's call: keep the shipped code** (already live
on `main`), but add a firm, durable rule going forward. Added to
"Working conventions" above. Also confirmed: the scheduled trigger
itself (whatever created this session on a schedule) is configured on
claude.ai outside this repo — a session has no tool access to edit that
stored prompt directly (same caveat as the branch-assignment issue in
entry (2)) — so the rule lives here, as the default posture, rather than
depending on that external prompt's wording.

### 2026-08-28 (3) — Combined activity/sighting list with scroll-to-focus
### map selection; fixed a desktop layout bug on the public site

Three explicit asks, same session as the open-questions review above (and
on `main`, per that entry's branch-policy change):

1. **Combine the activity and sighting listings on the property view**
   (both the logged-in `PropertyMapPage` and the public
   `PublicPropertyPage`) **into one list, and drive what's shown on the
   map by scroll position** rather than a "hide/show every record"
   checkbox set: a colored background highlights whichever card is
   currently scrolled into a trigger band near the top of the list, and
   *that* record is the one drawn on the map. A checkbox per record still
   exists, but its meaning changed — it now **pins** that record so it
   stays shown regardless of scroll, letting more than one show at once.
   The old **Hide all from map** bulk button is now **Clear all**,
   clearing every pin (not hiding every record) — with pinning now
   opt-in rather than opt-out (default: nothing pinned, just follow
   scroll), "hide everything" no longer means anything on its own.
2. **Public site desktop layout bug**: `PublicOrganizationPage` and
   `PublicPropertyPage` reuse `.app-shell`/`.app-main` for the shared
   top-bar styling, but `.app-main`'s `margin-left: 220px` (reserving the
   authenticated app's sidebar-nav gutter) applied unconditionally by
   class name alone — since the public pages render `PublicHeader`
   instead of `AppShell`'s sidebar nav, this left a blank 220px strip
   down the left side of every public page on desktop. Fixed with a new
   `.app-shell--public` modifier class (higher-specificity override, so
   it wins regardless of CSS source order) rather than touching the
   authenticated shell's rule.
3. **Public site "make full use of real estate"**: beyond the margin
   bug, `PublicOrganizationPage`'s property list was still capped at the
   authenticated app's 640px form-width (`.page`), reading as a narrow
   off-center column with nothing else on the page. New `.page--public`
   (1100px max-width) plus `.card-list--grid` (responsive grid at
   ≥640px) so the property list actually fills a wide desktop viewport
   instead of stacking single-file.

**Implementation notes:**
- New `useFocusedListItem` hook (`hooks/useFocusedListItem.ts`) —
  IntersectionObserver-based scroll-spy against a caller-supplied
  scroll container and item-id list, rather than a hand-rolled scroll
  handler; recomputes its trigger-band `rootMargin` via `ResizeObserver`
  since the container's height depends on viewport size (the map above
  it is a `vh`-based height). Shared by both pages.
- **Deliberately did not draw a separate overlay element** for the
  "colored background the height of a single entry" — a real card's
  height varies with its content (species names, notes, badges), so a
  fixed-height overlay would need constant resyncing with whatever card
  it's supposed to be sitting over. Simpler and exactly as visible:
  give the *focused card itself* (`.card--focused`) the colored
  background — its height is trivially "the height of that entry"
  because it *is* that entry.
- Both pages now sort activities and sightings into one list by the
  most meaningful date each type has (an activity's done date if set,
  else planned date; a sighting's observed date), newest first, with
  undated records sorted last rather than dropped. A small
  `.type-badge` pill (`Activity`/`Sighting`) replaces the old
  section headings so the type is still obvious per-row.
- `PublicPropertyPage` previously had **no** map-visibility controls at
  all (always drew every record) — it gets the full pin/scroll-focus/
  Clear-all treatment too, since it's a client-only viewing preference
  that doesn't need auth or write access.
- **Not implemented**: no "show everything" bulk button (removed in the
  2026-08-27 session's checkbox model and not reintroduced here — the
  combined list plus pinning already covers it, and a previous session
  explicitly dropped the mirror "Show all" button as one-bulk-button-is
  -enough).
- **Docs:** `docs/manual/properties.md`'s "Choosing what's plotted on
  the map" subsection rewritten for the new scroll-focus/pin model;
  `docs/manual/public-site.md` updated to describe the same behavior on
  the public property page.
- **Screenshots not regenerated this session**, despite being within
  the once-per-calendar-date allowance (last run was 2026-08-27) and
  `property-map-with-records.png`/`public-property.png` now being
  actively wrong (old two-section layout, no highlight, no type
  badges) rather than just stale — an explicit judgment call: actually
  running `capture.js` needs a full live backend+frontend+PostGIS stack
  brought up from scratch in this sandbox (GDAL/PostGIS aren't
  installed this session, unlike some prior sessions that did that
  setup), which is disproportionate to this session's actual scope.
  Flagged here instead of silently skipped — next session touching
  screenshots should regenerate both images.
- **Verified without a live backend**: no GDAL/PostGIS/Django stack was
  set up this session (frontend-only change; see screenshot note
  above). Instead: `tsc -b && vite build` clean, then a scratch
  Playwright script (`vite preview` + `page.route()` mocking the public
  API endpoints with synthetic activities/sightings — no real backend
  needed since `PublicPropertyPage`/`PublicOrganizationPage` don't
  require auth) confirmed: the combined list renders and sorts
  correctly; exactly one card is ever focused/highlighted, and it
  changes correctly as the list is scrolled through several positions
  (top/middle/bottom); pinning a record increments the "Showing X of Y"
  hint by exactly one and reveals **Clear all**, which resets the pin
  count back down; `.app-main`'s computed `margin-left` on the public
  pages is `0px` at a 1280px desktop viewport (was `220px`); and
  `.page--public` renders at its 1100px cap instead of 640px. No
  unexpected console errors/warnings (React key/DOM-nesting warnings
  included) beyond the expected `/api/auth/me` connection-refused noise
  (no backend running) and headless WebGL performance notices seen in
  prior sessions too. `PropertyMapPage` (the authenticated admin page)
  was **not** independently live-tested this session — it shares the
  exact same hook and combined-list/sort/pin logic verified above on
  the public page, and `tsc`/`vite build` cover it, but confirm it
  against a real login session before treating it as equally proven.

### 2026-08-28 (2) — Open-questions review with the owner; branch policy
### change (commit directly to `main`)

A scheduled task earlier the same day (see its own entry immediately
below) compiled the current `docs/open-questions.md` list into
`build-questions.md` and pushed it on a feature branch, per that task's
"don't trigger a build" instruction. This entry is the live follow-up
where the owner actually reviewed and answered it.

- **Branch policy: sessions now commit directly to `main`**, not a
  per-session feature branch — explicit owner instruction ("again, all
  future sessions can commit directly to main"), given twice now. This
  session merged the scheduled task's `claude/relaxed-mendel-esas6c`
  branch into `main` (fast-forward) and worked directly on `main` from
  that point on. **Caveat noted back to the owner:** the "develop on
  branch X" assignment a session gets at startup is set by the
  platform/scheduler config (session/schedule settings on claude.ai), not
  something a session can change for *future* automated runs — if a
  scheduled trigger keeps handing out a fresh feature branch, that's the
  thing to update there, not something this file can fix.
- **Decisions recorded** (owner review, all 2026-08-28, full text now in
  `docs/open-questions.md`'s "Recently resolved" section and
  `docs/data-model-notes.md`):
  - Hosting/ops model and real email delivery (SMTP) — **dismissed for
    now**, not answered, still open.
  - Sensitive-sighting default visibility — **decided**: an
    organization's own call, set **per property** (not a
    sensitive-species-list auto-detection mechanism as originally framed
    in the question). Reframes the data-model shape: implies a new
    `Property`-level field, not a species-list flag. **Not implemented
    this session** — recorded as a follow-up build item.
  - Default workflow states (Planned → In Progress → Done seed) —
    **confirmed as-is**, no change.
  - Public site surfacing the sighting↔activity link — **decided: yes**.
    **Not implemented this session** — follow-up build item.
  - Starter species list — **confirmed**: stays empty, no starter list.
  - Licensing of public data — **decided**: leave unlicensed for now.
  - **New, raised mid-review (not from the original scan): vanity slug
    URLs** — decided shape: one vanity slug per organization
    (`/public/<org-slug>`), sub-slugs for its properties underneath
    (`/public/<org-slug>/<property-slug>`). Queued for the next build,
    not started.
  - **New: QR code generator for public URLs**, to ship alongside the
    slugs above — generates a scannable code for a public org/property
    URL, with an option to embed a center image (e.g. a logo). Queued for
    the next build, not started.
- **This session's own scope: docs/decisions only, no code.** Updated
  `docs/open-questions.md` (moved five items into "Recently resolved",
  added the two new queued items to "Tech / infrastructure"),
  `docs/data-model-notes.md` (sighting public-visibility section,
  reframed to the per-property decision), and `build-questions.md`
  (status index reflecting all of the above). No models/migrations/API/
  UI touched — those are the four follow-up build items above, left for
  a future session. No `docs/manual/` update applies (no user-facing
  behavior changed yet).
- **Not verified against a live stack** — doc-only session, nothing to
  run `manage.py check` or `tsc -b` against.

### 2026-08-28 — Docker publish: only rebuild the image whose files changed

Explicit ask: don't waste Action runtime rebuilding both images when a
push only touched files that aren't built into either one. Reworked
`.github/workflows/docker-publish.yml` to gate each matrix build on its
own build inputs.
- Added a `changes` job using `dorny/paths-filter@v3` that reports
  whether `backend/**` and/or `frontend/**` changed on the push; the
  `build-and-push` job `needs` it and each matrix step is gated by a
  `guard` step (`needs.changes.outputs[matrix.name]`, indexing
  backend/frontend by the matrix entry's name).
- **Tag/release and manual runs still build BOTH images** regardless of
  the diff (`startsWith(github.ref, 'refs/tags/') || github.event_name
  == 'workflow_dispatch'` short-circuits the gate) — a `vX.Y.Z` release
  should publish a complete, matched set, and the changes-filter has no
  meaningful base to diff against on a tag push anyway. So the
  conditional behavior only applies to pushes to `main`.
- Since each image's build context is exactly `./backend` / `./frontend`,
  editing docs, `docker-compose.yml`, `CLAUDE.md`, or the workflow file
  itself now rebuilds **nothing**. Deliberately did *not* treat a change
  to the workflow file as a reason to rebuild — matches the ask (only
  rebuild when an image's actual inputs change).
- Tag policy is unchanged (`latest` on main, semver on a `vX.Y.Z` tag).
- **Not verified against a live run** (same no-Docker-Hub-credentials
  limitation as the workflow's original 2026-08-26 session and the
  2026-08-27 tag-fix session): validated the edited YAML with
  `python3 -c "import yaml; yaml.safe_load(...)"`. First real push to
  `main` that touches only one folder is the actual end-to-end test.
  No code/model/UI touched, so no `docs/manual/` update applies.

### 2026-08-27 (5) — "Forgot password" reset flow + invitation resend

Picked up two concretely-scoped, already-called-out gaps rather than a
new product decision: `open-questions.md`'s "Auth and API" section had
explicitly noted "Also blocks a 'forgot password' reset flow" ever since
the 2026-08-26 invite-flow session, and the pending-invitations UI had
no way to fix an invite that expired before anyone accepted it short of
revoke-and-recreate.

- **Backend: `PasswordResetToken` model** (`apps/accounts/models.py`,
  migration `0005_passwordresettoken.py`) — one-time, one-hour-expiry
  token per user, same "opaque unguessable token + `is_expired`
  property" shape as `Invitation` but its own model (no org/role scope,
  much shorter expiry, single-use via `used_at`). New
  `apps/accounts/password_reset.py` mirrors `invitations.py`'s
  `send_invitation_email` pattern (same real-email-not-configured
  caveat — see below). Two new `AllowAny` endpoints:
  `POST /api/auth/password-reset/` (always returns the same generic
  "if an account exists…" 200 regardless of whether the email has one —
  deliberately not branching, to avoid turning this into a
  user-enumeration oracle — and deletes any previous unused token for
  that user before minting a new one) and
  `POST /api/auth/password-reset/confirm/` (token + new password; a
  bad/expired/already-used token all get the same generic 400, same
  "don't confirm what's behind an opaque token" stance as invitation
  accept; success sets the password, marks the token used, and logs the
  user in immediately — same convention as signup/invitation-accept).
  **Unlike the invite flow, there's no admin-UI fallback for a case
  where the email doesn't arrive** — returning the reset link directly
  in the API response (the invite flow's fallback) would itself leak
  whether an email has an account, so this flow is genuinely only
  exercisable via real email delivery or reading the console-backend
  log; noted in `open-questions.md`.
- **Backend: `POST /api/org/invitations/<id>/resend/`** (admin-only,
  `InvitationViewSet.resend`) — bumps `created_at` (which `is_expired`
  measures from) and re-sends the invitation email, keeping the same
  token rather than minting a new one since a previously-shared/received
  link should keep working. Fixes the "invite expired before anyone
  used it" case without revoke-and-recreate.
- **Frontend:** `ForgotPasswordPage` (`/forgot-password`, linked from
  `LoginPage`) and `ResetPasswordPage` (`/reset-password/:token`, both
  outside `RequireAuth` like the other pre-session-auth pages) —
  `AuthContext` gained `requestPasswordReset`/`confirmPasswordReset`
  alongside the existing `login`/`signup`/`acceptInvitation`. A **Resend**
  button on `OrgAdminPage`'s `PendingInvitationRow`, next to the existing
  Copy-link/Revoke actions.
- **Real bug found (and fixed) by testing at a phone viewport with an
  unusually long test email, not by reading the diff:** `.card__row`'s
  first child (the div wrapping an email address, used by both
  `MemberRow` and `PendingInvitationRow`) had no `min-width`/wrapping of
  its own — a long-enough email forced the row wider than the card
  instead of wrapping, independent of how many action buttons sat next
  to it (reproduced the same overflow on `MemberRow`, which has only one
  button, via `git`-free A/B — confirmed it wasn't specific to adding a
  third button to the pending-invitation row). Fixed generically with
  `.card__row > :first-child { min-width: 0; overflow-wrap: anywhere; }`
  rather than a one-off class, since the same shape (email + actions)
  recurs. Confirmed via `scrollWidth`/`clientWidth` comparison before/after,
  not just a screenshot.
- **Also fixed, found while updating this same area of the docs:**
  `open-questions.md`'s "Recently resolved" note on property-scoped
  roles claimed scoping was "enforced the same way" as account-role
  checks — it isn't; `org_scoping.py` only ever filters by organization,
  never by `Membership.properties` (confirmed by reading the actual
  permission/queryset code). `docs/manual/roles-and-permissions.md` and
  `limitations.md` already had this right — only `open-questions.md`'s
  summary was stale/wrong. Corrected in place rather than left for a
  future session to trip over, per this file's own "wrong prose next to
  an edit" precedent.
- **Docs:** `docs/manual/getting-started.md` gained a "Forgot your
  password?" subsection under "Logging in"; `account.md` swapped its
  stale "no forgot-password flow" line for a link to the new one;
  `organization-admin.md`'s "Pending invitations" section documents
  Resend and the "(expired)" flag staying visible instead of vanishing.
  `open-questions.md`: moved both features into "Recently resolved",
  updated the "Real email delivery isn't configured" bullet to cover
  the reset flow too (and its extra enumeration-avoidance constraint),
  and fixed the property-scoping inaccuracy above.
- **Verified for real:** installed GDAL/GEOS/PostGIS system packages and
  a local PostgreSQL 16 in this sandbox (same fallback prior sessions
  documented), ran `makemigrations`/`migrate`/`makemigrations --check`
  clean, then curl-drove both new endpoints directly: identical generic
  response for an existing vs. nonexistent email (no enumeration), weak-
  password rejection, bad-token rejection, a successful reset, confirmed
  the session is live immediately after (auto-login), confirmed the old
  password then fails and the new one works, confirmed the same token
  can't be reused (400), and confirmed `resend` 404s across organizations
  and re-sends the email with the same token intact. Frontend: `tsc -b`
  and `vite build` clean. Full Playwright, live backend, real browser
  (not simulated): signup → log out → forgot-password with a real and a
  fake email (byte-identical confirmation message) → extracted the reset
  link from the (console-backend) server log → mismatched-confirmation
  client-side validation → successful reset → auto-logged-in landing on
  the dashboard → old password rejected / new password accepted → the
  same reset link rejected on reuse with a friendly message. Separately:
  admin invites a member → Resend → confirmed exactly one additional
  invitation email sent (not zero, not two) → the invitee still joins
  successfully via the resent invitation's unchanged token. Also
  re-verified both flows still pass after the `.card__row` CSS fix, and
  screenshotted the fixed pending-invitations card at a 375px viewport
  to confirm the email wraps instead of clipping.
- **Screenshots:** `docs/manual/images/` was already regenerated once
  today (the earlier "Help nav link" session), so per the once-per-
  calendar-date cap this session did **not** re-run `capture.js`.
  `org-admin.png` now shows one fewer action button than the live page
  (Copy invite link / Revoke, not yet Resend) — same "slightly stale,
  not actively wrong" case the cap's own carve-out describes (the image
  still accurately shows what a pending invitation looked like at
  capture time), not a renamed/removed control, so left for the next
  regen rather than run twice today. `capture.js` itself needed no
  changes — it doesn't click or select on those specific buttons.
- **Not done:** no rate limiting on the password-reset request endpoint
  (an unauthenticated user could spam it for a given address — low
  practical risk today at this project's scale, but worth noting for
  when real email delivery exists and sending costs something); no
  "resend" equivalent for the reset flow itself (requesting again from
  `/forgot-password` already covers it — it just invalidates the older
  token); real SMTP configuration is still not done — this flow, like
  the invite flow, remains console-log-only until that's picked (see
  "Hosting/ops model" in `open-questions.md`).

### 2026-08-27 (4) — Docker publish: dropped the per-commit sha tag

Explicit ask: "github action is pushing branch name. I only want latest
from the main branch, GitHub tags/release for other tags." Checked the
actual GitHub Actions run logs rather than guessing — the workflow's
triggers were already correctly scoped (push to `main`, or a `v*.*.*`
tag; no branch-push trigger for other branches), but its
`docker/metadata-action` tag list also included `type=sha`, so every
push to `main` produced two Docker Hub tags — `latest` *and* the short
commit sha (confirmed from a real run's logs:
`habitat-backend:latest,habitat-backend:46f93e9`) — the extra tag the
author didn't want. Removed `type=sha` from
`.github/workflows/docker-publish.yml`'s tags list; a push to `main`
now produces only `latest`, and a `vX.Y.Z` tag/release push produces
only that version number. No other changes — no code/model/UI touched
this session, so no `docs/manual/` update applies.
- **Side effect worth knowing:** a manual `workflow_dispatch` run from
  a branch that's neither `main` nor a version tag will now produce
  zero matching tags and fail outright (previously it would have
  silently pushed a stray sha-tagged image) — this is the correct
  enforcement of "only latest from main, tags for other tags," not a
  regression, but noted here in case a future session sees that
  failure and wonders why.
- **Not independently re-verified against a live Docker Hub push** (no
  credentials in this sandbox, same limitation as the original
  2026-08-26 session that added this workflow) — verified by reading
  the actual GitHub Actions run history/logs for this workflow via the
  GitHub API instead, confirming the exact tag list a real run
  produced before this fix, and validated the edited YAML with
  `python3 -c "import yaml; yaml.safe_load(...)"`.

### 2026-08-27 (3) — Nav: a way to reach the manual from the app

Explicit ask: the logged-in UI needed a way to actually get to the
manual (`docs/manual/`) — there was previously no in-app link to it at
all. **Assumption, since there's no in-app docs viewer and no docs-
hosting decision yet** (see `docs/open-questions.md`, "Hosting/ops
model"): added a new **Help** entry to `BottomNav.tsx` (between Public
site and Admin — grouped with Public site as the other "opens in a new
tab, leaves the app" link), linking straight to
`docs/manual/README.md` **on GitHub at `main`** (not a branch-relative
or in-app path) so the link is stable and always shows the current,
merged manual rather than a feature branch's in-progress copy. Revisit
this if/when Habitat gets a real hosted docs site — this is the
simplest thing that actually works today, not a permanent answer.
Updated `docs/manual/getting-started.md`'s nav bullet list to match.
- **Verified for real:** installed GDAL/GEOS/PostGIS + a local
  PostgreSQL 16 in this sandbox (same fallback prior sessions
  documented), ran the signup → dashboard flow with Playwright at three
  viewports (390px, 1280px, and the tighter 375px/iPhone SE), confirmed
  exactly one Help link renders with the correct `href`/`target="_blank"`,
  and — since this pushes the bottom tab bar to 8 items on mobile —
  explicitly measured `.app-nav`'s `scrollWidth` against the viewport
  width at 375px to rule out horizontal overflow/clipping rather than
  just eyeballing a screenshot: they matched exactly (no overflow), with
  flexbox correctly giving the longest label ("Properties") more room
  and shrinking the rest, so nothing overlaps or clips even on the
  narrowest common phone width. Visually dense at 8 items on a small
  phone, but legible and fully on-screen. `tsc -b && vite build` clean.
- **Not done:** no in-app documentation viewer (this just links out to
  GitHub); the Help link isn't shown on the unauthenticated pages
  (login/signup/public site) — only inside the logged-in app's nav,
  since that's what was asked for.

### 2026-08-27 (2) — Manual: linked chapter-to-chapter navigation path

Explicit ask: docs should link to each other, or at least form a
readable path starting from Getting started through to the rest, rather
than requiring a reader to keep returning to the chapter index. Added a
`---` + `[← Previous](...) · [Manual index](README.md) · [Next →](...)`
footer to the bottom of all 13 `docs/manual/` chapters, forming one
linear chain in the same order as `README.md`'s chapter list
(`getting-started.md` → `dashboard.md` → `properties.md` →
`activities.md` → `sightings.md` → `linking-sightings-activities.md` →
`species.md` → `tasks.md` → `roles-and-permissions.md` →
`organization-admin.md` → `account.md` → `public-site.md` →
`limitations.md`, first/last chapters missing the not-applicable
prev/next respectively). Documented the convention in both
`docs/manual/README.md`'s "Keeping this manual current" section (the
mechanics: splice a new chapter into the chain, don't just add it to the
index) and here, so it doesn't quietly rot the next time a chapter is
added. Also fixed one stale line noticed while touching `account.md` —
it still described a newly-added member logging in with "the initial
password an admin set for them," which the 2026-08-26 invite-flow session
replaced with an emailed/shared accept link; not something this session
was otherwise touching, but wrong prose sitting right next to an edit is
worse to leave than to fix. No code changes.

### 2026-08-27 — Logged-in UI pass: Combobox pickers, map item selection,
### a dashboard landing page

Explicit ask, in stages: (1) the app's association pickers (linking a
sighting/activity, an activity's species, a task's assignee/origin) were
plain `<select>`s that "will not scale with more data"; (2) the property
map always plotted every loaded activity/sighting with no way to choose
what shows; (3, added mid-session) the logged-in landing page should
surface tasks/recent sightings/activities instead of dropping straight
into the properties list; (4) a "planned/upcoming activities" section on
that landing page, its own section, hidden when nothing's upcoming; (5)
while scrolling the record lists that pick what's on the map, the map
itself should stay pinned in place — generalized, on request, to *every*
page with a map, not just that one. No backend/model changes — this was
entirely `frontend/`.

- **New `Combobox` component** (`components/Combobox.tsx`) — a
  hand-rolled type-to-filter picker (no new dependency, same "don't add a
  UI-kit for one component" reasoning as the no-drawing-library decision
  for map polygons): focus opens a filtered list of all options, typing
  narrows it (plain case-insensitive substring match, capped at 50
  rendered rows so a very long list doesn't bloat the DOM), arrow
  keys/Enter/Escape work, and a selected value shows with a × to clear
  back to unset — the same "Unassigned"/"None" affordance the `<select>`s
  it replaces had via their empty first option. Client-side filtering
  over an already-fetched list, not server-side search — fine at a single
  org's current scale; noted in the component's own comment as the thing
  to revisit if a list ever gets large enough that even fetching it all
  stops being reasonable.
  Wired in everywhere a `<select>` picked one record out of a growable
  account-wide list: `LinkedRecordsPanel` (sighting↔activity linking),
  `ActivitySpeciesPanel` (species picker in the add-row), `TasksPage`
  (assignee — both the add-task form and each task row's inline
  reassign — and the add-task form's origin-sighting/origin-activity
  pickers), and `SightingFormPage`'s own species field. Left alone:
  small, fixed-size enums (activity type, workflow status, a species
  link's role) — those aren't the "won't scale" problem this was solving.
- **Map item selection on `PropertyMapPage`.** Each activity/sighting
  card in the lists below the map now has its own checkbox — checked
  (the default, for every record) means it's plotted on the map,
  unchecked hides it, independent of the pre-existing public/private
  load-time toggle. A `map-selection-hint` line above the lists reports
  "Showing X of Y activities and X of Y sightings on the map." Each
  section also got a **Hide all from map** bulk button. **Deliberately
  dropped the mirror "Show all on map" bulk button** — added first, then
  removed per explicit follow-up feedback mid-session; individually
  re-checking a record (or just reloading the page, which resets the
  in-memory hidden-set state) already covers restoring visibility, and
  one bulk button reads cleaner than two. State is two `Set<number>` of
  *hidden* ids (not *visible* ones) specifically so a newly-created
  record defaults to shown without needing to be added to anything.
- **Dashboard landing page** (`pages/DashboardPage.tsx`), now what `/`
  renders (was a bare `<Navigate to="/properties">`) and what
  login/signup/accept-invite already navigate to post-auth without any
  of their own changes needed. Up to four sections, each just linking
  out to the real page for that data (read-only summary, not a new place
  to edit anything): **Your tasks** (assigned to the current user,
  open/assigned only, newest first), **Planned / upcoming activities**
  (not-done activities across every property, soonest-planned-first —
  **hidden entirely, not just empty, when nothing qualifies**, per the
  explicit ask), **Recent activities** and **Recent sightings** (newest
  *logged*, i.e. `created_at`, across every property — deliberately not
  the activity's planned/done date or the sighting's observed-at time,
  which still show on each row). All client-side sorted/sliced from the
  same org-wide list endpoints `TasksPage`/`PropertyMapPage` already
  call — no new API surface. New "Home" nav entry (first in the list,
  🏠) alongside the existing ones; `App.tsx`'s `"/"` route now renders
  `DashboardPage` directly.
- **Real bug found and fixed by actually scrolling a short page in
  Playwright, not by reading the CSS:** the first pass at "pin the map
  while scrolling" used `position: sticky` on `.map-panel`. That looked
  right on a page with a long record list, but on a *short* one (a
  property with only a couple of records, or the create/edit draw
  forms' own short form) the map's reserved height in the document flow
  is taller than the remaining scrollable distance, so the browser never
  lets the sticky element go before you reach the bottom — the still-
  "stuck" map visually overlapped the tail of the content scrolling
  underneath it. Fixed by replacing sticky with a split-scroll-region
  layout instead: `.page--map` is sized to exactly the viewport's
  available height (`overflow: hidden`), `.map-panel` is a plain
  (non-sticky) fixed-height flex item, and everything below it on every
  page that has a map (`PropertyMapPage`, `PublicPropertyPage`,
  `ActivityFormPage`, `SightingFormPage`, `PropertyFormPage` — applied to
  all of them per the explicit "any page with a map" follow-up) is
  wrapped in a new `.map-page-scroll` div with its own
  `overflow-y: auto`. The map and the scrollable content now literally
  can't occupy the same pixels, so there's no overlap edge case to find
  at any content length — confirmed by re-running the same short-page
  Playwright scroll test that caught the sticky bug, and by checking
  `getBoundingClientRect()` before/after scrolling directly (map: same
  position; content: moved within its own box, invisible above/below its
  own clipped region rather than overlapping the map).
- **Docs:** new `docs/manual/dashboard.md` chapter (linked from
  `README.md`, right after "Getting started" since it's the new landing
  page) covering the four sections and what's hidden when empty.
  `getting-started.md`'s "What you'll see after logging in" now leads
  with the dashboard instead of the properties list, and gained a "Home"
  bullet (plus a missing "Account" bullet the nav list had never
  mentioned). `properties.md` gained a "Choosing what's plotted on the
  map" subsection and a note that the map stays fixed while the lists
  below scroll. `public-site.md` got the matching one-line note for the
  public property page. `tasks.md`, `linking-sightings-activities.md`,
  `activities.md`, `sightings.md` each reworded their "dropdown"
  language to describe the search-box Combobox behavior instead.
- **Screenshots:** ran `capture.js` for real (first regen today, after
  yesterday's — within the once-per-calendar-date cap) — it needed real
  updates, not just a re-run, since the old script's post-signup
  `waitForURL('**/properties')` would have hung forever against the new
  dashboard-first landing route, and the sighting-edit-linked step's
  `.field-row select` locator no longer matches anything now that
  panel's a Combobox. Added a `pickCombobox()` helper, fixed both call
  sites, added `dashboard-empty.png` and `dashboard-populated.png`
  (linked from `getting-started.md` and the new `dashboard.md`), and
  changed the tasks-page step to actually submit its first task (via the
  new assignee/origin Combobox pickers) rather than just filling the
  form unsubmitted — needed a real task in the list both to make
  `tasks.png`'s own caption ("task list... and the Add a task form")
  accurate and to give the populated-dashboard screenshot a real "your
  tasks" entry. Also dropped the `properties-empty.png` capture — no
  chapter references it anymore now that `dashboard-empty.png` covers
  the "what you land on after signup" screenshot instead — and deleted
  the now-orphaned file from `docs/manual/images/`.
- **Verified for real:** installed GDAL/GEOS/PostGIS system packages and
  a local PostgreSQL 16 in this sandbox (same fallback prior sessions
  documented), ran the full flow end-to-end with a hand-written
  Playwright script (separate from `capture.js`) asserting on real DOM
  state rather than just screenshotting: signup lands on the empty
  dashboard; the ActivitySpeciesPanel and LinkedRecordsPanel Combobox
  pickers actually create the species-link/sighting-activity-link they're
  driven to select; a task created via the assignee/origin Combobox
  pickers shows up in the list and, from the current user's own
  assignment, in the dashboard's "Your tasks"; "Planned / upcoming
  activities" appears while an activity is un-done and *disappears*
  (not just renders empty) once both seeded activities are PATCHed to a
  done workflow state; the map-selection hint text updates correctly
  through unchecking a single card, "Hide all from map," and re-checking
  a card by hand; and that "Show all on map" no longer exists as a
  button. Separately confirmed the sticky-map bug and its fix by reading
  `getBoundingClientRect()` of `.map-panel`/`.record-lists` before and
  after a manual scroll on a short page, both before the fix (showed the
  overlap numerically) and after (showed none). `tsc -b && vite build`
  clean throughout. Also spot-checked a 1280px desktop viewport (sidebar
  nav layout) for the dashboard and map-selection UI, not just the
  390px mobile viewport the detailed script used.
- **Not done:** Combobox filtering is still client-side/all-loaded, not
  server-side search — fine at current scale, flagged in the component's
  own comment as the thing to revisit if that stops being true; no
  per-user dashboard customization (reordering sections, row counts);
  map item-selection state isn't persisted (resets on navigation/reload
  — arguably a feature, since it means a fresh visit always starts from
  "everything shown").

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
