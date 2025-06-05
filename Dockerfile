# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg-dev \
    libfontconfig1 \
    libgirepository1.0-dev \
    gir1.2-gtk-3.0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/db /app/migrations /app/static

# Create a script to initialize database and start the app
RUN echo '#!/bin/bash\n\
if [ ! -f /app/db/invoice_gen.db ]; then\n\
    echo "Initializing database..."\n\
    export FLASK_APP=app_factory.py\n\
    export FLASK_ENV=production\n\
    if [ ! -f /app/migrations/alembic.ini ]; then\n\
        flask db init\n\
    fi\n\
    flask db migrate -m "Initial migration"\n\
    flask db upgrade\n\
fi\n\
gunicorn --bind 0.0.0.0:8080 --workers 4 "app_factory:create_app()"\n' > /app/start.sh && chmod +x /app/start.sh

# Set environment variables
ENV FLASK_APP=app_factory.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run the start script
CMD ["/app/start.sh"]
