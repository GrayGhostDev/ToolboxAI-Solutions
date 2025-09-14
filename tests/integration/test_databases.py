import asyncio
import os
import asyncpg
import pytest
from datetime import datetime

# Skip all tests in this module as they require external services
pytestmark = pytest.mark.skipif(
    not os.environ.get('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable"
)

async def test_databases():
    """Test all database connections with real queries"""
    
    databases = {
        "ghost_backend": "postgresql://grayghostdata:securepass123@localhost/ghost_backend",
        "educational_platform": "postgresql://grayghostdata:securepass123@localhost/educational_platform",
        "roblox_data": "postgresql://grayghostdata:securepass123@localhost/roblox_data",
        "mcp_memory": "postgresql://grayghostdata:securepass123@localhost/mcp_memory"
    }
    
    results = {}
    
    for db_name, connection_string in databases.items():
        try:
            conn = await asyncpg.connect(connection_string)
            
            # Test basic connectivity
            version = await conn.fetchval('SELECT version()')
            
            # Get table count
            table_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            # Get row counts for key tables
            row_counts = {}
            if db_name == "educational_platform":
                try:
                    row_counts["users"] = await conn.fetchval("SELECT COUNT(*) FROM users")
                except:
                    row_counts["users"] = "Table not found"
                try:
                    row_counts["lessons"] = await conn.fetchval("SELECT COUNT(*) FROM lessons")
                except:
                    row_counts["lessons"] = "Table not found"
                try:
                    row_counts["classes"] = await conn.fetchval("SELECT COUNT(*) FROM classes")
                except:
                    row_counts["classes"] = "Table not found"
            
            await conn.close()
            
            results[db_name] = {
                "status": "✅ Connected",
                "tables": table_count,
                "row_counts": row_counts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            results[db_name] = {
                "status": f"❌ Failed",
                "error": str(e)
            }
    
    return results

# Run the test
results = asyncio.run(test_databases())
for db, info in results.items():
    print(f"\n{db}:")
    for key, value in info.items():
        print(f"  {key}: {value}")