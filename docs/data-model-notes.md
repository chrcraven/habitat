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
  **Decided: beyond that pair, states are org-defined, not a fixed global
  enum.** Each account/organization can define its own workflow states
  (e.g., planned → in-progress → done, plus whatever cancelled/on-hold/
  review states fit their process) rather than Habitat imposing one status
  set on everyone. Still open: what a sensible default state set looks
  like for a brand-new account (so a solo homeowner isn't forced to design
  a workflow just to log a planting), and whether "planned" and "done" (or
  their equivalents) are reserved states every custom workflow must map
  onto, since the public view depends on that distinction. See
  `open-questions.md`.
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
  **Structured, reference-backed species data — decided the reference is
  account-defined, not an external taxonomy.** Rather than integrating an
  outside standard (GBIF, USDA PLANTS, a regional native plant database)
  from the start, each account/organization maintains its own species
  list, defined by whoever manages that account (the "habitat manager").
  That account-defined list is what a sighting like Field Bindweed and the
  treatment addressing it resolve against (see below) — a shared reference
  *within* the account, not necessarily standardized across accounts. Free
  text likely still has a role as a fallback/detail field alongside the
  structured pick. Integrating an external taxonomy later (for
  cross-account consistency, or to make initial account setup easier) is a
  plausible future step, not a Phase 1 requirement.
- **Photos / media.** One activity record should support multiple photos,
  attachable at creation or added later (e.g., before/after). Likely also
  needs basic metadata per photo (captured date, maybe which
  planned-vs-done state it corresponds to). **Decided: stored in the
  database**, not external object storage — see `tech-stack-options.md`
  for the tradeoff and `open-questions.md` for the storage-growth question
  that raises at scale.
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

- **Species.** What was observed — same account-defined reference list as
  activity records (above), not an external taxonomy. Sightings and
  activities within the same account share that species reference list,
  since that's exactly what makes linking a sighting to a responding
  activity (below) meaningful — e.g., a Field Bindweed sighting and a
  Field Bindweed treatment referring to the same account-defined species
  record, not two independently-typed strings.
- **Point location.** Simple device-location capture — a single
  coordinate, not a drawn shape. This is the key structural difference from
  activity records.
- **Timestamp.** When the sighting occurred (which may differ from when it
  was logged, if entered after the fact).
- **Photos.** Same general need as activities — one or more photos
  attachable to the record, stored in the database (same decision as
  activities, above).
- **Notes.** Freeform text, same as activities.
- **Public visibility.** Same per-record public/private flag as activity
  records, public by default. Sightings raise a sharper version of the
  privacy question, though: reports of sensitive or at-risk species (e.g.,
  an endangered species' exact location) are a well-known case where
  public geolocation data can cause real harm (poaching, disturbance,
  collection). The per-record flag covers the mechanism (a sighting can be
  marked private). **Decided (2026-08-28): default behavior for sensitive
  sightings is an organization's own call, set per property** — not an
  auto-detected, species-list-driven default. **Implemented (2026-08-28):**
  `Property.sightings_public_by_default` (default `true`) — a new
  sighting on that property, when the creating request doesn't explicitly
  set its own `is_public`, starts from this value instead of the model's
  own `true` default (`SightingViewSet.perform_create`). The per-property
  admin form (`PropertyFormPage`) exposes it as a checkbox; the sighting
  form itself (`SightingFormPage`) seeds its own public/private checkbox
  from the property's current value for a brand-new sighting (an existing
  one keeps whatever it already has). Every sighting still carries its own
  independent, always-overridable `is_public` — this only changes the
  *starting* value.

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

**Decided: the sighting ↔ activity link is many-to-many, and created
directly — not gated behind resolving a task.** A user links a sighting to
one or more activities (and an activity can have multiple linked
sightings) directly, the same way they'd set any other relationship on the
record; the link doesn't have to be routed through, or wait on, a task
being resolved. One sighting can end up related to more than one activity
over time (e.g., an initial treatment and a follow-up), and one activity
can address several sightings.

Tasks (see "Task record" below) still exist, but as an independent,
optional mechanism for assigning follow-up work to a contributor — not as
the only path to creating this link. A land manager might create a task to
have a teammate look into a sighting, and separately (or as part of
handling that task) go link the sighting to an activity directly; in the
initial build the two aren't wired together automatically. A future
business rules engine (see "Automation" below) is the intended place for
automating that connection later — e.g., auto-creating the link when a
rule's conditions match.

Still open (tracked in `open-questions.md`):

- Should the public-facing view surface this link (e.g., "reported by a
  visitor, treated on this date")? **Decided (2026-08-28): yes.**
  **Implemented (2026-08-28):** `property_activities`/`property_sightings`
  in `backend/apps/public_site/views.py` each annotate their features with
  `linked_sighting_ids`/`linked_activity_ids` — filtered to only ever
  include the *other* side when it's also public (and on a public
  property), so a public visitor can never infer the existence of a
  private record via a link. `PublicPropertyPage` renders these as
  "Reported sightings: …" / "Treated by: …" lines on each card.

## Public-facing site (Phase 2)

An unauthenticated visitor can now view an org's public data in two
shapes, both backed by `backend/apps/public_site/` (no session/API-key
required — every query is filtered to `is_public=True` records, and a
private record 404s rather than 403s, so a guessed ID doesn't even
confirm it exists):

- **Per-property.** One property's boundary, its public activities, and
  its public sightings — photos included. The "someone other than the
  account owner can see what's happening on the land" view from
  `roadmap.md` Phase 2.
- **Per-organization.** A portfolio listing every property the org has
  marked public (`Property.is_public` — see "Accounts / ownership"
  below), for an org with more than one.

Both are reachable from the logged-in app's nav ("Public site", opens in
a new tab) and both link back to `/login` — the "method to get to the
backend/login" the public site needs so a visitor who wants to log in
themselves (or an account owner sharing their own public link) isn't
stuck. The sighting↔activity link (see above) and per-property sensitive-
sighting default visibility (see above) are both now built. Still not
built: a real vanity/slug URL instead of numeric IDs (see
`open-questions.md`, "Tech / infrastructure").

## Task record

Separate from the sighting ↔ activity link above, a **task** is a simple
assignable work item — one contributor assigning something to another (or
to themselves) to look into or follow up on. **Decided: tasks are
optional, not a required intermediary for anything else in the model, and
the initial build keeps them intentionally simple** — user-to-user
assignment, nothing more (see `use-cases.md` (g)). **Now has a real API
and UI** (`/api/tasks/`, org-scoped CRUD; `/tasks` page) — the model
existed since the very first backend session but had no way to reach it
from the app until this one. Origin (`origin_sighting`/`origin_activity`),
assignment, and status are all settable from the Tasks page; nothing
notifies the assignee yet (see `open-questions.md`).

Motivating example: a Field Bindweed sighting is logged. A land manager
creates a task — "check out this bindweed report" — and assigns it to a
teammate. That teammate investigates and, separately, links the sighting
to a new or existing treatment activity if warranted. The task and the
sighting-activity link are two different actions; resolving the task
doesn't automatically create the link.

Likely needed, initial build:

- **Origin.** A task can reference a sighting (or an activity, or nothing
  in particular — a general to-do), but doesn't have to. Creating a task
  from a sighting is something a user does deliberately, not an automatic
  side effect of logging one.
- **Assignment.** Which contributor on the account the task is assigned
  to — the core feature. Any contributor can assign a task to any other
  contributor on the same account, or to themselves. This is meaningful as
  soon as an account has more than one contributor, which — per the
  account model below — can be true even in Phase 1.
- **Status / lifecycle.** Exact states still open (see
  `open-questions.md`), but at minimum something like open → assigned →
  resolved, plus dismissed. Kept simple and generic for the initial
  build — this is a to-do list, not a workflow engine.

This simple, manual, user-to-user assignment is deliberately where the
initial build stops. A **business rules engine** (see "Automation" below)
is the planned way to later automate what's manual here — auto-creating
tasks, auto-assigning them based on rules, and auto-creating
sighting-activity links — without changing the underlying task or link
model.

Open questions this raises (tracked in `open-questions.md`):

- Exact status/lifecycle states for a task.
- Notification mechanism when a task is assigned to someone.
- Whether tasks have any public visibility at all (probably not — they're
  an internal work item, distinct from the sightings and activities that
  are public by default) or stay account-internal always.
- Whether/how tasks double as the moderation step once public sighting
  submissions exist (Phase 5) — a plausible fit, but no longer the only
  mechanism sightings flow through now that linking doesn't require a
  task, so this needs its own look once Phase 5 is nearer.

## Automation: rules engine (early idea)

In the initial build, creating a task, assigning it, and linking a
sighting to an activity are all manual actions a user takes — nothing
happens automatically. A **business rules engine** is the planned way to
automate that later: instead of a person deciding every time, an account
can configure conditions that trigger these same actions automatically.

Motivating examples: an organization wants "any sighting of Field
Bindweed within Property X's treatment zone automatically links to the
treatment activity already planned for that area" — no manual linking
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
- **Action(s).** What the rule does once triggered — automating the same
  things a user can already do manually:
  1. **Create a task**, optionally with a specific assignee pre-filled,
     rather than a user having to create and assign it themselves.
  2. **Auto-create the sighting ↔ activity link** — skip the manual
     linking step entirely when a sighting clearly matches work that's
     already planned, even work that's still in "planned" (not yet
     started) status. A rule recognizing that an incoming sighting
     belongs to an activity that already exists, without a person having
     to make that connection by hand.
  3. **Call a webhook** — notify an external system/URL when the rule
     fires, independent of anything happening inside Habitat. This is the
     push-based counterpart to the pull-based public API (Phase 4,
     `roadmap.md`) — useful for an organization's own internal tooling
     (e.g., a Slack notification, a ticketing system) as well as, later,
     third-party integrations.

This is explicitly **not** a Phase 1 concern — Phase 1 keeps task
creation, assignment, and sighting-activity linking fully manual. But that
manual model (task record, many-to-many sighting-activity link) is
designed to be exactly what the rules engine automates later, not a
different mechanism that gets replaced. Real configurability is a
Phase 3/4-era concern, likely alongside organization-scale permission
depth and the public API (see `roadmap.md`).

Open questions (tracked in `open-questions.md`):

- Who can define rules — any contributor, or only account
  admins/managers? Per-property or account-wide?
- How much rule complexity is exposed to users vs. kept simple by default
  (most accounts, especially solo ones, may never define a rule at all)?
- Webhook reliability concerns: retries, delivery guarantees, payload
  signing/authentication, rate limiting — real integration-surface
  questions, not just a data-model detail.
- Does auto-creating a sighting-activity link ever happen without any
  human review, or does it always still produce a task/notification for
  someone to confirm (even if the link is already made)? A real tradeoff
  between convenience and the risk of mis-linking a sighting to the wrong
  planned work.

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
  different numbers of properties and contributors. **An organization also
  has a globally-unique `slug`** (added 2026-08-29) — the vanity segment of
  its public URL (`/public/<slug>`), auto-generated from the name on create
  (slugify + numeric suffix on collision) and admin-editable in the org
  admin portal; a small reserved set (`org`, `properties`, `public`, `api`,
  …) is disallowed so a slug can't shadow the numeric-ID public routes. See
  `docs/open-questions.md` ("Recently resolved") and `apps/accounts/slugs.py`.
  **Decided: every account sees the same organization-management UI,
  regardless of current headcount.** Rather than hiding invites/roles/multiple-properties from a
  one-person account, the interface is uniform — a solo homeowner sees the
  same screens a large organization does, just mostly unused at first.
  This trades a small amount of unused UI surface for the small case in
  exchange for one interface to build and maintain, not two.
- **Property / parcel.** A piece of land with a boundary, owned by an
  account. **Decided: the boundary is user-drawn, not tied to a legal
  parcel.** Habitat doesn't require, or attempt to validate against,
  official cadastral/parcel data — a property is whatever area a user
  draws and names, which in practice will often approximate real property
  lines without being sourced from or reconciled against them. **Multiple
  properties are supported under a single account from the start** — a
  single homeowner might have exactly one property (their own yard), while
  a land trust has many. Activities and sightings are linked to a
  property, and through it to the owning account. **A property also has
  its own `is_public` flag** (default `true`), separate from and on top of
  each Activity/Sighting's own per-record flag — added alongside the
  Phase 2 public site so an org can keep an entire property (e.g. a
  manager's own yard) off the public site, rather than having to mark
  every one of its records private individually. **A property also has
  `sightings_public_by_default`** (default `true`, added 2026-08-28) — see
  "Sighting record" above. **A property also has a `slug`** (added
  2026-08-29) for the vanity public sub-URL
  (`/public/<org-slug>/<property-slug>`) — auto-generated from the property
  name, **unique only within its owning organization** (enforced by a
  `unique_together`/`UniqueConstraint` on `(organization, slug)`), so two
  different orgs can each have a `north-meadow`. Admin-editable on the
  property edit form. See `docs/open-questions.md` ("Recently resolved").
- **Users / contributors.** One or more people who can log activity under
  an account — **multi-user support is a property of every account, not a
  separate tier.** The author's own account may have just one contributor
  (the author) at first, but a second contributor (a spouse, a helper) can
  be added to that same account at any time, with no change in account
  type. For a larger organization, this is used more heavily from day
  one: multiple staff/volunteers, not all with the same access.
- **Permissions.** **Decided: role-based, with the ability to scope a role
  to specific properties.** Three roles — viewer (read only), editor
  (read/create/update), admin (also delete, and manage org membership) —
  each assignable either account-wide or limited to one or more specific
  properties, so a volunteer can be scoped to just the site they work on,
  while a program manager holds a role across the whole portfolio. This
  applies uniformly regardless of account size; a one-person account just
  has one person holding whatever role(s) they need account-wide. Both
  the role and the property scope are enforced backend-side
  (`apps/accounts/org_scoping.py`) and managed through the **org admin
  portal** — an in-app, admin-only page (`/admin`, not Django's own
  `/admin` site) where an admin renames the org and adds/edits/removes
  members. Adding a member with an email that already has a Habitat
  account attaches them immediately; a brand-new email instead creates a
  separate `Invitation` record (org, role, property scope, an unguessable
  token, a 7-day expiry) and emails an accept link — accepting it creates
  the `User` and `Membership` together and logs the person in. Real email
  *delivery* still isn't configured (see `open-questions.md`), so the
  accept link is also always shown/copyable in the admin UI as a
  fallback. Removing or demoting the org's last remaining admin is
  blocked so an account can't lock itself out.

The account/property/user/permission structure is meant to be the same
shape end to end — one account model, one UI, one role/permission system —
whether it's a single homeowner or a large multi-property organization
behind it. The remaining open work is filling in the exact role
definitions and default state for a brand-new account, not a separate
interface or model for the small case (see `open-questions.md`).

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
