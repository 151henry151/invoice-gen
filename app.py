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
import configparser
from sqlalchemy.sql import text

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_LOGO_SIZE = (200, 200)

def register_routes(app):
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # Custom URL generator to ensure proper URL generation with application root
    def url_for_with_prefix(*args, **kwargs):
        if args[0] == 'static':
            # For static files, use the standard url_for with application root prefix
            kwargs['_external'] = False
            kwargs['_scheme'] = None
            kwargs['_anchor'] = None
            return url_for(*args, **kwargs)
        
        # For all other routes, use the prefix
        kwargs['_external'] = True
        kwargs['_scheme'] = 'http'  # Always use HTTP for local development
        return url_for(*args, **kwargs)

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def resize_logo(image_path):
        """Resize the logo while maintaining aspect ratio"""
        try:
            from PIL import Image
            img = Image.open(image_path)
            width, height = img.size
            max_size = 200
            
            if width > height:
                new_width = min(width, max_size)
                new_height = int(height * (new_width / width))
            else:
                new_height = min(height, max_size)
                new_width = int(width * (new_height / height))
            
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
        pass

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
                db.session.flush()
                
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
                session.clear()  # Clear any existing session data
                session['user_id'] = user.id
                session['username'] = user.username
                session['profile_picture'] = user.profile_picture
                session.permanent = True  # Make the session persistent
                
                # Debug logging
                print(f"[DEBUG] User logged in - ID: {user.id}, Username: {user.username}")
                print(f"[DEBUG] Session after login - user_id: {session.get('user_id')}, username: {session.get('username')}")
                
                # Use url_for_with_prefix to ensure proper URL generation
                return redirect(url_for_with_prefix('dashboard'))
            
            flash('Invalid username/email or password!')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for_with_prefix('login'))

    @app.route('/')
    @login_required
    def index():
        return redirect(url_for('dashboard'))

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
                client_id = request.form.get('client_id')
                business_id = request.form.get('business_id')
                notes = request.form.get('notes')
                sales_tax_id = request.form.get('sales_tax_id')
                tax_applies_to = request.form.get('tax_applies_to')
                
                # Validate invoice number
                if not invoice_number:
                    flash('Invoice number is required', 'danger')
                    return redirect(url_for_with_prefix('create_invoice'))
                
                # Check for duplicate invoice number
                existing_invoice = db.session.query(Invoice).filter_by(
                    invoice_number=invoice_number,
                    user_id=session['user_id']
                ).first()
                if existing_invoice:
                    flash('This invoice number is already in use. Please choose a different one.', 'danger')
                    return redirect(url_for_with_prefix('create_invoice'))
                
                # Validate invoice number format (alphanumeric with optional hyphens and underscores)
                if not re.match(r'^[A-Za-z0-9\-_]+$', invoice_number):
                    flash('Invoice number can only contain letters, numbers, hyphens, and underscores', 'danger')
                    return redirect(url_for_with_prefix('create_invoice'))
                
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
                        elif item['type'] == 'note':
                            invoice_note = InvoiceItem(
                                invoice_id=invoice.id,
                                description=item['description'],
                                quantity=1,
                                unit_price=0,
                                total=0,
                                date=date
                            )
                            db.session.add(invoice_note)
                
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
        items = db.session.query(Item).filter_by(user_id=session['user_id']).all()
        labor_items = db.session.query(LaborItem).filter_by(user_id=session['user_id']).all()
        
        return render_template('create_invoice.html',
                             businesses=businesses,
                             selected_business=selected_business,
                             clients=clients,
                             selected_client=selected_client,
                             tax_rates=tax_rates,
                             items=items,
                             labor_items=labor_items)

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
            
            # Get all line items (items, labor, notes) in order
            all_line_items = []
            for item in db.session.query(InvoiceItem).filter_by(invoice_id=invoice.id).order_by(InvoiceItem.id).all():
                if item.quantity == 1 and item.unit_price == 0 and item.total == 0:
                    all_line_items.append({
                        'type': 'note',
                        'description': item.description,
                        'date': item.date.isoformat() if item.date else None
                    })
                else:
                    all_line_items.append({
                        'type': 'item',
                        'description': item.description,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total': float(item.total),
                        'date': item.date.isoformat() if item.date else None
                    })
            for labor in db.session.query(InvoiceLabor).filter_by(invoice_id=invoice.id).order_by(InvoiceLabor.id).all():
                all_line_items.append({
                    'type': 'labor',
                    'description': labor.description,
                    'hours': float(labor.hours),
                    'rate': float(labor.rate),
                    'total': float(labor.total),
                    'date': labor.date.isoformat() if labor.date else None
                })
            # Sort all_line_items by date (and fallback to id if needed)
            all_line_items.sort(key=lambda x: (x['date'] or ''))
            # Calculate subtotal and tax (exclude notes)
            subtotal = sum(item['total'] for item in all_line_items if item['type'] in ('item', 'labor'))
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
                'all_line_items': all_line_items,
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
        user = db.session.query(User).filter_by(id=session['user_id']).first()
        if request.method == 'POST':
            try:
                username = request.form.get('username')
                email = request.form.get('email')
                # Handle profile picture upload
                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(f"profile_{session['user_id']}_{file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        user.profile_picture = filename
                # Handle password change
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                if username:
                    user.username = username
                if email:
                    user.email = email
                if new_password:
                    if not current_password or not check_password_hash(user.password, current_password):
                        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({'success': False, 'message': 'Current password is incorrect.'})
                        flash('Current password is incorrect.', 'danger')
                        return render_template('edit_profile.html', user=user)
                    user.password = generate_password_hash(new_password)
                db.session.commit()
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    profile_picture_url = url_for('serve_upload', filename=user.profile_picture) if user.profile_picture else ''
                    return jsonify({
                        'success': True,
                        'profile_picture': profile_picture_url
                    })
                flash('Profile updated successfully!')
                return redirect(url_for('settings'))
            except Exception as e:
                import traceback
                error_message = f"{str(e)}\n{traceback.format_exc()}"
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_message}), 500
                flash(f'Error updating profile: {error_message}', 'danger')
                return render_template('edit_profile.html', user=user)
        return render_template('edit_profile.html', user=user)

    @app.route('/edit_profile', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        return redirect(url_for('settings'))

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
            return redirect(url_for_with_prefix('clients'))

    @app.route('/update_company', methods=['POST'])
    @login_required
    def update_company():
        company_id = request.form.get('company_id')
        name = request.form.get('name')
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')
        country = request.form.get('country')
        email = request.form.get('email')
        phone = request.form.get('phone')
        invoice_template = request.form.get('invoice_template', 'invoice_pretty')
        
        # Combine address fields
        address_parts = [address_line1]
        if address_line2:
            address_parts.append(address_line2)
        address_parts.extend([city, state, postal_code, country])
        address = ', '.join(filter(None, address_parts))
        
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
                company.invoice_template = invoice_template
                if logo_path:
                    company.logo_path = logo_path
        else:
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
            db.session.flush()  # Get the new company ID
            company_id = company.id
        db.session.commit()
        flash('Company details saved successfully!')
        next_url = request.form.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('businesses'))

    @app.route('/item_details')
    @login_required
    def item_details():
        item_id = request.args.get('item_id')
        is_new = request.args.get('new') == 'true'
        source = request.args.get('source')
        
        # Get client and business IDs from query parameters
        client_id = request.args.get('client_id')
        business_id = request.args.get('business_id')
        
        # If this is an AJAX request for item details
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and item_id:
            item = db.session.query(Item).filter_by(id=item_id, user_id=session['user_id']).first()
            if item:
                return jsonify(item.to_dict())
            return jsonify({'error': 'Item not found'}), 404
        
        # Regular page request
        items = db.session.query(Item).filter_by(user_id=session['user_id']).all()
        selected_item = None
        if item_id and not is_new:
            selected_item = db.session.query(Item).filter_by(id=item_id, user_id=session['user_id']).first()
        
        # Store client and business IDs in session if provided
        if client_id:
            session['selected_client_id'] = client_id
        if business_id:
            session['selected_company_id'] = business_id
        
        return render_template('item_details.html', 
                             items=items, 
                             selected_item=selected_item, 
                             is_new=is_new,
                             source=source)

    @app.route('/labor_details')
    @login_required
    def labor_details():
        item_id = request.args.get('item_id')
        is_new = request.args.get('new') == 'true'
        source = request.args.get('source')
        
        # Get client and business IDs from query parameters
        client_id = request.args.get('client_id')
        business_id = request.args.get('business_id')
        
        conn = get_db()
        labor_items = conn.execute(text('SELECT * FROM labor_items WHERE user_id = :user_id'),
                                 {'user_id': session['user_id']}).fetchall()
        
        selected_item = None
        if item_id and not is_new:
            selected_item = conn.execute(text('SELECT * FROM labor_items WHERE id = :item_id AND user_id = :user_id'),
                                       {'item_id': item_id, 'user_id': session['user_id']}).fetchone()
        
        # Store client and business IDs in session if provided
        if client_id:
            session['selected_client_id'] = client_id
        if business_id:
            session['selected_company_id'] = business_id
        
        return render_template('labor_details.html', 
                             labor_items=labor_items, 
                             selected_item=selected_item, 
                             is_new=is_new,
                             source=source)

    @app.route('/update_labor', methods=['POST'])
    @login_required
    def update_labor():
        item_id = request.form.get('item_id')
        description = request.form.get('description')
        rate = request.form.get('rate')
        source = request.form.get('source')
        
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
            cursor = conn.execute('''INSERT INTO labor_items (user_id, description, rate, hours)
                           VALUES (?, ?, ?, ?)''',
                        (session['user_id'], description, rate, 0))
            new_id = cursor.lastrowid
        
        conn.commit()
        flash('Labor item saved successfully!')
        
        # Get client and business IDs from session
        client_id = session.get('selected_client_id')
        business_id = session.get('selected_company_id')
        
        # Redirect back to invoice page with state preservation
        if source == 'create_invoice':
            return redirect(url_for('create_invoice', 
                                  open_dialog='add_labor', 
                                  new_labor_id=new_id,
                                  client_id=client_id,
                                  business_id=business_id))
        return redirect(url_for('dashboard'))

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

    @app.route('/update_item', methods=['POST'])
    @login_required
    def update_item():
        item_id = request.form.get('item_id')
        description = request.form.get('description')
        price = request.form.get('price')
        source = request.form.get('source')
        
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
        
        # Get client and business IDs from session
        client_id = session.get('selected_client_id')
        business_id = session.get('selected_company_id')
        
        # Redirect back to invoice page with state preservation
        if source == 'create_invoice':
            return redirect(url_for('create_invoice', 
                                  open_dialog='add_item', 
                                  new_item_id=new_id,
                                  client_id=client_id,
                                  business_id=business_id))
        return redirect(url_for('dashboard'))

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
                'id': company.id,
                'name': company.name,
                'address': company.address,
                'email': company.email,
                'phone': company.phone,
                'logo_path': company.logo_path
            })
        return jsonify({'error': 'Company not found'}), 404

    @app.route('/invoice/get_client/<int:client_id>')
    @login_required
    def get_client(client_id):
        client = db.session.query(Client).filter_by(id=client_id, user_id=session['user_id']).first()
        if client:
            return jsonify(client.to_dict())
        return jsonify({'error': 'Client not found'}), 404

    @app.route('/invoice/check_invoice_number/<invoice_number>')
    @login_required
    def check_invoice_number(invoice_number):
        invoice = db.session.query(Invoice).filter_by(invoice_number=invoice_number, user_id=session['user_id']).first()
        return jsonify({'exists': invoice is not None})

    @app.route('/save_selections', methods=['POST'])
    @login_required
    def save_selections():
        data = request.get_json()
        if data:
            session['selected_company_id'] = data.get('businessId')
            session['selected_client_id'] = data.get('clientId')
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

    @app.route('/clear_tax_rates', methods=['POST'])
    @login_required
    def clear_tax_rates():
        try:
            # Delete all tax rates for the current user
            db.session.query(SalesTax).filter_by(user_id=session['user_id']).delete()
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error clearing tax rates: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/invoice/create_sales_tax_rate', methods=['POST'])
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
        
        try:
            # Check for duplicate description
            existing = SalesTax.query.filter_by(
                user_id=session['user_id'],
                description=data['description']
            ).first()
            
            if existing:
                print("Duplicate description found:", data['description'])  # Debug log
                return jsonify({'error': 'A tax rate with this description already exists'}), 400
            
            # Create new tax rate
            new_tax = SalesTax(
                user_id=session['user_id'],
                rate=rate,
                description=data['description']
            )
            db.session.add(new_tax)
            db.session.commit()
            
            print("Successfully created tax rate:", new_tax)  # Debug log
            return jsonify({
                'id': new_tax.id,
                'rate': new_tax.rate,
                'description': new_tax.description
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print("Database error:", str(e))  # Debug log
            return jsonify({'error': 'Database error occurred'}), 500

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

    @app.context_processor
    def inject_app_root():
        return dict(APP_ROOT='/invoice')

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
    @login_required
    def remove_business(business_id):
        try:
            business = db.session.query(Business).filter_by(id=business_id, user_id=session['user_id']).first()
            if business:
                db.session.delete(business)
                db.session.commit()
                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Business not found'}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

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
        # Read Google Maps API key from credentials.ini
        config = configparser.ConfigParser()
        config.read('credentials.ini')
        env = os.environ.get('FLASK_ENV', 'development')
        section = 'dev' if env == 'development' else 'production'
        api_key = config.get(section, 'GOOGLE_MAPS_API_KEY', fallback='')

        if request.method == 'POST':
            name = request.form.get('name')
            address_line1 = request.form.get('address_line1')
            address_line2 = request.form.get('address_line2')
            city = request.form.get('city')
            state = request.form.get('state')
            postal_code = request.form.get('postal_code')
            country = request.form.get('country')
            email = request.form.get('email')
            phone = request.form.get('phone')
            business_id = request.form.get('business_id')
            
            # Combine address fields
            address_parts = [address_line1]
            if address_line2:
                address_parts.append(address_line2)
            address_parts.extend([city, state, postal_code, country])
            address = ', '.join(filter(None, address_parts))
            
            # Handle logo upload
            logo_path = None
            if 'logo' in request.files:
                logo = request.files['logo']
                if logo and logo.filename:
                    filename = secure_filename(logo.filename)
                    logo_path = filename
                    logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            if business_id:
                # Update existing business
                business = db.session.query(Business).filter_by(id=business_id, user_id=session['user_id']).first()
                if business:
                    business.name = name
                    business.address = address
                    business.email = email
                    business.phone = phone
                    if logo_path:
                        business.logo_path = logo_path
                    db.session.commit()
                    flash('Business details updated successfully!')
            else:
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
                flash('New business created successfully!')
            
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
                             source=source,
                             GOOGLE_MAPS_API_KEY=api_key)  # Pass API key to template

    @app.route('/serve_upload/<path:filename>')
    @login_required
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/delete_invoice/<invoice_number>', methods=['POST'])
    @login_required
    def delete_invoice(invoice_number):
        try:
            # Get the invoice
            invoice = db.session.query(Invoice).filter_by(invoice_number=invoice_number, user_id=session['user_id']).first()
            if not invoice:
                flash('Invoice not found', 'danger')
                return redirect(url_for_with_prefix('invoice_list'))
            
            # Delete the invoice (cascade will handle related items)
            db.session.delete(invoice)
            db.session.commit()
            flash('Invoice deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting invoice: {str(e)}', 'danger')
        
        return redirect(url_for_with_prefix('invoice_list'))

    @app.route('/edit_invoice/<invoice_number>', methods=['GET', 'POST'])
    @login_required
    def edit_invoice(invoice_number):
        invoice = db.session.query(Invoice).filter_by(invoice_number=invoice_number, user_id=session['user_id']).first()
        if not invoice:
            flash('Invoice not found', 'danger')
            return redirect(url_for_with_prefix('invoice_list'))
        
        if request.method == 'POST':
            try:
                # Extract form data
                date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
                due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
                client_id = request.form.get('client_id')
                business_id = request.form.get('business_id')
                notes = request.form.get('notes')
                sales_tax_id = request.form.get('sales_tax_id')
                tax_applies_to = request.form.get('tax_applies_to')
                
                # Validate required fields
                if not client_id:
                    flash('Please select a client.')
                    return redirect(url_for_with_prefix('edit_invoice', invoice_number=invoice_number))
                
                if not business_id:
                    flash('Please select a business.')
                    return redirect(url_for_with_prefix('edit_invoice', invoice_number=invoice_number))
                
                # Update invoice
                invoice.date = date
                invoice.due_date = due_date
                invoice.client_id = client_id
                invoice.business_id = business_id
                invoice.notes = notes
                invoice.sales_tax_id = sales_tax_id
                invoice.tax_applies_to = tax_applies_to
                
                # Clear existing items and labor
                db.session.query(InvoiceItem).filter_by(invoice_id=invoice.id).delete()
                db.session.query(InvoiceLabor).filter_by(invoice_id=invoice.id).delete()
                
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
                        elif item['type'] == 'note':
                            invoice_note = InvoiceItem(
                                invoice_id=invoice.id,
                                description=item['description'],
                                quantity=1,
                                unit_price=0,
                                total=0,
                                date=date
                            )
                            db.session.add(invoice_note)
                
                db.session.commit()
                flash('Invoice updated successfully!')
                return redirect(url_for_with_prefix('invoice_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating invoice: {str(e)}')
                return redirect(url_for_with_prefix('edit_invoice', invoice_number=invoice_number))
        
        # GET request handling
        businesses = db.session.query(Business).filter_by(user_id=session['user_id']).all()
        clients = db.session.query(Client).filter_by(user_id=session['user_id']).all()
        tax_rates = db.session.query(SalesTax).filter_by(user_id=session['user_id']).all()
        line_items = db.session.query(InvoiceItem).filter_by(invoice_id=invoice.id).all()
        labor_items = db.session.query(InvoiceLabor).filter_by(invoice_id=invoice.id).all()
        items = db.session.query(Item).filter_by(user_id=session['user_id']).all()
        return render_template('create_invoice.html',
            businesses=businesses,
            selected_business=invoice.business,
            selected_company=invoice.business,
            clients=clients,
            selected_client=invoice.client,
            tax_rates=tax_rates,
            invoice=invoice,
            is_edit=True,
            line_items=line_items,
            labor_items=labor_items,
            items=items
        )

    def format_labor_hours(hours):
        """Format labor hours as 'Xhr Ym' where Y is minutes."""
        whole_hours = int(hours)
        minutes = int((hours - whole_hours) * 60)
        if minutes == 0:
            return f"{whole_hours}hr"
        return f"{whole_hours}hr {minutes}m"

    app.jinja_env.filters['format_labor_hours'] = format_labor_hours

    def format_price(price, show_cents=True):
        """Format price with conditional decimal places.
        show_cents=True: Always show 2 decimal places (for subtotal, tax, total)
        show_cents=False: Only show cents if they exist (for line items)"""
        if show_cents:
            return f"${price:.2f}"
        # Only show cents if they exist
        if price == int(price):
            return f"${int(price)}"
        return f"${price:.2f}"

    app.jinja_env.filters['format_price'] = format_price

    def format_date(date_str):
        """Format date string from YYYY-MM-DD to MM/DD/YYYY."""
        if not date_str:
            return ""
        try:
            # Handle both string and date object inputs
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date_obj = date_str
            return date_obj.strftime('%m/%d/%Y')
        except (ValueError, TypeError):
            return date_str

    app.jinja_env.filters['format_date'] = format_date

    app.jinja_env.globals.update(url_for_with_prefix=url_for_with_prefix) 

    # Register API routes
    @app.route('/invoice/api/items')
    @login_required
    def get_items():
        items = db.session.query(Item).filter_by(user_id=session['user_id']).all()
        return jsonify([{
            'id': item.id,
            'description': item.description,
            'price': float(item.unit_price)
        } for item in items])

    @app.route('/invoice/api/labor_items')
    @login_required
    def get_labor_items():
        labor_items = db.session.query(LaborItem).filter_by(user_id=session['user_id']).all()
        return jsonify([{
            'id': item.id,
            'description': item.description,
            'rate': float(item.rate)
        } for item in labor_items]) 