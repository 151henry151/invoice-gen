from flask import Flask, render_template, request, redirect, url_for, flash, send_file, render_template_string, session, g, current_app, jsonify
from datetime import datetime, timedelta
import sqlite3
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import pandas as pd
from weasyprint import HTML, CSS
import re
from openpyxl import load_workbook, Workbook
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
from PIL import Image
import subprocess
import json
from models import db, Company, Client, Item, LaborType, Invoice, LineItem, User

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a secure secret key

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///invoice_gen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Configure upload settings
UPLOAD_FOLDER = 'static/logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_LOGO_SIZE = (200, 200)  # Maximum dimensions for logo
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_setting(key, default=None):
    """Get a setting value from the database or return the default value."""
    try:
        # For now, we'll use session to store settings
        return session.get(key, default)
    except Exception as e:
        print(f"Error getting setting {key}: {str(e)}")
        return default

def set_setting(key, value):
    """Set a setting value in the database."""
    try:
        session[key] = value
        return True
    except Exception as e:
        print(f"Error setting {key}: {str(e)}")
        return False

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
        user_id = session.get('user_id')
        if not user_id or not User.query.get(user_id):
            session.clear()  # Clear session if user is invalid
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    with app.app_context():
        db.create_all()

def init_app(app):
    with app.app_context():
        init_db()

@app.context_processor
def utility_processor():
    def float_hours_to_hr_min(qty):
        hours = int(qty)
        minutes = int(round((qty - hours) * 60))
        return f"{hours}hr {minutes}m" if hours or minutes else "0hr 0m"
    return dict(get_setting=get_setting, float_hours_to_hr_min=float_hours_to_hr_min)

@app.route('/')
def index():
    # Get all companies and clients
    companies = Company.query.filter_by(user_id=session['user_id']).all() if 'user_id' in session else []
    clients = Client.query.filter_by(user_id=session['user_id']).all() if 'user_id' in session else []
    items = Item.query.filter_by(user_id=session['user_id']).all() if 'user_id' in session else []
    labor_types = LaborType.query.filter_by(user_id=session['user_id']).all() if 'user_id' in session else []
    selected_company = None
    selected_client = None
    if 'selected_company_id' in session:
        selected_company = Company.query.filter_by(id=session['selected_company_id'], user_id=session['user_id']).first()
    if 'selected_client_id' in session:
        selected_client = Client.query.filter_by(id=session['selected_client_id'], user_id=session['user_id']).first()
    
    # Get all items and labor types
    items = Item.query.all()
    labor_types = LaborType.query.all()
    
    # Generate invoice number
    invoice_number = generate_invoice_number()
    
    # Get current date and due date (30 days from now)
    current_date = datetime.now().strftime('%Y-%m-%d')
    due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Get selected tax rate from session or default to 0
    selected_tax_rate = session.get('selected_tax_rate', '0')
    
    # Check if the request is from a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
    
    # Define tax rates
    tax_rates = ['0', '5', '8', '10', '13', '15', '20']
    
    # Use mobile template for mobile devices
    template = 'mobile_index.html' if is_mobile else 'index.html'
    
    return render_template(template,
                         companies=companies,
                         clients=clients,
                         selected_company=selected_company,
                         selected_client=selected_client,
                         items=items,
                         labor_types=labor_types,
                         invoice_number=invoice_number,
                         date=current_date,
                         due_date=due_date,
                         selected_tax_rate=selected_tax_rate,
                         tax_rates=tax_rates)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print('REGISTER FORM DATA:', request.form)  # Debug print
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))
        # Create new user
        user = User(
            username=username,
            password=generate_password_hash(password),
            email=email
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
    template = 'mobile_register.html' if is_mobile else 'register.html'
    return render_template(template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
        return redirect(url_for('login'))
    
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone', 'ipad'])
    template = 'mobile_login.html' if is_mobile else 'login.html'
    return render_template(template)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password:
            flash('Current password and new password are required')
            return redirect(url_for('profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match')
            return redirect(url_for('profile'))
        
        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect')
            return redirect(url_for('profile'))
        
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password updated successfully')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = User.query.get(session['user_id'])
    
    # Delete all user's data
    Company.query.filter_by(user_id=user.id).delete()
    Client.query.filter_by(user_id=user.id).delete()
    Item.query.filter_by(user_id=user.id).delete()
    LaborType.query.filter_by(user_id=user.id).delete()
    
    # Delete user's invoices and line items
    invoices = Invoice.query.join(Client).filter(Client.user_id == user.id).all()
    for invoice in invoices:
        LineItem.query.filter_by(invoice_id=invoice.id).delete()
    Invoice.query.join(Client).filter(Client.user_id == user.id).delete()
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    session.clear()
    flash('Account deleted successfully')
    return redirect(url_for('login'))

@app.route('/new_client', methods=['POST'])
@login_required
def new_client():
    name = request.form.get('name')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')
    if not name:
        if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
            return jsonify({'error': 'Client name is required'}), 400
        flash('Client name is required')
        return redirect(url_for('index'))
    client = Client(
        user_id=session['user_id'],
        name=name,
        address=address,
        email=email,
        phone=phone
    )
    db.session.add(client)
    db.session.commit()
    if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
        return jsonify({'id': client.id, 'name': client.name}), 201
    flash('Client added successfully')
    return redirect(url_for('index'))

@app.route('/new_company', methods=['POST'])
@login_required
def new_company():
    name = request.form.get('name')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')
    if not name:
        if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
            return jsonify({'error': 'Name is required'}), 400
        flash('Name is required')
        return redirect(url_for('index'))
    company = Company(user_id=session['user_id'], name=name, address=address, email=email, phone=phone)
    db.session.add(company)
    db.session.commit()
    if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
        return jsonify({'id': company.id, 'name': company.name}), 201
    flash('Business added successfully')
    return redirect(url_for('index'))

@app.route('/edit_client/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.address = request.form.get('address')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        
        if not client.name:
            flash('Client name is required')
            return redirect(url_for('edit_client', client_id=client_id))
        
        db.session.commit()
        flash('Client updated successfully')
        return redirect(url_for('index'))
    
    return render_template('edit_client.html', client=client)

@app.route('/edit_company/<int:company_id>', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    
    if request.method == 'POST':
        company.name = request.form.get('name')
        company.address = request.form.get('address')
        company.email = request.form.get('email')
        company.phone = request.form.get('phone')
        
        if not company.name:
            flash('Company name is required')
            return redirect(url_for('edit_company', company_id=company_id))
        
        # Handle logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Resize logo if needed
                if resize_logo(filepath):
                    company.logo_path = filename
                else:
                    flash('Error processing logo image')
                    return redirect(url_for('edit_company', company_id=company_id))
        
        db.session.commit()
        flash('Company updated successfully')
        return redirect(url_for('index'))
    
    return render_template('edit_company.html', company=company)

@app.route('/delete_client/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully')
    return redirect(url_for('index'))

@app.route('/delete_company/<int:company_id>', methods=['POST'])
@login_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted successfully')
    return redirect(url_for('index'))

@app.route('/select_client/<int:client_id>')
@login_required
def select_client(client_id):
    session['selected_client_id'] = client_id
    return redirect(url_for('index'))

@app.route('/select_company/<int:company_id>')
@login_required
def select_company(company_id):
    session['selected_company_id'] = company_id
    return redirect(url_for('index'))

@app.route('/select_tax_rate/<rate>')
@login_required
def select_tax_rate(rate):
    session['selected_tax_rate'] = rate
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
    """Convert Excel file to PDF using LibreOffice"""
    try:
        # Convert Excel to PDF using LibreOffice
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', os.path.dirname(pdf_path),
            excel_path
        ]
        
        # Run the conversion command
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            raise Exception(f'LibreOffice conversion failed: {process.stderr}')
        
        # Get the generated PDF path (LibreOffice adds .pdf extension)
        generated_pdf = os.path.splitext(excel_path)[0] + '.pdf'
        
        # Move the generated PDF to the desired location
        if os.path.exists(generated_pdf):
            shutil.move(generated_pdf, pdf_path)
        else:
            raise Exception('PDF file was not generated')
            
    except Exception as e:
        raise Exception(f'Error converting to PDF: {str(e)}')

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
        date_str = request.form['date']
        due_date_str = request.form.get('due_date')
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else (date + timedelta(days=30) if date else None)
        invoice_number = request.form['invoice_number']
        output_format = 'pdf'  # Always use PDF now
        notes = request.form.get('notes', '')
        sales_tax_id = request.form.get('sales_tax_id')
        tax_applies_to = request.form.get('tax_applies_to')

        # Parse line items from JSON
        line_items_json = request.form.get('line_items_json', '[]')
        line_items_data = json.loads(line_items_json)

        # Get client information from database
        client = Client.query.filter_by(id=client_id, user_id=session['user_id']).first()
        if not client:
            flash('Client not found', 'danger')
            return redirect(url_for('index'))

        # Get business info from selected company
        company_id = session.get('selected_company_id')
        if company_id:
            company = Company.query.filter_by(id=company_id, user_id=session['user_id']).first()
            if company:
                business_name = company.name
                business_address = company.address
                business_phone = company.phone
                business_email = company.email
                logo_path = company.logo_path
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
                quantity = float(item.get('quantity', 1))
                price = float(item.get('price', 0))
                total = price * quantity
                subtotal += total
                date_value = item.get('date', date_str)
                date_obj = datetime.strptime(date_value, '%Y-%m-%d').date() if date_value else None
                line_items.append({
                    'date': date_obj,
                    'description': item.get('description', ''),
                    'quantity': quantity,
                    'unit_price': price,
                    'total': total,
                    'is_labor': False
                })
            elif item.get('type') == 'labor':
                hours_val = float(item.get('hours', 0))
                minutes_val = float(item.get('minutes', 0))
                hours_float = hours_val + (minutes_val / 60)
                rate = float(item.get('rate', get_setting('hourly_rate', '40.00')))
                total = hours_float * rate
                subtotal += total
                date_value = item.get('date', date_str)
                date_obj = datetime.strptime(date_value, '%Y-%m-%d').date() if date_value else None
                description = (
                    f"{item.get('description', '')} @ ${rate:.2f}/hr" if rate % 1 else f"{item.get('description', '')} @ ${int(rate)}/hr"
                )
                line_items.append({
                    'date': date_obj,
                    'description': description,
                    'quantity': hours_float,
                    'unit_price': rate,
                    'total': total,
                    'is_labor': True
                })
            elif item.get('type') == 'note':
                notes_text = item.get('description', notes_text)

        # Calculate sales tax if applicable
        sales_tax = 0
        if sales_tax_id and tax_applies_to:
            sales_tax_obj = None
            try:
                sales_tax_obj = db.session.query(db.Model.metadata.tables['sales_tax']).filter_by(id=sales_tax_id).first()
            except Exception:
                pass
            if sales_tax_obj:
                tax_rate = sales_tax_obj.rate
                taxable_amount = 0
                for item in line_items:
                    if (tax_applies_to == 'items' and 'h' not in str(item['quantity'])) or \
                       (tax_applies_to == 'labor' and 'h' in str(item['quantity'])) or \
                       tax_applies_to == 'both':
                        taxable_amount += item['total']
                sales_tax = taxable_amount * (tax_rate / 100)

        grand_total = subtotal + sales_tax

        # Create invoice record
        invoice = Invoice(
            invoice_number=invoice_number,
            client_id=client_id,
            date=date,
            due_date=due_date,
            notes=notes_text,
            total=grand_total,
            sales_tax_id=sales_tax_id,
            tax_applies_to=tax_applies_to
        )
        db.session.add(invoice)
        db.session.commit()
        invoice_id = invoice.id

        # Insert line items
        for item in line_items:
            line_item = LineItem(
                invoice_id=invoice_id,
                description=item['description'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total=item['total'],
                date=item['date']
            )
            db.session.add(line_item)
        db.session.commit()

        # Prepare data for template
        invoice_data = {
            'logo_url': logo_url,
            'business_name': business_name,
            'business_address': business_address,
            'business_phone': business_phone,
            'business_email': business_email,
            'client_name': client.name,
            'client_address': client.address,
            'client_phone': client.phone,
            'client_email': client.email,
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
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            logo.save(filepath)
            if not resize_logo(filepath):
                if os.path.exists(filepath):
                    os.remove(filepath)
                flash('Error processing logo. Please try again.', 'danger')
                return redirect(url_for('settings'))

        if company_id:
            # Update existing company
            company = Company.query.filter_by(id=company_id, user_id=session['user_id']).first()
            if company:
                if logo_path:
                    # Delete old logo if it exists
                    if company.logo_path:
                        old_logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path)
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)
                    company.logo_path = logo_path
                company.name = name
                company.address = address
                company.email = email
                company.phone = phone
                db.session.commit()
                flash('Company details updated successfully!', 'success')
                return redirect(url_for('index', selected_company=company_id))
        else:
            # Create new company
            company = Company(
                user_id=session['user_id'],
                name=name,
                address=address,
                email=email,
                phone=phone,
                logo_path=logo_path
            )
            db.session.add(company)
            db.session.commit()
            new_company_id = company.id
            flash('New company created successfully!', 'success')
            return redirect(url_for('index', selected_company=new_company_id))

    # For GET requests, get the company_id from URL parameters
    company_id = request.args.get('company_id')
    selected_company = None
    if company_id:
        selected_company = Company.query.filter_by(id=company_id, user_id=session['user_id']).first()
        if not selected_company:
            flash('Company not found', 'danger')
            return redirect(url_for('index'))

    return render_template('settings.html', selected_company=selected_company)

@app.route('/client_details')
@login_required
def client_details():
    client_id = request.args.get('client_id')
    is_new = request.args.get('new') == 'true'

    clients = Client.query.filter_by(user_id=session['user_id']).all()
    selected_client = None
    if client_id and not is_new:
        selected_client = Client.query.filter_by(id=client_id, user_id=session['user_id']).first()

    return render_template('client_details.html', clients=clients, selected_client=selected_client, is_new=is_new)

@app.route('/update_client', methods=['POST'])
@login_required
def update_client():
    client_id = request.form.get('client_id')
    name = request.form.get('name')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')

    if client_id:
        # Update existing client
        client = Client.query.filter_by(id=client_id, user_id=session['user_id']).first()
        if client:
            client.name = name
            client.address = address
            client.email = email
            client.phone = phone
            db.session.commit()
            selected_client_id = client.id
        else:
            flash('Client not found', 'danger')
            return redirect(url_for('index'))
    else:
        # Create new client
        client = Client(
            user_id=session['user_id'],
            name=name,
            address=address,
            email=email,
            phone=phone
        )
        db.session.add(client)
        db.session.commit()
        selected_client_id = client.id

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

    labor_items = LaborType.query.filter_by(user_id=session['user_id']).all()
    selected_item = None
    if item_id and not is_new:
        selected_item = LaborType.query.filter_by(id=item_id, user_id=session['user_id']).first()

    return render_template('labor_details.html', labor_items=labor_items, selected_item=selected_item, is_new=is_new)

@app.route('/update_labor', methods=['POST'])
@login_required
def update_labor():
    item_id = request.form.get('item_id')
    description = request.form.get('description')
    rate = request.form.get('rate')

    if item_id:
        # Update existing labor item
        labor_item = LaborType.query.filter_by(id=item_id, user_id=session['user_id']).first()
        if labor_item:
            labor_item.description = description
            labor_item.rate = rate
            db.session.commit()
            new_id = labor_item.id
        else:
            flash('Labor item not found', 'danger')
            return redirect(url_for('index'))
    else:
        # Create new labor item
        labor_item = LaborType(
            user_id=session['user_id'],
            description=description,
            rate=rate
        )
        db.session.add(labor_item)
        db.session.commit()
        new_id = labor_item.id

    flash('Labor item saved successfully!')
    return redirect(url_for('index', open_dialog='add_labor', new_labor_id=new_id))

@app.route('/remove_labor_item', methods=['POST'])
@login_required
def remove_labor_item():
    data = request.get_json()
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'success': False, 'error': 'No item ID provided'})

    labor_item = LaborType.query.filter_by(id=item_id, user_id=session['user_id']).first()
    if not labor_item:
        return jsonify({'success': False, 'error': 'Labor item not found'})
    try:
        db.session.delete(labor_item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/item_details')
@login_required
def item_details():
    item_id = request.args.get('item_id')
    is_new = request.args.get('new') == 'true'

    items = Item.query.filter_by(user_id=session['user_id']).all()
    selected_item = None
    if item_id and not is_new:
        selected_item = Item.query.filter_by(id=item_id, user_id=session['user_id']).first()

    return render_template('item_details.html', items=items, selected_item=selected_item, is_new=is_new)

@app.route('/update_item', methods=['POST'])
@login_required
def update_item():
    item_id = request.form.get('item_id')
    description = request.form.get('description')
    price = request.form.get('price')

    if item_id:
        # Update existing item
        item = Item.query.filter_by(id=item_id, user_id=session['user_id']).first()
        if item:
            item.description = description
            item.price = price
            db.session.commit()
            new_id = item.id
        else:
            flash('Item not found', 'danger')
            return redirect(url_for('index'))
    else:
        # Create new item
        item = Item(
            user_id=session['user_id'],
            description=description,
            price=price
        )
        db.session.add(item)
        db.session.commit()
        new_id = item.id

    flash('Item saved successfully!')
    return redirect(url_for('index', open_dialog='add_item', new_item_id=new_id))

@app.route('/remove_item', methods=['POST'])
@login_required
def remove_item():
    data = request.get_json()
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({'success': False, 'error': 'No item ID provided'})

    item = Item.query.filter_by(id=item_id, user_id=session['user_id']).first()
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'})
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_company/<int:company_id>')
@login_required
def get_company(company_id):
    company = Company.query.filter_by(id=company_id, user_id=session['user_id']).first()
    if company:
        return jsonify({
            'name': company.name,
            'address': company.address,
            'email': company.email,
            'phone': company.phone,
            'logo_path': company.logo_path
        })
    return jsonify({'error': 'Company not found'}), 404

@app.route('/get_client/<int:client_id>')
@login_required
def get_client(client_id):
    client = Client.query.filter_by(id=client_id, user_id=session['user_id']).first()
    if client:
        return jsonify({
            'name': client.name,
            'address': client.address,
            'email': client.email,
            'phone': client.phone
        })
    return jsonify({'error': 'Client not found'}), 404

@app.route('/check_invoice_number/<invoice_number>')
@login_required
def check_invoice_number(invoice_number):
    invoice = Invoice.query.join(Client).filter(
        Invoice.invoice_number == invoice_number,
        Client.user_id == session['user_id']
    ).first()
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
    # Assuming you have a SalesTax model
    sales_tax_table = db.Model.metadata.tables['sales_tax']
    rates = db.session.query(sales_tax_table).order_by(sales_tax_table.c.description).all()
    return jsonify([{
        'id': rate.id,
        'rate': rate.rate,
        'description': rate.description
    } for rate in rates])

@app.route('/api/sales-tax', methods=['DELETE'])
@login_required
def delete_all_sales_tax_rates():
    sales_tax_table = db.Model.metadata.tables['sales_tax']
    try:
        db.session.execute(sales_tax_table.delete())
        db.session.commit()
        return jsonify({'message': 'All tax rates have been cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500

@app.route('/api/sales-tax', methods=['POST'])
@login_required
def create_sales_tax_rate():
    data = request.get_json()
    if not data or 'rate' not in data or 'description' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        rate = float(data['rate'])
        if rate < 0:
            return jsonify({'error': 'Rate must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid rate value'}), 400
    sales_tax_table = db.Model.metadata.tables['sales_tax']
    # Check for duplicate description
    existing = db.session.query(sales_tax_table).filter_by(description=data['description']).first()
    if existing:
        return jsonify({'error': 'A tax rate with this description already exists'}), 400
    # Insert new tax rate
    insert_stmt = sales_tax_table.insert().values(rate=rate, description=data['description'])
    result = db.session.execute(insert_stmt)
    db.session.commit()
    new_id = result.inserted_primary_key[0]
    new_rate = db.session.query(sales_tax_table).filter_by(id=new_id).first()
    return jsonify({
        'id': new_rate.id,
        'rate': new_rate.rate,
        'description': new_rate.description
    }), 201

@app.route('/api/invoice/<int:invoice_id>/sales-tax', methods=['PUT'])
@login_required
def update_invoice_sales_tax(invoice_id):
    data = request.get_json()
    if not data or 'sales_tax_id' not in data or 'tax_applies_to' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    if data['tax_applies_to'] not in ['items', 'labor', 'both']:
        return jsonify({'error': 'Invalid tax_applies_to value'}), 400
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=session['user_id']).first()
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    sales_tax_table = db.Model.metadata.tables['sales_tax']
    tax_rate = db.session.query(sales_tax_table).filter_by(id=data['sales_tax_id']).first()
    if not tax_rate:
        return jsonify({'error': 'Sales tax rate not found'}), 404
    invoice.sales_tax_id = data['sales_tax_id']
    invoice.tax_applies_to = data['tax_applies_to']
    db.session.commit()
    return jsonify({
        'id': invoice.id,
        'sales_tax_id': invoice.sales_tax_id,
        'tax_applies_to': invoice.tax_applies_to,
        'tax_rate': tax_rate.rate,
        'tax_description': tax_rate.description
    })

@app.route('/generate_invoice', methods=['POST'])
@login_required
def generate_invoice():
    # Get form data
    invoice_number = request.form.get('invoice_number')
    client_id = request.form.get('client_id')
    date_str = request.form['date']
    due_date_str = request.form.get('due_date')
    tax_rate = request.form.get('tax_rate')
    notes = request.form.get('notes')
    
    # Get items and labor data
    items = []
    labor = []
    
    # Process items
    item_descriptions = request.form.getlist('item_description[]')
    item_quantities = request.form.getlist('item_quantity[]')
    item_prices = request.form.getlist('item_price[]')
    
    for i in range(len(item_descriptions)):
        if item_descriptions[i] and item_quantities[i] and item_prices[i]:
            items.append({
                'description': item_descriptions[i],
                'quantity': float(item_quantities[i]),
                'price': float(item_prices[i])
            })
    
    # Process labor
    labor_descriptions = request.form.getlist('labor_description[]')
    labor_hours = request.form.getlist('labor_hours[]')
    labor_rates = request.form.getlist('labor_rate[]')
    
    for i in range(len(labor_descriptions)):
        if labor_descriptions[i] and labor_hours[i] and labor_rates[i]:
            labor.append({
                'description': labor_descriptions[i],
                'hours': float(labor_hours[i]),
                'rate': float(labor_rates[i])
            })
    
    # Calculate totals
    subtotal = sum(item['quantity'] * item['price'] for item in items) + \
               sum(lab['hours'] * lab['rate'] for lab in labor)
    tax_amount = subtotal * (float(tax_rate) / 100)
    total = subtotal + tax_amount
    
    # Create invoice
    date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else (date + timedelta(days=30) if date else None)
    invoice = Invoice(
        invoice_number=invoice_number,
        client_id=client_id,
        date=date,
        due_date=due_date,
        notes=notes,
        total=total
    )
    
    db.session.add(invoice)
    db.session.flush()  # Get invoice ID
    
    # Add line items
    for item in items:
        line_item = LineItem(
            invoice_id=invoice.id,
            description=item['description'],
            quantity=item['quantity'],
            unit_price=item['price'],
            total=item['quantity'] * item['price']
        )
        db.session.add(line_item)
    
    for lab in labor:
        line_item = LineItem(
            invoice_id=invoice.id,
            description=lab['description'],
            quantity=lab['hours'],
            unit_price=lab['rate'],
            total=lab['hours'] * lab['rate']
        )
        db.session.add(line_item)
    
    db.session.commit()
    
    # Generate PDF
    pdf_path = generate_invoice_pdf(invoice.id)
    
    return send_file(pdf_path, as_attachment=True, download_name=f'invoice_{invoice_number}.pdf')

def generate_invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    client = Client.query.get(invoice.client_id)
    company = Company.query.get(session.get('selected_company_id'))
    
    # Create PDF
    pdf_path = os.path.join('static', 'invoices', f'invoice_{invoice.invoice_number}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Add company logo if exists
    if company and company.logo_path:
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path)
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 50, 700, width=100, height=100)
    
    # Add company details
    if company:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 650, company.name)
        c.setFont("Helvetica", 10)
        c.drawString(50, 635, company.address)
        c.drawString(50, 620, f"Email: {company.email}")
        c.drawString(50, 605, f"Phone: {company.phone}")
    
    # Add client details
    if client:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, 650, "Bill To:")
        c.setFont("Helvetica", 10)
        c.drawString(350, 635, client.name)
        c.drawString(350, 620, client.address)
        c.drawString(350, 605, f"Email: {client.email}")
        c.drawString(350, 590, f"Phone: {client.phone}")
    
    # Add invoice details
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 550, f"Invoice #{invoice.invoice_number}")
    c.setFont("Helvetica", 10)
    c.drawString(50, 535, f"Date: {invoice.date.strftime('%Y-%m-%d')}")
    c.drawString(50, 520, f"Due Date: {invoice.due_date.strftime('%Y-%m-%d')}")
    
    # Add line items
    y = 450
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Description")
    c.drawString(300, y, "Quantity")
    c.drawString(400, y, "Price")
    c.drawString(500, y, "Total")
    
    y -= 20
    c.setFont("Helvetica", 10)
    
    # Get line items
    line_items = LineItem.query.filter_by(invoice_id=invoice.id).all()
    
    for item in line_items:
        c.drawString(50, y, item.description)
        c.drawString(300, y, str(item.quantity))
        c.drawString(400, y, f"${item.unit_price:.2f}")
        c.drawString(500, y, f"${item.total:.2f}")
        y -= 20
    
    # Add totals
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(400, y, "Subtotal:")
    c.drawString(500, y, f"${invoice.total:.2f}")
    
    # Add notes if any
    if invoice.notes:
        y -= 40
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Notes:")
        c.setFont("Helvetica", 10)
        c.drawString(50, y - 15, invoice.notes)
    
    c.save()
    return pdf_path

@app.route('/invoices')
@login_required
def list_invoices():
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('view_invoice.html', invoice=invoice)

@app.route('/delete_invoice/<int:invoice_id>', methods=['POST'])
@login_required
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Delete associated line items
    LineItem.query.filter_by(invoice_id=invoice_id).delete()
    
    # Delete invoice
    db.session.delete(invoice)
    db.session.commit()
    
    flash('Invoice deleted successfully')
    return redirect(url_for('list_invoices'))

@app.route('/new_item', methods=['POST'])
@login_required
def new_item():
    description = request.form.get('description')
    price = request.form.get('price')
    if not description or not price:
        if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
            return jsonify({'error': 'Item description and price are required'}), 400
        flash('Item description and price are required')
        return redirect(url_for('index'))
    try:
        price = float(price)
    except ValueError:
        if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
            return jsonify({'error': 'Invalid price format'}), 400
        flash('Invalid price format')
        return redirect(url_for('index'))
    item = Item(
        user_id=session['user_id'],
        description=description,
        price=price
    )
    db.session.add(item)
    db.session.commit()
    if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
        return jsonify({'id': item.id, 'description': item.description, 'price': item.price}), 201
    flash('Item added successfully')
    return redirect(url_for('index'))

@app.route('/new_labor_type', methods=['POST'])
@login_required
def new_labor_type():
    description = request.form.get('description')
    rate = request.form.get('rate')
    
    if not description or not rate:
        flash('Labor type description and rate are required')
        return redirect(url_for('index'))
    
    try:
        rate = float(rate)
    except ValueError:
        flash('Invalid rate format')
        return redirect(url_for('index'))
    
    labor_type = LaborType(
        user_id=session['user_id'],
        description=description,
        rate=rate
    )
    try:
        db.session.add(labor_type)
        db.session.commit()
        flash('Labor type added successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding labor type: {e}', 'danger')
    return redirect(url_for('index'))

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    if request.method == 'POST':
        description = request.form.get('description')
        price = request.form.get('price')
        
        if not description or not price:
            flash('Item description and price are required')
            return redirect(url_for('edit_item', item_id=item_id))
        
        try:
            price = float(price)
        except ValueError:
            flash('Invalid price format')
            return redirect(url_for('edit_item', item_id=item_id))
        
        item.description = description
        item.price = price
        
        db.session.commit()
        flash('Item updated successfully')
        return redirect(url_for('index'))
    
    return render_template('edit_item.html', item=item)

@app.route('/edit_labor_type/<int:labor_type_id>', methods=['GET', 'POST'])
@login_required
def edit_labor_type(labor_type_id):
    labor_type = LaborType.query.get_or_404(labor_type_id)
    
    if request.method == 'POST':
        description = request.form.get('description')
        rate = request.form.get('rate')
        
        if not description or not rate:
            flash('Labor type description and rate are required')
            return redirect(url_for('edit_labor_type', labor_type_id=labor_type_id))
        
        try:
            rate = float(rate)
        except ValueError:
            flash('Invalid rate format')
            return redirect(url_for('edit_labor_type', labor_type_id=labor_type_id))
        
        labor_type.description = description
        labor_type.rate = rate
        
        db.session.commit()
        flash('Labor type updated successfully')
        return redirect(url_for('index'))
    
    return render_template('edit_labor_type.html', labor_type=labor_type)

@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully')
    return redirect(url_for('index'))

@app.route('/delete_labor_type/<int:labor_type_id>', methods=['POST'])
@login_required
def delete_labor_type(labor_type_id):
    labor_type = LaborType.query.get_or_404(labor_type_id)
    db.session.delete(labor_type)
    db.session.commit()
    flash('Labor type deleted successfully')
    return redirect(url_for('index'))

def generate_invoice_number():
    # Get the latest invoice number
    latest_invoice = Invoice.query.order_by(Invoice.invoice_number.desc()).first()
    
    if latest_invoice:
        # Extract the number part and increment
        try:
            number = int(latest_invoice.invoice_number.split('-')[1]) + 1
        except (IndexError, ValueError):
            number = 1
    else:
        number = 1
    
    # Format as INV-XXXX
    return f"INV-{number:04d}"

@app.route('/api/labor_types', methods=['POST'])
@login_required
def create_labor_type():
    data = request.get_json() if request.is_json else request.form
    description = data.get('description')
    rate = data.get('rate')
    if not description or not rate:
        if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
            return jsonify({'error': 'Missing required fields'}), 400
        flash('Labor description and rate are required')
        return redirect(url_for('index'))
    try:
        rate = float(rate)
    except ValueError:
        if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
            return jsonify({'error': 'Invalid rate value'}), 400
        flash('Invalid rate value')
        return redirect(url_for('index'))
    labor = LaborType(user_id=session['user_id'], description=description, rate=rate)
    db.session.add(labor)
    db.session.commit()
    if request.is_json or request.accept_mimetypes['application/json'] > request.accept_mimetypes['text/html']:
        return jsonify({'id': labor.id, 'description': labor.description, 'rate': labor.rate}), 201
    flash('Labor type added successfully')
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create the database tables
    with app.app_context():
        init_db()
        # migrate_settings_to_companies()  # Disabled to avoid NameError
    # Start the application
    app.run(debug=True, port=8080) 