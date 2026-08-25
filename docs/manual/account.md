# Your account

The **Account** nav entry (`/account`) is where you manage your own login —
today, that's just changing your password. It's available to every logged-in
member regardless of role, since it only ever acts on your own account, not
anyone else's.

![The Account page: your email, and a Change password form with current/new/confirm password fields.](images/account.png)

## Changing your password

Fill in:

- **Current password** — required, so someone who's grabbed your open
  session (but not your password) can't lock you out by changing it out
  from under you.
- **New password** and **Confirm new password** — must match, and must pass
  the same strength rules as signup (not too short, not too common, not
  entirely numeric).

You stay logged in after a successful change — no need to log back in.

This is the page to point a newly-added member at once they've logged in
with the initial password an admin set for them (see [Organization
admin](organization-admin.md#adding-a-member)) — it's the only in-app way
to change a password, since there's no "forgot password" / email-reset flow
yet.
