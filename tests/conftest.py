import pytest
from app_factory import create_app
from models import db as _db
import os
import tempfile
import models
from faker import Faker

fake = Faker()

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    _app = create_app('testing')
    return _app

@pytest.fixture(scope='session')
def db(app):
    """Create database for the tests."""
    with app.app_context():
        # Create all tables
        _db.create_all()
        
        # Create a test user for the session
        test_user = models.User(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        _db.session.add(test_user)
        _db.session.commit()
        
        yield _db
        
        # Clean up
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(db):
    """Get the test user."""
    return db.session.query(models.User).filter_by(username='testuser').first()

@pytest.fixture
def auth_client(client, test_user):
    """Create an authenticated client."""
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
        session['_fresh'] = True  # Mark session as fresh
        session['_id'] = 'test-session-id'  # Add a session ID
    return client

@pytest.fixture
def test_business(db, test_user):
    """Create a test business."""
    business = models.Business(
        name='Test Business',
        address='123 Test St',
        email='business@test.com',
        phone='123-456-7890',
        user_id=test_user.id
    )
    db.session.add(business)
    db.session.commit()
    return business

@pytest.fixture
def test_client_obj(db, test_user):
    """Create a test client."""
    client_obj = models.Client(
        name='Test Client',
        address='456 Client Ave',
        email='client@test.com',
        phone='098-765-4321',
        user_id=test_user.id
    )
    db.session.add(client_obj)
    db.session.commit()
    return client_obj

@pytest.fixture
def test_item(db, test_user):
    """Create a test item."""
    item = models.Item(
        description='Test Item',
        quantity=1,
        unit_price=100.00,
        user_id=test_user.id
    )
    db.session.add(item)
    db.session.commit()
    return item

@pytest.fixture
def test_tax_rate(db, test_user):
    """Create a test tax rate."""
    tax_rate = models.SalesTax(
        rate=8.5,
        description='Test Tax',
        user_id=test_user.id
    )
    db.session.add(tax_rate)
    db.session.commit()
    return tax_rate

@pytest.fixture
def fake_data():
    """Generate fake data for testing."""
    return {
        'business': {
            'name': fake.company(),
            'address': fake.street_address(),
            'email': fake.company_email(),
            'phone': fake.phone_number()
        },
        'client': {
            'name': fake.company(),
            'address': fake.street_address(),
            'email': fake.company_email(),
            'phone': fake.phone_number()
        },
        'item': {
            'description': fake.sentence(),
            'quantity': fake.random_int(min=1, max=10),
            'unit_price': fake.pyfloat(min_value=0.01, max_value=1000.00)
        },
        'tax_rate': {
            'rate': fake.pyfloat(min_value=0.0, max_value=100.0),
            'description': fake.word()
        }
    } 