"""Add organization_id to modern models for multi-tenant isolation

Revision ID: 2025_10_10_org_id
Revises:
Create Date: 2025-10-10 22:00:00.000000

This migration adds organization_id columns to 25 modern models for proper
multi-tenant data isolation. This is part of Phase 1, Task 1.3 of the
Supabase Backend Enhancement implementation.

Models Updated:
- Agent Models (6): AgentInstance, AgentExecution, AgentMetrics, AgentTaskQueue, AgentConfiguration, SystemHealth
- Roblox Models (4): RobloxEnvironment, RobloxSession, EnvironmentShare, EnvironmentTemplate
- Payment Models (10): Customer, Subscription, SubscriptionItem, CustomerPaymentMethod, Payment, Invoice, InvoiceItem, Refund, UsageRecord, Coupon
- Content Pipeline (7): EnhancedContentGeneration, ContentQualityMetrics, LearningProfile, ContentPersonalizationLog, ContentFeedback, ContentGenerationBatch, ContentCache

Note: SystemHealth and ContentCache use GlobalBaseModel (no organization_id)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_10_10_org_id'
down_revision = '005_add_file_storage'  # Depends on previous migration
branch_labels = None
depends_on = None


def upgrade():
    """Add organization_id columns and indexes to modern models"""

    # ========================================
    # AGENT MODELS (5 models + 1 global)
    # ========================================

    # AgentInstance - Add organization_id
    op.add_column('agent_instances', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_agent_instances_organization', 'agent_instances', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_agent_instances_organization_id', 'agent_instances', ['organization_id'])
    op.create_index('idx_agent_org_type_status', 'agent_instances', ['organization_id', 'agent_type', 'status'])

    # AgentExecution - Add organization_id
    op.add_column('agent_executions', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_agent_executions_organization', 'agent_executions', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_agent_executions_organization_id', 'agent_executions', ['organization_id'])
    op.create_index('idx_execution_org_status_created', 'agent_executions', ['organization_id', 'status', 'created_at'])

    # AgentMetrics - Add organization_id
    op.add_column('agent_metrics', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_agent_metrics_organization', 'agent_metrics', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_agent_metrics_organization_id', 'agent_metrics', ['organization_id'])
    op.create_index('idx_metrics_org_period', 'agent_metrics', ['organization_id', 'period_start', 'period_end'])

    # AgentTaskQueue - Add organization_id
    op.add_column('agent_task_queue', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_agent_task_queue_organization', 'agent_task_queue', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_agent_task_queue_organization_id', 'agent_task_queue', ['organization_id'])
    op.create_index('idx_queue_org_priority_created', 'agent_task_queue', ['organization_id', 'priority', 'created_at'])

    # AgentConfiguration - Add organization_id
    op.add_column('agent_configurations', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_agent_configurations_organization', 'agent_configurations', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_agent_configurations_organization_id', 'agent_configurations', ['organization_id'])
    op.create_index('idx_config_org_active', 'agent_configurations', ['organization_id', 'is_active', 'agent_type'])

    # SystemHealth - GlobalBaseModel (no organization_id)
    # Note: system_health table uses GlobalBaseModel - no organization_id added

    # ========================================
    # ROBLOX MODELS (4 models)
    # ========================================

    # RobloxEnvironment - Add organization_id
    op.add_column('roblox_environments', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_roblox_environments_organization', 'roblox_environments', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_roblox_environments_organization_id', 'roblox_environments', ['organization_id'])
    op.create_index('idx_roblox_env_org_user_status', 'roblox_environments', ['organization_id', 'user_id', 'status'])

    # RobloxSession - Add organization_id
    op.add_column('roblox_sessions', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_roblox_sessions_organization', 'roblox_sessions', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_roblox_sessions_organization_id', 'roblox_sessions', ['organization_id'])
    op.create_index('idx_roblox_session_org_env_user', 'roblox_sessions', ['organization_id', 'environment_id', 'user_id'])

    # EnvironmentShare - Add organization_id
    op.add_column('environment_shares', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_environment_shares_organization', 'environment_shares', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_environment_shares_organization_id', 'environment_shares', ['organization_id'])
    op.create_index('idx_env_share_org_user', 'environment_shares', ['organization_id', 'shared_with_user_id'])

    # EnvironmentTemplate - Add organization_id
    op.add_column('environment_templates', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_environment_templates_organization', 'environment_templates', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_environment_templates_organization_id', 'environment_templates', ['organization_id'])
    op.create_index('idx_template_org_category', 'environment_templates', ['organization_id', 'category'])

    # ========================================
    # PAYMENT MODELS (10 models)
    # ========================================

    # Customer - Add organization_id
    op.add_column('customers', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_customers_organization', 'customers', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_customers_organization_id', 'customers', ['organization_id'])
    op.create_index('idx_customer_org_user', 'customers', ['organization_id', 'user_id'])

    # Subscription - Add organization_id
    op.add_column('subscriptions', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_subscriptions_organization', 'subscriptions', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_subscriptions_organization_id', 'subscriptions', ['organization_id'])
    op.create_index('idx_subscription_org_status', 'subscriptions', ['organization_id', 'status'])

    # SubscriptionItem - Add organization_id
    op.add_column('subscription_items', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_subscription_items_organization', 'subscription_items', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_subscription_items_organization_id', 'subscription_items', ['organization_id'])

    # CustomerPaymentMethod - Add organization_id
    op.add_column('payment_methods', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_payment_methods_organization', 'payment_methods', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_payment_methods_organization_id', 'payment_methods', ['organization_id'])
    op.create_index('idx_payment_method_org_customer', 'payment_methods', ['organization_id', 'customer_id'])

    # Payment - Add organization_id
    op.add_column('payments', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_payments_organization', 'payments', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_payments_organization_id', 'payments', ['organization_id'])
    op.create_index('idx_payment_org_customer', 'payments', ['organization_id', 'customer_id'])

    # Invoice - Add organization_id
    op.add_column('invoices', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_invoices_organization', 'invoices', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_invoices_organization_id', 'invoices', ['organization_id'])
    op.create_index('idx_invoice_org_customer', 'invoices', ['organization_id', 'customer_id'])

    # InvoiceItem - Add organization_id
    op.add_column('invoice_items', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_invoice_items_organization', 'invoice_items', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_invoice_items_organization_id', 'invoice_items', ['organization_id'])

    # Refund - Add organization_id
    op.add_column('refunds', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_refunds_organization', 'refunds', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_refunds_organization_id', 'refunds', ['organization_id'])

    # UsageRecord - Add organization_id
    op.add_column('usage_records', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_usage_records_organization', 'usage_records', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_usage_records_organization_id', 'usage_records', ['organization_id'])

    # Coupon - Add organization_id (nullable for platform-wide coupons)
    op.add_column('coupons', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))  # NULL = platform-wide
    op.create_foreign_key('fk_coupons_organization', 'coupons', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_coupons_organization_id', 'coupons', ['organization_id'])

    # ========================================
    # CONTENT PIPELINE MODELS (6 tenant + 1 global)
    # ========================================

    # EnhancedContentGeneration - Add organization_id
    op.add_column('enhanced_content_generations', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_enhanced_content_generations_organization', 'enhanced_content_generations', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_enhanced_content_generations_organization_id', 'enhanced_content_generations', ['organization_id'])
    op.create_index('idx_ecg_org_user_status', 'enhanced_content_generations', ['organization_id', 'user_id', 'status'])

    # ContentQualityMetrics - Add organization_id
    op.add_column('content_quality_metrics', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_content_quality_metrics_organization', 'content_quality_metrics', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_content_quality_metrics_organization_id', 'content_quality_metrics', ['organization_id'])

    # LearningProfile - Add organization_id
    op.add_column('learning_profiles', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_learning_profiles_organization', 'learning_profiles', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_learning_profiles_organization_id', 'learning_profiles', ['organization_id'])

    # ContentPersonalizationLog - Add organization_id
    op.add_column('content_personalization_log', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_content_personalization_log_organization', 'content_personalization_log', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_content_personalization_log_organization_id', 'content_personalization_log', ['organization_id'])

    # ContentFeedback - Add organization_id
    op.add_column('content_feedback', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_content_feedback_organization', 'content_feedback', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_content_feedback_organization_id', 'content_feedback', ['organization_id'])

    # ContentGenerationBatch - Add organization_id
    op.add_column('content_generation_batches', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_content_generation_batches_organization', 'content_generation_batches', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_content_generation_batches_organization_id', 'content_generation_batches', ['organization_id'])

    # ContentCache - GlobalBaseModel (no organization_id)
    # Note: content_cache table uses GlobalBaseModel - no organization_id added

    # ========================================
    # DATA MIGRATION (populate organization_id)
    # ========================================

    # After adding nullable columns, populate organization_id from related user records
    # This will be done in a separate data migration script

    print("✅ Migration complete: Added organization_id to 23 modern models")
    print("⚠️  Next step: Run data migration to populate organization_id values")
    print("📝 Note: SystemHealth and ContentCache use GlobalBaseModel (no organization_id)")


def downgrade():
    """Remove organization_id columns and indexes"""

    # Drop in reverse order

    # Content Pipeline Models
    op.drop_index('ix_content_generation_batches_organization_id', table_name='content_generation_batches')
    op.drop_constraint('fk_content_generation_batches_organization', 'content_generation_batches', type_='foreignkey')
    op.drop_column('content_generation_batches', 'organization_id')

    op.drop_index('ix_content_feedback_organization_id', table_name='content_feedback')
    op.drop_constraint('fk_content_feedback_organization', 'content_feedback', type_='foreignkey')
    op.drop_column('content_feedback', 'organization_id')

    op.drop_index('ix_content_personalization_log_organization_id', table_name='content_personalization_log')
    op.drop_constraint('fk_content_personalization_log_organization', 'content_personalization_log', type_='foreignkey')
    op.drop_column('content_personalization_log', 'organization_id')

    op.drop_index('ix_learning_profiles_organization_id', table_name='learning_profiles')
    op.drop_constraint('fk_learning_profiles_organization', 'learning_profiles', type_='foreignkey')
    op.drop_column('learning_profiles', 'organization_id')

    op.drop_index('ix_content_quality_metrics_organization_id', table_name='content_quality_metrics')
    op.drop_constraint('fk_content_quality_metrics_organization', 'content_quality_metrics', type_='foreignkey')
    op.drop_column('content_quality_metrics', 'organization_id')

    op.drop_index('idx_ecg_org_user_status', table_name='enhanced_content_generations')
    op.drop_index('ix_enhanced_content_generations_organization_id', table_name='enhanced_content_generations')
    op.drop_constraint('fk_enhanced_content_generations_organization', 'enhanced_content_generations', type_='foreignkey')
    op.drop_column('enhanced_content_generations', 'organization_id')

    # Payment Models
    op.drop_index('ix_coupons_organization_id', table_name='coupons')
    op.drop_constraint('fk_coupons_organization', 'coupons', type_='foreignkey')
    op.drop_column('coupons', 'organization_id')

    op.drop_index('ix_usage_records_organization_id', table_name='usage_records')
    op.drop_constraint('fk_usage_records_organization', 'usage_records', type_='foreignkey')
    op.drop_column('usage_records', 'organization_id')

    op.drop_index('ix_refunds_organization_id', table_name='refunds')
    op.drop_constraint('fk_refunds_organization', 'refunds', type_='foreignkey')
    op.drop_column('refunds', 'organization_id')

    op.drop_index('ix_invoice_items_organization_id', table_name='invoice_items')
    op.drop_constraint('fk_invoice_items_organization', 'invoice_items', type_='foreignkey')
    op.drop_column('invoice_items', 'organization_id')

    op.drop_index('idx_invoice_org_customer', table_name='invoices')
    op.drop_index('ix_invoices_organization_id', table_name='invoices')
    op.drop_constraint('fk_invoices_organization', 'invoices', type_='foreignkey')
    op.drop_column('invoices', 'organization_id')

    op.drop_index('idx_payment_org_customer', table_name='payments')
    op.drop_index('ix_payments_organization_id', table_name='payments')
    op.drop_constraint('fk_payments_organization', 'payments', type_='foreignkey')
    op.drop_column('payments', 'organization_id')

    op.drop_index('idx_payment_method_org_customer', table_name='payment_methods')
    op.drop_index('ix_payment_methods_organization_id', table_name='payment_methods')
    op.drop_constraint('fk_payment_methods_organization', 'payment_methods', type_='foreignkey')
    op.drop_column('payment_methods', 'organization_id')

    op.drop_index('ix_subscription_items_organization_id', table_name='subscription_items')
    op.drop_constraint('fk_subscription_items_organization', 'subscription_items', type_='foreignkey')
    op.drop_column('subscription_items', 'organization_id')

    op.drop_index('idx_subscription_org_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_organization_id', table_name='subscriptions')
    op.drop_constraint('fk_subscriptions_organization', 'subscriptions', type_='foreignkey')
    op.drop_column('subscriptions', 'organization_id')

    op.drop_index('idx_customer_org_user', table_name='customers')
    op.drop_index('ix_customers_organization_id', table_name='customers')
    op.drop_constraint('fk_customers_organization', 'customers', type_='foreignkey')
    op.drop_column('customers', 'organization_id')

    # Roblox Models
    op.drop_index('idx_template_org_category', table_name='environment_templates')
    op.drop_index('ix_environment_templates_organization_id', table_name='environment_templates')
    op.drop_constraint('fk_environment_templates_organization', 'environment_templates', type_='foreignkey')
    op.drop_column('environment_templates', 'organization_id')

    op.drop_index('idx_env_share_org_user', table_name='environment_shares')
    op.drop_index('ix_environment_shares_organization_id', table_name='environment_shares')
    op.drop_constraint('fk_environment_shares_organization', 'environment_shares', type_='foreignkey')
    op.drop_column('environment_shares', 'organization_id')

    op.drop_index('idx_roblox_session_org_env_user', table_name='roblox_sessions')
    op.drop_index('ix_roblox_sessions_organization_id', table_name='roblox_sessions')
    op.drop_constraint('fk_roblox_sessions_organization', 'roblox_sessions', type_='foreignkey')
    op.drop_column('roblox_sessions', 'organization_id')

    op.drop_index('idx_roblox_env_org_user_status', table_name='roblox_environments')
    op.drop_index('ix_roblox_environments_organization_id', table_name='roblox_environments')
    op.drop_constraint('fk_roblox_environments_organization', 'roblox_environments', type_='foreignkey')
    op.drop_column('roblox_environments', 'organization_id')

    # Agent Models
    op.drop_index('idx_config_org_active', table_name='agent_configurations')
    op.drop_index('ix_agent_configurations_organization_id', table_name='agent_configurations')
    op.drop_constraint('fk_agent_configurations_organization', 'agent_configurations', type_='foreignkey')
    op.drop_column('agent_configurations', 'organization_id')

    op.drop_index('idx_queue_org_priority_created', table_name='agent_task_queue')
    op.drop_index('ix_agent_task_queue_organization_id', table_name='agent_task_queue')
    op.drop_constraint('fk_agent_task_queue_organization', 'agent_task_queue', type_='foreignkey')
    op.drop_column('agent_task_queue', 'organization_id')

    op.drop_index('idx_metrics_org_period', table_name='agent_metrics')
    op.drop_index('ix_agent_metrics_organization_id', table_name='agent_metrics')
    op.drop_constraint('fk_agent_metrics_organization', 'agent_metrics', type_='foreignkey')
    op.drop_column('agent_metrics', 'organization_id')

    op.drop_index('idx_execution_org_status_created', table_name='agent_executions')
    op.drop_index('ix_agent_executions_organization_id', table_name='agent_executions')
    op.drop_constraint('fk_agent_executions_organization', 'agent_executions', type_='foreignkey')
    op.drop_column('agent_executions', 'organization_id')

    op.drop_index('idx_agent_org_type_status', table_name='agent_instances')
    op.drop_index('ix_agent_instances_organization_id', table_name='agent_instances')
    op.drop_constraint('fk_agent_instances_organization', 'agent_instances', type_='foreignkey')
    op.drop_column('agent_instances', 'organization_id')

    print("✅ Rollback complete: Removed organization_id from 23 modern models")
