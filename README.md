# Invoice Generator

> **Pre-Release Notice**: This project is currently under development and not yet fully functional. This is a pre-release version with ongoing development and improvements.

A professional invoice generator for small businesses and freelancers, built with Flask and modern web technologies. This app allows you to manage company and client details, add labor and itemized costs, and generate professional invoices.

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

---

For questions or contributions, please open an issue or pull request on [GitHub](https://github.com/151henry151/invoice-gen). 