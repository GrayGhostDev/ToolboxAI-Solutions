"""
Create schools table and add school_id to users table
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/toolboxai")

def upgrade():
    """Create schools table and add school_id column to users table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if schools table exists
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'schools'
        """))
        
        if result.rowcount == 0:
            # Create schools table
            conn.execute(text("""
                CREATE TABLE schools (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    address VARCHAR(500) NOT NULL,
                    city VARCHAR(100) NOT NULL,
                    state VARCHAR(50) NOT NULL,
                    zip_code VARCHAR(10) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    principal_name VARCHAR(100),
                    district VARCHAR(200),
                    student_count INTEGER DEFAULT 0,
                    teacher_count INTEGER DEFAULT 0,
                    class_count INTEGER DEFAULT 0,
                    max_students INTEGER DEFAULT 500 NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE
                )
            """))
            conn.commit()
            print("✅ Created schools table")
            
            # Create index on name and city
            conn.execute(text("CREATE INDEX idx_schools_name ON schools(name)"))
            conn.execute(text("CREATE INDEX idx_schools_city ON schools(city)"))
            conn.commit()
            print("✅ Created indexes on schools table")
        else:
            print("ℹ️ schools table already exists")
        
        # Check if school_id column exists in users table
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'school_id'
        """))
        
        if result.rowcount == 0:
            # Add school_id column to users table
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN school_id VARCHAR(36) 
                REFERENCES schools(id) ON DELETE SET NULL
            """))
            conn.commit()
            print("✅ Added school_id column to users table")
        else:
            print("ℹ️ school_id column already exists in users table")

def downgrade():
    """Remove school_id column and schools table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Remove school_id column from users table
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS school_id"))
        conn.commit()
        print("✅ Removed school_id column from users table")
        
        # Drop schools table
        conn.execute(text("DROP TABLE IF EXISTS schools CASCADE"))
        conn.commit()
        print("✅ Dropped schools table")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()