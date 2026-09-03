# Limitations & known gaps

Habitat is mid-build (Phase 1 complete, with a handful of Phase 2/3 slices
pulled forward — see `/CLAUDE.md`'s "Current phase" section for exactly
what that means). This page collects the user-facing gaps in one place so
they're easy to check before assuming something exists. For the technical
open-question versions of some of these (with more implementation detail),
see `/docs/open-questions.md`.

## Accounts & organizations

- **No org switcher.** If you belong to more than one organization, the
  app always acts as your first membership; see
  [Getting started](getting-started.md#which-organization-am-i-in).
- **No real email delivery configured.** Inviting a new member (see
  [Organization admin](organization-admin.md#adding-a-member)) generates
  a real invite link and *tries* to email it, but no production email
  service is configured in this project yet — the admin portal always
  also shows a **Copy invite link** button as a fallback for exactly this
  reason. A password reset ("forgot password") flow **does** exist — see
  [Your account](account.md) — but it depends on that same missing email
  service, so in practice the reset link is only reachable by reading the
  server's console output. Unlike an invitation, it deliberately has no
  "copy the link" fallback in the admin portal: handing the link back
  would turn the reset form into a way to check whether a given email
  address has an account.

## Roles & permissions

- **A property-scoped admin can't hand off organization settings.** Their
  reach now stops at members scoped to their own properties (see [Roles
  and permissions](roles-and-permissions.md#what-a-property-scoped-admin-can-administer)),
  which also means renaming the organization, changing its public URL
  name or theme, authoring org-level pages, and reviewing feedback need
  an account-wide admin — there's no way to delegate one of those
  individually.
- **Roles are the fixed three.** viewer / editor / admin, optionally
  scoped to properties — no custom roles, and no per-feature permissions
  within a role.

## Records

- **You can't delete your last "finished" workflow state.** Your
  [workflow states](organization-admin.md#workflow-states) are yours to
  add, rename, reorder and delete, with one deliberate exception: at
  least one state must stay marked **Counts as finished work**, because
  that flag is the only thing telling the public map, your dashboard and
  the Activities filter which work is done. Un-flagging or deleting your
  only finished state is refused with an explanation. There's no such
  guard on the starting state — losing that one just means new activities
  start in whichever state is first.
- **Quick log doesn't keep a draft.** Backing out of a
  [quick log](dashboard.md#quick-log) mid-capture discards it. Quick log
  can't put species on an activity or link records — save the record and
  open it from its property to do those.
- **You still can't add species or links while creating a record.** The
  create forms now offer photos right after saving, but species on an
  activity and links between records are still edit-form-only: save
  first, then reopen the record from its property.
- **The activity and sighting lists filter client-side.** The
  [Activities](activities.md#finding-an-activity) and
  [Sightings](sightings.md#finding-a-sighting) pages fetch all your
  records and search them in the browser. Fine at the scale a single
  organization reaches today; it isn't paginated or server-side search.
- **The nav is the same on every page.** A menu that changes with where
  you are was considered and deliberately parked for now.
- **Task assignment notifications are in-app only** — no email or push.
  See [Tasks](tasks.md#notifications).
- **No due dates on tasks.**
- **No soft delete for anything except properties.** Deleting an
  activity, sighting, species, or task is immediate and permanent —
  see [Properties](properties.md#deleting-a-property) for the one place
  a delete is actually recoverable (30 days, admin-restorable).
- **No species merge/dedupe tool.**
- **A species' description is public, and there's no private notes
  field.** The description on the [species list](species.md) is shown to
  visitors on the public site by design; there's nowhere on a species to
  record something only your own members should see.
- **Tasks aren't shown on the public site** — they're an internal work
  item, not public-facing data. (Sighting↔activity links *are* now shown
  publicly — see [Public site](public-site.md).)

## Public site

- **No automatic, species-aware visibility.** A property has a
  [default public/private setting for new sightings](properties.md) an
  admin sets manually (e.g. for a preserve with an at-risk species) — but
  there's no automatic detection of "this species is sensitive" from the
  species list itself, and no location-fuzzing (showing an approximate
  area instead of the exact point) for a public sighting either.
- **No free-form CSS, and custom HTML is off unless it's switched on.**
  Public-site branding is limited to the fixed
  [Theme](organization-admin.md#theme) controls (colors, a font, a header
  image) — there's no free-text CSS field, and that's the deliberate
  final answer for styling rather than a step toward one.
  [Custom HTML pages](public-site.md#custom-html-pages) *do* now exist —
  your own HTML, CSS and JavaScript, run inside an isolated sandbox — but
  they're **off by default**: whoever runs your Habitat installation has
  to enable them, and can switch them off again for a single
  organization, so the Content type choice may simply not appear on your
  page form. A custom HTML page also doesn't inherit your theme, and is
  capped at 512 KB.
- **No content policy for author-published pages.** The sandbox around a
  custom HTML page stops author code reaching Habitat, other
  organizations, or anyone's login — but nothing stops an author
  publishing misleading content to their *own* page's visitors, and no
  written policy says what's allowed. The only remedy today is switching
  custom HTML off for that organization after the fact.

## Platform

- **In-app feedback isn't on by default.** The floating "Send feedback"
  button (for reporting bugs/friction/ideas about Habitat itself) is
  gated by a setting that's typically off on a given Habitat instance
  (e.g. off in production, on in a dev environment) — if you don't see
  it, that's expected, not a bug.
- **No public API yet.** Everything described in this manual is the
  logged-in app and the public *pages* — there is no documented,
  versioned API for third-party consumers. That's Phase 4 work.
- **No rules-engine automation** (e.g. auto-suggesting a sighting↔activity
  link, auto-creating a task from a sighting). Deliberately deferred; see
  `/CLAUDE.md`.
- **No automated tests documented for the frontend**, and backend testing
  is `manage.py test`/pytest-shaped but not comprehensively covered —
  this doesn't affect what you can do in the app, but it's worth knowing
  if something looks broken and you're wondering whether it was caught by
  a test suite.

If you hit a gap that isn't listed here, it's worth checking
`/docs/open-questions.md` before assuming it's a bug — it may be a
deliberately deferred decision rather than an oversight.

---

[← Public site](public-site.md) · [Manual index](README.md)
