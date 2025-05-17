from app import app, db
from models import User, Company, Client, Item, LaborType, Invoice, LineItem
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create a user
    user = User(username='testuser', password=generate_password_hash('password'), email='test@example.com')
    db.session.add(user)
    db.session.commit()

    # Create a company
    company = Company(user_id=user.id, name='Test Company', address='123 Test St', email='company@example.com', phone='555-1234')
    db.session.add(company)
    db.session.commit()

    # Create a client
    client = Client(user_id=user.id, name='Test Client', address='456 Client Rd', email='client@example.com', phone='555-5678')
    db.session.add(client)
    db.session.commit()

    # Create items
    item1 = Item(user_id=user.id, description='Box of Nails', price=39.00)
    db.session.add(item1)
    db.session.commit()

    # Create labor types
    labor1 = LaborType(user_id=user.id, description='work', rate=10.00)
    labor2 = LaborType(user_id=user.id, description='consulting', rate=45.50)
    db.session.add(labor1)
    db.session.add(labor2)
    db.session.commit()

    # Create an invoice
    invoice = Invoice(
        invoice_number='1001',
        client_id=client.id,
        date=date(2025, 5, 17),
        due_date=date(2025, 6, 16),
        notes='hey hey thanks for the work',
        total=627.50,
        sales_tax_id=None,
        tax_applies_to='items'
    )
    db.session.add(invoice)
    db.session.commit()

    # Add line items
    line1 = LineItem(
        invoice_id=invoice.id,
        description='work @ $10/hr',
        quantity=4.25,
        unit_price=10.00,
        total=42.50,
        date=date(2025, 5, 14)
    )
    line2 = LineItem(
        invoice_id=invoice.id,
        description='nails @ $39/hr',
        quantity=15.0,
        unit_price=39.00,
        total=585.00,
        date=date(2025, 5, 17)
    )
    db.session.add(line1)
    db.session.add(line2)
    db.session.commit()

    print("Seed data created successfully!") 