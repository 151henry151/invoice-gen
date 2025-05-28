#!/bin/sh
set -e
echo "Checking for invoices table in /app/db/invoice_gen.db..."
if ! sqlite3 /app/db/invoice_gen.db "SELECT name FROM sqlite_master WHERE type='table' AND name='invoices';" | grep -q invoices; then
  echo "Initializing database schema..."
  python -c "from app import init_db; init_db()"
  echo "Schema initialization complete. Tables in /app/db/invoice_gen.db:"
  sqlite3 /app/db/invoice_gen.db ".tables"
else
  echo "Invoices table already exists."
fi
exec gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 wsgi:application 