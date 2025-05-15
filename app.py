from flask import Flask, render_template, request, redirect, url_for, flash, send_file, render_template_string, session, g, current_app, jsonify
from datetime import datetime
import sqlite3
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import pandas as pd
from weasyprint import HTML, CSS
import re
from openpyxl import load_workbook
import openpyxl
import shutil
from openpyxl.styles import PatternFill, Border, Side
import pdfkit
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import time
from flask_login import current_user

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a secure secret key

# Configure upload settings
UPLOAD_FOLDER = 'static/logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        conn = get_db()
        try:
            # Create user
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                        (username, generate_password_hash(password), email))
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
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.')
        finally:
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
    companies = conn.execute('SELECT * FROM companies WHERE user_id = ? AND name != ?',
                           (session['user_id'], 'Your Company Name')).fetchall()
    
    # Get selected company from query parameter
    selected_company_id = request.args.get('selected_company')
    selected_company = None
    if selected_company_id:
        selected_company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?',
                                      (selected_company_id, session['user_id'])).fetchone()
    
    # Get selected client from query parameter
    selected_client_id = request.args.get('selected_client')
    selected_client = None
    if selected_client_id:
        selected_client = conn.execute('SELECT * FROM clients WHERE id = ? AND user_id = ?',
                                     (selected_client_id, session['user_id'])).fetchone()
    
    return render_template('index.html', 
                         clients=clients, 
                         labor_items=labor_items, 
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

def edit_excel_invoice(template_path, output_path, invoice_data):
    """Edit the Excel invoice template with new data"""
    # Copy the template to the output path
    shutil.copy2(template_path, output_path)
    
    # Load the workbook
    wb = load_workbook(output_path)
    ws = wb.active
    
    # Unmerge all cells first
    merged_cells = list(ws.merged_cells.ranges)
    for merged_range in merged_cells:
        ws.unmerge_cells(str(merged_range))
    
    # Add logo if provided
    if invoice_data.get('logo_path'):
        try:
            img = openpyxl.drawing.image.Image(invoice_data['logo_path'])
            # Adjust logo size and position
            img.width = 100  # Adjust width as needed
            img.height = 100  # Adjust height as needed
            ws.add_image(img, 'B2')  # Position the logo in cell B2
        except Exception as e:
            print(f"Error adding logo: {str(e)}")
    
    # Add spaces to company information in column C
    for row in range(3, 7):  # Rows 3-6
        cell = ws[f'C{row}']
        if cell.value:
            cell.value = '      ' + str(cell.value)
    
    # Get the background color from a surrounding cell (e.g., G6)
    surrounding_cell = ws['G6']
    fill_color = surrounding_cell.fill.start_color.index
    
    # Apply the same background color to G4 and G5
    ws['G4'].fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    ws['G5'].fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
    
    # Format the date as M/D/YYYY
    date_obj = datetime.strptime(invoice_data['date'], '%Y-%m-%d')
    formatted_date = date_obj.strftime('%-m/%-d/%Y')
    
    # Update invoice number and date
    ws['G8'] = f"Invoice  # {invoice_data['invoice_number']}"
    ws['G6'] = f"Date: {formatted_date}"
    
    # Get the formatting from template cells
    template_rate_cell = ws['F26']
    rate_number_format = template_rate_cell.number_format
    
    template_total_cell = ws['G26']
    total_number_format = template_total_cell.number_format
    
    # Get the formatting from the template's client cells
    template_client_name_cell = ws['B14']
    client_name_format = template_client_name_cell.number_format
    
    template_client_address_cell = ws['B15']
    client_address_format = template_client_address_cell.number_format
    
    # Update client information with correct formatting
    client_name_cell = ws['B14']
    client_name_cell.value = invoice_data['client_name']
    client_name_cell.number_format = client_name_format
    
    client_address_cell = ws['B15']
    client_address_cell.value = invoice_data['client_address']
    client_address_cell.number_format = client_address_format
    
    # Clear existing line items (rows 22-32) while preserving formatting
    for row in range(22, 33):
        for col in ['B', 'C', 'D', 'E', 'F', 'G']:
            cell = ws[f'{col}{row}']
            # Store original number format
            original_number_format = cell.number_format
            
            # Clear value
            cell.value = None
            
            # Set alternating background colors
            if (row - 22) % 2 == 0:  # Even rows (22, 24, 26, etc.)
                cell.fill = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type="solid")
            else:  # Odd rows (23, 25, 27, etc.)
                cell.fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type="solid")
            
            # Restore number format
            cell.number_format = original_number_format
    
    # Set border styles for columns F and G
    for row in range(22, 33):
        # Column F
        cell = ws[f'F{row}']
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin') if row == 22 else Side(style='none'),
            bottom=Side(style='thin') if row == 32 else Side(style='none')
        )
        
        # Column G
        cell = ws[f'G{row}']
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin') if row == 22 else Side(style='none'),
            bottom=Side(style='thin') if row == 32 else Side(style='none')
        )
    
    # Update line items
    row = 22  # Starting row for line items
    for item in invoice_data['line_items']:
        # Format the line item date as M/D/YYYY
        item_date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
        formatted_item_date = item_date_obj.strftime('%-m/%-d/%Y')
        
        # Set date with correct formatting
        date_cell = ws[f'B{row}']
        date_cell.value = formatted_item_date
        
        ws[f'C{row}'] = item['description']   # Description
        ws[f'E{row}'] = item['quantity']      # Quantity
        
        # Set rate with correct formatting
        rate_cell = ws[f'F{row}']
        rate_cell.value = item['unit_price']
        rate_cell.number_format = rate_number_format
        
        # Set total with correct formatting
        total_cell = ws[f'G{row}']
        total_cell.value = item['total']
        total_cell.number_format = total_number_format
        
        row += 1
    
    # Update final total with correct formatting
    total_cell = ws['G39']
    total_cell.value = f"$ {invoice_data['total']:.2f}"
    total_cell.number_format = total_number_format
    
    # Update notes if any
    if invoice_data.get('notes'):
        ws['C34'] = invoice_data['notes']
    
    # Save the workbook
    wb.save(output_path)

def convert_to_pdf(excel_path, pdf_path):
    """Convert Excel file to PDF using wkhtmltopdf"""
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
        html_path = temp_html.name
    
    # Convert Excel to HTML (you might need to adjust this based on your needs)
    os.system(f'libreoffice --headless --convert-to html --outdir {os.path.dirname(html_path)} {excel_path}')
    
    # Convert HTML to PDF
    pdfkit.from_file(html_path, pdf_path, configuration=config)
    
    # Clean up temporary files
    os.unlink(html_path)
    os.unlink(excel_path)

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['logo']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('Logo uploaded successfully')
        return redirect(url_for('index'))
    
    flash('Invalid file type')
    return redirect(url_for('index'))

@app.route('/create_invoice', methods=['POST'])
@login_required
def create_invoice():
    try:
        # Get form data
        client_id = request.form['client']
        date = request.form['date']
        invoice_number = request.form['invoice_number']
        items = request.form.getlist('item[]')
        item_dates = request.form.getlist('item_date[]')
        hours = request.form.getlist('hours[]')
        minutes = request.form.getlist('minutes[]')
        notes = request.form.get('notes', '')
        
        # Get client information from database
        conn = get_db()
        client = conn.execute('SELECT * FROM clients WHERE id = ? AND user_id = ?',
                            (client_id, session['user_id'])).fetchone()
        
        if not client:
            flash('Client not found')
            return redirect(url_for('index'))
        
        # Get settings
        hourly_rate = float(get_setting('hourly_rate', '40.00'))
        
        # Get logo path if it exists
        logo_path = get_setting('logo_path')
        if logo_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], logo_path)):
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_path)
        else:
            logo_path = None
        
        # Calculate total
        total = 0
        line_items = []
        for i in range(len(items)):
            if items[i].strip():  # Only process non-empty items
                hours_float = float(hours[i]) + (float(minutes[i]) / 60)
                item_total = hours_float * hourly_rate
                total += item_total
                
                line_items.append({
                    'date': item_dates[i],
                    'description': items[i],
                    'quantity': f"{hours[i]}h {minutes[i]}m",
                    'unit_price': hourly_rate,
                    'total': item_total
                })
        
        # Create invoice data
        invoice_data = {
            'invoice_number': invoice_number,
            'date': date,
            'client_name': client['name'],
            'client_address': client['address'],
            'line_items': line_items,
            'total': total,
            'notes': notes,
            'logo_path': logo_path
        }
        
        # Store invoice in database
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO invoices (user_id, client_id, invoice_number, date, total, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], client_id, invoice_number, date, total, notes))
        invoice_id = cursor.lastrowid
        
        # Store line items in database
        for item in line_items:
            cursor.execute('''
                INSERT INTO line_items (invoice_id, date, description, quantity, unit_price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (invoice_id, item['date'], item['description'], item['quantity'],
                 item['unit_price'], item['total']))
        
        conn.commit()
        
        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_excel:
            excel_path = temp_excel.name
        
        # Generate Excel file
        edit_excel_invoice('static/Invoice.xlsx', excel_path, invoice_data)
        
        # Increment invoice number for next time
        next_number = str(int(invoice_number) + 1)
        update_setting('next_invoice_number', next_number)
        
        # Send the Excel file
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=f'invoice_{invoice_data["invoice_number"]}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'An error occurred while generating the invoice: {str(e)}')
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
            logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_path))

        if company_id:
            # Update existing company
            company = conn.execute('SELECT * FROM companies WHERE id = ? AND user_id = ?', (company_id, session['user_id'])).fetchone()
            if company:
                if logo_path:
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
            flash('Company not found', 'error')
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
    else:
        # Create new labor item
        conn.execute('''INSERT INTO labor_items (user_id, description, rate)
                       VALUES (?, ?, ?)''',
                    (session['user_id'], description, rate))
    
    conn.commit()
    flash('Labor item saved successfully!')
    return redirect(url_for('index'))

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

if __name__ == '__main__':
    # Create the database tables
    with app.app_context():
        init_db()
        # Run the migration
        migrate_settings_to_companies()
    # Start the application
    app.run(debug=True, port=8080) 