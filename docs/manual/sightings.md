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
  Typing a name you already have — in any casing — selects the existing
  entry instead of adding a second copy, and that holds if the save
  fails and you press **Save** again: the retry reuses the species the
  first attempt created rather than refusing or duplicating it.
- **Observed at** — date and time; defaults to now.
- **Notes** — free text.
- **Public flag** — same public/private mechanism as a property or
  activity; see [Public site](public-site.md). For a brand-new sighting
  this starts from the property's own default (see
  [Properties](properties.md) — "New sightings on this property default
  to public") rather than always starting checked, though it's always
  yours to change before saving; editing an existing sighting keeps
  whatever it already has.

**After you save a new sighting, Habitat offers a photo step** — an
**Add photos** screen with the same camera control the edit page uses.
Add photos and press **Done**, or press **Skip**; either way you land back
on the property.

Linking to activities is still edit-mode-only, same as activities — save
the sighting first.

## Finding a sighting

The **Sightings** nav entry lists every sighting across all your
properties, with a **Search** box that matches the species (common or
scientific name), the property name, and the notes. Selecting a row opens
that sighting's edit form.

A sighting logged with no property has no edit form to open (the form
lives under a property), so it appears in the list as a plain row rather
than a link. If your role is [scoped to specific
properties](roles-and-permissions.md), the list shows only those
properties' sightings.

### What's on the public site

Like the Activities page, this one says how many of your sightings are
publicly visible — *"2 of 7 sightings are on the public site."* — and
badges every row:

| Badge | What it means |
| --- | --- |
| **Public** | Anyone with the link can see this sighting, **including its exact location**. |
| **Private** | You unticked *Show on the public site* on this sighting. |
| **Property private** | Marked public, but its property isn't — so nothing publishes it. |
| **Not public** | The sighting isn't on any property, and the public site only ever shows sightings through a property. |

A **Visibility** dropdown narrows the list to public or non-public — and
because the map plots whatever the list currently shows, choosing **On
the public site** draws exactly the points a stranger can see. That is
the quickest way to check a sensitive sighting isn't among them.

If any sightings are in the **Property private** state, the page counts
them too: publishing that property would put them all online at once.

### Seeing them on a map

Above the list is a map of **whatever the search currently matches** — so
the search box is also the map's control. Clear it and every sighting you
can see is plotted; type a species name and the map narrows to just those
points and zooms to fit them.

This is the way to see one species across your whole account at once. A
property's own map only ever shows that property, so before this page a
species recorded on three properties had nowhere it could be viewed
together. Search for it here and you get exactly those points, wherever
they are.

The line under the search box always says how many of your sightings are
currently plotted. A search that matches nothing leaves the map where it
was and says so, rather than going blank.

The map appears once you have at least one sighting; until then this page
is just the "log your first one" prompt.

![The Sightings page: a map of the matching sightings above a search box and the list, each row showing the species, property and date observed.](images/sightings-list.png)

## Editing a sighting

**Saving or cancelling takes you back where you came from** — the
[Sightings](#finding-a-sighting) list, the dashboard, or the property,
whichever you opened it from. The list's search box and filter are empty
again on return, though; see [Limitations](limitations.md).

Editor role and above. Same **Photos** section as activities (upload:
editor+; delete: admin only, 8MB/image-type cap) and the same
[linked-activities panel](linking-sightings-activities.md). Clicking a
thumbnail opens the photo full size, with ← and → stepping through the
rest and Escape closing it — see [Activities → Photos](activities.md#photos)
for the detail.

![A saved sighting's edit page: Photos section, and Linked activities showing this sighting connected to the "planting" activity.](images/sighting-edit-linked.png)

The form also shows **"Added by …"** above the save button, naming whoever
logged the sighting. Unlike an activity there's no "Last edited by" line —
Habitat doesn't record who last changed a sighting, only who created it.
Each row in the **Linked activities** panel says who made that link.

As with activities, none of this appears on the public site: a visitor
sees the sighting, never who reported it.

## Deleting a sighting

Admin role only, from the property's map page's sighting list — confirm
prompt, no undo.

**Permanent, with no 30-day window and no restore view** (unlike
[deleting a property](properties.md#deleting-a-property)). The prompt
says so, and counts the sighting's photos if it has any, since they're
deleted with it and are the one thing you can't re-enter from memory:

> Delete this sighting? Its 2 photos are deleted too. This can't be undone.

If the delete fails, the reason is shown in red on that sighting's own
card and the row stays put — see [deleting an
activity](activities.md#deleting-an-activity), which behaves identically.

---

[← Logging activities](activities.md) · [Manual index](README.md) · [Linking sightings and activities →](linking-sightings-activities.md)
