# Supabase Migration Tools

This directory contains comprehensive tools for migrating from PostgreSQL/FastAPI applications to Supabase. Each tool is designed to handle specific aspects of the migration process with robust error handling, progress tracking, and dry-run capabilities.

## Available Tools

### 1. SchemaAnalyzerTool (`schema_analyzer.py`)
- **Purpose**: Analyze PostgreSQL database schemas for migration planning
- **Features**:
  - Extract tables, columns, relationships, and constraints
  - Generate migration complexity reports
  - Identify potential migration issues

### 2. RLSPolicyGeneratorTool (`rls_policy_generator.py`)
- **Purpose**: Generate Row Level Security policies for Supabase tables
- **Features**:
  - Auto-detect table types (user, content, admin)
  - Generate appropriate RLS policies
  - Support for multi-tenant and hierarchical access patterns

### 3. DataMigrationTool (`data_migration.py`)
- **Purpose**: Migrate data from PostgreSQL to Supabase with integrity validation
- **Features**:
  - Batch processing with configurable sizes
  - Progress tracking and callbacks
  - Data integrity validation
  - Incremental migration support
  - Rollback capabilities
  - Performance optimization

### 4. VectorEmbeddingTool (`vector_embedding.py`)
- **Purpose**: Generate and manage vector embeddings for Supabase pgvector
- **Features**:
  - OpenAI ada-002 integration
  - Batch embedding generation with rate limiting
  - Caching mechanism for cost optimization
  - Similarity search setup
  - Vector index management

### 5. EdgeFunctionConverterTool (`edge_function_converter.py`)
- **Purpose**: Convert FastAPI endpoints to Supabase Edge Functions
- **Features**:
  - FastAPI endpoint analysis and extraction
  - TypeScript/Deno conversion
  - Automatic deployment script generation
  - Environment variable mapping
  - Dependency resolution

### 6. StorageMigrationTool (`storage_migration.py`)
- **Purpose**: Migrate files to Supabase Storage
- **Features**:
  - File inventory creation with filtering
  - Bucket configuration and creation
  - Batch upload mechanism with concurrent processing
  - Access policy setup
  - Migration verification and integrity checks

### 7. TypeGeneratorTool (`type_generator.py`)
- **Purpose**: Generate TypeScript types from Supabase schema
- **Features**:
  - TypeScript interface generation
  - Zod schema generation for validation
  - API client types with CRUD operations
  - Database types and utilities
  - Relationship mapping

## Usage Examples

### Basic Migration Workflow

```python
from core.agents.supabase.tools import (
    SchemaAnalyzerTool,
    DataMigrationTool,
    RLSPolicyGeneratorTool,
    TypeGeneratorTool
)

# 1. Analyze source schema
analyzer = SchemaAnalyzerTool()
schema = await analyzer.analyze(
    connection_string="postgresql://user:pass@localhost/db",
    database_name="my_app"
)

# 2. Generate RLS policies
rls_generator = RLSPolicyGeneratorTool()
policies = await rls_generator.generate_policies(schema)

# 3. Migrate data
data_migrator = DataMigrationTool(batch_size=1000)
result = await data_migrator.migrate_database(
    source_conn_string="postgresql://source",
    target_conn_string="postgresql://supabase",
    dry_run=False
)

# 4. Generate TypeScript types
type_generator = TypeGeneratorTool()
types = await type_generator.generate_types_from_connection(
    connection_string="postgresql://supabase",
    output_directory="./generated-types"
)
```

### Vector Embeddings Setup

```python
from core.agents.supabase.tools import VectorEmbeddingTool

# Setup vector embeddings
embedding_tool = VectorEmbeddingTool(
    openai_api_key="your-key",
    batch_size=50,
    cache_embeddings=True
)

# Generate embeddings for content
result = await embedding_tool.generate_embeddings(
    conn_string="postgresql://supabase",
    table_name="articles",
    text_columns=["title", "content"],
    embedding_column="embedding"
)

# Setup similarity search
await embedding_tool.setup_vector_search(
    conn_string="postgresql://supabase",
    table_name="articles",
    similarity_function="cosine"
)
```

### FastAPI to Edge Functions Conversion

```python
from core.agents.supabase.tools import EdgeFunctionConverterTool

# Convert FastAPI project
converter = EdgeFunctionConverterTool()

# Analyze project
endpoints = await converter.analyze_fastapi_project("./my-fastapi-app")

# Convert all endpoints
results = await converter.convert_project(
    project_path="./my-fastapi-app",
    target_directory="./edge-functions",
    dry_run=False
)
```

### File Storage Migration

```python
from core.agents.supabase.tools import StorageMigrationTool

# Setup storage migration
storage_tool = StorageMigrationTool(
    supabase_url="https://xxx.supabase.co",
    supabase_key="your-service-role-key"
)

# Create file inventory
inventory = await storage_tool.create_file_inventory(
    source_directory="./uploads",
    bucket_mapping={
        "images/*": "images",
        "documents/*": "documents",
        "*": "files"
    }
)

# Migrate files
result = await storage_tool.migrate_files(
    inventory=inventory,
    dry_run=False
)
```

## Key Features

### Error Handling
- Comprehensive exception handling with detailed error messages
- Graceful degradation on partial failures
- Retry mechanisms for transient failures

### Progress Tracking
- Optional progress callbacks for long-running operations
- Detailed logging with configurable levels
- Real-time status updates

### Dry Run Support
- All tools support dry-run mode for validation
- Preview changes before execution
- Cost estimation for API operations

### Performance Optimization
- Configurable batch sizes for optimal performance
- Concurrent processing with rate limiting
- Memory-efficient streaming for large datasets

### Validation & Integrity
- Data integrity checks during migration
- Schema compatibility validation
- Checksum verification for file transfers

## Dependencies

All tools use the following core dependencies:
- `asyncio` - Asynchronous operations
- `asyncpg` - PostgreSQL async driver
- `aiohttp` - HTTP client for API calls
- `aiofiles` - Async file operations
- `sqlalchemy` - Database ORM
- `openai` - OpenAI API integration (for embeddings)

See `requirements.txt` for complete dependency list.

## Configuration

Tools can be configured through environment variables:

```bash
# Database connections
DATABASE_URL=postgresql://user:pass@localhost/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key

# OpenAI (for embeddings)
OPENAI_API_KEY=your-openai-key

# Optional performance tuning
MIGRATION_BATCH_SIZE=1000
MAX_CONCURRENT_UPLOADS=5
```

## Best Practices

1. **Always run dry-run first** to validate the migration plan
2. **Start with schema analysis** to understand complexity
3. **Use incremental migration** for large datasets
4. **Monitor progress** with callbacks for long operations
5. **Verify integrity** after each major migration step
6. **Keep backups** of source data before migration
7. **Test thoroughly** in staging environment first

## Support

For issues or questions about the migration tools:
1. Check the detailed logging output for error details
2. Review the generated reports for migration insights
3. Use dry-run mode to validate before execution
4. Consult the Supabase documentation for platform-specific guidance