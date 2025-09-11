#!/usr/bin/env python3
"""
Migration script to create reports-related tables
Run this script to add report management functionality to the database
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine, init_db, check_database_health
from models import Base


def create_reports_tables():
    """Create reports-related tables"""
    
    print("🚀 Starting reports tables migration...")
    
    # Check database health
    if not check_database_health():
        print("❌ Database is not accessible. Please check your connection.")
        return False
    
    try:
        with engine.connect() as conn:
            # Create report_templates table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS report_templates (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    type VARCHAR(50) NOT NULL,
                    category VARCHAR(100),
                    icon VARCHAR(50),
                    fields JSON,
                    filters JSON,
                    default_format VARCHAR(20) DEFAULT 'pdf',
                    is_popular BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    data_sources JSON,
                    aggregations JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    CHECK (type IN ('progress', 'attendance', 'grades', 'behavior', 'assessment', 'compliance', 'gamification', 'custom')),
                    CHECK (default_format IN ('pdf', 'excel', 'csv', 'html', 'json'))
                );
            """))
            print("✅ Created report_templates table")
            
            # Create report_schedules table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS report_schedules (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    template_id VARCHAR(36) REFERENCES report_templates(id) ON DELETE CASCADE,
                    frequency VARCHAR(20) NOT NULL,
                    cron_expression VARCHAR(100),
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP,
                    next_run TIMESTAMP,
                    last_run TIMESTAMP,
                    hour INTEGER DEFAULT 9,
                    minute INTEGER DEFAULT 0,
                    day_of_week INTEGER,
                    day_of_month INTEGER,
                    format VARCHAR(20) DEFAULT 'pdf',
                    filters JSON,
                    parameters JSON,
                    school_id VARCHAR(36) REFERENCES schools(id) ON DELETE CASCADE,
                    class_id VARCHAR(36) REFERENCES classes(id) ON DELETE CASCADE,
                    recipients JSON,
                    auto_email BOOLEAN DEFAULT FALSE,
                    created_by VARCHAR(36) REFERENCES users(id),
                    is_active BOOLEAN DEFAULT TRUE,
                    failure_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    CHECK (frequency IN ('once', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
                    CHECK (format IN ('pdf', 'excel', 'csv', 'html', 'json')),
                    CHECK (hour >= 0 AND hour <= 23),
                    CHECK (minute >= 0 AND minute <= 59),
                    CHECK (day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)),
                    CHECK (day_of_month IS NULL OR (day_of_month >= 1 AND day_of_month <= 31))
                );
            """))
            print("✅ Created report_schedules table")
            
            # Create reports table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reports (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    format VARCHAR(20) NOT NULL DEFAULT 'pdf',
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    template_id VARCHAR(36) REFERENCES report_templates(id) ON DELETE SET NULL,
                    generated_by VARCHAR(36) REFERENCES users(id),
                    filters JSON,
                    parameters JSON,
                    school_id VARCHAR(36) REFERENCES schools(id) ON DELETE CASCADE,
                    class_id VARCHAR(36) REFERENCES classes(id) ON DELETE CASCADE,
                    file_path VARCHAR(500),
                    file_size INTEGER,
                    mime_type VARCHAR(100),
                    generated_at TIMESTAMP,
                    generation_time FLOAT,
                    error_message TEXT,
                    recipients JSON,
                    emailed_at TIMESTAMP,
                    schedule_id VARCHAR(36) REFERENCES report_schedules(id) ON DELETE SET NULL,
                    row_count INTEGER,
                    page_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    CHECK (type IN ('progress', 'attendance', 'grades', 'behavior', 'assessment', 'compliance', 'gamification', 'custom')),
                    CHECK (format IN ('pdf', 'excel', 'csv', 'html', 'json')),
                    CHECK (status IN ('pending', 'generating', 'ready', 'failed', 'scheduled', 'cancelled'))
                );
            """))
            print("✅ Created reports table")
            
            # Create report_generations table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS report_generations (
                    id VARCHAR(36) PRIMARY KEY,
                    report_id VARCHAR(36) REFERENCES reports(id) ON DELETE CASCADE,
                    schedule_id VARCHAR(36) REFERENCES report_schedules(id) ON DELETE CASCADE,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    duration_seconds FLOAT,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    records_processed INTEGER,
                    memory_usage_mb FLOAT,
                    triggered_by VARCHAR(36) REFERENCES users(id),
                    is_manual BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    CHECK (status IN ('pending', 'generating', 'ready', 'failed', 'scheduled', 'cancelled'))
                );
            """))
            print("✅ Created report_generations table")
            
            # Create indexes for better performance
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_generated_by ON reports(generated_by);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_school_id ON reports(school_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_class_id ON reports(class_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_report_schedules_active ON report_schedules(is_active);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_report_templates_popular ON report_templates(is_popular);"))
            print("✅ Created indexes for reports tables")
            
            # Insert default report templates
            conn.execute(text("""
                INSERT INTO report_templates (id, name, description, type, category, icon, fields, is_popular, is_active)
                VALUES 
                    ('11111111-1111-1111-1111-111111111111', 'Student Progress Report', 
                     'Comprehensive progress tracking including XP, levels, and achievements', 
                     'progress', 'Academic', 'TrendingUp', 
                     '["Student Name", "Class", "XP Earned", "Level", "Badges", "Completion Rate"]'::json,
                     true, true),
                    
                    ('22222222-2222-2222-2222-222222222222', 'Class Performance Summary', 
                     'Overall class performance metrics and comparisons', 
                     'grades', 'Academic', 'School', 
                     '["Class Name", "Average Score", "Top Performers", "Areas for Improvement"]'::json,
                     true, true),
                    
                    ('33333333-3333-3333-3333-333333333333', 'Individual Student Report Card', 
                     'Traditional report card with grades and teacher comments', 
                     'grades', 'Grades', 'Description', 
                     '["Subject", "Grade", "Teacher Comments", "Attendance", "Behavior"]'::json,
                     false, true),
                    
                    ('44444444-4444-4444-4444-444444444444', 'Roblox Activity Report', 
                     'Gaming platform engagement and educational game progress', 
                     'gamification', 'Gamification', 'EmojiEvents', 
                     '["Game Sessions", "Time Played", "Achievements", "Skills Developed"]'::json,
                     true, true),
                    
                    ('55555555-5555-5555-5555-555555555555', 'Parent Communication Log', 
                     'Record of parent-teacher communications and meetings', 
                     'custom', 'Communication', 'People', 
                     '["Date", "Parent Name", "Discussion Topics", "Action Items", "Follow-up"]'::json,
                     false, true),
                    
                    ('66666666-6666-6666-6666-666666666666', 'Compliance Audit Report', 
                     'COPPA, FERPA, and GDPR compliance status', 
                     'compliance', 'Compliance', 'Assessment', 
                     '["Regulation", "Status", "Issues", "Remediation", "Audit Date"]'::json,
                     false, true)
                ON CONFLICT (id) DO NOTHING;
            """))
            print("✅ Inserted default report templates")
            
            conn.commit()
            
        print("✅ Reports tables migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def rollback_reports_tables():
    """Rollback reports tables migration"""
    print("⚠️  Rolling back reports tables...")
    
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS report_generations CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS reports CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS report_schedules CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS report_templates CASCADE;"))
            conn.commit()
            
        print("✅ Rollback completed")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_reports_tables()
    else:
        create_reports_tables()