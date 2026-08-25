# Organization admin

The **Admin** nav entry (`/admin`) — visible only to members with the
admin role — is where your organization's own settings and membership
live. It's a page inside the app itself, scoped automatically to your own
organization, not Django's separate `/admin` site (which a developer might
use directly against the database, but which isn't org-aware and isn't
the intended path for day-to-day admin work).

A non-admin who navigates to `/admin` directly sees a plain "this page is
for organization admins only" message rather than being redirected away.

![The Organization admin page: org name field, the member list (here, one admin — the account's creator), and the "Add a member" form below.](images/org-admin.png)

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
- **Initial password** — see the important note below
- **Role** — viewer, editor, or admin (defaults to viewer)
- **Property scope** — optionally check specific properties to limit this
  member's role to just those (see [Roles and
  permissions](roles-and-permissions.md#property-scoped-roles) for the
  current enforcement caveat)

> **There is no email-invite flow.** No email backend is configured in
> this project yet, so adding a member works one of two ways:
>
> - **If that email already has a Habitat account** (anywhere — it
>   doesn't have to be in your org), they're simply attached to your
>   organization with the role/scope you set. The password field is
>   ignored in this case.
> - **If it's a brand-new email**, the password you type in **Initial
>   password** becomes their real login password immediately. You're
>   expected to share it with them yourself, out of band (text, in
>   person, whatever) — Habitat doesn't email it anywhere. They can change
>   it themselves afterward from their own [Account](account.md) page —
>   there's just no emailed invite link to get them started.

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
