"""migrate settings to companies and add invoice_template column

Revision ID: migrate_settings_to_companies
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'migrate_settings_to_companies'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add invoice_template column to companies table
    op.add_column('business', sa.Column('invoice_template', sa.String(100), nullable=True, server_default='invoice_pretty'))
    
    # Create a connection and session
    connection = op.get_bind()
    session = Session(bind=connection)
    
    try:
        # Get all users
        users = session.execute('SELECT id FROM users').fetchall()
        
        for user in users:
            # Check if user already has a company
            existing_company = session.execute(
                'SELECT id FROM business WHERE user_id = :user_id',
                {'user_id': user[0]}
            ).fetchone()
            
            if existing_company:
                continue
            
            # Get user settings
            settings = session.execute(
                'SELECT key, value FROM settings WHERE user_id = :user_id',
                {'user_id': user[0]}
            ).fetchall()
            
            settings_dict = {s[0]: s[1] for s in settings}
            
            # Create new company
            session.execute(
                '''
                INSERT INTO business (user_id, name, address, email, phone, logo_path, created_at, updated_at)
                VALUES (:user_id, :name, :address, :email, :phone, :logo_path, :created_at, :updated_at)
                ''',
                {
                    'user_id': user[0],
                    'name': settings_dict.get('company_name', ''),
                    'address': settings_dict.get('company_address', ''),
                    'email': settings_dict.get('company_email', ''),
                    'phone': settings_dict.get('company_phone', ''),
                    'logo_path': settings_dict.get('logo_path', ''),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            )
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def downgrade():
    # Remove invoice_template column from companies table
    op.drop_column('business', 'invoice_template')
    
    # Note: We don't remove the companies created from settings as that would be destructive
    # and could cause data loss. If needed, this should be handled separately. 