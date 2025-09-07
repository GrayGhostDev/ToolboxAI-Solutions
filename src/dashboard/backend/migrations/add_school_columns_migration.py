#!/usr/bin/env python3
"""
Migration to add missing columns to the schools table
These columns are defined in the School model but were missing from the initial migration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine, check_database_health


def upgrade():
    """Add missing columns to schools table"""
    
    print("🚀 Starting school columns migration...")
    
    # Check database health
    if not check_database_health():
        print("❌ Database is not accessible. Please check your connection.")
        return False
    
    try:
        with engine.connect() as conn:
            # Check which columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'schools'
            """))
            
            existing_columns = {row[0] for row in result}
            print(f"📊 Existing columns: {existing_columns}")
            
            # Add logo_url column if it doesn't exist
            if 'logo_url' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE schools 
                    ADD COLUMN logo_url VARCHAR(500)
                """))
                print("✅ Added logo_url column")
            else:
                print("ℹ️  logo_url column already exists")
            
            # Add website column if it doesn't exist
            if 'website' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE schools 
                    ADD COLUMN website VARCHAR(500)
                """))
                print("✅ Added website column")
            else:
                print("ℹ️  website column already exists")
            
            # Add founded_year column if it doesn't exist
            if 'founded_year' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE schools 
                    ADD COLUMN founded_year INTEGER
                """))
                print("✅ Added founded_year column")
            else:
                print("ℹ️  founded_year column already exists")
            
            # Add school_type column if it doesn't exist
            if 'school_type' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE schools 
                    ADD COLUMN school_type VARCHAR(50)
                """))
                print("✅ Added school_type column")
            else:
                print("ℹ️  school_type column already exists")
            
            # Add grade_levels column if it doesn't exist
            if 'grade_levels' not in existing_columns:
                conn.execute(text("""
                    ALTER TABLE schools 
                    ADD COLUMN grade_levels VARCHAR(100)
                """))
                print("✅ Added grade_levels column")
            else:
                print("ℹ️  grade_levels column already exists")
            
            # Commit the changes
            conn.commit()
            
        print("✅ School columns migration completed successfully!")
        
        # Display the updated table structure
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'schools'
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Updated schools table structure:")
            for row in result:
                nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
                print(f"  - {row[0]}: {row[1]} {nullable}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def downgrade():
    """Remove the added columns from schools table"""
    
    print("⚠️  Rolling back school columns...")
    
    try:
        with engine.connect() as conn:
            # Remove the added columns
            conn.execute(text("""
                ALTER TABLE schools 
                DROP COLUMN IF EXISTS logo_url,
                DROP COLUMN IF EXISTS website,
                DROP COLUMN IF EXISTS founded_year,
                DROP COLUMN IF EXISTS school_type,
                DROP COLUMN IF EXISTS grade_levels
            """))
            conn.commit()
            
        print("✅ Rollback completed")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()