# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We'll also install libreoffice here for the PDF conversion, and other OS-level dependencies.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    libreoffice \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg-dev \
    libfontconfig1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/static/logos && \
    chmod -R 777 /app/static/logos

# Copy the rest of the application code into the container at /app
COPY . .

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variables
ENV FLASK_APP=wsgi.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Use entrypoint.sh as the container's CMD
CMD ["/app/entrypoint.sh"]
