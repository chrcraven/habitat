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
- **Task assignment has no notifications.** See [Tasks](tasks.md).
- **No due dates on tasks.**
- **No species merge/dedupe tool.**
- **Sighting↔activity links, and tasks generally, aren't shown on the
  public site.**

## Public site

- **No vanity/slug URLs** — public pages are plain numeric IDs.
- **No sensitive-species-aware visibility.** A public sighting of a
  sensitive species (e.g. something poachable) is exposed exactly like
  any other — there's no automatic location-fuzzing or extra privacy
  gate.

## Platform

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
