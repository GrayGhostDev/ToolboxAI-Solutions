"""Add classes table

Revision ID: b6d899aab2fb
Revises: 002
Create Date: 2025-09-19 15:25:52.772699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b6d899aab2fb'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create classes table and enrollment relationship."""

    # Create classes table
    op.create_table('classes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(100), nullable=False),
        sa.Column('room', sa.String(100)),
        sa.Column('schedule', sa.String(200)),
        sa.Column('description', sa.Text()),
        sa.Column('start_time', sa.DateTime(timezone=True)),
        sa.Column('end_time', sa.DateTime(timezone=True)),
        sa.Column('max_students', sa.Integer(), server_default='30'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['teacher_id'], ['toolboxai.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('grade_level >= 1 AND grade_level <= 12'),
        sa.CheckConstraint('max_students > 0'),
        schema='toolboxai'
    )

    # Create class_enrollments table
    op.create_table('class_enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('dropped_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('final_grade', sa.Float()),
        sa.Column('attendance_percentage', sa.Float()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['class_id'], ['toolboxai.classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['toolboxai.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'student_id'),
        sa.CheckConstraint('attendance_percentage >= 0 AND attendance_percentage <= 100'),
        schema='toolboxai'
    )

    # Create indexes
    op.create_index('idx_class_teacher', 'classes', ['teacher_id'], schema='toolboxai')
    op.create_index('idx_class_subject_grade', 'classes', ['subject', 'grade_level'], schema='toolboxai')
    op.create_index('idx_class_active', 'classes', ['is_active'], schema='toolboxai')
    op.create_index('idx_enrollment_class', 'class_enrollments', ['class_id'], schema='toolboxai')
    op.create_index('idx_enrollment_student', 'class_enrollments', ['student_id'], schema='toolboxai')
    op.create_index('idx_enrollment_status', 'class_enrollments', ['status'], schema='toolboxai')

    # Create update trigger for classes table
    op.execute("""
        CREATE TRIGGER update_classes_updated_at
        BEFORE UPDATE ON toolboxai.classes
        FOR EACH ROW EXECUTE FUNCTION toolboxai.update_updated_at_column();
    """)

    # Create update trigger for class_enrollments table
    op.execute("""
        CREATE TRIGGER update_class_enrollments_updated_at
        BEFORE UPDATE ON toolboxai.class_enrollments
        FOR EACH ROW EXECUTE FUNCTION toolboxai.update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop classes table and related objects."""

    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_classes_updated_at ON toolboxai.classes')
    op.execute('DROP TRIGGER IF EXISTS update_class_enrollments_updated_at ON toolboxai.class_enrollments')

    # Drop indexes
    op.drop_index('idx_enrollment_status', 'class_enrollments', schema='toolboxai')
    op.drop_index('idx_enrollment_student', 'class_enrollments', schema='toolboxai')
    op.drop_index('idx_enrollment_class', 'class_enrollments', schema='toolboxai')
    op.drop_index('idx_class_active', 'classes', schema='toolboxai')
    op.drop_index('idx_class_subject_grade', 'classes', schema='toolboxai')
    op.drop_index('idx_class_teacher', 'classes', schema='toolboxai')

    # Drop tables
    op.drop_table('class_enrollments', schema='toolboxai')
    op.drop_table('classes', schema='toolboxai')
