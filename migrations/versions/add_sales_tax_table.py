"""add sales tax table

Revision ID: add_sales_tax_table
Revises: add_invoice_notes
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_sales_tax_table'
down_revision = 'add_invoice_notes'
branch_labels = None
depends_on = None

def upgrade():
    # Create sales_tax table
    op.create_table('sales_tax',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add sales_tax_id to invoice table
    op.add_column('invoice', sa.Column('sales_tax_id', sa.Integer(), nullable=True))
    op.add_column('invoice', sa.Column('tax_applies_to', sa.String(length=20), nullable=True))
    op.create_foreign_key('fk_invoice_sales_tax', 'invoice', 'sales_tax', ['sales_tax_id'], ['id'])

def downgrade():
    # Remove foreign key and columns from invoice table
    op.drop_constraint('fk_invoice_sales_tax', 'invoice', type_='foreignkey')
    op.drop_column('invoice', 'tax_applies_to')
    op.drop_column('invoice', 'sales_tax_id')
    
    # Drop sales_tax table
    op.drop_table('sales_tax') 