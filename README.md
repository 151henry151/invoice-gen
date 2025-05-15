# Invoice Generator

A web-based invoice generator for small businesses and freelancers. This app allows you to manage company and client details, add labor and itemized costs, and generate professional invoices.

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