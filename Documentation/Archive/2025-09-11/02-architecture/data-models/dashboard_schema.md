# Dashboard Database Schema

Generated: 2025-09-10T10:49:00.830030
Total Tables: 16

## Table of Contents

- [api_logs](#api_logs)
- [assignments](#assignments)
- [attendance](#attendance)
- [class_students](#class_students)
- [classes](#classes)
- [compliance_records](#compliance_records)
- [dashboard_users](#dashboard_users)
- [lessons](#lessons)
- [messages](#messages)
- [parent_children](#parent_children)
- [schools](#schools)
- [student_achievements](#student_achievements)
- [student_activity](#student_activity)
- [student_progress](#student_progress)
- [submissions](#submissions)
- [system_events](#system_events)

## api_logs

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| method | VARCHAR(10) | No | - | |
| endpoint | VARCHAR(500) | No | - | |
| status_code | INTEGER | No | - | |
| response_time | DECIMAL | Yes | - | |
| user_id (FK→dashboard_users) | VARCHAR(36) | Yes | - | |
| ip_address | INET | Yes | - | |
| user_agent | TEXT | Yes | - | |
| timestamp | TIMESTAMPTZ | Yes | NOW() | |

---

## assignments

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| title | VARCHAR(200) | No | - | |
| description | TEXT | Yes | - | |
| type | VARCHAR(50) | No | 'assignment' | |
| subject | VARCHAR(100) | No | - | |
| class_id (FK→classes) | VARCHAR(36) | No | - | |
| teacher_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| due_date | TIMESTAMPTZ | Yes | - | |
| points | INTEGER | Yes | 100 | |
| status | VARCHAR(20) | Yes | 'active' | |
| instructions | TEXT | Yes | - | |
| materials_url | VARCHAR(500) | Yes | - | |
| is_published | BOOLEAN | Yes | false | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |
| updated_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_assignments_class**: class_id
- **idx_assignments_teacher**: teacher_id
- **idx_assignments_due_date**: due_date

---

## attendance

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| student_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| class_id (FK→classes) | VARCHAR(36) | No | - | |
| lesson_id (FK→lessons) | VARCHAR(36) | Yes | - | |
| date | DATE | No | - | |
| status | VARCHAR(20) | No | 'present' | |
| notes | TEXT | Yes | - | |
| recorded_by (FK→dashboard_users) | VARCHAR(36) | Yes | - | |
| recorded_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_attendance_student_date**: student_id, date
- **idx_attendance_class_date**: class_id, date

---

## class_students

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| class_id (FK→classes) | VARCHAR(36) | Yes | - | |
| student_id (FK→dashboard_users) | VARCHAR(36) | Yes | - | |
| enrolled_at | TIMESTAMPTZ | Yes | NOW() | |
| status | VARCHAR(20) | Yes | 'active' | |
| grade | DECIMAL | Yes | - | |
| attendance_rate | DECIMAL | Yes | - | |

### Indexes

- **idx_class_students_class**: class_id
- **idx_class_students_student**: student_id

---

## classes

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| name | VARCHAR(200) | No | - | |
| description | TEXT | Yes | - | |
| subject | VARCHAR(100) | No | - | |
| grade_level | INTEGER | No | - | |
| teacher_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| school_id (FK→schools) | VARCHAR(36) | Yes | - | |
| schedule | VARCHAR(200) | Yes | - | |
| start_date | DATE | Yes | - | |
| end_date | DATE | Yes | - | |
| max_students | INTEGER | Yes | 30 | |
| student_count | INTEGER | Yes | 0 | |
| room | VARCHAR(50) | Yes | - | |
| is_active | BOOLEAN | Yes | true | |
| syllabus_url | VARCHAR(500) | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |
| updated_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_classes_teacher**: teacher_id
- **idx_classes_school**: school_id
- **idx_classes_subject_grade**: subject, grade_level

---

## compliance_records

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| type | VARCHAR(50) | No | - | |
| status | VARCHAR(20) | No | - | |
| details | JSONB | Yes | '{}' | |
| reviewed_by (FK→dashboard_users) | VARCHAR(36) | Yes | - | |
| reviewed_at | TIMESTAMPTZ | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |

---

## dashboard_users

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| password_hash | VARCHAR(255) | No | - | |
| first_name | VARCHAR(100) | Yes | - | |
| last_name | VARCHAR(100) | Yes | - | |
| role | VARCHAR(20) | No | 'student' | |
| school_id (FK→schools) | VARCHAR(36) | Yes | - | |
| grade_level | INTEGER | Yes | - | |
| phone | VARCHAR(20) | Yes | - | |
| address | TEXT | Yes | - | |
| emergency_contact_name | VARCHAR(100) | Yes | - | |
| emergency_contact_phone | VARCHAR(20) | Yes | - | |
| is_active | BOOLEAN | Yes | true | |
| is_verified | BOOLEAN | Yes | false | |
| profile_picture_url | VARCHAR(500) | Yes | - | |
| last_login | TIMESTAMPTZ | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |
| updated_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_dashboard_users_email**: email
- **idx_dashboard_users_role**: role
- **idx_dashboard_users_school**: school_id

---

## lessons

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| title | VARCHAR(200) | No | - | |
| description | TEXT | Yes | - | |
| subject | VARCHAR(100) | No | - | |
| class_id (FK→classes) | VARCHAR(36) | No | - | |
| teacher_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| scheduled_at | TIMESTAMPTZ | No | - | |
| duration_minutes | INTEGER | Yes | 50 | |
| lesson_type | VARCHAR(50) | Yes | 'standard' | |
| content_url | VARCHAR(500) | Yes | - | |
| roblox_world_id | VARCHAR(100) | Yes | - | |
| learning_objectives | TEXT | Yes | - | |
| materials | TEXT | Yes | - | |
| status | VARCHAR(20) | Yes | 'scheduled' | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |
| updated_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_lessons_class**: class_id
- **idx_lessons_scheduled**: scheduled_at

---

## messages

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| sender_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| recipient_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| subject | VARCHAR(200) | No | - | |
| content | TEXT | No | - | |
| type | VARCHAR(20) | Yes | 'general' | |
| priority | VARCHAR(20) | Yes | 'normal' | |
| is_read | BOOLEAN | Yes | false | |
| read_at | TIMESTAMPTZ | Yes | - | |
| class_id (FK→classes) | VARCHAR(36) | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_messages_recipient**: recipient_id, created_at DESC
- **idx_messages_sender**: sender_id, created_at DESC

---

## parent_children

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| parent_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| student_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| relationship | VARCHAR(50) | Yes | 'parent' | |
| is_primary | BOOLEAN | Yes | false | |
| can_view_grades | BOOLEAN | Yes | true | |
| can_view_attendance | BOOLEAN | Yes | true | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |

---

## schools

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| name | VARCHAR(200) | No | - | |
| address | VARCHAR(500) | No | - | |
| city | VARCHAR(100) | No | - | |
| state | VARCHAR(50) | No | - | |
| zip_code | VARCHAR(10) | No | - | |
| phone | VARCHAR(20) | Yes | - | |
| email | VARCHAR(100) | Yes | - | |
| principal_name | VARCHAR(100) | Yes | - | |
| district | VARCHAR(200) | Yes | - | |
| max_students | INTEGER | Yes | 500 | |
| student_count | INTEGER | Yes | 0 | |
| teacher_count | INTEGER | Yes | 0 | |
| class_count | INTEGER | Yes | 0 | |
| is_active | BOOLEAN | Yes | true | |
| logo_url | VARCHAR(500) | Yes | - | |
| website | VARCHAR(500) | Yes | - | |
| founded_year | INTEGER | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |
| updated_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_schools_district**: district
- **idx_schools_active**: is_active

---

## student_achievements

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| student_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| achievement_id (FK→achievements) | INTEGER | No | - | |
| earned_at | TIMESTAMPTZ | Yes | NOW() | |
| class_id (FK→classes) | VARCHAR(36) | Yes | - | |

---

## student_activity

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| student_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| type | VARCHAR(50) | No | - | |
| description | TEXT | No | - | |
| xp_earned | INTEGER | Yes | 0 | |
| class_id (FK→classes) | VARCHAR(36) | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_student_activity_student**: student_id

---

## student_progress

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| student_id (FK→dashboard_users) | VARCHAR(36) | No | - | |
| class_id (FK→classes) | VARCHAR(36) | Yes | - | |
| subject | VARCHAR(100) | Yes | - | |
| grade_level | INTEGER | Yes | - | |
| xp_points | INTEGER | Yes | 0 | |
| level | INTEGER | Yes | 1 | |
| streak_days | INTEGER | Yes | 0 | |
| total_badges | INTEGER | Yes | 0 | |
| rank_position | INTEGER | Yes | 0 | |
| gpa | DECIMAL | Yes | - | |
| attendance_rate | DECIMAL | Yes | - | |
| assignments_completed | INTEGER | Yes | 0 | |
| assignments_total | INTEGER | Yes | 0 | |
| last_activity | TIMESTAMPTZ | Yes | - | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |
| updated_at | TIMESTAMPTZ | Yes | NOW() | |

### Indexes

- **idx_student_progress_student**: student_id
- **idx_student_progress_class**: class_id

---

## submissions

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| assignment_id (FK→assignments) | VARCHAR(36) | Yes | - | |
| student_id (FK→dashboard_users) | VARCHAR(36) | Yes | - | |
| submitted_at | TIMESTAMPTZ | Yes | NOW() | |
| status | VARCHAR(20) | Yes | 'submitted' | |
| grade | DECIMAL | Yes | - | |
| progress | INTEGER | Yes | 0 | |
| content | TEXT | Yes | - | |
| file_url | VARCHAR(500) | Yes | - | |
| feedback | TEXT | Yes | - | |
| graded_at | TIMESTAMPTZ | Yes | - | |
| graded_by (FK→dashboard_users) | VARCHAR(36) | Yes | - | |

### Indexes

- **idx_submissions_assignment**: assignment_id
- **idx_submissions_student**: student_id

---

## system_events

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| event_type | VARCHAR(50) | No | - | |
| message | TEXT | No | - | |
| severity | VARCHAR(20) | Yes | 'info' | |
| user_id (FK→dashboard_users) | VARCHAR(36) | Yes | - | |
| metadata | JSONB | Yes | '{}' | |
| created_at | TIMESTAMPTZ | Yes | NOW() | |

---
