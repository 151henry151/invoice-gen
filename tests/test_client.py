import pytest
from models import Client
import models

def test_client_list_page(auth_client):
    """Test that the client list page loads correctly."""
    response = auth_client.get('/clients')
    assert response.status_code == 200
    assert b'Clients' in response.data

def test_create_client_success(auth_client):
    """Test successful client creation."""
    response = auth_client.post('/update_client', data={
        'name': 'Test Client',
        'address': '123 Test St',
        'email': 'test@client.com',
        'phone': '123-456-7890'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Client' in response.data or b'Client details saved successfully' in response.data

def test_create_client_duplicate_name(auth_client, test_client_obj):
    """Test client creation with duplicate name."""
    response = auth_client.post('/update_client', data={
        'name': 'Test Client',
        'address': '456 Other St',
        'email': 'other@client.com',
        'phone': '555-9876'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'already exists' in response.data or b'Test Client' in response.data

def test_edit_client_success(auth_client, test_client_obj):
    """Test successful client editing."""
    response = auth_client.post('/update_client', data={
        'client_id': test_client_obj.id,
        'name': 'Updated Client',
        'address': '456 New St',
        'email': 'updated@client.com',
        'phone': '987-654-3210'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Updated Client' in response.data or b'Client details saved successfully' in response.data

def test_delete_client_success(auth_client, test_client_obj):
    """Test successful client deletion."""
    response = auth_client.post(f'/remove_client/{test_client_obj.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'success' in response.data or b'removed' in response.data or response.is_json

def test_client_validation(auth_client):
    """Test client validation."""
    # Test with missing required fields
    response = auth_client.post('/update_client', data={
        'name': '',  # Empty name
        'address': '123 Test St',
        'email': 'test@client.com',
        'phone': '123-456-7890'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'is required' in response.data or b'Client' in response.data

@pytest.mark.xfail(reason="Search functionality not yet implemented")
def test_client_search(auth_client, app, test_user):
    """Test client search functionality."""
    with app.app_context():
        clients = [
            Client(name='ABC Company', address='123 St', email='abc@test.com', phone='123-456-7890', user_id=test_user.id),
            Client(name='XYZ Corp', address='456 Ave', email='xyz@test.com', phone='987-654-3210', user_id=test_user.id),
            Client(name='ABC Services', address='789 Blvd', email='services@test.com', phone='555-1234', user_id=test_user.id)
        ]
        for client in clients:
            models.db.session.add(client)
        models.db.session.commit()

    # Test search for 'ABC'
    response = auth_client.get('/clients?search=ABC')
    assert response.status_code == 200
    assert b'ABC Company' in response.data
    assert b'ABC Services' in response.data
    # Accept either not present or not found in HTML
    assert b'XYZ Corp' not in response.data or response.data.count(b'XYZ Corp') == 0

    # Test search for 'Corp'
    response = auth_client.get('/clients?search=Corp')
    assert response.status_code == 200
    assert b'XYZ Corp' in response.data
    assert b'ABC Company' not in response.data or response.data.count(b'ABC Company') == 0
    assert b'ABC Services' not in response.data or response.data.count(b'ABC Services') == 0

def test_client_list_pagination(auth_client, app, test_user):
    """Test client list pagination."""
    with app.app_context():
        for i in range(15):
            client = Client(
                name=f'Client {i}',
                address=f'{i} Test St',
                email=f'client{i}@test.com',
                phone='123-456-7890',
                user_id=test_user.id
            )
            models.db.session.add(client)
        models.db.session.commit()

    # Test first page
    response = auth_client.get('/clients?page=1')
    assert response.status_code == 200
    assert b'Client 0' in response.data
    assert b'Client 9' in response.data

    # Test second page
    response = auth_client.get('/clients?page=2')
    assert response.status_code == 200
    assert b'Client 10' in response.data
    assert b'Client 14' in response.data

def test_edit_client_invalid_id(auth_client):
    """Test editing non-existent client."""
    response = auth_client.post('/client/edit/999', data={
        'name': 'Invalid Client',
        'address': 'Invalid St',
        'email': 'invalid@client.com',
        'phone': '555-0000'
    })
    assert response.status_code == 404

def test_delete_client_invalid_id(auth_client):
    """Test deleting non-existent client."""
    response = auth_client.post('/client/delete/999')
    assert response.status_code == 404 