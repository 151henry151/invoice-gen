from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Business(db.Model):
    __tablename__ = 'business'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    logo_path = db.Column(db.String(200))
    invoice_template = db.Column(db.String(100), default='invoice_pretty')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='businesses')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'email': self.email,
            'phone': self.phone,
            'logo_path': self.logo_path,
            'invoice_template': self.invoice_template
        }

class Client(db.Model):
    __tablename__ = 'client'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='clients')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'email': self.email,
            'phone': self.phone
        }

class SalesTax(db.Model):
    __tablename__ = 'sales_tax'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='sales_taxes')
    invoices = db.relationship('Invoice', backref='sales_tax', lazy=True)
    
    def __repr__(self):
        return f'<SalesTax {self.description} ({self.rate}%)>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'rate': self.rate,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Invoice(db.Model):
    __tablename__ = 'invoice'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    sales_tax_id = db.Column(db.Integer, db.ForeignKey('sales_tax.id'), nullable=True)
    tax_applies_to = db.Column(db.String(20), nullable=True)  # 'items', 'labor', or 'both'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    business = db.relationship('Business', backref='invoices')
    client = db.relationship('Client', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')
    labor_items = db.relationship('InvoiceLabor', backref='invoice', cascade='all, delete-orphan')
    user = db.relationship('User', backref='invoices')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def to_dict(self):
        try:
            # Calculate subtotal from items and labor
            items_subtotal = sum(float(item.total) for item in self.items)
            labor_subtotal = sum(float(item.total) for item in self.labor_items)
            subtotal = items_subtotal + labor_subtotal
            
            # Calculate tax amount
            tax_amount = 0
            if self.sales_tax:
                if self.tax_applies_to == 'items':
                    taxable_amount = items_subtotal
                elif self.tax_applies_to == 'labor':
                    taxable_amount = labor_subtotal
                else:  # 'both'
                    taxable_amount = subtotal
                tax_amount = round(taxable_amount * (float(self.sales_tax.rate) / 100), 2)
            
            # Calculate total
            total = round(subtotal + tax_amount, 2)
            
            return {
                'id': self.id,
                'invoice_number': self.invoice_number,
                'date': self.date.isoformat() if self.date else None,
                'due_date': self.due_date.isoformat() if self.due_date else None,
                'status': self.status,
                'notes': self.notes,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'business': self.business.to_dict() if self.business else None,
                'client': self.client.to_dict() if self.client else None,
                'sales_tax': self.sales_tax.to_dict() if self.sales_tax else None,
                'tax_applies_to': self.tax_applies_to,
                'items': [item.to_dict() for item in self.items],
                'labor_items': [item.to_dict() for item in self.labor_items],
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'total': total
            }
        except Exception as e:
            print(f"Error in Invoice.to_dict(): {str(e)}")
            raise

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_item'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InvoiceItem {self.description}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total': float(self.total),
            'date': self.date.isoformat() if self.date else None
        }

class InvoiceLabor(db.Model):
    __tablename__ = 'invoice_labor'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InvoiceLabor {self.description}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'hours': float(self.hours),
            'rate': float(self.rate),
            'total': float(self.total),
            'date': self.date.isoformat() if self.date else None
        }

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='settings')
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='items')
    
    def __repr__(self):
        return f'<Item {self.description}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class LaborItem(db.Model):
    __tablename__ = 'labor_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='labor_items')
    
    def __repr__(self):
        return f'<LaborItem {self.description}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'description': self.description,
            'hours': self.hours,
            'rate': self.rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 