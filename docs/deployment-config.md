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

## Frontend (Vite, `import.meta.env`)

Vite inlines these **at build time**, so they belong to the image build,
not the running container.

| Variable | Default | What it does |
| --- | --- | --- |
| `VITE_API_URL` | `http://localhost:8000/api` | Where the SPA calls the API. |
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

These are still the **development** images: the backend runs
`manage.py runserver` and the frontend runs Vite's dev server. Whether to
add production images is an open question — see `docs/open-questions.md`,
"Tech / infrastructure".

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
