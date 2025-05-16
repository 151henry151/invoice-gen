class SalesTax(db.Model):
    __tablename__ = 'sales_tax'
    
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='sales_tax', lazy=True)
    
    def __repr__(self):
        return f'<SalesTax {self.description} ({self.rate}%)>'
    
    def to_dict(self):
        return {
            'id': self.id,
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
    
    # Relationships
    business = db.relationship('Business', backref='invoices')
    client = db.relationship('Client', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')
    labor_items = db.relationship('InvoiceLabor', backref='invoice', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'date': self.date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'business': self.business.to_dict() if self.business else None,
            'client': self.client.to_dict() if self.client else None,
            'sales_tax': self.sales_tax.to_dict() if self.sales_tax else None,
            'tax_applies_to': self.tax_applies_to,
            'items': [item.to_dict() for item in self.items],
            'labor_items': [item.to_dict() for item in self.labor_items]
        } 