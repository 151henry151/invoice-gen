#!/bin/bash

# If running inside the container, just run the script
if grep -q "/app" /proc/1/cmdline; then
    echo "Running test harness inside container..."
    export PYTHONPATH=/app:$PYTHONPATH
    python tests/test_harness.py
    exit $?
fi

# Otherwise, run inside the docker container
CONTAINER=$(docker ps --filter "name=invoice-gen-web-1" --format "{{.ID}}")
if [ -z "$CONTAINER" ]; then
    echo "Error: invoice-gen-web-1 container is not running. Please start the dev environment first."
    exit 1
fi

echo "Running test harness inside Docker container..."
docker exec -it $CONTAINER bash -c "export PYTHONPATH=/app:\$PYTHONPATH && python tests/test_harness.py"

# Check if the script was successful
if [ $? -eq 0 ]; then
    echo "Test harness completed successfully!"
    echo "You can now log in to the application with the test user credentials."
    echo "A summary of the created test data is available in test_data_summary.json"
else
    echo "Test harness failed!"
    exit 1
fi 