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

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

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

2.  **Create a directory for logo uploads (if it doesn't exist):**
    The `docker-compose.yml` file is configured to mount a local directory named `user_logos` into the container for persisting uploaded company logos. Create this directory in the root of the project:
    ```bash
    mkdir user_logos
    ```

3.  **Build and run the application using Docker Compose:**
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

1. **Set environment variables:**
   - `FLASK_APP=app.py`
   - `FLASK_ENV=production` (for production)

2. **Use a production WSGI server:**
   - Example: [gunicorn](https://gunicorn.org/)
   - Example command:
     ```bash
     gunicorn app:app
     ```

3. **Configure a reverse proxy (optional):**
   - Use Nginx or Apache to serve static files and proxy requests to Gunicorn.

4. **(Optional) Set up HTTPS:**
   - Use Let's Encrypt or another certificate provider.

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

---

For questions or contributions, please open an issue or pull request on [GitHub](https://github.com/151henry151/invoice-gen). 