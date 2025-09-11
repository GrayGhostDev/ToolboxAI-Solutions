# ToolboxAI Database Documentation

This directory contains the complete database infrastructure for the ToolboxAI Roblox Environment, including schemas, migrations, connection management, and setup scripts.

## 📁 Directory Structure

```text
database/
├── README.md                    # This documentation
├── alembic.ini                  # Alembic configuration
├── connection_manager.py        # Database connection management
├── setup_database.py           # Python setup script
├── migrate.py                  # Migration management script
├── schemas/                    # Database schema files
│   ├── 01_core_schema.sql      # Core user and content models
│   ├── 02_ai_agents_schema.sql # AI agent system models
│   ├── 03_lms_integration_schema.sql # LMS integration models
│   └── 04_analytics_schema.sql # Analytics and monitoring models
└── migrations/                 # Alembic migration files
    ├── env.py                  # Alembic environment configuration
    ├── script.py.mako          # Migration template
    └── versions/               # Generated migration files
```text
## 🗄️ Database Architecture

### Multi-Database Setup

ToolboxAI uses multiple PostgreSQL databases for different services:

1. **ghost_backend** - Main API, authentication, and user management
2. **educational_platform** - Educational content, lessons, quizzes, and progress
3. **roblox_data** - Roblox integration, scripts, and game sessions
4. **mcp_memory** - AI context and memory storage
5. **toolboxai_dev** - Development and testing database

### Additional Services

- **Redis** - Session storage, caching, and real-time data
- **MongoDB** (Optional) - Document storage for large datasets

## 🚀 Quick Start

### Prerequisites

1. **PostgreSQL 16+** - Primary database system
2. **Redis 6+** - Caching and session storage
3. **Python 3.9+** - With required packages
4. **Alembic** - Database migration tool

### Installation

1. **Install Python dependencies:**

   ```bash
   pip install sqlalchemy psycopg2-binary alembic redis pymongo python-dotenv
   ```

2. **Run the setup script:**

   ```bash
   ./scripts/setup_database.sh
   ```

3. **Or use Python setup:**
   ```bash
   python database/setup_database.py
   ```

### Environment Configuration

Copy the environment template and update with your credentials:

```bash
cp config/database.env.example .env
```text
Update the `.env` file with your database credentials:

```env
# Educational Platform Database
EDU_DB_HOST=localhost
EDU_DB_PORT=5432
EDU_DB_NAME=educational_platform
EDU_DB_USER=eduplatform
EDU_DB_PASSWORD=[REDACTED]
EDU_DB_ECHO=false

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```text
## 📊 Database Schemas

### Core Schema (01_core_schema.sql)

**Tables:**

- `users` - User accounts and profiles
- `roles` - Role-based access control
- `user_roles` - User-role associations
- `user_sessions` - Session management
- `learning_objectives` - Educational objectives
- `educational_content` - Content and lessons
- `content_objectives` - Content-objective relationships
- `quizzes` - Quiz definitions
- `quiz_questions` - Quiz questions
- `quiz_options` - Question options
- `quiz_attempts` - Student quiz attempts
- `user_progress` - Learning progress tracking

### AI Agents Schema (02_ai_agents_schema.sql)

**Tables:**

- `ai_agents` - AI agent definitions
- `agent_tasks` - Task management
- `agent_states` - SPARC framework states
- `agent_metrics` - Performance metrics
- `agent_communications` - Inter-agent communication
- `agent_learning_data` - Learning and adaptation
- `roblox_plugins` - Roblox Studio plugin management
- `roblox_scripts` - Generated Lua scripts
- `roblox_terrain` - Terrain configurations
- `roblox_game_sessions` - Game session tracking
- `roblox_player_sessions` - Player participation

### LMS Integration Schema (03_lms_integration_schema.sql)

**Tables:**

- `lms_integrations` - LMS platform configurations
- `lms_courses` - Course synchronization
- `lms_assignments` - Assignment integration
- `lms_grade_passbacks` - Grade passback tracking
- `lms_users` - User synchronization
- `lms_enrollments` - Enrollment management
- `websocket_connections` - Real-time connections
- `collaboration_sessions` - Live collaboration
- `collaboration_participants` - Session participants
- `collaboration_changes` - Change tracking

### Analytics Schema (04_analytics_schema.sql)

**Tables:**

- `usage_analytics` - Usage metrics and events
- `educational_analytics` - Learning insights
- `error_logs` - Error tracking and debugging
- `system_health_checks` - System monitoring
- `api_request_logs` - API usage tracking
- `notifications` - Notification system
- `achievements` - Gamification achievements
- `user_achievements` - User achievement tracking
- `leaderboards` - Leaderboard definitions
- `leaderboard_entries` - Leaderboard data

## 🔄 Migration Management

### Using Alembic

**Create a new migration:**

```bash
python database/migrate.py create "Add new feature"
```text
**Upgrade database:**

```bash
python database/migrate.py upgrade
```text
**Downgrade database:**

```bash
python database/migrate.py downgrade <revision>
```text
**View migration history:**

```bash
python database/migrate.py history
```text
**Check current revision:**

```bash
python database/migrate.py current
```text
### Direct Alembic Commands

```bash
cd database
alembic revision --autogenerate -m "Migration message"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```text
## 🔌 Connection Management

### Using the Connection Manager

```python
from database.connection_manager import get_session, get_async_session

# Synchronous session
with get_session('education') as session:
    # Your database operations
    pass

# Asynchronous session
async with get_async_session('education') as session:
    # Your async database operations
    pass
```text
### Available Databases

- `'education'` - Educational platform database
- `'ghost'` - Ghost backend database
- `'roblox'` - Roblox data database
- `'development'` - Development database

## 🏥 Health Monitoring

### Check Database Health

```bash
python database/connection_manager.py
```text
### Health Check Results

The health check will verify:

- ✅ PostgreSQL database connections
- ✅ Redis connection
- ✅ MongoDB connection (if configured)
- ✅ Database schema integrity

## 🛠️ Development Tools

### Create Development Data

```bash
python database/setup_database.py --dev-data
```text
### Reset Database

```bash
# Drop and recreate all tables
python -c "
from database.connection_manager import get_engine
from src.dashboard.backend.models import Base
engine = get_engine('education')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print('Database reset complete')
"
```text
### Database Backup

```bash
# Backup educational platform database
pg_dump -U eduplatform -h localhost educational_platform > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -U eduplatform -h localhost educational_platform < backup_file.sql
```text
## 📈 Performance Optimization

### Indexes

All schemas include optimized indexes for:

- Primary key lookups
- Foreign key relationships
- Frequently queried fields
- Full-text search
- Composite queries

### Materialized Views

- `mv_user_activity_summary` - User activity metrics
- `mv_content_performance` - Content performance data

### Connection Pooling

Configured with:

- Pool size: 10 connections
- Max overflow: 20 connections
- Connection recycling: 1 hour
- Pre-ping validation: Enabled

## 🔒 Security

### Database Security

- Role-based access control (RBAC)
- Encrypted password storage
- Session management with expiration
- Audit logging for all operations
- Soft delete functionality

### Connection Security

- SSL/TLS support for production
- Connection pooling with limits
- Rate limiting on API endpoints
- Input validation and sanitization

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if PostgreSQL is running
   - Verify connection parameters in `.env`
   - Check firewall settings

2. **Permission Denied**
   - Verify database user permissions
   - Check database ownership
   - Ensure user has CREATEDB privilege

3. **Migration Errors**
   - Check for conflicting migrations
   - Verify model definitions
   - Review Alembic configuration

4. **Performance Issues**
   - Check database indexes
   - Monitor connection pool usage
   - Review query performance

### Debug Mode

Enable debug mode in `.env`:

```env
EDU_DB_ECHO=true
DEBUG=true
```text
This will show all SQL queries and detailed error information.

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Redis Documentation](https://redis.io/documentation)

## 🤝 Contributing

When making database changes:

1. Create a new migration: `python database/migrate.py create "Description"`
2. Test the migration on development database
3. Update documentation if schema changes
4. Run health checks before committing
5. Coordinate with team for production deployments

## 📞 Support

For database-related issues:

1. Check the troubleshooting section above
2. Review the logs in `logs/` directory
3. Run health checks to identify issues
4. Contact the development team with specific error messages
