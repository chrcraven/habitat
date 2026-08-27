# Your dashboard

The page you land on right after logging in (or signing up) — `/`, also
reachable any time via **Home** in the nav — is a summary dashboard, not a
list of properties. It's meant to answer "what needs my attention" without
having to click into Tasks and every property one at a time.

![The dashboard for a brand-new organization: a welcome heading and an empty-state prompt to draw a first property.](images/dashboard-empty.png)

For a brand-new organization with no properties yet, it's just a prompt to
draw your first one. Once there's real data, it shows up to four sections,
each linking out to the full page that actually handles it:

![A populated dashboard: "Your tasks" with one assigned task, "Planned / upcoming activities" and "Recent activities" each listing an activity, and "Recent sightings" listing one sighting.](images/dashboard-populated.png)

- **Your tasks** — open or assigned [tasks](tasks.md) assigned to *you*
  specifically (not the whole organization's task list), newest first, up
  to five. A link to **All tasks** goes to the full [Tasks](tasks.md)
  page. If nothing's assigned to you, this just says so — it doesn't show
  other people's tasks.
- **Planned / upcoming activities** — [activities](activities.md) that
  aren't marked done yet, across every property, soonest-planned-first.
  **This section only appears when there's at least one** — it's hidden
  entirely once everything's done, rather than showing an empty heading.
- **Recent activities** — the most recently logged activities across every
  property (regardless of status), newest first.
- **Recent sightings** — the most recently logged [sightings](sightings.md)
  across every property, newest first.

Each activity/sighting row links straight to that record's edit page (on
its own property), the same as opening it from the property's own map
page — the dashboard doesn't add a separate view of the data, just a
cross-property summary of what's already there.

## What this doesn't do (yet)

- It's read-only — a summary, not another place to edit anything.
- "Recent" means *most recently logged* (when the record was created),
  not the activity's planned/done date or the sighting's observed-at
  time — those still show in each row's own detail.
- No per-user customization (reordering sections, changing how many rows
  show, dismissing a task from view without resolving it).

---

[← Getting started](getting-started.md) · [Manual index](README.md) · [Properties →](properties.md)
