#!/bin/bash

# Check if the database file exists
if [ ! -f /app/db/invoice_gen.db ]; then
    echo "Database file not found. Initializing database..."
    # Initialize the database
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
else
    echo "Database file exists. Running migrations..."
    flask db upgrade
fi

# Start the application
exec gunicorn --bind 0.0.0.0:8080 wsgi:application 