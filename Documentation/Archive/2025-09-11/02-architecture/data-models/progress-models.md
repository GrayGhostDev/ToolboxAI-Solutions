# Progress Tracking Models

This document details the data models used for tracking student progress, performance, and engagement across the educational platform. These models form the foundation for analytics, reporting, and personalized learning experiences.

## StudentCourseProgress Model

Tracks a student's overall progress through a specific course, including completed lessons, quiz performance, and overall advancement.

### Schema Definition

```lua
StudentCourseProgress = {
    id = string,                 -- Unique identifier (UUID)
    student_id = string,         -- References users.id
    course_id = string,          -- References courses.id
    enrolled_at = DateTime,      -- Enrollment timestamp
    last_accessed = DateTime,    -- Last activity timestamp
    status = string,             -- Enum: "not_started", "in_progress", "completed", "paused"
    
    -- Progress tracking
    completed_lessons = {
        {
            lesson_id = string,      -- References lessons.id
            completed_at = DateTime, -- Completion timestamp
            time_spent = number,     -- Total minutes spent
            attempts = number,       -- Number of access attempts
            score = number          -- Optional lesson score (0-100)
        }
    },
    
    -- Assessment tracking
    completed_quizzes = {
        {
            quiz_id = string,        -- References quizzes.id
            completed_at = DateTime, -- Best attempt completion
            attempts = number,       -- Total attempts made
            best_score = number,     -- Highest score achieved (0-100)
            best_attempt_id = string,-- References quiz_attempts.id
            time_spent = number,     -- Total time across all attempts
            passed = boolean        -- Whether passing score achieved
        }
    },
    
    -- Assignment tracking
    completed_assignments = {
        {
            assignment_id = string,  -- References assignments.id
            submitted_at = DateTime, -- Submission timestamp
            grade = number,         -- Grade received (0-100)
            feedback_id = string,   -- References feedback.id
            time_spent = number,    -- Minutes spent on assignment
            status = string        -- "submitted", "graded", "returned"
        }
    },
    
    -- Current state
    current_lesson_id = string,     -- Currently active lesson
    current_module_id = string,     -- Currently active module
    progress_percentage = number,   -- Overall completion (0-100)
    
    -- Certification
    certificate_issued = boolean,   -- Whether certificate was earned
    certificate_url = string,       -- URL to certificate PDF
    certificate_issued_at = DateTime,-- Certificate issue date
    
    -- Engagement metrics
    total_time_spent = number,      -- Total minutes in course
    login_streak = number,          -- Consecutive days accessed
    last_streak_date = DateTime,    -- Last date for streak calculation
    
    -- Student notes and bookmarks
    notes = {
        {
            id = string,            -- Note identifier
            lesson_id = string,     -- Associated lesson
            content = string,       -- Note text (markdown)
            created_at = DateTime,  -- Creation timestamp
            updated_at = DateTime,  -- Last edit timestamp
            tags = {string}        -- User-defined tags
        }
    },
    
    bookmarks = {
        {
            id = string,            -- Bookmark identifier
            content_type = string,  -- "lesson", "video", "quiz"
            content_id = string,    -- Referenced content ID
            position = string,      -- Position in content (e.g., "05:23")
            created_at = DateTime,  -- Bookmark timestamp
            note = string          -- Optional bookmark note
        }
    },
    
    -- Notifications
    last_notification_sent = DateTime, -- Last reminder sent
    notification_preferences = {
        reminders = boolean,
        achievements = boolean,
        deadlines = boolean
    },
    
    -- Custom fields for extensions
    custom_fields = {
        -- Flexible key-value pairs for school-specific data
    }
}
```

### Example Instance

```lua
{
    id = "PROG-2023-10001",
    student_id = "USR-STU-12345",
    course_id = "CRS-MATH-1001",
    enrolled_at = "2023-09-01T08:00:00Z",
    last_accessed = "2023-10-28T15:45:22Z",
    status = "in_progress",
    
    completed_lessons = {
        {
            lesson_id = "LSN-1001",
            completed_at = "2023-09-05T18:22:10Z",
            time_spent = 48,
            attempts = 1,
            score = 95
        },
        {
            lesson_id = "LSN-1002",
            completed_at = "2023-09-12T14:15:30Z",
            time_spent = 62,
            attempts = 2,
            score = 88
        }
    },
    
    completed_quizzes = {
        {
            quiz_id = "QZ-1001",
            completed_at = "2023-09-06T16:45:20Z",
            attempts = 2,
            best_score = 85,
            best_attempt_id = "QZAT-10001",
            time_spent = 25,
            passed = true
        }
    },
    
    current_lesson_id = "LSN-1003",
    progress_percentage = 35,
    certificate_issued = false,
    total_time_spent = 315,
    login_streak = 5
}
```

## QuizAttempt Model

Records detailed information about each attempt a student makes on a quiz, including individual question responses and timing.

### Schema Definition

```lua
QuizAttempt = {
    id = string,                    -- Unique attempt identifier
    student_id = string,            -- References users.id
    quiz_id = string,              -- References quizzes.id
    course_id = string,            -- References courses.id
    lesson_id = string,            -- References lessons.id (optional)
    
    -- Timing
    started_at = DateTime,         -- Attempt start time
    completed_at = DateTime,       -- Attempt completion time
    time_spent = number,           -- Total minutes spent
    time_limit_exceeded = boolean, -- If time limit was exceeded
    
    -- Scoring
    score = number,                -- Final score (0-100)
    points_earned = number,        -- Actual points earned
    points_possible = number,      -- Maximum possible points
    passed = boolean,              -- Whether passing threshold met
    passing_score = number,        -- Required passing score
    
    -- Detailed answers
    answers = {
        {
            question_id = string,       -- References questions.id
            question_type = string,     -- "multiple_choice", "essay", etc.
            answer = any,              -- Student's answer (type varies)
            correct_answer = any,      -- Correct answer for reference
            is_correct = boolean,      -- Whether answer was correct
            partial_credit = boolean,  -- Whether partial credit given
            points_earned = number,    -- Points for this question
            points_possible = number,  -- Maximum points for question
            time_spent = number,       -- Seconds on this question
            attempts_before_answer = number, -- Changes before submission
            confidence_level = number  -- Student's confidence (1-5)
        }
    },
    
    -- Feedback
    feedback = string,             -- Instructor feedback (markdown)
    feedback_provided_at = DateTime, -- When feedback was given
    feedback_provided_by = string,   -- Instructor user ID
    auto_feedback = string,        -- System-generated feedback
    
    -- Metadata
    attempt_number = number,       -- Which attempt this is (1st, 2nd, etc.)
    is_practice = boolean,        -- Whether this was practice mode
    environment = string,         -- "classroom", "home", "mobile"
    
    -- Device and location
    device_info = {
        type = string,            -- "desktop", "tablet", "mobile"
        browser = string,         -- Browser and version
        os = string,             -- Operating system
        screen_size = string     -- Screen resolution
    },
    
    location_info = {
        ip_address = string,      -- IP address (hashed)
        country = string,        -- Country code
        region = string,         -- State/province
        timezone = string        -- Timezone
    },
    
    -- Integrity tracking
    integrity_flags = {
        {
            type = string,        -- "tab_switch", "copy_paste", etc.
            timestamp = DateTime, -- When flag occurred
            details = string     -- Additional context
        }
    },
    
    -- Session tracking
    session_id = string,         -- Associated session
    interruptions = number,      -- Number of session interruptions
    
    -- Analytics metadata
    metadata = {
        question_order = {string}, -- Order questions were presented
        randomized = boolean,     -- Whether questions were randomized
        adaptive = boolean,       -- Whether adaptive testing was used
        difficulty_adjustments = {number} -- Difficulty changes during test
    }
}
```

## ActivityLog Model

Records fine-grained student activity for analytics, monitoring, and personalization.

### Schema Definition

```lua
ActivityLog = {
    id = string,                  -- Log entry identifier
    student_id = string,          -- References users.id
    timestamp = DateTime,         -- Activity timestamp
    
    -- Activity classification
    activity_type = string,       -- Activity type enum
    -- Types: "login", "logout", "lesson_start", "lesson_complete",
    -- "quiz_start", "quiz_submit", "video_play", "video_complete",
    -- "achievement_earned", "resource_download", "help_requested"
    
    activity_category = string,   -- "learning", "assessment", "social", "system"
    
    -- Context references
    course_id = string,          -- References courses.id (optional)
    lesson_id = string,          -- References lessons.id (optional)
    quiz_id = string,            -- References quizzes.id (optional)
    assignment_id = string,      -- References assignments.id (optional)
    resource_id = string,        -- References resources.id (optional)
    
    -- Activity details
    details = {
        action = string,         -- Specific action taken
        duration = number,       -- Duration in seconds (if applicable)
        progress = number,       -- Progress percentage (if applicable)
        score = number,         -- Score achieved (if applicable)
        input_method = string,  -- "mouse", "keyboard", "touch", "voice"
        interaction_count = number, -- Number of interactions
        
        -- Page/content tracking
        page_url = string,      -- Current page URL
        referrer_url = string,  -- Previous page URL
        content_section = string, -- Specific section accessed
        
        -- Performance metrics
        load_time = number,     -- Page/content load time (ms)
        response_time = number, -- Server response time (ms)
        
        -- Custom event data
        custom_data = {}       -- Flexible field for event-specific data
    },
    
    -- Device and environment
    device_info = {
        type = string,
        browser = string,
        os = string,
        screen_size = string,
        connection_type = string -- "wifi", "cellular", "ethernet"
    },
    
    -- Session context
    session_id = string,        -- Current session identifier
    session_duration = number,  -- Current session length (minutes)
    
    -- Learning context
    learning_path_id = string,  -- Current learning path
    learning_objective_id = string, -- Associated objective
    
    -- Outcome
    success = boolean,          -- Whether action was successful
    error_message = string     -- Error details if failed
}
```

## LearningAnalytics Model

Aggregated analytics data for insights, reporting, and personalization.

### Schema Definition

```lua
LearningAnalytics = {
    id = string,                -- Analytics record identifier
    student_id = string,        -- References users.id
    course_id = string,         -- References courses.id (optional)
    
    -- Time period
    period_type = string,       -- "daily", "weekly", "monthly", "custom"
    start_date = DateTime,      -- Period start
    end_date = DateTime,        -- Period end
    
    -- Time spent breakdown
    time_metrics = {
        total_time = number,          -- Total minutes
        lesson_time = number,         -- Time in lessons
        quiz_time = number,           -- Time in assessments
        assignment_time = number,     -- Time on assignments
        resource_time = number,       -- Time with resources
        idle_time = number,          -- Detected idle time
        
        time_by_day = {              -- Daily breakdown
            {
                date = DateTime,
                minutes = number
            }
        },
        
        peak_hours = {               -- Most active hours
            morning = number,        -- 6am-12pm
            afternoon = number,      -- 12pm-6pm
            evening = number,        -- 6pm-12am
            night = number          -- 12am-6am
        }
    },
    
    -- Performance metrics
    performance_metrics = {
        quiz_average = number,       -- Average quiz score
        quiz_improvement = number,   -- Score trend (+/- percentage)
        assignment_average = number, -- Average assignment grade
        completion_rate = number,    -- Content completion percentage
        mastery_level = number,     -- Overall mastery (0-100)
        
        strengths = {string},       -- Identified strong areas
        weaknesses = {string},      -- Areas needing improvement
        
        grade_distribution = {
            a_count = number,       -- 90-100%
            b_count = number,       -- 80-89%
            c_count = number,       -- 70-79%
            d_count = number,       -- 60-69%
            f_count = number       -- Below 60%
        }
    },
    
    -- Engagement metrics
    engagement_metrics = {
        login_count = number,        -- Number of logins
        session_count = number,      -- Number of sessions
        avg_session_length = number, -- Average session (minutes)
        participation_score = number, -- Participation level (0-100)
        
        interaction_metrics = {
            clicks_per_session = number,
            pages_per_session = number,
            videos_watched = number,
            resources_downloaded = number,
            questions_asked = number,
            forum_posts = number
        },
        
        engagement_trend = string,   -- "increasing", "stable", "decreasing"
        risk_level = string         -- "low", "medium", "high"
    },
    
    -- Learning patterns
    learning_patterns = {
        preferred_content_type = string,  -- "video", "text", "interactive"
        learning_pace = string,           -- "fast", "moderate", "slow"
        optimal_session_length = number,  -- Ideal minutes per session
        preferred_difficulty = string,    -- "easy", "medium", "hard"
        
        content_preferences = {
            video_preference = number,    -- 0-100 preference score
            text_preference = number,
            interactive_preference = number,
            audio_preference = number
        },
        
        study_patterns = {
            consistent_schedule = boolean,
            cramming_detected = boolean,
            review_frequency = string    -- "never", "rarely", "often"
        }
    },
    
    -- Comparative metrics
    comparison_metrics = {
        vs_class_average = number,      -- Percentage above/below
        vs_previous_period = number,    -- Change from last period
        percentile_rank = number,       -- Class percentile (0-100)
        vs_personal_best = number,      -- Compared to best performance
        
        peer_comparison = {
            ahead_of_peers = number,    -- Percentage of peers behind
            similar_to_peers = number,  -- Percentage at similar level
            behind_peers = number       -- Percentage of peers ahead
        }
    },
    
    -- Predictive metrics
    predictions = {
        estimated_completion_date = DateTime, -- Course completion prediction
        success_probability = number,        -- Likelihood of success (0-100)
        at_risk_indicators = {string},      -- Risk factors identified
        
        recommended_interventions = {
            {
                type = string,              -- "tutoring", "review", etc.
                urgency = string,           -- "low", "medium", "high"
                description = string        -- Intervention details
            }
        },
        
        next_milestone = {
            type = string,                  -- "module", "assessment", etc.
            description = string,
            estimated_date = DateTime,
            preparation_needed = string
        }
    },
    
    -- Achievement tracking
    achievements = {
        total_earned = number,
        recent_achievements = {string},    -- Last 5 achievements
        next_achievement = string,         -- Closest achievement
        achievement_velocity = number     -- Achievements per week
    }
}
```

## PerformanceReport Model

Structured reports for educators, parents, and administrators.

### Schema Definition

```lua
PerformanceReport = {
    id = string,                    -- Report identifier
    student_id = string,            -- References users.id
    course_id = string,             -- References courses.id (optional)
    
    -- Report metadata
    report_type = string,           -- "progress", "grade", "comprehensive"
    title = string,                 -- Report title
    description = string,           -- Report description
    
    period_start = DateTime,        -- Reporting period start
    period_end = DateTime,          -- Reporting period end
    generated_at = DateTime,        -- Generation timestamp
    generated_by = string,          -- User who generated report
    
    -- Access tracking
    accessed_by = {
        {
            user_id = string,
            role = string,          -- "student", "parent", "teacher"
            accessed_at = DateTime
        }
    },
    
    -- Summary metrics
    summary = {
        overall_grade = string,     -- Letter grade
        overall_percentage = number, -- Numeric grade (0-100)
        attendance_rate = number,   -- Attendance percentage
        completion_rate = number,   -- Work completion percentage
        
        behavior_score = number,    -- Behavior/participation score
        effort_score = number,      -- Effort rating
        
        total_time_spent = number,  -- Total hours
        assignments_completed = number,
        quizzes_taken = number,
        
        gpa_contribution = number,  -- GPA impact
        credit_hours = number      -- Credit hours earned
    },
    
    -- Detailed assessments
    assessments = {
        quizzes = {
            {
                id = string,
                title = string,
                date = DateTime,
                score = number,
                weight = number,    -- Grade weight percentage
                trend = string     -- "improving", "stable", "declining"
            }
        },
        
        assignments = {
            {
                id = string,
                title = string,
                submitted = DateTime,
                grade = number,
                feedback_summary = string,
                late = boolean
            }
        },
        
        projects = {
            {
                id = string,
                title = string,
                grade = number,
                collaboration_score = number,
                presentation_score = number
            }
        }
    },
    
    -- Skills assessment
    skills = {
        {
            skill_name = string,
            category = string,          -- "academic", "soft", "technical"
            mastery_level = string,     -- "beginner", "developing", "proficient", "advanced"
            evidence_count = number,    -- Number of demonstrations
            last_demonstrated = DateTime,
            
            sub_skills = {
                {
                    name = string,
                    level = number     -- 1-5 scale
                }
            }
        }
    },
    
    -- Goals and progress
    goals = {
        {
            goal_id = string,
            description = string,
            target_date = DateTime,
            progress = number,         -- 0-100 percentage
            status = string,          -- "on_track", "at_risk", "achieved", "missed"
            
            milestones = {
                {
                    description = string,
                    completed = boolean,
                    date = DateTime
                }
            }
        }
    },
    
    -- Feedback and recommendations
    feedback = {
        strengths = {string},          -- List of strengths
        improvements = {string},       -- Areas for improvement
        achievements = {string},       -- Notable achievements
        
        teacher_comments = string,     -- Narrative feedback
        
        action_items = {
            {
                priority = string,     -- "high", "medium", "low"
                description = string,
                due_date = DateTime,
                assigned_to = string  -- "student", "parent", "teacher"
            }
        },
        
        recommendations = {
            academic = {string},      -- Academic recommendations
            behavioral = {string},    -- Behavioral suggestions
            enrichment = {string}    -- Enrichment opportunities
        }
    },
    
    -- Next steps
    next_steps = {
        immediate_focus = string,     -- Primary focus area
        resources = {                 -- Recommended resources
            {
                type = string,
                title = string,
                url = string
            }
        },
        support_services = {string},  -- Available support services
        parent_actions = {string}     -- Suggested parent involvement
    },
    
    -- Report configuration
    configuration = {
        format = string,              -- "pdf", "html", "json"
        template = string,            -- Template used
        include_graphs = boolean,    -- Whether to include visualizations
        detail_level = string,       -- "summary", "detailed", "comprehensive"
        
        visibility = {
            student = boolean,
            parents = boolean,
            teachers = boolean,
            administrators = boolean
        },
        
        sharing = {
            shareable = boolean,
            share_url = string,
            expires_at = DateTime
        }
    }
}
```

## Implementation Notes

### Performance Optimization

1. **Indexing Strategy**
   - Index on `student_id`, `course_id`, and date fields
   - Composite indexes for common query patterns
   - Partial indexes for status-based queries

2. **Data Aggregation**
   - Pre-aggregate daily statistics during off-peak hours
   - Use materialized views for complex analytics queries
   - Implement caching for frequently accessed reports

3. **Data Partitioning**
   - Partition activity logs by month
   - Archive old progress data to cold storage
   - Maintain hot data for current academic year

### Privacy Considerations

1. **Data Minimization**
   - Only collect necessary data for educational purposes
   - Implement data retention policies
   - Provide data export capabilities for students

2. **Access Control**
   - Role-based access to progress data
   - Audit logging for all data access
   - Parent access limited to their children's data

3. **Anonymization**
   - Remove PII from analytics aggregations
   - Use hashed identifiers for tracking
   - Implement differential privacy for reports

### Real-time Updates

1. **Event Streaming**
   ```python
   async def stream_progress_event(event: ProgressEvent):
       # Update database
       await update_progress(event)
       # Stream to analytics
       await stream_to_analytics(event)
       # Notify subscribers
       await notify_subscribers(event)
   ```

2. **WebSocket Notifications**
   - Real-time progress updates to dashboards
   - Achievement notifications
   - Collaborative learning updates

### Integration Points

1. **LMS Synchronization**
   - Bi-directional grade sync
   - Progress milestone reporting
   - Assignment submission tracking

2. **Gamification System**
   - Achievement trigger evaluation
   - XP calculation from activities
   - Leaderboard updates

3. **Notification System**
   - Progress milestone alerts
   - Inactivity warnings
   - Achievement celebrations

---

*For related models, see [Quiz Models](quiz-models.md) and [Analytics Models](analytics-models.md). For implementation details, see [System Design](../system-design.md).*