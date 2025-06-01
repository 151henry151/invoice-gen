from app import app, db
from models import User, Business, Setting, Client, Invoice, SalesTax, Item, LaborItem, InvoiceItem, InvoiceLabor

with app.app_context():
    db.create_all()
    print('All tables created successfully.') 