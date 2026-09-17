# Two images from one file, selected with `--target`:
#
#   --target dev         `manage.py runserver`. What docker-compose.yml
#                        builds, and what the dev instance runs.
#   --target production   gunicorn + WhiteNoise, static files collected at
#                        build time. What a `vX.Y.Z` tag publishes.
#
# `production` is last, so a bare `docker build ./backend` with no target
# produces the one that is safe to put on the internet. Anything wanting
# the dev image has to say so — docker-compose.yml does.
#
# Until 2026-09-17 there was only the dev image, and its header said the
# production question was the owner's and downstream of an undecided
# hosting model. That was true and is no longer: the owner decided
# (2026-09-17) that habitat.dev.cravenator.com stays permanently dev and
# production gets its own domain, stood up from a version-tagged image.
# Following that plan against the old single-stage file would have put
# Django's development server — which Django's own docs say not to use in
# "anything resembling a production environment" — on the public internet.

# ---------------------------------------------------------------------
# base — system libraries, Python dependencies, application code.
# ---------------------------------------------------------------------
FROM python:3.12-slim AS base

# GeoDjango needs GDAL/GEOS/PROJ system libraries — this is why local dev
# is meant to run through Docker rather than a bare virtualenv. See
# ../CLAUDE.md and ../docs/tech-stack-options.md.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

# Build identity, baked in so /api/health/ can answer "what is running?"
# without the deployment having to tell it (D43). Set by
# ../.github/workflows/docker-publish.yml from the git tag and commit;
# empty in a local `docker build`, which the endpoint reports as null
# rather than guessing.
#
# Declared in `base` so BOTH targets inherit it — the dev image is what the
# dev host runs, and "which build is the dev host on?" is the question that
# has no answer today, since `latest` is rebuilt on every push to main.
# Placed after `COPY . .` on purpose: that layer already changes on every
# commit, so setting these here invalidates nothing that costs anything.
ARG HABITAT_VERSION=""
ARG HABITAT_REVISION=""
ENV HABITAT_VERSION=${HABITAT_VERSION} \
    HABITAT_REVISION=${HABITAT_REVISION}

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

# ---------------------------------------------------------------------
# dev — unchanged behaviour, deliberately.
# ---------------------------------------------------------------------
FROM base AS dev
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---------------------------------------------------------------------
# production
# ---------------------------------------------------------------------
FROM base AS production

# Collect static into STATIC_ROOT at *build* time, so the running
# container needs no writable filesystem and no start-up step for it.
#
# Two values exist only for the length of this command and neither ends up
# in the image: SECRET_KEY because settings.py requires one to import (the
# collected files do not depend on it, and the real key arrives from the
# environment at run time), and DEBUG=0 because that is what selects
# CompressedManifestStaticFilesStorage — the whole point, since it writes
# the hashed names and the .gz/.br copies WhiteNoise serves.
#
# collectstatic does not open a database connection, which is what makes
# this possible during a build with no `db` service to talk to. Verified
# rather than assumed: run against an unreachable POSTGRES_HOST it still
# exits 0.
# No --clear: the directory starts empty in a fresh build (its .gitkeep
# aside), and --clear is the flag that deletes that .gitkeep for anyone who
# copies this line into a local shell.
RUN DEBUG=0 SECRET_KEY=collectstatic-build-time-only \
    python manage.py collectstatic --noinput

# One worker, several threads — and the worker count is load-bearing, not
# a performance guess.
#
# DRF's throttles (apps/accounts/throttling.py) keep their state in the
# Django cache, there is no CACHES setting, and Django's default
# LocMemCache is **per process**. So N gunicorn workers make the login
# limit N times looser than the number written in the code, silently, with
# no error and nothing visible in any response. One worker keeps the limit
# exactly what it says.
#
# Threads are the concurrency instead, and they are not a consolation
# prize here: the expensive thing this app does is pbkdf2, and CPython's
# hashlib releases the GIL for it. Measured rather than assumed, on the
# pinned Python and four cores: four concurrent 1,000,000-iteration hashes
# finish in **1.23x** the wall time of one, not 4x. So a single worker
# still hashes four logins in parallel, which is the specific thing a
# thread pool would be useless for if the GIL were held.
#
# Raising GUNICORN_WORKERS is possible and is a decision, not a knob: it
# requires giving the throttle a shared cache backend first. See
# docs/deployment-config.md, "Running more than one replica" — the same
# constraint, for the same reason, one level up.
ENV GUNICORN_WORKERS=1 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=60
CMD ["sh", "-c", "exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --worker-class gthread \
    --timeout ${GUNICORN_TIMEOUT} \
    --access-logfile - \
    --error-logfile -"]
