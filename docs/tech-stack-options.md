# Tech Stack Options

Early research, not a decision. This lays out 2-3 candidate stacks and
evaluates each against the requirements that matter most to Habitat
specifically:

1. **Geospatial storage/querying** for both polygon geometries (activity
   boundaries) and points (sightings), at varying scale — from one yard to
   many large properties.
2. **A frontend capable of interactive map-drawing** — polygon/rectangle
   boundary tools, not just displaying pins.
3. **A public-facing web UI** — fast, simple, works for anonymous visitors.
4. **Multi-tenancy / organization support** — single-user accounts and
   multi-contributor organization accounts on the same platform.
5. **A future API surface** for third-party/downstream consumption.

No stack is selected yet. This should be revisited once Phase 1 scope
(single-user MVP) is more concrete.

---

## Option 1: Postgres + PostGIS, Django (or similar), React + MapLibre GL

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
- **Tradeoffs:** Mature and well-documented, but more infrastructure to
  operate (need to run/host Postgres+PostGIS yourself unless using a
  managed provider that supports PostGIS specifically — not all managed
  Postgres offerings enable it by default). Python/Django is a heavier
  framework than may be needed for a single-user Phase 1 MVP, though that
  weight is arguably what pays off at organization/API scale (Phases 3-4).

## Option 2: Postgres + PostGIS, Node/TypeScript full-stack (e.g., Next.js), MapLibre GL

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
- **Tradeoffs:** Single language across the stack is attractive for a
  small team/solo project, and the frontend map-drawing story is identical
  to Option 1. Weaker out-of-the-box geospatial ORM ergonomics than
  GeoDjango is the main cost — expect more raw SQL for spatial queries.

## Option 3: Supabase (managed Postgres + PostGIS + Auth + Storage), React + MapLibre GL

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

- **All three options converge on PostgreSQL + PostGIS** as the geospatial
  storage layer. This looks like the right foundation regardless of which
  application framework is chosen — it's mature, handles both geometry and
  point data well, and is supported (to varying degrees) by every option
  above. This is the one piece of this doc closest to a real conclusion;
  everything above it is more open.
- **Frontend map-drawing** is effectively decided as "React + MapLibre GL
  (or Leaflet) + a drawing plugin" across all options, since it's a
  frontend-only concern. MapLibre GL is preferred over Mapbox GL JS for
  being open-source/no-API-key-required, which matters for a public-facing
  site with unknown/anonymous traffic.
- **Managed vs. self-hosted** is a real early tradeoff: Supabase (Option 3)
  minimizes ops work for the Phase 1 MVP but may need to be revisited (or
  migrated off, or self-hosted) once Phase 3-4 needs (custom multi-tenancy
  logic, a bespoke API) outgrow what a BaaS auto-generates.
- **None of this blocks Phase 0 (planning) or early Phase 1 design.** This
  doc should be revisited with a real decision once Phase 1 scope
  (see `roadmap.md`) is concrete enough to prototype against.
