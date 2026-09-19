# Tasks

A **task** is a simple, optional, user-to-user to-do — "check out the
bindweed report" — assignable to any member of your organization. (You
can only *assign* a task to a current member, but a task assigned earlier
keeps pointing at that person even if they later leave the organization —
see [When an assignee leaves](#when-an-assignee-leaves).) Unlike
activities and sightings, a task is **organization-wide**, not tied to one
property; that's why it gets its own top-level nav entry ("Tasks") rather
than living inside a property's map page.

A task can optionally originate from a specific sighting or activity (any
one of the org's properties, not just one), or from nothing at all — a
general to-do isn't required to reference anything.

## Viewing tasks

Every member can see the full task list, with a status filter (Open,
Assigned, Resolved, Dismissed). Each task says who created it.

## Creating a task

Editor role and above, via the **+ Add task** form at the bottom of the
page: title (required), description, an assignee (or leave unassigned),
and optionally a sighting or activity it originated from. The assignee
and sighting/activity fields are search boxes (type to filter your
organization's member list or record list) rather than long dropdowns —
handy once either list has grown past a handful of entries. Assigning it
to someone on creation automatically sets its status to "Assigned";
leaving it unassigned sets it to "Open".

![The Tasks page: status filter, task list, and the "Add a task" form with title, description, assignee, and optional sighting/activity origin fields.](images/tasks.png)

## Updating a task

Editor role and above can, inline on each task row:

- **Reassign it** or set it back to unassigned, via the same search-box
  picker — applies immediately, no separate save step.
- **Change its status** the same way.
- **Edit its title/description** via an Edit toggle that opens a small
  inline form.

A member below editor role sees the task's current assignee/status as
plain text instead of the editable controls.

## When an assignee leaves

Removing someone from your organization does **not** touch the tasks
already assigned to them. Those tasks stay assigned, and Habitat keeps
showing the name — deliberately, because that name is the only record of
who was doing the work, and quietly blanking it would lose that.

What changes is that the task now says so. Wherever the assignee appears:

- Editors see their address in the assignee box as before, with a note
  underneath: *"This person is no longer a member of this organization.
  The task stays assigned to them until someone reassigns it."*
- Everyone else sees *"Assigned to them@example.com — no longer a
  member"* in place of the plain "Assigned to …" line.

They are no longer offered in the assignee picker, so you can't newly
assign work to them — only reassign this task to someone else, or clear
it back to unassigned with the **×**. Neither happens on its own; the
task sits there, correctly labelled, until someone decides.

Adding the same person back to the organization restores everything: the
note disappears and the task reads normally again.

## Deleting a task

Admin role only.

## Notifications

Assigning (or reassigning) a task to someone now notifies them — a 🔔
bell in the top bar shows an unread-count badge, and opening it lists your
20 most recent notifications, newest first. Each one names **who**
assigned it to you — "alice@example.com assigned you the task …" — so a
notification arriving out of the blue tells you who to ask about it. The badge counts **every** unread notification you have, not just
the twenty listed — so if it reads higher than the number of rows you can
see, that's accurate rather than a glitch. Clicking one marks it read and
takes you to the Tasks page; a **Mark all read** link clears every unread
notification at once, including any beyond the twenty shown. Assigning a task to
*yourself* doesn't generate a notification — there's nothing to tell you
that you don't already know. This is in-app only for now (no email or
push); see [Limitations](limitations.md).

## What this doesn't do (yet)

- **No email/push notifications** — see "Notifications" above; only the
  in-app bell exists today.
- **No due dates.**
- Tasks aren't shown anywhere on the [public site](public-site.md) — they're
  an internal coordination tool, not a public record type.

---

[← Species list](species.md) · [Manual index](README.md) · [Roles and permissions →](roles-and-permissions.md)
