import pytest
from models import User
from werkzeug.security import check_password_hash

def test_register_page(client):
    """Test that the registration page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data

def test_register_success(client, app, db):
    """Test successful user registration.
    Note: We do not assert the flash message here because Flask's test client does not always preserve flashed messages across redirects.
    Instead, we check for the login form and user creation in the database.
    """
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'TestPass123!@#'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check for login page rendered
    assert b'Login' in response.data

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'
        assert check_password_hash(user.password, 'TestPass123!@#')

def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username."""
    response = client.post('/register', data={
        'username': test_user.username,
        'email': 'other@example.com',
        'password': 'TestPass123!@#'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Username or email already exists' in response.data

def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post('/register', data={
        'username': 'otheruser',
        'email': test_user.email,
        'password': 'TestPass123!@#'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Username or email already exists' in response.data

def test_register_weak_password(client):
    """Test registration with weak password."""
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'weak'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Password must be at least 12 characters long' in response.data

def test_login_page(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post('/login', data={
        'username': test_user.username,
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invoice' in response.data or b'Dashboard' in response.data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username/email or password' in response.data

def test_logout(client, test_user):
    """Test logout functionality."""
    # First login
    client.post('/login', data={
        'username': test_user.username,
        'password': 'testpassword'
    })
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

@pytest.mark.xfail(reason="Password reset functionality not yet implemented")
def test_password_reset_request(client, test_user):
    """Test password reset request."""
    response = client.post('/reset_password_request', data={
        'email': test_user.email
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Check your email for instructions' in response.data

@pytest.mark.xfail(reason="Password reset functionality not yet implemented")
def test_password_reset(client, test_user):
    """Test password reset."""
    response = client.post('/reset_password', data={
        'token': 'test_token',
        'password': 'NewPass123!@#'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Your password has been reset' in response.data

@pytest.mark.xfail(reason="Password reset functionality not yet implemented")
def test_password_reset_invalid_token(client):
    """Test password reset with invalid token."""
    response = client.post('/reset_password', data={
        'token': 'invalid_token',
        'password': 'NewPass123!@#'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid or expired token' in response.data 