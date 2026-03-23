import os
import json
from datetime import datetime, timedelta
from faker import Faker
from app_factory import create_app
from models import User, Client, Business, Item, LaborItem, SalesTax, Invoice, InvoiceItem, InvoiceLabor
from werkzeug.security import generate_password_hash
from PIL import Image, ImageDraw, ImageFont
import random
import time

fake = Faker()

TEST_USERNAME = "testuser"
TEST_PASSWORD = "TestPass123!@#"
TEST_EMAIL = "test@example.com"

def clear_test_data():
    """Clear all existing test data."""
    app = create_app()
    with app.app_context():
        from app_factory import db
        
        # Delete all test data in reverse order of dependencies
        InvoiceLabor.query.delete()
        InvoiceItem.query.delete()
        Invoice.query.delete()
        SalesTax.query.delete()
        LaborItem.query.delete()
        Item.query.delete()
        Client.query.delete()
        Business.query.delete()
        
        # Delete test user if exists
        test_user = User.query.filter_by(username=TEST_USERNAME).first()
        if test_user:
            db.session.delete(test_user)
        
        db.session.commit()

def generate_profile_picture(username, user_id, size=(200, 200)):
    """Generate a simple profile picture with initials."""
    # Create a new image with a random background color
    bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Get initials from username
    initials = ''.join(word[0].upper() for word in username.split('_')[0].split())
    
    # Draw a circle in the center
    circle_color = (255, 255, 255)
    circle_radius = min(size) // 2 - 10
    circle_center = (size[0] // 2, size[1] // 2)
    draw.ellipse(
        [
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius
        ],
        fill=circle_color
    )
    
    # Draw initials in the circle
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=circle_radius)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = (
        circle_center[0] - text_width // 2,
        circle_center[1] - text_height // 2
    )
    
    draw.text(text_position, initials, fill=(0, 0, 0), font=font)
    
    # Save the image
    os.makedirs('uploads', exist_ok=True)
    timestamp = int(time.time())
    filename = f"profile_{user_id}_{timestamp}_profile.png"
    img.save(os.path.join('uploads', filename))
    return filename

def generate_business_logo(business_name, size=(400, 200)):
    """Generate a simple business logo."""
    # Create a new image with a random background color
    bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a rectangle in the center
    rect_color = (255, 255, 255)
    rect_width = size[0] - 40
    rect_height = size[1] - 40
    rect_position = (20, 20)
    draw.rectangle(
        [
            rect_position[0],
            rect_position[1],
            rect_position[0] + rect_width,
            rect_position[1] + rect_height
        ],
        fill=rect_color
    )
    
    # Draw business name
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=40)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position to center it
    text_bbox = draw.textbbox((0, 0), business_name, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = (
        (size[0] - text_width) // 2,
        (size[1] - text_height) // 2
    )
    
    draw.text(text_position, business_name, fill=(0, 0, 0), font=font)
    
    # Save the image
    os.makedirs('uploads', exist_ok=True)
    timestamp = int(time.time())
    filename = f"{timestamp}_{business_name.replace(' ', '_')}.png"
    img.save(os.path.join('uploads', filename))
    return filename

def create_test_data():
    """Create a comprehensive set of test data for manual testing."""
    print("Starting test data creation...")
    
    app = create_app()
    with app.app_context():
        from app_factory import db  # Import db here to ensure it's within app context
        
        # Clear existing test data
        clear_test_data()
        
        # Create test user with consistent credentials
        test_user = User(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=generate_password_hash(TEST_PASSWORD)
        )
        db.session.add(test_user)
        db.session.flush()  # Get the user ID before committing
        
        # Generate profile picture after we have the user ID
        test_user.profile_picture = generate_profile_picture(TEST_USERNAME, test_user.id)
        db.session.commit()
        print(f"Created test user: {test_user.username} (password: {TEST_PASSWORD})")
        
        # Create test businesses with logos
        businesses = []
        for i in range(3):
            business_name = fake.company()
            business = Business(
                name=business_name,
                address=fake.address(),
                phone=fake.phone_number(),
                email=fake.email(),
                user_id=test_user.id,
                logo_path=generate_business_logo(business_name)
            )
            db.session.add(business)
            businesses.append(business)
        db.session.commit()
        print(f"Created {len(businesses)} test businesses")
        
        # Create test clients
        clients = []
        for i in range(5):
            client = Client(
                name=fake.company(),
                address=fake.address(),
                phone=fake.phone_number(),
                email=fake.email(),
                user_id=test_user.id
            )
            db.session.add(client)
            clients.append(client)
        db.session.commit()
        print(f"Created {len(clients)} test clients")
        
        # Create test items with realistic descriptions
        item_descriptions = [
            '4x8 Sheets of 3/4" Plywood',
            'Cleaning Supplies',
            'Paint (1 Gallon)',
            'Box of Nails (1000 ct)',
            'LED Light Bulb (Pack of 4)',
            'HVAC Air Filter',
            'Office Chair',
            'Desk Lamp',
            'Extension Cord (25 ft)',
            'Printer Paper (500 sheets)'
        ]
        items = []
        for desc in item_descriptions:
            item = Item(
                description=desc,
                quantity=1,
                unit_price=round(random.uniform(5, 120), 2),
                user_id=test_user.id
            )
            db.session.add(item)
            items.append(item)
        db.session.commit()
        print(f"Created {len(items)} test items")

        # Create test labor items with realistic names
        labor_names = [
            'Carpentry',
            'Plumbing',
            'Cleaning Services',
            'Electrical Work',
            'Landscaping',
            'Painting',
            'HVAC Maintenance',
            'IT Support',
            'Window Installation',
            'Roof Repair'
        ]
        labor_items = []
        for name in labor_names:
            labor = LaborItem(
                description=name,
                hours=1.0,  # Set default hours for test data
                rate=round(random.uniform(25, 120), 2),
                user_id=test_user.id
            )
            db.session.add(labor)
            labor_items.append(labor)
        db.session.commit()
        print(f"Created {len(labor_items)} test labor items")

        # Create test sales tax rates with realistic names and values
        tax_rates = [
            ('VT State Tax', 6.0),
            ('NY State Tax', 8.875),
            ('Local Sales Tax', 2.0),
            ('MA State Tax', 6.25),
            ('NH No Sales Tax', 0.0)
        ]
        sales_taxes = []
        for name, rate in tax_rates:
            tax = SalesTax(
                description=name,
                rate=rate,
                user_id=test_user.id
            )
            db.session.add(tax)
            sales_taxes.append(tax)
        db.session.commit()
        print(f"Created {len(sales_taxes)} test sales tax rates")
        
        # Create test invoices
        invoices = []
        for i in range(12):
            # Randomly select a business and client
            business = fake.random_element(businesses)
            client = fake.random_element(clients)
            
            # Create invoice
            invoice = Invoice(
                invoice_number=f"INV-{fake.random_number(digits=6)}",
                date=datetime.now() - timedelta(days=fake.random_number(digits=2)),
                due_date=datetime.now() + timedelta(days=30),
                notes=fake.paragraph(),
                status=fake.random_element(['draft', 'sent', 'paid']),
                business_id=business.id,
                client_id=client.id,
                user_id=test_user.id,
                tax_applies_to=fake.random_element(['items', 'labor', 'both'])
            )
            db.session.add(invoice)
            db.session.flush()  # Ensure invoice.id is set before adding items/labor
            
            # Add random number of items
            num_items = fake.random_int(min=1, max=5)
            for _ in range(num_items):
                if fake.boolean():
                    # Add regular item
                    item = fake.random_element(items)
                    quantity = fake.random_int(min=1, max=10)
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        description=item.description,
                        quantity=quantity,
                        unit_price=item.unit_price,
                        total=quantity * item.unit_price,
                        date=invoice.date
                    )
                    db.session.add(invoice_item)
                else:
                    # Add labor item
                    labor_item = fake.random_element(labor_items)
                    hours = fake.random_int(min=1, max=8)
                    invoice_labor = InvoiceLabor(
                        invoice_id=invoice.id,
                        description=labor_item.description,
                        hours=hours,
                        rate=labor_item.rate,
                        total=hours * labor_item.rate,
                        date=invoice.date
                    )
                    db.session.add(invoice_labor)
            
            # Add random tax rate
            tax_rate = fake.random_element(sales_taxes)
            invoice.sales_tax_id = tax_rate.id
            
            invoices.append(invoice)
        
        db.session.commit()
        print(f"Created {len(invoices)} test invoices")
        
        # Save test data summary
        test_data = {
            "user": {
                "username": test_user.username,
                "password": TEST_PASSWORD,
                "email": test_user.email
            },
            "businesses": [b.name for b in businesses],
            "clients": [c.name for c in clients],
            "items": [i.description for i in items],
            "labor_items": [li.description for li in labor_items],
            "tax_rates": [f"{tr.description} ({tr.rate}%)" for tr in sales_taxes],
            "invoices": [f"{inv.invoice_number} - {inv.status}" for inv in invoices]
        }
        
        with open("test_data_summary.json", "w") as f:
            json.dump(test_data, f, indent=2)
        
        print("\nTest data creation complete!")
        print("Test data summary saved to test_data_summary.json")
        print("\nYou can now log in with:")
        print(f"Username: {test_user.username}")
        print(f"Password: {TEST_PASSWORD}")

if __name__ == "__main__":
    create_test_data() 