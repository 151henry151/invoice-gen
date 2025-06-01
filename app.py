from flask import Flask, render_template, request, redirect, url_for, flash, send_file, render_template_string, session, g, current_app, jsonify, make_response, send_from_directory
from datetime import datetime, timedelta
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
from werkzeug.middleware.proxy_fix import ProxyFix
import glob
import io
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Business, Setting, Client, Invoice, SalesTax, Item, LaborItem, InvoiceItem, InvoiceLabor

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_port=1, x_prefix=1)
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Use environment variable for secret key

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db/invoice_gen.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Configure static file serving
app.static_folder = 'static'
app.static_url_path = '/invoice/static'  # Update static URL path to include /invoice prefix

# Configure upload settings
UPLOAD_FOLDER = 'uploads'  # Changed from static/uploads to uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_LOGO_SIZE = (200, 200)  # Maximum dimensions for logo
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Custom URL generator to ensure /invoice prefix
def url_for_with_prefix(*args, **kwargs):
    kwargs['_external'] = True
    kwargs['_scheme'] = request.environ.get('HTTP_X_FORWARDED_PROTO', 'https')
    return url_for(*args, **kwargs)

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
            return redirect(url_for_with_prefix('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database setup
def get_db():
    return db.session

def close_db(e=None):
    pass  # SQLAlchemy handles connection cleanup

def get_setting(key, default=None):
    user_id = session.get('user_id')
    if not user_id:
        return default
    setting = db.session.query(Setting).filter_by(user_id=user_id, key=key).first()
    return setting.value if setting else default

def update_setting(key, value):
    if 'user_id' not in session:
        return
    setting = db.session.query(Setting).filter_by(user_id=session['user_id'], key=key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(user_id=session['user_id'], key=key, value=value)
        db.session.add(setting)
    db.session.commit()

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
                flash(error, 'danger')
            return render_template('register.html')

        try:
            # Create user
            hashed_password = generate_password_hash(password)
            user = User(
                username=username,
                password=hashed_password,
                email=email
            )
            db.session.add(user)
            db.session.flush()  # Get the user ID without committing
            
            # Set default settings for new user
            default_settings = [
                Setting(user_id=user.id, key='company_name', value='Your Company Name'),
                Setting(user_id=user.id, key='company_address', value='Your Company Address'),
                Setting(user_id=user.id, key='company_email', value='your.company@example.com'),
                Setting(user_id=user.id, key='hourly_rate', value='40.00'),
                Setting(user_id=user.id, key='next_invoice_number', value='1001'),
                Setting(user_id=user.id, key='logo_path', value='')
            ]
            db.session.add_all(default_settings)
            
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for_with_prefix('login'))
        except Exception as e:
            db.session.rollback()
            flash('Username or email already exists.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']
        
        user = db.session.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and check_password_hash(user.password, password):
            print(f"[DEBUG] User logged in - ID: {user.id}, Username: {user.username}")
            print(f"[DEBUG] User profile picture path: {user.profile_picture}")
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['profile_picture'] = user.profile_picture
            
            print(f"[DEBUG] Session after login - user_id: {session['user_id']}, username: {session['username']}, profile_picture: {session['profile_picture']}")
            return redirect(url_for_with_prefix('dashboard'))
        
        flash('Invalid username/email or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for_with_prefix('login'))

@app.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for_with_prefix('invoice_list'))
    return redirect(url_for_with_prefix('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    clients = db.session.query(Client).filter_by(user_id=session['user_id']).all()
    labor_items = db.session.query(LaborItem).filter_by(user_id=session['user_id']).all()
    items = db.session.query(Item).filter_by(user_id=session['user_id']).all()
    companies = db.session.query(Business).filter_by(user_id=session['user_id']).all()
    
    # Get selected company from query params or session
    selected_company_id = request.args.get('company_id') or session.get('selected_company_id')
    if selected_company_id:
        selected_company = db.session.query(Business).filter_by(id=selected_company_id, user_id=session['user_id']).first()
        if selected_company:
            session['selected_company_id'] = selected_company.id
    
    # Get selected client from query params or session
    selected_client_id = request.args.get('client_id') or session.get('selected_client_id')
    if selected_client_id:
        selected_client = db.session.query(Client).filter_by(id=selected_client_id, user_id=session['user_id']).first()
        if selected_client:
            session['selected_client_id'] = selected_client.id
    
    return render_template('dashboard.html',
                         clients=clients,
                         labor_items=labor_items,
                         items=items,
                         companies=companies)

@app.route('/new_client', methods=['POST'])
@login_required
def new_client():
    name = request.form['name']
    address = request.form['address']
    email = request.form['email']
    phone = request.form['phone']
    
    client = Client(
        user_id=session['user_id'],
        name=name,
        address=address,
        email=email,
        phone=phone
    )
    db.session.add(client)
    db.session.commit()
    flash('New client created successfully!', 'success')
    return redirect(url_for_with_prefix('dashboard'))

@app.route('/create_invoice', methods=['GET', 'POST'])
@login_required
def create_invoice():
    if request.method == 'POST':
        try:
            # Extract form data
            invoice_number = request.form.get('invoice_number')
            date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
            client_id = request.form.get('client_id') or session.get('selected_client_id')
            business_id = request.form.get('business_id') or session.get('selected_company_id')
            notes = request.form.get('notes')
            sales_tax_id = request.form.get('sales_tax_id')
            tax_applies_to = request.form.get('tax_applies_to')
            
            # Validate required fields
            if not client_id:
                flash('Please select a client.')
                return redirect(url_for_with_prefix('create_invoice'))
            
            if not business_id:
                flash('Please select a business.')
                return redirect(url_for_with_prefix('create_invoice'))
            
            # Create new invoice
            invoice = Invoice(
                user_id=session['user_id'],
                invoice_number=invoice_number,
                date=date,
                due_date=due_date,
                client_id=client_id,
                business_id=business_id,
                notes=notes,
                sales_tax_id=sales_tax_id,
                tax_applies_to=tax_applies_to
            )
            db.session.add(invoice)
            db.session.flush()  # Get the new invoice ID
            
            # Parse line items JSON
            line_items_json = request.form.get('line_items_json')
            if line_items_json:
                line_items = json.loads(line_items_json)
                for item in line_items:
                    if item['type'] == 'item':
                        invoice_item = InvoiceItem(
                            invoice_id=invoice.id,
                            description=item['description'],
                            quantity=item['quantity'],
                            unit_price=item['price'],
                            total=item['total'],
                            date=date
                        )
                        db.session.add(invoice_item)
                    elif item['type'] == 'labor':
                        invoice_labor = InvoiceLabor(
                            invoice_id=invoice.id,
                            description=item['description'],
                            date=datetime.strptime(item['date'], '%Y-%m-%d').date(),
                            hours=float(item['hours']) + float(item.get('minutes', 0)) / 60,
                            rate=item['rate'],
                            total=item['total']
                        )
                        db.session.add(invoice_labor)
            
            db.session.commit()
            flash('Invoice generated successfully!')
            return redirect(url_for_with_prefix('invoice_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error generating invoice: {str(e)}')
            return redirect(url_for_with_prefix('create_invoice'))
    
    # GET request handling
    business_id = request.args.get('business_id')
    businesses = db.session.query(Business).filter_by(user_id=session['user_id']).all()
    selected_business = None
    if business_id:
        selected_business = db.session.query(Business).filter_by(id=business_id, user_id=session['user_id']).first()
    
    clients = db.session.query(Client).filter_by(user_id=session['user_id']).all()
    selected_client_id = session.get('selected_client_id')
    selected_client = None
    if selected_client_id:
        selected_client = db.session.query(Client).filter_by(id=selected_client_id, user_id=session['user_id']).first()
    
    tax_rates = db.session.query(SalesTax).filter_by(user_id=session['user_id']).all()
    
    return render_template('create_invoice.html',
                         businesses=businesses,
                         selected_business=selected_business,
                         clients=clients,
                         selected_client=selected_client,
                         tax_rates=tax_rates)

@app.route('/preview_invoice')
@login_required
def preview_invoice():
    invoice_data = session.get('preview_invoice')
    if not invoice_data:
        flash('No invoice data found')
        return redirect(url_for_with_prefix('dashboard'))
    
    return render_template('invoice_pretty.html', **invoice_data)

@app.route('/download_invoice/<invoice_number>')
@login_required
def download_invoice(invoice_number):
    try:
        # Get invoice details
        invoice = db.session.query(Invoice).filter_by(invoice_number=invoice_number).first()
        if not invoice:
            flash('Invoice not found')
            return redirect(url_for_with_prefix('invoice_list'))
        
        # Get line items and labor items
        line_items = db.session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()
        labor_items = db.session.query(InvoiceLabor).filter_by(invoice_id=invoice.id).all()
        
        # Calculate subtotal
        subtotal = sum(float(item.total) for item in line_items) + sum(float(item.total) for item in labor_items)
        
        # Get sales tax
        sales_tax = db.session.query(SalesTax).filter_by(id=invoice.sales_tax_id).first() if invoice.sales_tax_id else None
        tax_amount = float(subtotal * sales_tax.rate / 100) if sales_tax else 0
        
        # Get company details
        company = invoice.business
        if company and company.logo_path:
            logo_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], company.logo_path))
        else:
            logo_path = None
        
        # Prepare data for template
        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'date': invoice.date.isoformat() if invoice.date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'client': invoice.client.to_dict() if invoice.client else None,
            'company': {
                'name': company.name,
                'address': company.address,
                'phone': company.phone,
                'email': company.email,
                'logo_path': logo_path
            } if company else None,
            'subtotal': float(subtotal),
            'tax_amount': float(tax_amount),
            'total': float(subtotal + tax_amount),
            'notes': invoice.notes,
            'line_items': [{
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.total),
                'date': item.date.isoformat() if item.date else None
            } for item in line_items],
            'labor_items': [{
                'description': item.description,
                'hours': float(item.hours),
                'rate': float(item.rate),
                'total': float(item.total),
                'date': item.date.isoformat() if item.date else None
            } for item in labor_items],
            'sales_tax': sales_tax.to_dict() if sales_tax else None,
            'tax_applies_to': invoice.tax_applies_to
        }
        
        # Render HTML
        html_content = render_template('invoice_pretty.html', **invoice_data)
        
        # Generate PDF
        pdf = HTML(string=html_content).write_pdf()
        
        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=invoice_{invoice_number}.pdf'
        
        return response
        
    except Exception as e:
        flash(f'Error generating invoice: {str(e)}')
        return redirect(url_for_with_prefix('invoice_list'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        company_id = request.form.get('company_id')
        name = request.form.get('name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        invoice_template = request.form.get('invoice_template', 'invoice_pretty')
        
        # Handle logo upload
        logo_path = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create a unique filename
                timestamp = int(time.time())
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Resize the logo
                if resize_logo(filepath):
                    logo_path = filename
                else:
                    flash('Error processing logo image.')
                    return redirect(url_for_with_prefix('settings'))
        
        try:
            if company_id:
                # Update existing company
                company = db.session.query(Business).filter_by(id=company_id, user_id=session['user_id']).first()
                if company:
                    company.name = name
                    company.address = address
                    company.email = email
                    company.phone = phone
                    company.invoice_template = invoice_template
                    if logo_path:
                        company.logo_path = logo_path
            else:
                # Create new company
                company = Business(
                    user_id=session['user_id'],
                    name=name,
                    address=address,
                    email=email,
                    phone=phone,
                    logo_path=logo_path,
                    invoice_template=invoice_template
                )
                db.session.add(company)
            
            db.session.commit()
            flash('Company details saved successfully!')
            next_url = request.form.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('businesses'))
        except Exception as e:
            flash(f'Error saving company details: {str(e)}')
            return redirect(url_for_with_prefix('settings'))
    
    # Get companies for the current user
    companies = db.session.query(Business).filter_by(user_id=session['user_id']).all()
    
    # Get selected company from query parameter or session
    selected_company_id = request.args.get('company_id') or session.get('selected_company_id')
    selected_company = None
    if selected_company_id:
        selected_company = db.session.query(Business).filter_by(id=selected_company_id, user_id=session['user_id']).first()
    
    return render_template('settings.html', companies=companies, selected_company=selected_company)

@app.route('/client_details')
@login_required
def client_details():
    client_id = request.args.get('client_id')
    is_new = request.args.get('new') == 'true'
    
    clients = db.session.query(Client).filter_by(user_id=session['user_id']).all()
    
    selected_client = None
    if client_id and not is_new:
        selected_client = db.session.query(Client).filter_by(id=client_id, user_id=session['user_id']).first()
    
    return render_template('client_details.html', clients=clients, selected_client=selected_client, is_new=is_new)

@app.route('/update_client', methods=['POST'])
@login_required
def update_client():
    client_id = request.form.get('client_id')
    name = request.form.get('name')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')
    from_create_invoice = request.form.get('from_create_invoice') == 'true'
    
    if client_id:
        # Update existing client
        client = db.session.query(Client).filter_by(id=client_id, user_id=session['user_id']).first()
        if client:
            client.name = name
            client.address = address
            client.email = email
            client.phone = phone
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
    flash('Client details saved successfully!', 'success')
    
    if from_create_invoice:
        # Store the selected client ID in the session
        session['selected_client_id'] = client.id
        return redirect(url_for_with_prefix('create_invoice'))
    else:
        return redirect(url_for_with_prefix('dashboard', selected_client=client.id))

@app.route('/update_company', methods=['POST'])
@login_required
def update_company():
    company_id = request.form.get('company_id')
    name = request.form.get('name')
    address = request.form.get('address')
    email = request.form.get('email')
    phone = request.form.get('phone')
    # Handle logo upload
    logo_path = None
    if 'logo' in request.files:
        file = request.files['logo']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Create a unique filename
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Resize the logo
            if resize_logo(filepath):
                logo_path = filename
            else:
                flash('Error processing logo image.')
                if company_id:
                    return redirect(url_for('business_details', business_id=company_id))
                else:
                    return redirect(url_for('business_details', new='true'))
    if company_id:
        company = db.session.query(Business).filter_by(id=company_id, user_id=session['user_id']).first()
        if company:
            company.name = name
            company.address = address
            company.email = email
            company.phone = phone
            if logo_path:
                company.logo_path = logo_path
    else:
        company = Business(
            user_id=session['user_id'],
            name=name,
            address=address,
            email=email,
            phone=phone,
            logo_path=logo_path
        )
        db.session.add(company)
        db.session.flush()  # Get the new company ID
        company_id = company.id
    db.session.commit()
    flash('Company details saved successfully!')
    next_url = request.form.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('businesses'))

@app.route('/labor_details')
@login_required
def labor_details():
    labor_items = db.session.query(LaborItem).filter_by(user_id=session['user_id']).all()
    return render_template('labor_details.html', labor_items=labor_items)

@app.route('/update_labor', methods=['POST'])
@login_required
def update_labor():
    labor_id = request.form.get('labor_id')
    description = request.form.get('description')
    hours = float(request.form.get('hours', 0))
    rate = float(request.form.get('rate', 0))
    source = request.form.get('source', 'labor_details')
    
    if labor_id:
        # Update existing labor item
        labor = db.session.query(LaborItem).filter_by(id=labor_id, user_id=session['user_id']).first()
        if labor:
            labor.description = description
            labor.hours = hours
            labor.rate = rate
    else:
        # Create new labor item
        labor = LaborItem(
            user_id=session['user_id'],
            description=description,
            hours=hours,
            rate=rate
        )
        db.session.add(labor)
        db.session.flush()  # Get the new labor ID without committing
    
    db.session.commit()
    flash('Labor details saved successfully!')
    
    if source == 'create_invoice':
        return redirect(url_for_with_prefix('create_invoice', open_dialog='add_labor', new_labor_id=labor.id))
    return redirect(url_for_with_prefix('labor_details'))

@app.route('/remove_labor_item', methods=['POST'])
@login_required
def remove_labor_item():
    labor_id = request.form.get('labor_id')
    labor = db.session.query(LaborItem).filter_by(id=labor_id, user_id=session['user_id']).first()
    if labor:
        db.session.delete(labor)
        db.session.commit()
    flash('Labor item removed successfully!')
    return redirect(url_for_with_prefix('labor_details'))

@app.route('/item_details')
@login_required
def item_details():
    items = db.session.query(Item).filter_by(user_id=session['user_id']).all()
    return render_template('item_details.html', items=items)

@app.route('/update_item', methods=['POST'])
@login_required
def update_item():
    item_id = request.form.get('item_id')
    description = request.form.get('description')
    price = float(request.form.get('price', 0))
    source = request.form.get('source', 'item_details')
    
    if item_id:
        # Update existing item
        item = db.session.query(Item).filter_by(id=item_id, user_id=session['user_id']).first()
        if item:
            item.description = description
            item.unit_price = price
    else:
        # Create new item
        item = Item(
            user_id=session['user_id'],
            description=description,
            unit_price=price,
            quantity=1
        )
        db.session.add(item)
        db.session.flush()  # Get the new item ID without committing
    
    db.session.commit()
    flash('Item details saved successfully!')
    
    if source == 'create_invoice':
        return redirect(url_for_with_prefix('create_invoice', open_dialog='add_item', new_item_id=item.id))
    return redirect(url_for_with_prefix('item_details'))

@app.route('/remove_item', methods=['POST'])
@login_required
def remove_item():
    item_id = request.form.get('item_id')
    item = db.session.query(Item).filter_by(id=item_id, user_id=session['user_id']).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed successfully!')
    return redirect(url_for_with_prefix('item_details'))

@app.route('/invoice/get_company/<int:company_id>')
@login_required
def get_company(company_id):
    company = db.session.query(Business).filter_by(id=company_id, user_id=session['user_id']).first()
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
    client = db.session.query(Client).filter_by(id=client_id, user_id=session['user_id']).first()
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
    invoice = db.session.query(Invoice).filter_by(invoice_number=invoice_number, user_id=session['user_id']).first()
    return jsonify({'exists': invoice is not None})

@app.route('/save_selections', methods=['POST'])
@login_required
def save_selections():
    data = request.get_json()
    business_id = data.get('businessId')
    client_id = data.get('clientId')
    
    session['selected_company_id'] = business_id
    session['selected_client_id'] = client_id
    
    return jsonify({'success': True})

@app.route('/api/sales-tax', methods=['GET'])
@login_required
def get_sales_tax_rates():
    tax_rates = db.session.query(SalesTax).filter_by(user_id=session['user_id']).all()
    return jsonify([{
        'id': tax.id,
        'rate': tax.rate,
        'description': tax.description
    } for tax in tax_rates])

@app.route('/api/sales-tax', methods=['DELETE'])
@login_required
def delete_all_sales_tax_rates():
    db.session.query(SalesTax).filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    return jsonify({'message': 'All sales tax rates deleted'})

@app.route('/api/sales-tax', methods=['POST'])
@login_required
def create_sales_tax_rate():
    if request.is_json:
        data = request.get_json()
        rate = data.get('rate')
        description = data.get('description')
    else:
        rate = request.form.get('rate')
        description = request.form.get('description')
    
    tax_rate = SalesTax(
        user_id=session['user_id'],
        rate=rate,
        description=description
    )
    db.session.add(tax_rate)
    db.session.commit()
    
    return jsonify({
        'id': tax_rate.id,
        'rate': tax_rate.rate,
        'description': tax_rate.description
    })

@app.route('/api/invoice/<int:invoice_id>/sales-tax', methods=['PUT'])
@login_required
def update_invoice_sales_tax(invoice_id):
    sales_tax_id = request.form.get('sales_tax_id')
    tax_applies_to = request.form.get('tax_applies_to')
    
    invoice = db.session.query(Invoice).filter_by(id=invoice_id, user_id=session['user_id']).first()
    if invoice:
        invoice.sales_tax_id = sales_tax_id
        invoice.tax_applies_to = tax_applies_to
        db.session.commit()
        
        tax_rate = db.session.query(SalesTax).filter_by(id=sales_tax_id).first()
        return jsonify({
            'id': invoice.id,
            'sales_tax_id': invoice.sales_tax_id,
            'tax_applies_to': invoice.tax_applies_to,
            'tax_rate': tax_rate.rate if tax_rate else None,
            'tax_description': tax_rate.description if tax_rate else None
        })
    return jsonify({'error': 'Invoice not found'}), 404

@app.route('/invoice_list')
@login_required
def invoice_list():
    # Get all invoices for the user
    invoices = db.session.query(Invoice).filter_by(user_id=session['user_id']).all()
    
    # Get all clients and companies for the user
    clients = db.session.query(Client).filter_by(user_id=session['user_id']).all()
    companies = db.session.query(Business).filter_by(user_id=session['user_id']).all()
    
    # Create dictionaries for quick lookup
    client_dict = {client.id: client for client in clients}
    company_dict = {company.id: company for company in companies}
    
    # Add client and company names to each invoice
    for invoice in invoices:
        invoice.client_name = client_dict.get(invoice.client_id, Client()).name
        invoice.company_name = company_dict.get(invoice.business_id, Business()).name
        # Calculate total for each invoice
        line_items = db.session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()
        labor_items = db.session.query(InvoiceLabor).filter_by(invoice_id=invoice.id).all()
        subtotal = sum(item.total for item in line_items) + sum(item.total for item in labor_items)
        tax_amount = 0
        if invoice.sales_tax_id:
            sales_tax = db.session.query(SalesTax).filter_by(id=invoice.sales_tax_id).first()
            if sales_tax:
                taxable_amount = 0
                for item in line_items:
                    if (invoice.tax_applies_to == 'items' and 'h' not in str(item.quantity)) or \
                       (invoice.tax_applies_to == 'labor' and 'h' in str(item.quantity)) or \
                       invoice.tax_applies_to == 'both':
                        taxable_amount += item.total
                for item in labor_items:
                    if (invoice.tax_applies_to == 'labor' or invoice.tax_applies_to == 'both'):
                        taxable_amount += item.total
                tax_amount = taxable_amount * (sales_tax.rate / 100)
        invoice.total = subtotal + tax_amount
    
    return render_template('invoice_list.html', invoices=invoices)

@app.route('/invoice/<invoice_number>')
@login_required
def view_invoice(invoice_number):
    try:
        # Get invoice data
        invoice = db.session.query(Invoice).filter_by(invoice_number=invoice_number, user_id=session['user_id']).first()
        if not invoice:
            flash('Invoice not found', 'danger')
            return redirect(url_for_with_prefix('invoice_list'))
        
        # Get company info
        company = db.session.query(Business).filter_by(id=invoice.business_id).first()
        if not company:
            flash('Company information not found', 'danger')
            return redirect(url_for_with_prefix('invoice_list'))
        
        # Get line items
        line_items = db.session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()
        labor_items = db.session.query(InvoiceLabor).filter_by(invoice_id=invoice.id).all()
        
        # Calculate totals
        subtotal = sum(float(item.total) for item in line_items) + sum(float(item.total) for item in labor_items)
        tax_amount = 0
        if invoice.sales_tax_id:
            sales_tax = db.session.query(SalesTax).filter_by(id=invoice.sales_tax_id).first()
            if sales_tax:
                taxable_amount = 0
                for item in line_items:
                    if (invoice.tax_applies_to == 'items' and 'h' not in str(item.quantity)) or \
                       (invoice.tax_applies_to == 'labor' and 'h' in str(item.quantity)) or \
                       invoice.tax_applies_to == 'both':
                        taxable_amount += float(item.total)
                for item in labor_items:
                    if (invoice.tax_applies_to == 'labor' or invoice.tax_applies_to == 'both'):
                        taxable_amount += float(item.total)
                tax_amount = taxable_amount * (float(sales_tax.rate) / 100)
        
        total = subtotal + tax_amount
        
        return render_template('view_invoice.html', 
                             invoice=invoice,
                             company=company,
                             line_items=line_items,
                             labor_items=labor_items,
                             subtotal=subtotal,
                             tax_amount=tax_amount,
                             total=total)
    except Exception as e:
        flash(f'Error viewing invoice: {str(e)}', 'danger')
        return redirect(url_for_with_prefix('invoice_list'))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        user = db.session.query(User).filter_by(id=session['user_id']).first()
        if user:
            user.username = username
            user.email = email
            db.session.commit()
            flash('Profile updated successfully!')
        return redirect(url_for_with_prefix('dashboard'))
    
    user = db.session.query(User).filter_by(id=session['user_id']).first()
    return render_template('edit_profile.html', user=user)

@app.context_processor
def inject_app_root():
    return dict(app_root='/invoice')

@app.context_processor
def inject_get_setting():
    return dict(get_setting=get_setting)

@app.route('/businesses')
def businesses():
    businesses = db.session.query(Business).filter_by(user_id=session['user_id']).all()
    return render_template('businesses.html', businesses=businesses)

@app.route('/clients')
def clients():
    clients = db.session.query(Client).filter_by(user_id=session['user_id']).all()
    return render_template('clients.html', clients=clients)

@app.route('/remove_business/<int:business_id>', methods=['POST'])
def remove_business(business_id):
    business = db.session.query(Business).filter_by(id=business_id, user_id=session['user_id']).first()
    if business:
        db.session.delete(business)
        db.session.commit()
        flash('Business removed successfully!')
    return redirect(url_for_with_prefix('businesses'))

@app.route('/remove_client/<int:client_id>', methods=['POST'])
def remove_client(client_id):
    client = db.session.query(Client).filter_by(id=client_id, user_id=session['user_id']).first()
    if client:
        db.session.delete(client)
        db.session.commit()
        flash('Client removed successfully!')
    return redirect(url_for_with_prefix('clients'))

@app.route('/business_details', methods=['GET', 'POST'])
@login_required
def business_details():
    if request.method == 'POST':
        # Handle new business creation
        name = request.form.get('name')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # Handle logo upload
        logo_path = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create a unique filename
                timestamp = int(time.time())
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Resize the logo
                resize_logo(filepath)
                logo_path = filename
        
        # Create new business
        business = Business(
            user_id=session['user_id'],
            name=name,
            address=address,
            email=email,
            phone=phone,
            logo_path=logo_path
        )
        db.session.add(business)
        db.session.commit()
        
        # Handle redirection based on source
        source = request.form.get('source')
        if source == 'create_invoice':
            return redirect(url_for_with_prefix('create_invoice', business_id=business.id))
        return redirect(url_for_with_prefix('businesses'))
    
    # GET request handling
    business_id = request.args.get('business_id')
    is_new = request.args.get('new') == 'true'
    source = request.args.get('source')  # Get source from query parameters
    businesses = db.session.query(Business).filter_by(user_id=session['user_id']).all()
    selected_business = None
    if business_id and not is_new:
        selected_business = db.session.query(Business).filter_by(id=business_id, user_id=session['user_id']).first()
    return render_template('business_details.html', 
                         businesses=businesses, 
                         selected_business=selected_business, 
                         is_new=is_new,
                         source=source)  # Pass source to template

@app.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Start the application
    app.run(debug=True, port=8080) 