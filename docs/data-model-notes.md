# Data Model Notes

This is early, deliberately unlocked thinking about what Habitat's core
records need to capture. It's written as open questions and options, not a
schema. Nothing here should be read as decided — see `open-questions.md`
for the running list of things this doc raises but doesn't resolve.

## Activity record

An "activity" is the individual land manager's core unit of work: a
seeding, planting, treatment, or other intervention. See
`use-cases.md` (a) for the motivating story.

Likely needed:

- **Activity type.** Seeding, planting, treatment, intervention (general
  catch-all), possibly others (removal, monitoring-only, maintenance?).
  Open question: fixed enum vs. extensible/user-defined types — a large
  organization may want treatment categories a single homeowner never
  needs, and vice versa.
- **Status / lifecycle.** At minimum, **planned** vs. **done** — this
  distinction is a hard requirement, because planned items need to feed a
  public "upcoming/in-progress work" view, not just a completed-work log.
  Beyond that pair, the exact state set is undecided. Candidates: planned →
  in-progress → done, plus maybe cancelled/abandoned, or on-hold. Options
  range from a simple fixed enum to a small configurable workflow (useful
  for an organization with its own process, overkill for a single
  homeowner). See `open-questions.md`.
- **Geometry, not just a point.** The area an activity/intervention applies
  to is a user-drawn shape — polygon, rectangle, or other geometry — not a
  single coordinate. This is a first-class modeling difference from
  sightings (below) and has real implications for storage and querying
  (see "Geospatial data handling" section).
- **Date(s).** At least one date (when planned for / when done). Possibly a
  range (start/end) for multi-day or ongoing work, and a separate
  "recorded on" timestamp vs. "activity date" — those aren't always the
  same (e.g., logging a planting from three days ago).
- **Species / treatment details.** For a planting or seeding: species
  (single or multiple, with quantities?). For a treatment: what was
  treated (target species, e.g., an invasive) and method/product used.
  **Direction: structured, reference-backed species data** — species
  fields should resolve against a reference list/taxonomy (e.g., a
  regional native plant database, or an existing standard like GBIF or
  USDA PLANTS) rather than staying free text, since that's what makes
  species data useful across the platform later (public display,
  filtering, and linking a sighting like Field Bindweed to the treatment
  that addresses it — see below). Free text likely still has a role as a
  fallback/detail field alongside the structured pick. Which reference
  source(s) to use is still open — see `open-questions.md`.
- **Photos / media.** One activity record should support multiple photos,
  attachable at creation or added later (e.g., before/after). Likely also
  needs basic metadata per photo (captured date, maybe which
  planned-vs-done state it corresponds to).
- **Notes.** Freeform text for anything structured fields don't capture.
- **Ownership / linkage.** Which account and which property/parcel (see
  below) the activity belongs to, and who (which user, under a
  multi-contributor account) logged or last edited it.
- **Public visibility.** **Decided: activity records are public by
  default, with a per-record public/private flag.** The public-facing view
  (`use-cases.md` (c)) is a core part of the vision, not an opt-in
  afterthought — but every individual activity record can be flagged
  private, overriding the default for that one record. This isn't only an
  account- or property-wide toggle; visibility is a field on the record
  itself. Still open: whether the flag is binary (public/private) or has
  more states, who can set/change it, and whether it's available from
  Phase 2 or added later — see `open-questions.md`.

## Sighting record

A "sighting" (e.g., a wildlife observation) is deliberately modeled
differently from an activity — see `use-cases.md` (b).

Likely needed:

- **Species.** What was observed — same structured/reference-backed
  direction as activity records (above). Sightings and activities should
  almost certainly share the same species reference list/taxonomy, since
  that shared reference is exactly what makes linking a sighting to a
  responding activity (below) meaningful — e.g., a Field Bindweed sighting
  and a Field Bindweed treatment referring to the same species record, not
  two independently-typed strings.
- **Point location.** Simple device-location capture — a single
  coordinate, not a drawn shape. This is the key structural difference from
  activity records.
- **Timestamp.** When the sighting occurred (which may differ from when it
  was logged, if entered after the fact).
- **Photos.** Same general need as activities — one or more photos
  attachable to the record.
- **Notes.** Freeform text, same as activities.
- **Public visibility.** Same per-record public/private flag as activity
  records, public by default. Sightings raise a sharper version of the
  privacy question, though: reports of sensitive or at-risk species (e.g.,
  an endangered species' exact location) are a well-known case where
  public geolocation data can cause real harm (poaching, disturbance,
  collection). The per-record flag covers the mechanism (a sighting can be
  marked private), but not the harder question of *default behavior* for
  sensitive species — should a species known to be sensitive auto-suggest
  or auto-set private, rather than relying on whoever logs the sighting to
  remember? Not resolved — see `open-questions.md`.

### Do sightings and activities share a data model?

**Decided: separate tables/record types.** Sightings and activities have
different location models (point vs. geometry) and different lifecycles (a
sighting has no "planned" state), so they don't share a single schema.
They still share conventions — photo attachment, account/property linkage,
species reference, visibility — even as separate types.

**But they need an explicit relationship: sightings can lead to
activities.** A sighting that identifies a problem — e.g., someone logs a
Field Bindweed (an invasive species) sighting — is exactly the kind of
input that should be able to inform, and later be linked to, the planned
or completed intervention that addresses it (see `use-cases.md` (f)). This
applies to the account owner's own sightings well before any public
submission mechanism exists (Phase 5), and is part of why public input
matters at all: it's the "reported → responded to" loop the public-facing
view can eventually show.

**Decided: that link is populated by a task, not created directly.**
Rather than a land manager linking a sighting straight to an activity, a
sighting spawns a **task** — an assignable work item — and it's the
resolution of that task that actually creates the sighting ↔ activity
link (or decides no activity is warranted). See "Task record" below for
the full shape of this. This resolves the "manual vs. automatic" and
"does the sighting's status change" questions from earlier drafts of this
doc: linking happens through the task's resolution, and a task carries its
own status independent of the sighting itself.

Still open (tracked in `open-questions.md`):

- Is the sighting ↔ activity link (as populated via resolved tasks)
  one-to-one or many-to-many? (One intervention might address several
  reported sightings; one sighting might relate to more than one activity
  over time, e.g. an initial treatment and a follow-up.)
- Should the public-facing view surface this link (e.g., "reported by a
  visitor, treated on this date")? That pairing is a good showcase of the
  public-input → management-action loop the project is ultimately aiming
  for.

## Task record

A sighting on its own doesn't put anything on anyone's plate — it just
sits there. A **task** is what turns "a sighting was logged" into
"someone is going to decide what, if anything, to do about it." It's the
assignable work item that sits between a sighting and the activity that
eventually addresses it (see `use-cases.md` (g)).

Motivating example: a Field Bindweed (invasive species) sighting is
logged. That spawns a task, assigned to a contributor on the account.
Resolving the task is what actually creates a planned treatment activity
(or attaches the sighting to one that already exists) — the sighting
itself never becomes an activity; the task is the bridge.

Likely needed:

- **Origin.** What spawned the task — almost always one or more sightings,
  though a task should probably also be creatable directly, without a
  triggering sighting (a land manager just deciding "we should treat this
  area"). A task can plausibly originate from **more than one sighting**
  — e.g., several people independently reporting the same patch of an
  invasive — in which case resolving the task links all of them to
  whichever activity it results in.
- **Assignment.** Which contributor on the account the task is assigned
  to. For a single-contributor account (the author, in Phase 1), this is
  trivially self-assignment — effectively a personal to-do generated from
  a sighting. For a multi-contributor organization, this is the real
  point: routing "something was observed" to a specific person
  responsible for triaging it.
- **Status / lifecycle.** At minimum: open (needs triage) → assigned →
  resolved, plus a dismissed/no-action-needed outcome — not every sighting
  warrants an activity. Exact states TBD (see `open-questions.md`). This
  is a separate lifecycle from an activity's planned/in-progress/done
  status: a task's job is to end in a decision, not to represent land work
  itself.
- **Resolution.** How a task gets closed out. At least three outcomes need
  to be representable:
  1. **Creates a new activity** — the task results in a new planned (or
     already-done) activity record, and its originating sighting(s) get
     linked to it.
  2. **Links to an existing activity** — the sighting(s) the task
     represents turn out to be covered by work that's already planned or
     underway, so the task attaches them to that activity instead of
     spawning a redundant one.
  3. **Dismissed** — no activity, no action; the task is closed without
     creating a link.

This is also the natural place for **moderation to live** once public
input exists (Phase 5, `roadmap.md`): a public-submitted sighting spawning
a task rather than immediately becoming actionable gives a land manager a
review step before it turns into (or attaches to) real planned work. That
isn't designed in detail yet, but the task mechanism introduced here (for
the account owner's own sightings, starting in Phase 1) is meant to be the
same mechanism that carries that later — not a separate system bolted on
in Phase 5.

Open questions this raises (tracked in `open-questions.md`):

- Exact status/lifecycle states for a task.
- Whether a task is a *required* intermediary (every sighting-to-activity
  link must pass through a resolved task) or an *optional* one (a land
  manager can also directly link a sighting to an activity without a
  formal task). Phase 1's single-contributor case argues for
  optional/lightweight, since ceremony matters less with one person;
  larger organizations may want it closer to required, so sightings don't
  fall through the cracks.
- Notification mechanism when a task is assigned to someone.
- Whether tasks have any public visibility at all (probably not — they're
  an internal work item, distinct from the sightings and activities that
  are public by default) or stay account-internal always.

## Automation: rules engine (early idea)

Phase 1's sighting → task mechanism (above) is really the simplest
possible rule: "every sighting spawns a task." Once an account has more
sightings, more contributors, or an established program (Phase 3+), a
fixed one-size-fits-all rule stops being enough — a business rules engine
generalizes that mechanism into something an account can configure.

Motivating examples: an organization wants "any sighting of Field
Bindweed within Property X's treatment zone automatically attaches to the
treatment activity already planned for that area" — no human triage
needed for a sighting that clearly matches an existing plan. Or: "any
sighting of an endangered species should immediately call our internal
notification webhook," independent of whether it also becomes a task.

Likely shape, very early:

- **Trigger.** An event a rule reacts to — at minimum, "a sighting is
  logged," possibly narrowed by conditions: species, geometry/proximity
  (within a property, within a given activity's boundary, within some
  radius), or other sighting attributes. Could eventually extend beyond
  sightings (e.g., an activity's status changing to done).
- **Condition(s).** What narrows a trigger to a specific rule — species
  match, location match (e.g., "sighting falls within this planned
  activity's geometry"), maybe a threshold (e.g., "3+ sightings of the
  same species in the same area").
- **Action(s).** What the rule does once triggered. At least three kinds
  worth naming now:
  1. **Create a task** — the default Phase 1 behavior, generalized: a rule
     could instead suppress task creation for conditions that don't
     warrant it, or create a task with a specific assignee pre-filled.
  2. **Auto-assign to an existing planned activity** — skip manual triage
     entirely when a sighting clearly matches work that's already planned,
     even work that's still in "planned" (not yet started) status. This is
     the "future planned action" auto-assignment case: a rule recognizing
     that an incoming sighting belongs to an activity that already exists,
     without a person having to make that connection by hand.
  3. **Call a webhook** — notify an external system/URL when the rule
     fires, independent of anything happening inside Habitat. This is the
     push-based counterpart to the pull-based public API (Phase 4,
     `roadmap.md`) — useful for an organization's own internal tooling
     (e.g., a Slack notification, a ticketing system) as well as, later,
     third-party integrations.

This is explicitly **not** a Phase 1 concern — Phase 1 needs exactly one
implicit rule ("every sighting spawns a self-assigned task"), hardcoded.
But the task/sighting/activity model above should be designed so that
hardcoded rule doesn't have to be ripped out later to make room for a real
rules engine — it's the rules engine's simplest possible configuration,
not a different mechanism. Real configurability is a Phase 3/4-era
concern, likely alongside organization-scale permission depth and the
public API (see `roadmap.md`).

Open questions (tracked in `open-questions.md`):

- Who can define rules — any contributor, or only account
  admins/managers? Per-property or account-wide?
- How much rule complexity is exposed to users vs. built-in system
  defaults (e.g., "sighting → task" as a fixed default, with true
  conditional logic reserved for larger organizations)?
- Webhook reliability concerns: retries, delivery guarantees, payload
  signing/authentication, rate limiting — real integration-surface
  questions, not just a data-model detail.
- Does auto-assignment to an existing planned activity ever happen without
  any human review, or does it always still produce a task/notification
  for someone to confirm (even if pre-resolved)? A real tradeoff between
  convenience and the risk of mis-linking a sighting to the wrong planned
  work.

## Accounts / ownership, single individual → multi-user organization

**Decided: one Habitat instance/account corresponds to one organization or
manager.** A single homeowner's account today happens to have one
contributor, but the account itself is not a "single-user" type — it's an
organization that currently has a headcount of one. There is no separate
"individual account" type with different capabilities, and no migration
step required to "become" an organization: **an org account supports
multiple users from the moment it's created**, whether or not it uses that
capability right away. The account model is the same shape whether it
represents one person managing one yard or a land trust managing many
properties and staff. This resolves the earlier open question of
individual-vs-org account types: there's one account/org model, not two,
and it holds up across the full range in `use-cases.md` (a single
homeowner, another individual homeowner, and a large organization — use
case d).

Rough shape under consideration:

- **Account (organization).** The top-level owner of data. Every Habitat
  account is, structurally, an organization — a single homeowner's account
  and a land trust's account are the same kind of thing, just with
  different numbers of properties and contributors. Open question: how
  much organization-management UI (invites, roles, multiple properties)
  gets exposed to a one-person account by default — the underlying model
  should be uniform, but the *interface* for a single homeowner shouldn't
  force them through org-management screens they don't need yet.
- **Property / parcel.** A piece of land with a boundary, owned by an
  account. **Multiple properties are supported under a single account from
  the start** — a single homeowner might have exactly one property (their
  own yard), while a land trust has many. Activities and sightings are
  linked to a property, and through it to the owning account.
- **Users / contributors.** One or more people who can log activity under
  an account — **multi-user support is a property of every account, not a
  separate tier.** The author's own account may have just one contributor
  (the author) at first, but a second contributor (a spouse, a helper) can
  be added to that same account at any time, with no change in account
  type. For a larger organization, this is used more heavily from day
  one: multiple staff/volunteers, not all with the same access.
- **Permissions.** Still open in detail — see `open-questions.md`. Likely
  needs at least: who can create/edit records, and at what scope
  (account-wide vs. specific properties). A larger organization probably
  needs per-property permission scoping (use case d); a single-person
  account needs approximately none of this complexity surfaced to them,
  even though the underlying model supports it.

The guiding constraint remains: the single-homeowner case should stay
simple to use — no organization-management UI forced on someone with one
property and one contributor — while the same account/property/user
structure supports an organization with many properties and many
contributors without a rearchitecture. With the account model now settled
as "one account = one org, currently at whatever headcount it has," the
remaining work is UI/UX simplification for the small case (hiding
org-management complexity a one-person account doesn't need yet) and
permission-model detail for the large case — not the underlying structure,
and not whether multi-user support exists at all.

## Geospatial data handling (first-class concern)

Storing and querying arbitrary user-drawn shapes alongside simple points is
a core technical challenge, not an incidental one, and needs to work at
both ends of the scale range:

- **Small scale:** one yard, a handful of small polygons (planting beds,
  treatment areas), a handful of point sightings. Low volume, but the
  drawing/editing UX and query correctness still need to be solid — this is
  the first real use case (Phase 1).
- **Large scale:** many properties, some potentially large tracts, with
  many activity geometries and many sightings accumulated over time.
  Needs to support:
  - Efficient storage of arbitrary polygon/rectangle geometry (not just
    bounding boxes).
  - Spatial querying — e.g., "activities within this area," "sightings
    near this point," "everything within a property's boundary" — with
    reasonable performance as the number of records grows.
  - Rendering many geometries on a map performantly (relevant to both the
    public map view, use case (c), and an organization-wide overview, use
    case (d)).
  - API-level geospatial filtering for downstream consumers (use case (e)),
    e.g., bounding-box or radius queries.
  - Interoperability with standard GIS formats and tools — the ability to
    export (and eventually import) data as GeoJSON, Shapefile, KML, or
    GeoPackage, so records logged in Habitat can be opened in QGIS,
    ArcGIS, or other GIS software, and so existing GIS data (e.g., a
    property boundary survey, an organization's existing parcel data) can
    be brought into Habitat rather than redrawn by hand.

**Decided: PostGIS is the geospatial engine**, running underneath the
chosen application stack — Django + GeoDjango, React + MapLibre GL (see
`tech-stack-options.md`). It natively handles both point and polygon
geometry, supports spatial indexing/querying at scale, and — via
GeoDjango's built-in GDAL/OGR bindings — gives a direct path to the
GIS-interoperability requirement above.
