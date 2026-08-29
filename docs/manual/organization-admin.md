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

## Choosing your public URL name

Below the name is a **Public URL name** field (a "slug") — the short,
readable part of your [public site](public-site.md) address. If your URL
name is `willow-creek-preserve`, your public portfolio lives at
`/public/willow-creek-preserve`, and each property sits under it (e.g.
`/public/willow-creek-preserve/north-meadow`).

- It's generated automatically from your organization name when the
  account is created, so there's always a working public URL without you
  doing anything.
- To change it, type a new one (lowercase letters, numbers, and hyphens)
  and press **Save URL name**. Leaving it blank and saving regenerates it
  from the current organization name.
- If the name you pick is already taken by another organization, or is a
  reserved word, you'll be asked to choose a different one.
- The older numeric-ID address keeps working too, so a link you shared
  before changing the URL name won't break.

## Public QR code

Under the URL name is a **Public QR code** generator — a scannable code
pointing at your organization's public site, for a sign, a flyer, or a
card.

- Press **Generate QR code** to create it, then **Download PNG** to save
  it.
- Optionally choose a **Center image** (e.g. your logo) to embed in the
  middle of the code before generating — the code uses a high
  error-correction level so it still scans with the image over it.
- Each property has its own QR code too, on the property's page (see
  [Properties](properties.md)).

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
- **Resend** — re-sends the invitation email using the *same* link (so a
  copy already shared or received still works), and resets its 7-day
  clock — the fix for an invitation that expired before anyone accepted
  it, without having to revoke it and fill out "Add a member" again from
  scratch.
- **Revoke** — cancels the invitation (with a confirm prompt) if it was
  sent to the wrong address or is no longer wanted. A revoked link stops
  working immediately.

An invitation also expires on its own after 7 days if nobody accepts it —
shown with an "(expired)" flag next to it rather than being removed, so
it stays visible to revoke or resend rather than silently vanishing. Once
accepted, it disappears from this list and the person shows up in
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

---

[← Roles and permissions](roles-and-permissions.md) · [Manual index](README.md) · [Your account →](account.md)
