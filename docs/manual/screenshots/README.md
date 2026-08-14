# Manual screenshots

`capture.js` drives a real, live local Habitat instance with Playwright
and regenerates the screenshots embedded in `docs/manual/*.md` (saved
into `docs/manual/images/`). It's a checked-in project asset, not a
one-off script — **re-run it (and update it if the UI changed shape)
whenever a session changes something a screenshot shows**, per
`/CLAUDE.md`'s "Keep the user manual current" convention.

## What it does

Signs up a fresh throwaway account, then walks the same path a new user
would: draw a property boundary → log an activity → log a sighting → link
them → visit Species/Tasks/Admin → check both public-site page shapes.
Screenshots land at the meaningful stopping points along the way. Each
`shot()` call in `capture.js` has a `MANIFEST` comment above it naming
which `docs/manual/*.md` chapter(s) embed that image — check that comment
before renaming or removing a screenshot, and add one when you add a new
`shot()` call.

## Prerequisites

You need a **live backend and frontend dev server**, backed by a **real
PostGIS-enabled Postgres** — this isn't a mocked/static walkthrough. Two
ways to get there:

### Option A: docker-compose (try this first)

```sh
cd /home/user/habitat
cp backend/.env.example backend/.env
docker compose up -d --build
```

If `docker` isn't already running as a daemon in your environment, you
may need to start it first (`dockerd &`, then wait a few seconds).

> **Known issue in this project's sandbox environment specifically:** the
> `postgis/postgis` image pull fails there — the sandbox's network proxy
> blocks the CDN host Docker Hub redirects image blobs to
> (`production.cloudfront.docker.com`), even though `docker` itself
> works. If you hit that, use Option B instead. This may not affect other
> environments (a real dev machine, CI, etc.) — try Option A first
> wherever you're running this.

### Option B: native Postgres + PostGIS (fallback, used to build the
### current screenshots)

```sh
apt-get update -qq
apt-get install -y postgis postgresql-16-postgis-3 gdal-bin libgdal-dev \
  libgeos-dev libproj-dev

service postgresql start

su postgres -c "psql -c \"CREATE USER habitat WITH PASSWORD 'habitat' SUPERUSER;\""
su postgres -c "psql -c \"CREATE DATABASE habitat OWNER habitat;\""
su postgres -c "psql -d habitat -c \"CREATE EXTENSION IF NOT EXISTS postgis;\""

cd /home/user/habitat/backend
python3 -m venv /tmp/habvenv
/tmp/habvenv/bin/pip install -r requirements.txt

export POSTGRES_HOST=localhost POSTGRES_DB=habitat POSTGRES_USER=habitat \
       POSTGRES_PASSWORD=habitat SECRET_KEY=devkey DEBUG=1 \
       ALLOWED_HOSTS=localhost,127.0.0.1
/tmp/habvenv/bin/python manage.py migrate
nohup /tmp/habvenv/bin/python manage.py runserver 0.0.0.0:8000 \
  > /tmp/backend.log 2>&1 &
```

(Adjust package/version names if the target OS isn't Debian/Ubuntu —
`postgresql-16-postgis-3` in particular is versioned to whatever
PostgreSQL major version is already installed; check with `psql
--version` / `apt-cache search postgis` first if `apt-get install` above
fails to find it.)

Then, either way, start the frontend:

```sh
cd /home/user/habitat/frontend
npm install
nohup npm run dev > /tmp/frontend.log 2>&1 &
```

Confirm both are up before proceeding:

```sh
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/auth/csrf/   # expect 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5173/                 # expect 200
```

## Installing this script's own dependencies

```sh
cd /home/user/habitat/docs/manual/screenshots
npm install
```

This installs the `playwright` npm package (pinned in `package.json`) but
**not** a browser binary — `capture.js` looks for one under
`PLAYWRIGHT_BROWSERS_PATH` first (this repo's sandbox environment
pre-installs Chromium there and sets that env var already), and falls
back to Playwright's normal bundled-browser resolution otherwise. If
neither is present:

```sh
npx playwright install chromium
```

## Running it

```sh
cd /home/user/habitat/docs/manual/screenshots
node capture.js
```

Takes well under a minute. Output PNGs overwrite `../images/*.png` in
place — review the diff (`git diff --stat ../images/`, and actually look
at a few of them) before committing, the same as you would for any other
generated asset.

Useful env var overrides (see the header comment in `capture.js` for the
full list): `BASE_URL` if the frontend isn't on the default port,
`SKIP_TILE_ABORT=1` if you're somewhere with real internet access and
want actual OpenStreetMap imagery in the map screenshots instead of a
blank background (see below).

## Basemap tiles

`MapCanvas` renders OpenStreetMap raster tiles
(`tile.openstreetmap.org`), which this project's sandbox environment
can't reach — `capture.js` aborts those requests by default so MapLibre
doesn't spend the whole run retrying them, which just leaves a blank
background behind the drawn shapes/markers in the map screenshots. That's
fine — the screenshots exist to show the *app UI*, not the basemap — but
if you're running this somewhere with real internet access and want
actual map tiles in the background, set `SKIP_TILE_ABORT=1`.

## Tearing down

If you followed Option B, stop the dev servers when you're done:

```sh
pkill -f "manage.py runserver"
pkill -f "vite --host"
```

`backend/.env` (Option A) or the exported env vars (Option B) hold
throwaway local credentials — nothing here is meant to persist or be
committed (`backend/.env` is already gitignored).
