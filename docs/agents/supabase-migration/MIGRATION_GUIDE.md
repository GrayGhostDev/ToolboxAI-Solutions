# ToolBoxAI Supabase Migration Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Migration Planning](#pre-migration-planning)
3. [Step-by-Step Migration Process](#step-by-step-migration-process)
4. [Common Migration Scenarios](#common-migration-scenarios)
5. [Troubleshooting](#troubleshooting)
6. [Post-Migration Tasks](#post-migration-tasks)
7. [Best Practices](#best-practices)

## Prerequisites

### System Requirements

#### Software Dependencies
- **Python**: 3.9 or higher
- **PostgreSQL Client**: psql 12+ for source database access
- **Node.js**: 16+ (for TypeScript type generation)
- **Git**: For version control of migration scripts

#### Python Dependencies
```bash
pip install -r requirements.txt

# Core dependencies:
# - asyncpg >= 0.27.0
# - sqlalchemy >= 1.4.0
# - supabase >= 1.0.0
# - langchain >= 0.0.350
# - pydantic >= 2.0.0
```

#### Database Access Requirements

**Source PostgreSQL Database:**
```sql
-- Create migration user with appropriate permissions
CREATE USER migration_user WITH PASSWORD 'secure_password';

-- Grant schema access
GRANT USAGE ON SCHEMA information_schema TO migration_user;
GRANT USAGE ON SCHEMA pg_catalog TO migration_user;
GRANT USAGE ON SCHEMA public TO migration_user;

-- Grant read access to all tables
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO migration_user;
GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO migration_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO migration_user;

-- Grant access to sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO migration_user;

-- For data export (if needed)
GRANT CONNECT ON DATABASE your_database TO migration_user;
```

**Target Supabase Project:**
- Supabase project URL
- Service role key (for admin operations)
- Database password
- Sufficient storage quota for data volume

### Environment Setup

#### Environment Variables
Create a `.env` file with the following configuration:

```bash
# Source Database Configuration
SOURCE_DATABASE_URL=postgresql://migration_user:password@localhost:5432/source_db
SOURCE_DATABASE_NAME=your_app_production

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_DB_PASSWORD=your_db_password

# Migration Configuration
MIGRATION_BATCH_SIZE=1000
MIGRATION_PARALLEL_WORKERS=4
MIGRATION_TIMEOUT_SECONDS=3600
ENABLE_DRY_RUN=true

# AI Configuration (Optional)
OPENAI_API_KEY=your_openai_key
USE_MOCK_LLM=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=migration.log
ENABLE_DETAILED_LOGGING=true
```

#### Directory Structure
```
migration-workspace/
├── .env                    # Environment configuration
├── migration_config.yaml  # Migration-specific settings
├── backups/               # Database backups
├── logs/                  # Migration logs
├── scripts/               # Generated migration scripts
├── validation/            # Validation test results
└── rollback/              # Rollback procedures
```

## Pre-Migration Planning

### 1. Database Assessment

#### Compatibility Check
Run the compatibility assessment tool:

```python
from core.agents.supabase import SupabaseMigrationAgent

agent = SupabaseMigrationAgent()

# Perform initial assessment
assessment = await agent.assess_compatibility(
    connection_string=SOURCE_DATABASE_URL,
    target_platform="supabase"
)

print(f"Compatibility Score: {assessment['score']}/100")
print(f"Blockers: {assessment['blockers']}")
print(f"Warnings: {assessment['warnings']}")
```

#### Data Inventory
Create an inventory of your data:

```bash
# Generate database statistics
python scripts/generate_inventory.py --source $SOURCE_DATABASE_URL --output inventory.json

# Example output structure:
{
    "tables": {
        "users": {
            "row_count": 10000,
            "size_mb": 15.2,
            "has_sensitive_data": true,
            "dependent_tables": ["profiles", "sessions"]
        }
    },
    "total_size_gb": 2.5,
    "estimated_migration_time": "4-6 hours"
}
```

### 2. Migration Strategy Selection

Choose the appropriate migration strategy based on your requirements:

#### Strategy 1: Big Bang Migration
**Best for:**
- Small to medium databases (< 1GB)
- Applications that can tolerate downtime
- Simple schema structures

**Timeline:** 2-8 hours
**Downtime:** Full downtime during migration

#### Strategy 2: Phased Migration
**Best for:**
- Large databases (> 1GB)
- Complex schema with many dependencies
- Applications requiring minimal downtime

**Timeline:** 1-2 weeks
**Downtime:** Minimal (cutover period only)

#### Strategy 3: Blue-Green Migration
**Best for:**
- Mission-critical applications
- Zero-downtime requirements
- Applications with read-heavy workloads

**Timeline:** 2-3 weeks
**Downtime:** Near-zero (DNS switch only)

### 3. Risk Assessment

#### Identify High-Risk Elements
```python
# Automated risk assessment
risk_assessment = await agent.assess_migration_risks(
    analysis_results=analysis,
    migration_strategy="phased"
)

# Example risk factors:
{
    "high_risk": [
        "Large JSONB columns (may require restructuring)",
        "Complex stored procedures (need Edge Function conversion)",
        "Custom data types (may need mapping)"
    ],
    "medium_risk": [
        "Large tables (may require batched migration)",
        "Complex foreign key relationships"
    ],
    "low_risk": [
        "Simple table structures",
        "Standard data types"
    ],
    "mitigation_strategies": [
        "Create rollback procedures for each phase",
        "Implement comprehensive testing",
        "Use progressive data migration"
    ]
}
```

## Step-by-Step Migration Process

### Phase 1: Pre-Migration Setup

#### Step 1: Create Backups
```bash
# Create full database backup
pg_dump -h localhost -U migration_user -d source_db > backups/pre_migration_backup.sql

# Create schema-only backup
pg_dump -h localhost -U migration_user -d source_db --schema-only > backups/schema_backup.sql

# Verify backup integrity
psql -h localhost -U migration_user -d test_restore_db < backups/pre_migration_backup.sql
```

#### Step 2: Set Up Supabase Project
```javascript
// Initialize Supabase project
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)

// Verify connectivity
const { data, error } = await supabase.from('_test').select('*').limit(1)
if (error && error.code !== 'PGRST116') {
  console.error('Supabase connection failed:', error)
} else {
  console.log('Supabase connection successful')
}
```

#### Step 3: Configure Migration Environment
```python
# Create migration configuration
migration_config = {
    "source": {
        "connection_string": SOURCE_DATABASE_URL,
        "database_name": SOURCE_DATABASE_NAME
    },
    "target": {
        "supabase_url": SUPABASE_URL,
        "service_role_key": SUPABASE_SERVICE_ROLE_KEY
    },
    "options": {
        "batch_size": 1000,
        "parallel_workers": 4,
        "enable_compression": True,
        "preserve_timestamps": True,
        "validate_data_integrity": True
    },
    "exclusions": {
        "tables": ["temp_data", "cache_*"],
        "schemas": ["information_schema", "pg_catalog"]
    }
}

# Save configuration
with open('migration_config.yaml', 'w') as f:
    yaml.dump(migration_config, f)
```

### Phase 2: Analysis and Planning

#### Step 4: Comprehensive Database Analysis
```python
from core.agents.supabase import SupabaseMigrationAgent

async def perform_analysis():
    agent = SupabaseMigrationAgent()

    # Comprehensive analysis
    analysis = await agent.analyze_database(
        connection_string=SOURCE_DATABASE_URL,
        database_name=SOURCE_DATABASE_NAME
    )

    # Save analysis results
    with open('analysis_results.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)

    # Generate analysis report
    report = generate_analysis_report(analysis)
    print(report)

    return analysis

# Run analysis
analysis = await perform_analysis()
```

#### Step 5: Generate Migration Plan
```python
async def create_migration_plan(analysis):
    agent = SupabaseMigrationAgent()

    # Generate comprehensive migration plan
    plan = await agent.generate_migration_plan(
        analysis_results=analysis,
        migration_options={
            "enable_realtime": True,
            "vector_dimensions": 1536,
            "multi_tenant": True,
            "batch_size": 1000,
            "rls_strategy": "role_based",
            "preserve_constraints": True,
            "optimize_indexes": True
        }
    )

    # Review and customize plan
    print(f"Migration Plan Summary:")
    print(f"- Tables to migrate: {len(plan.schema_mappings)}")
    print(f"- RLS policies: {len(plan.rls_policies)}")
    print(f"- Data migrations: {len(plan.data_migrations)}")
    print(f"- Estimated duration: {plan.estimated_duration} minutes")
    print(f"- Risk level: {plan.risk_assessment['level']}")

    # Save plan for review
    with open('migration_plan.json', 'w') as f:
        json.dump(asdict(plan), f, indent=2, default=str)

    return plan

# Generate plan
plan = await create_migration_plan(analysis)
```

### Phase 3: Dry Run Execution

#### Step 6: Execute Dry Run
```python
async def execute_dry_run(plan):
    agent = SupabaseMigrationAgent()

    print("Starting dry run migration...")

    # Execute dry run
    dry_results = await agent.execute_migration(
        plan=plan,
        dry_run=True
    )

    # Analyze dry run results
    if dry_results['status'] == 'completed':
        print("Dry run completed successfully!")

        # Review each phase
        for step in dry_results['steps']:
            print(f"✓ {step['step']}: {step['status']}")
            if step['status'] == 'failed':
                print(f"  Error: {step.get('error')}")

        return True
    else:
        print(f"Dry run failed: {dry_results.get('error')}")

        # Analyze failure points
        for step in dry_results['steps']:
            if step['status'] == 'failed':
                print(f"Failed step: {step['step']}")
                print(f"Error: {step.get('error')}")

        return False

# Execute dry run
dry_run_success = await execute_dry_run(plan)

if not dry_run_success:
    print("Please address dry run issues before proceeding")
    exit(1)
```

### Phase 4: Schema Migration

#### Step 7: Migrate Database Schema
```python
async def migrate_schema(plan):
    agent = SupabaseMigrationAgent()

    print("Migrating database schema...")

    # Execute schema migration only
    schema_results = await agent.execute_schema_migration(
        plan=plan,
        dry_run=False
    )

    if schema_results['status'] == 'completed':
        print("Schema migration completed successfully!")

        # Verify schema structure
        verification = await agent.verify_schema_migration(
            source_connection=SOURCE_DATABASE_URL,
            target_connection=SUPABASE_CONNECTION_STRING
        )

        if verification['schema_match']:
            print("Schema verification passed!")
            return True
        else:
            print("Schema verification failed!")
            print(f"Mismatches: {verification['mismatches']}")
            return False
    else:
        print(f"Schema migration failed: {schema_results.get('error')}")
        return False

# Execute schema migration
schema_success = await migrate_schema(plan)
```

#### Step 8: Apply RLS Policies
```python
async def apply_rls_policies(plan):
    from core.agents.supabase.tools import RLSPolicyGeneratorTool

    rls_tool = RLSPolicyGeneratorTool()

    print("Applying RLS policies...")

    # Generate SQL for RLS policies
    rls_sql = rls_tool.generate_sql(plan.rls_policies)

    # Apply policies to Supabase
    try:
        supabase = create_supabase_client()

        # Execute RLS policy SQL
        result = await supabase.rpc('execute_sql', {
            'sql': rls_sql
        })

        if result.error:
            print(f"RLS policy application failed: {result.error}")
            return False

        print("RLS policies applied successfully!")

        # Validate policies
        validation = rls_tool.validate_policies(plan.rls_policies, analysis['schema'])

        failed_validations = [v for v in validation if not v['valid']]
        if failed_validations:
            print("Policy validation warnings:")
            for validation in failed_validations:
                print(f"- {validation['policy']}: {validation['issues']}")

        return True

    except Exception as e:
        print(f"RLS policy application error: {e}")
        return False

# Apply RLS policies
rls_success = await apply_rls_policies(plan)
```

### Phase 5: Data Migration

#### Step 9: Execute Data Migration
```python
async def migrate_data(plan):
    agent = SupabaseMigrationAgent()

    print("Starting data migration...")

    # Execute data migration with progress tracking
    progress_callback = lambda progress: print(f"Migration progress: {progress['percentage']:.1f}% ({progress['table']})")

    data_results = await agent.execute_data_migration(
        plan=plan,
        dry_run=False,
        progress_callback=progress_callback
    )

    if data_results['status'] == 'completed':
        print("Data migration completed successfully!")

        # Verify data integrity
        integrity_check = await agent.verify_data_integrity(
            source_connection=SOURCE_DATABASE_URL,
            target_connection=SUPABASE_CONNECTION_STRING,
            tables=list(plan.schema_mappings.keys())
        )

        if integrity_check['passed']:
            print("Data integrity verification passed!")
            return True
        else:
            print("Data integrity verification failed!")
            print(f"Issues found: {integrity_check['issues']}")
            return False
    else:
        print(f"Data migration failed: {data_results.get('error')}")

        # Check for partial completion
        if data_results.get('partial_completion'):
            print("Partial migration completed. Resuming from checkpoint...")
            # Implement resume logic here

        return False

# Execute data migration
data_success = await migrate_data(plan)
```

### Phase 6: Function and Feature Migration

#### Step 10: Convert Edge Functions
```python
async def migrate_edge_functions(plan):
    print("Converting and deploying Edge Functions...")

    # Deploy each Edge Function
    for function_def in plan.edge_functions:
        try:
            # Deploy function to Supabase
            deployment_result = await deploy_edge_function(
                function_name=function_def['name'],
                function_code=function_def['code'],
                function_config=function_def['config']
            )

            if deployment_result['success']:
                print(f"✓ Deployed function: {function_def['name']}")

                # Test function
                test_result = await test_edge_function(
                    function_name=function_def['name'],
                    test_cases=function_def.get('test_cases', [])
                )

                if test_result['passed']:
                    print(f"✓ Function tests passed: {function_def['name']}")
                else:
                    print(f"⚠ Function tests failed: {function_def['name']}")
                    print(f"  Failures: {test_result['failures']}")
            else:
                print(f"✗ Failed to deploy function: {function_def['name']}")
                print(f"  Error: {deployment_result['error']}")

        except Exception as e:
            print(f"Error deploying function {function_def['name']}: {e}")

# Convert and deploy Edge Functions
await migrate_edge_functions(plan)
```

#### Step 11: Migrate Storage
```python
async def migrate_storage(plan):
    print("Migrating file storage...")

    # Create storage buckets
    for bucket_def in plan.storage_buckets:
        try:
            # Create bucket in Supabase Storage
            bucket_result = await create_storage_bucket(
                bucket_name=bucket_def['name'],
                bucket_config=bucket_def['config']
            )

            if bucket_result['success']:
                print(f"✓ Created bucket: {bucket_def['name']}")

                # Migrate files
                if bucket_def.get('files'):
                    migration_result = await migrate_bucket_files(
                        source_path=bucket_def['source_path'],
                        target_bucket=bucket_def['name'],
                        file_list=bucket_def['files']
                    )

                    print(f"✓ Migrated {migration_result['files_migrated']} files")
            else:
                print(f"✗ Failed to create bucket: {bucket_def['name']}")

        except Exception as e:
            print(f"Error migrating bucket {bucket_def['name']}: {e}")

# Migrate storage
await migrate_storage(plan)
```

### Phase 7: Validation and Testing

#### Step 12: Comprehensive Validation
```python
async def comprehensive_validation():
    agent = SupabaseMigrationAgent()

    print("Performing comprehensive validation...")

    # Full migration validation
    validation = await agent.validate_migration(
        source_connection=SOURCE_DATABASE_URL,
        target_connection=SUPABASE_CONNECTION_STRING
    )

    # Print validation results
    print(f"Overall Status: {validation['overall_status']}")

    for check_name, check_result in validation.items():
        if check_name != 'overall_status':
            status = "✓" if check_result.get('status') == 'passed' else "✗"
            print(f"{status} {check_name}: {check_result.get('status')}")

            if check_result.get('status') == 'failed':
                print(f"   Issues: {check_result.get('issues', [])}")

    return validation['overall_status'] == 'passed'

# Perform validation
validation_passed = await comprehensive_validation()

if not validation_passed:
    print("Migration validation failed. Please review and fix issues.")
    exit(1)
```

#### Step 13: Performance Testing
```python
async def performance_testing():
    print("Running performance tests...")

    # Define test queries
    test_queries = [
        {
            "name": "User lookup by ID",
            "sql": "SELECT * FROM users WHERE id = $1",
            "params": ["test-user-id"]
        },
        {
            "name": "Recent lessons query",
            "sql": "SELECT * FROM lessons WHERE created_at > NOW() - INTERVAL '7 days'",
            "params": []
        },
        {
            "name": "Complex join query",
            "sql": """
                SELECT u.name, l.title, e.enrolled_at
                FROM users u
                JOIN enrollments e ON u.id = e.student_id
                JOIN lessons l ON e.lesson_id = l.id
                WHERE u.organization_id = $1
            """,
            "params": ["test-org-id"]
        }
    ]

    # Run performance comparison
    performance_results = await compare_query_performance(
        source_connection=SOURCE_DATABASE_URL,
        target_connection=SUPABASE_CONNECTION_STRING,
        test_queries=test_queries,
        iterations=10
    )

    # Analyze results
    for query_result in performance_results:
        query_name = query_result['query_name']
        source_avg = query_result['source_avg_ms']
        target_avg = query_result['target_avg_ms']
        improvement = ((source_avg - target_avg) / source_avg) * 100

        print(f"Query: {query_name}")
        print(f"  Source: {source_avg:.2f}ms")
        print(f"  Target: {target_avg:.2f}ms")
        print(f"  Change: {improvement:+.1f}%")

# Run performance tests
await performance_testing()
```

## Common Migration Scenarios

### Scenario 1: Educational Platform (ToolBoxAI)

#### Characteristics
- 40+ tables with complex relationships
- User management with role-based access
- Content with vector embeddings
- Real-time features for collaboration
- Multi-tenant architecture

#### Migration Approach
```python
# Educational platform specific configuration
education_migration_options = {
    "enable_realtime": True,          # For collaborative features
    "vector_dimensions": 1536,        # OpenAI embeddings
    "multi_tenant": True,             # Organization isolation
    "rls_strategy": "hierarchical",   # Role-based access
    "preserve_user_sessions": True,   # Maintain active sessions
    "batch_size": 500,               # Conservative for data integrity
    "enable_audit_logging": True,     # Compliance requirements
    "custom_types": [                 # Platform-specific types
        "lesson_status",
        "quiz_type",
        "progress_state"
    ]
}

# Specific RLS policies for education
custom_rls_policies = [
    {
        "table": "lessons",
        "policy": "students_enrolled_content",
        "sql": """
            EXISTS (
                SELECT 1 FROM enrollments e
                JOIN classes c ON e.class_id = c.id
                JOIN class_lessons cl ON c.id = cl.class_id
                WHERE e.student_id = auth.uid()
                AND cl.lesson_id = lessons.id
                AND e.status = 'active'
            )
        """
    }
]
```

#### Timeline: 12-16 hours
- Analysis: 2 hours
- Planning: 2 hours
- Schema migration: 2 hours
- Data migration: 6 hours
- Function conversion: 2 hours
- Testing: 2 hours

### Scenario 2: E-commerce Platform

#### Characteristics
- High transaction volume
- Complex pricing and inventory logic
- Payment processing integration
- Analytics and reporting requirements

#### Migration Approach
```python
# E-commerce specific configuration
ecommerce_migration_options = {
    "enable_realtime": True,          # Inventory updates
    "preserve_transactions": True,     # Critical for consistency
    "enable_row_security": True,      # Customer data protection
    "batch_size": 2000,              # Higher throughput needed
    "parallel_workers": 6,           # Faster data migration
    "custom_functions": [            # Business logic preservation
        "calculate_shipping",
        "apply_discounts",
        "update_inventory"
    ]
}
```

### Scenario 3: SaaS Application

#### Characteristics
- Multi-tenant with strict isolation
- Feature flags and subscription tiers
- API-heavy architecture
- Real-time notifications

#### Migration Approach
```python
# SaaS specific configuration
saas_migration_options = {
    "multi_tenant": True,
    "tenant_isolation_strategy": "rls",
    "api_endpoint_conversion": True,
    "subscription_tier_mapping": True,
    "feature_flag_migration": True,
    "webhook_endpoint_migration": True
}
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Connection Timeouts
**Symptoms:**
- Migration fails with timeout errors
- Intermittent connection drops

**Solutions:**
```python
# Increase timeout settings
migration_options = {
    "connection_timeout": 300,      # 5 minutes
    "query_timeout": 600,          # 10 minutes
    "retry_attempts": 3,
    "retry_backoff": 5             # seconds
}

# Use connection pooling
connection_config = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

#### Issue 2: Memory Issues with Large Tables
**Symptoms:**
- Out of memory errors
- Slow performance during data migration

**Solutions:**
```python
# Reduce batch size and use streaming
large_table_options = {
    "batch_size": 100,             # Smaller batches
    "use_streaming": True,         # Stream instead of loading all
    "enable_compression": True,    # Compress data in transit
    "checkpoint_interval": 1000    # Save progress frequently
}

# Process tables sequentially
migration_order = [
    "small_tables_first",
    "medium_tables",
    "large_tables_last"
]
```

#### Issue 3: RLS Policy Conflicts
**Symptoms:**
- Access denied errors after migration
- Users can't see expected data

**Solutions:**
```sql
-- Debug RLS policies
SET row_security = off;  -- Temporarily disable RLS for testing

-- Check policy definitions
SELECT schemaname, tablename, policyname, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'your_table';

-- Test policy logic
SELECT auth.uid(), organization_id FROM users WHERE id = auth.uid();
```

#### Issue 4: Data Type Conversion Issues
**Symptoms:**
- Data type mismatch errors
- Precision loss in numeric data

**Solutions:**
```python
# Custom type mappings
type_mappings = {
    "serial": "bigint",           # Use bigint instead of serial
    "money": "decimal(19,4)",     # Convert money to decimal
    "jsonb": "jsonb",             # Direct mapping for JSON
    "uuid": "uuid",               # Direct UUID mapping
    "timestamp": "timestamptz"     # Use timezone-aware timestamps
}

# Pre-migration data validation
validation_rules = {
    "check_numeric_precision": True,
    "validate_json_structure": True,
    "check_uuid_format": True,
    "validate_date_ranges": True
}
```

#### Issue 5: Foreign Key Constraint Violations
**Symptoms:**
- Constraint violation errors during data insertion
- Referential integrity issues

**Solutions:**
```python
# Disable constraints during migration
migration_sequence = [
    "disable_foreign_keys",
    "migrate_parent_tables",
    "migrate_child_tables",
    "enable_foreign_keys",
    "validate_constraints"
]

# Or use dependency-ordered migration
dependency_order = calculate_table_dependencies(schema)
for table in dependency_order:
    migrate_table(table)
```

### Recovery Procedures

#### Rollback Process
```python
async def rollback_migration(rollback_point="complete"):
    agent = SupabaseMigrationAgent()

    print(f"Initiating rollback to: {rollback_point}")

    if rollback_point == "complete":
        # Complete rollback
        await agent.execute_complete_rollback()
    elif rollback_point == "data_only":
        # Keep schema, rollback data
        await agent.rollback_data_migration()
    elif rollback_point == "schema_only":
        # Rollback schema changes
        await agent.rollback_schema_migration()

    print("Rollback completed")

# Execute rollback if needed
await rollback_migration("complete")
```

#### Data Recovery from Backup
```bash
# Restore from backup if rollback fails
psql -h db.supabase.co -U postgres -d postgres < backups/pre_migration_backup.sql

# Selective table restore
pg_restore -h db.supabase.co -U postgres -d postgres -t specific_table backups/table_backup.dump
```

## Post-Migration Tasks

### 1. Application Configuration Updates

#### Update Connection Strings
```python
# Update application configuration
DATABASE_CONFIG = {
    "host": "db.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": SUPABASE_DB_PASSWORD,
    "sslmode": "require"
}

# Update ORM configuration
SQLALCHEMY_DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"
```

#### Update API Endpoints
```javascript
// Update frontend configuration
const supabaseConfig = {
  url: process.env.NEXT_PUBLIC_SUPABASE_URL,
  anonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  serviceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY  // Server-side only
}

// Initialize Supabase client
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(supabaseConfig.url, supabaseConfig.anonKey)
```

### 2. Security Hardening

#### Review and Optimize RLS Policies
```sql
-- Review all policies
SELECT
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual as using_clause,
    with_check as check_clause
FROM pg_policies
ORDER BY schemaname, tablename, policyname;

-- Test policy performance
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM lessons WHERE organization_id = 'test-org';
```

#### Configure API Security
```sql
-- Set up API rate limiting
INSERT INTO auth.rate_limits (identifier, action, limit_per_hour)
VALUES
    ('anon', 'select', 1000),
    ('authenticated', 'select', 10000),
    ('authenticated', 'insert', 1000);

-- Configure CORS settings
UPDATE auth.config
SET cors_allowed_origins = '["https://yourdomain.com", "https://app.yourdomain.com"]'
WHERE key = 'cors';
```

### 3. Performance Optimization

#### Create Necessary Indexes
```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_lessons_organization_id ON lessons(organization_id);
CREATE INDEX CONCURRENTLY idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX CONCURRENTLY idx_lessons_search ON lessons USING gin(to_tsvector('english', title || ' ' || content));

-- Vector similarity indexes
CREATE INDEX CONCURRENTLY idx_content_embeddings ON lesson_embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### Configure Connection Pooling
```javascript
// Use connection pooling for high-traffic applications
const { Pool } = require('pg')

const pool = new Pool({
  host: 'db.supabase.co',
  port: 5432,
  database: 'postgres',
  user: 'postgres',
  password: process.env.SUPABASE_DB_PASSWORD,
  max: 20,           // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
})
```

### 4. Monitoring and Alerting

#### Set Up Monitoring
```python
# Configure application monitoring
MONITORING_CONFIG = {
    "database_metrics": {
        "connection_count": True,
        "query_performance": True,
        "error_rates": True
    },
    "application_metrics": {
        "api_response_times": True,
        "user_activity": True,
        "feature_usage": True
    },
    "alerts": {
        "high_error_rate": {"threshold": 5, "window": "5m"},
        "slow_queries": {"threshold": 1000, "unit": "ms"},
        "connection_limit": {"threshold": 80, "unit": "percent"}
    }
}
```

#### Create Health Check Endpoints
```python
from fastapi import FastAPI
from supabase import create_client

app = FastAPI()

@app.get("/health")
async def health_check():
    try:
        # Test database connectivity
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        result = await supabase.from('users').select('id').limit(1).execute()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Best Practices

### 1. Planning Phase Best Practices

- **Start with Analysis**: Always perform comprehensive analysis before planning
- **Document Everything**: Keep detailed records of decisions and rationale
- **Plan for Rollback**: Design rollback procedures for every migration phase
- **Test with Subsets**: Use sample data for initial testing
- **Stakeholder Communication**: Keep all stakeholders informed of progress and risks

### 2. Execution Phase Best Practices

- **Always Start with Dry Run**: Never skip the dry run phase
- **Monitor Progress**: Use real-time monitoring during migration
- **Validate Each Phase**: Don't proceed until each phase is validated
- **Maintain Backups**: Keep multiple backup copies during migration
- **Document Issues**: Record any issues and resolutions for future reference

### 3. Security Best Practices

- **Principle of Least Privilege**: Grant minimum necessary permissions
- **Regular Security Audits**: Review RLS policies regularly
- **Encrypt Sensitive Data**: Use Supabase encryption features
- **Monitor Access Patterns**: Track unusual access patterns
- **Implement Audit Logging**: Log all significant database operations

### 4. Performance Best Practices

- **Index Strategy**: Plan indexes before data migration
- **Batch Optimization**: Tune batch sizes for your data patterns
- **Connection Management**: Use appropriate connection pooling
- **Query Optimization**: Review and optimize slow queries
- **Monitoring**: Implement comprehensive performance monitoring

### 5. Maintenance Best Practices

- **Regular Updates**: Keep Supabase and dependencies updated
- **Backup Strategy**: Implement automated backup procedures
- **Documentation**: Maintain up-to-date documentation
- **Disaster Recovery**: Test disaster recovery procedures regularly
- **Performance Reviews**: Conduct regular performance reviews

---

*Migration Guide Version: 1.0.0*
*Last Updated: 2025-09-21*
*Compatible with: ToolBoxAI Platform v1.1.0+, Supabase Latest*