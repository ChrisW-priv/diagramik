#!/bin/sh

set -o errexit
set -o pipefail

. /app/.venv/bin/activate

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

migrate() {
    log "Running migrations"
    python django_monolith/manage.py migrate
}

collect_static() {
    log "Collecting static files"
    python django_monolith/manage.py collectstatic --no-input
}

ensuresuperuser() {
    log "Creating superuser"
    python django_monolith/manage.py ensuresuperuser
}

setup() {
    log "Executing setup scripts"
    ensuresuperuser
    migrate
    collect_static
}

run_server() {
    log "Running django dev server"
    python django_monolith/manage.py runserver 0.0.0.0:8080 --noreload
}

run_wsgi() {
    log "Running wsgi server"
    cd django_monolith
    gunicorn --bind 0.0.0.0:8080 backend.wsgi:application
}

run_asgi() {
    log "Running asgi server with h2c support"
    cd django_monolith
    hypercorn backend.asgi:application --bind 0.0.0.0:8080
}

# Handle arguments using case statement (POSIX compliant)
case "$1" in
    migrate|collect_static|ensuresuperuser|setup|run_server|run_wsgi|run_asgi)
        "$1"
        ;;
    "")
        setup
        run_asgi
        ;;
    *)
        "$@"
        ;;
esac
