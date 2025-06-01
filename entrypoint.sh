#!/bin/bash

# Ensure the database directory exists and has proper permissions
mkdir -p /app/db
chmod 777 /app/db

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Create database tables if they don't exist
echo "Creating database tables..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"

# Start the application
exec gunicorn --bind 0.0.0.0:8080 app:app 