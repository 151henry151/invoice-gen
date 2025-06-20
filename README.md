# Invoice Generator

Current Version: 0.9.0-beta.1

## Version History
- 0.9.0-beta.1: Initial beta release with core invoice generation functionality

## Versioning
This project follows [Semantic Versioning](https://semver.org/). For the versions available, see the [tags on this repository](https://github.com/yourusername/invoice-gen/tags).

> **Pre-Release Notice**: This project is currently under development and not yet fully functional. This is a pre-release version with ongoing development and improvements.

A professional invoice generator for small businesses and freelancers, built with Flask and modern web technologies. This app allows you to manage company and client details, add labor and itemized costs, and generate professional invoices.

## Documentation

- [User Guide](USER_GUIDE.md) - For end users: Learn how to use the application, manage clients, create invoices, and more.
- [Developer Documentation](#) - For developers: Technical documentation, API reference, and setup instructions (this README).

## Project Structure

```
invoice_gen/
├── app.py                # Main Flask application
├── requirements.txt      # Python dependencies
├── templates/            # Jinja2 HTML templates
│   └── index.html        # Main dashboard and invoice creation UI
├── static/               # Static files (CSS, JS, images)
│   └── logos/            # Uploaded company logos
├── venv/                 # Python virtual environment (not tracked in git)
└── ...                   # Other supporting files
```

## Development and Production Environments

The application supports both development and production environments. The environment can be toggled using environment variables in the `docker-compose.yml` file.

### Environment Toggle

To switch between development and production modes, you can use either of these methods:

1. Using the provided script (recommended):
   ```bash
   # For development mode
   ./switch-env.sh dev

   # For production mode
   ./switch-env.sh prod
   ```

2. Using docker-compose directly:
   ```bash
   # For development mode
   DOCKERFILE=Dockerfile.dev FLASK_ENV=development docker-compose up --build

   # For production mode
   docker-compose up --build
   ```

The script method is recommended as it handles stopping the current environment and provides clear feedback about the switching process.

### Key Differences

#### Development Mode
- Uses Flask's development server with hot-reloading
- Debug mode enabled
- Mounts local directories for live code changes
- Uses HTTP instead of HTTPS
- More verbose logging
- Development-specific settings:
  - `SESSION_COOKIE_SECURE = False`
  - `PREFERRED_URL_SCHEME = 'http'`
  - Debug PIN enabled for debugging
  - Hot-reloading enabled

#### Production Mode
- Uses Gunicorn as WSGI server
- Debug mode disabled
- Optimized for performance
- Uses HTTPS (when configured)
- Minimal logging
- Production-specific settings:
  - `SESSION_COOKIE_SECURE = True`
  - `PREFERRED_URL_SCHEME = 'https'`
  - Debug PIN disabled
  - Hot-reloading disabled

### Environment Variables

Key environment variables that control the environment:

- `FLASK_ENV`: Set to `development` or `production`
- `DOCKERFILE`: Set to `Dockerfile.dev` for development or `Dockerfile` for production
- `SECRET_KEY`: Different keys for development and production
- `SCRIPT_NAME`: Application root path (e.g., `/invoice`)

### Switching Environments

1. Stop the current environment:
   ```bash
   docker-compose down
   ```

2. Clear any cached data (optional):
   ```bash
   docker-compose down -v
   ```

3. Start the desired environment:
   ```bash
   # For development
   DOCKERFILE=Dockerfile.dev FLASK_ENV=development docker-compose up --build

   # For production
   docker-compose up --build
   ```

### Important Notes

- Always use different secret keys for development and production
- Development mode should never be used in production
- Keep development-specific settings in `Dockerfile.dev`
- Production settings should be secure by default
- Database migrations work in both environments
- Static files are served differently in each environment

## Google Maps API Key Setup (for Address Autocomplete)

To enable address autocomplete using Google Places in the business details form, you must obtain a Google Maps API key with the Places API enabled. Follow these steps:

1. **Create a Google Cloud Project**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Sign in with your Google account.
   - Click the project drop-down at the top and select **New Project**.
   - Enter a project name (e.g., "InvoiceGen Address Picker") and click **Create**.

2. **Enable Billing**
   - Go to the [Billing page](https://console.cloud.google.com/billing) and link your project to a billing account.
   - Google provides a generous free tier for Maps/Places usage.

3. **Enable the Places API**
   - In the Cloud Console, make sure your project is selected.
   - Go to the [Places API page](https://console.cloud.google.com/apis/library/places-backend.googleapis.com) and click **Enable**.
   - (Optional but recommended) Also enable the [Maps JavaScript API](https://console.cloud.google.com/apis/library/maps-backend.googleapis.com).

4. **Create an API Key**
   - Go to the [Credentials page](https://console.cloud.google.com/apis/credentials).
   - Click **+ Create Credentials** > **API key**.
   - Copy the generated API key.

5. **Restrict Your API Key (Recommended)**
   - On the Credentials page, click your new API key.
   - Under **API restrictions**, select **Restrict key** and choose **Places API** and **Maps JavaScript API**.
   - Under **Application restrictions**, select **HTTP referrers** and add your domain (e.g., `localhost` for local development, or your production domain).

6. **Configure Your Application**
   - Copy `example_credentials.ini` to `credentials.ini` in your project root.
   - Paste your API key as the value for `GOOGLE_MAPS_API_KEY` in `credentials.ini`.
   - **Do not commit `credentials.ini` to version control!** (It is already in `.gitignore`.)

7. **Further Reading**
   - See the [Google Maps Platform documentation](https://developers.google.com/maps/documentation/places/web-service/overview) for more details.

**Note:** The address picker will not function until a valid API key is provided.

## API Documentation

The application provides several RESTful API endpoints for managing invoices, clients, and settings. All endpoints require authentication unless specified otherwise.

### Authentication Endpoints

- `POST /register`
  - Register a new user
  - Required fields: username, password, email
  - Returns: Redirect to login page on success

- `POST /login`
  - Authenticate user
  - Required fields: username/email, password
  - Returns: Redirect to dashboard on success

- `GET /logout`
  - Log out current user
  - Returns: Redirect to login page

### Client Management

- `POST /new_client`
  - Create a new client
  - Required fields: name, address, email, phone
  - Returns: Redirect to dashboard with success message

- `GET /get_client/<client_id>`
  - Get client details
  - Returns: JSON object with client information
  ```json
  {
    "name": "string",
    "address": "string",
    "email": "string",
    "phone": "string"
  }
  ```

### Company Management

- `GET /get_company/<company_id>`
  - Get company details
  - Returns: JSON object with company information
  ```json
  {
    "name": "string",
    "address": "string",
    "email": "string",
    "phone": "string",
    "logo_path": "string"
  }
  ```

- `POST /update_company`
  - Update company details
  - Fields: company_name, company_address, company_email, hourly_rate, logo (optional)
  - Returns: Redirect to dashboard with success message

### Invoice Management

- `GET /check_invoice_number/<invoice_number>`
  - Check if invoice number exists
  - Returns: JSON object with existence status
  ```json
  {
    "exists": boolean
  }
  ```

- `GET /download/<invoice_number>`
  - Download invoice as Excel file
  - Returns: Excel file download

### Sales Tax Management

- `GET /api/sales-tax`
  - Get all sales tax rates
  - Returns: Array of tax rate objects
  ```json
  [
    {
      "id": number,
      "rate": number,
      "description": "string"
    }
  ]
  ```

- `POST /api/sales-tax`
  - Create new sales tax rate
  - Required fields: rate, description
  - Returns: Created tax rate object
  ```json
  {
    "id": number,
    "rate": number,
    "description": "string"
  }
  ```

- `DELETE /api/sales-tax`
  - Delete all sales tax rates
  - Returns: Success message

- `PUT /api/invoice/<invoice_id>/sales-tax`
  - Update invoice sales tax settings
  - Required fields: sales_tax_id, tax_applies_to
  - Returns: Updated invoice tax information
  ```json
  {
    "id": number,
    "sales_tax_id": number,
    "tax_applies_to": "string",
    "tax_rate": number,
    "tax_description": "string"
  }
  ```

### Session Management

- `POST /save_selections`
  - Save selected business and client IDs
  - Fields: businessId, clientId
  - Returns: Success status
  ```json
  {
    "success": boolean
  }
  ```

### Error Responses

All API endpoints may return the following error responses:

- `400 Bad Request`: Missing or invalid required fields
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side error

## Testing

The application includes a test harness for populating the database with test data. This is useful for manual testing and development purposes.

### Test Harness

The test harness is located in the `tests` directory and can be run using the provided script:

```bash
# Run the test harness
./tests/run_test_harness.sh
```

The test harness will:
1. Clear any existing test data
2. Create a test user with the following credentials:
   - Username: `testuser`
   - Password: `TestPass123!@#`
   - Email: `test@example.com`
3. Generate test data including:
   - 3 test businesses with generated logos
   - 5 test clients
   - 10 test items
   - 5 test labor items
   - 5 tax rates (0%, 5%, 10%, 15%, 20%)
   - 12 test invoices with various line items and labor entries
4. Generate a summary of the created data in `test_data_summary.json`

After running the test harness, you can log in to the application using the test user credentials to explore and test the functionality with the generated data.

### Test Environment

The test harness uses the application's database and automatically cleans up any existing test data before creating new test data. This ensures a clean state for testing while preserving any production data.

## Customizing Invoice Templates

The Invoice Generator uses a single HTML (Jinja2) template for invoice generation. You can customize this template to match your branding, layout, and required fields.

### HTML (Jinja2) Template

- **Location:** `invoice-gen/templates/invoice_pretty.html`
- **Format:** Standard HTML with [Jinja2](https://jinja.palletsprojects.com/) templating syntax.
- **Variables:** You can use variables such as `{{ business_name }}`, `{{ client_name }}`, `{{ invoice_number }}`, `{{ line_items }}`, etc. (see the template for all available variables).
- **How to Customize:**
  - Edit the HTML and CSS directly in the template file.
  - Use Jinja2 control structures (e.g., `{% for item in line_items %}`) to loop through items.
  - Add or remove fields as needed.
  - Preview changes by generating a new invoice and viewing it in the app.

#### Common variables available in the template:
- `business_name`, `business_address`, `business_email`, `business_phone`
- `client_name`, `client_address`, `client_email`, `client_phone`
- `invoice_number`, `invoice_date`, `notes`, `subtotal`, `sales_tax`, `grand_total`
- `line_items` (list of items, each with `date`, `description`, `quantity`, `unit_price`, `total`)

#### Tips
- Always back up your template before making major changes.
- After editing the template, generate a test invoice to ensure your changes render as expected.
- For advanced logic, use Jinja2 syntax in the template.

## Frameworks & Libraries Used

- **Flask**: Web framework for Python
- **Jinja2**: Templating engine for HTML
- **WeasyPrint**: For PDF generation (if used)
- **Bootstrap** (optional): For UI styling (if included in static)
- **JavaScript**: For dynamic UI updates (inline in templates)

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/151henry151/invoice-gen.git
   cd invoice-gen
   ```

2. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database Migrations**

   The project uses Alembic for database migrations. Here's how to work with migrations:

   a. **Initial Setup**
   ```bash
   # The migrations directory is already set up in the project
   # To create a new migration after model changes:
   flask db migrate -m "Description of changes"
   
   # To apply pending migrations:
   flask db upgrade
   ```

   b. **Common Migration Commands**
   ```bash
   # View migration history
   flask db history
   
   # Downgrade to a specific version
   flask db downgrade <revision_id>
   
   # Upgrade to the latest version
   flask db upgrade
   ```

   c. **Migration Best Practices**
   - Always create a new migration when making model changes
   - Test migrations both up and down before committing
   - Include meaningful descriptions in migration messages
   - Review generated migration files before applying them
   - Back up your database before running migrations in production

   d. **Troubleshooting**
   - If migrations fail, check the error message and the migration file
   - Use `flask db current` to see the current migration version
   - Use `flask db heads` to see the latest migration version
   - If needed, you can manually edit migration files before applying them

4. **Run the development server:**
   ```bash
   flask run
   ```
   The app will be available at `http://127.0.0.1:5000/`.

## Development Environment

The project includes a Docker-based development environment that provides hot-reloading, debugging tools, and a consistent development experience.

### Starting the Development Environment

1. **Build and start the development containers:**
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```

2. **Access the application:**
   - Main application: http://localhost:8080/invoice
   - Debug toolbar will be available in the browser

### Development Features

- **Hot Reloading**: Changes to Python files automatically trigger a server reload
- **Debug Mode**: Detailed error messages and Flask debug toolbar
- **Development Tools**: Testing, formatting, and linting tools included
- **Separate Database**: Development database is isolated from production
- **No Rebuilding**: Code changes don't require container rebuilds

### Development Commands

1. **View logs:**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f
   ```

2. **Run tests:**
   ```bash
   docker-compose -f docker-compose.dev.yml exec web pytest
   ```

3. **Format code:**
   ```bash
   docker-compose -f docker-compose.dev.yml exec web black .
   ```

4. **Lint code:**
   ```bash
   docker-compose -f docker-compose.dev.yml exec web flake8
   ```

5. **Stop the development environment:**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

### Development Tools Included

- **pytest**: Testing framework
- **pytest-cov**: Test coverage reporting
- **black**: Code formatter
- **flake8**: Code linter
- **flask-debugtoolbar**: Debug toolbar for Flask applications

### Development Environment Structure

```
invoice-gen/
├── docker-compose.dev.yml    # Development Docker Compose configuration
├── Dockerfile.dev           # Development Dockerfile
├── entrypoint.dev.sh        # Development container entrypoint script
└── ...                      # Other project files
```

The development environment mounts your local code directory into the container, allowing for immediate code changes without rebuilding. The database and migrations are stored in Docker volumes to persist data between container restarts.

## Running with Docker

This application can be built and run using Docker and Docker Compose, simplifying deployment and ensuring consistency across environments.

**Prerequisites:**
*   [Docker](https://docs.docker.com/get-docker/) installed on your system.
*   [Docker Compose](https://docs.docker.com/compose/install/) installed on your system.

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/151henry151/invoice-gen.git
    cd invoice-gen
    ```
    Note: The `user_logos` directory is included in the repository and will be automatically created when you clone it. This directory is used to store uploaded company logos.

2.  **Build and run the application using Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image (the first time it's run, or if the Dockerfile/code changes) and then start the application container. The `--build` flag ensures the image is rebuilt if necessary.

4.  **Access the application:**
    Once the container is running, the application will be accessible at [http://localhost:8080/](http://localhost:8080/).

5.  **To stop the application:**
    Press `Ctrl+C` in the terminal where `docker-compose up` is running. To remove the containers, you can run:
    ```bash
    docker-compose down
    ```

**Alternative: Building and Running with Docker (without Docker Compose)**

If you prefer to use Docker directly without Docker Compose:

1.  **Build the Docker image:**
    ```bash
    docker build -t invoice-gen-app .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 8080:8080 -v "$(pwd)/user_logos:/app/static/logos" --name invoice-gen-container invoice-gen-app
    ```
    This command runs the container, maps port 8080, mounts the `user_logos` directory, and names the container `invoice-gen-container`.

3.  **Access the application:**
    [http://localhost:8080/](http://localhost:8080/)

4.  **To stop and remove the container:**
    ```bash
    docker stop invoice-gen-container
    docker rm invoice-gen-container
    ```

## Deployment

### Production Deployment with Docker and Nginx

This application is designed to be deployed behind a reverse proxy (like Nginx) and can be run using Docker Compose. Here's a complete guide for production deployment:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/151henry151/invoice-gen.git
   cd invoice-gen
   ```
   Note: The `user_logos` directory is included in the repository and will be automatically created when you clone it. This directory is used to store uploaded company logos.

2. **Configure environment variables:**
   Create a `.env` file in the project root with the following variables:
   ```
   FLASK_APP=wsgi.py
   FLASK_ENV=production
   SECRET_KEY=your-secure-secret-key-here
   DATABASE_URL=sqlite:///invoice_gen.db
   ```

3. **Build and start the Docker container:**
   ```bash
   docker-compose up -d --build
   ```

4. **Configure Nginx:**
   - Copy the example configuration:
     ```bash
     cp nginx.conf.example /etc/nginx/sites-available/invoice-gen
     ```
   - Edit the configuration:
     - Replace `your-domain.com` with your actual domain
     - Update SSL certificate paths
     - Adjust the static files path to match your deployment
   - Enable the site:
     ```bash
     ln -s /etc/nginx/sites-available/invoice-gen /etc/nginx/sites-enabled/
     ```
   - Test and reload Nginx:
     ```bash
     nginx -t
     systemctl reload nginx
     ```

5. **Set up SSL certificates:**
   ```bash
   certbot --nginx -d your-domain.com
   ```

6. **Verify the deployment:**
   - Check container health:
     ```bash
     docker ps
     docker logs invoice-gen-web-1
     ```
   - Test the application:
     - Visit `https://your-domain.com/invoice/`
     - Verify SSL certificate
     - Check static file serving
     - Test PDF generation

### Important Production Considerations

1. **Database Persistence:**
   - The SQLite database is mounted as a volume in `docker-compose.yml`
   - Regular backups are recommended

2. **Static Files:**
   - Company logos are stored in the `user_logos` directory
   - Static files are served directly by Nginx for better performance

3. **Security:**
   - SSL/TLS is required for production
   - Security headers are configured in Nginx
   - Use strong secret keys in production

4. **Monitoring:**
   - The container includes a healthcheck
   - Monitor logs for errors:
     ```bash
     docker logs -f invoice-gen-web-1
     ```

5. **Updates:**
   - Pull latest changes:
     ```bash
     git pull
     docker-compose up -d --build
     ```
   - Database migrations may be required for schema updates

### Troubleshooting

1. **502 Bad Gateway:**
   - Check if the Docker container is running
   - Verify Nginx proxy configuration
   - Check container logs for errors

2. **Static Files Not Loading:**
   - Verify Nginx static file configuration
   - Check file permissions
   - Ensure correct paths in configuration

3. **Database Issues:**
   - Check database file permissions
   - Verify volume mounting
   - Check application logs for SQL errors

## Features

- Company and client management
- Add labor and itemized costs
- Live calculation of total costs
- Professional invoice generation
- Responsive, user-friendly UI

## Notes
- All configuration is handled in `app.py` and `templates/index.html`.
- Static assets (CSS, JS, images) are in the `static/` directory.
- For PDF export, ensure WeasyPrint is installed and configured if used.

## Database Migrations

This project uses Flask-Migrate (Alembic) to manage database migrations. This allows you to evolve your database schema over time without losing data.

### Initial Setup

If you need to reset the migration environment (e.g., during development or if the migration state is corrupted), follow these steps:

1. **Backup and Reset Migrations:**
   - Inside the Docker container, run:
     ```sh
     mv /app/migrations /app/migrations_backup_$(date +%Y%m%d_%H%M%S)
     flask db init
     ```
   - This creates a fresh `migrations/` directory with a new `alembic.ini`.

2. **Configure the Database URL:**
   - Ensure that the `sqlalchemy.url` in `/app/migrations/alembic.ini` points to your database. For example:
     ```ini
     [alembic]
     sqlalchemy.url = sqlite:////app/db/invoice_gen.db
     ```

3. **Generate and Apply the Initial Migration:**
   - Run:
     ```sh
     flask db migrate -m "Initial migration"
     flask db upgrade
     ```

### Making Schema Changes

When you need to update your database schema (e.g., adding a new table or column):

1. **Update your SQLAlchemy models** in `models.py`.
2. **Generate a new migration:**
   ```sh
   flask db migrate -m "Describe your change"
   ```
3. **Apply the migration:**
   ```sh
   flask db upgrade
   ```

This workflow ensures that your database schema evolves safely in production without data loss.

## URL Prefix Configuration

This application is configured to run under the `/invoice` URL prefix (e.g., `https://example.com/invoice/`). This configuration is handled through the WSGI server (Gunicorn) using the `SCRIPT_NAME` environment variable, which is the recommended way to handle URL prefixes in Flask applications.

### How it works

1. The `SCRIPT_NAME` environment variable is set in `docker-compose.yml`:
   ```yaml
   environment:
     - SCRIPT_NAME=/invoice
   ```

2. Nginx is configured to pass this prefix to Gunicorn in `nginx/conf.d/hromp.com.conf`:
   ```nginx
   location /invoice/ {
       proxy_pass http://172.20.0.2:8080;  # No trailing slash to preserve prefix
       proxy_set_header SCRIPT_NAME /invoice;
       # ... other proxy settings ...
   }
   ```

### Changing the URL Prefix

To serve the application under a different URL prefix or without a prefix:

1. Update the `SCRIPT_NAME` environment variable in `docker-compose.yml`:
   - For a different prefix (e.g., `/billing`): `SCRIPT_NAME=/billing`
   - For no prefix: Remove the `SCRIPT_NAME` line entirely

2. Update the Nginx configuration in `nginx/conf.d/hromp.com.conf`:
   - For a different prefix:
     ```nginx
     location /billing/ {
         proxy_pass http://172.20.0.2:8080;
         proxy_set_header SCRIPT_NAME /billing;
         # ... other proxy settings ...
     }
     ```
   - For no prefix:
     ```nginx
     location / {
         proxy_pass http://172.20.0.2:8080;
         # Remove the SCRIPT_NAME header
         # ... other proxy settings ...
     }
     ```

3. Restart both services:
   ```bash
   systemctl restart nginx
   docker-compose down && docker-compose up -d
   ```

### Important Notes

- The Flask application itself doesn't need to know about the URL prefix - it's handled entirely by the WSGI server and reverse proxy
- All URLs in templates should use `url_for()` to generate links, which will automatically include the correct prefix
- Static files are automatically handled through the `SCRIPT_NAME` configuration
- The application will work correctly whether served from the root path or any prefix

---

For questions or contributions, please open an issue or pull request on [GitHub](https://github.com/151henry151/invoice-gen). 