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
  *)
    exec "$@"
    ;;
esac
