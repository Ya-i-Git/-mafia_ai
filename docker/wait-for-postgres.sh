#!/bin/bash
set -e

host="${POSTGRES_HOST:-postgres}"
port="${POSTGRES_PORT:-5432}"
user="${POSTGRES_USER:-mafia_user}"
db="${POSTGRES_DB:-mafia_db}"

echo "Waiting for PostgreSQL at $host:$port..."

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -p "$port" -U "$user" -d "$db" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - executing command"
exec "$@"
