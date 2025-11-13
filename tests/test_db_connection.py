#!/usr/bin/env python3
"""
Quick test script to verify Supabase database connection
"""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("SUPABASE DATABASE CONNECTION TEST")
print("=" * 60)

# Test 1: Check environment variables
print("\n1. Checking Environment Variables...")
supabase_url = os.getenv("SUPABASE_URL")
database_url = os.getenv("DATABASE_URL")
direct_url = os.getenv("DIRECT_URL")

print(f"   SUPABASE_URL: {supabase_url}")
print(f"   DATABASE_URL: {database_url[:50]}..." if database_url else "   DATABASE_URL: NOT SET")
print(f"   DIRECT_URL: {direct_url[:50]}..." if direct_url else "   DIRECT_URL: NOT SET")

if not database_url:
    print("\n❌ ERROR: DATABASE_URL not set in .env file")
    sys.exit(1)

# Test 2: Test Supabase Python Client
print("\n2. Testing Supabase Python Client...")
try:
    from supabase import create_client

    supabase_anon = os.getenv("SUPABASE_ANON_KEY")
    supabase_service = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if supabase_url and supabase_service:
        client = create_client(supabase_url, supabase_service)
        # Try to query users table
        result = client.table("users").select("*").limit(1).execute()
        print(f"   ✅ Supabase client connected successfully")
        print(f"   ✅ Users table accessible (found {len(result.data)} rows)")
    else:
        print("   ⚠️  Supabase credentials not found")
except Exception as e:
    print(f"   ❌ Supabase client error: {e}")

# Test 3: Test SQLAlchemy Connection
print("\n3. Testing SQLAlchemy Connection...")
try:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"   ✅ SQLAlchemy connected successfully")
        print(f"   ✅ PostgreSQL version: {version[:50]}")

        # Test if tables exist
        result = conn.execute(
            text(
                """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'courses', 'lessons')
            ORDER BY table_name
        """
            )
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"   ✅ Found tables: {', '.join(tables) if tables else 'NONE'}")

        if "courses" in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM courses"))
            count = result.fetchone()[0]
            print(f"   ✅ Courses table has {count} rows")

except Exception as e:
    print(f"   ❌ SQLAlchemy connection error: {e}")
    print(f"   💡 This might be a network issue or incorrect credentials")

# Test 4: Test Direct URL Connection
if direct_url:
    print("\n4. Testing Direct URL Connection...")
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(direct_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"   ✅ Direct URL connection successful")
    except Exception as e:
        print(f"   ❌ Direct URL connection error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("- If SQLAlchemy works: Your courses API should work!")
print("- If Supabase client works but SQLAlchemy doesn't: Use simplified router")
print("- If neither works: Check network/firewall settings")
print()
