# Tech Stack Options

**The geospatial layer is decided: PostgreSQL + PostGIS** (see
`data-model-notes.md`) — all three candidates below are built on it. The
application framework layered on top has now also been chosen. This doc
evaluates the candidates against the requirements that matter most to
Habitat specifically:

1. **Geospatial storage/querying** for both polygon geometries (activity
   boundaries) and points (sightings), at varying scale — from one yard to
   many large properties.
2. **A frontend capable of interactive map-drawing** — polygon/rectangle
   boundary tools, not just displaying pins.
3. **A public-facing web UI** — fast, simple, works for anonymous visitors.
4. **Multi-tenancy / organization support** — one account per
   organization/manager (possibly of one), holding multiple properties and
   multiple contributors (see `data-model-notes.md`).
5. **A future API surface** for third-party/downstream consumption.
6. **GIS interoperability** — exporting (and eventually importing) data in
   standard GIS formats (GeoJSON, Shapefile, KML, GeoPackage) so Habitat
   data can be used in QGIS, ArcGIS, or other GIS software, not just
   through Habitat's own UI/API.

## Decision: Option 1

**Chosen: PostgreSQL + PostGIS, Django + GeoDjango, React + MapLibre GL**
(see Option 1 below for the full evaluation). The deciding factors were
GeoDjango's first-class GDAL/OGR support — the strongest of the three
candidates on the GIS-interoperability requirement, which is a stated
priority (see `data-model-notes.md` and `open-questions.md`) — combined
with Django REST Framework's maturity for the public API planned in Phase
4. Options 2 and 3 are kept below as the alternatives that were actually
weighed, not just discarded ideas, in case a revisit is ever warranted
(e.g., if Phase 1 velocity or team composition changes).

---

## Option 1 (chosen): Postgres + PostGIS, Django (or similar), React + MapLibre GL

- **Backend:** Python, Django + Django REST Framework, with
  `django.contrib.gis` (GeoDjango) on top of PostgreSQL + PostGIS.
- **Frontend:** React (or similar), MapLibre GL JS for rendering, a
  drawing plugin (e.g., Mapbox GL Draw's MapLibre-compatible forks, or
  Terra Draw) for polygon/rectangle boundary capture.
- **Geospatial:** PostGIS is a mature, industry-standard geospatial
  extension for Postgres — native geometry/geography types, spatial
  indexing (GiST), and rich spatial query support (containment,
  intersection, distance) out of the box. Handles both polygons and points
  natively in the same database, at effectively any scale Habitat is
  likely to reach for a long time.
- **Map drawing:** GeoDjango + PostGIS pairs naturally with GeoJSON, which
  is what browser drawing libraries (MapLibre GL Draw / Terra Draw,
  Leaflet.draw) natively produce — low friction between what the user draws
  and what gets stored.
- **Public UI:** Straightforward — Django can serve server-rendered public
  pages directly, or the same API can back a separate public frontend.
- **Multi-tenancy:** No built-in multi-tenancy primitive; would be modeled
  explicitly (organization/account as a first-class model, with
  row-level ownership and Django's permission framework, or a
  multi-tenancy package). Well-understood territory for Django but requires
  deliberate design.
- **API:** Django REST Framework is well suited to a public API
  (serializers, pagination, filtering, auth) and has geospatial-aware
  serialization via GeoDjango.
- **GIS interoperability:** GeoDjango has built-in GDAL/OGR bindings, so
  reading and writing Shapefile, KML, and GeoJSON is a first-class,
  well-documented path — arguably the strongest of the three options on
  this criterion specifically.
- **Tradeoffs:** Mature and well-documented, but more infrastructure to
  operate (need to run/host Postgres+PostGIS yourself unless using a
  managed provider that supports PostGIS specifically — not all managed
  Postgres offerings enable it by default). Python/Django is a heavier
  framework than may be needed for a single-user Phase 1 MVP, though that
  weight is arguably what pays off at organization/API scale (Phases 3-4).

## Option 2 (not chosen): Postgres + PostGIS, Node/TypeScript full-stack (e.g., Next.js), MapLibre GL

- **Backend:** Node.js/TypeScript, either a framework like NestJS for a
  dedicated API or a full-stack framework (Next.js) that handles both the
  UI and API routes, with an ORM that supports PostGIS (e.g., Prisma with
  a PostGIS extension/raw SQL for geometry columns, or Kysely/raw SQL for
  more direct geospatial control).
- **Frontend:** Same React + MapLibre GL + drawing-plugin approach as
  Option 1, but same-language (TypeScript) across frontend and backend,
  which may reduce friction for a solo developer/early contributor moving
  between UI and API code.
- **Geospatial:** Same PostGIS foundation and capability as Option 1 — the
  database layer doesn't change. The difference is in ORM/query ergonomics:
  TypeScript ORMs generally have less mature first-class geospatial support
  than GeoDjango, so more geospatial queries may need to be written as raw
  SQL rather than through the ORM's query builder.
- **Map drawing:** Identical to Option 1 (frontend is React + MapLibre
  either way); this is a frontend concern that's largely independent of
  backend language choice.
- **Public UI:** Next.js (or similar) is well suited to a fast public
  frontend with server-side rendering, useful for a public map/gallery-style
  view that should be fast and shareable.
- **Multi-tenancy:** Same situation as Option 1 — no built-in primitive,
  needs explicit modeling. TypeScript ecosystem has less established
  convention here than Django's; more design work up front.
- **API:** A dedicated API layer (NestJS, or Next.js API routes/route
  handlers) can serve the same OpenAPI/REST or GraphQL surface for
  downstream consumers.
- **GIS interoperability:** No GDAL/OGR bindings built in the way GeoDjango
  has them — GIS format import/export would mean shelling out to `ogr2ogr`
  (or a Node GDAL binding) or relying on PostGIS's own
  `ST_AsGeoJSON`/`ST_AsKML`/shapefile-export functions directly. Workable,
  but more assembly required than Option 1.
- **Tradeoffs:** Single language across the stack is attractive for a
  small team/solo project, and the frontend map-drawing story is identical
  to Option 1. Weaker out-of-the-box geospatial ORM ergonomics than
  GeoDjango, and more assembly required for GIS format interoperability,
  are the main costs — expect more raw SQL/CLI tooling for spatial work.

## Option 3 (not chosen): Supabase (managed Postgres + PostGIS + Auth + Storage), React + MapLibre GL

- **Backend:** Supabase as a backend-as-a-service: managed PostgreSQL with
  PostGIS available as an extension, built-in authentication, built-in file
  storage (useful for activity/sighting photos), and auto-generated REST
  (and optionally GraphQL) APIs directly off the database schema, plus
  row-level security (RLS) for access control.
- **Frontend:** Same React + MapLibre GL + drawing-plugin pattern as the
  other options.
- **Geospatial:** Same PostGIS engine under the hood as Options 1-2, so the
  same geometry/point storage and spatial query capability — but with less
  operational burden, since Supabase manages the Postgres instance and
  PostGIS extension.
- **Map drawing:** Same as other options — a frontend concern, unaffected
  by backend choice.
- **Public UI:** Would still need a separate frontend app (Supabase isn't a
  page-rendering framework), but that frontend can query Supabase's
  auto-generated API directly for public/anonymous reads if RLS policies
  allow it — potentially less custom backend code for the public view.
- **Multi-tenancy:** Row-level security (RLS) is a natural fit for
  multi-tenant scoping — policies can be written per-table to restrict rows
  by account/organization membership, which maps reasonably well onto the
  single-user vs. organization account model in `data-model-notes.md`.
  This is a genuine strength of this option for Habitat's specific
  multi-tenancy need.
- **API:** Supabase's auto-generated REST/GraphQL API is convenient early,
  but a bespoke, versioned, documented public API for third-party consumers
  (use case (e) in `use-cases.md`) likely still needs a hand-built layer on
  top rather than exposing the auto-generated API directly — auto-generated
  schema APIs tend to leak internal table structure and are harder to
  evolve independently of the database schema.
- **GIS interoperability:** Since it's PostGIS underneath, the same
  `ST_AsGeoJSON`/`ST_AsKML` functions and `ogr2ogr` path are available —
  same underlying capability as Option 2, reached via direct SQL/CLI
  access to the managed database rather than an application-layer library.
- **Tradeoffs:** Fastest path to a working Phase 1 MVP — least
  infrastructure to stand up, auth and storage solved out of the box, RLS
  gives a head start on multi-tenancy. Costs: less control over the
  database/infrastructure than self-hosting, potential vendor lock-in
  (mitigated somewhat since it's Postgres underneath — self-hosting later
  is possible but not free), and the convenient auto-generated API is
  probably not the right long-term public API surface, so Phase 4 likely
  means building a real API layer regardless of this choice.

---

## Cross-cutting notes

- **PostgreSQL + PostGIS is decided**, not just converged-on — see
  `data-model-notes.md`. It's mature, handles both geometry and point data
  natively, supports the spatial querying Habitat needs at any scale it's
  likely to reach, and gives a direct, standard path (via GDAL/OGR and
  PostGIS's own export functions) to the GIS-interoperability requirement.
  Every option below builds on it; the application framework choice on top
  is now decided too (see "Decision: Option 1" above).
- **Frontend map-drawing** is effectively decided as "React + MapLibre GL
  (or Leaflet) + a drawing plugin" across all options, since it's a
  frontend-only concern. MapLibre GL is preferred over Mapbox GL JS for
  being open-source/no-API-key-required, which matters for a public-facing
  site with unknown/anonymous traffic.
- **Managed vs. self-hosted** was a real tradeoff in weighing Option 3
  against Option 1 — Supabase minimizes ops work but was judged likely to
  need revisiting (or migrating off) once Phase 3-4 needs (custom
  multi-tenancy logic, a bespoke API) outgrow what a BaaS auto-generates.
  Option 1 takes on more up-front infrastructure in exchange for not
  needing that later migration.
- **Next step:** Phase 1 implementation against the chosen stack (Django +
  GeoDjango + PostGIS, React + MapLibre GL) — see `roadmap.md`.
