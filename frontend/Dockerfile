# Local dev / dev-instance image: this runs Vite's *dev server*, not a
# production build. Whether to add a production image (a built bundle
# behind a static server) is an open question for the owner — see
# /docs/open-questions.md, "Tech / infrastructure" — and is downstream of
# the still-undecided hosting model. This file deliberately doesn't
# answer it; it only makes the image reproducible.
FROM node:20-slim

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

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
