#!/usr/bin/env sh
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'


echo ${GREEN} "Starting application in $ENVIRONMENT mode..." ${NC}
echo ${GREEN} "Host: 0.0.0.0, Port: $BACKEND_PORT" ${NC}

run_migrations() {
    echo "${GREEN}Applying database migrations...${NC}"
    poetry run alembic upgrade head
}

case "$1" in
  dev)
    echo ${GREEN} "Running development stage..." ${NC}
    run_migrations
    exec poetry run uvicorn src.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
    ;;
  prod)
    echo ${GREEN} "Running production stage..." ${NC}
    run_migrations
    exec poetry run gunicorn src.main:app \
      -k uvicorn_worker.UvicornWorker \
      -w $BACKEND_WORKERS \
      -b 0.0.0.0:$BACKEND_PORT \
      --timeout 60
    ;;
  test)
    # The suite runs against a real PostgreSQL, so the schema has to be there
    # before pytest starts: without this, every test that touches a migrated
    # table fails on `relation "users" does not exist` instead of on its own
    # assertion. Applied here rather than in the test command so it survives the
    # per-scope overrides that `make test-unit`, `make test-integration` and
    # `make test-e2e` pass as arguments.
    echo ${GREEN} "Running testing stage..." ${NC}
    run_migrations
    shift
    exec "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
