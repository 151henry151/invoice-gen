#!/bin/bash

# Function to display usage
show_usage() {
    echo "Usage: ./switch-env.sh [dev|prod]"
    echo "  dev  - Switch to development environment"
    echo "  prod - Switch to production environment"
    exit 1
}

# Check if argument is provided
if [ $# -ne 1 ]; then
    show_usage
fi

# Stop any running containers
echo "Stopping current environment..."
docker-compose down

# Switch based on argument
case "$1" in
    "dev")
        echo "Switching to development environment..."
        DOCKERFILE=Dockerfile.dev FLASK_ENV=development docker-compose up --build
        ;;
    "prod")
        echo "Switching to production environment..."
        docker-compose up --build
        ;;
    *)
        show_usage
        ;;
esac 