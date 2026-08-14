# Logging activities

An **activity** is restoration or management work done on a property —
seeding, planting, a treatment, removal, monitoring, maintenance, a
general "intervention", or "other". Unlike a sighting (a single point), an
activity is drawn as a **shape** — the area the work covers.

## Creating an activity

From a property's map page, tap **+ Activity** (visible to editor role and
above). You'll draw the area the same way you draw a property boundary —
tap the map or **📍 Drop pin here** to add vertices, **Undo**/**Clear** to
fix mistakes. An activity's shape needs **at least 3 points** before it
can be saved (a property's boundary can be saved with none — an activity's
can't, since the shape *is* the record).

Fields:

- **Activity type** — seeding, planting, treatment, removal, monitoring,
  maintenance, intervention (general), or other.
- **Status** — drawn from your organization's own workflow states (see
  [below](#status-workflow)), not a fixed list.
- **Date planned** / **Date done** — both optional, independent dates.
- **Notes** — free text (conditions, quantities, follow-up needed, etc.).
- **Public flag** — "Show on the public view" — same public/private
  mechanism as a property or a sighting; see [Public site](public-site.md).

Photos and linking to sightings are **only available once the activity is
saved** (edit mode) — there's nowhere to attach them to yet on the create
form. Save the activity first, then reopen it to edit.

## Status workflow

Every organization gets a default three-state workflow when it's created —
**Planned → In Progress → Done** — but the set of statuses is *your
organization's own*, not a fixed enum: exactly two of the states are
flagged specially (which one counts as "planned" and which counts as
"done"), and anything in between is up to you. There's currently no UI to
add/rename workflow states beyond the default set — that would need to
happen directly in the database (Django admin) today.

## Editing an activity

Editor role and above. The edit form reopens with the drawn shape already
loaded and zoomed to.

### Photos

Once an activity exists, its edit page has a **Photos** section: a grid of
thumbnails plus a **+ Photo** control that opens your device's camera
(rear camera preferred on a phone) or file picker. Anyone with editor role
can upload; **removing** a photo requires **admin** role — treated as a
more destructive action than adding one. Photos are capped at 8MB each and
must be an image file.

### Linked sightings

Also edit-mode-only — see
[Linking sightings and activities](linking-sightings-activities.md).

## Deleting an activity

Admin role only, from the property's map page (not the edit form) — each
activity row in the list has its own **Delete** button with a confirm
prompt.
