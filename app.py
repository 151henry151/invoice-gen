from flask import Flask, render_template, request, redirect, url_for, flash, send_file, render_template_string, session, g, current_app, jsonify
from datetime import datetime, timedelta
import sqlite3
import os
# Removed reportlab imports
# Removed pandas import
from weasyprint import HTML, CSS
import re
from openpyxl import load_workbook, Workbook
import openpyxl
import shutil
from openpyxl.styles import PatternFill, Border, Side
# Removed pdfkit import
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import time
from flask_login import current_user
from PIL import Image
import subprocess
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a secure secret key

# Configure upload settings
UPLOAD_FOLDER = 'static/logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_LOGO_SIZE = (200, 200)  # Maximum dimensions for logo
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_logo(image_path):
    """Resize the logo while maintaining aspect ratio"""
    try:
        from PIL import Image
        img = Image.open(image_path)
        # Calculate new dimensions while maintaining aspect ratio
        width, height = img.size
        max_size = 200  # Maximum dimension
        
        if width > height:
            new_width = min(width, max_size)
            new_height = int(height * (new_width / width))
        else:
            new_height = min(height, max_size)
            new_width = int(width * (new_height / height))
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img.save(image_path)
        return True
    except Exception as e:
        print(f"Error resizing logo: {str(e)}")
        return False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database setup
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('invoice_gen.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect('invoice_gen.db')
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db.commit()
    db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

def get_setting(key, default=None):
    db = get_db()
    user_id = session.get('user_id')
    if not user_id:
        return default
    setting = db.execute(
        'SELECT value FROM settings WHERE user_id = ? AND key = ?',
        (user_id, key)
    ).fetchone()
    return setting['value'] if setting else default

def update_setting(key, value):
    if 'user_id' not in session:
        return
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)',
                (session['user_id'], key, value))
    conn.commit()
    conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Password validation
        errors = []
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long.")
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()-_=+\[\]{};:'\",.<>/?]", password):
            errors.append("Password must contain at least one special character.")
        
        if errors:
            for error in errors:
                flash(error, 'danger') # Use 'danger' category for error messages
            return render_template('register.html') # Stay on register page

        # If validation passes, proceed to create user
        conn = None # Initialize conn to None
        try:
            conn = get_db() # Assign conn here
            # Create user
            hashed_password = generate_password_hash(password) # Hash after validation
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                        (username, hashed_password, email))
            user_id = cursor.lastrowid
            
            # Set default settings for new user
            default_settings = [
                (user_id, 'company_name', 'Your Company Name'),
                (user_id, 'company_address', 'Your Company Address'),
                (user_id, 'company_email', 'your.company@example.com'),
                (user_id, 'hourly_rate', '40.00'),
                (user_id, 'next_invoice_number', '1001'),
                (user_id, 'logo_path', '')
            ]
            cursor.executemany('INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?)',
                           default_settings)
            
            conn.commit()
            flash('Registration successful! Please log in.', 'success') # Use 'success' category
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
        finally:
            if conn: # Ensure conn is defined before trying to close
                conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        
        flash('Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = get_db()
    clients = conn.execute('SELECT * FROM clients WHERE user_id = ?', 
                         (session['user_id'],)).fetchall()
    labor_items = conn.execute('SELECT * FROM labor_items WHERE user_id = ?',
                             (session['user_id'],)).fetchall()
    items = conn.execute('SELECT * FROM items WHERE user_id = ?',
                        (session['user_id'],)).fetchall()
    companies = conn.execute('SELECT * FROM companies WHERE user_id = ? AND name != ?',
                           (session['user_id'], 'Your Company Name')).fetchall()
    
    # Get selected company from query parameter or session
    selected_company_id = request.args.get('selected_company') or session.get('selected_company_id')
    selected_company = None
    if selected_company_id:
        selected_company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?',
                                      (selected_company_id, session['user_id'])).fetchone()
        if selected_company:
            session['selected_company_id'] = selected_company_id
    
    # Get selected client from query parameter or session
    selected_client_id = request.args.get('selected_client') or session.get('selected_client_id')
    selected_client = None
    if selected_client_id:
        selected_client = conn.execute('SELECT * FROM clients WHERE id = ? AND user_id = ?',
                                     (selected_client_id, session['user_id'])).fetchone()
        if selected_client:
            session['selected_client_id'] = selected_client_id
    
    return render_template('index.html', 
                         clients=clients, 
                         labor_items=labor_items,
                         items=items,
                         companies=companies,
                         selected_company=selected_company,
                         selected_client=selected_client,
                         get_setting=get_setting)

@app.route('/new_client', methods=['POST'])
@login_required
def new_client():
    name = request.form['name']
    address = request.form['address']
    email = request.form['email']
    phone = request.form['phone']
    
    conn = get_db()
    conn.execute('INSERT INTO clients (user_id, name, address, email, phone) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], name, address, email, phone))
    conn.commit()
    flash('New client created successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/create_invoice', methods=['POST'])
@login_required
def create_invoice():
    try:
        # Get form data
        client_id = request.form['client']
        date = request.form['date']
        invoice_number = request.form['invoice_number']
        output_format = 'pdf'  # Always use PDF now
        notes = request.form.get('notes', '')
        sales_tax_id = request.form.get('sales_tax_id')
        tax_applies_to = request.form.get('tax_applies_to')

        # Parse line items from JSON
        line_items_json = request.form.get('line_items_json', '[]')
        line_items_data = json.loads(line_items_json)

        # Get client information from database
        conn = get_db()
        client = conn.execute('SELECT * FROM clients WHERE id = ? AND user_id = ?',
                            (client_id, session['user_id'])).fetchone()
        if not client:
            flash('Client not found', 'danger')
            return redirect(url_for('index'))

        # Get business info from selected company
        company_id = session.get('selected_company_id')
        if company_id:
            company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?', (company_id, session['user_id'])).fetchone()
            if company:
                business_name = company['name']
                business_address = company['address']
                business_phone = company['phone']
                business_email = company['email']
                logo_path = company['logo_path']
                if logo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], logo_path)):
                    logo_url = url_for('static', filename=f'logos/{logo_path}')
                else:
                    logo_url = url_for('static', filename='default_logo.png')
        else:
            business_name = get_setting('business_name', 'Business Name')
            business_address = get_setting('business_address', 'Business Address')
            business_phone = get_setting('business_phone', 'Business Phone')
            business_email = get_setting('business_email', 'Business Email')
            logo_path = get_setting('logo_path')
            if logo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], logo_path)):
                logo_url = url_for('static', filename=f'logos/{logo_path}')
            else:
                logo_url = url_for('static', filename='default_logo.png')

        # Calculate totals
        subtotal = 0
        line_items = []
        notes_text = notes
        for item in line_items_data:
            if item.get('type') == 'item':
                quantity = int(item.get('quantity', 1))
                price = float(item.get('price', 0))
                total = price * quantity
                subtotal += total
                line_items.append({
                    'date': item.get('date', date),
                    'description': item.get('description', ''),
                    'quantity': quantity,
                    'unit_price': price,
                    'total': total
                })
            elif item.get('type') == 'labor':
                hours_val = float(item.get('hours', 0))
                minutes_val = float(item.get('minutes', 0))
                hours_float = hours_val + (minutes_val / 60)
                rate = float(item.get('rate', get_setting('hourly_rate', '40.00')))
                total = hours_float * rate
                subtotal += total
                line_items.append({
                    'date': item.get('date', date),
                    'description': item.get('description', f"Labor - {int(hours_val)}h {int(minutes_val)}m"),
                    'quantity': f"{int(hours_val)}h {int(minutes_val)}m",
                    'unit_price': rate,
                    'total': total
                })
            elif item.get('type') == 'note':
                notes_text = item.get('description', notes_text)

        # Calculate sales tax if applicable
        sales_tax = 0
        if sales_tax_id and tax_applies_to:
            tax_rate = conn.execute('SELECT rate FROM sales_tax WHERE id = ?', (sales_tax_id,)).fetchone()
            if tax_rate:
                taxable_amount = 0
                for item in line_items:
                    if (tax_applies_to == 'items' and 'h' not in str(item['quantity'])) or \
                       (tax_applies_to == 'labor' and 'h' in str(item['quantity'])) or \
                       tax_applies_to == 'both':
                        taxable_amount += item['total']
                sales_tax = taxable_amount * (tax_rate['rate'] / 100)

        grand_total = subtotal + sales_tax

        # Create invoice record
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (
                user_id, invoice_number, client_id, date, notes, total,
                sales_tax_id, tax_applies_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            invoice_number,
            client_id,
            date,
            notes_text,
            grand_total,
            sales_tax_id,
            tax_applies_to
        ))
        invoice_id = cursor.lastrowid

        # Insert line items
        for item in line_items:
            cursor.execute('''
                INSERT INTO line_items (
                    invoice_id, description, quantity, unit_price,
                    total, date
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                invoice_id,
                item['description'],
                item['quantity'],
                item['unit_price'],
                item['total'],
                item['date']
            ))

        conn.commit()

        # Prepare data for template
        invoice_data = {
            'logo_url': logo_url,
            'business_name': business_name,
            'business_address': business_address,
            'business_phone': business_phone,
            'business_email': business_email,
            'client_name': client['name'],
            'client_address': client['address'],
            'client_phone': client['phone'],
            'client_email': client['email'],
            'invoice_date': date,
            'invoice_number': invoice_number,
            'line_items': line_items,
            'subtotal': subtotal,
            'sales_tax': sales_tax,
            'grand_total': grand_total,
            'notes': notes_text
        }

        print("INVOICE DATA FOR PDF:", invoice_data)

        if output_format == 'pdf':
            try:
                # Render HTML
                html_content = render_template('invoice_pretty.html', **invoice_data)

                # Debug: Print module paths
                import weasyprint
                from weasyprint import HTML
                print("WeasyPrint module path:", weasyprint.__file__)
                print("HTML class path:", HTML.__module__)

                # Generate PDF
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                    pdf_path = temp_pdf.name
                    try:
                        # Create HTML object with the rendered content
                        html = HTML(string=html_content, base_url=request.host_url)
                        # Write PDF
                        html.write_pdf(pdf_path)
                        return send_file(
                            pdf_path,
                            as_attachment=True,
                            download_name=f'invoice_{invoice_number}.pdf',
                            mimetype='application/pdf'
                        )
                    except Exception as e:
                        print(f"Error during PDF generation: {str(e)}")
                        print(f"Error type: {type(e)}")
                        print(f"HTML content type: {type(html_content)}")
                        print(f"HTML content length: {len(str(html_content))}")
                        print(f"HTML content preview: {str(html_content)[:200]}")  # Print first 200 chars
                        raise
            except Exception as e:
                print(f"Error in PDF generation block: {str(e)}")
                print(f"Error type: {type(e)}")
                raise

    except Exception as e:
        flash('An error occurred while generating the invoice: {}'.format(str(e)), 'danger')
        return redirect(url_for('index'))

@app.route('/preview/<invoice_number>')
def preview_invoice(invoice_number):
    conn = get_db()
    invoice = conn.execute('''
        SELECT i.*, c.name as client_name, c.address as client_address, c.email as client_email
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        WHERE i.invoice_number = ?
    ''', (invoice_number,)).fetchone()
    
    line_items = conn.execute('''
        SELECT * FROM line_items WHERE invoice_id = ?
    ''', (invoice['id'],)).fetchall()
    
    return f'''
        <html>
            <body>
                <h1>Invoice Preview</h1>
                <p>Invoice #{invoice_number} has been created.</p>
                <p><a href="/download/{invoice_number}">Download Excel Invoice</a></p>
            </body>
        </html>
    '''

@app.route('/download/<invoice_number>')
def download_invoice(invoice_number):
    conn = get_db()
    invoice = conn.execute('''
        SELECT i.*, c.name as client_name
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        WHERE i.invoice_number = ?
    ''', (invoice_number,)).fetchone()
    filename = f"static/{invoice['client_name'].lower().replace(' ', '_')}_invoice_{invoice_number}.xlsx"
    return send_file(filename, as_attachment=True)

def migrate_settings_to_companies():
    conn = get_db()
    users = conn.execute('SELECT id FROM users').fetchall()
    for user in users:
        user_id = user['id']
        name = conn.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', (user_id, 'company_name')).fetchone()
        address = conn.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', (user_id, 'company_address')).fetchone()
        email = conn.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', (user_id, 'company_email')).fetchone()
        phone = conn.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', (user_id, 'company_phone')).fetchone()
        logo = conn.execute('SELECT value FROM settings WHERE user_id = ? AND key = ?', (user_id, 'logo_path')).fetchone()
        # Only migrate if company_name exists and not already in companies
        if name and not conn.execute('SELECT 1 FROM companies WHERE user_id = ? AND name = ?', (user_id, name['value'])).fetchone():
            conn.execute(
                'INSERT INTO companies (user_id, name, address, email, phone, logo_path) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, name['value'], address['value'] if address else '', email['value'] if email else '', phone['value'] if phone else '', logo['value'] if logo else '')
            )
    conn.commit()
    conn.close()

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db()
    if request.method == 'POST':
        company_id = request.form.get('company_id')
        name = request.form.get('name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        logo = request.files.get('logo')
        logo_path = None

        if logo and logo.filename:
            filename = secure_filename(logo.filename)
            logo_path = f"{session['user_id']}_{int(time.time())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], logo_path)
            
            # Create upload folder if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save the file
            logo.save(filepath)
            
            # Resize the logo
            if not resize_logo(filepath):
                # If resize fails, delete the uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash('Error processing logo. Please try again.', 'danger')
                return redirect(url_for('settings'))

        if company_id:
            # Update existing company
            company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?', (company_id, session['user_id'])).fetchone()
            if company:
                if logo_path:
                    # Delete old logo if it exists
                    if company['logo_path']:
                        old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company['logo_path'])
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)
                    conn.execute('UPDATE companies SET name=?, address=?, email=?, phone=?, logo_path=? WHERE id=? AND user_id=?',
                        (name, address, email, phone, logo_path, company_id, session['user_id']))
                else:
                    conn.execute('UPDATE companies SET name=?, address=?, email=?, phone=? WHERE id=? AND user_id=?',
                        (name, address, email, phone, company_id, session['user_id']))
                conn.commit()
                flash('Company details updated successfully!', 'success')
                return redirect(url_for('index', selected_company=company_id))
        else:
            # Create new company
            cursor = conn.execute('INSERT INTO companies (user_id, name, address, email, phone, logo_path) VALUES (?, ?, ?, ?, ?, ?)',
                (session['user_id'], name, address, email, phone, logo_path))
            conn.commit()
            new_company_id = cursor.lastrowid
            flash('New company created successfully!', 'success')
            return redirect(url_for('index', selected_company=new_company_id))

    # For GET requests, get the company_id from URL parameters
    company_id = request.args.get('company_id')
    selected_company = None
    if company_id:
        selected_company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?', (company_id, session['user_id'])).fetchone()
        if not selected_company:
            flash('Company not found', 'danger')
            return redirect(url_for('index'))

    return render_template('settings.html', selected_company=selected_company)

@app.route('/client_details')
@login_required
def client_details():
    client_id = request.args.get('client_id')
    is_new = request.args.get('new') == 'true'
    
    conn = get_db()
    clients = conn.execute('SELECT * FROM clients WHERE user_id = ?', 
                         (session['user_id'],)).fetchall()
    
    selected_client = None
    if client_id and not is_new:
        selected_client = conn.execute('SELECT * FROM clients WHERE id = ? AND user_id = ?',
                                    (client_id, session['user_id'])).fetchone()
    
    return render_template('client_details.html', clients=clients, selected_client=selected_client, is_new=is_new)

@app.route('/update_client', methods=['POST'])
@login_required
def update_client():
    client_id = request.form.get('client_id')
    name = request.form.get('name')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    conn = get_db()
    if client_id:
        # Update existing client
        conn.execute('''UPDATE clients 
                       SET name = ?, address = ?, email = ?, phone = ?
                       WHERE id = ? AND user_id = ?''',
                    (name, address, email, phone, client_id, session['user_id']))
        selected_client_id = client_id
    else:
        # Create new client
        cursor = conn.execute('''INSERT INTO clients (user_id, name, address, email, phone)
                       VALUES (?, ?, ?, ?, ?)''',
                    (session['user_id'], name, address, email, phone))
        selected_client_id = cursor.lastrowid
    
    conn.commit()
    flash('Client details saved successfully!', 'success')
    return redirect(url_for('index', selected_client=selected_client_id))

@app.route('/update_company', methods=['POST'])
@login_required
def update_company():
    company_name = request.form.get('company_name')
    company_address = request.form.get('company_address')
    company_email = request.form.get('company_email')
    hourly_rate = request.form.get('hourly_rate')
    
    # Update company settings
    update_setting('company_name', company_name)
    update_setting('company_address', company_address)
    update_setting('company_email', company_email)
    update_setting('hourly_rate', hourly_rate)
    
    # Handle logo upload
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename and allowed_file(file.filename):
            # Create logos directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            filename = secure_filename(f"{session['user_id']}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            update_setting('logo_path', filename)
    
    flash('Company details saved successfully!')
    return redirect(url_for('index'))

@app.route('/labor_details')
@login_required
def labor_details():
    item_id = request.args.get('item_id')
    is_new = request.args.get('new') == 'true'
    
    conn = get_db()
    labor_items = conn.execute('SELECT * FROM labor_items WHERE user_id = ?', 
                         (session['user_id'],)).fetchall()
    
    selected_item = None
    if item_id and not is_new:
        selected_item = conn.execute('SELECT * FROM labor_items WHERE id = ? AND user_id = ?',
                                    (item_id, session['user_id'])).fetchone()
    
    return render_template('labor_details.html', labor_items=labor_items, selected_item=selected_item, is_new=is_new)

@app.route('/update_labor', methods=['POST'])
@login_required
def update_labor():
    item_id = request.form.get('item_id')
    description = request.form.get('description')
    rate = request.form.get('rate')
    
    conn = get_db()
    if item_id:
        # Update existing labor item
        conn.execute('''UPDATE labor_items 
                       SET description = ?, rate = ?
                       WHERE id = ? AND user_id = ?''',
                    (description, rate, item_id, session['user_id']))
        new_id = item_id
    else:
        # Create new labor item
        cursor = conn.execute('''INSERT INTO labor_items (user_id, description, rate)
                       VALUES (?, ?, ?)''',
                    (session['user_id'], description, rate))
        new_id = cursor.lastrowid
    
    conn.commit()
    flash('Labor item saved successfully!')
    return redirect(url_for('index', open_dialog='add_labor', new_labor_id=new_id))

@app.route('/remove_labor_item', methods=['POST'])
@login_required
def remove_labor_item():
    data = request.get_json()
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({'success': False, 'error': 'No item ID provided'})
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM labor_items WHERE id = ? AND user_id = ?',
                    (item_id, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/item_details')
@login_required
def item_details():
    item_id = request.args.get('item_id')
    is_new = request.args.get('new') == 'true'
    
    conn = get_db()
    items = conn.execute('SELECT * FROM items WHERE user_id = ?', 
                        (session['user_id'],)).fetchall()
    
    selected_item = None
    if item_id and not is_new:
        selected_item = conn.execute('SELECT * FROM items WHERE id = ? AND user_id = ?',
                                   (item_id, session['user_id'])).fetchone()
    
    return render_template('item_details.html', items=items, selected_item=selected_item, is_new=is_new)

@app.route('/update_item', methods=['POST'])
@login_required
def update_item():
    item_id = request.form.get('item_id')
    description = request.form.get('description')
    price = request.form.get('price')
    
    conn = get_db()
    if item_id:
        # Update existing item
        conn.execute('''UPDATE items 
                       SET description = ?, price = ?
                       WHERE id = ? AND user_id = ?''',
                    (description, price, item_id, session['user_id']))
        new_id = item_id
    else:
        # Create new item
        cursor = conn.execute('''INSERT INTO items (user_id, description, price)
                       VALUES (?, ?, ?)''',
                    (session['user_id'], description, price))
        new_id = cursor.lastrowid
    
    conn.commit()
    flash('Item saved successfully!')
    return redirect(url_for('index', open_dialog='add_item', new_item_id=new_id))

@app.route('/remove_item', methods=['POST'])
@login_required
def remove_item():
    data = request.get_json()
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({'success': False, 'error': 'No item ID provided'})
    
    conn = get_db()
    try:
        conn.execute('DELETE FROM items WHERE id = ? AND user_id = ?',
                    (item_id, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_company/<int:company_id>')
@login_required
def get_company(company_id):
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?',
                         (company_id, session['user_id'])).fetchone()
    if company:
        return jsonify({
            'name': company['name'],
            'address': company['address'],
            'email': company['email'],
            'phone': company['phone'],
            'logo_path': company['logo_path']
        })
    return jsonify({'error': 'Company not found'}), 404

@app.route('/get_client/<int:client_id>')
@login_required
def get_client(client_id):
    conn = get_db()
    client = conn.execute('SELECT * FROM clients WHERE id = ? AND user_id = ?',
                         (client_id, session['user_id'])).fetchone()
    if client:
        return jsonify({
            'name': client['name'],
            'address': client['address'],
            'email': client['email'],
            'phone': client['phone']
        })
    return jsonify({'error': 'Client not found'}), 404

@app.route('/check_invoice_number/<invoice_number>')
@login_required
def check_invoice_number(invoice_number):
    conn = get_db()
    # Check if the invoice number exists in the database
    invoice = conn.execute('SELECT id FROM invoices WHERE invoice_number = ? AND user_id = ?',
                         (invoice_number, session['user_id'])).fetchone()
    return jsonify({'exists': invoice is not None})

@app.route('/save_selections', methods=['POST'])
@login_required
def save_selections():
    data = request.get_json()
    if data:
        if 'businessId' in data:
            session['selected_company_id'] = data['businessId']
        if 'clientId' in data:
            session['selected_client_id'] = data['clientId']
    return jsonify({'success': True})

@app.route('/api/sales-tax', methods=['GET'])
@login_required
def get_sales_tax_rates():
    conn = get_db()
    rates = conn.execute('SELECT * FROM sales_tax ORDER BY description').fetchall()
    return jsonify([{
        'id': rate['id'],
        'rate': rate['rate'],
        'description': rate['description']
    } for rate in rates])

@app.route('/api/sales-tax', methods=['DELETE'])
@login_required
def delete_all_sales_tax_rates():
    conn = get_db()
    try:
        # Delete all tax rates
        conn.execute('DELETE FROM sales_tax')
        conn.commit()
        return jsonify({'message': 'All tax rates have been cleared'}), 200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': 'Database error occurred'}), 500

@app.route('/api/sales-tax', methods=['POST'])
@login_required
def create_sales_tax_rate():
    data = request.get_json()
    print("Received data:", data)  # Debug log
    
    if not data or 'rate' not in data or 'description' not in data:
        print("Missing required fields. Data:", data)  # Debug log
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        rate = float(data['rate'])
        if rate < 0:
            print("Invalid rate value (negative):", rate)  # Debug log
            return jsonify({'error': 'Rate must be positive'}), 400
    except ValueError as e:
        print("Invalid rate value:", data['rate'], "Error:", str(e))  # Debug log
        return jsonify({'error': 'Invalid rate value'}), 400
    
    conn = get_db()
    try:
        # Check for duplicate description
        existing = conn.execute('SELECT id FROM sales_tax WHERE description = ?', 
                              (data['description'],)).fetchone()
        if existing:
            print("Duplicate description found:", data['description'])  # Debug log
            return jsonify({'error': 'A tax rate with this description already exists'}), 400
        
        # Insert new tax rate
        cursor = conn.execute('INSERT INTO sales_tax (rate, description) VALUES (?, ?)',
                            (rate, data['description']))
        conn.commit()
        
        # Get the newly created tax rate
        new_rate = conn.execute('SELECT * FROM sales_tax WHERE id = ?', 
                              (cursor.lastrowid,)).fetchone()
        
        print("Successfully created tax rate:", new_rate)  # Debug log
        return jsonify({
            'id': new_rate['id'],
            'rate': new_rate['rate'],
            'description': new_rate['description']
        }), 201
        
    except sqlite3.Error as e:
        print("Database error:", str(e))  # Debug log
        conn.rollback()
        return jsonify({'error': 'Database error occurred'}), 500

@app.route('/api/invoice/<int:invoice_id>/sales-tax', methods=['PUT'])
@login_required
def update_invoice_sales_tax(invoice_id):
    data = request.get_json()
    
    if not data or 'sales_tax_id' not in data or 'tax_applies_to' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['tax_applies_to'] not in ['items', 'labor', 'both']:
        return jsonify({'error': 'Invalid tax_applies_to value'}), 400
    
    conn = get_db()
    try:
        # Check if invoice exists and belongs to user
        invoice = conn.execute('SELECT id FROM invoices WHERE id = ? AND user_id = ?',
                             (invoice_id, session['user_id'])).fetchone()
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        # Check if sales tax rate exists
        tax_rate = conn.execute('SELECT id FROM sales_tax WHERE id = ?',
                              (data['sales_tax_id'],)).fetchone()
        if not tax_rate:
            return jsonify({'error': 'Sales tax rate not found'}), 404
        
        # Update invoice with sales tax information
        conn.execute('''
            UPDATE invoices 
            SET sales_tax_id = ?, tax_applies_to = ?
            WHERE id = ? AND user_id = ?
        ''', (data['sales_tax_id'], data['tax_applies_to'], invoice_id, session['user_id']))
        
        conn.commit()
        
        # Get updated invoice data
        updated_invoice = conn.execute('''
            SELECT i.*, st.rate as tax_rate, st.description as tax_description
            FROM invoices i
            LEFT JOIN sales_tax st ON i.sales_tax_id = st.id
            WHERE i.id = ? AND i.user_id = ?
        ''', (invoice_id, session['user_id'])).fetchone()
        
        return jsonify({
            'id': updated_invoice['id'],
            'sales_tax_id': updated_invoice['sales_tax_id'],
            'tax_applies_to': updated_invoice['tax_applies_to'],
            'tax_rate': updated_invoice['tax_rate'],
            'tax_description': updated_invoice['tax_description']
        })
        
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': 'Database error occurred'}), 500

if __name__ == '__main__':
    # Create the database tables
    with app.app_context():
        init_db()
        # Run the migration
        migrate_settings_to_companies()
    # Start the application
    app.run(debug=True, port=8080) 