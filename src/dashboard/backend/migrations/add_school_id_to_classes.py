"""
Add school_id column to classes table
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/toolboxai")

def upgrade():
    """Add school_id column to classes table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'classes' AND column_name = 'school_id'
        """))
        
        if result.rowcount == 0:
            # Add school_id column
            conn.execute(text("""
                ALTER TABLE classes 
                ADD COLUMN school_id VARCHAR(36) 
                REFERENCES schools(id) ON DELETE SET NULL
            """))
            conn.commit()
            print("✅ Added school_id column to classes table")
        else:
            print("ℹ️ school_id column already exists in classes table")

def downgrade():
    """Remove school_id column from classes table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE classes DROP COLUMN IF EXISTS school_id"))
        conn.commit()
        print("✅ Removed school_id column from classes table")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()