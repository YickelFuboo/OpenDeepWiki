"""Add app config models

Revision ID: 001
Revises: 
Create Date: 2024-07-29 21:36:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    # 创建应用配置表
    op.create_table('app_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('app_id', sa.String(length=100), nullable=False, unique=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('organization_name', sa.String(length=100), nullable=True),
        sa.Column('repository_name', sa.String(length=100), nullable=True),
        sa.Column('allowed_domains_json', sa.Text(), nullable=True),
        sa.Column('enable_domain_validation', sa.Boolean(), nullable=False, default=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('introduction', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=50), nullable=True),
        sa.Column('recommended_questions_json', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建应用配置MCP表
    op.create_table('app_config_mcps',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('app_config_id', sa.String(length=36), nullable=False),
        sa.Column('mcp_server_name', sa.String(length=100), nullable=False),
        sa.Column('mcp_server_url', sa.String(length=500), nullable=False),
        sa.Column('mcp_server_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('app_config_mcps')
    op.drop_table('app_configs') 