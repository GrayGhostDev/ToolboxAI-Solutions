# Educational Platform Database Schema

Generated: 2025-09-10T10:49:00.787177
Total Tables: 12

## Table of Contents

- [content_objectives](#content_objectives)
- [educational_content](#educational_content)
- [learning_objectives](#learning_objectives)
- [quiz_attempts](#quiz_attempts)
- [quiz_options](#quiz_options)
- [quiz_questions](#quiz_questions)
- [quizzes](#quizzes)
- [roles](#roles)
- [user_progress](#user_progress)
- [user_roles](#user_roles)
- [user_sessions](#user_sessions)
- [users](#users)

## content_objectives

### Columns

| Column                                | Type | Nullable | Default | Description |
| ------------------------------------- | ---- | -------- | ------- | ----------- |
| content_id (FK→educational_content)   | UUID | Yes      | -       |             |
| objective_id (FK→learning_objectives) | UUID | Yes      | -       |             |

---

## educational_content

### Columns

| Column                 | Type         | Nullable | Default  | Description |
| ---------------------- | ------------ | -------- | -------- | ----------- |
| title                  | VARCHAR(200) | No       | -        |             |
| description            | TEXT         | Yes      | -        |             |
| subject                | VARCHAR(50)  | No       | -        |             |
| grade_level            | INTEGER      | No       | -        |             |
| environment_type       | VARCHAR(50)  | No       | -        |             |
| terrain_size           | VARCHAR(20)  | Yes      | 'medium' |             |
| difficulty_level       | VARCHAR(20)  | Yes      | 'medium' |             |
| duration_minutes       | INTEGER      | Yes      | 30       |             |
| max_students           | INTEGER      | Yes      | 30       |             |
| content_data           | JSONB        | No       | -        |             |
| generated_scripts      | JSONB        | Yes      | -        |             |
| terrain_config         | JSONB        | Yes      | -        |             |
| game_mechanics         | JSONB        | Yes      | -        |             |
| accessibility_features | BOOLEAN      | Yes      | false    |             |
| multilingual           | BOOLEAN      | Yes      | false    |             |
| version                | INTEGER      | Yes      | 1        |             |
| is_template            | BOOLEAN      | Yes      | false    |             |
| is_published           | BOOLEAN      | Yes      | false    |             |
| created_by (FK→users)  | UUID         | Yes      | -        |             |
| created_at             | TIMESTAMPTZ  | Yes      | NOW()    |             |
| updated_at             | TIMESTAMPTZ  | Yes      | NOW()    |             |

### Indexes

- **idx_content_subject_grade**: subject, grade_level
- **idx_content_created_by**: created_by, created_at DESC
- **idx_content_published**: is_published, created_at DESC

---

## learning_objectives

### Columns

| Column              | Type         | Nullable | Default | Description |
| ------------------- | ------------ | -------- | ------- | ----------- |
| title               | VARCHAR(200) | No       | -       |             |
| description         | TEXT         | Yes      | -       |             |
| subject             | VARCHAR(50)  | No       | -       |             |
| bloom_level         | VARCHAR(20)  | Yes      | -       |             |
| curriculum_standard | VARCHAR(100) | Yes      | -       |             |
| measurable          | BOOLEAN      | Yes      | true    |             |
| created_at          | TIMESTAMPTZ  | Yes      | NOW()   |             |
| updated_at          | TIMESTAMPTZ  | Yes      | NOW()   |             |

---

## quiz_attempts

### Columns

| Column                        | Type        | Nullable | Default | Description |
| ----------------------------- | ----------- | -------- | ------- | ----------- |
| quiz_id (FK→quizzes)          | UUID        | Yes      | -       |             |
| user_id (FK→users)            | UUID        | Yes      | -       |             |
| session_id (FK→user_sessions) | UUID        | Yes      | -       |             |
| attempt_number                | INTEGER     | No       | -       |             |
| started_at                    | TIMESTAMPTZ | Yes      | NOW()   |             |
| completed_at                  | TIMESTAMPTZ | Yes      | -       |             |
| score                         | DECIMAL     | Yes      | -       |             |
| passed                        | BOOLEAN     | Yes      | -       |             |
| time_taken                    | INTEGER     | Yes      | -       |             |
| answers                       | JSONB       | Yes      | -       |             |
| feedback                      | JSONB       | Yes      | -       |             |
| adaptive_adjustments          | JSONB       | Yes      | -       |             |

### Indexes

- **idx_quiz_attempts_user**: user_id, completed_at DESC
- **idx_quiz_attempts_quiz**: quiz_id, score DESC

---

## quiz_options

### Columns

| Column                          | Type        | Nullable | Default | Description |
| ------------------------------- | ----------- | -------- | ------- | ----------- |
| question_id (FK→quiz_questions) | UUID        | Yes      | -       |             |
| option_text                     | TEXT        | No       | -       |             |
| is_correct                      | BOOLEAN     | Yes      | false   |             |
| explanation                     | TEXT        | Yes      | -       |             |
| order_index                     | INTEGER     | No       | -       |             |
| created_at                      | TIMESTAMPTZ | Yes      | NOW()   |             |

---

## quiz_questions

### Columns

| Column               | Type        | Nullable | Default  | Description |
| -------------------- | ----------- | -------- | -------- | ----------- |
| quiz_id (FK→quizzes) | UUID        | Yes      | -        |             |
| question_type        | VARCHAR(20) | No       | -        |             |
| question_text        | TEXT        | No       | -        |             |
| correct_answer       | TEXT        | Yes      | -        |             |
| difficulty           | VARCHAR(20) | Yes      | 'medium' |             |
| points               | INTEGER     | Yes      | 1        |             |
| time_limit           | INTEGER     | Yes      | -        |             |
| hint                 | TEXT        | Yes      | -        |             |
| explanation          | TEXT        | Yes      | -        |             |
| order_index          | INTEGER     | No       | -        |             |
| question_data        | JSONB       | Yes      | -        |             |
| created_at           | TIMESTAMPTZ | Yes      | NOW()    |             |

### Indexes

- **idx_quiz_questions_quiz**: quiz_id, order_index

---

## quizzes

### Columns

| Column                              | Type         | Nullable | Default | Description |
| ----------------------------------- | ------------ | -------- | ------- | ----------- |
| title                               | VARCHAR(200) | No       | -       |             |
| description                         | TEXT         | Yes      | -       |             |
| subject                             | VARCHAR(50)  | No       | -       |             |
| grade_level                         | INTEGER      | No       | -       |             |
| content_id (FK→educational_content) | UUID         | Yes      | -       |             |
| time_limit                          | INTEGER      | Yes      | -       |             |
| passing_score                       | INTEGER      | Yes      | 70      |             |
| max_attempts                        | INTEGER      | Yes      | 3       |             |
| shuffle_questions                   | BOOLEAN      | Yes      | true    |             |
| shuffle_options                     | BOOLEAN      | Yes      | true    |             |
| show_results                        | BOOLEAN      | Yes      | true    |             |
| is_adaptive                         | BOOLEAN      | Yes      | false   |             |
| difficulty_progression              | JSONB        | Yes      | -       |             |
| created_by (FK→users)               | UUID         | Yes      | -       |             |
| created_at                          | TIMESTAMPTZ  | Yes      | NOW()   |             |
| updated_at                          | TIMESTAMPTZ  | Yes      | NOW()   |             |

---

## roles

### Columns

| Column      | Type        | Nullable | Default | Description |
| ----------- | ----------- | -------- | ------- | ----------- |
| description | TEXT        | Yes      | -       |             |
| is_system   | BOOLEAN     | Yes      | false   |             |
| priority    | INTEGER     | Yes      | 0       |             |
| permissions | JSONB       | Yes      | '{}'    |             |
| created_at  | TIMESTAMPTZ | Yes      | NOW()   |             |
| updated_at  | TIMESTAMPTZ | Yes      | NOW()   |             |

---

## user_progress

### Columns

| Column                                            | Type        | Nullable | Default | Description |
| ------------------------------------------------- | ----------- | -------- | ------- | ----------- |
| user_id (FK→users)                                | UUID        | Yes      | -       |             |
| content_id (FK→educational_content)               | UUID        | Yes      | -       |             |
| progress_type                                     | VARCHAR(20) | No       | -       |             |
| completion_percentage                             | DECIMAL     | Yes      | -       |             |
| time_spent_seconds                                | INTEGER     | Yes      | 0       |             |
| attempts_count                                    | INTEGER     | Yes      | 0       |             |
| best_score                                        | DECIMAL     | Yes      | -       |             |
| current_streak                                    | INTEGER     | Yes      | 0       |             |
| max_streak                                        | INTEGER     | Yes      | 0       |             |
| difficulty_level                                  | VARCHAR(20) | Yes      | -       |             |
| mastery_level                                     | VARCHAR(20) | Yes      | -       |             |
| last_interaction                                  | TIMESTAMPTZ | Yes      | -       |             |
| next_recommended_content (FK→educational_content) | UUID        | Yes      | -       |             |
| learning_style                                    | JSONB       | Yes      | -       |             |
| performance_trends                                | JSONB       | Yes      | -       |             |
| recommendations                                   | JSONB       | Yes      | -       |             |
| created_at                                        | TIMESTAMPTZ | Yes      | NOW()   |             |
| updated_at                                        | TIMESTAMPTZ | Yes      | NOW()   |             |

### Indexes

- **idx_progress_user_content**: user_id, content_id
- **idx_progress_completion**: completion_percentage DESC, last_interaction DESC

---

## user_roles

### Columns

| Column                 | Type        | Nullable | Default | Description |
| ---------------------- | ----------- | -------- | ------- | ----------- |
| user_id (FK→users)     | UUID        | Yes      | -       |             |
| role_id (FK→roles)     | UUID        | Yes      | -       |             |
| assigned_at            | TIMESTAMPTZ | Yes      | NOW()   |             |
| assigned_by (FK→users) | UUID        | Yes      | -       |             |

---

## user_sessions

### Columns

| Column              | Type         | Nullable | Default | Description |
| ------------------- | ------------ | -------- | ------- | ----------- |
| user_id (FK→users)  | UUID         | Yes      | -       |             |
| session_type        | VARCHAR(20)  | Yes      | 'web'   |             |
| ip_address          | INET         | Yes      | -       |             |
| user_agent          | TEXT         | Yes      | -       |             |
| device_id           | VARCHAR(255) | Yes      | -       |             |
| browser_fingerprint | VARCHAR(500) | Yes      | -       |             |
| country             | VARCHAR(2)   | Yes      | -       |             |
| timezone            | VARCHAR(50)  | Yes      | -       |             |
| locale              | VARCHAR(10)  | Yes      | -       |             |
| created_at          | TIMESTAMPTZ  | Yes      | NOW()   |             |
| expires_at          | TIMESTAMPTZ  | No       | -       |             |
| refresh_expires_at  | TIMESTAMPTZ  | Yes      | -       |             |
| last_activity       | TIMESTAMPTZ  | Yes      | NOW()   |             |
| is_active           | BOOLEAN      | Yes      | true    |             |
| revoked_at          | TIMESTAMPTZ  | Yes      | -       |             |
| revoked_reason      | VARCHAR(255) | Yes      | -       |             |
| security_events     | JSONB        | Yes      | '[]'    |             |

### Indexes

- **idx_sessions_user_id**: user_id
- **idx_sessions_token**: token
- **idx_sessions_expires_at**: expires_at

---

## users

### Columns

| Column                | Type         | Nullable | Default   | Description |
| --------------------- | ------------ | -------- | --------- | ----------- |
| password_hash         | VARCHAR(255) | No       | -         |             |
| first_name            | VARCHAR(100) | Yes      | -         |             |
| last_name             | VARCHAR(100) | Yes      | -         |             |
| display_name          | VARCHAR(200) | Yes      | -         |             |
| avatar_url            | VARCHAR(500) | Yes      | -         |             |
| bio                   | TEXT         | Yes      | -         |             |
| role                  | VARCHAR(20)  | Yes      | 'student' |             |
| grade_level           | INTEGER      | Yes      | -         |             |
| school_name           | VARCHAR(200) | Yes      | -         |             |
| district_name         | VARCHAR(200) | Yes      | -         |             |
| subjects_taught       | JSONB        | Yes      | -         |             |
| subjects_interested   | JSONB        | Yes      | -         |             |
| is_active             | BOOLEAN      | Yes      | true      |             |
| is_verified           | BOOLEAN      | Yes      | false     |             |
| is_superuser          | BOOLEAN      | Yes      | false     |             |
| email_verified_at     | TIMESTAMPTZ  | Yes      | -         |             |
| last_login            | TIMESTAMPTZ  | Yes      | -         |             |
| login_count           | INTEGER      | Yes      | 0         |             |
| failed_login_count    | INTEGER      | Yes      | 0         |             |
| locked_until          | TIMESTAMPTZ  | Yes      | -         |             |
| two_factor_enabled    | BOOLEAN      | Yes      | false     |             |
| two_factor_secret     | VARCHAR(255) | Yes      | -         |             |
| settings              | JSONB        | Yes      | '{}'      |             |
| preferences           | JSONB        | Yes      | '{}'      |             |
| notification_settings | JSONB        | Yes      | '{}'      |             |
| created_at            | TIMESTAMPTZ  | Yes      | NOW()     |             |
| updated_at            | TIMESTAMPTZ  | Yes      | NOW()     |             |
| created_by (FK→users) | UUID         | Yes      | -         |             |
| updated_by (FK→users) | UUID         | Yes      | -         |             |
| version               | INTEGER      | Yes      | 1         |             |
| audit_log             | JSONB        | Yes      | '[]'      |             |

### Indexes

- **idx_users_email**: email
- **idx_users_username**: username
- **idx_users_role**: role
- **idx_users_created_at**: created_at DESC

---
