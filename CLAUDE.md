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
- `docs/deployment-config.md` — every environment variable the app reads
  (backend settings + Vite build vars), with the recipe for serving the
  public site on its own origin. **Add any new environment-specific value
  here** rather than hardcoding a hostname/flag in application code.
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
  frontend test runner TBD. **The first backend tests landed 2026-09-04**
  — `backend/apps/public_site/tests.py`, joined 2026-09-06 by
  `backend/apps/accounts/tests.py` (the image-upload allowlist) and
  `backend/config/tests.py` (the transport-security settings, plus
  Django's own deploy checks run against a resolved `DEBUG=0`
  configuration). Run one with `python manage.py test apps.public_site`,
  or all three with `python manage.py test`. They use Django's built-in
  runner deliberately (no new dependency, and adopting pytest stays an
  open call). Most verification in this repo is still done by driving a
  live stack, as the task-log entries describe; a checked-in test earns
  its place when an invariant has already regressed silently once.
  **CI runs them as of 2026-09-05** — `.github/workflows/tests.yml`, on
  every push to `main` and every pull request: `manage.py check`,
  `makemigrations --check --dry-run` and `manage.py test` against a real
  `postgis/postgis` service container, plus `npm ci`/`tsc -b`/`vite build`
  for the frontend. It needs no secrets. **It does not gate image
  publishing** — whether `docker-publish.yml` should `needs:` it is an
  open question for the owner, not a build-session default. A green CI run
  is a floor, not a substitute for driving a live stack: it currently runs
  126 backend tests across six modules, and there is still no frontend
  test runner. Each *test class* exists because an invariant had already
  broken once — that is the bar for adding one, not coverage for its own
  sake. (`apps/accounts/tests.py` now carries seven unrelated defects, D6,
  D8, D10, D14, D16, D17 and D22, in seven clearly-separated sections
  rather than
  one theme — D14 lives there because the shared helper it exercises,
  `apps/accounts/query_params.py`, does, even though the endpoints it
  covers are in four other apps;
  `apps/feedback/tests.py` joined 2026-09-07 for D9, and
  `apps/activities/tests.py` + `apps/species/tests.py` 2026-09-08 for D12
  and D13, with D18 joining `activities` 2026-09-10.) **One test there is
  worth knowing about before you judge a suite by its red-path count:**
  D9's timing-compare fix has no functional symptom, so 9 of its 10 tests
  pass against the pre-fix code by design and the tenth asserts the
  *mechanism*. A test can be right and still not fail on the bug — say
  which one is doing the work.
  **D16 (2026-09-09) adds the one thing this suite didn't have: a
  genuinely concurrent test.** Its `TransactionTestCase` runs two real
  threads against real Postgres, because the defect only exists across
  committed transactions — a plain `TestCase` wraps the whole test in one
  and the race disappears. It also pairs the concurrency tests with a
  *mechanism* test asserting the `SELECT ... FOR UPDATE` is actually
  issued: a race that happened to serialize on a fast machine would let
  the concurrent tests pass against broken code, and the mechanism test
  can't. Copy that pairing if you ever test another race.
  **D17 (2026-09-10) generalizes that pairing past races, and shows how to
  prove a mechanism test earns its place.** The defect is "the guard runs
  after the work it prevents", so the outcome (a 400) is identical whether
  the fix is right or useless. Rather than assert that in prose, the run
  wrote the *naive* fix — decode first, measure after — and ran the suite
  against it: both outcome tests passed, and only the mechanism test went
  red. If you add a mechanism test, build the plausible-but-wrong fix and
  show it catches that; a red path against the *original* bug doesn't
  demonstrate this, because the ordering tests fail on the status code
  first and never reach their own assertion. Two of D17's tests also prove
  ordering with no patching at all, by sending a body whose *content*
  would produce a different error message if it had been looked at.
  **D18 (2026-09-10) is the third application of that pairing, and it
  produced the sharpest argument yet for building the naive fix.** The
  wrong fix there — an application-level `.exists()` re-check with no
  database constraint — doesn't just fail to help: it takes the module
  from 6 failures to 4 by making the *symptom* (a sticky 500) disappear
  **while leaving the race and the duplicate rows completely intact**. It
  is arguably worse than the bug, because the corruption stops announcing
  itself, and every test about the symptom is satisfied by it. Measure
  what a naive fix actually turns green before trusting a smaller failure
  count. D18's concurrency tests also show how to force an interleaving
  honestly: a `threading.Barrier` inside `save()` (the INSERT) holds both
  requests until each has run its own SELECT, so the real `get_or_create`
  and the real endpoint are exercised rather than a stand-in.
  **D22 (2026-09-11) is the clearest case yet that a defect and its most
  tempting bad fix need different tests, and it generalizes past
  ordering.** Its four tests split: one pins the *mechanism* (the message
  doesn't claim delivery), three pin the *constraint* that makes the
  wording hard (the reply is byte-identical whoever asks — the
  anti-enumeration property). Against the original bug **only the
  mechanism test fails**; the three constraint tests pass, because the old
  string was equally generic. Then the plausible-but-wrong fix — stop
  over-claiming delivery *and* be helpfully specific about whether the
  account exists — **passes the mechanism test and fails the constraint
  tests**. Each half is blind to exactly what the other catches. So "does
  the red path reproduce the bug?" is not sufficient evidence a section is
  well-built: ask separately what the *attractive wrong fix* would be, and
  which test stops it. Note also what these tests deliberately don't do —
  assert the literal string, which would have to be edited alongside every
  future copy change while catching nothing.
  **Note the gap `config/tests.py` closed:** `manage.py check` (what CI
  runs) does **not** include Django's deployment security checks, so
  `check --deploy`'s findings sat unread for the life of the project —
  which is exactly how D7 survived. If you add a settings-level
  guarantee, assert it in a test; the checker that would otherwise catch
  it is not wired to anything.

## Task log

Reverse-chronological. Each entry: what was done, key decisions/assumptions
made along the way, and what's left. Keep entries short — this is a pointer
for the next session, not a full changelog (git history is that).

### 2026-09-12 — Scheduled programmer session: built D23 both halves — a
### mistyped address no longer reports itself as a login requirement, and
### the guard this repo already had would have been an open redirect

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/adoring-curie-ea5uk9`, sitting at `b44ff0e` while `origin/main`
was at `4763e17` — local `main` **16 behind**; moved to `main` per this
file's standing rule and fast-forwarded before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy before and after — no blocker. `GET /api/feedback/pull/`
returned `[]` with both negative controls re-run — the **thirty-third**
pull, the steady state.

**The morning check-in left exactly one takeable item; this run took both
its halves and re-deferred the other nineteen** (table in
`build-questions.md`).

**Half 1: a real `NotFoundPage` on the catch-all, deliberately outside
`RequireAuth`.** Two properties are load-bearing and pinned in its
docstring because both are easy to undo by accident: it **renders in place
rather than redirecting** (the old `replace` bounce is exactly why a
visitor couldn't reread their own typo), and it must **stay outside
`RequireAuth`** or the defect returns whole. It echoes the attempted
address as text — not a link, since it is untrusted input that matched no
route — and offers a way on **per audience**, because the two audiences
need opposite things: dashboard/properties for a member, a login link plus
"check the address for a typo" for an anonymous visitor, who is the one
the old behaviour actually stranded.

**Half 2: `?next=` capture, honoured at all ten sites.** Four post-auth
navigations, five `status === "authenticated"` guards, **and the links
between the auth screens** — that last part isn't padding: without it the
return works from whichever screen the bounce happened to land on and
silently fails from the others, the "four filters, not two" failure this
repo keeps naming.

**The transferable finding is about reuse, and it is a new shape for this
repo.** The check-in correctly named `_clean_page_path` as the guard to
reuse — and copying it verbatim would have been an open redirect.
Measured against the real host with a same-origin control rather than
argued from spec: `//evil.com`, `/\evil.com` and tab/newline-assembled
`/<TAB>/evil.com` **all resolve to `https://evil.com/`**, because a
browser normalizes a backslash in a path and strips tab/newline/CR
*before* parsing, so a control character assembles a `//` that isn't
literally in the string. **The naive port passes 29 of 36 unit cases and
leaves all four open.** Every prior "don't half-fix it" lesson here was
about *coverage*; this one is that **an in-repo guard is only safe to
reuse when the new use shares its threat model** — and *displayed* versus
*navigated to* does not.

**Verified.** 36/36 unit cases on the sanitizer; `npm ci`, `tsc -b`,
`vite build` clean, new strings confirmed in the built bundle **against an
unchanged control**. **25/25 in real Chromium at 390px** against the built
bundle served locally with SPA fallback and no backend (the live host was
again unreachable from Chromium through the proxy, as the check-in
recorded). **Against the real pre-fix code 13 of 24 fail**, reproducing
D23 verbatim: `/pubic/test` → `/login`, and **Back lands on
`about:blank`** — stronger than the check-in measured, because `replace`
consumed the only history entry. Nine pass both ways deliberately, and the
four hostile-`?next=` tests are **exactly the ones that catch the naive
fix** (the D22 lesson: a defect and its best bad fix need different
tests); the org-slug control proves the bounce was specific to unmatched
routes.

**Two things caught by looking, not asserting:**

1. **An assertion that passed while testing the wrong page.** The
   "long address doesn't overflow" check used `/public/<long>/<long>` —
   a **valid two-segment route**, so it rendered `PublicPropertyPage` and
   proved nothing. Caught by opening the screenshot and reading *"This
   property isn't public"*. Re-pointed at a genuinely unmatched shape; it
   wraps across three lines, no overflow.
2. **The new source file was binary.** backslash-u escapes in the
   control-character check were interpreted on write, leaving **real NUL,
   0x1f and 0x7f bytes** in `returnTo.ts` — same runtime behaviour, but
   git and grep both treated it as binary (`grep` said "binary file
   matches"). Rewritten as explicit `charCodeAt` comparisons with a
   comment saying why it isn't an escape. **Worth knowing before writing
   any character-class guard through a tool that parses JSON.**

**Also fixed in the same pass**, per the check-in's note:
`PublicOrganizationPage`'s org-root error now reads *"This organization
isn't public, or doesn't exist."* The sweep found **four** *"Couldn't load
this page"* sites rather than the two expected — and the other three are
the genuinely different "a well-formed request failed" case
`RecordNotFound`'s docstring distinguishes, so they were left alone. The
expected count was wrong, not the code.

**Stated plainly rather than left to be inferred:** no backend file
changed, so **no PostGIS stack was stood up and no backend run is
claimed**; **neither half is pinned by a test** (still no frontend test
runner), so a catch-all regression would be caught by nothing; and this is
a *client-side* not-found — the SPA fallback means the HTTP status stays
**200**, so a link checker still won't see a dead address. That last one is
in `limitations.md` rather than quietly skipped.

**Deliberately NOT done:** naming "whoever runs this one" (the check-in's
best-value owner question, and the one piece of D23 a session cannot
supply — D22's shipped message still issues an instruction the app gives no
way to follow); a real 404 status (serving-layer, downstream of the
hosting model); `/admin/*` → `/manage`, which is correct back-compat.

**Docs:** `docs/open-questions.md` (D23 found → built, with the naive-fix
measurement; queue-state records the seventh consecutive one-run cycle and
the reuse lesson; App-feedback the thirty-third pull),
`build-questions.md` (BUILT entry plus the nineteen re-deferrals), and the
manual — `getting-started.md` gains "Following a link into the app" and
"An address that doesn't exist" (the check-in correctly left this for the
session that would make it true) and `limitations.md` the 200-status note.
**No migrations. No screenshots and no `capture.js` change** — the
not-found page is a new state no existing screenshot claims to show (the
D14 precedent), `login.png`/`signup.png` are visually identical since only
hrefs changed, and `capture.js` visits `/login` and `/signup` directly and
waits on `text=Log in`, none of which moved.

**Queue state: empty of authorized work again after one run — seventh
consecutive cycle.** Named successor for the lens, carried from the
check-in: this run covered the user who is *lost*; **the user who is new
is unexamined** — what someone hits between signing up and having any
data, where every list is empty and several screens exist only to be
filled.

**Still open, deliberately:** **who "whoever runs this one" is** (new, and
the cheapest high-value answer in the queue); D22's second half and the
SMTP question; the "super sighting" grouping question; B2 and the
contextual menu (both anchored 2026-09-03); whether CI should gate the
image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass; app-wide rate limiting; the
name-uniqueness casing gap.

### 2026-09-11 (4) — Scheduled programmer session: built D22's fork-free
### half, then the feedback pipeline broke a 31-run silence with two real
### items — and the screenshot said "All 1 sightings"

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/elegant-dirac-j7vrgp`, which already sat at `origin/main`
(`b50b797`) while local `main` was **14 behind**; moved to `main` per this
file's standing rule and fast-forwarded before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy before and after the build — no blocker.

**`GET /api/feedback/pull/` returned two real items, ending thirty-one
consecutive empty pulls.** Worth recording plainly, because the empties
had hardened into an assumption: the streak was a steady state, not a
broken pipeline — the moment a user typed something it came straight
through, and the mechanism needed nothing. Both items were built this run,
one only in part. With the morning check-in's single takeable item that
made three pieces of work; the other seventeen queued items are
re-deferred with stated reasons (table in `build-questions.md`).

**D22's fork-free half: the reset reply no longer asserts a delivery
nothing can verify.** `PASSWORD_RESET_REQUESTED_DETAIL` — a named constant
carrying its own rationale, because the change that would undo this is
someone shortening the message back to something friendlier — now reads
*"…a reset link has been **requested**. Email delivery isn't configured on
every Habitat deployment — if nothing arrives, contact whoever runs this
one."* "Requested" is precisely what the function can vouch for, and the
second sentence gives the locked-out reader somewhere to go. **Resend**
became "Resent" plus a hedge pointing at the **Copy invite link** button
beside it — the two surfaces are worded *differently* on purpose, since
that screen has a self-serve fallback and the reset flow deliberately has
none.

**The verification lesson is the durable part, and it is a generalization
of D17/D18 rather than a repeat.** The four new tests split: one pins the
*mechanism*, three pin the *constraint* that makes this message hard to
word (the reply must be byte-identical whoever asks). Against the real
pre-fix string **only 1 of 4 fails** — the mechanism test; the constraint
tests pass, because "has been sent" was equally generic. So the
plausible-but-wrong fix was built: stop over-claiming delivery *and* be
helpfully specific ("We couldn't find an account for that email."). It
**passes the mechanism test and fails the two constraint tests**. Each
half is blind to exactly what the other catches — so "the red path
reproduces the bug" is *not* sufficient evidence a section is well-built.
Ask separately what the attractive wrong fix is, and which test stops it.

**Feedback 13 — the Activities nav icon.** 🌾 → 🛠️: the glyph named the
*subject* of the work rather than the work, and doubled up with Sightings
🦋 on the two adjacent entries most easily confused (both org-wide record
lists). 🪏 is more literal but Unicode 16 with patchy coverage. Measured
at 390/375/320px rather than eyeballed — no overflow, no box overlap, no
clipped labels. Dense at 320px, but pre-existing: swapping a glyph doesn't
move label widths.

**Feedback 14, and the split is the contribution.** *"…I want to see all
crabgrass sightings, as points… maybe a species filter or some sort of
super sighting?"* **A species filter already existed** (the Sightings
search has matched species names since 2026-09-03), so the missing piece
was never filtering — it was that sightings could only be seen as points
**inside one property**. One species on three properties had nowhere it
could be viewed at once. Built: the Sightings page's map plots `filtered`,
so the search box the page already had became the map's control rather
than gaining a second one. No new API surface; reuses `MapCanvas`,
`ensureCircleLayer` and the same blue a sighting has on its property map.
The map is hidden entirely when the org has no sightings (an empty 50vh
map would crowd out the "log your first one" prompt) **and on a failed
load** — a map showing nothing would imply the org genuinely has none,
which is the misattribution D21 fixed elsewhere. The **"super sighting"**
half is a real data-model question and is queued, not guessed at; a
cheaper intermediate worth asking first is a structured species picker.
**The Activities sibling was deliberately not built** — polygons need
status styling and a legend, nobody asked, and this repo's "four filters,
not two" rule is about a *defect* in N places, not widening a request.

**Verified.** 126/126 backend tests (up from 122), `check` and
`makemigrations --check` clean — **no migration**. `npm ci`, `tsc -b`,
`vite build` clean, new strings confirmed in the built bundle with zero
occurrences of the old ones. **19/19 Playwright checks in real Chromium at
390px against a live stack**, seeding the feedback's own scenario (one
species on two properties): the map holds 3 points filtered to crabgrass,
4 cleared, 1 on a single match, and refits each time (z 10.720 → 10.101).

**Three harness traps, all reusable:**

1. **A bash `$'\U0001F6E0'` grep silently reports 0 for emoji that are
   present.** It said the new icon was missing from the bundle and would
   have "confirmed" a rollback. The tell: it also reported 0 for
   *unchanged, pre-existing* icons. Python found all of them. **Always
   include an unchanged control in a presence check.**
2. **A red assertion that was the harness, not the app.** "Map refits"
   failed with identical zooms — the seeded fourth point sat *inside* the
   filtered set's latitude span, and latitude dominates the fit at this
   viewport, so both sets genuinely fitted the same box.
3. **Getting a real handle on a live MapLibre map took three attempts, and
   the first two silently verified nothing** while surrounding assertions
   passed. `container._map` doesn't exist; a React fiber walk returned
   "not found". What works: patch `Map.prototype.getSource` on the app's
   own maplibre module instance (match the `?v=` hash — a different URL is
   a different module) and trigger one filter change. A blank-to-blank
   "nudge" does **not** trigger it, because `filtered` is memoized and a
   whitespace query trims to the same empty string.

**The bug only *looking* found.** All 19 assertions passed while the
screenshot read **"All 1 sightings are plotted on the map above."** — the
state a brand-new account is in, so the first thing many users would see,
not an edge case. Fixed with a singular branch that also drops "Search to
narrow them down" (nothing to narrow). Third time in this repo's history
that reading the image, not the assertions, caught the defect.

**Screenshots regenerated** — today's allowance was unused (last regen
2026-09-03) and `sightings-list.png` had gone from accurate to *actively
wrong* (the page gained a whole map panel), so this is the cap's intended
case rather than a judgment call. **`capture.js` needed a real update**,
not just a re-run: the sightings step's 600ms settle is too short for a
map to load its style and `fitBounds`. 19 images changed, mostly the icon.

**Docs:** `docs/open-questions.md` (D22's built half with both
measurements; the App-feedback section records the streak ending and that
one feedback id held two requests; "Logged-in app UX" gains both new
items), `build-questions.md` (BUILT entry, the seventeen re-deferrals,
four owner questions), this file's tests bullet (it claimed 122 and six
defects) and its testing-lessons paragraph, and the manual —
`sightings.md` (new "Seeing them on a map"), `getting-started.md` (the
verbatim quote), `organization-admin.md` (the Resend caveat) and
`limitations.md` (test count, the client-side-filter bullet now covers the
map, and a new bullet for the two gaps this leaves).

**Queue state: empty of authorized work again, but for a different reason
than the last six cycles** — the refill came from a *user*, not from an
audit lens. Worth noting for the next run: the lens-driven refill
mechanism was described as spent, and it was; what actually refilled the
queue was somebody using the app. **Still open, deliberately:** D22's
second half and the SMTP question; the "super sighting" grouping question;
B2 and the contextual menu (both anchored 2026-09-03); whether CI should
gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass; app-wide rate limiting; the
name-uniqueness casing gap.

### 2026-09-11 (3) — Scheduled PM check-in: a locked-out user is told a
### reset link "has been sent" on a deployment that sends no email — and
### that page is the one screen with no route to the caveat

Routine "resolve open questions" run, project-manager scope only (its own
trigger: identify, notify, record/queue — don't write, edit or push code,
and don't trigger the next build; no live human joined). Scheduler
assigned `claude/hopeful-rubin-ybzmy3`, which already sat at `origin/main`
(`51d022b`) while local `main` was **13 behind**; moved to `main` per this
file's standing rule and fast-forwarded before reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **thirty-first** empty pull, the steady
state.

**This run swept the successor lens the last entry named** — surfaces
where the app reports **success** before the server has confirmed
anything — and the sweep, not the sighting, is the contribution.

**D22: the "forgot password" flow asserts a delivery it cannot verify.**
`apps/accounts/views.py:194-196` answers every request with *"If an
account exists for that email, a reset link **has been sent**."* Six facts
that only matter together: `settings.py:292` defaults `EMAIL_BACKEND` to
the **console** backend; `send_password_reset_email` is **best-effort**,
catching and logging its own exceptions, so **the response is
byte-identical whether the mail was delivered, silently failed, or was
written to a log file**; the flow **deliberately has no fallback**
(handing the link back would be an enumeration oracle — a correct
decision, and exactly what leaves the user nowhere to go); **an admin
cannot help**, since the admin-sets-a-password field was removed
2026-08-26 and nothing replaced it; and `/forgot-password` sits **outside
`RequireAuth`/`AppShell`** (`App.tsx:64`) while the **Help** link lives
only in `BottomNav.tsx:74`, *inside* `AppShell` — so the one screen where
the caveat matters is the one screen with **no in-app route to it**.

**The asymmetry is the sharpest framing, and the fix is already written in
this repo.** Three surfaces claim an email will arrive; exactly one is
honest. `AddMemberForm` (`rows.tsx:720-721`) says *"…**If the email
doesn't arrive**, copy the link from the pending invitation below"*; the
**Resend** button twelve lines away says only **"Sent!"**; the reset
confirmation says **"has been sent"**.

**Severity ranked rather than flattened.** The two invite surfaces have a
visible fallback *on the same screen*, so a stuck admin can self-serve —
wording bugs. The reset flow has none by design, so it is a **dead end
presented as success**, landing on the person already locked out.

**Confirmed live.** The deployed host returns that exact string — probed
with an **empty** email, the branch where `user is None`, so no token was
minted, no mail attempted and **nothing was written to the live
instance**. Both frontend strings confirmed in the Vite-served modules
against the negative control (a nonexistent module returns SPA-fallback
HTML, not a module).

**What can't be determined from here changes the severity, and is the
finding restated:** whether the live host has SMTP configured. There is no
outside signal — **and neither has the user**. Put to the owner as the
highest-value one-line answer in the queue.

**The manual is already right, which is this finding's shape** (D16/D19/
D20; the opposite of D13): `getting-started.md:63-67` and
`limitations.md:15-25` both say delivery isn't configured and the link
only reaches the console log, so **no manual edit applies**. One note left
for the fixing session: `getting-started.md:59-60` **quotes the message
verbatim**, so changing the string makes that quote stale (the D19
precedent).

**Split, so a build session can take the safe half without deciding a
product question:** the **fork-free half** is to stop asserting delivery
at the two un-hedged sites, using `AddMemberForm`'s hedge as the in-repo
precedent — the anti-enumeration constraint is *not* a blocker, since a
message can stop claiming delivery without branching on whether the
account exists. **The owner's half** is whether a locked-out user gets a
real way out: (a) wording only, (b) let the app know whether email works
(the `GET /api/feedback/config/` precedent — **not** an enumeration
oracle, since it describes the *deployment*, not an address), or (c) an
admin-side reset action. PM recommendation: (a) now, (b) next, (c) only if
wanted.

**The mechanism worth keeping is about un-parking, not finding.** The
resend "Sent!" had been seen by several check-ins and left un-queued each
time as "entangled with the open real-email question". Sweeping the class
separated them: **the wording is independent of the delivery decision.**
Generalize it — when an item sits un-queued because it is entangled with
an open question, test whether *part* of it actually depends on that
question. Here the entanglement was assumed rather than checked, and it
had parked a real defect for several runs.

**Audited clean under the same lens — the class is narrow, it is only the
email claims.** Every inline auto-apply control is a **controlled**
component bound to server data, not optimistic local state (`MemberRow`'s
role select and property checkboxes; `TaskRow`'s assignee and status), so
a failed PATCH snaps back to the server's value rather than showing a
change that never happened — the exact defect hunted, and absent. Both
reorder callers reload on **failure as well as success**. `PhotoUploader`
keeps no local list. `AccountPage`'s "Password updated." and
`PostSavePhotoStep`'s "Your X is saved." follow real confirmations;
`FeedbackButton`'s "your feedback was sent" is true (it reached Habitat's
own database); "Copied!" waits on `clipboard.writeText` and falls back to
a prompt.

**Docs:** `build-questions.md` (new 2026-09-11 (3) entry — D22, the
clean-audit inventory, the seventeen re-deferrals, the questions),
`docs/open-questions.md` (new D22 bullet under "Auth and API"; queue-state
records the sweep, the un-parking lesson and the successor; App-feedback
the thirty-first pull). **No code, migrations, manual changes, or
screenshots** — `limitations.md` was re-read and makes no claim D22
falsifies; it is accurate and even explains why the reset flow has no
fallback. Push notification sent.

**Queue state: one takeable item (D22's fork-free half).** Success
reporting is now spent as a lens. **Named successor, a real gap rather
than a guess:** every audit to date has looked at the app from the inside
— code, strings, endpoints. None has asked what a user who is **stuck**
can actually do. A locked-out user has no route to Help, no "contact
whoever runs this instance", and no documentation path anywhere on the
unauthenticated screens.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; **D22's second half**; real SMTP; due dates on tasks; the D6
backfill query; the org switcher; a real cron for the purge; server-side
search/pagination (*not yet*); quick-log draft persistence; the Node 20
pass; app-wide rate limiting; the name-uniqueness casing gap.

### 2026-09-11 (2) — Scheduled programmer session: built D20, then pointed
### the check-in's own successor lens at error messages and found D21 — on
### the deployed host, a failed save showed the user nothing at all, and a
### failed list load said "you have no species"

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/adoring-curie-gc3j9t`, which already sat at `origin/main`
(`5a45a66`) while local `main` was **12 behind**; moved to `main` per this
file's standing rule and fast-forwarded before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **thirtieth** empty pull, the steady state.

**The morning check-in left exactly one takeable item; this run took it and
re-deferred the other sixteen with stated reasons** (table in
`build-questions.md`). D20 is two words in two files, so rather than stop
at a thin session this run continued into the successor lens the check-in
itself named — **error messages: is the stated cause the real one?** — and
that produced D21 on the first surface examined.

**D20: both delete dialogs now read "Manage → Recently deleted".** The
reasoning is pinned in a comment **on the dialog in `PropertiesPage.tsx`**,
with a pointer from its twin, because the change that would undo this is a
future nav rename — and that person is reading the dialog, not a doc. The
comment names both label sources (`BottomNav.tsx` for "Manage",
`manage/sections.ts` for "Recently deleted") and records why the
`/admin → /manage` redirect doesn't cover a *menu path*. Confirmed in the
built bundle: two occurrences of the new string, **zero** of the old.

**D21: `handleResponse` fell back to `Response.statusText`, and HTTP/2
removed the reason phrase.** Per the Fetch spec `statusText` is `""` for
anything that didn't arrive over HTTP/1.1, and the deployed host
negotiates **h2** (measured: `http_version=2`). So `ApiError.message` was
`""` — and since every error render in the app is guarded on the message's
own truthiness (`{error && <p className="form-error">{error}</p>}`, 20+
sites), **no element rendered**. A failed save was indistinguishable from a
button that does nothing: D13's symptom by a different route.

**The list pages are what make it a misattribution rather than only a
silence, and that is the finding.** `useAsync` stores `err.message` too, so
a failed load left `error === ""`, which makes `{!loading && !error && (…)}`
**true** — `SpeciesPage` renders its whole normal body against null data
and reaches its empty state. The screen says the list is empty; the truth
is that it could not be loaded. An app stating a cause that isn't the real
one is exactly what the lens was pointed at.

**Measured with one variable, not argued from the spec.** Two local TLS
servers differing in **nothing but ALPN** (`http/1.1` vs `h2`), serving
identical 404 `text/html` and 503 `text/plain` bodies, fetched from real
Chromium and run through `client.ts`'s own `errorMessage` copied verbatim:
h1 → `"Not Found"`, h2 → `""` → **user sees nothing at all**. The dev
host's own `/api/nosuchendpoint/` was confirmed to be exactly that shape
(404, `text/html`, h2) before anything was built. **Nothing was written to
the live instance.**

**Which real responses hit it:** the edge proxy's 5xx while the backend
restarts — which this deployment does **on a 15-minute schedule**, so it's
a recurring live condition, not a hypothetical — plus Django's
`DEBUG=False` 500 page and a 404 on a mistyped API path.

**Fixed** with `statusFallback(status)` at **both** sites that read
`statusText` (`handleResponse` and `postForBlob`; a sweep confirms there
are exactly two — the "four filters, not two" precedent). **It deliberately
does not keep `statusText` when non-empty:** that would make the message
depend on the transport, so local dev (h1) would show text while production
(h2) showed none — precisely how this stayed invisible. The reason phrase
is a fixed restatement of the status code, so nothing is lost by never
reading it. 502/503/504 get "try again in a moment" because that advice is
true for them and misleading for a 400.

**Verified including the regression guard, which matters more here than a
red path:** a fix that clobbered real DRF messages would be worse than the
bug. Both shapes — `{"detail": …}` and field-level `{"is_done": [...]}` —
come back **unchanged on both protocols**; only the no-message case changed,
and it changed from nothing to something. `npm ci`, `tsc -b`, `vite build`
clean, both new strings confirmed in the built bundle. **No backend file
changed, so no PostGIS stack was stood up and no backend run is claimed.**
**Neither defect is pinned by a test** — there is still no frontend test
runner — stated plainly rather than left to be inferred.

**Why D21 survived, and the technique worth keeping:** `client.ts` had been
audited repeatedly and was correct on every axis previously asked of it
(types, CSRF, the DRF unpacking fixed 2026-09-03). It only became visible
once the question was *"what does the user actually end up seeing?"*, and
only reproducible once the **environment** matched — **on HTTP/1.1, which
local dev serves, the bug does not exist at all.** A defect that is
invisible in development and universal in production won't be found by
reading a diff, and wasn't. Vary one environmental axis in a controlled
experiment rather than reasoning about a spec. Two smaller traps: a
`pkill -f "node servers.js"` pattern matches its own shell and killed the
harness (exit 144) — scope the pattern or use the background runner; and
Playwright's `ignoreHTTPSErrors` has to be on `newContext`, not `newPage`,
or a same-origin `fetch` fails with a bare "Failed to fetch".

**Recorded, deliberately NOT fixed:** a `fetch` that rejects outright
(offline, DNS failure) is a `TypeError`, not an `ApiError`, and surfaces
the browser's own "Failed to fetch" — technical, but non-empty and not
misattributing, so a much weaker and separate item.

**Docs:** `docs/open-questions.md` (D20 found → built; new D21 bullet;
queue-state records that the refill mechanism has changed shape twice
rather than run out, and names the successor lens; App-feedback the
thirtieth pull), `build-questions.md` (BUILT entry with the sixteen
re-deferral reasons). **No manual change applies and for D20 that is the
finding's shape** — `docs/manual/properties.md:150` already said "Manage →
Recently deleted", so the fix makes existing documentation true;
`limitations.md` was re-read and makes no claim about error messages, so
there is nothing to correct. **No migrations and no screenshots** (both
dialogs are `window.confirm`, which `capture.js` never opens).

**Queue state: empty of authorized work again after exactly one run — the
sixth consecutive cycle.** The refill mechanism has now changed shape
twice rather than exhausting: asking a new *question* of already-read code
has produced three findings in four runs (D19 captions, D20 nav paths, D21
error messages), and D21 is the first that is a genuine misattribution
rather than a stale string. **Error messages are now spent as a lens.**
Named successor: the surfaces where the app reports **success** — a
confirmation that fires before the server has confirmed anything. The
check-in already found one un-queued instance (the resend-invite "Sent!",
entangled with the open real-email question), but the class is broader than
that one button and has never been swept.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass; app-wide rate limiting; the
name-uniqueness casing gap.

### 2026-09-10 (6) — Scheduled programmer session: built D19 — the box that
### publishes your work to the internet no longer denies that it does, and
### the manual finally says which fields actually travel

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/elegant-dirac-m5log7`, which already sat at `origin/main`
(`bb29e4e`) while local `main` was **10 behind**; moved to `main` per this
file's standing rule and fast-forwarded before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **twenty-eighth** empty pull, the steady
state.

**The morning check-in left exactly one takeable item; this run took it and
re-deferred the other sixteen with stated reasons** (table in
`build-questions.md`).

**D19: the `is_public` checkbox on `ActivityFormPage` now reads "Show on
the public site".** The default was deliberately **not** touched, per the
check-in's guardrail — public-by-default with a per-record private flag is
a decided project stance, and flipping it would be a build session settling
a product question on its own authority. The reasoning is pinned in a
comment **on the label**, quoting the string it replaced, because the
change that would undo this is someone tidying a caption back toward
brevity.

**The one call the check-in left implicit: "site", not "view".** The
check-in reasoned that keeping *"Show on the public view"* would make
`activities.md`'s existing quote correct with **no manual edit at all**.
True, and still the wrong trade: `public site` is the app's vocabulary
everywhere else (the nav entry, all three sibling labels, nine manual
chapters), while `public view` survived *only* in this stale label. Leaving
one form as the lone holdout of a second vocabulary is how the next drift
starts. The label matches its siblings; the manual's quote was updated
instead — a one-line edit against a permanent inconsistency.

**Both of the check-in's open notes are resolved, and the first inverted.**
It flagged as unverified whether `activity-new.png` shows the checkbox,
warning the screenshot could go from stale to *actively wrong*. Both
`activity-new.png` **and** `activity-edit.png` were opened and looked at:
each is cropped at the Notes field, several controls above the checkbox,
which is **not in frame in either**. So **no screenshot regeneration is
needed** and the cap-policy case does not arise. Worth keeping as a
technique — two `Read` calls on the PNGs settled it conclusively and more
cheaply than the reasoning that would have gone into guessing.

**The second note was taken and is the larger half of the work.**
`public-site.md` gains a **"What a public record publishes"** section,
placed so the chapter reads: what makes a record public → what that
publishes → what is never exposed. Every field was checked against
`ActivitySerializer.Meta.fields` and `SightingSerializer.Meta.fields`
rather than recalled — **the public endpoints reuse the app's own
serializers**, so every field on them travels, photos included. It names
the two things easiest to miss: **notes publish in full** (there is no
private-notes field on either record type), and **the exact location
publishes** with no fuzzing, which is what actually matters for a sensitive
sighting.

**Verified on the shipped artifact, not just the source.** `tsc -b` and
`vite build` clean; the built bundle then contains **zero** occurrences of
the old caption and **zero** of the string `public view` anywhere, against
**two** of `Show on the public site`. The render path was checked rather
than assumed (D13's lesson): the checkbox sits above every conditional in
the component — `savedId` short-circuits to the photo step at line 197, the
first `{existing && (` is at line 340 — so it renders on create and edit
alike. The sweep was re-run rather than trusted: every remaining `Phase 1` /
`not yet` occurrence under `frontend/src` is a code comment. **No backend
file changed, so no PostGIS stack was stood up and no backend run is
claimed.** There is still no frontend test runner, so **this defect is not
pinned by a test** — stated plainly rather than left to be inferred from a
green suite; if the caption regresses, nothing catches it.

**Docs:** `docs/open-questions.md` (D19 found → built, with the
wording call, the screenshot resolution and the honest no-test note;
queue-state records the fifth consecutive empty-after-one-run cycle and
refines the successor lens; App-feedback the twenty-eighth pull),
`build-questions.md` (BUILT entry with the seventeen re-deferral reasons),
and the manual — `activities.md` (the quoted label, plus that the flag is
ticked by default and what that means) and `public-site.md` (the new
section). **No migrations and no screenshots.**

**Queue state: empty of authorized work again after exactly one run — the
fifth consecutive cycle.** The honesty lens survived contact with a build:
its first application was real, its fix was one line, and the *manual* half
turned out to be the more valuable piece, since enumerating what a public
record publishes is something nineteen correctness findings never surfaced
— nothing about it is a bug. The named successors (delete dialogs, the
invite flow, the theme/QR panels, empty states) are still unexamined, with
one refinement: **point the lens at what a caption *promises*, not only at
what it denies.** D19 was a denial and fell to a search for
absence-claiming strings; a caption that *overstates* a guarantee ("this
can't be undone", "only you can see this") would not match that search at
all, and is the same defect class.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass; app-wide rate limiting; the
name-uniqueness casing gap.

### 2026-09-10 (5) — Scheduled PM check-in: the box that publishes your
### work to the internet says "no public view exists yet", and it is ticked
### by default — five activities are live behind it right now

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Scheduler assigned `claude/hopeful-rubin-drrlfk`, which
already sat at `origin/main` (`a1dd012`) while local `main` was **9
behind**; moved to `main` per this file's standing rule and fast-forwarded
before reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **twenty-seventh** empty pull, the steady
state.

**The previous entry said the next check-in needed a changed threat model,
since the lens list was spent and no unopened module remained. This run
took that literally** and asked a different question rather than a new way
to attack the code: **does the app tell the user the truth about what it is
doing?** That is answered by reading *rendered strings*, not control flow,
and it produced a defect on the first surface examined.

**D19: the checkbox that publishes an activity denies that it publishes.**
`ActivityFormPage.tsx:327` renders `Show on the public view (no public view
exists yet in Phase 1)` next to the `is_public` checkbox, which defaults to
**checked** (line 72). The public view has existed since **2026-08-14**.

**It is not an access-control defect, and reading it as one would send a
build session hunting the wrong thing.** Every filter is correct —
`property_activities` requires `is_public=True` and resolves the property
through `_public_property_or_404`, so the two-condition rule holds and
nothing unflagged is published. The defect is **informed consent**: the
only on-screen account of what the flag does is a denial that it does
anything, and the denial reassures in exactly the direction that causes
harm.

**The asymmetry is the sharpest framing — three of four get it right.**
`SightingFormPage`, `PropertyFormPage` and `QuickLogPage` are all truthful.
Only the activity form carries the stale parenthetical, and it is attached
to the record type carrying drawn geometry, both dates and free-text notes.

**Live, not theoretical:** the anonymous
`/api/public/properties/1/activities/` returns **5 activities, 3 carrying
notes**, all `is_public: true`. Only field *lengths* were read — the note
text was deliberately not copied into this repo, the same reasoning that
redacted D8's address. **Nothing was written to the live instance.**

**Swept, so it can't be half-fixed:** every other `Phase 1`/`not yet`
string under `frontend/src` is a **code comment**, not a rendered one. Line
327 is the only one a user sees.

**Framed build-ready, not a question**, with one guardrail stated so it
isn't overshot: **do not change the default in the same pass** —
public-by-default with a per-record private flag is a decided project
stance, so flipping it would be a build session settling a product question
on its own authority. The item is the caption.

**No manual edit applies, and that is the finding's shape** (as with D16,
the opposite of D13): `docs/manual/activities.md:36` already quotes the
label as *"Show on the public view"* and calls it the same mechanism as a
property or sighting — **the manual documents the truthful behaviour and
the screen contradicts it**, so fixing the caption makes the existing quote
literally correct. Two notes left for the fixing session: check whether
`activity-new.png` shows the checkbox (if so it goes stale → *wrong*;
**unverified here**, I did not open the image), and the manual nowhere
enumerates *which* fields a public record publishes, notes included — the
weaker sibling, and the natural addition to `public-site.md`.

**Also audited, the first CI-as-a-threat-surface pass this project has
done — clean.** Recorded so it isn't re-derived: no `pull_request_target`;
no attacker-controlled `${{ }}` in any `run:` block (the one interpolation
takes only workflow-computed values and a literal matrix name);
`tests.yml` uses no secrets; `docker-publish.yml` never runs on a fork PR,
so `DOCKERHUB_TOKEN` is never exposed to untrusted code. Two hygiene notes
recorded with an explicit recommendation **not** to queue either: the
publish workflow's header comment says "chrcraven namespace" while the
images are `cravenator/habitat-*` (stale comment, not a broken workflow —
runs #78–#82 were green), and neither workflow declares a `permissions:`
block.

**Queue state: one takeable item (D19) — and the refill mechanism changed
shape rather than returning.** All nineteen findings to date came from
asking whether the *code* is correct; none had asked whether the
*interface* is honest, and the two barely overlap — D19 sits on code
several prior audits read straight past because nothing was wrong with it.
**The honesty lens is barely started:** only one form's labels were read.
Named for next time — what the other destructive or publishing controls
claim (delete dialogs, the invite flow, the theme and QR panels), and
whether any empty state or hint asserts something no longer true.

**Docs:** `build-questions.md` (new 2026-09-10 (5) entry — D19, the
rendered-string sweep, the CI audit, the two hygiene notes, the standing
questions), `docs/open-questions.md` (new D19 bullet; queue-state records
the refill and names the successor lens; App-feedback the twenty-seventh
pull). **No code, migrations, manual changes, or screenshots** —
`limitations.md` was re-read and makes no claim D19 falsifies (its testing
bullet is accurate at 122 across six modules). Push notification sent.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass; app-wide rate limiting; the
name-uniqueness casing gap.

### 2026-09-10 (4) — Scheduled programmer session: built D18 — the
### duplicate-species guard has a database behind it now, and the naive fix
### that would have hidden the 500 while keeping the corruption is on record

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/adoring-curie-ir9dsr`, which already sat at `origin/main`
(`7d73585`) while local `main` was **8 behind**; moved to `main` per this
file's standing rule and fast-forwarded before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy, checked before and after the build — no blocker.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **twenty-sixth** empty pull, the steady state.

**The morning check-in left exactly one takeable item; this run took it and
re-deferred the other fifteen with stated reasons** (table in
`build-questions.md`).

**D18: `UniqueConstraint(["activity", "species"])` on
`ActivitySpecies.Meta`, plus migration `activities/0004`. The view's logic
is unchanged, and that is the point** — the constraint alone makes the
existing 400 correct under a race, because it hands `get_or_create` back
its own `except IntegrityError` recovery branch, which without a constraint
is unreachable. The only view change is defensive
(`MultipleObjectsReturned → 400`). The reasoning is pinned **on the
constraint**, since the change that would undo this is someone deleting
something that looks like tidy-up.

**One migration, dedupe first** (`activities/0003` precedent) — keep the
lowest id, print what was removed. `AddConstraint` fails outright on a
database holding duplicates, so the halves are only correct together.

**The dedupe was verified against a database that actually held
duplicates, which the check-in had recorded as uncheckable from here.** It
isn't, and the technique is reusable: roll `activities` back to 0003 on a
local PostGIS instance and the pre-D18 state is reachable again. Three rows
for one pair were then created **through the ORM** — which is D18 in one
line, since a `UniqueConstraint` is enforced by the *database*. Re-applying
0004 reported `removing 2 duplicate ActivitySpecies row(s)`, kept the
lowest-id row **with its own role and quantity**, left an unrelated pair
untouched, and the constraint then refused a fresh duplicate; the reverse
path was exercised too. What stays unknown is only whether the
*deployment* holds duplicates — almost certainly not, but the migration
doesn't assume it.

**Verified, including two red paths.** 16 new tests in
`apps/activities/tests.py` — **122/122**, up from 109. Against the real
pre-fix code, **6 of 21 fail** in that module and reproduce D18 verbatim:
`2 != 1 : a species must never be linked to one activity twice: concurrent
adds returned ['201', '201'] and left 2 rows`, and
`MultipleObjectsReturned: get() returned more than one ActivitySpecies --
it returned 2!` raised from Django's own `query.py` **through the real
endpoint** — the sticky 500, end to end.

**The second red path is the one worth reading.** Per D17's lesson the
naive fix was actually built (an `.exists()` re-check, no constraint). It
takes the module from **6 failures to 4** — and which four is the finding:
it makes the sticky 500 disappear **while leaving the race and the
duplicate rows entirely intact**, which is arguably worse than the bug,
because the corruption stops announcing itself. Only the mechanism tests
catch it; `test_the_database_itself_refuses_a_duplicate_pair` bypasses the
view, so no application-level check can satisfy it. **A smaller failure
count is not evidence a fix works.**

The concurrency tests use the **real** `get_or_create` and the real
endpoint — a `threading.Barrier` inside `ActivitySpecies.save()` (the
INSERT) holds both requests until each has run its own SELECT, which is
the interleaving two simultaneous POSTs actually produce. Four tests pass
both ways deliberately, including that a *different* species is still
accepted (the constraint is on the pair, not the activity) and that
remove-then-re-add still works.

`check` and `makemigrations --check` clean. Local PostGIS 3.4 +
PostgreSQL 16. **No frontend file changed, so no `tsc -b`/`vite build` was
run and none is claimed** — but `ActivitySpeciesPanel`'s error render was
checked rather than assumed (D13's lesson): it is on the unconditional
path, so the 400 does reach the user.

**A workaround this closes, handled rather than papered over.** The full
suite surfaced a failure in *another app*, and it was the right kind:
D13's `test_two_links_to_one_activity_count_as_one_activity`
(`apps/species/tests.py`) **constructed the duplicate state on purpose**,
because `apps/species/views.py` counts distinct activities precisely since
duplicates could exist. The constraint makes that fixture impossible. The
test now asserts the stronger fact (the duplicate is refused) and is
renamed; the view keeps `distinct()` — counting activities is what its
message claims to do, and that shouldn't silently depend on a constraint
declared in another app — but its comment no longer asserts the now-false
"has no unique constraint".

**Deliberately NOT changed:** the name-uniqueness case-sensitivity
mismatch (`name__iexact` vs. case-sensitive constraints), which the
check-in recorded and recommended against. Closing it needs a `Lower()`
functional constraint *and* a decision about existing differently-cased
rows — a product call.

**Docs:** `docs/open-questions.md` (D18 found → built, with the dedupe
verification and the naive-fix measurement; queue-state records the
emptying and the spent lens list; App-feedback the twenty-sixth pull),
`docs/data-model-notes.md` (new "one row per (activity, species)" bullet
stating why it is a database constraint rather than a view check),
`build-questions.md` (BUILT entry with the fifteen re-deferral reasons),
this file's tests bullet (it claimed 109) and its testing-lessons
paragraph, and the manual — `activities.md`'s Species section now says
each species appears once and what the refusal reads like (the check-in
correctly left this for the session that would make it true), and
`limitations.md`'s testing bullet (109 → 122, and "six areas" → "six
modules", removing the apparent off-by-one the check-in flagged).
**No screenshots** — nothing visual changed, no `capture.js` selector
affected.

**Queue state: empty of authorized work again after exactly one run — the
fourth consecutive cycle.** But genuinely new this time: the previous three
refills each came from a named lens, and **that list is now spent with no
unopened module left**. The next check-in needs a changed threat model,
driving the live host as a user, or an owner answer. The standing one-line
owner answers are now the cheapest way to refill the queue.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass; app-wide rate limiting; the
name-uniqueness casing gap.

### 2026-09-10 (3) — Scheduled PM check-in: the "already linked" guard has
### nothing in the database behind it — two adds at once leave a duplicate,
### and every add after that is a 500 that never clears on its own

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Scheduler assigned `claude/funny-euler-owodmy`, which
already sat at `origin/main` (`bff91a4`) while local `main` was **7
behind**; moved to `main` per this file's standing rule and fast-forwarded
before reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **twenty-fifth** empty pull, the steady
state.

**This run spent the last two lenses on the list, in one pass**, because
they are the same question from two sides: *what does a half-finished or
repeated write leave behind?*

**D18: `get_or_create` with no unique constraint behind it.** The POST at
`apps/activities/views.py:315` returns 400 on `created is False` — but
`get_or_create` is an unlocked SELECT-then-INSERT, safe only when a
constraint can reject the loser, and `ActivitySpecies.Meta` carries **only
`verbose_name_plural`**.

**The asymmetry is the sharpest framing, because the sibling gets it
right.** `SightingActivityLink` — same feature family, `get_or_create` at
two call sites — carries `UniqueConstraint(fields=["sighting",
"activity"])`. A sweep of every model settles how isolated the gap is:
**eight uniqueness constraints exist**, and `ActivitySpecies` is the
**only** model stating a uniqueness rule in a user-facing error message
with nothing in the database enforcing it.

**The constraint is the guard's mechanism, not hygiene on top of it — a
quick read gets this backwards.** `get_or_create` is `try: get() except
DoesNotExist: try: create() except IntegrityError: get()`. **With** a
constraint the loser's INSERT is rejected, the `IntegrityError` is caught,
the re-read returns `created=False`, and the 400 fires correctly under a
race. **Without** one that branch is *unreachable* — the second INSERT
succeeds and the endpoint answers 201. The guard fails **open**.

**Reproduced on the repo's own pinned Django 5.2.17** on plain non-GIS
models mirroring both link models (the D12/D14 technique), interleaved the
way two concurrent POSTs run: both SELECTs see nothing, both INSERTs
return 201, **two rows**. The same interleaving on the sibling is refused
by the database. Sequentially the guard works perfectly (201 then 400),
which is why nobody noticed.

**The persistent damage earns the record, and it is worse than the
duplicate row.** From then on the next POST for that pair never reaches
the 400 — `get_or_create`'s own `get()` raises
`MultipleObjectsReturned`, whose MRO is just `Exception` (not an
`APIException`, not a Django `ValidationError`), and there is **no custom
`EXCEPTION_HANDLER`** (re-verified, not inherited from D13) — so it is a
**500**. Unlike D13's transient 500 this one is **self-inflicted and
sticky**: the bad row persists, so the endpoint stays broken for that pair.
Smaller symptoms: `species_names` iterates the M2M *through* this table so
the species renders twice, and that field is served **unauthenticated by
the public site**; and one species can be both `planted` and
`treated_target` on the same activity.

**The missing constraint has already cost a workaround, which is the
strongest evidence it should exist.** `apps/species/views.py:61-68` counts
*distinct activities* precisely because duplicates can exist. D13 spotted
the absence and worked around it for counting; nobody asked whether the
thing doing the keeping holds under concurrency.

**Scope, honestly:** editor-gated; **needs real concurrency**, and a naive
double-click is *not* it — `ActivitySpeciesPanel` disables Add while
pending (checked at the source, not taken from the 2026-09-09 audit's
summary), so the triggers are two editors, two tabs (the `busy` flag is
per-component), a network retry, or direct API use. No data exposure, no
cross-org reach, no escalation, and **self-recoverable** (both rows are
listed with a Remove each; PATCH/DELETE address rows by `link_id` and never
hit the ambiguity). Same class as D13/D14. **Nothing was written to the
live instance.**

**Framed as build-ready** (the D12/D13/D14/D16/D17 call): add the
constraint, which fixes the 400 **with no view change at all** by handing
`get_or_create` back its recovery branch. Two notes, neither a fork: the
migration must **dedupe first** (keep the lowest id, one migration so no
half-applied state — the `activities/0003` precedent) since
`AddConstraint` fails on existing duplicates, and **this can't be checked
from here** (no database access, same as the D6 backfill); and handle
`MultipleObjectsReturned` → 400 defensively too. A test should use the
**D16/D17 pairing** — the outcome test can pass by accident if the
requests serialize, so pair it with a mechanism test, and build the
plausible-but-wrong fix (an `.exists()` re-check, no constraint) to show
it catches that.

**Recorded but deliberately NOT queued:** the two name-uniqueness rules
reject duplicates **case-insensitively** (`name__iexact`) while their
constraints are case-sensitive, so a race between "Seeding" and "seeding"
leaves two types. Much weaker — no 500 (those use `.filter()`, not
`.get()`), no persistent breakage — and closing it needs a `Lower()`
functional constraint *plus* a decision about existing rows. A product
call. **Recommendation: not now.**

**Audited clean under the same lenses**, recorded so it isn't re-derived:
`signup`, `invitation_accept` and `password_reset_confirm` are all
properly atomic; and the one that matters most given D10 (*empty scope
encodes account-wide*), `membership.properties.set(...)`, is inside the
transaction at **all three** call sites — so a failure between creating a
membership and writing its scope cannot leave a fail-open account-wide
member. The purge is per-property atomic and dodges the D10 manager trap
(`Sighting` has no custom default manager). `notify()` sits outside the
task's commit, the right failure direction. And **D17's own ordering
question asked of the other four image endpoints comes back clean** — each
runs validate → byte cap → `.read()`. Two weaker surfaces deliberately not
queued: the reorder path's N un-transacted PATCHes (self-healing, it
normalizes to array indices) and the total absence of idempotency keys.

**Queue state: one takeable item (D18) — and the lens list is now spent.**
Three applications, three findings (concurrency → D16, resource exhaustion
→ D17, failure/idempotency → D18), which confirms the technique rather
than just repeating it. With no unopened module and no named lens left,
the next check-in needs a changed threat model, driving the live host as a
user, or an owner answer. "Nothing new" stays a real outcome.

**Docs:** `build-questions.md` (new 2026-09-10 (3) entry — D18 with the
interleaving table, the eight-constraint sweep, the clean-audit
inventory, the not-queued casing gap, the six standing questions),
`docs/open-questions.md` (new D18 bullet under "Tech / infrastructure";
queue-state records the refill and the spent lens list; App-feedback the
twenty-fifth pull). **No code, migrations, manual changes, or
screenshots** — `limitations.md` was re-read and makes no claim D18
falsifies, so there is nothing to correct; its nearest bullet ("No species
merge/dedupe tool") is about the *species list*, not duplicate links, and
shouldn't be conflated. Its testing bullet was **counted rather than
trusted** and is accurate (109 methods across six modules); one cosmetic
wrinkle recorded not fixed — it says "six areas" then lists seven themes,
which isn't an off-by-one because `accounts/tests.py` holds six sections.
Push notification sent.

### 2026-09-10 (2) — Scheduled programmer session: built D17 — a 250 KB
### upload no longer costs a third of a gigabyte, and the proof the fix is
### real is a test that only fails against the *plausible* wrong fix

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/elegant-dirac-2uopdy`; moved to `main` per this file's standing
rule, fast-forwarding **6 commits** to `621a409` before reading anything.
Read `docs/open-questions.md` and `build-questions.md` per the triage
rule. **The owner's "Build next run" authorization is long spent and was
not treated as covering this.**

Dev host healthy, checked before and after the build — no blocker.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **twenty-fourth** empty pull, the steady state.

**The morning check-in left exactly one takeable item; this run took it
and re-deferred the other fourteen with stated reasons** (table in
`build-questions.md`).

**D17: the QR center image was the app's only unbounded image input.**
The guard is now split across two layers by responsibility rather than
piled into one — the *view* owns what an upload may be (`MAX_LOGO_BYTES`
= 5 MB plus `validate_image_upload`, both **before** `logo.read()`, so an
oversized body is never pulled into memory), and `qrcodes.py` owns what a
*decode* may cost (`MAX_LOGO_PIXELS` = 16,000,000, checked on
`Image.open().size` before `.convert()`). That matches how the other four
endpoints already work instead of inventing a fifth pattern. **No
migration.**

**Both constants are justified and pinned, not just picked.** 5 MB is
asserted *equal to* `MAX_THEME_IMAGE_BYTES` — a center image is the same
class of asset as a theme banner, so the two must not disagree. 16 MP is
deliberately generous (the logo is thumbnailed to a couple of hundred
pixels, so a 12 MP phone photo passes) while sitting well below Pillow's
89,478,485 threshold, which is what keeps *our* guard the one that fires
rather than leaving the gap beneath Pillow's — the whole finding.

**Re-measured independently rather than trusting the check-in**, driving
the repo's real `make_qr_png`: 9000×9000 → 200, **+313 MB**, 2.68 s
pre-fix; **400 at +0.0 MB and 0.01 s** after. **The number that matters
most is the one the cap still allows**, though, not the one it blocks:
4000×4000 costs +62.8 MB / 0.5 s, which is the honest bound now in place.
My byte figures differ from the check-in's (different test-image
generation); the shape and conclusion are identical.

**The verification lesson is the durable part, and it took two red-path
runs to get.** The first, against the real pre-fix code, gave **5 of 11
failing** — the right five, headline `200 != 400` where the 200 *is* the
defect. But it never exercised the mechanism test, which failed on the
status code before reaching its own assertion. So a second red path was
run against the **naive fix** (decode first, measure after):
`test_an_image_over_the_pixel_cap_is_refused` **passes**, the boundary
test **passes**, and only `test_an_oversized_image_is_never_decoded`
fails — *"the oversized logo was decoded before being rejected — the
guard ran after the work it exists to prevent"*. A decode-then-measure
fix returns the correct 400 while spending the identical memory; every
outcome test is blind to it. **If you write a mechanism test, build the
plausible-but-wrong fix and show it catches that** — the original bug's
red path doesn't demonstrate it. Two other tests prove ordering with no
patching at all, by sending bodies whose *content* would yield a
different message if it had been read.

11 new tests in a **sixth** section of `apps/accounts/tests.py` —
**109/109**, up from 98. Six pass both ways deliberately: three pin the
endpoint's real job (so "delete the feature" isn't a passing fix), three
pin the constants. `check` and `makemigrations --check` clean. `npm ci`,
`tsc -b`, `vite build` clean. Local PostGIS 3.4 + PostgreSQL 16 (usual
fallback; two stale PPAs still need removing first). Both reverted files
restored and confirmed **byte-identical**, no scratch residue in the tree.

**One refinement beyond the recommendation:** Pillow's own
`DecompressionBombError` at the extreme tail used to answer "Could not
read the center image." It now gives the *dimensions* message — same user
mistake, just larger, and two guards that compose should say one thing.

**Deliberately NOT changed: the missing role gate.** The check-in noted
these are the only image endpoints without `ensure_role`. Left alone —
it is documented as intentional at the call site (a QR code exposes
nothing not already public), and D17 is fixed by bounding the resource,
not by narrowing who may ask. Adding a gate would be a build session
making a silent product change on its own authority. A test pins the
viewer's access so that "fix" goes red instead of shipping quietly.

**Frontend, small but now load-bearing:** `QrCodePanel`'s
`accept="image/*"` became the shared `ACCEPTED_IMAGE_TYPES`. The
2026-09-06 (2) session left it alone **correctly** (not a D6 surface —
never stored or served back, still true); what changed is that the server
now type-checks this path, so the picker would otherwise offer a file the
backend refuses.

**Docs:** `docs/open-questions.md` (D17 found → built, with the
measurements, the two constants' rationale, and the role-gate
non-decision; queue-state records the empty-after-one-run rhythm as
settled across three cycles; App-feedback the twenty-fourth pull),
`build-questions.md` (BUILT entry with the fourteen re-deferral reasons),
this file's tests bullet (it claimed 98 and five defects), and the
manual. **Both doc inaccuracies the check-in flagged are fixed**, since
this was the session that made the second one true: `limitations.md`'s
testing bullet (claimed 90 tests, now 109, concurrency area named) and
its image-formats bullet (now covers the QR center image), plus
`organization-admin.md`'s QR section gaining the two limits in user
terms. `properties.md` needed no edit — its QR text already
cross-references the org section for the center image, so the limits are
reachable without duplicating them. **No screenshots** — nothing visual
changed and no `capture.js` selector is affected.

**Queue state: empty of authorized work again after exactly one run.**
Three cycles running now (D12/D13, D14, D15/D16, D17), so this is the
settled rhythm, not a coincidence: a check-in applies a lens and refills
by one or two, the next programmer run empties it. **Lenses still
unapplied over already-read code: failure and partial-write behaviour,
and ordering/idempotency.** App-wide rate limiting stays unqueued — a
design question, not a bounded fix, and a different item from D17.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher;
a real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass.

### 2026-09-10 — Scheduled PM check-in: a 77 KB upload costs the server
### half a gigabyte — the one image input of five that nobody capped, and
### the only one a viewer can reach

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Scheduler assigned `claude/hopeful-rubin-f5ue79`, which
already sat at `origin/main` (`5c64aa6`) while local `main` was **5
behind**; moved to `main` per this file's standing rule and fast-forwarded
before reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **twenty-third** empty pull, the steady
state.

**This run applied the successor lens the last entry named**, rather than
looking for an unopened module (there are none). Concurrency was spent on
D16; this took the next one on that list — **resource exhaustion** — and
it produced a defect on the first surface it examined.

**D17: the QR center image is the app's only unbounded image input.**
`_qr_response` does `request.FILES.get("logo")` → `logo.read()` →
`Image.open(...).convert("RGBA")` with **no size check, no type check and
no pixel check**.

**The asymmetry is the sharpest framing, because this codebase already
solved it four times.** Habitat has five image inputs; the other four each
call `validate_image_upload` *and* an explicit byte cap. The QR logo calls
neither — and it is also the only one of the five with **no role gate**,
so it falls through to `IsAuthenticated` and **a viewer, the lowest role,
can reach it**.

**Measured against the repo's real `qrcodes.py` on pinned Pillow 12.3.0**,
not reasoned about: 9000×9000 (**77 KB**) → 200, **+468 MB peak RSS**,
3.9 s; 12000×12000 → 200, +484 MB; 20000×20000 → correctly 400.

**The middle of that range is the finding, and it is what a quick read
misses.** The tempting conclusion is "Pillow protects us", and above 2×
`MAX_IMAGE_PIXELS` it really does — it raises, the existing
`except Exception → ValueError` catches it, the view returns a clean 400.
But the guard only engages above 89,478,485 pixels: **9000×9000 is under
the limit, so nothing warns and nothing raises**, and it still costs half
a gigabyte. Pillow's protection is real and irrelevant — an attacker stays
beneath it. This also refines rather than contradicts the 2026-09-06 (3)
check-in, which was right about the *undecodable* image it examined and
never asked about a decodable but enormous one.

**Second half: `DATA_UPLOAD_MAX_MEMORY_SIZE` looks like a cap and isn't.**
Measured on Django 5.2.17's real `MultiPartParser`: 25 MB as a **text**
field → `RequestDataTooBig`; 25 MB as a **file** field → accepted; 200 MB
→ accepted. It excludes file uploads by design, which is exactly why the
other four endpoints carry their own `image.size >` check — and
`settings.py`'s own comment says so. The principle was understood at three
call sites and this path never got it.

**Scope stated honestly:** DoS-shaped — no data exposure, no cross-org
reach, no escalation, endpoint authenticated. **Nothing was uploaded to
the live instance**; every measurement ran locally, in-process. What earns
it a record is that the trigger needs no sophistication and is available
to the least-privileged role. One non-mitigation pinned so it isn't
assumed: an edge proxy's body-size limit bounds only the 200 MB half — the
77 KB row passes any such limit untouched, so **the pixel dimension, not
the byte count, is the load-bearing check**.

**Framed as build-ready, not a question** (the D6/D13/D14/D16 call, not
D5/D8/D11's): `Image.open()` is lazy and exposes `.size` without decoding,
so the guard is open → reject on `w * h` → only then `.convert()`, paired
with a byte cap and the `validate_image_upload` the other four already
make. Nothing legitimate is near the limit — the logo is thumbnailed to
25% of the QR's width. **Deliberately kept separate from app-wide rate
limiting** (absent since 2026-08-27), which is a design question, not a
bounded fix, and stays unqueued.

**Audited clean under the same lens:** all four other image endpoints
genuinely carry their caps (checked at each call site rather than trusting
`images.py`'s docstring, which asserts it); and Pillow has **exactly one**
entry point in the whole backend, so the "four filters, not two" sweep
this repo does came back with one.

**Two `limitations.md` inaccuracies found — recorded, not fixed**, per
this session's scope: the testing bullet says "90 tests across six areas"
where the suite is now **98** and has gained a concurrency section the
list doesn't name; and the image-formats bullet ends "the picker only
offers the accepted formats", which the QR picker (`accept="image/*"`)
contradicts — an SVG there is refused only because Pillow can't decode it,
so the user gets a generic error rather than the format message. The
second becomes true as written the moment D17 lands, so the fixing session
is the natural one to correct both.

**Docs:** `build-questions.md` (new 2026-09-10 entry — D17 with the
measurement tables, the clean-audit notes, the two doc bugs, the six
standing questions), `docs/open-questions.md` (new D17 bullet under "Tech
/ infrastructure"; queue-state records the refill and that the successor
mechanism is now **confirmed** at two applications rather than proposed;
App-feedback the twenty-third pull). **No code, migrations, manual
changes, or screenshots.** Push notification sent.

**Queue state: one takeable item (D17).** Everything else unchanged — B2
and the contextual menu (both anchored 2026-09-03); whether CI should gate
the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher; a
real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass.

### 2026-09-09 (2) — Scheduled programmer session: built D15 and the
### sibling the check-in missed, then found D16 — two admins clicking at
### the same moment could leave an organization with no admin at all

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/adoring-curie-7ljgyn`; moved to `main` per this file's standing
rule, fast-forwarding **4 commits** to `d2d803a` before reading anything.
Read `docs/open-questions.md` and `build-questions.md` per the triage
rule. **The owner's "Build next run" authorization is long spent and was
not treated as covering this.**

Dev host healthy, checked before and after the build — no blocker.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **twenty-second** empty pull, the steady state.

**The morning check-in left exactly one takeable item; this run took it
and re-deferred the other fourteen with stated reasons** (table in
`build-questions.md`).

**D15, and it had a sibling the check-in didn't notice.**
`PublicPropertyPage` carries the identical pinned-state shape as
`PropertyMapPage` — same carryover, same count bug. Fixed in the same
pass, per this repo's own precedent (D3's "four filters, not two", D6's
"eight serving paths, not two").

**The fix is the check-in's recommendation, not D14's comment.** Each page
keys on the property's identity, so a property change remounts and resets
*all* per-property state rather than pruning one set — the correct
semantic, since that state is about one property. **The public page's key
is deliberately narrower than the route:** its page nav switches between
Explore and that property's authored pages without leaving the property,
and keying on the whole route would remount there, tearing down the map
and dropping a visitor's pins for a property they never left.

**Reproduced in a browser before fixing, which the item's "latent" status
made non-trivial.** No in-app path changes `:id` while the page stays
mounted, so the defect needed a **temporary, uncommitted** switch link
standing in for the property switcher that would trigger it. Pre-fix:
*"Showing 3 of 1 on the map"* and a "Clear all" with zero pinned cards.
Post-fix: "Showing 1 of 1", no stray button. **The same run confirms the
check-in's correction empirically** — property B lists exactly one card,
its own, so nothing cross-property is drawn and there is no leak. Trigger
removed afterwards and the file confirmed byte-identical.

**Then D16, found by changing the question rather than opening a module.**
The morning entry concluded the refill mechanism was spent, since no
unopened module remains. Too narrow: auditing *modules* is exhausted,
auditing already-read code under a **new question** is not. This run asked
one nobody had asked — **can two requests interleave between a check and
its write?** — and it produced a defect on the first look.

**The last-account-wide-admin guard is check-then-act with nothing held
between.** `MembershipViewSet.partial_update` and `.destroy` both count
the org's account-wide admins and then write, and `settings.py` sets no
`ATOMIC_REQUESTS`, so each statement autocommits. Two admins demoting
*each other* at the same moment both read a count of 2, both pass, both
write.

**The severity is the consequence, not the trigger.** No attacker needed —
two admins tidying membership at once, or one admin with two tabs. The
organization is then permanently unadministrable: no rename, no
account-wide member management, no invites, no feedback queue.
`_account_wide_admin_count`'s own docstring already called that state
unrecoverable. **Verified by reproducing it**, not reasoning: two threads
against real Postgres, pre-fix both demotions return **200** and the org
is left with **zero** account-wide admins.

**Fixed** with a `select_for_update()` row lock on the Organization inside
`transaction.atomic()` on both paths, re-reading the membership inside the
lock. Two details pinned in the helper's docstring rather than left to be
re-derived: the lock must be on the *organization* row, not the membership
rows (the rows a competing request changes aren't the ones this request
read, so locking what you read wouldn't help), and it can't be
`select_for_update()` on the count query — that query is a `DISTINCT` over
a join and Postgres rejects `FOR UPDATE` with both. Creating a membership
can't lower the count, so it doesn't contend for the lock.

**Verified, including the red path.** 12 new tests in a **fifth** section
of `apps/accounts/tests.py` — **98/98** with the suite, up from 90.
Stashing *only* `views.py` while leaving the tests ran them against the
real pre-fix code: **8 of 12 fail**, the headline one stating the finding
in its own message (`0 not greater than or equal to 1 : an organization
must never be left with zero account-wide admins: concurrent demotions
returned [200, 200]`). The 4 that pass both ways are deliberate and say
so — they guard against a "fix" that makes the guard fire when it
shouldn't, the exact failure mode D10 hit on this guard once already.
**One test does work the concurrency tests can't:** it asserts the
`SELECT ... FOR UPDATE` is actually issued, so a race that happened to
serialize on a fast machine can't pass against broken code.

`check` and `makemigrations --check` clean — **no migration**. `npm ci`,
`tsc -b`, `vite build` clean. Local PostGIS 3.4 + PostgreSQL 16.

**A measurement trap worth repeating, because it nearly cost the finding:**
the first pre-fix browser run came back **green** — no defect. It was
wrong. The run had raced the data load and clicked zero cards ("Showing 0
of 0", 0 pinned badges), proving nothing. Hardened with an explicit wait
and preconditions asserted, it reproduces every time. **A red path that
comes back green is a reason to check the harness before believing it** —
the same family as the earlier "don't read an exit code through a pipe"
and "an apt install that reported success while doing nothing" lessons.
Also worth knowing: `gdal-bin` fails to configure in this sandbox
(`iF`), and it does not matter — GeoDjango needs `libgdal.so`/`libgeos_c`,
which install fine.

**Docs:** `docs/open-questions.md` (D15 found → built with its sibling;
new D16 bullet; the ⚠️ correction on D14's paragraph now points at the
fix; queue-state records that the refill mechanism **changed shape rather
than running out**; App-feedback the twenty-second pull),
`build-questions.md` (BUILT entry with the fourteen re-deferral reasons),
and this file's tests bullet (it claimed 90 and four defects in
`apps/accounts/tests.py`).

**No manual change applies, and for D16 that is the finding's shape:**
`roles-and-permissions.md` already promised an organization "can never end
up with zero account-wide admins" — the code simply didn't hold the
invariant the docs asserted, so the fix makes the existing sentence true
rather than needing new prose (the opposite of D13, where the manual had
to gain a sentence). For D15, `properties.md`'s "Showing X of Y" text
stays accurate for every reachable state, as the morning check-in
established. **No screenshots** — nothing visual changed and no
`capture.js` selector is affected.

**Queue state: empty of authorized work again, but the morning entry's
"the reserve is spent" call was wrong** and is corrected in place.
Concurrency is now spent as a lens; the obvious successors over the same
already-read code are **rate limiting / resource exhaustion** (there is
no rate limiting anywhere in the app — flagged 2026-08-27, never
revisited), **failure and partial-write behaviour**, and
**ordering/idempotency**.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher
(which D15's fix now makes safe to land); a real cron for the purge;
server-side search/pagination (*not yet*); quick-log draft persistence;
the Node 20 pass.

### 2026-09-09 — Scheduled PM check-in: the frontend audit comes back
### clean, and the one item it was carrying is misdescribed in both
### directions — the collision it warns about cannot happen

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no
live human joined). Scheduler assigned `claude/funny-euler-cy7w48`, which
already sat at `origin/main` (`6ee52c8`) while local `main` was **3
behind**; moved to `main` per this file's standing rule and
fast-forwarded before reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **twenty-first** empty pull, the steady
state.

**This run audited the frontend as a module** — the surface the last
three check-ins each named as the only remaining reserve, and where
D14's root cause lived. **It came back clean**, and what held is recorded
in `build-questions.md` so it isn't re-derived: one
`dangerouslySetInnerHTML` and it's the server-sanitized markdown branch
(the `html` branch frames a sandboxed document, never inlines); **zero**
`.innerHTML`/`eval`/`new Function`/`document.write` and **zero**
`localStorage`/`sessionStorage` anywhere in `src`; all three
`target="_blank"` carry `rel="noopener noreferrer"`; `canAccess` really
is the single gate both the Manage menu and each sub-page consult;
`useAsync` cancels on unmount *and* on a dependency change; all 19 files
with a submit handler disable on pending; `NotificationsBell` and
`QrCodePanel` clean up their interval, listener and object URLs.

**The D13 pattern was checked properly rather than by grepping counts** —
per *distinct* error variable. `rows.tsx` declares 8 (one per row
component) against 8 render sites, and every one sits on the
unconditional path right inside `return (`, not inside an `editing`
branch. That lesson has been applied everywhere, not just where it was
found.

**D15, and it is a correction rather than a discovery.** The one item the
frontend carried was D14's parting note: `PropertyMapPage` keeps pins in
component state and React Router reuses the component when `:id` changes,
so pins carry over. The carryover is real; **both halves of how it was
described are wrong.**

**The stated consequence cannot happen.** `Activity` and `Sighting`
declare no custom primary key, so ids are global `AutoField` values — a
pin key `activity-5` names a record on the property it was pinned on and
can never match a different record elsewhere. The map filter also reads
over the *current* property's own features, so a stale key matches
nothing: **no cross-property data can ever be drawn, and there is no
leak.**

**The real symptom is a count bug the note misses.** `shownIds.size` is
rendered raw, stale pins included, so pinning two records on property 1
and opening property 2 shows *"Showing 3 of 2 on the map"* — a numerator
exceeding its own denominator — plus a "Clear all" button with no visible
pinned card.

**And it is unreachable today, so it is latent, not live.** Checked, not
assumed: the only in-app link to `/properties/:id` is
`PropertiesPage.tsx:70`, and every `navigate()` to a property page comes
from a *different* route, each mounting the page fresh. Nothing changes
`:id` while the page stays mounted. The queued **org switcher** is
exactly the change that would make it real.

**The recommendation is not the code comment's.** That comment rejects
`key={propertyId}` because it "would also reset the pinned-record set" —
fair as scope for D14's run, but the concern is unfounded: **resetting
pins when the property changes is the correct behaviour**, since the
carryover is the bug. The targeted fix is pruning `pinnedIds` to the
current `itemIds`, which also removes the stray "Clear all".

**Scope stated honestly:** cosmetic and unreachable — the smallest thing
these check-ins have recorded, kept at that size rather than inflated.
Its value is the correction: as written, the note would have sent a build
session hunting an id collision that cannot exist.

**Queue state: D15 is the only takeable item, and the refill mechanism is
now exhausted everywhere.** With the frontend audited there is **no
unopened module left, backend or frontend** — and six of the nine
substantial findings to date came from that one move. A future check-in
needs a different mechanism (a changed threat model, driving the live
host as a user, or an owner answer). Recorded plainly so the next run
doesn't rediscover it: "nothing new" is becoming a real state, not a
failed run.

**Docs:** `build-questions.md` (new 2026-09-09 entry — the clean-audit
inventory, D15, the queue-state point, the six standing questions),
`docs/open-questions.md` (new D15 bullet; a ⚠️ correction stamped on
D14's own paragraph pointing at it; queue-state records the audit and the
exhausted mechanism; App-feedback the twenty-first pull). **No code,
migrations, manual changes, or screenshots** — `docs/manual/properties.md`
was re-read and its "Showing X of Y on the map" text is accurate for
every state a user can actually reach, so documenting an unreachable
count bug would be the wrong fix (the same call the D13 check-in made).
Push notification sent.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher
(now also D15's trigger); a real cron for the purge; server-side
search/pagination (*not yet*); quick-log draft persistence; the Node 20
pass.

### 2026-09-08 (4) — Scheduled programmer session: built D14 — a mistyped
### property URL no longer 500s the app three times, and no longer sends
### the request at all

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/elegant-dirac-fpwxha`; moved to `main` per this file's standing
rule, fast-forwarding **1 commit** to `2f168b6` before reading anything.
Read `docs/open-questions.md` and `build-questions.md` per the triage
rule. **The owner's "Build next run" authorization is long spent and was
not treated as covering this.**

Dev host healthy, checked before and after the build — no blocker.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **twentieth** empty pull, the steady state.

**The morning check-in left exactly one takeable item; this run took it
and re-deferred the other fourteen with stated reasons** (table in
`build-questions.md`).

**Backend: one shared helper, four call sites, no migration.** New
`apps/accounts/query_params.py` (`int_query_param`) parses the id and
raises DRF's `ValidationError` instead of letting the string reach the
database driver. Wired into activities, sightings and tasks;
`apps/pages/views.py` switched its import to DRF's `get_object_or_404`,
which catches `(TypeError, ValueError, ValidationError)` where Django's
catches only `DoesNotExist` — the difference that made the DRF detail
routes fine and that one hand-written lookup not.

**The queued sub-question was answered with a rule, not a preference,
which is the part worth keeping.** "400 vs 404 vs ignore" resolves to
**match what a valid-but-nonexistent id already does at that call site.**
On a *filter*, a valid id matching nothing returns 200 and an empty list
by design, so 404 is the wrong shape and 400 is honest. On the *lookup*
in pages, which already 404s a cross-org id, a malformed id is "no such
property" — so 404. The rule is in the module docstring, not just its
outcome.

**A behavioural trap that would have been silent:** the helper returns
`None` for an *empty* value as well as an absent one, and callers test
`is not None`, not truthiness. `?property=` (empty) has always meant "no
filter"; `?property=0` has always filtered, because `"0"` is a truthy
*string*. Testing truthiness on a parsed int would have flipped the
second case with nothing on screen to explain it. Pinned by a test.

**Frontend — the root cause, and the better fix.** New `utils/ids.ts`
(`parseRouteId`) plus a shared `RecordNotFound`; `PropertyMapPage`,
`ActivityFormPage` and `SightingFormPage` guard their route params
**before any request is issued**, each via a thin outer component around
the existing loader — the outer-loader/inner split the two form pages
already used, rather than changing the shared `useAsync` contract for
every page in the app. `parseRouteId` also rejects negative and
fractional ids: every id here is a positive integer key, and
`Number("-3")` is a good number no row will match.

**Verified, including the red path.** 8 new tests in a **fourth**
section of `apps/accounts/tests.py` (placed there because the shared
helper is, though the endpoints span four other apps) — **90/90** with
the suite, up from 82. Stashing *only* the four view files while leaving
the tests and helper ran them against the real pre-fix code: **5 of 8
fail, 13 subtest errors**, with `ValueError: Field 'id' expected a number
but got 'NaN'` in the traceback — the 500 itself. The 3 that pass both
ways are deliberate and say so in their docstrings (don't make the
filters strict about existence; the param must still filter; empty still
means no filter). `check` and `makemigrations --check` clean — **no
migration**. `npm ci`, `tsc -b`, `vite build` clean. Local PostGIS 3.4 /
GDAL 3.8.4 + PostgreSQL 16.

**Then driven in a real browser, because the finding is about what a user
sees:** 19 Playwright checks in Chromium at 390px against a live stack —
four malformed URL shapes each show the not-found message, issue **no
malformed request at all**, and produce no 5xx; a mistyped activity edit
URL names the activity, not the property; a real property still saves,
opens and fires its normal property-scoped requests. **The screenshot was
looked at, not just asserted on** — the message wraps cleanly at phone
width and keeps the back link and nav. Zero 500s in the backend log.

**Two measurement traps hit this run, both reusable:** (1) an apt install
reported success while doing nothing — the exit code read was the
trailing `tail`'s, not apt's, and the log said `dpkg was interrupted`;
`dpkg -l | grep` settled it. Same family as the "don't read an exit code
through a pipe" lesson, but the culprit was the last command in the
script. (2) `pip install` hit the documented `files.pythonhosted.org`
read timeout again; `--timeout 300 --retries 15` cleared it.

**Docs:** `docs/open-questions.md` (D14 found → built; queue-state records
the one-run refill and re-emptying, and that the frontend is *still*
unaudited as a module even though D14's three sites are fixed;
App-feedback the twentieth pull), `build-questions.md` (BUILT entry with
the fourteen re-deferral reasons), this file's tests bullet (it claimed
82 and three defects in `apps/accounts/tests.py`), and the manual —
`limitations.md`'s testing bullet claimed the suite "covers the public
site's visibility rules and little else", which the previous check-in
flagged as understated and left for the next session touching that file;
it now names what runs while keeping the honest warning that the suite is
deliberately narrow. **No screenshots** — the not-found screen is a new
state no existing screenshot claims to show, and no `capture.js` selector
is affected.

**Queue state: empty of authorized work again after exactly one run —
the same rhythm as the previous cycle**, now the established pattern
rather than a coincidence. The only reserve left is the frontend, which
no check-in has audited as a module.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher;
a real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass.

### 2026-09-08 (3) — Scheduled PM check-in: the app 500s itself three
### times over on a mistyped URL — and the audit that keeps refilling this
### queue has now run out of backend to audit

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no
live human joined). Scheduler assigned `claude/hopeful-rubin-6o8n7x`;
moved to `main` per this file's standing rule. **`main` was already
current at `b44ff0e`** — no fast-forward needed, unlike the last several
runs.

Dev host healthy. D7 confirmed still live (CSRF cookie carries `Secure`);
HSTS still absent, still correctly an owner call.
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **nineteenth** empty pull, the steady state.

**This run audited `apps/tasks/` and `apps/pages/`** — the two modules
the last entry named as never opened — and **both came back clean on
their own terms**, which is recorded in `build-questions.md` so it isn't
re-derived: the pages module's sandbox headers, per-tenant kill-switch
and soft-delete guards all hold, and `PublicPageDetailSerializer` has no
path that inlines author HTML; the tasks module's org checks are real and
`perform_update` reads the previous assignee before `save()`, so
reassignment notifications fire on the true transition.

**D14 came from a pattern cutting across five modules instead.** A
non-numeric query param reaches the database layer and returns an
**unhandled 500** — and the ordinary UI sends one: `/properties/abc` is a
real route, `PropertyMapPage` does `Number(id)` with **no NaN guard**,
and `withQuery` skips only `undefined`, so the literal `NaN` goes on the
wire. One mistyped URL produces **three 500s** where "no such property"
is the truth.

**The sharpest framing is that DRF already ships the fix and four call
sites don't use it.** `rest_framework.generics.get_object_or_404` catches
`(TypeError, ValueError, ValidationError)` — its docstring says it exists
for exactly this — while `django.shortcuts.get_object_or_404` catches
only `DoesNotExist`. That is why the DRF detail route correctly 404s on
`/api/properties/NaN/` and `apps/pages/views.py:57` does not.

**Verified empirically on the repo's own pinned Django 5.2.17 / DRF
3.15.2**, reproducing each call site's shape on plain non-GIS models —
`?property=NaN` → 500 on three endpoints, `?property=999` → 200, detail
route → 404. **Scope stated honestly:** no data exposure, no cross-org
reach, no escalation; all four endpoints are authenticated. This is
500-hygiene, the same low-severity class as D13.

**A sweep narrowed it a lot and is worth not redoing:** every URL *path*
parameter uses an `<int:>`/`<slug:>`/`<str:token>` converter, so all ~40
path-param `get_object_or_404` sites are protected at URL resolution.
Only the four query params are exposed. `?blooming_on=` already returns
400 on bad input — the in-repo precedent for the fix.

**A correction to this run's own working, kept because the trap is
reusable:** an early check grepped Django's shortcut for `"ValueError"`
and concluded it catches it. It doesn't — that match is a `raise
ValueError` for a bad first argument. The empirical 500 is the truth.
Don't test for an exception handler by grepping for the exception's name.

**Queue state: refilled by one item, and the refill mechanism is now out
of backend.** D14 needs no owner answer, so it is the only thing a build
session may currently take. More importantly, with these two modules
audited **no unaudited backend module remains** — and six of the eight
substantial findings to date came from opening a module nobody had
opened. The only surface left for that move is **the frontend, never
audited as a module**, which is also where D14's root cause lives
(`Number(id)` unguarded in three pages; no `isNaN`/`isFinite` anywhere in
`frontend/src`).

**Docs:** `build-questions.md` (new 2026-09-08 (3) entry),
`docs/open-questions.md` (D14 bullet; queue-state records the refill and
the exhausted-backend point; App-feedback records the nineteenth pull).
**No code, migrations, manual changes, or screenshots** — `limitations.md`
was re-read and makes no claim D14 falsifies; one small inaccuracy found
there (its testing bullet still describes the suite as covering "the
public site's visibility rules and little else", now understated at 82
tests across six modules) is **recorded, not fixed**, per this session's
scope. Push notification sent.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher;
a real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass.

### 2026-09-08 (2) — Scheduled programmer session: built D12 and D13 —
### the queue filled a session for the first time in eight runs, and a
### frontend gap meant D13's fix would otherwise have reached nobody

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/adoring-curie-ln467q`; moved to `main` per this file's standing
rule, fast-forwarding **40 commits** before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **eighteenth** empty pull, the steady
state.

**Both of the morning check-in's items were built, in its recommended
order — the first run in eight where the queue supplied a whole
session's work rather than one item.** All 13 other queued items are
re-deferred with stated reasons in `build-questions.md`.

**D12: `species` is now in `read_only_fields`.** The reasoning is pinned
**on the field**, not at the call site, because the change that would
undo this is someone making it writable again — and that person is
reading the serializer. Read-only rather than validated was re-checked
rather than inherited: `client.ts` types the PATCH payload as
`Partial<{role; quantity; detail}>`, so no caller sends the field.
Also commented `SightingActivityLinkSerializer`, the latent sibling that
is safe only because nothing writes through it.

**D13 mirrors `ActivityTypeViewSet.destroy` and names both relations —
with one nuance the recommendation didn't anticipate, found while
building.** `ActivitySpecies` has **no unique constraint** on
`(activity, species)`; only the POST path's `get_or_create` keeps it to
one row per pair. Counting through-rows — what the obvious
implementation does — would tell an admin to go and fix two activities
that don't exist. It counts **distinct activities**, and a test pins it.

**The part worth reading: a frontend gap meant the backend fix would
have reached nobody.** `SpeciesRow.handleDelete` set an error into state
that the **non-editing render path never displayed** — the
`{error && …}` line existed only inside the `editing` branch. A refused
delete would have looked like a Delete button that silently did nothing,
arguably worse than the 500 it replaced. This is why the run was driven
in a browser instead of trusted to a green suite.

**Verified, including the red path.** 18 tests in **two new modules**
(`apps/activities/tests.py`, `apps/species/tests.py` — the repo's fifth
and sixth), **82/82** with the suite, up from 64. Stashing only the three
tracked source files while leaving the tests ran them against the real
pre-fix code: **13 of 18 fail**. The 9 species errors are the raw
`ProtectedError` — the 500 itself; one activities failure reproduces the
cross-tenant denial verbatim in its own error text (`'Their Secret
Orchid' on Seeding (Mine)`). The 5 that pass both ways are deliberate and
named in each docstring: three guard against a "fix" that breaks the
endpoint's real job, two pin the POST path that was always correct and is
what makes the finding legible.

`check` and `makemigrations --check` clean — **no migration**. `npm ci`,
`tsc -b`, `vite build` clean. Local PostGIS/GDAL + PostgreSQL 16 (usual
fallback; two stale PPAs still need removing first). Exit codes read from
files, never a pipe. **Then 8 Playwright checks in Chromium at 390px
against a live stack** — a real in-use species deleted through the real
UI shows the visible refusal, stays listed, wraps inside its card, and no
500 reaches the browser; an unused one still deletes. **The screenshot
was looked at, not just asserted on.** Console noise was checked against
the backend log rather than assumed benign: two pre-signup
`/api/auth/me/` 403s and the 400 that is the refusal.

**Worth knowing for the next session:** the pinned `playwright@1.62.1`
wants a browser build this sandbox doesn't have; launch with
`executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'`
rather than running `playwright install` (no egress to the download
host).

**Docs:** `docs/open-questions.md` (both bullets found → built;
queue-state records the same-day re-emptying; App-feedback the eighteenth
pull), `build-questions.md` (BUILT entry with all 13 re-deferral
reasons), this file's tests bullet (it claimed 64), and the manual —
`species.md` gains "A species that's in use can't be deleted" (which the
morning entry said the *fixing* session should write, because it would
then be true) and `limitations.md` the matching bullet. **No
screenshots** — the refusal is a new state no existing screenshot claims
to show, and no `capture.js` selector is affected.

**Queue state: empty again, and the refill lasted exactly one run** — a
refinement of the eight-run pattern, not a restatement. The only known
reserve is what no check-in has opened: `apps/tasks/`, `apps/pages/`, and
the frontend as a module.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher;
a real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass.

### 2026-09-08 — Scheduled PM check-in: one endpoint's POST and PATCH
### halves disagree about whose species you may reference — and the
### species list is the one per-org table that never got the delete guard

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no
live human joined). Scheduler assigned `claude/funny-euler-a71h7m`; moved
to `main` per this file's standing rule, fast-forwarding **39 commits**
before reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **seventeenth** empty pull, the steady
state. D7 still live (CSRF cookie carries `Secure`); HSTS still absent,
still correctly an owner call.

**This run audited the three modules the last entry's pattern note named
as never opened** — `apps/activities/`, `apps/sightings/`,
`apps/species/` — and they held **two build-ready defects**, so the
prediction that the audit is what refills the queue held up.

**D12: an editor can attach another organization's species to their own
activity.** `ActivitySpeciesSerializer` leaves `species` writable
(`read_only_fields = ["activity"]` only), and
`activity_species_detail`'s PATCH passes `data=request.data` with **no
context and no org check**. **The sharpest framing is that the two
halves of one endpoint disagree:** the POST path 24 lines above does
`get_object_or_404(Species, id=..., organization=activity.organization)`
and rejects exactly the id PATCH accepts.

**Why the 2026-09-01 cross-org FK pass missed it:** that session fixed
`ActivitySerializer.property/status/activity_type` and
`SightingSerializer.property/species`, all on `ModelViewSet`s. This one
is a *through-model* serializer driven by a function-based view. A sweep
confirms it is the **only** remaining instance.

**Verified empirically on the repo's own pinned Django 5.2 / DRF 3.15**,
by reproducing the serializer's exact shape on plain non-GIS models:
the PATCH validates, saves, and returns the other org's `species_name`.
Three consequences: cross-org disclosure by id enumeration — and
`species_names` is served **unauthenticated** by the public site, so a
foreign name can be republished on the attacker's own public page; a
**cross-tenant denial** (`PROTECT` means org A's row blocks org B from
deleting its *own* species, via a row org B can't see); and integrity.
**Scope honest:** editor-gated, so a cross-tenant primitive, not an
unauthenticated hole, and nothing was written to the live instance.

**Recommended fix is `species` in `read_only_fields`, and that was
checked rather than assumed:** `client.ts:569` types the PATCH payload
as `Partial<{ role; quantity; detail }>` — the frontend never sends
`species` — so read-only breaks nothing and needs no validation code.

**D13: deleting an in-use species is an unhandled 500.** `SpeciesViewSet`
has no `destroy()` guard; both FKs into `Species` are `PROTECT`.
Measured, not assumed: `ProtectedError` subclasses `IntegrityError`, and
DRF's `exception_handler` returns `None` for it, with no custom
`EXCEPTION_HANDLER` anywhere. **What makes it worth recording: the same
file's two siblings already fixed exactly this, twice, with comments
saying so** — `WorkflowStateViewSet` and `ActivityTypeViewSet` both
return a 400 naming how many records are in the way. Species is the
third per-org reference list and the only one without it. Fix mirrors
`ActivityTypeViewSet.destroy`; note the count spans **two** relations.

**A correction to this run's own working, kept because the trap is
reusable:** an early probe seemed to show the host running pre-D8 code
(which would have meant D10's escalation fix wasn't live). Wrong — the
string grepped for lived only in a **code comment**, which Vite strips.
Re-measured on user-visible strings: **the host does carry D8**. Also:
a nonexistent path returns **200** there (SPA fallback serves a 549-byte
`index.html`), so status code proves nothing and content must be
compared. D9/D10 are backend-only with no unauthenticated observable, so
their deployment is unconfirmable from outside; confirming D10 would
mean deleting a property on the live instance, deliberately not done.

**Audited clean:** sightings' soft-delete OR and both-sides link scope
checks; the bloom filter's wrap handling and its 400 on bad input; the
workflow-state/activity-type guards including their ordering. One latent
thing recorded but **not** called a defect —
`SightingActivityLinkSerializer` also leaves `sighting`/`activity`
writable, but nothing ever writes through it (both endpoints use
`get_or_create` on org-checked objects; there is no PATCH route). It
becomes a real D12 the day someone adds one.

**Queue state: for the first time in eight runs there is work a build
session may take without asking** — D12 and D13, both fork-free, D12
first since it is the one that crosses an org boundary. Never-audited
modules are now down to `apps/tasks/` and `apps/pages/`, plus the
frontend, which has never been audited as a module.

**Docs:** `build-questions.md` (new 2026-09-08 entry),
`docs/open-questions.md` (D12/D13 bullets; queue-state and App-feedback).
**No code, migrations, manual changes, or screenshots** —
`limitations.md` was re-read and makes no claim either defect falsifies;
D13's manual gap is an absence the fixing session should write, since
documenting today's 500 as intended behaviour would be the wrong fix.
Push notification sent.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; D11; due dates on tasks; the D6 backfill query; the org switcher;
a real cron for the purge; server-side search/pagination (*not yet*);
quick-log draft persistence; the Node 20 pass.

### 2026-09-07 (4) — Scheduled programmer session: built D9, then found and
### built D10 — deleting a property promoted a property-scoped admin to a
### full account-wide one, with one supported click

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/elegant-dirac-zdafwx`, already at `origin/main` (`8ca82cb`) while
local `main` was **37 behind**; fast-forwarded to `main` per this file's
standing rule before reading anything. Read `docs/open-questions.md` and
`build-questions.md` per the triage rule. **The owner's "Build next run"
authorization is long spent and was not treated as covering this.**

Dev host healthy. `GET /api/feedback/pull/` returned `[]` — the
**sixteenth** empty pull, the steady state.

**D9 built, and it is the first run in seven where the queue actually
supplied the work.** `apps/feedback/auth.py` uses
`constant_time_compare` now. New `apps/feedback/tests.py` (the repo's
fourth module), 10 tests. **Only 1 of the 10 fails against the pre-fix
code, and that is the honest shape:** a timing channel has no functional
symptom, so that one pins the *mechanism* rather than a result. The other
nine exist for the invariant that would actually be catastrophic and that
nothing had ever asserted — **an unset token denies everything** (most
deployments have never set `HABITAT_FEEDBACK_TOKEN`).

**Taking only a one-line fix would have been a thin session, so the run
continued into an audit of `org_scoping.py`** — the module every scoped
queryset derives from, and one no check-in had opened. That found **D10**,
the most severe defect these audits have produced.

**`scoped_property_ids` read scope through `membership.properties`.** A
related manager inherits the *related* model's default manager, and
`Property`'s hides soft-deleted rows — so a membership whose scoped
properties were all deleted came back empty, and **empty is this module's
encoding for "account-wide over the whole organization"**.

**The severity is the trigger, not an exotic input.** DELETE on a
property is admin-gated *and* scope-filtered, so a property-scoped admin
is authorised to delete its **own** property — and that one click
promoted it. **Verified through the real HTTP endpoints against pre-fix
code**, not reasoned about: the caller then got **200 renaming the
organization**, could reach the org's real account-wide admins, and could
hand out account-wide scope. No second actor, no race, no waiting.

**Two siblings, which is why the fix is four files.** The
invitation-accept path copied scope the same way, so an invitation whose
property was deleted before acceptance created an **account-wide
member**. And the lockout guard, inverted: it asked
`membership.properties.exists()` while `_account_wide_admin_count` asked
with a **join** — a join bypasses the manager, so the count was right and
the check was wrong, and once they disagreed the guard refused to let
anyone demote or remove that admin. Not an escalation; the tell that
"account-wide" was defined twice. One definition now
(`is_property_scoped`).

**Fixed** by reading stored scope from the **join table** in one helper
(`stored_scope_ids`) used everywhere scope is *determined* — the helper,
both membership serializers, the invitation copy. **`all_objects` was the
first fix and it was not enough, which is the lesson worth keeping:** a
`prefetch_related("properties")` is populated through the *default*
manager and then satisfies a `manager="all_objects"` call from its own
cache, so the escape hatch silently stops escaping. The member list
prefetches exactly that, and the new list-consistency test failed on it —
caught by a test, not by reading the diff. Querying the through model
can't be shadowed by a prefetch or by any manager on Property. **Least
privilege falls out rather than being bolted on:** the deleted property is still filtered from data on the way out, so
such a member sees **nothing** rather than everything, and gets its exact
access back on restore. No migration.

**Verified, including the red path.** 14 tests appended to
`apps/accounts/tests.py` (third section — D6, D8, now D10). **64/64**
with the suite, up from 40. Reverting only the three tracked source files
while leaving the tests ran them against the real pre-fix code: **8 of 12
fail**, the end-to-end one stating the finding in its own message
(`200 != 403 : a property-scoped admin must not be able to rename the
organization after deleting its own property`). The four that pass both
ways are deliberate — one pins the Django semantic the defect rests on,
one is the restore path, one guards against loosening the lockout guard.

`check` and `makemigrations --check` clean. **No frontend file changed,
so no `tsc -b`/`vite build` was run and none is claimed** — the
serializer still returns a list of ids; what changed is that it now tells
the truth. Local PostGIS/GDAL + PostgreSQL 16 (usual fallback; the two
stale PPAs still need removing first). Exit codes read from files, never
a pipe.

**D11 — deliberately not built, and a genuine fork.** After the 30-day
purge the join rows cascade away, so a membership scoped only to purged
properties becomes account-wide **for real** and indistinguishable from a
legitimate one (verified: `ensure_account_wide_admin` allows it
post-purge). **D10's fix bounds this to the retention window; it does not
close it** — said plainly rather than glossed. The remedies (demote at
purge, delete the membership, or add a field so "scoped to nothing" is
representable) are all decisions, so it is recorded with a recommendation
((c)) instead of guessed. It is also in `limitations.md` with concrete
advice, because it is live behaviour today.

**Docs:** `docs/open-questions.md` (D9 built; new D10/D11; queue-state and
App-feedback), `docs/data-model-notes.md` (how "account-wide" is encoded
and the trap in it), `build-questions.md` (BUILT entry with all eleven
re-deferral reasons), this file's tests bullet (it claimed 40), and the
manual — `roles-and-permissions.md` and `properties.md` (deleting a
property doesn't change anyone's role) and `limitations.md` (D11).
**No screenshots** — nothing visual changed, no `capture.js` selector
affected.

**Pattern worth keeping:** seven runs in, the queue supplied *an* item for
the first time — but not enough to fill a session. The substantial finds
keep coming from auditing a module no prior check-in had opened (D3, D6,
D7, D8, D10). Still never opened: `apps/activities/`, `apps/sightings/`,
`apps/species/` beyond cross-org FK validation.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair; D5's Q1/Q2; D8's
Q1/Q2; **D11**; due dates on tasks; the D6 backfill query; the org
switcher; a real cron for the purge; server-side search/pagination (*not
yet*); quick-log draft persistence; the Node 20 pass.

### 2026-09-07 (3) — Scheduled PM check-in: D8's two questions both shrink
### under measurement — Q1 is one row and needs no build session at all;
### Q2 wouldn't have covered the exposed org

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Scheduler assigned `claude/hopeful-rubin-c5ygt3`, which
already sat at `origin/main` (`d421f61`) while local `main` was **36
behind**; fast-forwarded to `main` per this file's standing rule before
reading anything.

Dev host healthy. `GET /api/feedback/pull/` returned `[]` with both
negative controls re-run — the **fifteenth** empty pull, the steady
state. **D7 confirmed still live** (CSRF `Set-Cookie` carries `Secure`);
HSTS still absent, which is correct and still an owner call.

**The finding is that yesterday's own item got smaller in both
directions, and only measuring the live host showed it.**

**D8's Q1 is one row, and its remediation needs no build session.** The
deployment holds **exactly two organizations** (ids 1/2 → 200, 3-10 →
404). Org 1 is `test`, unaffected; org 2 is the only email-derived one.
So "backfill existing rows" is a single admin action, not a migration —
and the tradeoff that made it the owner's call (*clearing a slug breaks
an already-shared URL*) is at most one tester's own link. Verified in
code rather than assumed: `OrganizationSerializer` takes a blank `slug`
write as "regenerate from the name", which `Organization.save()` does
(`if not self.slug`), so renaming **and** clearing the Public URL name on
Manage → Organization fixes it today — exactly the two-step yesterday's
build put on that screen.

**D8's Q2 would not have protected org 2, which yesterday's entry
implies it would.** That entry described the case as an account
publishing "nothing at all". On the live host org 2 **does** publish —
one public property, `Shop yard`. So an `is_public` gate defaulting to
`True`, or derived from "has this org published anything", leaves org 2
exposed exactly as it is. Q2 is still a real question about the
asymmetry with `Property`; it is **not** the remedy, and answering it
shouldn't be mistaken for closing the exposure. The address stays
redacted from committed files, same reasoning as yesterday.

**D9 — one new build-ready item, deliberately low-severity.**
`apps/feedback/auth.py` compares its bearer token with `!=`, which
short-circuits on the first differing byte. Scope stated honestly: over
HTTPS across the internet, jitter swamps it — hardening, not a live hole,
and nothing suggests exploitation. Framed as a build item rather than a
question because there's no fork (`django.utils.crypto.constant_time_compare`,
one line plus an import). Worth recording only because it is **the only
queued item a build session may currently take without asking**, and the
last six programmer runs each had to source their own work.

**Audited clean, in two areas no prior check-in had opened.** The
invitation/password-reset token flows: the invitee's email comes from the
invitation row, never the request body (so a token holder can't redirect
an invite); expiry enforced on preview, accept and reset-confirm;
one-time use via `used_at`; bad/used/expired all answered identically, so
neither flow is an enumeration oracle; both atomic. And the feedback app
beyond D9: admin list/resolve are org-scoped *and* account-wide-admin
gated, `feedback_config` is authenticated, `_clean_page_path` rejects a
scheme and `//host`, and `mark_synced` only touches `new` rows.

**Docs:** `build-questions.md` (new 2026-09-07 (3) entry — the two
re-measurements, D9, the clean audit, the six questions),
`docs/open-questions.md` (D8 bullet gains the re-measurement; new D9
bullet under "Tech / infrastructure"; queue-state records that the queue
is no longer empty, by one item; App-feedback records the fifteenth
pull). **No code, migrations, manual changes, or screenshots** —
`limitations.md` was re-read and already records the Q2 gap accurately
(added yesterday), so there was nothing to correct; D9 isn't
user-facing. Push notification sent.

### 2026-09-07 (2) — Scheduled programmer session: built D8's additive
### half — a nameless signup no longer publishes the user's email address

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/adoring-curie-32u9en`, which already sat at `origin/main`
(`2489806`) while local `main` was **35 behind**; fast-forwarded to `main`
per this file's standing rule before reading anything. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy (`GET /` and `/api/auth/csrf/` both 200).
`GET /api/feedback/pull/` returned `[]` with the negative control re-run
(tokenless → 403) — the **fourteenth** empty pull, the steady state.

**The morning check-in predicted the queue held nothing this run could
build, and it was right for the sixth run running.** All eleven items are
re-deferred with stated reasons in `build-questions.md`. So this run took
**D8's additive half**, the same move the two 2026-09-05 runs made for D4
and D5 — and it is the sixth consecutive run to have to source its own
item.

**Built: signup no longer derives the account name from the email.**
`Organization.DEFAULT_NAME` (`"My land"`) replaces the
`f"{email}'s land"` literal. The reason is pinned in a comment **on the
constant**, not at the call site, because the change that would undo this
is someone adding a friendlier email-derived default back — and that
person is reading the model, not the view.

**Why this half needed no owner decision, which is the whole reason it
was takeable:** it is a class constant, not a field, so **no migration**;
and it affects only rows created from now on, so **no existing row
changes and no already-shared public URL breaks**. Those are exactly the
costs that make Q1 and Q2 the owner's.

**The disclosure gap was the other half of the finding, and it is closed
in all three silent places.** D8's sharpest point was that the affected
person was never told. Signup now says the name is shown publicly and
what blank does (and the placeholder no longer suggests "your name").
**Manage → Organization** says the name is public **and** that renaming
doesn't change an existing public URL — the non-obvious half, and
load-bearing: `Organization.save()` regenerates a slug only
`if not self.slug`, so an admin renaming to take something *out* of
public view must clear the Public URL name too. That is the exact screen
the morning entry says org id 2's owner needs, so the trap is now on the
screen instead of in a doc.

**Deliberately NOT built, and the split is the point:** D8's Q1 (backfill
existing email-derived rows — a rename leaves the old slug serving,
clearing it breaks a shared URL) and Q2 (an `is_public` gate on
`Organization` — either default has a real cost). Both stay the owner's.
**Org id 2 on the dev host is still exposed right now**; an admin can
clear it today, changing *both* fields.

**Verified, including the red path.** 7 new tests
(`apps/accounts/tests.py`, second section — the module now carries two
unrelated defects), **40/40** with the existing suite. Then the part that
earns them: reverting only the tracked `views.py`/`models.py` changes,
while leaving the tests and re-adding *only* the constant so they still
import, ran them against the **real pre-fix call site** — **6 of 7 fail**.
The seventh passes both ways deliberately (it guards against a fix that
stops honouring the field at all). One test,
`test_the_public_page_is_still_served`, exists for a *reader* rather than
a regression: it pins Q2 as open so a green suite can't be misread as
"the org page is gated now".

`manage.py check` and `makemigrations --check` clean — **no migration**.
`tsc -b` and `vite build` clean. Local PostGIS/GDAL + PostgreSQL 16
(usual sandbox fallback; the two stale PPAs still need removing first,
and `pip install` needed `--timeout 120 --retries 8` after a
`files.pythonhosted.org` read timeout — worth knowing for the next
session). Every exit code read from a redirected file, never a pipe.

**Then driven for real in a browser**, per this repo's own recurring
lesson: 18 Playwright checks in Chromium at 390px against a live stack —
a real signup through the real UI with the name blank produces
`name = "My land"` / `slug = "my-land"`, and the anonymous public payload
**and rendered page** contain no `@` at all. **The screenshots were
looked at, not just asserted on:** the hint wraps cleanly at phone width,
and the public page for a publish-nothing account now reads "My land"
where it would have read an email address.

Worth not re-deriving: the first Manage assertion failed on a
**selector**, not the app — `.field` filtered by
`hasText: "Organization name"` matches *two* fields, because the Public
URL name hint contains the words "the organization name".

**Docs:** `docs/open-questions.md` (D8 rewritten to additive-half-built
with Q1/Q2 kept explicitly open; queue-state records that six consecutive
programmer runs have now had to invent their own item, and that the
fork-free pieces are being taken first so the next run may find none
left; App-feedback records the fourteenth pull), `build-questions.md`
(new BUILT entry with all eleven re-deferral reasons), this file's tests
bullet (it claimed 33), and the manual — `getting-started.md` (a new
"Your account name is public" section; its old text **quoted the
placeholder I changed**, so it was actively wrong, not just stale),
`organization-admin.md` (the rename/slug two-step),
`public-site.md` (a new section stating plainly that the org page is
**not** gated) and `limitations.md` (the Q2 gap, recorded honestly rather
than left undocumented).

**No screenshots** — today's allowance is available (last regen
2026-09-03) but the change is an added hint line: `signup.png` is
slightly stale, not *wrong* (no control renamed or removed, alt text
still accurate), and `capture.js` needed no change since it fills the
form by input type and never touches the placeholder or hint.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; HSTS and the
`SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair (confirmed still off
today); D5's Q1/Q2; **D8's Q1/Q2**; due dates on tasks; the D6 backfill
query; the org switcher; a real cron for the purge; server-side
search/pagination (*not yet*); quick-log draft persistence; the Node 20
pass.

### 2026-09-07 — Scheduled PM check-in: signing up without naming your
### account publishes your email address — and every org is readable by
### anyone, published or not

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Scheduler assigned `claude/funny-euler-hpbll4`, which
already sat at `origin/main` (`1748974`) while local `main` was **34
behind**; fast-forwarded to `main` per this file's standing rule before
reading anything.

**Yesterday's D7 fix is confirmed live, not just merged.** The deployed
host's CSRF `Set-Cookie` now carries `Secure`, where yesterday it did
not — so the deployment picked up the commit. HSTS is still absent, which
is correct: D7 left it as an owner call deliberately, and it's re-raised
rather than treated as a gap. `GET /api/feedback/pull/` returned `[]`
with both negative controls re-run — the **thirteenth** empty pull, the
pipeline's steady state.

**D8, and it came from a thread rather than a hunch.** The audit pass
started by asking whether D3's soft-delete guard had reached the public
site's *theme-image* endpoints. It had — `property_theme_image` resolves
through `_public_property_or_404`, which inherits the soft-delete
manager. Its sibling `organization_theme_image` doesn't gate at all, and
pulling that thread found the larger thing: **`organization_detail` and
`organization_detail_by_slug` have no gate whatsoever** — a bare
`get_object_or_404(Organization, …)` serving name, slug, theme and
`created_at` to anyone. Combined with `views.py:105` naming a nameless
org `f"{email}'s land"` and that field being **optional** at signup, a
user who publishes nothing still has their email address served
unauthenticated at a stable URL.

**Verified on the live host:** org id 2 is exactly this case, on both the
numeric and the vanity-slug route, and ids enumerate (1/2 → 200, 3/4/5 →
404). The address is **redacted in the committed docs deliberately** —
writing a third party's email into a repo file spreads it further, which
is the very thing the item is about.

**The asymmetry is the sharpest way to hold it:** `Property` deliberately
404s when private so a guessed id "can't even confirm something exists"
(the 2026-08-14 stance, still in that module's docstring), and
`Organization` has no equivalent. The two halves of the same public site
take opposite stances, and the ungated half is the one carrying PII.
**Scope stated honestly:** no credentials, no private land data —
`_organization_payload` filters properties correctly. What leaks is an
email plus an account's existence and age, to someone never told: neither
the signup screen nor the manual says the account name is published.

**Recorded as a question, not a build-ready item** — the same call D5 got,
the opposite of D3/D4/D6 — because the fix has a real fork. Q1: what the
new default should be, and whether existing rows are backfilled — not
free, because `Organization.save()` regenerates a slug only `if not
self.slug` (`models.py:137`), so a rename leaves the email-derived slug
serving and clearing it breaks an already-shared URL. Q2: whether
`Organization` gains an `is_public` gate at all. PM recommendation: Q1 for
new signups only, existing rows by hand, Q2 treated as its own question.
**One thing needs no build:** org id 2's exposure is live now and an admin
can clear it today — but **both** the name and the **Public URL name**
must change, per `models.py:137`.

**Queue state — sixth consecutive run with nothing a build session may
take.** D8 joins the ten already-deferred items rather than refilling the
queue. The one-line answers that would change that grew by two: B2 and the
contextual menu (both anchored 2026-09-03), the publish gate, and **HSTS
plus the `SECURE_SSL_REDIRECT`/`TRUST_X_FORWARDED_PROTO` pair** left open
by D7 and confirmed still off today.

**Docs:** `build-questions.md` (new 2026-09-07 entry), `docs/open-questions.md`
(new D8 bullet under "Accounts, orgs, and permissions"; queue-state and
App-feedback sections updated). **No code, migrations, manual changes, or
screenshots** — `limitations.md` was re-read and makes no claim about what
the public organization page exposes, so there is nothing to *correct*;
the manual gap D8 describes is an absence, and the session that changes
the behaviour should write it, since it will then be true. Push
notification sent.

### 2026-09-06 (4) — Scheduled programmer session: built D7 — the site is
### served over HTTPS and its cookies were not marked `Secure`; Django had
### been reporting it all along, in a check nothing ran

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Scheduler assigned
`claude/elegant-dirac-cmjn7w`; moved to `main` per this file's standing
rule, fast-forwarding **33 commits** before reading anything, since a
stale local ref makes `build-questions.md` read as an older queue than the
one that exists. Read it and `docs/open-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

Dev host healthy (`GET /` and `/api/auth/csrf/` both 200).
`GET /api/feedback/pull/` returned `[]` with both negative controls
re-run — the **twelfth** empty pull, and the pipeline's steady state.

**The morning check-in predicted the queue held nothing this run could
build, and it was right.** All ten items are re-deferred with stated
reasons in `build-questions.md`. So this run sourced its own item — the
**fifth consecutive** run to have to.

**Built D7: `settings.py` had no transport-security settings at all.**
Django's defaults therefore applied, and the deployed HTTPS site handed
out session and CSRF cookies with **no `Secure` attribute**.

**Verified against the live host, not reasoned about**, and the finding is
three facts that only matter together: the CSRF `Set-Cookie` carries
`Path=/; SameSite=Lax` and **no `Secure`**; there is **no HSTS header**;
and **port 80 is reachable** (404 on both `/` and `/api/...`, no HTTPS
redirect). So a browser holding a session that is induced into any plain
`http://` request to the host — an `http://` image anywhere, a stale
bookmark, a typed address — puts `sessionid` and `csrftoken` on the wire
in cleartext. **The 404 protects nothing: the cookies are in the request,
not the response.** Scope stated honestly rather than overclaimed: it
needs an on-path attacker *and* a trigger for one plaintext request, so
it's a transport weakness, not a remotely-exploitable hole, and nothing
suggests exploitation.

**Why it survived is the part worth keeping.** Django's own
`manage.py check --deploy` had been reporting exactly this
(`security.W012`, `security.W016`) for the life of the deployment. Those
checks aren't part of plain `manage.py check` — which is what CI runs —
so the finding sat in the tooling, unread, the whole time. That's now
closed: `config/tests.py` runs the deploy checks against a resolved
`DEBUG=0` configuration.

**The one real decision: the cookie flags default to `not DEBUG`, not to
a fixed value.** It cuts both ways — a hardcoded `True` breaks every
developer (local dev is plain HTTP, where a browser silently refuses to
store a `Secure` cookie, so login fails with nothing on screen to explain
it), and a hardcoded `False` is what shipped. Deriving from `DEBUG` means
the flag that already separates a laptop from a deployment flips these
too, so **the live host — confirmed to run `DEBUG=0`, since it serves
Django's `DEBUG=False` 404 page — gets the fix on its next image pull with
no config edit.** Recorded as a deployment note: a `DEBUG=0`-over-HTTP
deployment would need to opt back out; there is none today.

**Three settings that needed an owner call were left off and documented
rather than guessed.** `SECURE_HSTS_SECONDS` stays 0 deliberately, and the
asymmetry with the cookie flags is the point: a browser *remembers* HSTS
and it can't be recalled within its `max-age`, so it's a commitment with a
tail rather than a code default (recommended: `31536000`). And
`SECURE_SSL_REDIRECT` + `TRUST_X_FORWARDED_PROTO` are **a pair** —
enabling the redirect alone gives an infinite redirect loop behind the
TLS-terminating proxy this host sits behind, and trusting the header is
only safe where the proxy overwrites it.

Also pinned with the reasoning inline, so a later tidy-up can't collapse
it: `SESSION_COOKIE_HTTPONLY = True` and `CSRF_COOKIE_HTTPONLY = False`
are deliberately different. The second is **load-bearing** —
`frontend/src/api/client.ts:68` reads `document.cookie` for the token
(checked, not assumed), so making it HttpOnly would break every write.

**Verified, including the red path.** 10 new tests (`config/tests.py`, the
repo's **third** module, Django's built-in runner — no new dependency),
33/33 with the existing suite, and bare `manage.py test` discovers them so
CI needs no workflow change. Then the part that earns them: stashing only
the tracked `settings.py` change while leaving the new tests in place ran
them against the **real pre-fix settings** — all 10 fail. And Django's own
verdict measured both ways: `check --deploy` at `DEBUG=0` reported
**W012 and W016 before, neither after**, with W004/W008/W009 unchanged
(deliberate, deployment-owned — asserted in a test so a green run isn't
misread as "deploy checks are clean"). Local dev confirmed
byte-identical: `DEBUG` unset → both flags `False`, exactly as before.

`manage.py check` and `makemigrations --check` clean — **no migration**,
settings only. **No frontend change, so no `tsc -b`/`vite build` was run
and none is claimed.** Local PostGIS/GDAL + PostgreSQL 16 (usual sandbox
fallback; the two stale PPAs still needed removing first). Every exit code
read from a redirected file, never through a pipe.

**Docs:** `docs/deployment-config.md` (six new variables in the backend
table, plus a "Transport security" section carrying the `not DEBUG`
rationale, the HSTS asymmetry, the redirect/proxy-header pairing, and an
explicit deployment note that a `DEBUG=0` deployment changes behaviour on
upgrade), `docs/open-questions.md` (new D7 bullet under "Tech /
infrastructure"; queue-state records the refill-and-re-empty and the
five-runs-running pattern; App-feedback records the twelfth pull and that
an empty pull needs no further investigation), `build-questions.md` (new
BUILT entry with all ten re-deferral reasons), and this file's tests
bullet — which claimed 23 tests across two modules and now also warns that
`manage.py check` excludes the deploy checks.

**No `docs/manual/` change applies** — nothing user-facing changed, and
`limitations.md` was re-read: it makes no claim about cookies, HTTPS or
transport, so there was nothing to correct. **No screenshots** — nothing
visual changed.

**Still open, deliberately:** B2 and the contextual menu (both anchored
2026-09-03); whether CI should gate the image publish; D5's Q1/Q2; due
dates on tasks; the D6 backfill query; the org switcher; a real cron for
the purge; server-side search/pagination (*not yet*); quick-log draft
persistence; the Node 20 pass. **Plus new, and one-line each for whoever
owns the deployment:** turn on HSTS, and decide the redirect/proxy-header
pair.

### 2026-09-06 (3) — Scheduled PM check-in: host recovered and running the
### D6 fix; an audit pass found nothing — and the queue is now empty of
### anything a build session may take

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Scheduler assigned `claude/hopeful-rubin-fft1nc`, which sat
at `origin/main` (`98e2b42`) while local `main` was 32 behind;
fast-forwarded to `main` per this file's standing rule before reading
anything.

**The outage is over, and the fix built during it is live.** `GET /` and
`/api/auth/csrf/` both 200. Better than a liveness check: the host is
confirmed to be running yesterday's D6 commit — the dev host serves the
frontend through Vite, so `GET /src/utils/images.ts` (a file that did not
exist before `936a30c`) returns the real `ACCEPTED_IMAGE_TYPES` module,
against a control of a long-existing file. **Stated with its limit:** that
proves the *frontend* half. The backend half has no unauthenticated
observable — a legitimate PNG serves identically either side of the fix —
and confirming it would mean uploading to the live instance, deliberately
not done. `GET /api/feedback/pull/` returned `[]` with both negative
controls re-run — the **eleventh** empty pull; yesterday's run couldn't
pull at all, so one *run* is missing from the sequence, not a result.
CI green across Tests #4–#8 and docker-publish #78–#82, and the
paths-filter gating is observably working (docs-only commits finished in
19–25s having built nothing; the D6 commit took 58s and built both).

**The audit pass came back clean — the first check-in in six that didn't
find a defect.** Recorded so it isn't re-derived: the public site's
authored-page paths *are* guarded against a soft-deleted property, and the
load-bearing reason is that `objects = PropertyManager()` is declared
**before** `all_objects` (`models.py:264` vs `:268`), which is what makes
`_default_manager` the filtering one — reverse those two lines and every
public property lookup starts serving deleted properties with nothing else
changing. Also: `apps/notifications` (never audited before) has no
mark-read IDOR; tasks staying account-wide for a property-scoped member
matches `roles-and-permissions.md` exactly; the QR logo picker's
`image/*` is safe because an undecodable image raises `ValueError` into a
400, not a 500; and yesterday's manual edits match `ALLOWED_IMAGE_TYPES`
exactly (re-checked because two earlier runs each found a false claim in
`limitations.md`). One nuance recorded but deliberately not called a
defect: a task's `origin_sighting_species`/`origin_activity_type` reach
through to a property a scoped member can't open — covered by "tasks are
account-wide", but that's where it would leak if scoping ever tightens.

**The finding is the queue state, and it's now a pattern worth acting
on.** Nothing here is buildable without an owner answer. D6 was the last
item carrying no decision, and it shipped — so the well the last four
programmer runs drew from is dry: each of them found the queue empty of
authorized work and **sourced its own additive item** (D3, D4's additive
half, D5's additive half, D6). **A programmer run firing next would
triage the queue correctly and find nothing it may build.** Three
one-line answers would change that: B2 (the logo mark as the "h"), the
contextual menu (unpark or keep parked — its stated precondition has been
satisfied since the day it was parked), and whether CI should gate the
image publish. Also open: D5's Q1/Q2, due dates on tasks, and the D6
backfill query, which still wants someone with database access.

**Docs:** `build-questions.md` (new 2026-09-06 (3) entry — the recovery,
the deployment confirmation, the four clean audit areas, the queue-state
finding, the six questions), `docs/open-questions.md` (App-feedback
records the eleventh pull and the missing run; queue-state records the
clean audit, the five-runs-running pattern, and the host recovery).
**No code, migrations, manual changes, or screenshots** — nothing
user-facing changed, and `limitations.md` was re-read and is accurate.
Push notification sent.

### 2026-09-06 (2) — Scheduled programmer session: built D6 — image
### uploads are an allowlist now, and a stored type can't steer a response
### header. **The dev host was down for the whole session.**

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Local ref already sat at `origin/main`
(`a925c13`); the scheduler assigned `claude/adoring-curie-trzd0c` and this
session moved to `main` per this file's standing rule. Read
`docs/open-questions.md` and `build-questions.md` per the triage rule.
**The owner's "Build next run" authorization is long spent and was not
treated as covering this.**

**Blocker, and the reason for the notification: `habitat.dev.cravenator.com`
was down for this entire session** — every probe from 10:09 to 10:29 UTC
failed, **including across the 15-minute refresh boundaries**, so this was
not a deploy blip. Port 80 returned a genuine `503 upstream connect error
… connection timeout` (an Envoy-shaped edge that is itself up, reporting
its upstream unreachable); port 443 reset the TLS handshake. **Diagnosed,
not assumed:** DNS resolves, this session's general egress is healthy
(`api.github.com` → 200), and the CONNECT-then-reset signature was checked
against a deliberately closed port and produced the *same* signature — so
that half proves nothing and **the 503 is the actual evidence**. Distinct
from the 2026-08-28 egress-policy block, which was a 403 on CONNECT.
**The owner confirmed the cause live, same session: a power outage** —
so not a deploy, image or application fault, and this session's commit is
not implicated. Recorded explicitly because a 503 sitting next to a
same-day backend commit otherwise invites exactly that suspicion. Consequence worth recording: **`GET /api/feedback/pull/`
could not be run** — the first session since the pipeline went live with no
pull at all, empty or otherwise, so the ten-consecutive-empty streak is
neither continued nor broken.

**Built D6, the only queued item needing no owner answer.** The other nine
are re-deferred with stated reasons in `build-questions.md`.

**One allowlist in one place, because the old check was four copies of one
line.** New `apps/accounts/images.py` (png/jpeg/webp/gif); all four upload
endpoints call it. Normalization handles both directions a naive fix gets
wrong: `IMAGE/JPEG` and `image/jpeg; charset=binary` are legitimate and
pass, `image/jpg` resolves to `image/jpeg`, and a trailing parameter
doesn't sneak `image/svg+xml` through.

**The second half is the one worth reading, and it is what makes the
database's contents stop mattering.** All **eight** serving paths now go
through `image_response()`, which serves the allowlisted value and falls
back to `application/octet-stream` otherwise — so a row written *before*
today cannot still steer a response header. Without it the fix would only
protect databases that were already clean. Eight, not the obvious two: the
two authenticated photo views, the two `AllowAny` public twins, and the org
and property header banners on both sides — those last four read as
theming rather than photos, which is how they hide.

**The sub-question was answered, not guessed:** no `Content-Disposition:
attachment` (PM recommendation — the two halves close the hole, and it
would change what "open image in new tab" does for a real photo). **The
backfill check was not run** and that is a genuine gap: no database access
here, and the dev host was down. The serving fix demotes it from
remediation to information; the query is in `open-questions.md` for whoever
has access.

**Verified, including the red path.** 16 new tests
(`apps/accounts/tests.py`, the repo's second module, Django's built-in
runner again — no new dependency), 23/23 with the existing suite. Then the
part that earns them: stashing the tracked view changes while leaving the
new untracked module and tests in place ran the suite against the **real
pre-fix views** — **exactly 4 failures**, and the right ones (upload
refusal, stored-type normalization, and the pre-existing-row serving
assertions on both the anonymous and authenticated paths). The rest pass
both ways deliberately — "still accepts a PNG", "bytes served unchanged"
and the `nosniff` assertion guard against a fix that breaks things rather
than asserting the fix.

**A real bug the tests caught that the diff and `manage.py check` did
not:** the two theme endpoints were edited to call `validate_image_upload`
with no import added — every theme upload would have 500'd on `NameError`.
A runtime name in a view body is invisible to `check`; the integration test
found it instantly. Worth remembering before trusting a clean `check` on a
multi-file edit.

`manage.py check` and `makemigrations --check` clean — **no migration**,
view logic only. `tsc -b` and `vite build` clean. Local PostGIS/GDAL +
PostgreSQL 16 (usual fallback; the two stale PPAs still need removing
first). Every exit code read from a redirected file, never through a pipe.

**Frontend, deliberately small:** `PhotoUploader` and `ThemeEditorPanel`
had `accept="image/*"`, which would now offer a file the server refuses
with an unactionable 400; both use `ACCEPTED_IMAGE_TYPES` from new
`utils/images.ts`, whose comment says the backend is the enforcement.
**`QrCodePanel` left alone on purpose** — its image goes to Pillow and is
never stored or served back, so it isn't a D6 surface.

**Docs:** `docs/open-questions.md` (D6 rewritten found → built; queue-state
records the refill *and* the re-emptying, plus the outage),
`build-questions.md` (new BUILT entry with all nine re-deferral reasons and
the outage), this file's tests bullet (it claimed 7 tests in one module),
and the manual — `limitations.md` gains the accepted-formats bullet, which
the morning's entry explicitly said should be written by the session that
makes it true, plus `activities.md` ("must be an image file" → the four
formats) and `organization-admin.md`'s header-image bullet.
**No screenshots** — nothing visual changed; no `capture.js` selector is
affected (the file inputs it drives are `hidden` and selected by label).

**Still open, deliberately:** B2 and the contextual menu (both anchored to
2026-09-03 — quoting the anchor date, not a tally, per the correction the
morning run made); whether CI should gate the image publish; D5's Q1/Q2;
due dates on tasks; the org switcher; a real cron for the purge;
server-side search/pagination (*not yet*); quick-log draft persistence; the
Node 20 pass.

### 2026-09-06 — Scheduled PM check-in: an uploaded photo can be an SVG,
### and the app serves it back as script on its own origin

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no live
human joined). Started on the scheduler-assigned `claude/funny-euler-3cr3zf`
branch and moved to `main` per this file's standing rule; that branch sat
at `origin/main` (`ec13400`) while local `main` was 29 behind — fast-forwarded
before reading anything. Dev instance healthy (`GET /` and `/api/auth/csrf/`
both 200); `GET /api/feedback/pull/` returned `[]` — **tenth consecutive
empty pull**, with both negative controls re-run this time (tokenless → 403,
wrong token → 403), so the `[]` is a real empty queue.

**D6: every image-upload endpoint accepts `image/svg+xml`, and every
serving path echoes the stored type back.** The validator is one line,
copied four times (`activities/views.py:207`, `sightings/views.py:91`,
`accounts/views.py:426` and `:477`): `startswith("image/")` against
`UploadedFile.content_type` — the **client's** multipart header, not
anything derived from the bytes. No allowlist exists anywhere (`grep svg`
over non-test Python returns nothing). Serving is
`HttpResponse(bytes(photo.image), content_type=photo.content_type)`,
including the two `AllowAny` public-site twins.

**Scope measured, not argued — this one is easy to overclaim.** The app's
own grids render photos only in `<img>`, which does not execute SVG
script. The vector is direct navigation to the photo URL. **`nosniff`
does not help** — Django sets it by default and the live host has it, but
it stops sniffing, not a type declared honestly. Verified in real Chromium
against a listener sending that exact header: script in `<img>` → **0**
beacon hits; same URL navigated directly → **1**. Why it matters: the live
host serves app, API and public site from one origin, and Django's
defaults leave the session cookie sent on a same-origin top-level GET
while `CSRF_COOKIE_HTTPONLY` is unset (so False, JS-readable). Ceiling
stated honestly: planting the file needs an editor-or-above account, so
it's a privilege-escalation primitive, not an unauthenticated hole — and
**nothing was uploaded to the live instance**, deliberately.

**Framed as a build item, not a question** — the D3/D4 call, not D5's.
The fix has no fork: allowlist the raster types on upload (in one shared
place, not four copies), and serve the allowlisted value rather than
echoing a client-controlled string. One narrow sub-question left for the
build session to state rather than guess (`Content-Disposition:
attachment`, and a one-query backfill check); PM recommendation is
allowlist + serve-allowlisted-value, skip the disposition header.

**Also corrected this file's sibling bookkeeping:** the running day-counts
for B2 and the contextual menu had drifted (read "nine days" and "eight"
for items both anchored to 2026-09-03, i.e. three days) because they were
incremented once per check-in run rather than once per day. Future entries
quote the anchor date, not a tally.

**No manual edit applies** — nothing user-facing changed, and
`limitations.md` makes no claim about accepted image formats (re-read to
confirm). The session that lands the allowlist is the one that adds it,
because it will then be true.

**Still open, deliberately:** B2 and the contextual menu (both since
2026-09-03); whether CI should gate the image publish; D5's Q1/Q2;
due dates on tasks; the org switcher; a real cron for the purge;
server-side search/pagination (*not yet*); quick-log draft persistence;
the Node 20 action-deprecation pass.

**Docs:** `build-questions.md` (new 2026-09-06 entry),
`docs/open-questions.md` (new D6 bullet under "Tech / infrastructure";
queue-state records the refill and the tally correction; App-feedback
records the tenth empty pull). **No code, migrations, manual changes, or
screenshots.** Push notification sent.

### 2026-09-05 (4) — Scheduled programmer session: built D5's additive
### half — the images are reproducible and hold no secrets; the
### production-image question stays the owner's

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Local `main` was **27 commits behind**
at start — fast-forwarded before reading anything, since a stale local ref
makes `build-questions.md` read as an older queue than the one that
exists. Dev instance healthy (`GET /` and `/api/auth/csrf/` both 200);
`GET /api/feedback/pull/` returned `[]` — **ninth consecutive empty
pull**, still the steady state. Read `docs/open-questions.md` and
`build-questions.md` per this file's triage rule. **The owner's "Build
next run" authorization is spent and was not treated as covering this.**

**The morning check-in predicted the queue held nothing authorized, and
that was correct.** Every item is blocked on a yes/no, a product call, the
hosting model, or "recommended not yet". Rather than stop there or invent
work, this run took **the one piece of D5 that carries no decision** —
the same reasoning that let D4's additive half ship the day before.

**Built: `npm ci` from the lockfile, and a `.dockerignore` per context.**
`frontend/Dockerfile` copied only `package.json` and ran `npm install`; it
now copies `package-lock.json` too and runs `npm ci`, so the image's
dependency set is reproducible *and* is the set `tests.yml` validates.
Neither build context had a `.dockerignore` at all.

**The drift was measured, not argued — that's the part worth reading.**
Resolving this same `package.json` fresh, on the same machine within the
same hour as `npm ci` against the committed lockfile, produced **37
differently-versioned packages**, `react-router-dom` among them (6.30.4
pinned vs 6.30.6 fresh) — a real runtime dependency, not just build
tooling. Package *counts* matched exactly (157 both ways, nothing added or
missing), which is what made this silent rather than obvious. **One honest
qualifier:** Vite resolved to 5.4.21 both ways, so yesterday's "past the
5.4.15 path-traversal fixes" claim did hold for the image — by luck, not
by construction, which is what pinning removes.

**The backend's `.dockerignore` is about secrets, and the scope is
narrower than it first sounds.** `docker-compose.yml` *requires* a
`backend/.env`, so on any machine following the documented local-dev path
that file exists with a real `SECRET_KEY` and database password, and
`COPY . .` baked it into a layer. **Published images were never
affected** — `.env` is gitignored and Actions builds from a clean
checkout — so this only ever hit locally built images. Still worth
closing: "the image happens not to contain secrets, because CI happens to
check out clean" isn't a property anyone should re-derive. Verified the
exclusion breaks nothing: there is **no dotenv loader anywhere** in
`config/`, `manage.py` or `entrypoint.sh` (`settings.py` reads
`os.environ` only), and `env_file:` is applied by the Docker CLI from the
host at container-create time, not read from the image.

**Verified.** `npm ci` succeeds against the committed lockfile (111
packages) — which also proves the two manifests are in sync, the one way
this change could have broken the build outright, since `npm ci` fails
hard where `npm install` silently reconciles. The lockfile-exact tree
then built the app for real: `tsc -b` and `vite build` both exit 0, and
the image's actual `CMD` (`npm run dev`) came up as Vite 5.4.21 serving
`/` and `/src/main.tsx` at 200. Checked mechanically against
`git ls-files` that **no tracked file is excluded from either context**
(82 frontend, 122 backend, zero), with the intended matches spot-checked
both ways — `node_modules/`, `dist/`, `.env`, `.env.local`, `*.pyc`,
`.venv/` excluded; `package-lock.json`, `src/main.tsx`, `entrypoint.sh`,
`requirements.txt` and `.env.example` (via the `!` negation) kept.
No `docker build` could be run *locally* — no Docker daemon here and the
registry blob host is blocked, the same limitation the 2026-08-14 and
2026-08-26 sessions documented — so every step the Dockerfile performs was
exercised directly instead. **CI then supplied the missing piece: both
images built and pushed on this commit** (docker-publish run #78, frontend
and backend jobs both green), and because the `COPY` line itself changed,
the layer cache for `RUN npm ci` was necessarily invalidated — so `npm ci`
ran fresh inside a real image build and succeeded. Tests run #4 is green
too. **No backend Python changed**, so no PostGIS stack was stood up and
none is claimed.

**Deliberately NOT built: D5's actual question.** No production image,
`docker-publish.yml` untouched, and the live host still runs `runserver`
and Vite's dev server. Q1 (is that host meant to be production-shaped?)
and Q2 (nginx vs `vite preview`, gunicorn vs uvicorn, workers,
`collectstatic`/whitenoise, whether the dev images stay for local
`docker-compose`?) are all downstream of the undecided hosting model, and
a build session answering them alone is what this file's boldness
carve-out forbids. `frontend/Dockerfile`'s header says so and points at
the open question.

**Docs:** `docs/deployment-config.md` (new "Building the images" section —
the natural home for "no `.env` is baked in, so every value in the tables
above must reach the *running* container"), `docs/open-questions.md`,
`build-questions.md` (new BUILT entry with the nine re-deferral reasons),
and this log. **No `docs/manual/` change applies** — nothing user-facing
changed; re-read `limitations.md` to confirm it makes no claim about
images or deployment, and it doesn't. **No migration and no screenshots.**

**Still open, deliberately:** B2 (**nine days**); the contextual menu
(eight); whether CI should gate the image publish; D5's Q1/Q2; due dates
on tasks; the org switcher; a real cron for the purge; server-side
search/pagination (*not yet*); quick-log draft persistence; the Node 20
action-deprecation pass.

### 2026-09-05 (2) — Scheduled programmer session: built D4's additive half
### — the repo's tests now actually run in CI; the publish gate stays the
### owner's call

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Local HEAD already equalled
`origin/main` (`d40e714`) — no fast-forward needed, unlike the last three
runs. Dev instance healthy (`GET /` and `/api/auth/csrf/` both 200);
`GET /api/feedback/pull/` returned `[]` — **seventh consecutive empty
pull**, still the steady state. Read `docs/open-questions.md` and
`build-questions.md` per this file's triage rule. **The owner's "Build next
run" authorization is spent and was not treated as covering this.**

**Built D4, the only queued item that didn't need an owner answer.** The
other seven are re-deferred with stated reasons in `build-questions.md`.

**`.github/workflows/tests.yml`** — two jobs, on push to `main`, **every
pull request**, and manual dispatch. Backend: a `postgis/postgis:16-3.4`
service container (GeoDjango can't be exercised against plain PostgreSQL
or SQLite), apt-installed GDAL/GEOS/PROJ on the runner, Python **3.12 to
match `backend/Dockerfile`'s base**, then `manage.py check`,
`makemigrations --check --dry-run`, `manage.py test`. Frontend: `npm ci`,
then `tsc -b` and `vite build` as **separate steps** so a red run says
which half failed. **No secrets and no hosting decision** — which is
exactly why this was buildable without asking, where the purge cron
(mechanism (i)) was not.

**The part worth reading: every guard was verified to fail, not just to
pass.** A suite whose red path nobody has seen is the same class of
problem as a suite nobody runs. Stripping the four
`property__deleted_at__isnull=True` guards from `public_site/views.py`
produces **exactly 5 failures**, matching yesterday's measurement — so
this workflow would genuinely have caught D3, which is the whole claim
being made for it. An unmigrated model change **exits 1** from
`makemigrations --check` and writes **no stray migration file**. A type
error **exits 1** from `tsc -b` rather than being skipped by its
incremental cache. Clean tree: 7/7 tests, both checks exit 0, `npm ci`/
`tsc -b`/`vite build` clean; every probe edit restored and `git status`
confirmed clean before committing. `postgis/postgis:16-3.4` was confirmed
to exist on Docker Hub rather than assumed — a bad tag would fail every
run.

**A measurement error worth not repeating:** the first pass at the
migration check read `exit=$?` after a pipe to `tail`, which reports
`tail`'s status, not Python's — it printed `exit=0` for a case that
actually fails. Re-measured by redirecting to a file. Don't read an exit
code through a pipeline.

**Deliberately NOT built: the publish gate.** `docker-publish.yml` is
untouched. Whether `build-and-push` should `needs:` this is the
sub-question the morning's PM run carved out for the owner, and it got the
same treatment five prior runs gave B2. PM recommendation stands (**gate
it** — publishing an image from a commit known to be broken is worse than
publishing nothing, and `latest` is what a deployment pulls), but the
owner has tuned that workflow twice and its publish behaviour shouldn't
change under them without a yes. `tests.yml` carries a header comment
saying so and naming how to wire the gate.

**Docs:** `docs/open-questions.md` (D4 rewritten from found to
additive-half-built, gating kept explicitly open; queue-state section
records the queue is empty of authorized work again),
`build-questions.md` (new BUILT entry with the seven re-deferral reasons),
this file's tests bullet, and manual `limitations.md` — **that last one
corrects a claim this session first wrongly called accurate.** Its testing
bullet said there were no automated frontend checks and described backend
testing as merely "`manage.py test`-shaped", which now *understates* what
runs; rewritten to say what actually executes and that it's a thin floor
(7 tests, one module, no frontend test runner) rather than a safety net,
so "it's in CI" doesn't get read as "it's covered". **No migration**
(no model change) and **no screenshots** — nothing visual changed, no
`capture.js` selector affected.

**Still open, deliberately:** B2 (**seven days**); the contextual menu
(six); **whether CI should gate the image publish** (new, a one-line
yes/no); server-side search/pagination (*not yet*); due dates on tasks;
the org switcher; a real cron for the purge; quick-log draft persistence.

### 2026-09-04 (4) — Scheduled programmer session: fixed D3 — deleting a
### property now actually retracts its published photos; repo gets its
### first backend tests

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Local `main` was **22 commits behind**
at start — fast-forwarded before reading anything, since a stale local ref
makes `build-questions.md` read as an older queue than the one that
exists. Dev instance healthy (`GET /` and `/api/auth/csrf/` both 200);
`GET /api/feedback/pull/` returned `[]` — **fifth consecutive empty pull**,
still the steady state. Read `docs/open-questions.md` and
`build-questions.md` per this file's triage rule. **The owner's "Build next
run" authorization is spent and was not treated as covering this.**

**Built D3, the only queued item that didn't need an owner answer.** The
other six are re-deferred with stated reasons in `build-questions.md`, not
silently skipped — B2 is now **five days** unanswered and the contextual
menu four; both still need a yes/no from the owner, and a build session
supplying its own is exactly what that carve-out prevents.

**The fix is four filters, not the two the check-in identified.** Both
record helpers (`_public_activity_or_404`, `_public_sighting_or_404`) and
**both link helpers** now carry `property__deleted_at__isnull=True`. The
link helpers are the part worth reading: they gate on
`sighting__property__is_public` / `activity__property__is_public` — the
same join semantics — and **a Sighting↔Activity link is not constrained to
one property** (nothing in `SightingActivityLinkSerializer` enforces it,
and it even serves `activity_property_name`). So a *live* property's
activity could keep naming a deleted property's sighting id in its public
link list. Confirmed against pre-fix code, which returns that id where the
fixed code returns `[]`. No migration — query-filter logic only.

**Also corrected the docs that stated the wrong invariant**, since they're
part of why this survived three weeks rather than incidental to it: the
module docstring said everything in `public_site` is scoped to
`is_public=True` (one condition where there are two), and
`data-model-notes.md` claimed soft delete hid a property from "the app, the
public site, everywhere" — flatly false for the public site. Both now state
two conditions and name the join-vs-manager trap outright.

**The repo now has backend tests — `apps/public_site/tests.py`, 7 of
them.** There were none anywhere before. Added rather than deferred because
this invariant already regressed silently once and nothing would catch a
recurrence. Django's built-in runner, so **no new dependency and no
undecided convention** (this file already names `manage.py test`; pytest
stays "if/when adopted"). They're a real guard, not a restatement: **5
failures against the pre-fix code, 7/7 after**, checked both ways by
stashing the fix. One test deliberately pins the *Django semantic* (a
join-only filter still matches a soft-deleted property) so a future Django
change explains itself rather than just going red.

**Checked and deliberately left:** `PageViewSet`'s
retrieve/update/destroy don't filter `property__deleted_at`, so a page on a
deleted property stays reachable by direct URL — but only to an
authenticated org member who could restore the property anyway, the `list`
path *is* guarded, and nothing links to it. Recorded in
`build-questions.md` so it isn't re-derived.

**Verified for real.** Local PostGIS/GDAL + PostgreSQL 16 (usual sandbox
fallback; two stale PPAs still need removing first). `manage.py check`
clean, `makemigrations --check` reports no changes. Plus a 30-assertion
script driving the real HTTP endpoints through publish → soft-delete →
restore → mark-private, confirming a live property's photos keep serving
throughout and that restore needs no re-publishing by hand. **No frontend
change**, so no `tsc -b`/`vite build` was needed and none is claimed.

**Docs:** `docs/open-questions.md` (D3 rewritten from found to built, with
the wider scope; new queue-state paragraph recording that the queue is
again empty of authorized work), `docs/data-model-notes.md` (the false
"everywhere" corrected), `build-questions.md` (new BUILT entry with the six
re-deferral reasons), manual `properties.md` (deletion now says explicitly
that it retracts the public page and photos, and that restore brings them
back) and `public-site.md` (its "two flags" section — the natural place
this gap hid — now names deletion as the third, absolute condition).
**Screenshots not regenerated** — nothing visual changed, no `capture.js`
selector affected.

**Still open, deliberately:** B2 (five days); the contextual menu (four);
server-side search/pagination (*not yet*); due dates on tasks; the org
switcher; a real cron for the purge; quick-log draft persistence.

### 2026-09-04 (3) — Scheduled PM check-in: deleting a property doesn't
### retract its published photos — the public site never got the
### soft-delete pass the rest of the app did

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no
live human joined). Started on the scheduler-assigned `claude/...` branch
and moved to `main` per this file's standing rule and the run's own "ONLY
USE THE MAIN BRANCH" instruction; `origin/main` == HEAD == `85e7bdb`.
Dev instance reachable (`GET /` and `/api/auth/csrf/` both 200);
`GET /api/feedback/pull/` returned `[]` — fourth consecutive empty pull,
still the steady state.

**One finding, and it's the most consequential these check-ins have
produced.** Same move as the last three runs — check a promise against
the code — starting from yesterday's purge build and working outward.

**D3: a deleted property's photos are still served to anonymous
visitors.** `apps/public_site/views.py` has **no `deleted_at` guard
anywhere**, while `ActivityViewSet`, `SightingViewSet` *and* their
function-based `_get_activity_in_scope`/`_get_sighting_in_scope` helpers
all carry one. The two public helpers gate on `is_public=True,
property__is_public=True` — and a related-field filter is a plain SQL
join that does **not** apply `Property.objects`' soft-delete filter,
while a soft-deleted property still has `is_public=True`. So the public
page 404s and the portfolio omits it, but
`/api/public/activities/<id>/photos/(<id>/image/)` and the two sighting
equivalents keep serving.

**The inversion is the clearest way to hold it:** flipping a property
*private* does cut those photos off; deleting it does not — the stronger
action retracts less. Scope stated precisely so it isn't over-read: only
already-public records on an already-public property, so this is a
failure to **retract published data**, not exposure of anything private.
The window is now ~30 days thanks to yesterday's purge fix; before it,
indefinite — the two defects compounded and only one is closed.

**Verified empirically, not reasoned about**, since the whole finding
rests on one Django semantic: reproduced `Property`'s exact manager shape
plus an `Activity` FK on plain non-GIS models in a throwaway Django 5.2 +
SQLite project and ran both lookups verbatim — the property lookup 404s,
**the activity lookup returns the row**, and adding
`property__deleted_at__isnull=True` excludes it while leaving a live
property's activity reachable.

**Deliberately framed as a build item, not a question.** Unlike Q1/Q2 it
needs no owner answer: the fix mirrors a guard this repo already applies
in four places, and a restored property's photos come back on their own
since `deleted_at` is simply cleared. It went to the owner as a heads-up
about a live gap, with the note that a build session should take it
without asking.

**Cause, worth not re-deriving:** soft delete (2026-08-29) covered the
authenticated app carefully — including the function-based photo views,
the exact analogue of the two that leak. `apps/public_site/` (built
2026-08-14, two weeks earlier) was simply never opened.

**Also checked so the next session doesn't redo it:** yesterday's purge
build is sound end to end (no overridden `Property.delete()`, so the hard
delete is real; per-property `atomic()` and the materialised loop are
correct; `entrypoint.sh` sweeps after `migrate` and outside `set -e`) —
D3 is adjacent to that work, not in it.

**No manual edit, deliberately.** Nothing in `docs/manual/` is wrong
today — `properties.md` and the delete dialog both say deletion "hides
its activities and sightings" and neither mentions the public site.
Building D3 makes the natural reading true; documenting the gap instead
would be the wrong fix. Recorded that reasoning in `build-questions.md`
rather than acting on it, per this session's scope.

**Still open, deliberately:** B2 (the logo mark as the "h") — **four
days** unanswered, untouched; the contextual menu (unpark?) — three days;
server-side search/pagination (recommendation still *not yet*); due dates
on tasks (a product call); the org switcher; a real cron for the purge;
quick-log draft persistence.

**Docs:** `build-questions.md` (new 2026-09-04 (3) entry — D3, Q1-Q3, the
refreshed menu), `docs/open-questions.md` (new "Tech / infrastructure"
bullet for D3; queue-state and App-feedback sections updated). **No code,
migrations, manual changes, or screenshots.** Push notification sent.

### 2026-09-04 (2) — Scheduled programmer session: fixed both defects the
### morning's check-in found — the promised deletion now happens, and
### "your first membership" is finally deterministic

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Dev instance healthy (`GET /` and
`/api/auth/csrf/` both 200); `GET /api/feedback/pull/` returned `[]` —
third consecutive empty pull, still the expected steady state. Read
`docs/open-questions.md` and `build-questions.md` per this file's triage
rule. **The owner's "Build next run" authorization is spent and was not
treated as covering this** — this session's own trigger is what scoped it.

Built **D1 and D2**, the only two queued items that didn't need an owner
answer. The other four are re-deferred with reasons in
`build-questions.md`, not silently skipped.

**1. The 30-day purge is now actually performed.** The manual told users
a deleted property is removed for good after 30 days and *nothing in the
repo ever ran the command that would do it* — the gap was recorded only
in that command's own docstring. New `apps/accounts/purging.py` holds the
logic (the management command is now a thin wrapper over it and still
works, still idempotent), called from **two** places, neither needing a
hosting decision: `backend/entrypoint.sh` on every backend start
(whole-database sweep, deliberately outside `set -e`'s reach — a purge
that fails is a problem to fix, not a reason to stop the app booting),
and `PropertyViewSet.deleted`/`.restore` lazily, bounded to the caller's
own organization.

**The lazy call does more than run the sweep, which is the part worth
reading: both endpoints were quietly lying.** `deleted`'s own docstring
claimed it listed properties "still inside their 30-day restore window"
and it did no such filtering; `restore` would happily resurrect a
property 60 days dead. Sweeping first makes both true by construction
rather than by adding a second window check that could drift from the
purge's own rule.

**Two decisions recorded rather than assumed:** the lazy sweep is
**org-wide, not filtered to a property-scoped admin's own properties**
even though the list it precedes *is* scope-filtered — expiry is a
retention window the app already committed to, not a discretionary
action, and scoping it would make the day a property actually dies depend
on who happened to log in. And **mechanism (i), a scheduled GitHub
Actions workflow, was considered and deliberately not built**: it needs a
target URL and a bearer-token secret provisioned in the repository,
neither of which a session can do, and would fail loudly on every
scheduled run until they were — trading a silent gap for a noisy one. A
real cron is still worth adding if a deployment wants a specific hour;
nothing built here is in its way.

**2. `Membership.Meta.ordering = ["created_at", "id"]`** (migration
`accounts/0013_alter_membership_options`, `AlterModelOptions`, no table
rewrite). An unordered `.first()` in `org_scoping.get_active_membership`
meant a two-org user's active organization — and every scoped queryset in
the app, which all derive from that one call — could change between
requests after any membership row update. **No manual edit was needed and
that's the point:** `limitations.md` and `getting-started.md` already
told users the app uses their first/oldest membership; the fix makes the
code match the docs rather than the other way round. **The org switcher
is explicitly not built** — left open in `open-questions.md`, since it
touches that same function and is a feature, not a follow-up.

**Found while building, and worth not re-deriving:** `Sighting` has to be
imported *inside* `purge_due_properties`, not at module scope —
`apps.sightings` imports from `apps.accounts`, so a top-level import is
circular. Each property's purge is its own `transaction.atomic()`, so a
sweep failing part-way can't leave a property whose sightings are gone
but which is itself still sitting in the restore list.

**Verified for real.** Local PostGIS/GDAL + PostgreSQL 16 (usual sandbox
fallback; the two stale PPAs still need removing first).

**Docs:** `docs/open-questions.md` (both bullets rewritten from
needs-a-decision to built, with the org switcher and the real-cron option
kept explicitly open), `docs/data-model-notes.md` (soft-delete purge
performers; new "Which membership is active" bullet under Permissions),
`build-questions.md` (new BUILT entry with the re-deferral reasons),
manual `properties.md` and `organization-admin.md` (both now say when the
sweep actually happens, and that an expired property can't be listed or
restored). `limitations.md` needed no change — re-read, still accurate.
**Screenshots not regenerated** — nothing visual changed; no `capture.js`
selector is affected.

**Still open, deliberately:** B2 (the logo mark as the "h") — third day
unanswered, untouched; the contextual menu (unpark?) — second day;
server-side search/pagination; due dates on tasks (a product call, not a
gap); quick-log draft persistence; the org switcher; a real scheduled
cron for the purge.

### 2026-09-04 — Scheduled PM check-in: two verified defects nobody had
### raised, both found by checking a doc claim against the code

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no
live human joined). `origin/main` == HEAD == `9829401`. Dev instance
reachable (`GET /` and `/api/auth/csrf/` both 200);
`GET /api/feedback/pull/` returned **`[]`** — second consecutive empty
pull, the expected steady state, endpoint still authenticating.

**The finding is two defects, not a queue state.** Both came from the
same move that produced the last two runs' findings — take a sentence the
docs assert and go check it in the code:

- **D1: the app promises a 30-day deletion nothing performs.**
  `docs/manual/properties.md` tells users a deleted property is removed
  for good after 30 days. Nothing runs `purge_deleted_properties` —
  verified, not assumed: the only workflow in the repo is
  `docker-publish.yml`, and neither `entrypoint.sh` nor
  `docker-compose.yml` schedules anything. The gap is recorded honestly
  in the command's own docstring **and nowhere else** — not in
  `open-questions.md`, not in `limitations.md`, never put to the owner.
  So soft-deleted properties are retained indefinitely, and a user
  deleting a property to be rid of its data isn't. Nothing hits day 30
  before **2026-09-28**, which is the window. Also established that it's
  **less blocked on the undecided hosting model than the docstring
  assumes**: a lazy purge on the "Recently deleted" read needs no
  infrastructure at all, and a scheduled Actions workflow needs no
  hosting decision — only a real cron is genuinely blocked.
- **D2: which org a multi-org user is in isn't deterministic.**
  `org_scoping.py:22` uses an unordered `.first()` and
  `Membership.Meta` has constraints but no `ordering`, so the active org
  can change between requests when any membership row is updated — and
  every scoped queryset in the app derives from that one call.
  `limitations.md`'s "always acts as your first membership" is the intent,
  not a guarantee. Reachable via a supported flow, since
  `MembershipViewSet.create` deliberately attaches an existing user to a
  second org. Split into a one-line floor (`ordering`, an
  `AlterModelOptions` migration) and the separate org-switcher feature.

**Q1 (B2, the logo mark as the "h") is now two days unanswered** and
still the only unbuilt piece of that six-item feedback batch; **Q2 (unpark
the contextual menu?) one day**. Both re-raised compactly rather than
re-argued.

**Q3 — the candidate menu was rebuilt**, since three of its four items
shipped. D1 and D2 are the two best-defined entries on it. Server-side
search/pagination is carried over but **shaped into a yes/no** (stock DRF
`SearchFilter` + `PageNumberPagination`, page size 50, client-side
filters kept as in-page refinement), recommendation still *not yet*. One
new item needing a product call: **due dates on tasks**.

**Two things checked so the next session doesn't re-derive them:**
`limitations.md` is accurate as of today (re-read end to end after two
consecutive runs each found a false claim in it — the two defects above
are absences from it, not errors in it), and **GIS export is Phase 4**
(`roadmap.md:120`), so a thin queue is not a reason to pick it up.

**Docs:** `build-questions.md` (new 2026-09-04 entry — D1, D2, Q1-Q3, the
refreshed menu), `docs/open-questions.md` (new bullets under "Tech /
infrastructure" and "Accounts, orgs, and permissions"; the queue-state
and App-feedback sections updated). No `docs/manual/` update applies —
nothing user-facing changed, and D1's manual consequence is deliberately
queued rather than edited, per this session's scope. **No code,
migrations, or screenshots.** Push notification sent.

### 2026-09-03 (4) — Scheduled programmer session: built three of the
### four queued candidates, plus two defects found by looking at a screenshot

Scheduled "programmer" session (its own trigger scopes it to implementing
and committing directly to `main`). Local `main` was **18 commits
behind** at start — fast-forwarded before reading anything, since a stale
local ref makes `build-questions.md` read as an older version of the
queue than the one that actually exists. Dev instance reachable (`GET /`
and `/api/auth/csrf/` both 200); `GET /api/feedback/pull/` returned
`[]`, so no new user feedback this run.

Read `docs/open-questions.md` and `build-questions.md` per this file's
triage rule. **The owner's "Build next run" authorization is spent and
was not treated as covering this** — the queue's four Q3 candidates were
a menu, not an authorization. This session's own trigger is what scoped
it, per the "not every scheduled session is queue-only" convention.
Built three of the four, and re-deferred the fourth with a reason.

**1. Workflow-state editor.** `WorkflowStateViewSet` stopped being
`ReadOnlyModelViewSet` — now an `OrganizationScopedViewSet`, a deliberate
near-copy of `ActivityTypeViewSet` 14 lines below it (that model was
copied *from* `WorkflowState` last week, so this closes the loop). New
`/manage/workflow-states`, same wrapper and same `sections.ts#canAccess`
gate as Activity types.

**The flagged sub-question was the actual work, and the answer is
asymmetric — which is the part worth reading.** The queue warned not to
guess at the `is_planned`/`is_done` guard. Tracing every reader settled
it: **`is_done` is guarded** on un-flagging *and* deletion, because it is
the only signal anything downstream has for "finished"
(`ActivitySerializer.is_done` drives the public map's two layers, the
dashboard's Recent/Upcoming split, the Activities status filter), so an
org with none silently shows every activity as unfinished forever with
nothing explaining why. **`is_planned` is deliberately not guarded** —
both readers (`ActivityFormPage`, `QuickLogPage`) already fall back to
the first state, so losing it degrades a default rather than breaking a
display. Guarding both symmetrically would have looked tidier and been
wrong. Also added while there: a state can't carry both flags (they're
the two ends of a workflow), the last state can't be deleted at all
(`Activity.status` is required), and a state in use 400s naming how many
activities are in it rather than 500ing from `ProtectedError`.

**2. Activity-type reordering.** Exactly as small as the queue predicted
— `order` was already writable, so frontend-only, no migration. Shared
with the new editor via `pages/manage/reorder.ts`. **Non-obvious bit:** a
move rewrites every changed row's `order` rather than swapping the moved
pair's two values, because nothing guarantees the stored numbers are
distinct (the Add form takes `list.length`, so delete-then-add produces
duplicates) and swapping two equal values is a no-op that reads as a
broken button. Normalizing to array indices makes the list self-healing.

**3. Photos on the regular create forms.** Rather than copying quick
log's step into two more files, extracted it to
`components/PostSavePhotoStep.tsx` and pointed **all three** create flows
at it, quick log included — one copy instead of three that drift. That's
a refactor of a flow shipped the day before, so it was driven end to end
in a browser rather than trusted to typecheck.

**4. Server-side search/pagination — re-deferred, not skipped.** It's a
real design call (which endpoints gain query params, page size, whether
the client-side filters stay as a fallback), not a mechanical change, and
nothing is hurting at today's volumes. Left in `open-questions.md`.

**5. The manual bug the last check-in recorded — fixed.**
`limitations.md` no longer says the "forgot password" flow doesn't exist.
Per that entry's own warning the adjacent true claim was kept and made
explicit: the flow exists but has no SMTP, and deliberately has no
admin-UI link fallback, since returning the link would let the endpoint
be used to check who has an account.

**Two real defects found outside the original scope — both by *looking at
a screenshot*, with all 26 assertions green:**

- **Every DRF field-level validation error in the app rendered as raw
  JSON.** `handleResponse` unpacked `{"detail": ...}` and fell back to
  `JSON.stringify(body)` for everything else, so the new guard's refusal
  reached the user as `{"is_done":["This is your only state..."]}`.
  Pre-existing — the activity-type duplicate-name error had it too — and
  fixed once in the client (`errorMessage`), which fixes every form.
- **A name field was painting over the reorder arrows.** An `<input>`
  keeps its intrinsic width however far its flex parent shrinks, so it
  overflowed and covered the ▲ on the inline-rename rows. Latent while
  those rows had one action; visible the moment there were three.

Same lesson as 2026-09-02 (7), recorded again because it keeps being what
catches real defects: the assertions all passed while the screen was
visibly wrong.

**Verified for real.** Local PostGIS/GDAL + PostgreSQL 16 (usual sandbox
fallback). `manage.py check` and `makemigrations --check` clean — **no
migration; permission/validation logic and frontend only**. 36 API checks
(seeded workflow, create/rename/case-insensitive duplicate rejection,
both-flags rejection, the un-flag guard from both sides, all three delete
guards and their exact messages, guard *ordering*, cross-org isolation in
four verbs, anonymous refusal) plus 8 role checks (viewer reads only,
editor writes but can't delete, admin deletes). `tsc -b` and `vite build`
clean. 31 Playwright checks in real Chromium at a phone viewport:
reordering including persistence across a reload and both end-arrows
disabled, the guard refusing in the UI with the checkbox staying checked,
add/rename/delete, activity-type reorder, the photo step on both create
forms with an upload verified server-side, Skip, editing still navigating
away, and quick log driven all the way through the shared step. No
console errors beyond the documented basemap-tile noise.

**Worth knowing:** the first API run's two failures were both the
*test's* assumptions, not the app's behavior — the guards make "an org
with only a not-done state" unreachable, and the in-use check runs before
the last-state one. Read a red assertion against the guards before
reading it as a bug.

**Docs:** `data-model-notes.md` (Status workflow rewritten as
decided-and-built, with the asymmetry explained),
`docs/open-questions.md` (queue-state section updated; four items into
"Recently resolved"), `build-questions.md` (new BUILT entry),
manual `organization-admin.md` (new "Workflow states" section, plus
activity-type ordering), `activities.md` (its status-workflow section
had claimed this needed Django admin; new photo-step text),
`sightings.md`, `limitations.md` (password-reset correction, and three
now-false bullets replaced by the one real remaining guard).
**`capture.js` needed a real fix, not just a re-run** — it waits for a
return to the property after saving, which the new photo step interrupts,
so it would have hung; `skipPhotoStep()` added at both call sites.
**Screenshots not regenerated** — already done once today, so the
once-per-calendar-date cap applies; `manage.png` picks up the new entry
at the next regen, and its alt text was left describing what the current
image actually shows.

**Still open, deliberately:** B2 (the logo mark as the "h") — never
answered by the owner, so untouched; the contextual menu, parked, though
its stated unparking precondition has now been met; server-side
search/pagination; quick-log draft persistence; and the public-site
relocation's remaining ops steps.

### 2026-09-03 (3) — Scheduled PM check-in: the queue is empty of
### authorized work; one unanswered question, one expired parking reason

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, don't trigger the next build — no
live human joined). Local `main` was 17 commits behind at start;
fast-forwarded, then `origin/main` == HEAD == `b4aeb02`. Dev instance
reachable (`GET /` and `/api/auth/csrf/` both 200).
`GET /api/feedback/pull/` returned **`[]`** — the first empty pull since
the pipeline started producing real user content on 2026-09-02, and the
expected steady state rather than a fault (both prior batches were
triaged, built and marked synced; the endpoint still authenticates).

**The finding is a queue state, not a feature request.** The owner's
*"Build next run"* authorization was taken up in full by the same day's
programmer run and is **spent** — all six items shipped. Nothing else in
`build-questions.md` is authorized, so a programmer run firing next would
triage the queue correctly and find **nothing it may build**. That's what
went to the owner, alongside two real questions.

**Q1 — B2 is still unanswered** (the logo mark becoming the "h" in
"habitat"). It was carved out of the authorization precisely because it
had no answer, and the programmer run respected that exactly, so it is
now the only unbuilt piece of that six-item batch. Noted the cost of the
delay: it was meant to ship *with* the auth-screen logo fix, which
shipped without it, so building it now means a second pass over the same
five screens.

**Q2 — the contextual menu's parking reason has expired.** It was parked
2026-09-03 with a specific revisit condition recorded ("until
Activities/Sightings exist org-wide there's no global list for a
contextual menu to contrast with") — and both pages shipped that same
day. So the condition is already true; re-raised as "unpark, or keep
parked?" rather than left sitting on a satisfied precondition. Keeping it
parked is a fine answer.

**Q3 — four candidates for the next run, each verified against the code
this run rather than relayed from this log.** Two came back different
from what the docs claim:

- **A workflow-state editor is the best-defined item in the repo right
  now.** `WorkflowStateViewSet` is still `ReadOnlyModelViewSet` and its
  own docstring says the editing UI "doesn't exist yet," while
  `ActivityTypeViewSet` — built last week as a deliberate near-copy of
  `WorkflowState` — sits **14 lines below it in the same file**,
  writable, explicitly contrasting itself with it. So the shape is
  already decided and already shipped once, and `/manage`'s new
  section-page pattern gives it a home. Flagged the one sub-question not
  to guess at: `is_planned`/`is_done` drive the public map's styling, so
  an editor needs a guard against an org deleting or un-flagging its last
  `is_done` state.
- **Activity-type reordering is smaller than `limitations.md` says.**
  That page claims reordering "needs the database directly," but `order`
  is already in `ActivityTypeSerializer.Meta.fields` — writable through
  the API today. Frontend affordance only; no backend, no migration.
- Photos on the regular create forms (quick log set the precedent;
  `PhotoUploader` already does camera capture, so it's a flow change).
- Server-side search/pagination for the two new org-wide lists.

**A verified doc bug, recorded not fixed:**
`docs/manual/limitations.md` still tells users *"No password reset
('forgot password') flow either"* — but that flow shipped 2026-08-27,
confirmed against the code this run rather than this log
(`ForgotPasswordPage.tsx`, `ResetPasswordPage.tsx`,
`backend/apps/accounts/urls.py:19-20`). The 2026-08-27 session updated
`account.md` and `open-questions.md` and left this line behind. The
*adjacent* claim is accurate and shouldn't be lost in the fix: no SMTP,
so the link is only reachable via server console output, and this flow
deliberately has no admin-UI fallback (returning the link would let the
endpoint be used to check who has an account). Left unfixed per this
session's scope and queued so the next build session triages it — a
manual that says a shipped feature is missing is worse than a stale
screenshot.

**Docs:** `build-questions.md` (new 2026-09-03 (2) entry — the empty-queue
state, Q1-Q3, the four verified candidates, the doc bug),
`docs/open-questions.md` (new "Build queue state" section; the B2 and
contextual-menu bullets updated; the empty pull recorded under "App
feedback"). No `docs/manual/` update applies — nothing user-facing
changed, and the one manual fix found is deliberately queued rather than
made. **No code, migrations, or screenshots.** Push notification sent.

### 2026-09-03 (2) — Scheduled programmer session: built all six
### authorized items — the app's Phase 1 information architecture, replaced

Scheduled "programmer" session (explicit build authorization in its own
trigger). `main` verified current, then fast-forwarded — the local ref was
15 commits behind `origin/main` at start, worth knowing since a stale
local `main` makes `build-questions.md` read as a version older than the
one the owner actually authorized. Dev instance reachable (`GET /` and
`/api/auth/csrf/` both 200); `GET /api/feedback/pull/` returned `[]`, so
no new user feedback this run. Read `docs/open-questions.md` and
`build-questions.md` per this file's triage rule: the queue opened with
an authorization banner covering **six** items (owner, live, 2026-09-03:
*"Build next run"* — naming the next run, which is this one). **Built all
six**, in the recommended order, rather than stopping at one.

**Both stated exclusions respected.** The contextual menu is untouched and
not half-built toward — the nav stays flat. **B2 (the logo mark becoming
the "h" in "habitat") was never answered by the owner and was not built**:
the wordmark renders exactly as before.

**1. The five unauthenticated screens now show the real logo** (A1).
`Logo` gained a `size="lg"` variant, needed because `.logo__mark` is
hard-coded to nav size while these screens use the brand as their own
`<h1>`. So the first screen a new user sees is no longer the stale
placeholder.

**2. The dashboard stops double-counting** (A2). "Recent activities" now
filters to the exact complement of what the Planned section shows
(`!isUpcoming`), so the two sections can't both claim a record — chosen
over inventing a second rule that could drift from the first. Limit is 3;
a separate `TODO_LIMIT` holds "Your tasks" and "Planned / upcoming" at 5,
since the feedback was about the Recent sections specifically.

**3. Manage: the 1061-line admin page is gone** (A3 + B1b, built together
as the queue advised). `pages/manage/` now holds a verbatim-extracted
row/form module, seven section pages, a shared `ManageSectionPage`
wrapper, and `sections.ts`. `/admin` → `/manage`, member-visible, with
Properties/Species/Public site moved under it and every admin-only surface
gated per section inside.

**The flagged trap was real and is the part worth reading.** The queue
warned this change *moves a gate*, so the risk is exposure rather than
layout. Two consequences: (a) **the gate lives in exactly one place** —
`sections.ts#canAccess` is consulted by the menu *and* by each sub-page's
own guard, because every section now has its own linkable URL where the
old page had none, and "hidden from the menu but reachable by URL" is
precisely the failure a per-section hand-written check invites; (b) it was
**verified against four memberships, not one** — an account-wide viewer,
an account-wide editor, a property-scoped viewer, and a property-scoped
admin. For the three non-admins all six admin-only surfaces are absent
*and* all seven sub-routes refuse when typed directly. The scoped admin is
where the two filters compose: it keeps Members and Recently deleted,
loses the four org-level sections, and `/manage/theme` refuses it while
`/manage/members` opens.

**4. Two new org-wide pages** (B1a): `/activities` and `/sightings`, each
searchable, each row linking to the existing per-property edit form (the
owner asked for "found **and** edited"). Client-side filtering over the
list endpoints `DashboardPage` already calls — no new API surface, the
same tradeoff `SpeciesPage` takes. Property scoping needs nothing new: the
backend already filters those endpoints.

**5. Quick log offers photos after saving** (A4), with Skip.
`PhotoUploader` already did camera capture, so this was a flow step, not
new capability. It's the first place in the app where a photo can be
attached without a separate trip to an edit form — the regular create
forms still can't, now recorded in `limitations.md` as the gap this sets a
precedent for.

**Decisions made while building, recorded rather than assumed:**

- **`/admin` → `/manage` with redirects** — the queue left this a
  build-session call. Renamed, since "Admin" is a misnomer for a
  member-visible section, and the bookmark cost was avoidable:
  `/admin/pages/:pageId/edit` carries its page id across rather than
  dumping the visitor on the index.
- **An a11y fix inside A1's blast radius, deliberately not B2.** The mark
  in an `<h1>` next to the literal word "habitat" made a screen reader
  announce "Habitat habitat" — the mark is now `alt=""` and the wordmark
  carries the name. Same trap B2's write-up flagged, handled only for the
  case A1 created; the visual wordmark is untouched, so B2 is still
  genuinely unanswered.
- **Two empty states that couldn't previously exist.** "Recently deleted"
  and "Feedback" were hidden when empty because they sat mid-page; on
  their own routes a blank screen reads as broken, so both now say
  there's nothing.
- **"No activities logged yet" became wrong** once Recent shows only
  completed work — someone whose activities are all planned has plenty
  logged. Now "No completed activities yet."

**Caught by reading the new code back, not by a failing test:** each
section page fired its fetch before the wrapper's access guard rendered,
so a viewer opening `/manage/feedback` sent a request that merely 403'd.
Nothing leaked (the backend refuses; the wrapper shows the refusal), but
the old single-route page gated its fetches and these should too — every
section now gates on the same `canAccess` call it renders with.

**Verified for real.** Local PostGIS/GDAL + PostgreSQL 16 (same sandbox
fallback; the two stale PPAs still need removing first). `manage.py check`
and `makemigrations --check` clean — **no migration; this is frontend-only**.
`tsc -b` and `vite build` clean. **118 Playwright assertions in real
Chromium at a phone viewport, all passing**: the logo on all five auth
screens (loaded, not a broken reference, and heading-sized); the
dashboard's counts and the absence of any planned activity from Recent;
both list pages including search, the status filter, the "Showing X of Y"
hint, and a row actually opening the edit form; all seven Manage
sub-routes; both `/admin` redirects; the nav's new shape; quick log end to
end through the photo step; and the four-membership gate matrix above. No
console errors beyond the documented basemap-tile noise.

**A verification-harness lesson worth keeping:** the first run failed on
quick log, and the cause was the *seed*, not the app — it set a property's
shape with a `geometry` key, but the field is `boundary`
(`PropertySerializer.geo_field`) and the wrong key is silently ignored, so
the property saved shapeless and the "which property is this point on?"
inference correctly found nothing. Worth remembering before reading a
red assertion as a product bug.

**Docs:** manual `getting-started.md` (new nav list), `activities.md` and
`sightings.md` (new "Finding a/an …" sections + screenshots),
`organization-admin.md` (retitled "Manage (organization admin)", each
section now says which sub-page it's on, moved-from-`/admin` note),
`dashboard.md`, `properties.md`, `species.md`, `public-site.md`,
`account.md`, `roles-and-permissions.md`, `README.md` (nav/section
wording throughout), `limitations.md` (quick-log photo gap corrected, and
three new honest gaps: the regular create forms still can't attach
photos, the two lists filter client-side, and the nav is the same on
every page). `docs/open-questions.md` and `build-questions.md` both
updated — the authorization banner is replaced by a BUILT entry and is
now spent.

**Screenshots regenerated** (last regen 2026-09-02, so within the
once-per-calendar-date cap), 21 in total including three new ones
(`manage.png`, `activities-list.png`, `sightings-list.png`).
**`capture.js` needed real updates, not just a re-run**: it drove
`/admin` for the member-list shot and read the "View public site" href
from that page, both of which moved. Same lesson as the 2026-09-02 run —
the script rots silently between regens.

**Still open, deliberately:** B2 (the logo mark as the "h") — unanswered
by the owner, so untouched; the contextual menu, parked; quick-log draft
persistence; activity-type reordering; workflow states still not editable
in-app; and the public-site relocation's remaining ops steps.

### 2026-09-03 — Scheduled PM check-in: six more feedback items triaged;
### `page_path` confirmed working and already changing the triage

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, and ask rather than infer if a build
seems wanted — no live human joined). `main` verified current:
`origin/main` == HEAD == `7c5e8fa`. Dev instance reachable (`GET /` and
`/api/auth/csrf/` both 200). `GET /api/feedback/pull/` returned **six new
items** (ids 7-12); all triaged in `build-questions.md` (2026-09-03) and
marked synced afterwards — confirmed the follow-up pull returns `[]`.

**All six verified against the code, not recorded at face value**, and
two came back materially different from the report:

- **The nav-restructure request (id 8) can't be built as written.** It
  asks for Activities and Sightings nav entries, but there are no
  `/activities` or `/sightings` routes at all — both live only inside a
  property. So it's implicitly a request for two new org-wide list pages,
  which is *also* what id 10's "found and edited on their respective
  pages using a search/filtering function" needs: **the two items are one
  feature.** Separately, moving Properties and Species "under admin"
  would hide them from viewers and editors, since the Admin nav entry is
  `isAdmin`-gated — almost certainly not the intent, but a real
  consequence, so it's a question rather than a build-session guess.
- **The logo-as-"h" request (id 12) is more answerable than it looks.**
  Read the actual SVGs: each seasonal mark is a vertical stem plus a
  shoulder arch dropping to a second leg — structurally a lowercase "h"
  already, with the foliage growing out of the stem. So it's typographic
  execution, not a redesign. Flagged one trap for whoever builds it: the
  mark carries `alt="Habitat"` beside the literal text "habitat", so a
  naive split would have a screen reader announce "Habitat abitat".
- **Three confirmed exactly as reported, and one is broader:** the old
  `🌿 Habitat` placeholder is on **five** unauthenticated screens, not
  just login (the 2026-08-29 logo work covered `TopBar`/`PublicHeader`
  only) — so the first screen a new user sees is the stale one. The
  dashboard genuinely double-counts (`recentActivities` has no `is_done`
  filter, so a planned activity shows in both sections) and uses
  `RECENT_LIMIT = 5` where three was asked for. `OrgAdminPage.tsx` is
  1061 lines rendering eight top-level sections on one route.
  `QuickLogPage.tsx:264` navigates away immediately on save, and
  `PhotoUploader` already does camera capture — so the photo request is a
  flow step, not new capability.

**`page_path` (built yesterday) is confirmed working and already earned
its keep** — all six items carried the screen they came from, and it
changed the triage rather than decorating it (one item is vague until its
`/admin` path makes it specific; another is identifiable as being about
the day-old quick-log flow only because of its path). Recorded in
`docs/open-questions.md`, whose "App feedback" section had it listed as
still-open queued work.

**Named a theme rather than filing six unrelated nits:** four of the six
are the same complaint — too much on one screen, and no way to find one
record among many. The app has outgrown its Phase 1 information
architecture now that there's real data in it.

**Docs:** `build-questions.md` (new 2026-09-03 entry, sections A/B/C),
`docs/open-questions.md` ("Logged-in app UX" gained the two questions and
the four build-ready items; "App feedback" records the second real batch
and moves `page_path` out of the still-open list). No `docs/manual/`
update applies — nothing user-facing changed. **No code, migrations, or
screenshots.** Push notification sent naming the two questions.

**Live follow-up, same session:** the owner replied to the notification
answering B1's load-bearing sub-question — *"I'm asking for two pages to
help manage those two things"* — confirming the inferred reading:
**Activities and Sightings become two new org-wide pages**, which also
settles feedback id 10's second half (the two items are one feature).
**Recorded, not built** — per this session's own trigger (project-manager
scope, "wait for me to explicitly say 'build this'") and this file's
durable rule that a queue-scoped session stays queue-scoped for its whole
lifetime; a detailed answer is not build authorization. The two remaining
nav sub-questions (the Admin-gating conflict, and what "changes based on
current page" means) were re-asked rather than defaulted.

The owner then answered both: **"Admin" becomes a "Manage" section**
visible to every member with the admin-only surfaces role-gated inside
it (which resolves the exposure conflict — the gate moves inward rather
than disappearing), and **the contextual menu is parked** ("park for a
hot minute") rather than dropped. Finally: **"Build next run."** That's
explicit build authorization naming *the next run*, so this session
recorded it as an authorization banner at the top of
`build-questions.md` — same shape as the 2026-09-02 (6) precedent —
covering six items (A1-A4, the two new pages, the Manage section) with
two exclusions stated so a build session can't widen into them: the
parked contextual menu, and **B2 (the logo mark as the "h" in
"habitat"), which the owner never answered** and which is therefore not
authorized despite touching the same brand surfaces as A1. Still nothing
built this session.

### 2026-09-02 (7) — Scheduled programmer session: built all five
### authorized feedback items, end to end

Scheduled "programmer" session (explicit build authorization in its own
trigger). Dev instance up (`GET /` and `/api/auth/csrf/` both 200);
`GET /api/feedback/pull/` returned `[]`, so no new user feedback this
run. Read `docs/open-questions.md` and `build-questions.md` per this
file's triage rule: the queue held exactly one authorized item — the
owner's *"build these in the next build session"* covering all five
2026-09-02 feedback items. **Built all five**, in the recommended order,
rather than stopping at one.

**1. Org-defined activity types + the display fix** (both halves). New
`ActivityType` — a per-org table shaped deliberately like
`WorkflowState` (unique name per org, `order`, default set seeded by a
`post_save` signal); `Activity.activity_type` is now a PROTECT FK.
Writable `/api/activity-types/` and an **Activity types** section in the
org admin console (rename in place, add, delete). **The casing half fell
out of the shape rather than needing its own mechanism:** `name` is both
the stored value and the label, so there is no slug left to render by
mistake — which is what the queue file warned about ("the org can name
it" must not reintroduce raw slugs). `ActivitySerializer` also serves
`activity_type_name` beside the id, mirroring `status_name`, so the app
and the public site can't drift over a label. All six frontend render
sites updated. Deleting a type in use returns a **400 saying how many
activities are on it**, not a 500 from `ProtectedError`.

**The flagged backfill trap was real and is handled.** Migration
`activities/0003` is schema + data + cleanup as one migration (a
half-applied state can't exist): it seeds each existing org's eight types
in proper Title Case, repoints every existing activity, and gives a value
outside the eight — reachable only via Django admin or the API directly —
a row of its own rather than silently rewriting it. **Verified against a
database seeded at the pre-migration state** with two orgs, four
activities and one such legacy value, not just on an empty database.

**2. Species description + bloom range.** `notes` **renamed** to
`description` (migration `species/0002`). The queue file said "consider"
the rename; it's the right call, because the field was *already* served
unauthenticated (`SightingSerializer` nests `SpeciesSerializer` as
`species_detail`) under a name that implied privacy — the name was the
bug. The species screen now labels it "Shown publicly" on both its add
and edit forms. **The year-wrap trap was also real:** bloom endpoints are
stored as MMDD integers and served as `MM-DD` strings, so they carry no
year to drift; a range may wrap (Nov→Feb) and there is deliberately **no
`start <= end` validation**. The filter is server-side
(`?blooming_on=MM-DD|today`) because the wrap makes it more than a
comparison, with `Species.blooms_on` as the same rule in Python next to
the model. Surfaces publicly as detail on a **sighting**, per the owner.

**3. Quick log** (`/quick-log`, entry point on the dashboard). Geometry
decides the record type — one point is a sighting, three or more an
activity — and **the property is inferred from where the points land**
(new `positionInPolygon` in `utils/geo.ts`), so "which property?" isn't a
step; it stays overridable, and a point outside every boundary falls back
to asking (which is also how you log a sighting with no property). The
capture screen gives the map the **whole viewport**, which is the
concrete answer to the phone screen-space half of the complaint; the
detail step then takes the screen in turn, so neither half is squeezed.
Two points is the one genuinely ambiguous count and is blocked with an
explanation rather than guessed at. **Sub-questions defaulted, as the
queue advised, not blocked on:** no draft persistence, and the existing
`.page--map` layout left alone pending real use. The existing
activity/sighting forms are untouched — this is an additional way in.

**4. Logo links home.** `/` in the app; the org's own public root on the
public site, which is the distinction the queue called out — `/` there
would drop a visitor into the login-gated app.

**5. Feedback records its page path.** `Feedback.page_path`, in the
admin's own list *and* the cross-org pull payload (reaching the build
queue is the whole point). Stores a path, not a URL: a full or
protocol-relative URL is dropped rather than rejecting the feedback over
a context field.

**Found while building, fixed, outside the original scope:**

- **Cross-org FK holes on `Activity`.** Writing `validate_activity_type`
  meant looking at its siblings — `ActivitySerializer.status` had never
  been validated against the caller's organization either, the same class
  of bug the 2026-09-01 session fixed for `property`. An editor could
  point an activity at another org's workflow state by id. Both validate
  now; confirmed with a two-org test.
- **A blank page whenever a map page's layer effect re-ran during
  unmount.** `map.remove()` tears down the style, but a page holds its
  map in state, so an effect firing a tick later called into it and
  threw, unmounting the whole React tree. Quick log hit it (leaving
  capture stops the location watch, which changes a layer effect's
  dependency), but the hazard is general — guarded in `mapLayers.ts` so
  every map page is covered, not just this one.
- **`capture.js` had been broken since the last regen (2026-08-29)**, in
  two places, both from later sessions: `form.form--panel select` started
  matching the Theme panel's font select once that section landed above
  the member form, and the "View public site" href became absolute when
  the public site's origin was made configurable. Both fixed; the script
  runs end to end again. Worth knowing for the next session: a regen gap
  means the script rots silently.

**Verified for real.** Installed PostGIS/GDAL + local PostgreSQL 16 (same
sandbox fallback prior sessions documented). `manage.py check` and
`makemigrations --check` clean. 46 curl checks covering the seeded type
set and its Title Case, create/rename/delete, case-insensitive duplicate
rejection, delete-in-use as a 400, the bloom round-trip, Feb 29, rejection
of Feb 30 / month 13 / a real date with a year / half a range, the
wrap-aware filter on both sides of the year, page-path storage and its
URL rejection, the cross-org FK rejections, and the public payloads. Then
38 Playwright checks in real Chromium at a phone viewport: quick log end
to end (capture → detail → the saved record visible on its property),
the two-point block, day clamping when moving to a shorter month, the
blooming-today filter, the admin activity-type section, and — from an
anonymous second context — the species description, bloom range, Title
Case activity type, and the public logo's destination. `tsc -b` and
`vite build` clean.

**Two layout bugs came from *looking at* the generated screenshot, not
from the assertions:** MapLibre's attribution painting over the capture
screen's Cancel link, and the floating feedback button clipping the
primary action at phone width. Both fixed and re-measured at 390px and
1280px. Worth repeating the lesson: the assertions all passed while the
screen was visibly wrong.

**Docs:** `docs/data-model-notes.md` (Activity type bullet rewritten as
decided-and-built, new "Species: public description and bloom period"
subsection, feedback `page_path`), `docs/open-questions.md` (all five
moved into "Recently resolved"; "Data model" is now empty; "Logged-in app
UX" reduced to the two things genuinely still open), `build-questions.md`
(authorization banner replaced by a BUILT entry — that authorization is
now spent), manual `dashboard.md` (new "Quick log" section +
screenshot), `activities.md`, `species.md`, `organization-admin.md` (new
"Activity types" section), `public-site.md` (new "Species detail on a
sighting"), `getting-started.md`, `limitations.md` (new gaps recorded:
no type reordering, no quick-log draft, and **a species has no private
notes field any more** — the honest cost of the rename).

**Screenshots regenerated** (last regen 2026-08-29, so within the
once-per-calendar-date cap), including a new `quick-log.png`.
`capture.js` also now fills in a species' description and bloom period,
so `species.png` demonstrates the fields the chapter is mostly about
rather than showing them permanently empty.

### 2026-09-02 (6) — Owner authorized the build: all five feedback items
### are cleared for the next build session (still not built here)

Owner, live, verbatim: **"build these in the next build session."** That's
the explicit authorization this file's working conventions require, and
it names *the next build session* — not this one, which is
project-manager-scoped and correctly did not implement anything. Recorded
as an authorization banner at the top of `build-questions.md` covering
all five 2026-09-02 feedback items, so the next programmer run reads
"authorized, go" rather than "decided, awaiting a go-ahead" and doesn't
re-ask a question that's already been answered.

**Scope recorded explicitly:** the five items and their already-decided
sub-decisions — not a general licence to build anything else in that
file. A recommended order is included (feedback page-capture and the logo
link first, since they're small and independent; the two migrations —
activity types, then species — after; quick log last as the largest and
most design-sensitive), with a note that splitting the two migrations
across runs is the safer shape but all five are authorized together.

The three late-surfacing traps are re-stated in the banner so a build
session hits them before writing code, not after: the activity-type
migration needs a **data backfill** (and an org-defined row still needs a
human label or raw slugs return); the bloom range is **annual and
recurring** while a date carries a year and can wrap it; and `notes` is
**already publicly served**, so the species screen must label it public.

### 2026-09-02 (5) — Live follow-up: owner answered all three feedback
### questions — all five items now build-ready, none built

Same session as the check-in below; the owner replied live to its
notification, answering all three open questions at once. **Recording
only** — the owner didn't say "build this," so per this session's
project-manager scope and this file's own durable rule (a queue-scoped
session stays queue-scoped for its whole lifetime; a detailed answer is
not build authorization), everything was queued rather than implemented.
**Net effect: all five of the day's feedback items are now build-ready.**

**Activity type — org-defined *and* fix the casing** (*"org defined
values, but also fixing the casing too"*): both halves, not a choice
between them. Shape follows the existing `WorkflowState` precedent
exactly — per-org table, FK on `Activity`, seeded defaults per org —
which makes it a data migration that backfills existing string values,
not just a schema change. Flagged for the build session: an org-defined
row still needs a human label, so "the org can name it" must not quietly
drop the display name and reintroduce raw slugs.

**Species — surface `notes`, add a bloom date range** (*"notes isn't
visible on the species definition screen. bloom time as date start and
end. This would be used as a filter."*). The owner's diagnosis is
correct and was verified against the code, which also settles the
sub-question this check-in had flagged as needing care: `Species.notes`
is on the model, in `SpeciesSerializer`, and in the frontend `Species`
type, but `SpeciesPage.tsx` renders only common and scientific name in
*both* its add and edit forms. The field has never been reachable from
the UI, so it's provably empty everywhere — which removes the
data-exposure risk that had made "repurpose `notes`" the unsafe reading.
Decision recorded: surface `notes` as the description rather than adding
a near-duplicate field, with that reading stated explicitly rather than
assumed silently. One real modeling call left for the build session: a
bloom period is annual and recurring while a `DateField` carries a year,
and a range can wrap the year (Nov–Feb) — a naive `start <= end` filter
breaks winter-blooming species.

**Quick log — an additional mode, entry point on the dashboard** (*"quick
log makes sense on the dashboard"*): answers the load-bearing question
(not a replacement — the existing forms stay, since they're needed for
editing anyway) and gives the dashboard its first action alongside its
read-only summaries. Draft persistence and whether the phone
screen-space complaint needs its own layout pass stay unanswered;
recommended defaults recorded rather than left as blockers.

**Then the owner closed the last sub-question**: the species description
surfaces as *"more info on the public site when viewing the sightings"* —
extra detail on a sighting on the public property page, not a separate
public species page. Tracing that answer turned up a real finding:
**`notes` is already served publicly today.** `public_site/views.py:204`
serves public sightings through `SightingSerializer`, which nests
`SpeciesSerializer` — including `notes` — as `species_detail`. So the
field already reaches unauthenticated visitors and only the rendering is
missing. That makes the decision consistent with existing behavior and
shrinks the backend work, but it also means **a field labelled "Notes" is
silently public**: it's empty today only because no UI ever wrote to it,
and anything entered via Django admin or the API directly is already
exposed. Recorded for the build session: label it explicitly as
public-facing on the species screen, and consider renaming the field to
`description` in the same migration so the name stops implying privacy.

**Docs:** `build-questions.md` (new 2026-09-02 (7) entry with each
decision and its build notes; the three B items in (6) marked decided
and cross-referenced so a build session can't read the question without
the answer), `docs/open-questions.md` (the two "Data model" bullets and
the "Logged-in app UX" quick-log bullet rewritten as decided-not-yet-built).
No `docs/manual/` update applies — nothing user-facing changed yet. No
code, migrations, or screenshots.

### 2026-09-02 (4) — Scheduled PM check-in: the feedback pipeline
### delivered five real user items — first genuine build input it's produced

Routine "resolve open questions" run, project-manager scope only (its own
trigger: record/queue, don't build, even if a live request arrives —
none did). `main` verified current: `origin/main` == HEAD == `7bc079a`.
Dev instance reachable (`GET /` and `/api/auth/csrf/` both 200).

**Step 3 of this routine's own job produced content for the first time.**
Every prior check-in recorded it as a no-op (no token) or an empty queue;
this run `GET /api/feedback/pull/` returned **five real items** — feature
requests and bug reports from the owner's `test` org, not the earlier
pipeline smoke test. All five triaged in `build-questions.md`
(2026-09-02 (6)) and then marked synced, so the next pull won't re-serve
them. `synced` means *recorded*, not *resolved* — none is built.

**Two were verified against the code rather than recorded at face
value**, and both hold up: the logo genuinely isn't a link (`TopBar.tsx`
and `PublicHeader.tsx` both render a bare `<Logo>`), and the lowercase
activity-type complaint is more precisely a serialization gap —
`Activity.ActivityType` already carries proper labels ("Seeding",
"Intervention (general)"), but `ActivitySerializer` exposes only the raw
value, which the frontend then renders directly in six places. So the
human-readable labels exist server-side and simply never reach the
client.

**Triage: three build-ready, three needing an owner decision.** Ready
without input — logo links home (with the one real call being that the
*public* header's logo goes to the org's public root, not `/`, which
would drop a visitor into the login-gated app); feedback captures its
submitting page path (requested through the pipeline itself, and worth
doing early since it makes every later item cheaper to act on); and
activity-type display labels via a serializer field, mirroring the
existing `status_name` convention so the app and public site can't
drift. Needing the owner — whether the activity type enum becomes
org-defined (the question `Activity`'s own docstring has carried since
the first backend session, now asked by a real user; three shapes on the
table, PM recommendation is the `WorkflowState`-mirroring one); species
description + bloom time (three sub-questions, the load-bearing one being
*where* it displays — species reach the public site today only as a name
on a sighting/activity, with no species page at all, so this is a feature,
not two columns); and the geometry-first mobile logging workflow, a
redesign of the app's core flow that needs shaping on replacement-vs-
additional-mode, draft persistence, and whether the phone screen-space
complaint is the same problem or its own layout pass.

**Docs:** `build-questions.md` (new 2026-09-02 (6) entry with the full
triage, A/B/C sections), `docs/open-questions.md` (two new "Data model"
bullets, a new "Logged-in app UX" section, a new "Public-site content
policy" section, and the "App feedback" section updated to record that
the pipeline delivered real content end to end). No `docs/manual/` update
applies — nothing user-facing changed. **No code, migrations, or
screenshots this session.** Push notification sent naming the three
questions.

### 2026-09-02 (3) — Scheduled programmer session: built custom HTML/JS
### pages — the last unbuilt piece of the storytelling feature family

Scheduled "programmer" session (explicit build authorization in its own
trigger). Pulled the live feedback queue first, now that the token is
provisioned — `GET /api/feedback/pull/` returned `[]`, so nothing new
came from users this run; dev instance up (`GET /` 200). Read
`docs/open-questions.md` and `build-questions.md` per this file's triage
rule: exactly one item was decided-and-unbuilt — **custom HTML/JS on the
public site** (owner decided 2026-09-02: isolated-origin sandbox, not
allowlist sanitization). Built it end to end.

**Built.** `Page.content_format` (`markdown` | `html`, default markdown,
migration `pages/0002`) plus `Organization.custom_html_allowed`
(migration `accounts/0012`). An `html` page's body is **never inlined**
into the public site's DOM — it's served as its own document at
`/api/public/o/<org>/pages/<slug>/document/` (and the property mirror)
and embedded via `<iframe sandbox="allow-scripts">`.
`PublicPageDetailSerializer` returns an empty `body_html` plus a
`document_url`, so there's no code path that could inline it by
accident. Frontend: a shared `PublicPageBody` component owns the
markdown-vs-html branch for both public pages (rather than duplicating
the security-relevant decision in two files), a Content type picker on
`PageFormPage` shown only where the gates allow it, and a
`.page-content-frame` style.

**The security control is the sandbox, not sanitization and not the
hostname.** The document response carries `Content-Security-Policy:
sandbox allow-scripts`, which applies the sandbox to the document itself
— a unique opaque origin whether it's framed or opened directly.
`allow-same-origin` is withheld from both the header and the iframe
attribute, since granting it alongside `allow-scripts` lets a document
remove its own sandbox.

**Answered the architecture question `build-questions.md` explicitly
queued** (is the per-page iframe still needed once the whole public site
is off-origin?): **yes, keep it** — the decided shape is a *single
shared* public subdomain, so without it every tenant's authored content
would share one origin with every other tenant's; and because the
sandbox holds on any origin, the feature works correctly on a deployment
that hasn't relocated the public site yet. So it's deliberately **not**
gated on `PUBLIC_SITE_URL` — relocation is defence in depth, per this
repo's own standing note that an environment-specific value is never a
reason to defer application work.

**Two gates, both policy rather than security** (`apps/pages/custom_html.py`):
`HABITAT_CUSTOM_PAGE_HTML`, off by default so upgrading changes nothing,
and `Organization.custom_html_allowed` — the per-tenant kill-switch,
editable only from Django admin, deliberately *not* from an org's own
admin console, since an org switched off for abuse must not be able to
switch itself back on. Turning either off also stops *already-published*
pages rendering, not just new edits. Plus a 512 KB size cap
(`HABITAT_CUSTOM_PAGE_HTML_MAX_BYTES`).

**Two bugs found by testing, not by reading the diff:**
`frame-ancestors 'self'` alone silently blanks the frame wherever the
frontend is served from a different origin than the API — local dev, and
the relocated-public-site deployment this feature exists for — so it now
includes `FRONTEND_URL` and `PUBLIC_SITE_URL`. And Django's
`XFrameOptionsMiddleware` stamps `X-Frame-Options: DENY` on the document
and breaks the embed outright, hence `@xframe_options_exempt` on both
document views.

**Verified for real, in a browser.** Installed PostGIS/GDAL + local
PostgreSQL 16 (same sandbox fallback prior sessions documented; the two
stale PPAs still need removing first). 22 curl checks: markdown pages
entirely unchanged (a `<script>` in markdown source still stripped);
html create/public payload/empty `body_html`/document served verbatim
with the script intact; every response header asserted, including that
`allow-same-origin` is **absent**; unpublish → 404 → republish → 200;
the size cap; property-scoped html pages. A second backend at the
default flag proved the off state fully inert (`custom_html_enabled`
false, `html` write 400s, markdown still 201s, an already-authored html
page stops rendering). Kill-switch exercised per-org, confirmed not to
affect another org. Then 14 Playwright checks in real Chromium: page
authored through the actual UI, and from inside the frame the author's
script **runs** and reports `cookie=blocked | origin="null" |
localStorage=blocked | parentDOM=blocked` — with a canary cookie planted
on the app's origin first so that check isn't vacuous — while the
embedding page's own DOM contains none of the author content and a
markdown page still renders inline with no iframe. `manage.py check` /
`makemigrations --check` clean; `tsc -b` and `vite build` clean.

**Docs:** `docs/data-model-notes.md` (new "Custom HTML/JS pages"),
`docs/deployment-config.md` (two env vars + an "Enabling custom-HTML
pages" section), `docs/open-questions.md` (marked built, sub-question
answered, the content-policy question left open as policy not code),
`build-questions.md` (new dated entry), manual `public-site.md` (new
"Custom HTML pages" section), `organization-admin.md`, `properties.md`,
`limitations.md` (replaced the now-false "no raw HTML or scripting"
bullet, added a content-policy one). **Screenshots not regenerated** —
the Content type picker only appears where the feature is enabled, which
isn't the default state existing screenshots depict, so nothing went
from accurate to wrong.

**Still open, deliberately:** no content policy/TOS for author-published
pages (a policy question, not a build one — the sandbox stops author
code reaching Habitat, but not an author misleading their own page's
visitors; the kill-switch is the after-the-fact remedy); per-tenant
origin isolation (the deliberate consequence of the single-shared-subdomain
decision); and the public-site relocation's remaining ops steps
(DNS/TLS/serving path), unchanged from the previous session.

### 2026-09-02 (2) — Scheduled programmer session: built the
### property-scoped admin-console narrowing (plus the lockout-guard fix it
### exposed); public-site relocation re-deferred as ops-blocked

Scheduled "programmer" session (explicit build authorization in its own
trigger: "incorporate this feedback into the codebase and commit directly
to main"). Read `docs/open-questions.md` and `build-questions.md` per this
file's own triage rule. Exactly two items were decided-and-unbuilt, both
from the same day's live decision session (entry below): the
property-scoped admin-console narrowing, and the public-site relocation to
an isolated subdomain. Built the first end to end; re-deferred the second
with a stated reason (see below), rather than half-building it.

**Built — a property-scoped admin now administers its properties, not the
organization.** Backend `apps/accounts/org_scoping.py` gained
`is_property_scoped`/`membership_manageable`/`scope_assignable`/
`ensure_account_wide_admin`, wired into `MembershipViewSet` (list/create/
partial_update/destroy), `InvitationViewSet` (list/revoke/resend),
`OrganizationDetailView.patch`, `organization_theme_image`, and the
feedback app's own-org list/resolve. Every edge case the decision record
explicitly left "for the build session to nail down" got answered and
written down (`data-model-notes.md`, "Permissions") rather than left
implicit: **full containment, not partial overlap** (an admin for property
A can't act on a member scoped to A+B — that would change their access to
B); **an account-wide member is never reachable** by a scoped admin, which
is also what structurally keeps them away from the org's account-wide
admins; **adding a member is allowed but must land inside the admin's own
scope** (no account-wide member, no widening an existing member past the
admin's scope — which is also what stops a scoped admin widening
*itself*, verified explicitly); **the member list is filtered**, not shown
read-only, so a scoped admin doesn't see rows where every action would
fail; **pending invitations follow the membership rule**, since an
invitation carries the scope its membership will have; and **org-level
actions with no property dimension stay with account-wide admins** (org
rename, public URL slug, org theme + header image, org-level pages, the
feedback queue). `build-questions.md` predicted membership scoping would
need its own set-vs-set comparison rather than a reuse of
`property_accessible` — that held, hence the new helpers.

**Correctness fix the narrowing exposed** (not part of the decision, a
consequence of it): the "an org needs at least one admin" lockout guard
counted *any* admin. Once a property-scoped admin can no longer rename the
org or manage account-wide members, an org left holding only scoped admins
can't administer itself at all, with no in-app recovery. The guard now
counts **account-wide** admins (`_account_wide_admin_count` replaces
`_admin_count`) and also blocks *scoping* the last account-wide admin to
specific properties, not just demoting or removing them. Also fixed a
one-line consistency gap noticed in the same file: `property_qr_code`
never applied property-scope filtering the way `property_theme_image` and
the property API already did.

**Frontend:** `OrgAdminPage` now hides the org-level half of the page
(name, public URL name, QR, Theme, Pages + landing page, Feedback) from a
property-scoped admin and shows a short note saying who handles those
instead; the add-member form requires at least one property for a scoped
admin (client-side guard plus the backend's own 403), and the member-row
scope hint reads differently for one. The previously-hidden "+ Add page"
control is now simply inside the org-level block.

**Then, live, the owner corrected this session's second call and it got
built too.** The public-site relocation had been re-deferred here as
"ops-blocked (DNS/TLS/serving path)"; the owner's response was *"like the
existing codebase, I'd use configmaps to override defaults"* — i.e. the
code shouldn't wait on a hostname existing, it should read the hostname
from configuration, the way `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` and
`POSTGRES_HOST` already do. That's correct and it's a better rule than the
one this session started with, so it's recorded as a standing note in
`build-questions.md`: an environment-specific value is never a reason to
defer application work — it becomes a variable with a behavior-preserving
default, and the deployment overrides it. Built accordingly:
`PUBLIC_SITE_URL` (backend) / `VITE_PUBLIC_SITE_URL` (frontend), blank by
default = public site on the app's own origin exactly as today; set = every
public link and QR code the app hands out points at the isolated origin.
`CSRF_TRUSTED_ORIGINS` split out from `CORS_ALLOWED_ORIGINS` (it was a
plain alias and still defaults to it) so a deployment can let the public
origin *read* `/api/public/...` without trusting it for state-changing
requests against the app — the exact thing isolation exists to prevent.
QR generation now prefers the configured origin over the caller-supplied
`base_url`, since a QR code is a physical artifact that outlives the
session that generated it. New `docs/deployment-config.md` lists every
env var the app reads plus the step-by-step relocation recipe; what
remains is genuinely ops (DNS record, TLS cert, serving the frontend build
at that hostname), with no further repo work needed to relocate. The
per-page sandboxed-iframe/CSP layer stays deliberately unbuilt — with the
whole site off-origin it may be redundant, better judged against a real
origin than guessed at (`build-questions.md` has the reasoning). Cookie
hardening re-verified while here: `settings.py` still sets no
`SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN`, so both remain host-only,
which is the precondition the subdomain decision rests on.

**Verified, both modes, not just the new one:** two backends and two
frontend builds side by side — one plain, one configured for an isolated
public origin. QR codes decoded with `zbarimg` (not just asserted):
default deployment still encodes the caller-supplied origin and still 400s
without one; configured deployment encodes the configured origin, ignores
a `base_url` claiming `https://client-supplied.example.com`, and works
with no `base_url` at all. Settings asserted directly for both shapes,
including that the public origin lands in CORS but *not* in
`CSRF_TRUSTED_ORIGINS`. Playwright against both stacks confirmed "View
public site", the nav entry, and the QR preview all resolve to the app's
own origin in the default build and to the isolated origin in the
configured one, with no page errors either way. The 44-check scoped-admin
suite re-run afterwards, still green — no regression from the config work.

**Verified for real:** installed PostGIS/GDAL + a local PostgreSQL 16 in
this sandbox (same fallback prior sessions documented; the apt run needed
two stale third-party PPAs removed first — deadsnakes/ondrej both 403 —
worth knowing for the next session). `manage.py check` and
`makemigrations --check` both clean (no model change — this is permission
logic only). A 44-check API script against a live one-org/two-property
setup with five differently-scoped members covered: list filtering; a
scoped admin blocked on an account-wide member, a partially-overlapping
member, and the org's own account-wide admin; allowed on an in-scope
member; blocked from widening/unscoping a member *and itself*; the three
invite paths (account-wide → 403, out-of-scope property → 403, own
property → 201); invitation list/revoke/resend scoping; every org-level
action 403ing while the account-wide owner's identical calls still 200;
and the lockout guard across all four transitions, including the specific
case a property-scoped admin does *not* satisfy it. Explicit regression
checks that an account-wide admin's behavior is byte-identical throughout.
Zero 500s across the run. Frontend `tsc -b` + `vite build` clean; a
Playwright run against the live stack confirmed the account-wide admin's
`/admin` still shows every section and all three members, while the
scoped admin's shows the notice, no org-level sections, only its own row,
and the add-member guard firing — no page errors either way.

**Docs:** `docs/deployment-config.md` (new — the env-var reference and
relocation recipe), `docs/data-model-notes.md` (new sub-bullet under Permissions
with the full rule, and the old "not extended to the org admin console"
line replaced), `docs/open-questions.md` (item moved out of "Accounts,
orgs, and permissions" into "Recently resolved"), `build-questions.md`
(new dated entry answering each queued sub-question, item marked built,
relocation re-deferral recorded), manual `roles-and-permissions.md` (new
"What a property-scoped admin can administer" section, rewritten last-admin
rule), `organization-admin.md` (scoped-admin note at the top, member list
+ add-member + feedback wording), `limitations.md` (replaced the now-false
"doesn't extend to the org admin portal" bullet). **Screenshots not
regenerated** — `org-admin.png` still accurately depicts what an
account-wide admin sees (the common case, and what the surrounding text
describes); the scoped-admin view is a new, uncommon state no existing
screenshot claims to show, so nothing went from accurate to wrong.

### 2026-09-02 — Scheduled PM check-in, then a long live decision session:
### property-scoped admin console, feedback pipeline confirmed live,
### and a major public-site architecture pivot (isolated-origin relocation)

Started as the routine "resolve open questions" scheduled task
(project-manager scope only — see this session's own instructions: record/
queue, don't build, wait for an explicit "build this"). The owner then
joined live and this stayed in that recording/queuing posture per
`CLAUDE.md`'s own durable rule, even though several of the exchanges below
read like detailed build specs — nothing was implemented this session.

**PM check-in findings (no code):** re-confirmed `main` unchanged since
the 2026-09-01 programmer session; found one genuinely new item that
session had raised but never pushed to the owner (should a property-scoped
admin's reach into the org admin console itself be narrowed?); re-
confirmed Custom HTML and the feedback-token gap were both still open.
Sent a push notification naming all three.

**Live decisions recorded (all owner, 2026-09-02, none built this
session):**
1. **Property-scoped admin console — narrow it.** A property-scoped
   admin's admin-level actions (member/role management via `/admin`)
   should reach only members scoped to their own property/properties, not
   the whole org. Exact boundary (can they invite a new member into their
   own scope? edit a member whose scope only partially overlaps theirs?)
   left for the build session — several concrete edge cases queued in
   `build-questions.md` rather than guessed at here.
2. **Feedback pipeline confirmed fully live, not just built.** The owner
   provisioned `HABITAT_FEEDBACK_TOKEN` on both `habitat.dev.cravenator.com`
   and this scheduled routine's own environment, then submitted a real
   test item. Verified for real: pulled it via the bearer-token endpoint,
   marked it synced, confirmed a follow-up pull correctly excluded it
   (the incremental-fetch dedup actually works). This closes the last
   ops-only gap the feedback pipeline (built 2026-08-29) had.
3. **Custom HTML/JS on the public site — isolated-origin sandbox, not
   allowlist-sanitization.** Reverses the 2026-08-29 "park it, accept
   on-origin risk" call. Walked the owner through the three options
   (allowlist-sanitize / raw on shared origin / sandboxed isolated
   origin) in plain language since the original framing wasn't landing;
   owner chose isolation.
4. **Isolated-origin shape — a single shared subdomain, not a purchased
   domain, not per-tenant subdomains.** Checked this against the actual
   codebase rather than re-deriving from the original 2026-08-29
   checklist's theoretical recommendation: `backend/config/settings.py`
   never sets `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN`, so both are
   already Django's default host-only cookies — a subdomain like
   `public.habitat.dev.cravenator.com` genuinely won't receive the app's
   session/CSRF cookies, so no new domain purchase is needed, just a DNS
   record + a normal (non-wildcard) TLS cert. Single-shared (not
   per-org) was the owner's own call, to avoid wildcard DNS/TLS
   complexity.
5. **Scope of the relocation — the whole public site, and a move, not a
   rewrite.** The owner's first reaction to (3)/(4) was that this
   "probably undoes a lot of current public site decisions," then asked
   to "can existing and start over" — which on clarification meant the
   *entire* public site (Explore view, vanity slugs, QR codes, authored
   pages, theme controls), not just the not-yet-built custom-HTML layer.
   Rather than recording "scrap and redesign" at face value, walked the
   owner through what's actually driving the need (isolation, not any
   flaw in what's built — nothing already shipped is unsafe) and offered
   two paths: (A) relocate the existing, already-verified feature set to
   the new isolated subdomain unchanged, or (B) actually redesign the
   public site from scratch. **Owner picked (A).** So the eventual build
   is a *move* (same models/views/features, different serving origin),
   not a rewrite — flagged this distinction explicitly in
   `build-questions.md` so a future build session doesn't over-scope it
   into a redesign, and so none of the already-shipped, already-verified
   work (2026-08-14 through 2026-08-31) gets discarded needlessly.
   **Architectural note recorded for the build session:** since the
   *whole* public site moving off-origin already isolates the app's
   session cookies from any author JS, the original "sandbox each
   authored page in its own nested iframe" plan may no longer be strictly
   necessary — flagged as something to evaluate at build time rather than
   building both layers reflexively.

**Not built this session** — everything above is decided-and-queued in
`docs/open-questions.md` ("Public site storytelling / custom content",
"Accounts, orgs, and permissions") and `build-questions.md`, both updated
in step with each decision as it was made. No `docs/manual/` update
applies (nothing user-facing changed yet). The next build session has a
meaningfully large, mostly-decided chunk of work waiting: property-scoped
admin-console narrowing, and the public-site-to-isolated-subdomain
relocation plus real custom-HTML/JS authoring on top of it — both still
need an explicit "build this," not just design sign-off.

### 2026-09-01 — Scheduled programmer session: property-scoped role
### enforcement, plus a cross-org data-integrity fix found along the way

Scheduled "programmer" session (explicit build authorization per its own
trigger). Read `docs/open-questions.md` and `build-questions.md` per this
file's own triage rule — two PM check-ins earlier the same day (see
`build-questions.md`) had already confirmed the only two genuinely open
items (Custom HTML on the public site; the feedback-token ops gap) were
unchanged and not build-ready, and re-confirmed the same again this run.
Rather than idle, picked up a well-scoped, already-decided-in-*shape* gap
that had sat undisturbed since the very first org-admin-portal session
(2026-08-14): **property-scoped roles were stored and editable through
the admin portal from day one but never actually enforced** — every
membership behaved as account-wide regardless of which properties were
checked, a limitation both `docs/manual/roles-and-permissions.md` and
`limitations.md` had documented (accurately) the whole time. Not a design
question (the shape — viewer/editor/admin, optionally scoped to specific
properties — was decided in 2026-08-14's session), just an unimplemented
piece of an already-decided feature.

**Built:** `apps/accounts/org_scoping.py` gained `scoped_property_ids`/
`property_accessible`/`ensure_property_accessible`/
`ensure_optional_property_accessible`/`filter_by_property_scope`, wired
into `PropertyViewSet`/`ActivityViewSet`/`SightingViewSet`/`PageViewSet`
(queryset filtering + create-time checks) and the function-based photo/
link/species-link views that look records up directly instead of going
through a filtered queryset. A property-scoped membership now only ever
sees/acts on its own properties' activities, sightings, and pages; can't
create a brand-new Property or org-level Page (nothing to scope either
to — an admin creates one and adds the member to it); and can't create a
property-less Sighting (it'd be invisible to every scoped member,
including its own creator). Species/Task/WorkflowState stay account-wide
— none has a Property FK to scope by, a deliberate reading, not an
oversight. Frontend: the session payload's `MembershipSerializer` now
carries the caller's own `properties` scope; a new `isPropertyScoped()`
helper hides "+ New property" (`PropertiesPage`, `DashboardPage`) and
"+ Add page" (`OrgAdminPage`) for a scoped member instead of showing a
control that would always 403.

**Real cross-org bug found and fixed along the way, not property-scoping
itself:** while writing the scope-validation helper, found
`ActivitySerializer.property` and `SightingSerializer.property`/
`.species` had never been validated against the caller's own
organization *at all* — the auto-generated `PrimaryKeyRelatedField`
queried the entire table, so any editor could set either FK to a record
belonging to a completely different organization. Since the public site
derives a property's public activities/sightings straight off that FK
(`apps/public_site/views.py`), this meant one org's editor could plant a
fabricated activity or sighting on a *different* org's public property
page just by knowing/guessing its numeric id — confirmed for real with a
two-organization curl test, not theoretical. Fixed with the same
`validate_<field>`-against-the-caller's-org pattern `TaskSerializer`/
`PageSerializer` already used for their own FKs.

**Explicitly not extended to the org admin console itself** — a
property-scoped admin (an unusual configuration; the common case is
account-wide) can still manage the org's members/roles account-wide,
including in principle its own scope, via the existing
`MembershipViewSet`. Queued as its own open question
(`docs/open-questions.md`, "Accounts, orgs, and permissions") rather than
decided unilaterally — narrowing `/admin` for a scoped admin is a real
design call, not an implementation detail.

**Verified for real:** installed PostGIS/GDAL and a local PostgreSQL 16
in this sandbox (same fallback prior sessions documented), `manage.py
check`/`makemigrations --check` both clean (no model change — this is
permission/validation logic only, no new fields). Four curl-driven test
scripts against a live two-organization, two-property, scoped-vs-
unscoped setup covered: the cross-org property/species rejection; a
scoped member seeing only its own property/activities and being blocked
from creating on an out-of-scope property, a new Property, or a
property-less Sighting; the Sighting↔Activity link and photo endpoints'
scope checks; `Page`'s identical scoping — each with explicit regression
checks that an unscoped account-wide admin's behavior is unchanged. Zero
500s across all runs. Frontend: `tsc -b` and `vite build` clean; a
Playwright run against the live backend+frontend confirmed an unscoped
admin still sees "+ New property" while a scoped member does not, and
that the scoped member's own properties list shows only their own
property, not the org's other one.

**Docs:** `docs/data-model-notes.md` ("Permissions" — replaced a
since-inaccurate line that had claimed property scope was already
enforced), `docs/open-questions.md` (updated the Permissions bullet,
new bullet for the org-console gap), `docs/manual/
roles-and-permissions.md` and `limitations.md` (replaced "stored but not
enforced" with what's now actually enforced and what still isn't),
`docs/manual/properties.md` (note that a scoped member won't see
"+ New property"), `build-questions.md` (new dated entry). Screenshots
not regenerated — nothing existing went from accurate to wrong (a scoped
member is a new session state no existing screenshot depicts); left for
the next regen per this file's own cap policy.

### 2026-08-31 (4) — Scheduled programmer session: built the public-site
### "constrained theme controls" (custom CSS) layer

Scheduled "programmer" session (explicit build authorization per its own
trigger — see `CLAUDE.md`'s "not every scheduled session is queue-only"
rule). Read `docs/open-questions.md` and `build-questions.md` per this
file's own triage rule; the one substantial decided-but-unbuilt item left
in the queue was the public-site custom-CSS layer — direction/shape fully
decided earlier the same day (session (2) below: constrained theme
controls, not raw CSS) and repeatedly confirmed build-ready by two later
PM check-ins (session (3) below). Built it end to end.

**Backend:** new `theme_primary_color`/`theme_background_color`/
`theme_accent_color` (blank-by-default hex fields, `HEX_COLOR_VALIDATOR`
— a 6-digit-hex-only regex that both rejects a `red`/named-color value
*and* is the actual security control preventing CSS injection through
these fields, verified with a `#fff; } body { display:none` payload),
`theme_font` (fixed `ThemeFont` choices: sans/serif/rounded/monospace —
no arbitrary font-family text, no externally-loaded webfont), and
`theme_header_image`/`_content_type` (one banner image, DB-stored like
every other photo) — added identically to both `Organization` and
`Property` (`apps/accounts/theming.py` factors out the shared field/
validator/choices so they're not duplicated by hand; migration
`accounts/0011_organization_theme_accent_color_and_more`). A property's
theme overrides its org's **per field, not all-or-nothing** — leaving one
color blank falls back to the org's own value for just that field.
New session-authenticated `GET/POST/DELETE /api/org/theme-image/` +
`/api/properties/<id>/theme-image/` (editor+ to write; GET lets the admin
UI preview even on a still-private property) and unauthenticated
`GET /api/public/organizations/<id>/theme-image/` +
`/api/public/properties/<id>/theme-image/` (numeric-only, same convention
as every other public-site photo sub-resource) for the actual public
rendering. `OrganizationSerializer`/`PropertySerializer` gained the four
value fields plus a computed `has_theme_header_image` boolean (never the
raw image bytes over JSON).

**Frontend:** new `ThemeEditorPanel` component (color swatches with a
"Reset to default" per field, a font `<select>`, header-image upload/
replace/remove with a live preview) — shared by a new "Theme" section on
`OrgAdminPage` (org-level) and `PropertyMapPage` (property-level, editor+
only, next to the existing Pages section). The actual theming mechanism
on the public site (`frontend/src/utils/theme.ts#publicThemeStyle`) is
just CSS custom-property overrides — `index.css` already routes nearly
everything (backgrounds, buttons, links, cards) through a handful of
variables (`--color-primary`, `--color-bg`, etc.) defined once on
`:root`, so overriding those same variables as an inline `style` on the
outermost `.app-shell--public` element re-themes the whole subtree for
free, no per-component styling logic needed. Two new variables
(`--public-accent`, `--public-font-family`) back the accent-color and
font knobs specifically. `publicHeaderImageUrl()` resolves a property's
own header image first, falling back to its org's, same per-field
independence as the colors.

**Real bug found by testing, not reading the diff:** the header banner
`<img>` had no reserved height, so a Playwright screenshot taken right
after navigation (before the image finished loading) showed nothing at
all where the banner should be — not a rendering bug (the image did load
correctly; `naturalWidth`/`complete` both confirmed it a moment later),
but a real layout-jump risk for a slow connection. Fixed with a
`min-height` + placeholder background on `.public-header-image` so the
space is reserved immediately rather than collapsing to zero until the
image decodes.

**Scope call, not silently skipped:** the header banner is rendered on
the org portfolio page and on an authored page, but deliberately **not**
above a property's Explore/map view — that layout is a fixed-height
split-scroll region (see its own long-standing comment in `index.css`)
that a banner image would need real layout rework to sit above cleanly,
out of scope for this pass; noted in `data-model-notes.md` for whoever
picks that up.

**Docs:** `docs/data-model-notes.md` (new "Constrained theme controls"
subsection), `docs/open-questions.md` and `build-questions.md` (item
marked built; the still-genuinely-open custom-HTML/JS item explicitly
called out as *not* covered by this session or by the earlier
isolated-origin parking — that was about *where* author content runs,
not *whether* to sanitize it, so raw HTML/JS still needs its own explicit
owner confirmation before a future build session ships it), manual
chapters `organization-admin.md` (new "Theme" section),
`properties.md` (property-level Theme section), `public-site.md` (new
"Theme" section describing what a visitor sees), `limitations.md`
(reworded the stale "no custom CSS" bullet — now accurate: constrained
theme controls exist, raw CSS/HTML/JS still doesn't, and isn't a
stepping-stone toward the former).

**Verified for real:** installed PostGIS/GDAL/GEOS system packages and a
local PostgreSQL 16 in this sandbox (same fallback prior sessions
documented — `postgresql-16-postgis-3`/`gdal-bin`/`libgdal-dev` this
time), ran `makemigrations`/`migrate`/`makemigrations --check` clean.
Curl-drove the full new surface directly: valid-hex PATCH, rejected a
named color and the CSS-injection-shaped payload above (both 400 with
the field's own error, not a 500), rejected an invalid font choice,
confirmed a blank value resets to "inherit default", uploaded/served/
deleted both an org and a property header image (confirmed the public
endpoint 404s once deleted), confirmed a private property's theme image
404s on the *public* endpoint while the *authenticated* one still 200s
(admin preview keeps working pre-publish), confirmed cross-org property
theme-image scoping 404s, and confirmed an unauthenticated POST 403s.
Frontend: `tsc -b` and `vite build` clean. Full Playwright run against
the live backend+frontend (installed `playwright@1.62.1` in the
scratchpad, `/opt/pw-browsers` Chromium): signed up, set an org theme
(three colors + a font) and uploaded a header image via the real UI,
confirmed the public org portfolio page's computed background-color and
heading color matched the chosen hex values exactly (not just "looks
different") and the header image loaded with a nonzero `naturalWidth`;
created a property, set **only its accent color** (left primary/
background blank), and confirmed the public property page's Explore view
showed the **org's** background/primary (the fallback working) while
showing the **property's own** accent on its heading (the override
working) — proving the per-field, not all-or-nothing, fallback is real
and not just documented intent. No unexpected console errors beyond the
documented sandbox basemap-tile noise.

**Screenshots:** not regenerated — last regen was 2026-08-29 (within the
once-per-calendar-date allowance today), but the new Theme sections are
additive/below-the-fold on both admin pages and don't touch any selector
`capture.js` uses, so nothing existing went from stale to actively wrong;
left for the next regen per this file's own cap policy.

### 2026-08-31 (3) — Scheduled PM re-fire: build context now fully clear,
### no open questions remain, no notification (redundant same-day)

The "resolve open questions" routine re-fired later the same calendar
date. Project-manager scope only; no live human joined this run. Between
the earlier PM check-in (entry below) and this re-fire, the owner had
joined live and decided the last open design question — the public-site
custom-CSS shape (constrained theme controls, session (2) below) — so as
of this run **no open design questions remain**: re-read
`docs/open-questions.md` and `build-questions.md` in full and found
nothing "can't-be-built-until-you-answer" left. The whole public-site
storytelling feature is decided end to end (pages foundation shipped
2026-08-30; custom CSS/HTML/JS layer all decided, isolated origin
parked) — build-ready pending only an explicit "build this."

**Verified rather than assumed:** `git fetch origin main` — `origin/main`
== this session's assigned branch == `634fce5` (today's CSS-decision
commit); a stale *local* `main` ref briefly looked 29 behind until the
fetch, but origin was current all along (no real divergence — noted so
the next session doesn't re-trip on it). Curl'd the live dev instance:
reachable (`/` and `/api/auth/csrf/` both 200), and
`GET /api/feedback/pull/` still returns "no token configured" —
`HABITAT_FEEDBACK_TOKEN` remains unprovisioned (ops step, unchanged;
routine step 3 stays a no-op). This session's env has no feedback var
either.

**No push notification this run** — deliberately. The one outstanding
item (the feedback token) was already flagged in a notification earlier
today, and the CSS question was answered live by the owner earlier today;
a same-day re-ping about an unchanged, already-known ops gap is fatigue,
not signal. Recorded the "build context fully clear" status in
`build-questions.md` (new dated section) and bumped the feedback-token
re-confirmation note in `docs/open-questions.md`. No code, migrations, or
manual changes.

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
