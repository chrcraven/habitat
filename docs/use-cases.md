# Use Cases

Concrete, early user stories. These are meant to ground the data model and
tech stack discussions (see `data-model-notes.md` and
`tech-stack-options.md`), not to be a final feature spec. None of the UI,
field names, or workflows described here are locked in.

## a. Individual logging planned vs. completed work, with a drawn boundary and photos

> As a homeowner restoring native plant habitat on my property, I want to
> record a planting, seeding, or treatment as an activity tied to a specific
> area of my land — not just a point — so the record reflects the actual
> footprint of the work.

- I draw a shape (polygon or rectangle) on a map of my property marking
  where the work applies — e.g., the back slope where I'm seeding a native
  grass mix, or the bed where I'm treating an invasive shrub.
- I create the activity record before doing the work, mark it **planned**,
  and give it a date (or target date range), an activity type (seeding,
  planting, treatment, or other intervention), and species/treatment
  details (e.g., which native species, or which invasive species and
  treatment method).
- Later, I mark the same record **done** — or a very similar workflow lets
  me log it after the fact as already completed — and attach photos taken
  during or after the work.
- I can add freeform notes at any point (conditions, quantities, follow-up
  needed).
- The distinction between planned and done matters: a planned record should
  be able to show up as "upcoming work" somewhere, not just disappear into
  a private to-do list.
- The record is public by default, but I can flag this specific activity
  private if I don't want it shown on the public view (see (c)) — that
  choice is per-record, not an account-wide setting I'd have to remember
  to toggle elsewhere.

## b. Individual logging a wildlife sighting via device location

> As the same homeowner, I want to log a wildlife sighting — a bird, an
> insect, evidence of an animal — quickly, from my phone, at the location
> where I saw it, without having to draw a shape.

- I capture the sighting at my current device location (a point), not a
  drawn area — sightings are opportunistic and instantaneous, not tied to a
  managed area.
- I record species (if known), a timestamp, and optionally photos and
  notes.
- This is explicitly a different location model than activity records:
  sightings are simple point captures, interventions are drawn-boundary
  areas. They stay separate record types, connected by a direct
  sighting-to-activity link rather than merged (see `data-model-notes.md`
  and (f)).
- Like activities, the sighting is public by default with a per-record
  private flag — which matters more here, since a sighting's exact point
  location can be sensitive for some species (see `open-questions.md`).

## c. Public visitor viewing planned and completed work on a map

> As a visitor to the property — a neighbor, someone walking by, or someone
> viewing the property's public page online — I want to see what's been
> done and what's planned, laid out on a map, without needing an account.

- I see the property's boundary and, within it, the areas where activity
  has happened or is planned, distinguished visually (e.g., completed vs.
  upcoming).
- I can see basic details for each activity — what it is, roughly when, and
  photos if available — without needing to know the underlying data
  structure or log in.
- I do not see any record the land manager has flagged private — activities
  and sightings are public by default, but the per-record flag (see (a),
  (b)) is what this view actually respects.
- This same experience should work whether the "property" is one
  homeowner's yard or a single property within a much larger organization's
  portfolio — the visitor doesn't need to know or care which.

## d. A large land management organization managing many properties and contributors

> As a land trust (or similar organization) with many properties and
> multiple staff/volunteer contributors, I want everyone's activity logging
> to live under one organizational account, spanning many parcels, with
> appropriate permissions per person and per property.

- The organization's account has multiple properties or parcels, each with
  its own boundary and its own activity/sighting history — not one flat
  pool of records.
- Multiple people can log activity under the organization, with role-based
  permissions (e.g., admin/editor/viewer) that can be scoped to specific
  properties — a volunteer might hold an editor role limited to the one
  site they work on, while a program manager holds a role across the whole
  portfolio (see `data-model-notes.md`).
- The organization's public-facing presentation likely needs to work at two
  levels: an overview across all their properties, and a per-property view
  comparable to what an individual homeowner's public page looks like.
- This needs to work without requiring the organization to run separate
  Habitat accounts per property or per staff member — one account,
  internally structured, not many disconnected ones.
- (Still open: exact role definitions and defaults — see
  `open-questions.md`.)

## e. A downstream program consuming Habitat data via API, at small and large scale

> As a third-party program or tool — for example, a regional
> restoration-tracking dashboard or a citizen-science project — I want to
> pull structured activity and sighting data from Habitat via an API,
> whether the source is a single homeowner or a large organization with
> many properties.

- At small scale: I request data for one individual's property (with their
  permission/opt-in) and get back their activity and sighting records in a
  consistent structure — the same structure I'd get from any other
  individual user.
- At large scale: I request data across an organization's full portfolio of
  properties — potentially thousands of records across many parcels — and
  the API holds up in terms of both response structure and practical
  performance (pagination, filtering by date/area/type, etc.).
- The data structure I consume is the same shape regardless of whether the
  producing account has one contributor and one property or many of each —
  there's only one account/org model (see `data-model-notes.md`), so the
  API shouldn't require me to know how big the account behind the data is.
- I can filter/query geospatially — e.g., "activity within this bounding
  area" — not just by owning account or property ID.
- I authenticate with an API key (decided — see `data-model-notes.md` and
  `roadmap.md` Phase 4), not the email/password flow a human user logs in
  with.
- (This use case is explicitly forward-looking — see Roadmap Phase 4. It's
  included now so the data model and API shape are considered from the
  start, not bolted on later.)
- I can also get data out in standard GIS interchange formats (e.g.,
  GeoJSON, Shapefile, KML/GeoPackage export), not just the API's native
  JSON — so Habitat data can be pulled into QGIS, ArcGIS, or another
  program's own GIS pipeline, not only consumed programmatically.

## f. Linking a sighting to a resulting intervention

> As a land manager, when a sighting identifies a problem — e.g., a Field
> Bindweed (an invasive species) sighting logged on my property — I want to
> be able to tie that sighting to the intervention I later plan or carry
> out to address it, so the record shows cause and response, not just two
> disconnected entries.

- The sighting (species, point location, timestamp, photos — see (b))
  stays a sighting; it isn't converted into an activity record.
- I link the sighting directly to the activity that addresses it — a
  many-to-many relationship, not something gated behind any other step
  (see `data-model-notes.md`). A single intervention might address more
  than one related sighting; a sighting might relate to more than one
  activity over time (e.g., an initial treatment and a follow-up).
- I might also create a task first (see (g)) to have myself or a teammate
  look into the sighting before deciding what to link it to — but that's a
  separate, optional step, not a requirement for making the link.
- On the public-facing view, this link is what turns a passive observation
  into a visible story — "reported here, treated on this date" — which is
  also the shape public input (see Phase 5 in `roadmap.md`) is ultimately
  meant to support, even though the sighting in this story didn't have to
  come from a public submission. The same linking need exists for the
  account owner's own sightings today, well before any public-input
  mechanism exists.
- This use case is why sightings and activities are modeled as separate
  record types with an explicit relationship between them, rather than
  either merged into one type or left with no connection at all (see
  `data-model-notes.md`).

## g. Assigning a task to follow up on a sighting

> As a land manager who's part of an organization account with other
> contributors (or working solo), I want to hand a logged sighting off to
> a specific person — myself or a teammate — as a simple to-do, so it
> doesn't just sit there unless someone happens to remember it.

- I create a task, optionally referencing the sighting (or an activity, or
  nothing in particular), and assign it to a contributor on the account —
  myself, or a teammate.
- This is meaningful as soon as an account has more than one contributor,
  which can be true even in Phase 1 if the author has added a second
  person to their own account (see `data-model-notes.md`); otherwise it's
  simple self-assignment.
- Creating the task is something I do deliberately — it isn't an automatic
  side effect of logging a sighting. Not every sighting needs a task.
- Resolving the task (marking it done, or dismissing it) is separate from
  whatever I decide to do about the sighting itself — if that includes
  linking it to an activity, I do that as its own step (see (f)), not as
  something the task resolution triggers automatically.
- This is also a plausible mechanism for review/moderation once public
  sighting submissions exist (Phase 5) — a publicly-submitted sighting
  could generate a task for a land manager to triage — though that's not
  designed in detail yet.

## h. An organization configures a rule to automate sighting handling

> As a land management organization running an ongoing program — e.g.,
> Field Bindweed treatment across several properties — I want new
> sightings that clearly match work already underway to be handled
> automatically instead of manually linked or triaged every time, and I
> want external systems to hear about certain sightings immediately.

- I define a rule: when a sighting matching certain conditions (species,
  location within a property or an existing activity's boundary) is
  logged, take a specific action automatically, rather than a person
  manually creating a task (see (g)) or linking it to an activity (see
  (f)) every time.
- One action: the sighting is auto-linked to an already-planned activity
  that covers it — including one that hasn't started yet — with no manual
  linking step. Useful when the same kind of sighting keeps recurring in
  an area we're already planning to treat.
- Another action: a task is auto-created and auto-assigned to a specific
  person or role, instead of someone having to notice the sighting and
  create the task themselves.
- Another action: a webhook fires to an external system independent of
  either of the above — e.g., notifying our team's internal tools the
  moment a sighting of a specific high-priority species comes in.
- This is explicitly an organization-scale need, not something the author
  needs alone in Phase 1 — a solo user manually linking and (occasionally)
  self-assigning tasks is simple enough not to need configuration. This
  use case describes what that same manual model (task record,
  sighting-activity link) grows into once an organization has volume,
  patterns, and external tools worth automating around (see `roadmap.md`
  and `data-model-notes.md`).
