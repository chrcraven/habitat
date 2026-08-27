# Logging sightings

A **sighting** is a wildlife observation at a single **point** location —
unlike an activity, it's not an area. Different table, different
lifecycle from an activity (see `/docs/data-model-notes.md` if you want
the underlying data-model reasoning), but the two can be
[linked](linking-sightings-activities.md).

## Creating a sighting

From a property's map page, tap **+ Sighting** (editor role and above).
Set the location either by:

- Tapping the map, or
- **📍 Use my location** — a one-shot capture of your device's current
  position (different from the *continuous* location tracking used while
  drawing a property/activity boundary — a sighting only needs one point,
  so it just grabs your position once).

You can tap the map again afterward to adjust the point.

![Logging a new sighting: a point placed on the map, species typed into "Or add a new species", and notes filled in.](images/sighting-new.png)

Fields:

- **Species** — search your organization's [species list](species.md) by
  typing into the field (a type-to-filter picker, not a long dropdown —
  handy once your list has more than a handful of species), or type a
  new common name directly into the "Or add a new species" field to
  create one on the spot (no need to visit the Species page first).
- **Observed at** — date and time; defaults to now.
- **Notes** — free text.
- **Public flag** — same public/private mechanism as a property or
  activity; see [Public site](public-site.md).

Photos and linking to activities are edit-mode-only, same as activities —
save the sighting first.

## Editing a sighting

Editor role and above. Same **Photos** section as activities (upload:
editor+; delete: admin only, 8MB/image-type cap) and the same
[linked-activities panel](linking-sightings-activities.md).

![A saved sighting's edit page: Photos section, and Linked activities showing this sighting connected to the "planting" activity.](images/sighting-edit-linked.png)

## Deleting a sighting

Admin role only, from the property's map page's sighting list — confirm
prompt, no undo.

---

[← Logging activities](activities.md) · [Manual index](README.md) · [Linking sightings and activities →](linking-sightings-activities.md)
