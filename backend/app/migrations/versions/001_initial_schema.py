"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create images table
    op.create_table(
        'images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('storage_url', sa.Text(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_status', sa.String(20), server_default='pending'),
    )
    op.create_index('idx_images_processed_at', 'images', ['processed_at'])
    op.create_unique_constraint('uq_images_storage_key', 'images', ['storage_key'])
    
    # Create person_groups table
    op.create_table(
        'person_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('representative_face_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create faces table
    op.create_table(
        'faces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('image_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embedding', Vector(512), nullable=False),
        sa.Column('bounding_box', postgresql.JSON, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('person_group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_group_id'], ['person_groups.id'], ondelete='SET NULL'),
    )
    
    # Add foreign key constraint for representative_face_id after faces table is created
    op.create_foreign_key(
        'fk_person_groups_representative_face_id',
        'person_groups',
        'faces',
        ['representative_face_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create face_group_assignments table
    op.create_table(
        'face_group_assignments',
        sa.Column('face_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['face_id'], ['faces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_group_id'], ['person_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('face_id', 'person_group_id'),
    )
    
    # Create indexes
    op.create_index('idx_faces_image_id', 'faces', ['image_id'])
    op.create_index('idx_faces_person_group_id', 'faces', ['person_group_id'])
    
    # Create IVFFlat index for vector similarity search
    # Note: This requires at least some data. We'll create it after initial data is loaded.
    # For now, we'll create a regular index and the user can create IVFFlat later
    op.execute("""
        CREATE INDEX idx_faces_embedding ON faces 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)


def downgrade() -> None:
    op.drop_index('idx_faces_embedding', table_name='faces')
    op.drop_index('idx_faces_person_group_id', table_name='faces')
    op.drop_index('idx_faces_image_id', table_name='faces')
    op.drop_table('face_group_assignments')
    op.drop_table('faces')
    op.drop_table('person_groups')
    op.drop_index('idx_images_processed_at', table_name='images')
    op.drop_table('images')
    op.execute('DROP EXTENSION IF EXISTS vector')
