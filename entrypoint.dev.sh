#!/bin/bash

export FLASK_ENV=development

# Initialize database if it doesn't exist
if [ ! -f /app/db/invoice_gen.db ]; then
    echo "Initializing database..."
    if [ ! -f /app/migrations/alembic.ini ]; then
        flask db init
    fi
    flask db migrate -m "Initial migration"
    flask db upgrade
fi

# Start Flask development server
exec flask run --host=0.0.0.0 --port=8080 --debug 