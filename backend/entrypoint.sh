#!/bin/sh
# Runs on every backend container start (see ../CLAUDE.md and
# ../docker-compose.yml). Waits for Postgres to accept connections, then
# applies migrations, then hands off to the container's real CMD
# (runserver in dev; a real deploy would override CMD, not this script).
#
# Both images run this — the dev one before `runserver`, the production
# one before gunicorn — and that is a decision resting on an assumption
# the owner stated on 2026-09-17: Kubernetes, `replicas: 1`. One pod means
# one start, so there is nothing to race.
#
# The assumption is one command away from being false. `kubectl scale
# --replicas=2` needs no code change, no rebuild and no review, produces
# no error, and would have two pods run `migrate` against the same
# database at once. That is the failure shape this repo keeps finding:
# right until it quietly isn't. docs/deployment-config.md, "Running more
# than one replica", names what has to move first (this call to an
# initContainer or a Job, the purge below to a CronJob, and the login
# throttle to a shared cache). Read that before scaling, not after.
set -e

POSTGRES_HOST="${POSTGRES_HOST:-db}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

echo "entrypoint: waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until python - <<'PYEOF'
import os, socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((os.environ["POSTGRES_HOST"], int(os.environ["POSTGRES_PORT"])))
except OSError:
    sys.exit(1)
else:
    s.close()
    sys.exit(0)
PYEOF
do
    sleep 1
done
echo "entrypoint: database is accepting connections."

echo "entrypoint: applying migrations..."
python manage.py migrate --noinput

# Honour the 30-day soft-delete retention window the app promises its users
# (docs/manual/properties.md). Idempotent and almost always a no-op, so
# it's cheap to run on every boot; the "Recently deleted" admin views run
# the same sweep lazily in between restarts. See apps/accounts/purging.py.
#
# Deliberately NOT under `set -e`: a purge that fails is a problem to fix,
# not a reason to stop the application from starting.
echo "entrypoint: purging expired soft-deleted properties..."
python manage.py purge_deleted_properties || \
    echo "entrypoint: WARNING: purge failed; continuing startup."

echo "entrypoint: starting: $*"
exec "$@"
