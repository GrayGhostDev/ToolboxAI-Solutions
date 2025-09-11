-- Simple Data Creation for ToolboxAI Educational Platform
-- This script creates realistic test data using direct SQL

-- Clear existing test data (optional)
-- DELETE FROM users WHERE email LIKE '%@test.%';

-- Create Test Users (if not already created)
INSERT INTO users (username, email, password_hash, first_name, last_name, role, grade_level, school_name, is_active, is_verified)
SELECT * FROM (VALUES
    ('john_teacher', 'john@test.edu', '$2b$12$3641c3aac9354aa4b8ac3b3677d7b1a358c535aaafe160ce0821c8f8', 'John', 'Smith', 'teacher', 7, 'Lincoln Middle School', true, true),
    ('sarah_teacher', 'sarah@test.edu', '$2b$12$3641c3aac9354aa4b8ac3b3677d7b1a358c535aaafe160ce0821c8f8', 'Sarah', 'Johnson', 'teacher', 8, 'Lincoln Middle School', true, true),
    ('alice_student', 'alice@test.edu', '$2b$12$3641c3aac9354aa4b8ac3b3677d7b1a358c535aaafe160ce0821c8f8', 'Alice', 'Wilson', 'student', 7, 'Lincoln Middle School', true, true),
    ('bob_student', 'bob@test.edu', '$2b$12$3641c3aac9354aa4b8ac3b3677d7b1a358c535aaafe160ce0821c8f8', 'Bob', 'Davis', 'student', 7, 'Lincoln Middle School', true, true),
    ('charlie_student', 'charlie@test.edu', '$2b$12$3641c3aac9354aa4b8ac3b3677d7b1a358c535aaafe160ce0821c8f8', 'Charlie', 'Miller', 'student', 8, 'Lincoln Middle School', true, true)
) AS v(username, email, password_hash, first_name, last_name, role, grade_level, school_name, is_active, is_verified)
WHERE NOT EXISTS (SELECT 1 FROM users WHERE users.email = v.email);

-- Create Learning Objectives
INSERT INTO learning_objectives (title, description, subject, grade_level)
SELECT * FROM (VALUES
    ('Understand Solar System', 'Students will understand the structure and components of our solar system', 'Science', 7),
    ('Master Linear Equations', 'Students will solve linear equations and graph them', 'Mathematics', 7),
    ('Explore Ancient Civilizations', 'Students will learn about major ancient civilizations', 'History', 7),
    ('Cell Biology Basics', 'Students will understand cell structure and function', 'Science', 7),
    ('Geometry Fundamentals', 'Students will master basic geometric concepts', 'Mathematics', 8)
) AS v(title, description, subject, grade_level)
WHERE NOT EXISTS (SELECT 1 FROM learning_objectives WHERE learning_objectives.title = v.title);

-- Create Educational Content
INSERT INTO educational_content (
    title, subject, grade_level, description, environment_type,
    content_data, is_published, created_by
)
SELECT 
    v.title, v.subject, v.grade_level, v.description, v.environment_type,
    v.content_data::jsonb, v.is_published, 
    (SELECT id FROM users WHERE role = 'teacher' LIMIT 1) as created_by
FROM (VALUES
    ('Solar System Exploration', 'Science', 7, 
     'Interactive journey through our solar system with planets, moons, and space phenomena',
     'space_station',
     '{"type": "course", "duration": 60, "modules": 5, "features": ["3D visualization", "interactive quizzes", "simulations"]}',
     true),
    
    ('Linear Equations Mastery', 'Mathematics', 7,
     'Complete course on solving and graphing linear equations',
     'classroom',
     '{"type": "course", "duration": 45, "modules": 4, "features": ["practice problems", "step-by-step solutions", "graphing tools"]}',
     true),
    
    ('Ancient Civilizations Tour', 'History', 7,
     'Virtual tour through ancient Egypt, Greece, Rome, and China',
     'historical_site',
     '{"type": "course", "duration": 50, "modules": 4, "features": ["virtual tours", "timeline explorer", "artifact gallery"]}',
     true),
    
    ('Cell Biology Lab', 'Science', 7,
     'Interactive laboratory for exploring cell structure and function',
     'laboratory',
     '{"type": "course", "duration": 40, "modules": 3, "features": ["microscope simulator", "3D cell models", "experiments"]}',
     true),
    
    ('Geometry World', 'Mathematics', 8,
     'Explore geometry through interactive 3D shapes and proofs',
     'geometric_space',
     '{"type": "course", "duration": 55, "modules": 5, "features": ["3D shape builder", "proof assistant", "measurement tools"]}',
     true)
) AS v(title, subject, grade_level, description, environment_type, content_data, is_published)
WHERE NOT EXISTS (SELECT 1 FROM educational_content WHERE educational_content.title = v.title);

-- Create Quizzes
INSERT INTO quizzes (
    title, description, subject, grade_level, 
    total_points, time_limit_minutes, is_published, created_by
)
SELECT 
    v.title, v.description, v.subject, v.grade_level,
    v.total_points, v.time_limit_minutes, v.is_published,
    (SELECT id FROM users WHERE role = 'teacher' LIMIT 1) as created_by
FROM (VALUES
    ('Solar System Quiz', 'Test your knowledge of planets and space', 'Science', 7, 100, 30, true),
    ('Linear Equations Practice', 'Solve linear equations and identify slopes', 'Mathematics', 7, 100, 25, true),
    ('Ancient History Test', 'Questions about ancient civilizations', 'History', 7, 100, 35, true),
    ('Cell Biology Assessment', 'Identify cell parts and functions', 'Science', 7, 100, 30, true),
    ('Geometry Challenge', 'Solve geometry problems and proofs', 'Mathematics', 8, 150, 40, true)
) AS v(title, description, subject, grade_level, total_points, time_limit_minutes, is_published)
WHERE NOT EXISTS (SELECT 1 FROM quizzes WHERE quizzes.title = v.title);

-- Create Quiz Questions for Solar System Quiz
WITH solar_quiz AS (
    SELECT id FROM quizzes WHERE title = 'Solar System Quiz' LIMIT 1
)
INSERT INTO quiz_questions (
    quiz_id, question_text, question_type, options, correct_answer, points, sequence_order
)
SELECT 
    sq.id, v.question_text, v.question_type, v.options::jsonb, v.correct_answer, v.points, v.sequence_order
FROM solar_quiz sq, (VALUES
    ('What is the largest planet in our solar system?', 'multiple_choice', 
     '["Jupiter", "Saturn", "Earth", "Mars"]', 'Jupiter', 10, 1),
    ('How many planets are in our solar system?', 'multiple_choice',
     '["7", "8", "9", "10"]', '8', 10, 2),
    ('Which planet is known as the Red Planet?', 'multiple_choice',
     '["Venus", "Mars", "Jupiter", "Mercury"]', 'Mars', 10, 3),
    ('True or False: The Sun is a star', 'true_false',
     '["True", "False"]', 'True', 5, 4),
    ('What is the closest planet to the Sun?', 'multiple_choice',
     '["Venus", "Earth", "Mercury", "Mars"]', 'Mercury', 10, 5)
) AS v(question_text, question_type, options, correct_answer, points, sequence_order)
WHERE NOT EXISTS (
    SELECT 1 FROM quiz_questions qq 
    WHERE qq.quiz_id = sq.id AND qq.question_text = v.question_text
);

-- Create AI Agent Configurations
INSERT INTO ai_agents (
    name, agent_type, description, version, 
    model_config, capabilities, is_active
)
SELECT * FROM (VALUES
    ('supervisor', 'orchestrator', 
     'Main orchestration agent for complex educational tasks', '2.0.0',
     '{"model": "gpt-4", "temperature": 0.7, "max_tokens": 4000}'::jsonb,
     ARRAY['{"skill": "orchestration", "level": "expert"}'::jsonb], true),
    
    ('content_creator', 'content', 
     'Generates educational content aligned with curriculum', '2.0.0',
     '{"model": "gpt-4", "temperature": 0.8, "max_tokens": 8000}'::jsonb,
     ARRAY['{"skill": "content_creation", "level": "expert"}'::jsonb], true),
    
    ('quiz_generator', 'assessment',
     'Creates quizzes and assessments', '2.0.0',
     '{"model": "gpt-4", "temperature": 0.6, "max_tokens": 4000}'::jsonb,
     ARRAY['{"skill": "assessment_design", "level": "expert"}'::jsonb], true)
) AS v(name, agent_type, description, version, model_config, capabilities, is_active)
WHERE NOT EXISTS (SELECT 1 FROM ai_agents WHERE ai_agents.name = v.name);

-- Create Achievements
INSERT INTO achievements (
    name, description, type, points, icon_url
)
SELECT * FROM (VALUES
    ('First Steps', 'Complete your first lesson', 'milestone', 10, '/icons/first-steps.png'),
    ('Quiz Master', 'Score 100% on any quiz', 'performance', 25, '/icons/quiz-master.png'),
    ('Week Warrior', '7-day learning streak', 'consistency', 50, '/icons/streak.png'),
    ('Explorer', 'Try all subject areas', 'exploration', 30, '/icons/explorer.png'),
    ('Helper', 'Help another student', 'social', 20, '/icons/helper.png')
) AS v(name, description, type, points, icon_url)
WHERE NOT EXISTS (SELECT 1 FROM achievements WHERE achievements.name = v.name);

-- Create Sample Progress Records
INSERT INTO user_progress (
    user_id, content_id, progress_percentage, xp_earned, time_spent_minutes
)
SELECT 
    u.id as user_id,
    c.id as content_id,
    (random() * 100)::int as progress_percentage,
    (random() * 500 + 100)::int as xp_earned,
    (random() * 120 + 30)::int as time_spent_minutes
FROM 
    (SELECT id FROM users WHERE role = 'student' LIMIT 3) u
CROSS JOIN 
    (SELECT id FROM educational_content LIMIT 3) c
ON CONFLICT (user_id, content_id) DO UPDATE
SET progress_percentage = EXCLUDED.progress_percentage,
    xp_earned = EXCLUDED.xp_earned;

-- Summary
SELECT 
    'Data Creation Summary' as report,
    (SELECT COUNT(*) FROM users WHERE email LIKE '%@test.%') as test_users,
    (SELECT COUNT(*) FROM educational_content WHERE is_published = true) as published_content,
    (SELECT COUNT(*) FROM quizzes WHERE is_published = true) as published_quizzes,
    (SELECT COUNT(*) FROM quiz_questions) as quiz_questions,
    (SELECT COUNT(*) FROM ai_agents WHERE is_active = true) as active_agents,
    (SELECT COUNT(*) FROM achievements) as achievements,
    (SELECT COUNT(*) FROM user_progress) as progress_records;