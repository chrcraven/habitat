# Public site

Habitat can show a read-only view of an organization's work to anyone,
with no login. This is meant for the "what's happening on this land"
audience — neighbors, land-trust supporters, the curious — separate from
the logged-in app the organization's own members use.

There are two public page shapes, both unauthenticated:

- **Organization portfolio** — `/public/org/<org id>` — lists every
  property that organization has marked public.
- **Property page** — `/public/properties/<property id>` — one property's
  boundary, its public activities, its public sightings, and their
  photos.

From inside the logged-in app, **Public site** in the nav opens your
org's portfolio page in a new tab (a different audience's view, not a
page inside the authed app). The [org admin page](organization-admin.md)
has the same link at the top.

**Organization portfolio page** — lists public properties, no login required:

![The organization portfolio page: "Willow Creek Preserve" with one public property listed, and a "Log in" link in the header.](images/public-org.png)

**Property page** — boundary, activities, sightings, and a breadcrumb back to the portfolio page:

![The public property page: boundary, one activity and one sighting listed below, no edit controls anywhere.](images/public-property.png)

Like the logged-in property map page, the map stays fixed at the top of
the page while the activity/sighting lists below it scroll — the same
"never lose sight of the map" behavior described there.

Activities on the map are styled by whether they're done yet — the same
dashed-orange-for-planned/in-progress vs. solid-green-for-done distinction
as the logged-in [property map page](properties.md#viewing-a-property), with
a small legend explaining it. This is the visitor-facing version of that
same planned-vs-completed distinction — a visitor can tell "planned"
apart from "already done" without reading each activity's status text.

## What controls whether something shows up

Two independent flags, both of which have to be true for a record to
appear publicly — a property with private activities on it doesn't leak
them, and a public activity on a private property doesn't leak the
property either:

1. **The property's own public flag** — set when
   [creating or editing a property](properties.md), default **on**. A
   property with this off doesn't appear on the org portfolio page at
   all, and its direct public-property URL shows "This property isn't
   public, or doesn't exist" instead of any of its data.
2. **Each activity's / sighting's own public flag** — set individually
   per record, default **on**. Even on a public property, an individual
   activity or sighting marked private is left out of its public page.

This two-level design exists specifically so an organization managing one
public property (say, a preserve) and one private one (say, the manager's
own yard) can keep the private one off the public site entirely, rather
than having to mark every record on it private one at a time.

## What the public site does *not* expose

- A **private or nonexistent** property ID returns the same generic "not
  public, or doesn't exist" message either way — deliberately, so someone
  guessing IDs can't use the response to tell "private" apart from "never
  existed."
- No edit/delete controls, no way to log new activities/sightings, no
  private-records toggle (there's nothing to toggle — the public API only
  ever returns public records to begin with).
- The [sighting↔activity link](linking-sightings-activities.md) isn't
  surfaced — connected records show up as separate, unrelated cards.
- URLs are plain numeric IDs — there's no vanity/slug URL
  (`/public/org/my-preserve`) yet.
