# Tasks

A **task** is a simple, optional, user-to-user to-do — "check out the
bindweed report" — assignable to any member of your organization. Unlike
activities and sightings, a task is **organization-wide**, not tied to one
property; that's why it gets its own top-level nav entry ("Tasks") rather
than living inside a property's map page.

A task can optionally originate from a specific sighting or activity (any
one of the org's properties, not just one), or from nothing at all — a
general to-do isn't required to reference anything.

## Viewing tasks

Every member can see the full task list, with a status filter (Open,
Assigned, Resolved, Dismissed).

## Creating a task

Editor role and above, via the **+ Add task** form at the bottom of the
page: title (required), description, an assignee (or leave unassigned),
and optionally a sighting or activity it originated from. Assigning it to
someone on creation automatically sets its status to "Assigned"; leaving
it unassigned sets it to "Open".

![The Tasks page: status filter, task list, and the "Add a task" form with title, description, assignee, and optional sighting/activity origin fields.](images/tasks.png)

## Updating a task

Editor role and above can, inline on each task row:

- **Reassign it** or set it back to unassigned, via a dropdown — applies
  immediately, no separate save step.
- **Change its status** the same way.
- **Edit its title/description** via an Edit toggle that opens a small
  inline form.

A member below editor role sees the task's current assignee/status as
plain text instead of the editable controls.

## Deleting a task

Admin role only.

## What this doesn't do (yet)

- **No notifications.** Assigning a task to someone doesn't email, push,
  or otherwise ping them — they only find out by checking the Tasks page
  themselves.
- **No due dates.**
- Tasks aren't shown anywhere on the [public site](public-site.md) — they're
  an internal coordination tool, not a public record type.
