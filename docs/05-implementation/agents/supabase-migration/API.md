# ToolBoxAI Supabase Migration System - API Documentation

## Table of Contents

1. [SupabaseMigrationAgent](#supabasemigrationagent)
2. [Migration Tools](#migration-tools)
3. [Data Models](#data-models)
4. [Error Handling](#error-handling)
5. [Usage Examples](#usage-examples)

## SupabaseMigrationAgent

The main orchestrator class for PostgreSQL to Supabase migration operations.

### Class Definition

```python
class SupabaseMigrationAgent(BaseAgent):
    """
    Specialized agent for PostgreSQL to Supabase migration.

    Integrates with SPARC framework for intelligent migration planning
    and execution with comprehensive safety checks and rollback capabilities.
    """
```

### Constructor

```python
def __init__(
    self,
    llm: Optional[Any] = None,
    state_manager: Optional[StateManager] = None,
    **kwargs
) -> None:
```

**Parameters:**
- `llm` (Optional[Any]): Language model for AI-powered decision making
- `state_manager` (Optional[StateManager]): SPARC state management system
- `**kwargs`: Additional configuration parameters

**Example:**
```python
from core.agents.supabase import SupabaseMigrationAgent
from core.sparc.state_manager import StateManager

state_manager = StateManager()
agent = SupabaseMigrationAgent(
    state_manager=state_manager,
    enable_logging=True,
    batch_size=1000
)
```

### Core Methods

#### analyze_database

```python
async def analyze_database(
    self,
    connection_string: str,
    database_name: str
) -> Dict[str, Any]:
```

Analyzes existing PostgreSQL database structure and generates comprehensive analysis report.

**Parameters:**
- `connection_string` (str): PostgreSQL connection string (format: `postgresql://user:pass@host:port/db`)
- `database_name` (str): Name of the database to analyze

**Returns:**
- `Dict[str, Any]`: Analysis results containing:
  - `schema`: Complete schema information
  - `relationships`: Table relationships and foreign keys
  - `complexity`: Migration complexity assessment
  - `recommendations`: AI-generated recommendations

**Raises:**
- `ConnectionError`: Database connection failed
- `PermissionError`: Insufficient database permissions
- `ValueError`: Invalid connection string or database name

**Example:**
```python
analysis = await agent.analyze_database(
    connection_string="postgresql://user:pass@localhost:5432/myapp",
    database_name="myapp_production"
)

print(f"Found {len(analysis['schema']['tables'])} tables")
print(f"Complexity level: {analysis['complexity']['level']}")
```

#### generate_migration_plan

```python
async def generate_migration_plan(
    self,
    analysis_results: Dict[str, Any],
    migration_options: Optional[Dict[str, Any]] = None
) -> MigrationPlan:
```

Generates comprehensive migration plan based on database analysis.

**Parameters:**
- `analysis_results` (Dict[str, Any]): Results from `analyze_database()`
- `migration_options` (Optional[Dict[str, Any]]): Migration configuration options

**Migration Options:**
```python
migration_options = {
    "enable_realtime": bool,           # Enable Supabase Realtime
    "vector_dimensions": int,          # Vector embedding dimensions
    "multi_tenant": bool,              # Multi-tenant architecture
    "batch_size": int,                 # Data migration batch size
    "parallel_workers": int,           # Number of parallel workers
    "preserve_constraints": bool,      # Preserve all constraints
    "optimize_indexes": bool,          # Optimize index creation
    "custom_types": List[str],         # Custom type mappings
    "excluded_tables": List[str],      # Tables to exclude
    "rls_strategy": str               # RLS policy strategy
}
```

**Returns:**
- `MigrationPlan`: Comprehensive migration plan object

**Example:**
```python
plan = await agent.generate_migration_plan(
    analysis_results=analysis,
    migration_options={
        "enable_realtime": True,
        "vector_dimensions": 1536,
        "multi_tenant": True,
        "batch_size": 500
    }
)

print(f"Migration estimated duration: {plan.estimated_duration} minutes")
print(f"Risk level: {plan.risk_assessment['level']}")
```

#### execute_migration

```python
async def execute_migration(
    self,
    plan: MigrationPlan,
    dry_run: bool = True
) -> Dict[str, Any]:
```

Executes the migration plan with comprehensive logging and error handling.

**Parameters:**
- `plan` (MigrationPlan): Migration plan from `generate_migration_plan()`
- `dry_run` (bool): If True, simulates migration without actual changes

**Returns:**
- `Dict[str, Any]`: Migration execution results containing:
  - `status`: 'started', 'completed', 'failed'
  - `start_time`: ISO timestamp
  - `end_time`: ISO timestamp (if completed)
  - `dry_run`: Boolean indicating simulation mode
  - `steps`: List of executed steps with results
  - `error`: Error message (if failed)
  - `rollback`: Rollback results (if applicable)

**Migration Phases:**
1. **Schema Creation**: Tables, constraints, indexes
2. **RLS Policies**: Row Level Security implementation
3. **Data Migration**: Batch data transfer with validation
4. **Vector Embeddings**: Vector data migration and optimization
5. **Edge Functions**: API endpoint conversion and deployment
6. **Storage Migration**: File storage and bucket configuration
7. **Validation**: Comprehensive integrity checks

**Example:**
```python
# Dry run first
dry_results = await agent.execute_migration(plan, dry_run=True)
if dry_results['status'] == 'completed':
    print("Dry run successful, proceeding with actual migration")

    # Actual migration
    results = await agent.execute_migration(plan, dry_run=False)
    print(f"Migration {results['status']}")
```

#### validate_migration

```python
async def validate_migration(
    self,
    source_connection: str,
    target_connection: str
) -> Dict[str, Any]:
```

Validates migration completeness and data integrity between source and target databases.

**Parameters:**
- `source_connection` (str): Source PostgreSQL connection string
- `target_connection` (str): Target Supabase connection string

**Returns:**
- `Dict[str, Any]`: Validation results containing:
  - `schema_validation`: Schema structure comparison
  - `data_validation`: Data integrity verification
  - `performance_comparison`: Query performance analysis
  - `security_validation`: RLS policy verification
  - `overall_status`: 'passed' or 'failed'

**Example:**
```python
validation = await agent.validate_migration(
    source_connection="postgresql://user:pass@localhost:5432/source_db",
    target_connection="postgresql://postgres:pass@db.supabase.co:5432/postgres"
)

if validation['overall_status'] == 'passed':
    print("Migration validation successful!")
else:
    print("Validation issues found:")
    for check, result in validation.items():
        if result.get('status') == 'failed':
            print(f"- {check}: {result.get('message')}")
```

#### process_task

```python
async def process_task(
    self,
    task: str,
    context: Dict[str, Any]
) -> TaskOutput:
```

Processes migration-related tasks with SPARC framework integration.

**Parameters:**
- `task` (str): Task description ('analyze', 'plan', 'execute', 'validate')
- `context` (Dict[str, Any]): Task context and parameters

**Returns:**
- `TaskOutput`: Standardized task result with success status and metadata

**Task Types:**
- `"analyze"`: Database analysis task
- `"plan"`: Migration planning task
- `"execute"`: Migration execution task
- `"validate"`: Migration validation task

**Example:**
```python
# Task-based execution
result = await agent.process_task(
    task="analyze",
    context={
        "connection_string": "postgresql://...",
        "database_name": "myapp"
    }
)

if result.success:
    analysis_data = result.result
    print(f"Analysis completed: {len(analysis_data['schema']['tables'])} tables found")
```

## Migration Tools

### SchemaAnalyzerTool

Analyzes PostgreSQL database schemas and extracts comprehensive structural information.

```python
class SchemaAnalyzerTool:
    """Tool for analyzing PostgreSQL database schemas."""

    async def analyze(
        self,
        connection_string: str,
        database_name: str
    ) -> Dict[str, Any]:
        """Analyze database schema comprehensively."""

    async def extract_relationships(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract relationships and dependencies from schema."""

    def generate_migration_report(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a migration complexity report."""
```

**Schema Analysis Output:**
```python
{
    "database": "database_name",
    "tables": [
        {
            "name": "table_name",
            "columns": [
                {
                    "name": "column_name",
                    "type": "data_type",
                    "nullable": bool,
                    "default": "default_value",
                    "autoincrement": bool
                }
            ],
            "primary_key": {"constrained_columns": ["id"]},
            "foreign_keys": [...],
            "indexes": [...],
            "unique_constraints": [...],
            "check_constraints": [...],
            "row_count": int,
            "size_bytes": int
        }
    ],
    "views": [...],
    "sequences": [...],
    "functions": [...],
    "triggers": [...],
    "enums": [...]
}
```

### RLSPolicyGeneratorTool

Generates Row Level Security policies for Supabase based on access patterns and table analysis.

```python
class RLSPolicyGeneratorTool:
    """Tool for generating Row Level Security policies for Supabase."""

    async def generate_policies(
        self,
        schema: Dict[str, Any],
        access_patterns: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate RLS policies based on schema and access patterns."""

    def generate_sql(
        self,
        policies: List[Dict[str, Any]]
    ) -> str:
        """Generate SQL statements for RLS policies."""

    def validate_policies(
        self,
        policies: List[Dict[str, Any]],
        schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate generated policies against schema."""
```

**RLS Policy Structure:**
```python
{
    "name": "policy_name",
    "table": "table_name",
    "policy_type": "SELECT|INSERT|UPDATE|DELETE|ALL",
    "roles": ["authenticated", "anon", "service_role"],
    "using_clause": "auth.uid() = user_id",
    "check_clause": "auth.uid() = user_id",  # Optional for INSERT/UPDATE
    "description": "Policy description"
}
```

**Policy Types:**
- **User Policies**: `auth.uid() = user_id` - Users access their own data
- **Content Policies**: Role-based content access with enrollment checks
- **Admin Policies**: Admin-only access with role verification
- **Multi-tenant Policies**: Organization-based data isolation
- **Time-based Policies**: Content access based on publish/expire dates

### Tool Integration Examples

```python
# Direct tool usage
schema_analyzer = SchemaAnalyzerTool()
rls_generator = RLSPolicyGeneratorTool()

# Analyze schema
schema = await schema_analyzer.analyze(
    "postgresql://user:pass@host/db",
    "database_name"
)

# Generate policies
policies = await rls_generator.generate_policies(
    schema=schema,
    access_patterns={"multi_tenant": True}
)

# Generate SQL
sql = rls_generator.generate_sql(policies)
print(sql)
```

## Data Models

### MigrationPlan

```python
@dataclass
class MigrationPlan:
    """Represents a complete migration plan."""
    schema_mappings: Dict[str, Any] = field(default_factory=dict)
    rls_policies: List[Dict[str, Any]] = field(default_factory=list)
    data_migrations: List[Dict[str, Any]] = field(default_factory=list)
    edge_functions: List[Dict[str, Any]] = field(default_factory=list)
    storage_buckets: List[Dict[str, Any]] = field(default_factory=list)
    type_definitions: Dict[str, str] = field(default_factory=dict)
    rollback_procedures: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration: int = 0  # in minutes
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
```

### RLSPolicy

```python
@dataclass
class RLSPolicy:
    """Represents a Row Level Security policy."""
    name: str
    table: str
    policy_type: PolicyType
    roles: List[str]
    using_clause: str
    check_clause: Optional[str] = None
    description: Optional[str] = None
```

### PolicyType

```python
class PolicyType(Enum):
    """Types of RLS policies."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "ALL"
```

### TableInfo

```python
@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    row_count: int
    size_bytes: int
```

## Error Handling

### Exception Types

```python
# Connection errors
class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass

# Permission errors
class InsufficientPermissionsError(Exception):
    """Raised when database permissions are insufficient."""
    pass

# Migration errors
class MigrationExecutionError(Exception):
    """Raised when migration execution fails."""
    pass

# Validation errors
class MigrationValidationError(Exception):
    """Raised when migration validation fails."""
    pass
```

### Error Response Format

```python
{
    "error": {
        "type": "ConnectionError",
        "message": "Failed to connect to database",
        "details": {
            "host": "localhost",
            "port": 5432,
            "database": "myapp",
            "timestamp": "2025-09-21T10:30:00Z"
        },
        "suggestion": "Check connection parameters and network connectivity"
    }
}
```

### Error Handling Examples

```python
try:
    analysis = await agent.analyze_database(connection_string, database_name)
except DatabaseConnectionError as e:
    print(f"Connection failed: {e}")
    # Implement retry logic or alternative connection
except InsufficientPermissionsError as e:
    print(f"Permission error: {e}")
    # Request additional permissions or use different credentials
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log error and implement fallback
```

## Usage Examples

### Complete Migration Workflow

```python
import asyncio
from core.agents.supabase import SupabaseMigrationAgent

async def complete_migration():
    """Complete migration workflow example."""

    # Initialize agent
    agent = SupabaseMigrationAgent()

    try:
        # Step 1: Analyze source database
        print("Analyzing source database...")
        analysis = await agent.analyze_database(
            connection_string="postgresql://user:pass@localhost:5432/source_db",
            database_name="production_app"
        )

        print(f"Analysis complete:")
        print(f"- Tables: {len(analysis['schema']['tables'])}")
        print(f"- Complexity: {analysis['complexity']['level']}")
        print(f"- Estimated effort: {analysis['complexity']['estimated_effort']} hours")

        # Step 2: Generate migration plan
        print("\nGenerating migration plan...")
        plan = await agent.generate_migration_plan(
            analysis_results=analysis,
            migration_options={
                "enable_realtime": True,
                "vector_dimensions": 1536,
                "multi_tenant": True,
                "batch_size": 1000,
                "rls_strategy": "role_based"
            }
        )

        print(f"Migration plan generated:")
        print(f"- RLS policies: {len(plan.rls_policies)}")
        print(f"- Data migrations: {len(plan.data_migrations)}")
        print(f"- Edge functions: {len(plan.edge_functions)}")
        print(f"- Estimated duration: {plan.estimated_duration} minutes")
        print(f"- Risk level: {plan.risk_assessment['level']}")

        # Step 3: Dry run execution
        print("\nExecuting dry run...")
        dry_results = await agent.execute_migration(plan, dry_run=True)

        if dry_results['status'] == 'completed':
            print("Dry run successful!")

            # Step 4: Actual migration
            print("\nExecuting actual migration...")
            migration_results = await agent.execute_migration(plan, dry_run=False)

            if migration_results['status'] == 'completed':
                print("Migration completed successfully!")

                # Step 5: Validation
                print("\nValidating migration...")
                validation = await agent.validate_migration(
                    source_connection="postgresql://user:pass@localhost:5432/source_db",
                    target_connection="postgresql://postgres:pass@db.supabase.co:5432/postgres"
                )

                if validation['overall_status'] == 'passed':
                    print("Migration validation successful!")
                    return True
                else:
                    print("Migration validation failed!")
                    return False
            else:
                print(f"Migration failed: {migration_results.get('error')}")
                return False
        else:
            print(f"Dry run failed: {dry_results.get('error')}")
            return False

    except Exception as e:
        print(f"Migration error: {e}")
        return False

# Run the migration
if __name__ == "__main__":
    success = asyncio.run(complete_migration())
    print(f"Migration {'succeeded' if success else 'failed'}")
```

### Custom RLS Policy Generation

```python
from core.agents.supabase.tools import RLSPolicyGeneratorTool

async def generate_custom_policies():
    """Example of custom RLS policy generation."""

    rls_tool = RLSPolicyGeneratorTool()

    # Mock schema for example
    schema = {
        "tables": [
            {
                "name": "lessons",
                "columns": [
                    {"name": "id", "type": "uuid"},
                    {"name": "title", "type": "text"},
                    {"name": "created_by", "type": "uuid"},
                    {"name": "organization_id", "type": "uuid"},
                    {"name": "status", "type": "text"}
                ]
            },
            {
                "name": "enrollments",
                "columns": [
                    {"name": "id", "type": "uuid"},
                    {"name": "student_id", "type": "uuid"},
                    {"name": "lesson_id", "type": "uuid"},
                    {"name": "enrolled_at", "type": "timestamp"}
                ]
            }
        ]
    }

    # Access patterns for educational platform
    access_patterns = {
        "lessons": {
            "multi_tenant": True,
            "hierarchical": True,
            "time_based": True
        },
        "enrollments": {
            "multi_tenant": True
        }
    }

    # Generate policies
    policies = await rls_tool.generate_policies(schema, access_patterns)

    # Generate SQL
    sql = rls_tool.generate_sql(policies)

    print("Generated RLS Policies:")
    print(sql)

    # Validate policies
    validation_results = rls_tool.validate_policies(policies, schema)

    for result in validation_results:
        if not result['valid']:
            print(f"Policy validation error: {result['policy']}")
            for issue in result['issues']:
                print(f"  - {issue}")

# Run the example
asyncio.run(generate_custom_policies())
```

### Schema Analysis Only

```python
from core.agents.supabase.tools import SchemaAnalyzerTool

async def analyze_schema_only():
    """Example of standalone schema analysis."""

    analyzer = SchemaAnalyzerTool()

    # Analyze database
    schema = await analyzer.analyze(
        connection_string="postgresql://user:pass@localhost:5432/myapp",
        database_name="production"
    )

    # Extract relationships
    relationships = await analyzer.extract_relationships(schema)

    # Generate migration report
    report = analyzer.generate_migration_report(schema)

    print("Schema Analysis Results:")
    print(f"- Database: {schema['database']}")
    print(f"- Tables: {len(schema['tables'])}")
    print(f"- Views: {len(schema['views'])}")
    print(f"- Functions: {len(schema['functions'])}")
    print(f"- Foreign Keys: {len(relationships['foreign_keys'])}")

    print(f"\nMigration Report:")
    print(f"- Estimated effort: {report['estimated_effort']} hours")
    print(f"- Complexity factors: {report['complexity_factors']}")
    print(f"- Recommendations: {report['recommendations']}")

# Run the analysis
asyncio.run(analyze_schema_only())
```

---

*API Documentation Version: 1.0.0*
*Last Updated: 2025-09-21*
*Compatible with: ToolBoxAI Platform v1.1.0+*