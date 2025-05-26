# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We'll also install libreoffice here for the PDF conversion, and other OS-level dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends     libreoffice     # Add other OS-level dependencies for WeasyPrint if needed, e.g.,
    # libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1
    # For now, let's assume WeasyPrint's Python package handles its direct deps
    # or that they are covered by the base image or libreoffice install.
    && rm -rf /var/lib/apt/lists/*     && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

RUN python -c "from app import init_db; init_db()"

# Initialize the database
# Ensure schema.sql is present and app.py can initialize the DB.
# We might need a small script to run init_db() if flask run doesn't trigger it appropriately on first start.
# For now, assume app.py handles DB initialization if it doesn't exist.
# If not, we'll add a RUN command here later: RUN python -c "from app import init_db; init_db()"

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variables
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8080
# ENV FLASK_ENV production # Uncomment for production

# Run app.py when the container launches
# Using Gunicorn for production is better, but let's start with flask run for simplicity.
# We will refine this to use Gunicorn later.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
