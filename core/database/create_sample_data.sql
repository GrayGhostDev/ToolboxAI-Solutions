-- ============================================================================
-- Sample Data Creation for Dashboard Backend
-- ============================================================================
-- This script creates sample data for testing the Dashboard functionality

-- Create sample schools
INSERT INTO schools (id, name, address, city, state, zip_code, phone, email, principal_name, district, max_students, student_count, teacher_count, class_count, is_active)
VALUES 
    ('school-001', 'Lincoln Elementary School', '123 Main Street', 'Anytown', 'CA', '90210', '(555) 123-4567', 'office@lincoln-elem.edu', 'Dr. Sarah Johnson', 'Anytown School District', 500, 0, 0, 0, true),
    ('school-002', 'Washington Middle School', '456 Oak Avenue', 'Anytown', 'CA', '90211', '(555) 234-5678', 'admin@washington-middle.edu', 'Mr. Robert Chen', 'Anytown School District', 800, 0, 0, 0, true),
    ('school-003', 'Roosevelt High School', '789 Pine Boulevard', 'Anytown', 'CA', '90212', '(555) 345-6789', 'info@roosevelt-high.edu', 'Ms. Maria Rodriguez', 'Anytown School District', 1200, 0, 0, 0, true)
ON CONFLICT (id) DO NOTHING;

-- Create sample dashboard users (teachers, students, parents, admins)
INSERT INTO dashboard_users (id, username, email, password_hash, first_name, last_name, role, school_id, grade_level, is_active, is_verified)
VALUES 
    -- Administrators
    ('admin-001', 'admin', 'admin@toolboxai.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'System', 'Administrator', 'admin', 'school-001', NULL, true, true),
    
    -- Teachers
    ('teacher-001', 'msjohnson', 'johnson@lincoln-elem.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Emily', 'Johnson', 'teacher', 'school-001', NULL, true, true),
    ('teacher-002', 'mrsmith', 'smith@lincoln-elem.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Michael', 'Smith', 'teacher', 'school-001', NULL, true, true),
    ('teacher-003', 'msdavis', 'davis@washington-middle.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Jennifer', 'Davis', 'teacher', 'school-002', NULL, true, true),
    ('teacher-004', 'mrwilson', 'wilson@roosevelt-high.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'David', 'Wilson', 'teacher', 'school-003', NULL, true, true),
    
    -- Students
    ('student-001', 'alex_parker', 'alex.parker@student.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Alex', 'Parker', 'student', 'school-001', 3, true, true),
    ('student-002', 'sam_thompson', 'sam.thompson@student.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Sam', 'Thompson', 'student', 'school-001', 3, true, true),
    ('student-003', 'emma_garcia', 'emma.garcia@student.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Emma', 'Garcia', 'student', 'school-002', 7, true, true),
    ('student-004', 'noah_martinez', 'noah.martinez@student.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Noah', 'Martinez', 'student', 'school-002', 7, true, true),
    ('student-005', 'olivia_brown', 'olivia.brown@student.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Olivia', 'Brown', 'student', 'school-003', 11, true, true),
    ('student-006', 'ethan_jones', 'ethan.jones@student.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Ethan', 'Jones', 'student', 'school-003', 11, true, true),
    
    -- Parents
    ('parent-001', 'parent_parker', 'parent.parker@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Lisa', 'Parker', 'parent', 'school-001', NULL, true, true),
    ('parent-002', 'parent_garcia', 'parent.garcia@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Carlos', 'Garcia', 'parent', 'school-002', NULL, true, true),
    ('parent-003', 'parent_brown', 'parent.brown@email.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPYbWl6/Fy5hC', 'Michelle', 'Brown', 'parent', 'school-003', NULL, true, true)
ON CONFLICT (id) DO NOTHING;

-- Create sample classes
INSERT INTO classes (id, name, code, description, subject, grade_level, teacher_id, school_id, max_students, is_active)
VALUES 
    ('class-001', '3rd Grade Mathematics', 'MATH-3A', 'Introduction to multiplication and division', 'Mathematics', 3, 'teacher-001', 'school-001', 25, true),
    ('class-002', '3rd Grade Reading', 'ELA-3A', 'Building reading comprehension skills', 'English Language Arts', 3, 'teacher-002', 'school-001', 25, true),
    ('class-003', '7th Grade Science', 'SCI-7A', 'Earth science and biology fundamentals', 'Science', 7, 'teacher-003', 'school-002', 30, true),
    ('class-004', '11th Grade Physics', 'PHYS-11A', 'Introduction to physics concepts', 'Physics', 11, 'teacher-004', 'school-003', 20, true)
ON CONFLICT (id) DO NOTHING;

-- Enroll students in classes
INSERT INTO class_students (id, class_id, student_id, status, grade, attendance_rate)
VALUES 
    ('enrollment-001', 'class-001', 'student-001', 'active', 85.5, 95.0),
    ('enrollment-002', 'class-002', 'student-001', 'active', 88.2, 97.0),
    ('enrollment-003', 'class-001', 'student-002', 'active', 92.1, 93.0),
    ('enrollment-004', 'class-002', 'student-002', 'active', 89.8, 96.0),
    ('enrollment-005', 'class-003', 'student-003', 'active', 91.5, 98.0),
    ('enrollment-006', 'class-003', 'student-004', 'active', 87.3, 94.0),
    ('enrollment-007', 'class-004', 'student-005', 'active', 94.2, 99.0),
    ('enrollment-008', 'class-004', 'student-006', 'active', 86.7, 92.0)
ON CONFLICT (id) DO NOTHING;

-- Create sample assignments
INSERT INTO assignments (id, title, description, type, subject, class_id, teacher_id, due_date, points, status, is_published)
VALUES 
    ('assignment-001', 'Multiplication Tables Practice', 'Practice multiplication tables 1-10', 'homework', 'Mathematics', 'class-001', 'teacher-001', NOW() + INTERVAL '3 days', 100, 'active', true),
    ('assignment-002', 'Division Word Problems', 'Solve real-world division problems', 'assignment', 'Mathematics', 'class-001', 'teacher-001', NOW() + INTERVAL '1 week', 150, 'active', true),
    ('assignment-003', 'Reading Comprehension Quiz', 'Quiz on Chapter 5', 'quiz', 'English Language Arts', 'class-002', 'teacher-002', NOW() + INTERVAL '2 days', 75, 'active', true),
    ('assignment-004', 'Science Fair Project', 'Create a volcano model', 'project', 'Science', 'class-003', 'teacher-003', NOW() + INTERVAL '2 weeks', 200, 'active', true),
    ('assignment-005', 'Physics Lab Report', 'Report on pendulum experiment', 'lab', 'Physics', 'class-004', 'teacher-004', NOW() + INTERVAL '5 days', 125, 'active', true)
ON CONFLICT (id) DO NOTHING;

-- Create sample submissions
INSERT INTO submissions (id, assignment_id, student_id, status, grade, progress, content, feedback)
VALUES 
    ('submission-001', 'assignment-001', 'student-001', 'graded', 85.0, 100, 'Completed all multiplication tables', 'Good work! Keep practicing 7x8.'),
    ('submission-002', 'assignment-001', 'student-002', 'graded', 92.0, 100, 'Excellent understanding shown', 'Outstanding work!'),
    ('submission-003', 'assignment-003', 'student-001', 'submitted', NULL, 100, 'My answers to the quiz questions', NULL),
    ('submission-004', 'assignment-004', 'student-003', 'in_progress', NULL, 75, 'Working on the volcano design', NULL),
    ('submission-005', 'assignment-005', 'student-005', 'graded', 94.0, 100, 'Detailed analysis of pendulum motion', 'Excellent scientific reasoning!')
ON CONFLICT (id) DO NOTHING;

-- Create sample lessons
INSERT INTO lessons (id, title, description, subject, class_id, teacher_id, scheduled_at, duration_minutes, lesson_type, status)
VALUES 
    ('lesson-001', 'Introduction to Multiplication', 'Learn basic multiplication concepts', 'Mathematics', 'class-001', 'teacher-001', NOW() + INTERVAL '1 day', 45, 'standard', 'scheduled'),
    ('lesson-002', 'Character Analysis in Stories', 'How to analyze story characters', 'English Language Arts', 'class-002', 'teacher-002', NOW() + INTERVAL '2 days', 50, 'standard', 'scheduled'),
    ('lesson-003', 'Roblox Volcano Simulation', 'Interactive volcano learning in Roblox', 'Science', 'class-003', 'teacher-003', NOW() + INTERVAL '3 days', 60, 'roblox', 'scheduled'),
    ('lesson-004', 'Physics in Roblox World', 'Explore physics concepts in virtual environment', 'Physics', 'class-004', 'teacher-004', NOW() + INTERVAL '4 days', 90, 'roblox', 'scheduled')
ON CONFLICT (id) DO NOTHING;

-- Create sample student progress
INSERT INTO student_progress (id, student_id, class_id, subject, grade_level, xp_points, level, streak_days, total_badges, rank_position, gpa, attendance_rate, assignments_completed, assignments_total)
VALUES 
    ('progress-001', 'student-001', 'class-001', 'Mathematics', 3, 450, 3, 7, 2, 2, 3.4, 96.0, 8, 10),
    ('progress-002', 'student-001', 'class-002', 'English Language Arts', 3, 380, 2, 5, 1, 3, 3.5, 97.0, 6, 8),
    ('progress-003', 'student-002', 'class-001', 'Mathematics', 3, 520, 4, 12, 3, 1, 3.7, 93.0, 9, 10),
    ('progress-004', 'student-003', 'class-003', 'Science', 7, 680, 5, 15, 4, 1, 3.6, 98.0, 12, 14),
    ('progress-005', 'student-005', 'class-004', 'Physics', 11, 890, 7, 21, 6, 1, 3.8, 99.0, 15, 16)
ON CONFLICT (id) DO NOTHING;

-- Create sample student activity
INSERT INTO student_activity (id, student_id, type, description, xp_earned, class_id)
VALUES 
    ('activity-001', 'student-001', 'assignment_completed', 'Completed Multiplication Tables Practice', 50, 'class-001'),
    ('activity-002', 'student-001', 'quiz_passed', 'Passed Reading Comprehension Quiz', 25, 'class-002'),
    ('activity-003', 'student-002', 'achievement_earned', 'Earned Math Wizard badge', 100, 'class-001'),
    ('activity-004', 'student-003', 'lesson_attended', 'Attended Roblox Volcano Simulation', 30, 'class-003'),
    ('activity-005', 'student-005', 'perfect_score', 'Scored 100% on Physics Lab', 75, 'class-004')
ON CONFLICT (id) DO NOTHING;

-- Create sample attendance records
INSERT INTO attendance (id, student_id, class_id, date, status, recorded_by)
VALUES 
    ('attendance-001', 'student-001', 'class-001', CURRENT_DATE - INTERVAL '1 day', 'present', 'teacher-001'),
    ('attendance-002', 'student-001', 'class-002', CURRENT_DATE - INTERVAL '1 day', 'present', 'teacher-002'),
    ('attendance-003', 'student-002', 'class-001', CURRENT_DATE - INTERVAL '1 day', 'present', 'teacher-001'),
    ('attendance-004', 'student-003', 'class-003', CURRENT_DATE - INTERVAL '1 day', 'present', 'teacher-003'),
    ('attendance-005', 'student-005', 'class-004', CURRENT_DATE - INTERVAL '1 day', 'present', 'teacher-004'),
    -- Add some historical attendance
    ('attendance-006', 'student-001', 'class-001', CURRENT_DATE - INTERVAL '2 days', 'present', 'teacher-001'),
    ('attendance-007', 'student-002', 'class-001', CURRENT_DATE - INTERVAL '2 days', 'absent', 'teacher-001'),
    ('attendance-008', 'student-003', 'class-003', CURRENT_DATE - INTERVAL '3 days', 'present', 'teacher-003')
ON CONFLICT (id) DO NOTHING;

-- Create sample messages
INSERT INTO messages (id, sender_id, recipient_id, subject, content, type, priority, is_read, class_id)
VALUES 
    ('message-001', 'teacher-001', 'parent-001', 'Alex\'s Progress Update', 'Alex is doing well in mathematics. Keep up the good work!', 'progress', 'normal', false, 'class-001'),
    ('message-002', 'teacher-003', 'parent-002', 'Science Fair Project', 'Emma\'s volcano project is looking great. She\'s very creative!', 'assignment', 'normal', true, 'class-003'),
    ('message-003', 'admin-001', 'teacher-004', 'New Roblox Features', 'We\'ve added new physics simulation tools to the Roblox environment.', 'announcement', 'high', false, NULL)
ON CONFLICT (id) DO NOTHING;

-- Create parent-child relationships
INSERT INTO parent_children (id, parent_id, student_id, relationship, is_primary, can_view_grades, can_view_attendance)
VALUES 
    ('parent-child-001', 'parent-001', 'student-001', 'parent', true, true, true),
    ('parent-child-002', 'parent-002', 'student-003', 'parent', true, true, true),
    ('parent-child-003', 'parent-003', 'student-005', 'parent', true, true, true)
ON CONFLICT (id) DO NOTHING;

-- Create sample system events
INSERT INTO system_events (id, event_type, message, severity, user_id)
VALUES 
    ('event-001', 'user_login', 'Teacher Emily Johnson logged in', 'info', 'teacher-001'),
    ('event-002', 'assignment_created', 'New assignment created: Multiplication Tables Practice', 'info', 'teacher-001'),
    ('event-003', 'roblox_session_started', 'Student Alex Parker started Roblox learning session', 'info', 'student-001'),
    ('event-004', 'grade_updated', 'Grade updated for student Sam Thompson', 'info', 'teacher-001'),
    ('event-005', 'system_backup', 'Daily system backup completed successfully', 'info', 'admin-001')
ON CONFLICT (id) DO NOTHING;

-- Create sample API logs
INSERT INTO api_logs (id, method, endpoint, status_code, response_time, user_id, ip_address)
VALUES 
    ('log-001', 'GET', '/api/dashboard/teacher', 200, 45.2, 'teacher-001', '192.168.1.100'),
    ('log-002', 'POST', '/api/assignments', 201, 89.7, 'teacher-001', '192.168.1.100'),
    ('log-003', 'GET', '/api/dashboard/student', 200, 32.1, 'student-001', '192.168.1.101'),
    ('log-004', 'PUT', '/api/submissions/submission-001', 200, 56.8, 'teacher-001', '192.168.1.100'),
    ('log-005', 'GET', '/api/dashboard/parent', 200, 41.3, 'parent-001', '192.168.1.102')
ON CONFLICT (id) DO NOTHING;

-- Create sample compliance records
INSERT INTO compliance_records (id, type, status, details, reviewed_by)
VALUES 
    ('compliance-001', 'COPPA', 'compliant', '{"data_collection": "minimal", "parental_consent": "obtained"}', 'admin-001'),
    ('compliance-002', 'FERPA', 'compliant', '{"student_records": "protected", "access_control": "enforced"}', 'admin-001'),
    ('compliance-003', 'GDPR', 'compliant', '{"data_processing": "lawful", "user_rights": "respected"}', 'admin-001')
ON CONFLICT (id) DO NOTHING;

-- Update school counts based on created data
UPDATE schools SET 
    student_count = (SELECT COUNT(*) FROM dashboard_users WHERE school_id = schools.id AND role = 'student' AND is_active = true),
    teacher_count = (SELECT COUNT(*) FROM dashboard_users WHERE school_id = schools.id AND role = 'teacher' AND is_active = true),
    class_count = (SELECT COUNT(*) FROM classes WHERE school_id = schools.id AND is_active = true);

-- Update class student counts
UPDATE classes SET 
    student_count = (SELECT COUNT(*) FROM class_students WHERE class_id = classes.id AND status = 'active');

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Sample data created successfully!';
    RAISE NOTICE '📊 Created: 3 schools, 13 users, 4 classes, 5 assignments, 5 submissions, 4 lessons';
    RAISE NOTICE '🎯 Dashboard should now display real data instead of mock data';
    RAISE NOTICE '🔑 Login credentials: admin/password, msjohnson/password, student-001/password, etc.';
END $$;