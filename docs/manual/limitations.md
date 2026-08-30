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
  reason. No password reset ("forgot password") flow either, for the same
  reason.

## Roles & permissions

- **Property-scoped roles are stored but not enforced.** You can check
  specific properties for a member's role in the admin portal, but every
  membership currently behaves as account-wide regardless. See [Roles and
  permissions](roles-and-permissions.md#property-scoped-roles).

## Records

- **No workflow-state editor.** A new organization gets a default
  Planned → In Progress → Done set of activity statuses; there's no UI to
  add, rename, or reorder these — only the two initial "planned"/"done"
  flags and the default three states exist without going into the
  database directly.
- **Task assignment notifications are in-app only** — no email or push.
  See [Tasks](tasks.md#notifications).
- **No due dates on tasks.**
- **No soft delete for anything except properties.** Deleting an
  activity, sighting, species, or task is immediate and permanent —
  see [Properties](properties.md#deleting-a-property) for the one place
  a delete is actually recoverable (30 days, admin-restorable).
- **No species merge/dedupe tool.**
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
- **No custom styling, HTML, or scripting on authored pages.** [Pages](public-site.md#authored-pages-and-the-landing-page)
  are Markdown only — no custom CSS, raw HTML, or JavaScript layer yet.
  That's a separate, still-undecided feature (see `/docs/open-questions.md`,
  "Public site storytelling / custom content") — not a bug, and a
  deliberate security choice for now (author content is sanitized before
  it's shown publicly).

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
