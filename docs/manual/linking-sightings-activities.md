# Linking sightings and activities

A sighting and an activity can be linked directly to each other — e.g. "I
spotted bindweed here" (a sighting) linked to "treated the bindweed here"
(an activity that followed up on it). This is a direct many-to-many link,
not gated behind creating a [task](tasks.md) first — you can link two
records with nothing else involved.

## Where to find it

Both an activity's edit page ("Linked sightings") and a sighting's edit
page ("Linked activities") show the same panel, from opposite sides of
the same relationship. **Edit-mode only** — like photos, there's nothing
to link to until the record has been saved once.

## Linking a record

The panel lists anything already linked, each with an **Unlink** button
(editor role and above). Below that, a dropdown of *candidates* — every
other sighting/activity **on the same property** that isn't already
linked — plus a **+ Link** button. Candidates are scoped to the current
property because that's the pairing that's actually meaningful in
practice; you can't link across properties from this panel.

## Unlinking

Editor role and above can remove a link from either side — it's treated
as a normal update to the relationship (not a destructive delete), so it
doesn't require admin the way deleting a photo or a whole record does.

## What this doesn't do (yet)

- The link isn't shown anywhere on the [public site](public-site.md) —
  a public visitor sees each activity and sighting as its own card, with
  no indication they're connected.
- There's no rules-engine automation that suggests or creates a link for
  you based on species/location/timing — that's deliberately deferred to
  a later phase (see `/CLAUDE.md`, "Rules engine, API, public input").
