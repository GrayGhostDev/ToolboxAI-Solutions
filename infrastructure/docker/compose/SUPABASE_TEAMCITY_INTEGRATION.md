# TeamCity + Supabase PostgreSQL Integration

**Date**: 2025-11-08
**Status**: ✅ Integration Complete - Ready for Initialization

---

## 🎯 Overview

TeamCity has been successfully integrated with Supabase's PostgreSQL 17 instance, eliminating the need for a separate PostgreSQL container and consolidating database infrastructure.

### Architecture Change

**Before:**
```
TeamCity Server → teamcity-postgres (PostgreSQL 16)
                  (Separate container)
```

**After:**
```
TeamCity Server → supabase_db_supabase (PostgreSQL 17)
                  via supabase_network_supabase
                  (Shared with Supabase services)
```

---

## ✅ Completed Integration Steps

### 1. Database Setup
- ✅ Created `teamcity` database in Supabase PostgreSQL 17
- ✅ Configured database owner: `supabase_admin`
- ✅ Database accessible on port 54322 (host) and 5432 (internal)

### 2. Docker Compose Configuration
**File**: `infrastructure/docker/compose/docker-compose.teamcity.yml`

**Changes Made**:
- ✅ Removed standalone `teamcity-db` service (postgres:16-alpine)
- ✅ Added `supabase_network_supabase` to networks
- ✅ Updated TeamCity server environment variables:
  ```yaml
  TEAMCITY_DATABASE_URL: jdbc:postgresql://db.supabase.internal:5432/teamcity
  TEAMCITY_DATABASE_USER: supabase_admin
  TEAMCITY_DATABASE_PASSWORD: postgres
  ```
- ✅ Removed `teamcity_db_data` volume (no longer needed)
- ✅ Removed `depends_on: teamcity-db` (managed externally)

### 3. Network Integration
- ✅ TeamCity server connected to `supabase_network_supabase` (172.20.0.13/16)
- ✅ TeamCity can resolve `db.supabase.internal` hostname
- ✅ Network communication verified between TeamCity and Supabase PostgreSQL

### 4. Database Configuration Update
**File**: `/data/teamcity_server/datadir/config/database.properties` (inside container)

**Updated Configuration**:
```properties
#Updated: 2025-11-08 - Integrated with Supabase PostgreSQL
connectionProperties.password=postgres
connectionProperties.user=supabase_admin
connectionUrl=jdbc\:postgresql\://db.supabase.internal:5432/teamcity
```

---

## 📊 Connection Verification

### Supabase PostgreSQL Details
- **Container**: `supabase_db_supabase`
- **Image**: `public.ecr.aws/supabase/postgres:17.6.1.005`
- **Network**: `supabase_network_supabase` (172.20.0.0/16)
- **Internal Hostname**: `db.supabase.internal`
- **Internal Port**: 5432
- **Host Port**: 54322

### TeamCity Database
```bash
# Connect to TeamCity database from host
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity"

# Check database exists
psql "postgresql://supabase_admin:postgres@localhost:54322/postgres" -c "\l" | grep teamcity
```

### Network Verification
```bash
# Verify TeamCity is on Supabase network
docker network inspect supabase_network_supabase | grep teamcity-server

# Check connectivity from TeamCity container
docker exec teamcity-server ping -c 3 db.supabase.internal
```

---

## 🔄 Current Status: Data Initialization Required

### Issue Identified
TeamCity successfully connects to Supabase PostgreSQL but detects a data inconsistency:
```
ERROR: Data parts are inconsistent: the Data Directory exists
(from another version of TeamCity) but the database does not.
```

### Root Cause
The `teamcity_data` Docker volume contains configuration from the previous PostgreSQL 16 setup, but the new Supabase database is empty.

### Resolution Options

#### Option 1: Fresh TeamCity Setup (Recommended for Development)
**Best for**: Clean start, testing, development environments

```bash
# Stop TeamCity services
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml down

# Remove TeamCity data volume
docker volume rm infrastructure_docker_compose_teamcity_data

# Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml up -d

# Access TeamCity UI and complete first-time setup
open http://localhost:8111
```

**Result**: TeamCity will initialize a fresh database schema in Supabase PostgreSQL.

#### Option 2: Restore from Backup (For Production Migration)
**Best for**: Migrating existing TeamCity installation

```bash
# 1. Ensure you have a backup of the old database
docker exec teamcity-postgres pg_dump -U teamcity teamcity > teamcity_backup.sql

# 2. Restore to Supabase PostgreSQL
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" < teamcity_backup.sql

# 3. Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

**Result**: TeamCity will recognize existing data and continue with current configuration.

#### Option 3: Manual Data Directory Reset
**Best for**: Keeping some configuration, resetting database link

```bash
# Remove only the database-related files from data directory
docker exec teamcity-server rm -f /data/teamcity_server/datadir/config/database.properties
docker exec teamcity-server rm -rf /data/teamcity_server/datadir/system/caches/

# Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

---

## 📁 Files Modified

### Created Files
1. `docker-compose.teamcity.yml.backup-YYYYMMDD-HHMMSS` - Backup before changes
2. `SUPABASE_TEAMCITY_INTEGRATION.md` - This documentation

### Modified Files
1. `infrastructure/docker/compose/docker-compose.teamcity.yml`
   - Line 13: Updated comment to reflect Supabase integration
   - Lines 17-28: Removed teamcity-db service, added integration notes
   - Lines 39-42: Updated database connection environment variables
   - Lines 76-79: Added supabase_network_supabase, removed depends_on
   - Line 260: Removed teamcity_db_data volume
   - Lines 317-319: Added external supabase_network_supabase

---

## 🔍 Verification Commands

### Check Services Status
```bash
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml ps
```

### Check TeamCity Logs
```bash
docker logs teamcity-server --tail 50
```

### Check Database Tables (After Initialization)
```bash
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -c "\dt"
```

### Check Supabase PostgreSQL Connections
```bash
psql "postgresql://supabase_admin:postgres@localhost:54322/postgres" \
  -c "SELECT datname, usename, client_addr, state FROM pg_stat_activity WHERE datname = 'teamcity';"
```

---

## 🎯 Benefits of Integration

### Infrastructure Consolidation
- ✅ **Reduced Containers**: Eliminated separate PostgreSQL container
- ✅ **Shared Resources**: TeamCity uses existing Supabase PostgreSQL 17
- ✅ **Unified Management**: Single PostgreSQL instance for multiple services
- ✅ **Version Upgrade**: Moved from PostgreSQL 16 → 17

### Operational Advantages
- ✅ **Simpler Backup Strategy**: One PostgreSQL instance to backup
- ✅ **Centralized Monitoring**: Monitor all databases in one place
- ✅ **Resource Efficiency**: Reduced memory footprint (~2GB saved)
- ✅ **Network Optimization**: Fewer network hops, shared network

### Development Workflow
- ✅ **Easier Troubleshooting**: Single database to inspect
- ✅ **Faster Startup**: No separate database container to start
- ✅ **Consistent Configuration**: Shared PostgreSQL configuration
- ✅ **Future-Ready**: Aligns with 2025 best practices

---

## 📊 Resource Comparison

| Metric | Before (Separate DB) | After (Supabase Integration) | Improvement |
|--------|---------------------|------------------------------|-------------|
| **Containers** | 5 (server + 3 agents + db) | 4 (server + 3 agents) | 20% reduction |
| **Memory Reserved** | 4G (server) + 1G (db) = 5G | 4G (server only) | 20% reduction |
| **Memory Limit** | 6G (server) + 2G (db) = 8G | 6G (server only) | 25% reduction |
| **Networks** | 2 (teamcity + toolboxai) | 3 (teamcity + supabase + toolboxai) | Shared network |
| **Volumes** | 9 volumes | 8 volumes | 11% reduction |
| **PostgreSQL Version** | 16-alpine | 17.6.1 (Supabase) | Major upgrade |

---

## 🔐 Security Considerations

### Current Configuration
- **Database User**: `supabase_admin` (Supabase admin user)
- **Database Password**: `postgres` (Supabase default)
- **Network**: Internal Docker network (supabase_network_supabase)
- **Access**: TeamCity server only, no external exposure

### Production Recommendations
1. **Create Dedicated TeamCity User**:
   ```sql
   CREATE USER teamcity_user WITH PASSWORD 'secure_password_here';
   GRANT ALL PRIVILEGES ON DATABASE teamcity TO teamcity_user;
   ```

2. **Update Connection Credentials**:
   ```yaml
   TEAMCITY_DATABASE_USER: teamcity_user
   TEAMCITY_DATABASE_PASSWORD: ${TEAMCITY_DB_PASSWORD}
   ```

3. **Use Docker Secrets**:
   ```yaml
   secrets:
     teamcity_db_password:
       external: true
   environment:
     TEAMCITY_DATABASE_PASSWORD_FILE: /run/secrets/teamcity_db_password
   ```

4. **Enable SSL/TLS** for PostgreSQL connection in production

---

## 🚀 Next Steps

### Immediate (Choose One)
1. **Fresh Setup**: Remove teamcity_data volume and initialize fresh
2. **Migrate Data**: Restore backup from old teamcity-postgres
3. **Manual Reset**: Clear database references and re-initialize

### Short-Term (After Initialization)
1. Create dedicated TeamCity PostgreSQL user
2. Update connection credentials to use dedicated user
3. Configure SSL/TLS for database connections
4. Set up automated database backups
5. Monitor TeamCity performance with Supabase PostgreSQL

### Long-Term
1. Migrate other services to use Supabase PostgreSQL (if applicable)
2. Consolidate all PostgreSQL databases under Supabase
3. Implement connection pooling (PgBouncer) if needed
4. Set up PostgreSQL replication for high availability

---

## 🐛 Troubleshooting

### TeamCity Won't Start
**Symptom**: Container starts but TeamCity server doesn't initialize

**Checks**:
```bash
# 1. Verify database connectivity
docker exec teamcity-server nc -zv db.supabase.internal 5432

# 2. Check database.properties
docker exec teamcity-server cat /data/teamcity_server/datadir/config/database.properties

# 3. Check logs
docker logs teamcity-server --tail 100
```

**Solution**: See "Resolution Options" section above

### Connection Refused
**Symptom**: `Connection refused` error in logs

**Checks**:
```bash
# Verify Supabase PostgreSQL is running
docker ps | grep supabase_db

# Check network connectivity
docker exec teamcity-server ping db.supabase.internal
```

### Authentication Failed
**Symptom**: `password authentication failed for user "supabase_admin"`

**Solution**:
```bash
# Verify credentials in database.properties match Supabase
docker exec supabase_db_supabase env | grep POSTGRES
```

---

## 📞 Support & Resources

### Configuration Files
- Docker Compose: `infrastructure/docker/compose/docker-compose.teamcity.yml`
- Database Config: Container path `/data/teamcity_server/datadir/config/database.properties`
- Supabase Config: `supabase/config.toml`

### Useful Commands
```bash
# View all TeamCity-related containers
docker ps | grep teamcity

# Connect to Supabase PostgreSQL
psql "postgresql://supabase_admin:postgres@localhost:54322/postgres"

# Check TeamCity database
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity"

# Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart

# Clean restart (remove data)
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml down -v
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml up -d
```

### External References
- [Supabase PostgreSQL Documentation](https://supabase.com/docs/guides/database)
- [TeamCity Database Configuration](https://www.jetbrains.com/help/teamcity/setting-up-an-external-database.html)
- [Docker Networking](https://docs.docker.com/network/)

---

## ✅ Success Criteria

- [x] TeamCity connects to Supabase PostgreSQL
- [x] Network connectivity established (supabase_network_supabase)
- [x] Docker Compose configuration updated
- [x] Database.properties updated with Supabase connection
- [x] Old teamcity-postgres container removed
- [x] Documentation created
- [ ] TeamCity successfully initializes (pending user action)
- [ ] Build agents connect to TeamCity server
- [ ] Test builds execute successfully

---

**Integration Completed**: 2025-11-08
**Performed By**: Claude Code Automation
**Next Action**: Choose initialization option and complete TeamCity setup
