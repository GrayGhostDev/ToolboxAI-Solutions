"""Add educational content fields to content table

Revision ID: 002_add_educational_content_fields
Revises: 001_initial_schema
Create Date: 2025-09-14 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_educational_content_fields'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add educational fields to content table"""
    
    # Add new columns to content table
    op.add_column('content', 
        sa.Column('subject', sa.String(100), nullable=True)
    )
    op.add_column('content',
        sa.Column('grade_level', sa.Integer(), nullable=True)
    )
    op.add_column('content',
        sa.Column('difficulty', sa.String(20), nullable=True)
    )
    op.add_column('content',
        sa.Column('content_metadata', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, server_default='{}')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_content_subject_grade', 'content', ['subject', 'grade_level'])
    op.create_index('idx_content_difficulty', 'content', ['difficulty'])
    
    # Add check constraint for grade_level
    op.create_check_constraint(
        'ck_content_grade_level',
        'content',
        'grade_level >= 1 AND grade_level <= 12'
    )
    
    # Add check constraint for difficulty
    op.create_check_constraint(
        'ck_content_difficulty',
        'content',
        "difficulty IN ('beginner', 'intermediate', 'advanced', 'expert')"
    )
    
    # Update existing records with default values
    op.execute("""
        UPDATE content 
        SET content_metadata = '{}'::jsonb 
        WHERE content_metadata IS NULL
    """)
    
    # Try to populate subject and grade_level from related lesson/course
    op.execute("""
        UPDATE content c
        SET subject = co.subject,
            grade_level = co.grade_level
        FROM lessons l
        JOIN courses co ON l.course_id = co.id
        WHERE c.lesson_id = l.id
        AND c.subject IS NULL
    """)
    
    # Set default difficulty based on lesson difficulty if available
    op.execute("""
        UPDATE content c
        SET difficulty = 
            CASE 
                WHEN l.difficulty = 0 THEN 'beginner'
                WHEN l.difficulty = 1 THEN 'intermediate'
                WHEN l.difficulty = 2 THEN 'advanced'
                WHEN l.difficulty = 3 THEN 'expert'
                ELSE 'intermediate'
            END
        FROM lessons l
        WHERE c.lesson_id = l.id
        AND c.difficulty IS NULL
    """)


def downgrade():
    """Remove educational fields from content table"""
    
    # Drop check constraints
    op.drop_constraint('ck_content_difficulty', 'content', type_='check')
    op.drop_constraint('ck_content_grade_level', 'content', type_='check')
    
    # Drop indexes
    op.drop_index('idx_content_difficulty', table_name='content')
    op.drop_index('idx_content_subject_grade', table_name='content')
    
    # Drop columns
    op.drop_column('content', 'metadata')
    op.drop_column('content', 'difficulty')
    op.drop_column('content', 'grade_level')
    op.drop_column('content', 'subject')