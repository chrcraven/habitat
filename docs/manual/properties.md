# Properties

A **property** is a piece of land your organization manages — a yard, a
preserve, a parcel. An organization can hold any number of properties.
Activities and sightings are always logged against one property.

## Creating a property

From **Properties**, tap **+ New property** (or the equivalent add
control). You'll land on a map:

![Drawing a new property's boundary: four tapped points forming a shape, a "Back Meadow" name field below, and Drop pin/Undo/Clear controls under the map.](images/property-new.png)

- **Draw the boundary** by either tapping points directly on the map, or
  — if your device shares its location — tapping **📍 Drop pin here** to
  drop a vertex at your actual current position. You can mix both freely:
  tap a few points on the map, walk somewhere and drop a pin, tap some
  more. Each placed point shows as a small marker immediately so you get
  feedback even before there are enough points (3+) to preview the filled
  shape.
- **Undo** removes the last point; **Clear** removes them all.
- The boundary is **optional at creation time** — you can save a property
  with just a name and draw the boundary later by editing it.
- **Name** the property.
- **"Show this property on the public site"** — checked by default. This
  is the property-level half of Habitat's public/private control; see
  [Public site](public-site.md) for how it combines with each individual
  activity/sighting's own public flag.

Requires **editor** role or higher. See
[Roles and permissions](roles-and-permissions.md).

## Viewing a property

![A property's map page: its drawn boundary, an activity and a sighting plotted on the map, the visibility toggles, and the Activities/Sightings lists below with Edit/Delete controls.](images/property-map-with-records.png)

Tapping a property opens its map page: the drawn boundary, its activities
and sightings (blue) plotted on the map, and two lists below. Activities
are colored by whether they're done yet — a small legend on the map
explains the two styles:

- **Planned / in progress** — dashed orange outline, light orange fill.
  Anything not marked done, including a custom workflow's in-between
  states (e.g. "In Progress"), gets this styling.
- **Done** — solid green outline, light green fill.

Two toggles above the lists:

- **Show private records too** — by default the map/lists show only
  records marked public; check this to also see private ones. This is
  about what *you* see while logged into your own org's app — separate
  from the public site, which only ever shows public records regardless
  of this toggle.
- **Show my current location on the map** — off by default; turns on a
  "you are here" marker (a different style from the sighting dots, so
  they're not confused) using your device's live location. Off by default
  deliberately, since this is a *viewing* page — the drawing pages
  (below) turn location tracking on automatically instead, since that's
  the whole point of being there.

## Editing a property

Editor role or higher can edit a property's name, boundary, and public
flag from the same map-drawing UI described above — it opens already
zoomed to the existing boundary and pre-loads its current points so you
can add to or adjust the shape rather than starting over.

## Deleting a property

Admin role only. Deleting a property **also deletes its activities and
sightings** — you get a confirmation dialog that says so before it
happens. There's no undo.
