FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p static/logos

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose the port the app runs on
EXPOSE 8765

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=8765"] 