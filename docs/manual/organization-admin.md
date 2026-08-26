# Organization admin

The **Admin** nav entry (`/admin`) — visible only to members with the
admin role — is where your organization's own settings and membership
live. It's a page inside the app itself, scoped automatically to your own
organization, not Django's separate `/admin` site (which a developer might
use directly against the database, but which isn't org-aware and isn't
the intended path for day-to-day admin work).

A non-admin who navigates to `/admin` directly sees a plain "this page is
for organization admins only" message rather than being redirected away.

![The Organization admin page: the member list, a "Pending invitations" section with a just-sent invitation (Copy invite link / Revoke buttons), and the "Add a member" form below.](images/org-admin.png)

## Renaming your organization

A single **Organization name** field with its own **Save name** button.

## Members

The member list is visible to **any** member of the org (so even a viewer
can see who's on the team), but only admins can add, remove, or change
anyone.

### Adding a member

Fill in the **Add a member** form:

- **Email** (required)
- First/last name (optional)
- **Role** — viewer, editor, or admin (defaults to viewer)
- **Property scope** — optionally check specific properties to limit this
  member's role to just those (see [Roles and
  permissions](roles-and-permissions.md#property-scoped-roles) for the
  current enforcement caveat)

What happens next depends on whether that email already has a Habitat
account:

- **If it already has an account** (anywhere — it doesn't have to be in
  your org already), they're attached to your organization immediately
  with the role/scope you set. No invitation step, since they can already
  log in.
- **If it's a brand-new email**, Habitat creates a pending invitation and
  emails an accept link to it. The invitee opens the link, sets their own
  password, and lands in your organization with the role/scope you chose —
  no password to make up and share yourself.

> **No real email delivery is configured in this project yet** (see
> [Limitations](limitations.md)), so the email may never actually arrive.
> Every pending invitation also shows a **Copy invite link** button (see
> below) — if the invitee says they never got anything, copy that link and
> send it to them yourself (text, chat, whatever) instead.

### Pending invitations

A **Pending invitations** section appears between the member list and the
add-member form whenever your organization has any — each shows the
invited email, role, and property scope (if any), plus:

- **Copy invite link** — copies the same accept link the invitation email
  contains, for sharing manually.
- **Revoke** — cancels the invitation (with a confirm prompt) if it was
  sent to the wrong address or is no longer wanted. A revoked link stops
  working immediately.

An invitation also expires on its own after 7 days if nobody accepts it.
Once accepted, it disappears from this list and the person shows up in
**Members** instead. See [Getting started](getting-started.md#joining-an-existing-organization)
for what the invitee sees when they open the link.

### Changing a member's role or property scope

Inline on each member's row — a role dropdown and a checkbox per property.
Changes apply immediately (no separate save button). Subject to the [last
admin protection](roles-and-permissions.md#the-last-admin-safety-rule).

### Removing a member

A **Remove** button per row, with a confirm prompt. Also subject to the
last-admin protection.

## Jumping to the public site

A **View public site ↗** link at the top of the page opens your
organization's [public portfolio page](public-site.md) in a new tab —
useful for checking what it actually looks like to someone who isn't
logged in.
