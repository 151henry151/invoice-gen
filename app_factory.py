from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Business, Setting, Client, Invoice, SalesTax, Item, LaborItem, InvoiceItem, InvoiceLabor
import os

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
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Register blueprints and routes
    from app import register_routes
    register_routes(app)
    
    return app 