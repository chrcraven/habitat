# Species list

Habitat doesn't look species up against an external taxonomy (GBIF, USDA
PLANTS, etc.) — every organization keeps its **own** species list, and
sightings (and eventually activities) are logged against entries on that
list.

## Viewing the list

**Manage → Species** — every member can view it, regardless of
role. A **Search** box above the list filters it by common or scientific
name as you type (once there's more than one species to filter) — handy
once the list grows past a screenful.

**Only what's blooming today** is a second filter, and it's the reason the
bloom period below is worth filling in: tick it and the list narrows to
species whose bloom period covers today's date. It handles a period that
runs through the new year correctly, so a November-to-February bloomer
shows up in January.

![The Species page: the add-species form at the top, and a list of the organization's species below, each with Edit/Delete.](images/species.png)

## Adding a species

Editor role and above, from the form at the top of the page:

- **Common name** (required) and **scientific name** (optional).
- **Description** — free text. **This is shown publicly**: visitors see it
  wherever the species appears on your [public site](public-site.md), and
  the form says so under the field. Don't put anything here you'd only
  want your own members to read.
- **Bloom starts** / **Bloom ends** — a month and a day each. There's no
  year to pick, because a bloom period repeats every year. Set both or
  neither.

  A period that **runs through the new year** is fine — for a species that
  blooms November to February, set the start to November and the end to
  February, in that order. Habitat reads it correctly rather than treating
  it as an error.

You don't have to come here first, either — the
[sighting form](sightings.md) lets you type a brand-new common name
directly while logging a sighting, which creates the species entry on the
spot (with no description or bloom period; add those here afterwards).

## Editing or deleting a species

- **Edit** (common name, scientific name, description, bloom period) —
  editor role and above, inline on each row.
- **Delete** — admin role only, with a confirm prompt.

There's no merge/dedupe tool if two similar entries get created by
accident (e.g. via the quick-add-while-logging-a-sighting path) — you'd
need to edit one and manually reassign or delete the other by hand today.

---

[← Linking sightings and activities](linking-sightings-activities.md) · [Manual index](README.md) · [Tasks →](tasks.md)
