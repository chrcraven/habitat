# Roles and permissions

Every member of an organization has exactly one role for that
organization: **viewer**, **editor**, or **admin**. Roles are enforced by
the backend on every request — the app's UI only *hides* controls a role
can't use; it doesn't independently decide what's allowed.

## The three roles

| Role | Can do |
|---|---|
| **Viewer** | Read-only: see properties, activities, sightings, species, tasks, and org members. Cannot create, edit, or delete anything. |
| **Editor** | Everything a viewer can, plus create and update: properties, activities, sightings, species, tasks, photo uploads, and sighting↔activity links. |
| **Admin** | Everything an editor can, plus **delete** anything (properties, activities, sightings, species, tasks, photos), plus organization admin: rename the org, add/remove members, change roles, manage property scoping. |

Deleting a photo specifically requires admin even though uploading one
only requires editor — it's treated as more destructive than adding a
record, the same way removing a member is more destructive than adding
one.

## Account creation and your first role

Whoever signs up (`/signup`) becomes **admin** of the brand-new
organization created in that same step. Any *other* member added later —
via the [org admin portal](organization-admin.md) — starts as **viewer**
by default (an admin can set a different role when adding them, or change
it afterward). This is a deliberate "minimal permissions until expanded by
an admin" default.

## Property-scoped roles

A member's role can optionally be **scoped to specific properties**
instead of applying account-wide — set from the [org admin
portal](organization-admin.md), per member: leave every property
unchecked for account-wide access, or check specific ones to limit that
member to just those properties.

> **Current limitation:** property scoping is stored and editable, but
> **not yet enforced**. Every membership today behaves as account-wide
> regardless of which properties are checked. This is a known Phase 1 gap
> — see `/CLAUDE.md` and `/docs/open-questions.md` if you're picking this
> up.

## The "last admin" safety rule

An organization can never end up with zero admins through the admin
portal: both **demoting** an organization's only remaining admin to a
lower role, and **removing** them entirely, are rejected with an error.
You need at least one other admin in place first.
