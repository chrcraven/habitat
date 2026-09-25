# Your dashboard

The page you land on right after logging in (or signing up) — `/`, also
reachable any time via **Home** in the nav — is a summary dashboard, not a
list of properties. It's meant to answer "what needs my attention" without
having to click into Tasks and every property one at a time.

![The dashboard for a brand-new organization: a welcome heading and an empty-state prompt to draw a first property.](images/dashboard-empty.png)

For a brand-new organization with no properties yet, it's just a prompt to
draw your first one. Once there's real data, it shows up to four sections,
each linking out to the full page that actually handles it:

![A populated dashboard: "Your tasks" with one assigned task and an "All tasks" link, "Planned / in progress activities" listing one planned activity with an "All activities" link, "Recent activities" reading "No completed activities yet" because the only activity here isn't done, and "Recent sightings" listing one sighting.](images/dashboard-populated.png)

- **Your tasks** — open or assigned [tasks](tasks.md) assigned to *you*
  specifically (not the whole organization's task list), newest first, up
  to five. A link to **All tasks** goes to the full [Tasks](tasks.md)
  page. If nothing's assigned to you, this just says so — it doesn't show
  other people's tasks.
- **Planned / in progress activities** — [activities](activities.md) that
  aren't marked done yet, across every property, soonest-planned-first, up
  to five. A link to **All activities** goes to the full
  [Activities](activities.md#finding-an-activity) page. **This section only
  appears when there's at least one** — it's hidden entirely once
  everything's done, rather than showing an empty heading.

  **Worth knowing: this is every activity that isn't done, not only the
  ones still ahead of you.** Habitat has no notion of a planned date having
  passed — nothing anywhere compares a date to today — so an activity
  planned for last November sits in this section exactly like one planned
  for next spring, and because the list is sorted soonest-first, the
  *oldest* slipped work is what fills the five rows. If several things have
  slipped, genuinely upcoming work can be pushed out of this section
  entirely. Use **All activities** and the **Status** filter
  (*Planned / in progress*) to see the whole list.
- **Recent activities** — the most recently logged **completed**
  activities across every property, newest first, up to three. Anything
  still planned appears in the section above instead, not in both.
- **Recent sightings** — the most recently logged [sightings](sightings.md)
  across every property, newest first, up to three.

For the full list of either — with a search box — use the
[Activities](activities.md#finding-an-activity) or
[Sightings](sightings.md#finding-a-sighting) nav entry; the dashboard
shows only the most recent few.

Each activity/sighting row links straight to that record's edit page (on
its own property), the same as opening it from the property's own map
page — the dashboard doesn't add a separate view of the data, just a
cross-property summary of what's already there.

## Quick log

**⊕ Quick log**, at the top of the dashboard, is the fast way to record
something you're standing in front of. It's the one action on an otherwise
read-only page, and it's built for logging on a phone out in the field:
the map gets the whole screen while you place the record, and the form
only appears afterwards.

![The quick-log capture screen: the map fills the whole screen with three points placed inside a property boundary, the hint reading "3 points — this will be an activity area", and Cancel / Next: activity details along the bottom.](images/quick-log.png)

**Where you tap decides what you're logging.** You don't pick a record
type first:

- **One point** → a [sighting](sightings.md).
- **Three or more points** → an [activity](activities.md), covering the
  area they enclose.
- Two points can't enclose an area and are too many for a sighting, so
  **Next** stays disabled until you add a third or undo back to one. The
  hint above the map tells you which you're currently heading for.

**Which property doesn't get asked either** — Habitat works it out from
where you tapped, and your property boundaries are drawn on the map so you
can see what you're standing on. If the spot isn't inside any of your
boundaries, the details step asks you to pick one (and for a sighting you
can leave it blank, which records a sighting with no property).

**📍 Drop pin here** places a point at your device's actual location, so
you can walk an area and drop a pin at each corner instead of tapping a
map you can't see well in daylight. **Undo** and **Clear** work the same
as they do on the drawing forms.

**The map stays where you put it.** Quick log follows your device's
location the whole time you're on this screen, and it zooms to fit your
points when a new one lands outside the current view — but panning or
zooming by hand sticks, rather than being undone a moment later by the
next GPS reading. (Until 2026-09-25 it wasn't: on an account whose
properties have no drawn boundary, every location update snapped the map
back, so on a phone you effectively couldn't pan away from your own
points.)

Then **Next** takes you to a short details step — species and time for a
sighting, type and status for an activity, plus notes and the public flag
for either — and saving drops you on the property that now holds the
record.

**A sighting needs a species, and you can add one right here.** Pick from
your [species list](species.md) if the plant or animal is already on it,
or type a common name into **Or add a new species** and Habitat creates it
as it saves. That matters most on a new account, whose species list starts
empty — you don't have to leave quick log (and lose the point you just
placed) to go and add one first. Typing a name you already have selects
the existing entry rather than creating a second copy of it.

The details step waits for your species list before it appears, so the
picker never shows you an empty list it's still fetching. On a slow
connection you'll see **Loading your species list…** for a moment; if it
can't be fetched at all you get **Retry** rather than a form that would
quietly add a second copy of a species you already have. Either way the
point you placed is still there — **← Back to map** takes you to it.

Two things to know:

- **Backing out discards the capture.** There's no saved draft; if you
  leave mid-flow you start again. A *failed save* is different: the form
  stays put with everything you typed, and pressing **Save** again is
  safe — if the first attempt got as far as creating the species, the
  retry reuses it rather than refusing or making a duplicate.
- **Photos, species on an activity, and linking records aren't here.**
  Quick log gets the record down fast; open it from the property
  afterwards to add the rest. (A *sighting's* species is on the details
  step, as above — it's required, so it has to be.) The per-property
  **+ Activity** / **+ Sighting** buttons and their full forms still exist
  and are unchanged — quick log is an extra way in, not a replacement.
- **You need edit access to see it.** Quick log creates records, so it's
  offered to editors and admins. A viewer sees the dashboard without it —
  see [Roles and permissions](roles-and-permissions.md).

## What this doesn't do (yet)

- Apart from Quick log, it's read-only — a summary, not another place to
  edit anything.
- "Recent" means *most recently logged* (when the record was created),
  not the activity's planned/done date or the sighting's observed-at
  time — those still show in each row's own detail.
- The two Recent sections show three rows each, and that number isn't
  adjustable.
- No per-user customization (reordering sections, changing how many rows
  show, dismissing a task from view without resolving it).

---

[← Getting started](getting-started.md) · [Manual index](README.md) · [Properties →](properties.md)
