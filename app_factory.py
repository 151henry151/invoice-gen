from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Business, Setting, Client, Invoice, SalesTax, Item, LaborItem, InvoiceItem, InvoiceLabor
import os
from datetime import timedelta

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configure based on environment
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db/invoice_gen.db')
    
    # Common configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # Configure URL prefix and scheme for local development
    app.config['APPLICATION_ROOT'] = '/invoice'
    app.config['PREFERRED_URL_SCHEME'] = 'http'
    app.config['SESSION_COOKIE_SECURE'] = False  # Allow cookies over HTTP
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'  # Set cookie path to root to ensure it's available across all paths
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Set session lifetime
    
    # Configure static files - serve from /invoice/static
    app.static_folder = 'static'
    app.static_url_path = '/invoice/static'  # Explicitly set the full path including APPLICATION_ROOT
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Register blueprints and routes
    from app import register_routes
    register_routes(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app

# Create a single app instance for Gunicorn
app = create_app() 