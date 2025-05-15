## Description

Currently, the application is not packaged for containerized deployment, which can make setup and deployment more complex for users. Packaging the entire repository in a Docker container will simplify deployment, ensure consistency across environments, and make it easier for others to contribute or run the application.

## Current Behavior

- The application must be set up manually, with dependencies installed individually.
- Deployment steps may vary between environments, leading to inconsistencies.

## Expected Behavior

- The repository includes a Dockerfile and (optionally) a docker-compose.yml for easy setup.
- Users can build and run the application with a single Docker command.
- All dependencies are installed and configured automatically within the container.
- The application runs consistently across different environments.

## Technical Details

- Create a Dockerfile that installs all necessary dependencies and sets up the application.
- (Optional) Create a docker-compose.yml for multi-container setups (e.g., with a database).
- Update documentation to include Docker usage instructions.

## Acceptance Criteria

- [ ] A Dockerfile is present in the repository
- [ ] Users can build and run the application using Docker
- [ ] All dependencies are installed and configured within the container
- [ ] The application runs consistently across environments
- [ ] Documentation includes Docker usage instructions