#!/bin/bash
set -e

echo "🚀 Starting Griot..."
echo "🔍 Debug: Environment variables loaded"
echo "🔍 Debug: Current working directory: $(pwd)"
echo "🔍 Debug: Python version: $(python --version)"

# Wait for services
echo "🔍 Debug: Waiting for PostgreSQL..."
timeout=30
counter=0
while ! pg_isready -h postgres -p 5432 -U postgres >/dev/null 2>&1; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -gt $timeout ]; then
        echo "❌ PostgreSQL timeout"
        exit 1
    fi
done
echo "✅ PostgreSQL is ready"

echo "🔍 Debug: Waiting for Redis..."
counter=0
while ! redis-cli -h redis -p 6379 -a "$REDIS_PASSWORD" ping >/dev/null 2>&1; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -gt $timeout ]; then
        echo "❌ Redis timeout"
        exit 1
    fi
done
echo "✅ Redis is ready"

# Initialize services
echo "🔍 Debug: Initializing services..."
./scripts/init-music.sh >/dev/null 2>&1

echo "🔍 Debug: Checking database initialization..."
INIT_LOCK_FILE="/tmp/griot_initialized"
if [ ! -f "$INIT_LOCK_FILE" ]; then
    echo "🔍 Debug: Running database initialization..."
    cd /app
    python scripts/init_database.py
    # Ensure subscription migration script runs as part of standard migrations (idempotent)
    # This is a safeguard in case migrate_schema misses certain cases
    if [ -f "./scripts/migrate_add_subscription_columns.py" ]; then
        echo "🔧 Running subscription columns migration script..."
        python ./scripts/migrate_add_subscription_columns.py || echo "⚠️ Subscription migration script failed (continuing)"
    fi
    touch "$INIT_LOCK_FILE"
fi

# Always check and fix invalid password hashes (runs on every startup)
# This catches users who registered with bad hashes after initial deployment
echo "🔧 Checking for invalid password hashes..."
cd /app
python ./scripts/fix_password_hashes.py || echo "⚠️ Password hash fixing failed (continuing)"

# Reset users if requested
if [ "${RESET_USERS:-false}" = "true" ]; then
    echo "🔄 Resetting users as requested..."
    cd /app
    python scripts/reset_users.py
fi

echo "🔍 Debug: Starting uvicorn server..."
WORKER_COUNT=${UVICORN_WORKERS:-4}
if [ "${DEBUG:-false}" = "true" ]; then
    echo "🔍 Debug: Starting in debug mode with reload"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --no-access-log
else
    echo "🔍 Debug: Starting in production mode with $WORKER_COUNT worker(s)"
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers $WORKER_COUNT --no-access-log
fi