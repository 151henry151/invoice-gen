import pytest
from app import app, db
from models import User, Client
from werkzeug.security import generate_password_hash
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            # Create a test user and client
            user = User(username='testuser', password=generate_password_hash('password'), email='test@example.com')
            db.session.add(user)
            db.session.commit()
            client_obj = Client(user_id=user.id, name='Test Client', address='123 Test St', email='client@example.com', phone='555-1234')
            db.session.add(client_obj)
            db.session.commit()
        yield client


def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def test_login(client):
    rv = login(client, 'testuser', 'password')
    assert b'Logged in successfully!' in rv.data


def test_generate_invoice_pdf(client):
    # Log in
    login(client, 'testuser', 'password')

    # Prepare invoice data
    invoice_data = {
        'client': 1,
        'date': '2025-05-17',
        'invoice_number': 'TEST-1001',
        'line_items_json': '[{"type":"item","description":"Test Item","quantity":2,"price":50,"total":100,"date":"2025-05-17"}]'
    }

    # Generate invoice (PDF)
    response = client.post('/create_invoice', data=invoice_data, follow_redirects=True)
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'

    # Save PDF to file
    pdf_path = 'test_invoice.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(response.data)
    print(f"\nPDF generated: {pdf_path}\nOpen this file to view the invoice.")

# You can add more tests for creating companies, clients, items, labor types, and invoices as needed. 