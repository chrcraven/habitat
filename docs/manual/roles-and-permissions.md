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
via the [Manage section](organization-admin.md) — starts as **viewer**
by default (an admin can set a different role when adding them, or change
it afterward). This is a deliberate "minimal permissions until expanded by
an admin" default.

## Property-scoped roles

A member's role can optionally be **scoped to specific properties**
instead of applying account-wide — set from the [Manage
portal](organization-admin.md), per member: leave every property
unchecked for account-wide access, or check specific ones to limit that
member to just those properties.

A property-scoped member only ever sees (and can only create or change
records on) their own properties — that property's activities, sightings,
and authored pages. Properties, activities, and sightings outside their
scope simply don't appear in any list, the same as if they didn't exist.
Two things a property-scoped member can't do at all, regardless of role:
create a brand-new property (there's nothing yet to scope it to — an
admin creates it and adds them to it instead), or create a sighting with
no property attached (it would be invisible to them, and every other
scoped member, immediately after creating it). Species, tasks, and an
org's workflow states stay visible/usable account-wide even for a
scoped member — they aren't tied to one property in Habitat's data model.

### What a property-scoped admin can administer

A property-scoped **admin** (an unusual setup — most admins are
account-wide) administers *their own properties*, not the organization.
In the [Manage section](organization-admin.md) they see a shorter menu:

- **Members**: the members scoped to their own properties, plus
  themselves. A member counts as theirs only if *every* property that
  member is scoped to is one the admin manages — someone scoped to a
  property the admin doesn't manage stays out of reach, as does anyone
  with account-wide access.
- **Adding a member** works, but the new member has to be scoped to at
  least one of the admin's own properties. A property-scoped admin can't
  add an account-wide member, can't widen an existing member's scope past
  their own properties, and can't widen their own.
- **Pending invitations** follow the same rule — they see, resend and
  revoke only invitations scoped inside their own properties.
- **Organization settings are hidden**: the organization's name, its
  public URL name, its theme and header image, org-level pages, and the
  feedback list are all handled by an account-wide admin. Everything at
  the *property* level — a property's own theme, pages, QR code, recently
  deleted properties — still works normally for the properties they
  manage.

## The "last admin" safety rule

An organization can never end up with zero **account-wide** admins
through Manage: demoting an organization's only remaining
account-wide admin, limiting them to specific properties, and removing
them entirely are all rejected with an error. You need at least one other
account-wide admin in place first. A property-scoped admin doesn't
satisfy this rule — they can't administer the organization itself, so an
organization left with only scoped admins would have no way back.

---

[← Tasks](tasks.md) · [Manual index](README.md) · [Manage →](organization-admin.md)
