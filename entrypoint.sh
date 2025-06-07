#!/bin/bash

export FLASK_ENV=production

# Ensure the database directory exists and has proper permissions
mkdir -p /app/db
chmod 777 /app/db

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Create database tables if they don't exist
echo "Creating database tables..."
python3 -c "from app_factory import create_app; app = create_app(); app.app_context().push()"

# Start the application with proper configuration
exec gunicorn --bind 0.0.0.0:8080 --workers 4 "app_factory:create_app()" 