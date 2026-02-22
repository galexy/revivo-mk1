#!/usr/bin/env bash
# Setup PostgreSQL and Mailpit for local development (Claude Code Web or bare-metal).
#
# This script is idempotent — safe to run multiple times.
# It starts PostgreSQL, configures password auth for the postgres user,
# creates the required databases, and installs/starts Mailpit.
#
# Usage:
#   sudo bash scripts/setup-postgres.sh
#
# Skip this script when developing inside the Docker Compose devcontainer,
# which provides its own PostgreSQL and Mailpit services.

set -euo pipefail

PG_VERSION="${PG_VERSION:-16}"
PG_USER="postgres"
PG_PASSWORD="postgres"
DATABASES=("personal_finance" "finance_test" "jobs")

MAILPIT_VERSION="${MAILPIT_VERSION:-v1.29.1}"

HBA_FILE="/etc/postgresql/${PG_VERSION}/main/pg_hba.conf"

# ── 1. Ensure PostgreSQL is running ──────────────────────────────────────────

if pg_isready -q 2>/dev/null; then
    echo "PostgreSQL is already running."
else
    echo "Starting PostgreSQL ${PG_VERSION}..."
    pg_ctlcluster "${PG_VERSION}" main start || true
    # Wait for it to become ready
    for i in {1..10}; do
        if pg_isready -q 2>/dev/null; then
            break
        fi
        sleep 1
    done
    if ! pg_isready -q 2>/dev/null; then
        echo "ERROR: PostgreSQL failed to start." >&2
        exit 1
    fi
    echo "PostgreSQL started."
fi

# ── 2. Configure password authentication for localhost TCP connections ───────

# Allow md5 (password) auth for local TCP — needed by asyncpg / psycopg2.
# Only modify if the file still has scram-sha-256 (the Ubuntu default).
if grep -q 'scram-sha-256' "$HBA_FILE" 2>/dev/null; then
    echo "Updating pg_hba.conf to use md5 auth for TCP connections..."
    sed -i 's/scram-sha-256/md5/g' "$HBA_FILE"
    pg_ctlcluster "${PG_VERSION}" main reload
    echo "pg_hba.conf updated and PostgreSQL reloaded."
fi

# ── 3. Set postgres user password ────────────────────────────────────────────

echo "Setting password for user '${PG_USER}'..."
su - postgres -c "psql -c \"ALTER USER ${PG_USER} PASSWORD '${PG_PASSWORD}';\"" > /dev/null 2>&1

# ── 4. Create required databases ─────────────────────────────────────────────

for db in "${DATABASES[@]}"; do
    if su - postgres -c "psql -lqt" | cut -d'|' -f1 | grep -qw "$db"; then
        echo "Database '${db}' already exists."
    else
        echo "Creating database '${db}'..."
        su - postgres -c "createdb -O ${PG_USER} ${db}"
        echo "Database '${db}' created."
    fi
done

echo ""
echo "PostgreSQL setup complete."
echo "  Host:      localhost"
echo "  Port:      5432"
echo "  User:      ${PG_USER}"
echo "  Password:  ${PG_PASSWORD}"
echo "  Databases: ${DATABASES[*]}"

# ── 5. Install and start Mailpit ─────────────────────────────────────────────

if command -v mailpit &>/dev/null; then
    echo ""
    echo "Mailpit is already installed: $(mailpit version)"
else
    echo ""
    echo "Installing Mailpit ${MAILPIT_VERSION}..."
    ARCH="$(uname -m)"
    case "$ARCH" in
        x86_64)  MAILPIT_ARCH="linux-amd64" ;;
        aarch64) MAILPIT_ARCH="linux-arm64" ;;
        *)       echo "WARNING: Unsupported architecture ${ARCH}, skipping Mailpit." ; MAILPIT_ARCH="" ;;
    esac
    if [ -n "$MAILPIT_ARCH" ]; then
        curl -sL --max-time 30 \
            "https://github.com/axllent/mailpit/releases/download/${MAILPIT_VERSION}/mailpit-${MAILPIT_ARCH}.tar.gz" \
            | tar -xzf - -C /usr/local/bin mailpit
        chmod +x /usr/local/bin/mailpit
        echo "Mailpit installed: $(mailpit version)"
    fi
fi

# Start Mailpit if not already running
if pgrep -x mailpit &>/dev/null; then
    echo "Mailpit is already running."
else
    echo "Starting Mailpit (SMTP :1025, Web UI :8025)..."
    nohup mailpit --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025 \
        --smtp-auth-accept-any --smtp-auth-allow-insecure \
        > /tmp/mailpit.log 2>&1 &
    sleep 1
    if pgrep -x mailpit &>/dev/null; then
        echo "Mailpit started (PID $(pgrep -x mailpit))."
    else
        echo "WARNING: Mailpit failed to start. Check /tmp/mailpit.log"
    fi
fi

echo ""
echo "Connection URLs:"
echo "  DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/personal_finance"
echo "  DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/personal_finance"
echo "  TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finance_test"
echo "  JOB_QUEUE_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobs"
echo ""
echo "Mailpit:"
echo "  SMTP:   localhost:1025"
echo "  Web UI: http://localhost:8025"
