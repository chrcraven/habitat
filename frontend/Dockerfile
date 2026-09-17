# Two images from one file, selected with `--target`:
#
#   --target dev         Vite's dev server. What docker-compose.yml builds,
#                        and what the dev instance runs.
#   --target production   `vite build` output served by nginx. What a
#                        `vX.Y.Z` tag publishes.
#
# `production` is last, so a bare `docker build ./frontend` with no target
# produces the one that is safe to put on the internet.
#
# The header this file carried until 2026-09-17 deferred the production
# image to the owner as downstream of an undecided hosting model. That is
# now decided (permanently-dev dev host, production on its own domain,
# released from a version tag), so following the plan with only the dev
# image would have served unminified source over HMR to real users.
#
# **The thing to know before editing this file**: `VITE_*` values are
# substituted into the bundle by `vite build`, not read at run time.
# Measured — building with VITE_API_URL set to a marker leaves that exact
# string in dist/assets/*.js, and `import.meta.env` appears zero times in
# the output. So a build arg here would bake one deployment's URLs into
# the image and break the "publish once, deploy anywhere" release plan, and
# no ConfigMap could override it afterwards. It is left out on purpose:
# src/api/client.ts defaults a production build to a **relative** /api, so
# the image is deployment-neutral and the reverse proxy decides what that
# resolves to. See docs/deployment-config.md.

# ---------------------------------------------------------------------
# deps — node_modules, from the lockfile, shared by every stage below.
# ---------------------------------------------------------------------
FROM node:20-slim AS deps

WORKDIR /app

# Both manifests, then `npm ci` — not `npm install` against package.json
# alone, which is what this did until 2026-09-05.
#
# `npm ci` installs exactly what package-lock.json pins, which is also
# the set .github/workflows/tests.yml validates, so a green CI run and
# this image finally agree on their dependencies. Resolving fresh let
# them drift silently instead: measured on 2026-09-05, a lockfile-free
# install of this very package.json produced 37 differently-versioned
# packages than the committed lockfile (react-router-dom among them,
# 6.30.4 vs 6.30.6) — same machine, same hour. `npm ci` also fails loudly
# if the two files fall out of sync, rather than quietly resolving
# something nobody has tested.
COPY package.json package-lock.json ./
RUN npm ci

# ---------------------------------------------------------------------
# dev — unchanged behaviour, deliberately.
# ---------------------------------------------------------------------
FROM deps AS dev

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]

# ---------------------------------------------------------------------
# build — `tsc -b && vite build`, so a type error fails the image build
# rather than shipping.
# ---------------------------------------------------------------------
FROM deps AS build

COPY . .
RUN npm run build

# ---------------------------------------------------------------------
# production — static files, nothing else. No Node in the final image.
# ---------------------------------------------------------------------
FROM nginx:1.27-alpine AS production

# Declared, and deliberately unused. The publish workflow passes the build
# identity to both images uniformly (D43), and nginx has no runtime that
# could report it — the backend's /api/health/ answers that question for the
# deployment, and this image's OCI labels answer it for `docker inspect`.
# Declaring them here keeps the workflow free of a per-image special case
# and stops the build warning about arguments nothing consumed. If this
# image ever wants to stamp its own version, the plumbing is already here.
ARG HABITAT_VERSION=""
ARG HABITAT_REVISION=""

# Replaces the stock default.conf rather than adding beside it; two server
# blocks both listening on 80 for `_` would make which one answers depend
# on file ordering.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

# The stock image runs its master as root and its workers as `nginx`. A
# cluster enforcing a restricted pod security standard wants
# `nginxinc/nginx-unprivileged` instead, which listens on 8080 and needs
# the port changed in nginx.conf to match.
EXPOSE 80
