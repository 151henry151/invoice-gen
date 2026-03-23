#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running tests in Docker container...${NC}"

# Run the tests
docker-compose -f docker-compose.dev.yml exec web pytest "$@"

# Capture the exit code
EXIT_CODE=$?

# Check if tests passed
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
else
    echo -e "\n${RED}Some tests failed.${NC}"
fi

exit $EXIT_CODE 