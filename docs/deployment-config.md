# Deployment configuration

Every environment-specific value Habitat reads, in one place. The code
never hardcodes a deployment's hostnames, secrets, or feature flags: each
setting below is an environment variable with a default that makes local
development work out of the box (`docker-compose up`), overridden per
environment — a ConfigMap/Secret, an `.env` file, whatever the deployment
uses. Adding a *new* environment-specific value means adding it here and
in `backend/config/settings.py` (or the frontend's `import.meta.env`),
not branching on a hostname in application code.

Written 2026-09-02, when the public site gained the ability to live on its
own origin (see "Serving the public site on its own origin" below) — that
relocation is entirely a configuration change, which is what prompted
writing the full list down.

## Backend (`backend/config/settings.py`)

| Variable | Default | What it does |
| --- | --- | --- |
| `SECRET_KEY` | `insecure-dev-key-change-me` | Django signing key. **Must** be set to a real secret anywhere but local dev. |
| `DEBUG` | `1` | `1`/`0`. Turn off outside local dev. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames Django will serve. |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` | `habitat` / `habitat` / `habitat` / `db` / `5432` | PostGIS connection. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated origins allowed to call the API from a browser. |
| `CSRF_TRUSTED_ORIGINS` | *(falls back to `CORS_ALLOWED_ORIGINS`)* | Origins trusted for state-changing requests. Set explicitly when some origin should be able to *read* the API without being trusted to *write* — see below. |
| `FRONTEND_URL` | `http://localhost:5173` | Origin of the authenticated app, used to build invite and password-reset links in emails. |
| `PUBLIC_SITE_URL` | *(blank)* | Origin the public site is served from. Blank means same origin as the app. See below. |
| `EMAIL_BACKEND` | console backend | Real SMTP isn't configured yet (see `open-questions.md`); `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` are read when it is. |
| `HABITAT_FEEDBACK_ENABLED` | `0` | Turns the in-app feedback button and its endpoints on. |
| `HABITAT_FEEDBACK_TOKEN` | *(blank)* | Bearer token for the cross-org feedback pull endpoint. Blank always denies — never "unauthenticated is fine". Must match the value held by whatever scheduled routine pulls feedback. |
| `HABITAT_CUSTOM_PAGE_HTML` | `0` | Lets organizations author public pages as their own HTML/JS instead of markdown. Off by default; see below. |
| `HABITAT_CUSTOM_PAGE_HTML_MAX_BYTES` | `524288` (512 KB) | Cap on one custom-HTML page's stored source. |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | *(derived: on when `DEBUG=0`)* | Marks the cookies HTTPS-only. **Not a fixed default** — see below. |
| `SECURE_HSTS_SECONDS` | `0` (off) | HSTS max-age. Off by default on purpose; see below. |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` / `SECURE_HSTS_PRELOAD` | `0` | Only meaningful once `SECURE_HSTS_SECONDS` is non-zero. |
| `SECURE_SSL_REDIRECT` | `0` | Have Django redirect HTTP→HTTPS. Must be enabled together with the next one; see below. |
| `TRUST_X_FORWARDED_PROTO` | `0` | Lets Django read the original scheme from `X-Forwarded-Proto`. Only safe when the proxy overwrites that header. |
| `THROTTLE_NUM_PROXIES` | `0` | How many reverse proxies sit in front of this process. Decides where the login/signup rate limits read the client address from. **`0` means `X-Forwarded-For` is never trusted** — see "Rate limits" below. |
| `HABITAT_SUPPORT_CONTACT` | *(blank)* | Who a stuck user should contact about *this* deployment — an address, a URL, a name. Appears in the "forgot password" reply, the one screen whose reader is already locked out. Blank keeps the generic "whoever runs this Habitat instance". |
| `GUNICORN_WORKERS` | `1` | Production image only. **Raising it is a decision, not a knob** — see "Running more than one replica". |
| `GUNICORN_THREADS` | `4` | Production image only. Concurrency within the single worker. |
| `GUNICORN_TIMEOUT` | `60` | Production image only. Seconds before gunicorn kills a stuck request. |

Boolean variables accept `1`/`true`/`yes`/`on` (and their negatives);
blank or unset means "use the default".

## Response compression

Added 2026-09-14. `GZipMiddleware` is enabled unconditionally in
`config/settings.py` — there is **no environment variable for it**, which
is deliberate: it has no deployment-specific tradeoff to configure, and a
knob would only invite a deployment to turn it off by accident. Measured
10.8x on this app's list payloads.

Two consequences a deployment should know about rather than discover:

- **A proxy or CDN in front of Habitat must honour `Vary:
  Accept-Encoding`**, which the middleware sets. A cache that ignores it
  can serve gzipped bytes to a client that never asked for them. Any
  standard reverse proxy does this correctly; it is called out because
  the failure mode is a hard-to-read decoding error rather than a 500.
- **Double compression is not a problem, but is waste.** If your edge
  proxy already compresses, Django's middleware still runs first and the
  proxy will see a response that is already `Content-Encoding: gzip` and
  leave it alone. Nothing breaks; you may prefer to disable one of them.

BREACH — the standing objection to compressing responses — is mitigated
by the pinned Django rather than merely accepted: `GZipMiddleware` pads
each compressed response with up to 100 random bytes. See the comment on
the middleware in `config/settings.py` for the full reasoning, including
why no view is exempted.

## Transport security

Added 2026-09-06, after the deployed site was found handing out session
and CSRF cookies with **no `Secure` attribute** while being served over
HTTPS. A browser holding a Habitat session would therefore send both
cookies, in cleartext, to `http://<the same host>/anything` — and that
host answers on port 80, issues no HTTPS redirect, and sent no HSTS
header, so nothing upstream closed the gap either. Django's own
`manage.py check --deploy` had been reporting it (`security.W012` and
`security.W016`) for as long as the deployment has existed; nothing ran
that command.

**The two cookie flags default to `not DEBUG` rather than to a fixed
value**, which is the one genuinely load-bearing choice in this block:

- A hardcoded `True` breaks every developer. Local dev is served over
  plain HTTP, and a browser silently declines to store a `Secure`
  cookie there, so login would fail with nothing on the page to explain
  it.
- A hardcoded `False` is what shipped until 2026-09-06.

Deriving the default from `DEBUG` means the flag that already separates
"a developer's laptop" from "a real deployment" also flips these, so a
deployment gets the safe posture **without having to know these
variables exist**. A `DEBUG=0` deployment genuinely served over plain
HTTP — there is none today — opts back out with
`SESSION_COOKIE_SECURE=0` / `CSRF_COOKIE_SECURE=0`.

> **Deployment note.** Because of that derivation, a deployment already
> running `DEBUG=0` starts issuing `Secure` cookies as soon as it picks
> up this change, with no configuration edit. That is the fix landing.
> It is only a problem for a `DEBUG=0` deployment served over plain
> HTTP, where sessions would stop working until the two variables above
> are set to `0`.

**HSTS is deliberately off by default, unlike the cookie flags.** A
browser *remembers* HSTS and there is no way to recall it within its
`max-age`, so committing a hostname to HTTPS-only has a tail that a code
default should not decide on a deployment's behalf. The `Secure` flags
are what actually stop the cookies leaking; HSTS is defence in depth for
the first navigation to the host. A deployment settled on HTTPS should
set `SECURE_HSTS_SECONDS=31536000`.

**`SECURE_SSL_REDIRECT` and `TRUST_X_FORWARDED_PROTO` are a pair —
enable both or neither.** Behind a TLS-terminating proxy (which is how
`habitat.dev.cravenator.com` is served) Django only learns the original
scheme from `X-Forwarded-Proto`. Turning on the redirect *without* the
header trust gives an infinite redirect loop: every proxied request
looks like plain HTTP to Django, which redirects it to HTTPS, which the
proxy terminates and forwards as HTTP again. Trusting the header is
itself only safe when the proxy **overwrites** it on every request — if
a client can set it directly, any request can declare itself secure.

`config/tests.py` asserts these defaults in both directions, and runs
Django's own deploy checks against the settings a `DEBUG=0` deployment
resolves to.

## Frontend (Vite, `import.meta.env`)

Vite inlines these **at build time**, so they belong to the image build,
not the running container.

| Variable | Default | What it does |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000/api` in a **dev** build, `/api` (relative) in a **production** build | Where the SPA calls the API. The production default names no host, which is what lets one published image run in any deployment — see "Building the images". |
| `VITE_PUBLIC_SITE_URL` | *(blank)* | Origin the public site is served from; blank means same origin. The sibling of the backend's `PUBLIC_SITE_URL`. |

## Building the images

Both images are built from their own directory as the context
(`./backend`, `./frontend` — see `.github/workflows/docker-publish.yml`),
and each directory carries a `.dockerignore`. Two consequences worth
knowing before deploying:

- **No `.env` is ever baked into an image.** Both `.dockerignore` files
  exclude it, deliberately: `docker-compose.yml` requires a
  `backend/.env` for local dev, so on a developer's machine that file
  exists and holds a real `SECRET_KEY` and database password, and a plain
  `COPY . .` would copy it into a layer. Nothing in either image reads a
  dotenv file — `settings.py` reads `os.environ` only — so every value in
  the tables above must be supplied to the *running container*
  (ConfigMap/Secret, `env_file:`, `-e`), never assumed to be inside it.
  The one exception to that rule is the frontend's `VITE_*` variables,
  which Vite inlines at build time and which therefore have to be present
  *during* the image build.
- **The frontend image installs from `package-lock.json` via `npm ci`**,
  so its dependency set is reproducible and is the same set
  `.github/workflows/tests.yml` validates. Until 2026-09-05 it ran
  `npm install` against `package.json` alone, which resolved fresh at
  build time — a green CI run did not imply a green image.

### Two targets, one Dockerfile each

Since 2026-09-17 each Dockerfile builds **two** images, selected with
`--target`:

| target | backend | frontend | published as |
| --- | --- | --- | --- |
| `dev` | `manage.py runserver` | Vite dev server | `latest`, on a push to `main` |
| `production` | gunicorn + WhiteNoise, static collected at build time | `vite build` output served by nginx | `X.Y.Z`, on a `vX.Y.Z` tag |

`production` is the **last** stage in both files, so a bare
`docker build ./backend` produces the one that is safe to put on the
internet; `docker-compose.yml` names `target: dev` explicitly, which is
why local development is unchanged.

The tag mapping is deliberate and is the two hosting decisions expressed
as one rule: `habitat.dev.cravenator.com` is permanently a dev instance
and pulls `latest`, so `latest` has to stay the dev image it has always
been; production is stood up from a version tag, so a version tag is the
only thing that produces gunicorn and nginx. Getting it backwards would
put two development servers on the public internet — which is exactly
what following the release plan against the pre-2026-09-17 Dockerfiles
would have done.

`.github/workflows/tests.yml` **builds both production targets on every
push and pull request, without pushing them.** That matters because
`docker-publish.yml` only builds them on a tag, and as of 2026-09-17
there are zero git tags and zero GitHub releases — so without that job the
first release would be the first time anyone learned whether those stages
build at all.

### The one thing that is not overridable at run time

Everything in the backend table is read from `os.environ` at process
start, so a ConfigMap or Secret changes it with a restart and no rebuild.
**The frontend's `VITE_*` values are not like that**, and the production
build is precisely what removes the ability:

- Vite substitutes `import.meta.env.VITE_*` during `vite build`.
  Measured — building with `VITE_API_URL` set to a marker leaves that
  exact string in `dist/assets/*.js`, and `import.meta.env` appears
  **zero** times in the output.
- Today's *dev* image runs `npm run dev`, and Vite's dev server reads the
  environment at container start, so an override genuinely works there.
  The multi-stage `vite build` is what ends that.

Which is why `VITE_API_URL` defaults to a **relative** `/api` in a
production build rather than to any hostname: the published image names
no host at all, so the same artifact a `vX.Y.Z` tag published runs in any
deployment, and there is nothing for a ConfigMap to need to override. The
cost is a precondition, stated plainly below.

### What the deployment has to route

The production frontend image is a static file server and nothing else —
it deliberately does not proxy to the backend, because the moment its
nginx config names a backend host the image stops being
deployment-neutral. The ingress or reverse proxy in front of both must
send these paths to the **backend** service:

| path | why |
| --- | --- |
| `/api/` | the whole application API, public-site data included |
| `/admin/` | Django admin — load-bearing here, it is the only place the per-tenant custom-HTML kill-switch can be set |
| `/static/` | Django admin's own CSS and JS, served by WhiteNoise out of the image |

Everything else goes to the **frontend** service, which answers unknown
paths with the SPA's `index.html`. One consequence already recorded with
D23 and worth repeating here: that fallback means a mistyped in-app
address returns **200** with the app's own not-found screen, not a 404, so
a link checker cannot see a dead in-app address.

### Secrets are not ConfigMaps

`SECRET_KEY`, `POSTGRES_PASSWORD` and `HABITAT_FEEDBACK_TOKEN` belong in a
Secret. A ConfigMap is plaintext to anything that can read the namespace,
and that is as true at one replica as at ten.

## Rate limits

Added 2026-09-17 (D40). Two endpoints are rate-limited and no others:
`POST /api/auth/login/` at **10 requests a minute per client address**,
and `POST /api/auth/signup/` at **5 an hour**. The constants and the
reasoning live in `backend/apps/accounts/throttling.py`.

They exist because those two are the only unauthenticated endpoints that
run a password hash, and Django's default hasher is pbkdf2 at 1,000,000
iterations — about 600 ms of server CPU per request, paid even for an
email that has no account, because `ModelBackend.authenticate` hashes
against a throwaway user to flatten the timing difference. Roughly 400
request bytes buy 600 ms of CPU.

**The limit cannot be made cheaper instead.** The expense *is* the
security control: a faster hasher is weaker password storage for every
user. Do not "optimise" `PASSWORD_HASHERS`.

Two deployment-facing consequences:

- **`THROTTLE_NUM_PROXIES` defaults to 0, and behind a proxy that is
  wrong.** At 0 the limit keys on `REMOTE_ADDR`, so behind a reverse proxy
  every request appears to come from the proxy and the limit becomes
  *global* — too strict, and visible as users complaining. Set it to the
  number of proxies that **overwrite** `X-Forwarded-For` (usually 1; a
  Kubernetes ingress in front of another proxy is 2). The default is 0
  rather than DRF's own `None` because `None` trusts a client-supplied
  header, which an attacker varies per request — a throttle that is
  present, visible in the code, and refuses nobody. Failing too strict is
  loud; failing open is silent.

  **This applies to `habitat.dev.cravenator.com` today.** It sits behind a
  TLS-terminating proxy, so with `THROTTLE_NUM_PROXIES` unset every
  request reaches Django carrying the proxy's address and the sign-in
  limit is shared by everyone using that instance — ten attempts a minute
  across the whole deployment rather than per person. Harmless at two
  organizations; set it to `1` (or whatever the hop count is) when that
  stops being true, and set it on production from the start.
- **The limit's state lives in Django's cache, and there is no `CACHES`
  setting.** That is `LocMemCache`: per process, not shared. See the next
  section.

## Running more than one replica

Habitat is deployed to Kubernetes at **`replicas: 1`** (owner, 2026-09-17),
and three things in this repo are correct *because of that* rather than in
general. None of them errors if the assumption stops holding, which is why
they are written down here rather than left to be discovered:

| what | why one replica makes it correct | what to change first |
| --- | --- | --- |
| The login/signup rate limits | `LocMemCache` is per process, so one process means one bucket | Configure a shared `CACHES` backend (Redis, or Django's database cache table) before adding a replica **or** raising `GUNICORN_WORKERS` |
| `migrate` on every boot (`backend/entrypoint.sh`) | one pod, one start, nothing to race | Move it to an initContainer or a Job |
| The soft-delete purge sweep on boot | same | Move it to a `CronJob` — which is also the "real cron for the purge" this repo has wanted since 2026-08-29 |

The rate limit is the one that fails most quietly. `kubectl scale
--replicas=2` needs no code change, no rebuild and no review, produces no
error, and makes the login limit **twice as loose as the number written in
the code**, invisibly. `GUNICORN_WORKERS=3` does the same thing inside a
single pod — which is why the production image ships **one** worker and
several threads instead of several workers. That is not a performance
compromise: CPython's `hashlib` releases the GIL for pbkdf2, measured at
four concurrent 1,000,000-iteration hashes finishing in 1.23x the wall
time of one, so a single worker still hashes concurrent logins in
parallel.

The Kubernetes manifests live in the deployment's own configuration, not
in this repo, so nothing here can enforce `replicas: 1` — the same limit
recorded against D6, D28 and D37. This section is the enforcement.

## Rolling back a deploy

Every other section here is about running Habitat. This one is about
un-running a release, which is the situation you are in when a deploy
turns out to be bad. Read it **before** you need it: the obvious
sequence — pull the previous image, restart — leaves the application
broken in a way that does not announce itself.

### What a naive rollback actually does

`backend/entrypoint.sh` runs `manage.py migrate` on every container
start, so the database is always rolled *forward* to whatever the running
image knows. Swapping back to an older image does not undo that. The
older code then meets a schema from the future.

Measured end to end against PostgreSQL 16 and the pinned Django 5.2.17,
rolling the real repository back across the D33 release:

| Old image against the newer database | Result |
| --- | --- |
| `manage.py migrate` (what the entrypoint runs) | **exit 0**, "No migrations to apply" |
| Container start | **clean**, nothing in the logs |
| Reading existing records | **works** — no corruption, nothing mis-served |
| Writing a new record | **`IntegrityError`, surfaced to the user as a 500** |

So browsing the app looks completely healthy and the outage is deferred
to the first person who tries to save something. Two of the four affected
tables in that release are `accounts_organization` and
`accounts_property`, which means **signup and property creation break**,
not just photo upload.

The mechanism is ordinary Django: a new `CharField(blank=True)` is added
as `NOT NULL DEFAULT ''` and the default is then dropped, leaving a
`NOT NULL` column with no database default. Older code does not know the
field, omits it from its `INSERT`, and Postgres rejects the row. Nothing
about this is specific to D33 — **any release that adds a non-nullable
column without a database default behaves this way.**

Nothing warns you because `migrate` does not object to a database holding
migration records that aren't on disk. It applies what it knows and exits
0, so `set -e` never trips.

### The trap: roll the schema back *first*, from the outgoing image

The command that undoes a migration needs the migration **file** in order
to reverse it. The image you are rolling back to does not have that file.
So:

```
# From the image you are rolling back FROM — i.e. before you swap:
manage.py migrate <app> <target_migration>
```

Running the same command from the rolled-back image **exits 0 and does
nothing** — measured; it reports "No migrations to apply" and leaves the
column in place, because Django cannot see a migration it does not have.
That is the same silent success as above, one layer deeper, and it is the
step most likely to convince an operator the rollback worked when it did
not. **Verify against the database, not the exit code.**

### The procedure

1. **Find which migrations the target release lacks.** From a checkout:

   ```
   git diff --name-only --diff-filter=A <target-commit> <current-commit> \
       -- 'backend/apps/*/migrations/*.py'
   ```

2. **Work out the down-migrate target per app** — the migration
   immediately *before* the earliest one that list names for that app.
   (`manage.py showmigrations <app>` prints the ordered list.) Use `zero`
   to unwind an app completely.
3. **Down-migrate, from the currently-deployed image**, before swapping
   anything.
4. **Confirm against the database** that the columns are gone:

   ```
   select table_name, column_name from information_schema.columns
    where column_name = '<the column>';
   ```

5. **Then** deploy the older image.

### Worked example: rolling back past D33

D33 added a digest column beside each of the four stored-image columns,
in three migrations. The full sequence, run for real:

```
manage.py migrate activities 0004     # from the outgoing image
manage.py migrate sightings  0001
manage.py migrate accounts   0013
```

Confirmed afterwards: zero `%sha256%` columns remain, and the rolled-back
code writes photos and organizations again.

### Rolling forward again

Re-deploying the fixed image is enough — the entrypoint's own `migrate`
re-applies everything. Verified on real data, including the case that
looks riskiest: a photo written **during** the rollback window, by code
that knew nothing about digests, comes back with a correct digest,
because the backfill is guarded by `WHERE image_sha256 = ''` and so is
idempotent. Nothing has to be repaired by hand.

### Before you rely on any of this

- **Every data migration in this repository is currently reversible** —
  verified with `manage.py sqlmigrate --backwards` on all six
  `RunPython`/`RunSQL` migrations, which is the authoritative check
  (grepping for `reverse_sql`/`reverse_code` misses a reverse passed
  positionally). This is a property of each migration, not a guarantee
  the framework enforces: a future migration written without a reverse
  makes the release above it un-rollbackable, and the failure appears
  only when you try.
- **Check what you are rolling back *to* actually exists.** At the time
  of writing the frontend publishes only a mutable `latest` tag, so there
  is no earlier frontend image to roll back to at all; the backend
  carries two commit-sha tags that predate several security fixes and are
  accidental residue rather than policy. `docker-publish.yml` already
  builds both images as a matched set from a `vX.Y.Z` tag — that
  mechanism exists and has never been used. See `docs/open-questions.md`,
  "Tech / infrastructure" (D37).
- **Roll back both halves together.** Because builds are conditional per
  folder, backend and frontend `latest` come from different commits, and
  API shapes do change between releases — D30 changed
  `/api/notifications/` from a bare list to an object. "Roll back only
  the broken half" is not safe unless you have checked that specific pair.

## Serving the public site on its own origin

The public site can run on an origin of its own, isolated from the
authenticated app — the decided direction for hosting author-supplied
content, since Habitat's session and CSRF cookies are host-only and so
can't reach a different hostname (see `docs/open-questions.md`, "Public
site storytelling / custom content"). No code change is needed to relocate
it; it is configuration plus DNS/TLS:

1. **DNS + TLS** for the public hostname, e.g.
   `public.habitat.dev.cravenator.com`. A normal single-host certificate
   is enough — the decision was one shared public subdomain, not
   per-tenant subdomains, so no wildcard is required.
2. **Serve the frontend at that hostname.** The same frontend image serves
   both: its `/public/...` routes are what a visitor lands on. It needs
   `VITE_API_URL` pointing at the API, like any other build.
3. **Backend config:**
   - `PUBLIC_SITE_URL=https://public.habitat.dev.cravenator.com` — every
     public link and QR code the app generates then points there.
   - Add the public origin to `CORS_ALLOWED_ORIGINS` so the public pages
     can read `/api/public/...` cross-origin.
   - Set `CSRF_TRUSTED_ORIGINS` to the **app's** origin only. This is the
     reason the two lists are separate: the public origin must be able to
     read the public API, but must never be trusted for state-changing
     requests against the authenticated app — trusting an origin that
     serves author-supplied content is exactly what isolating it prevents.
   - Add the public hostname to `ALLOWED_HOSTS` if the backend is reached
     through it.
4. **Frontend build:** `VITE_PUBLIC_SITE_URL` set to the same origin, so
   the app's outbound links ("View public site", the nav entry, QR-code
   previews) point at the public site rather than at themselves.

Leaving `PUBLIC_SITE_URL`/`VITE_PUBLIC_SITE_URL` unset keeps the
pre-relocation behavior exactly: the public pages are served from the
app's own origin, and every link resolves against whatever origin the
browser is already on.

Note the asymmetry between the two: the backend prefers `PUBLIC_SITE_URL`
over the origin a client sends when generating a QR code. A QR code is a
physical artifact that outlives the session that made it, so once a
deployment has stated where the public site lives, the server uses that
rather than a value a caller supplied.

## Enabling custom-HTML pages

`HABITAT_CUSTOM_PAGE_HTML=1` lets an organization author a public page as
its own HTML/CSS/JavaScript document rather than markdown (the owner's
2026-09-02 decision — see `open-questions.md`). It's off by default, so
no deployment starts serving author-supplied documents just by upgrading.

What makes this safe to enable is **not** this flag and **not** which
hostname serves the public site: it's that such a page is never inlined
into the public site's DOM. It's served as its own document under
`Content-Security-Policy: sandbox allow-scripts` and embedded in an
`<iframe sandbox="allow-scripts">` — no `allow-same-origin` in either
place — so the browser gives it a unique opaque origin with no cookies,
no storage, and no access to the embedding page. That holds on any
origin. Details in `data-model-notes.md` ("Custom HTML/JS pages").

Recommended production shape is still to enable it **together with** the
public-site relocation above: the sandbox isolates author content from
the app, and a separate origin isolates it again. They're independent
settings, and either works without the other.

Two more things worth knowing before turning it on:

- **The per-tenant kill-switch is `Organization.custom_html_allowed`**,
  editable only from Django admin (deliberately not from an org's own
  admin console). Setting it False stops that organization authoring new
  HTML pages *and* stops its already-published ones rendering — the
  document endpoint 404s and the public payload's `document_url` goes
  null. Turning the deployment flag itself back off has the same effect
  for every org. Nothing is deleted either way; flipping it back on
  restores the pages as they were.
- **This is a policy decision as much as a technical one.** The sandbox
  stops author script reaching Habitat or its users' sessions. It does
  not stop an author misleading the visitors of their *own* page. There's
  no content policy written yet (noted in `data-model-notes.md`); the
  kill-switch is the response after the fact.

---

[Manual index](manual/README.md) · [Open questions](open-questions.md) · [Data model notes](data-model-notes.md)
