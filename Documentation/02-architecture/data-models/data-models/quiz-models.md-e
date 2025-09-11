# Quiz and Assessment Models

This document defines the data models for quizzes, assessments, questions, and evaluation within the ToolBoxAI-Solutions platform.

## Quiz Model

Represents a complete quiz or assessment that can be assigned to students.

### Schema Definition

```lua
Quiz = {
    -- Identification
    id = string,                    -- Unique quiz identifier (UUID)
    title = string,                  -- Quiz title
    slug = string,                   -- URL-friendly identifier
    version = number,                -- Quiz version number
    
    -- Description
    description = string,            -- Quiz description
    instructions = string,           -- Instructions for students (markdown)
    
    -- Educational Context
    context = {
        course_id = string,          -- Associated course
        lesson_id = string,          -- Associated lesson (optional)
        module_id = string,          -- Associated module (optional)
        
        grade_level = number,        -- Target grade level
        subject = string,            -- Subject area
        topics = {string},          -- Related topics
        
        difficulty = string,         -- "easy", "medium", "hard", "adaptive"
        
        learning_objectives = {      -- Objectives being assessed
            {
                id = string,
                description = string,
                weight = number      -- Importance weight
            }
        },
        
        standards = {               -- Curriculum standards
            {
                system = string,
                code = string,
                description = string
            }
        },
        
        prerequisites = {string}     -- Required prior knowledge
    },
    
    -- Quiz Configuration
    configuration = {
        type = string,              -- "formative", "summative", "diagnostic", "practice"
        
        timing = {
            time_limit = number,    -- Minutes allowed (0 = unlimited)
            time_per_question = number, -- Seconds per question (optional)
            
            show_timer = boolean,   -- Display countdown timer
            warning_time = number,  -- Minutes before warning
            
            auto_submit = boolean,  -- Auto-submit when time expires
        },
        
        attempts = {
            max_attempts = number,  -- Maximum allowed attempts (0 = unlimited)
            
            retake_delay = number,  -- Hours between attempts
            
            attempt_feedback = string, -- "immediate", "after_submission", "after_due_date"
            
            scoring_method = string, -- "highest", "latest", "average"
        },
        
        display = {
            questions_per_page = number, -- Questions per page (0 = all)
            
            randomize_questions = boolean, -- Randomize question order
            randomize_options = boolean,   -- Randomize answer options
            
            show_progress = boolean,       -- Show progress indicator
            allow_navigation = boolean,    -- Allow moving between questions
            allow_review = boolean,        -- Allow reviewing before submit
            
            show_correct_answers = string, -- "never", "after_attempt", "after_due_date"
        },
        
        requirements = {
            passing_score = number,        -- Minimum passing percentage
            required = boolean,            -- Required for course completion
            
            lockdown_browser = boolean,    -- Require secure browser
            webcam_monitoring = boolean,   -- Enable proctoring
            
            honor_code = boolean,         -- Require honor code agreement
        }
    },
    
    -- Questions
    questions = {
        {
            id = string,                  -- Question identifier
            order = number,               -- Display order
            
            question_bank_id = string,    -- Reference to question bank
            
            weight = number,              -- Point value
            
            required = boolean,           -- Required question
            
            pool = {                      -- Question pool settings
                pool_id = string,
                select_count = number     -- Random selection from pool
            }
        }
    },
    
    total_questions = number,           -- Total number of questions
    total_points = number,              -- Total possible points
    
    -- Grading
    grading = {
        method = string,                -- "points", "percentage", "rubric"
        
        grade_scale = {
            {
                grade = string,         -- "A", "B", etc.
                min_percentage = number,
                feedback = string       -- Grade-specific feedback
            }
        },
        
        partial_credit = boolean,       -- Allow partial credit
        negative_marking = boolean,     -- Deduct for wrong answers
        penalty_percentage = number,    -- Penalty for wrong answer
        
        auto_grade = boolean,          -- Automatic grading
        manual_review = boolean,       -- Requires manual review
        
        rubric_id = string            -- Grading rubric reference
    },
    
    -- Availability
    availability = {
        status = string,               -- "draft", "published", "archived"
        
        available_from = DateTime,     -- Start availability
        available_until = DateTime,    -- End availability
        
        due_date = DateTime,          -- Due date for completion
        late_submission = boolean,    -- Allow late submissions
        late_penalty = number,        -- Penalty percentage per day
        
        visibility = string,          -- "public", "enrolled", "assigned"
        
        access_code = string,        -- Access code if required
        
        prerequisites = {             -- Must complete before access
            {
                type = string,       -- "quiz", "lesson", "score"
                id = string,
                min_score = number
            }
        }
    },
    
    -- Feedback
    feedback = {
        show_score = boolean,         -- Show score immediately
        show_answers = boolean,       -- Show correct answers
        show_feedback = boolean,      -- Show question feedback
        
        completion_message = string,  -- Message after completion
        
        pass_message = string,       -- Message if passed
        fail_message = string,       -- Message if failed
        
        certificate = {
            enabled = boolean,
            template_id = string,
            min_score = number
        }
    },
    
    -- Statistics
    statistics = {
        total_attempts = number,      -- Total attempts made
        unique_students = number,     -- Unique students attempted
        
        average_score = number,       -- Average score percentage
        median_score = number,        -- Median score
        
        pass_rate = number,          -- Percentage who passed
        completion_rate = number,    -- Percentage who completed
        
        average_duration = number,   -- Average time to complete
        
        difficulty_index = number,   -- Calculated difficulty (0-1)
        discrimination_index = number, -- How well quiz discriminates
        
        reliability = number,        -- Cronbach's alpha
        
        question_statistics = {      -- Per-question statistics
            {
                question_id = string,
                attempts = number,
                correct_rate = number,
                average_time = number,
                discrimination = number
            }
        }
    },
    
    -- Metadata
    creator = {
        user_id = string,
        created_at = DateTime,
        
        collaborators = {
            {
                user_id = string,
                role = string,
                added_at = DateTime
            }
        }
    },
    
    tags = {string},                -- Quiz tags
    
    updated_at = DateTime,
    published_at = DateTime,
    
    ai_generated = boolean,         -- AI-generated quiz
    ai_config = {}                  -- AI generation parameters
}
```

## Question Model

Represents individual questions that can be used in quizzes.

### Schema Definition

```lua
Question = {
    -- Identification
    id = string,                    -- Unique question identifier
    version = number,               -- Question version
    
    -- Question Content
    content = {
        text = string,              -- Question text (markdown)
        
        media = {                   -- Associated media
            {
                type = string,      -- "image", "video", "audio"
                url = string,
                caption = string,
                transcript = string -- For accessibility
            }
        },
        
        code = {                    -- Code snippet if applicable
            language = string,
            content = string,
            line_numbers = boolean
        },
        
        formula = {                 -- Mathematical formula
            latex = string,
            mathml = string
        },
        
        context = string           -- Additional context/scenario
    },
    
    -- Question Type and Options
    type = string,                 -- Question type (see below)
    -- Types: "multiple_choice", "true_false", "multiple_select",
    -- "short_answer", "essay", "numeric", "matching", "ordering",
    -- "fill_blank", "code", "drawing", "file_upload"
    
    options = {                    -- For choice-based questions
        {
            id = string,
            text = string,
            media_url = string,
            is_correct = boolean,
            feedback = string,     -- Option-specific feedback
            partial_credit = number -- Partial credit percentage
        }
    },
    
    -- Answer Configuration
    answer = {
        correct_answers = {any},   -- Correct answer(s)
        
        acceptable_answers = {     -- Alternative correct answers
            {
                value = any,
                partial_credit = number
            }
        },
        
        answer_key = string,       -- Detailed answer explanation
        
        solution = string,         -- Step-by-step solution
        
        validation = {
            type = string,        -- "exact", "contains", "regex", "numeric_range"
            
            case_sensitive = boolean,
            trim_whitespace = boolean,
            
            numeric_tolerance = number, -- For numeric answers
            
            regex_pattern = string,    -- For pattern matching
            
            min_length = number,       -- For text answers
            max_length = number,
            
            required_keywords = {string}, -- Must contain keywords
            
            code_test_cases = {        -- For code questions
                {
                    input = string,
                    expected_output = string,
                    points = number
                }
            }
        },
        
        rubric = {                    -- For essay/subjective
            {
                criterion = string,
                description = string,
                points = number,
                levels = {
                    {
                        level = string,
                        description = string,
                        points = number
                    }
                }
            }
        }
    },
    
    -- Scoring
    scoring = {
        points = number,              -- Point value
        
        partial_credit = boolean,     -- Allow partial credit
        negative_marking = boolean,   -- Negative marks for wrong
        
        bonus = boolean,             -- Bonus question
        
        weight = number,             -- Weight in quiz
        
        difficulty = number,         -- Difficulty level (1-5)
    },
    
    -- Feedback
    feedback = {
        correct = string,            -- Feedback if correct
        incorrect = string,          -- Feedback if incorrect
        partial = string,           -- Feedback if partially correct
        
        hint = string,              -- Hint (if hints enabled)
        
        explanation = string,       -- Detailed explanation
        
        resources = {               -- Learning resources
            {
                title = string,
                url = string,
                type = string
            }
        }
    },
    
    -- Educational Metadata
    metadata = {
        subject = string,
        topic = string,
        subtopic = string,
        
        grade_level = number,
        
        learning_objectives = {string},
        
        bloom_level = string,       -- Bloom's taxonomy level
        
        standards = {
            {
                system = string,
                code = string
            }
        },
        
        keywords = {string},
        
        estimated_time = number,    -- Seconds to answer
        
        language = string,         -- Question language
        
        accessibility = {
            alt_text = string,     -- Alternative text
            audio_description = string,
            captions = boolean
        }
    },
    
    -- Usage Statistics
    statistics = {
        usage_count = number,       -- Times used in quizzes
        
        attempt_count = number,     -- Total attempts
        
        correct_rate = number,      -- Percentage correct
        
        average_time = number,      -- Average time to answer
        
        discrimination_index = number, -- Item discrimination
        
        difficulty_index = number,  -- Item difficulty
        
        reviews = {
            average_rating = number,
            rating_count = number
        }
    },
    
    -- Question Bank
    bank = {
        bank_id = string,          -- Question bank ID
        category = string,         -- Category within bank
        
        tags = {string},          -- Question tags
        
        shared = boolean,         -- Shared across organization
        
        quality_score = number    -- Quality rating
    },
    
    -- Version Control
    history = {
        {
            version = number,
            changed_by = string,
            changed_at = DateTime,
            change_summary = string,
            content_snapshot = {}
        }
    },
    
    -- Status
    status = string,              -- "draft", "review", "approved", "deprecated"
    
    reviewed_by = string,
    reviewed_at = DateTime,
    
    created_by = string,
    created_at = DateTime,
    updated_at = DateTime,
    
    -- AI Generation
    ai_generated = boolean,
    ai_prompt = string,
    ai_model = string
}
```

## QuestionBank Model

Repository of reusable questions organized by category and topic.

### Schema Definition

```lua
QuestionBank = {
    id = string,
    name = string,
    description = string,
    
    -- Organization
    organization_id = string,
    department = string,
    
    -- Categories
    categories = {
        {
            id = string,
            name = string,
            parent_id = string,    -- For nested categories
            
            question_count = number,
            
            metadata = {
                subject = string,
                grade_levels = {number},
                difficulty_range = {
                    min = number,
                    max = number
                }
            }
        }
    },
    
    -- Questions
    questions = {string},         -- Question IDs in bank
    total_questions = number,
    
    -- Sharing
    visibility = string,          -- "private", "department", "organization", "public"
    
    sharing = {
        allow_copy = boolean,
        allow_modify = boolean,
        require_attribution = boolean,
        
        shared_with = {
            {
                entity_type = string, -- "user", "department", "organization"
                entity_id = string,
                permissions = {string}
            }
        }
    },
    
    -- Quality Control
    quality = {
        review_required = boolean,
        
        reviewers = {string},     -- User IDs of reviewers
        
        quality_threshold = number, -- Minimum quality score
        
        validation_rules = {
            require_feedback = boolean,
            require_explanation = boolean,
            require_standards = boolean
        }
    },
    
    -- Statistics
    statistics = {
        usage_count = number,     -- Times questions used
        quiz_count = number,      -- Quizzes using bank
        
        average_difficulty = number,
        average_discrimination = number,
        
        last_updated = DateTime,
        last_used = DateTime
    },
    
    -- Metadata
    tags = {string},
    
    created_by = string,
    created_at = DateTime,
    updated_at = DateTime
}
```

## AssessmentResult Model

Records the complete results of a quiz attempt including detailed analytics.

### Schema Definition

```lua
AssessmentResult = {
    id = string,
    
    -- References
    quiz_id = string,
    attempt_id = string,         -- References QuizAttempt
    student_id = string,
    
    -- Scoring
    score = {
        raw_score = number,       -- Points earned
        total_points = number,    -- Points possible
        percentage = number,      -- Percentage score
        
        weighted_score = number,  -- After weighting
        curved_score = number,    -- After curve adjustment
        
        grade = string,          -- Letter grade
        passed = boolean,        -- Pass/fail status
        
        percentile = number,     -- Percentile rank
        z_score = number        -- Standard score
    },
    
    -- Performance Analysis
    performance = {
        questions_attempted = number,
        questions_correct = number,
        questions_incorrect = number,
        questions_skipped = number,
        
        accuracy_rate = number,
        
        time_taken = number,     -- Total minutes
        time_per_question = number,
        
        efficiency_score = number, -- Speed vs accuracy
        
        strengths = {string},    -- Strong areas identified
        weaknesses = {string},   -- Weak areas identified
        
        improvement_from_last = number, -- Percentage improvement
    },
    
    -- Question-Level Analysis
    question_analysis = {
        {
            question_id = string,
            
            response_time = number,
            changes_made = number,   -- Times answer changed
            
            correct = boolean,
            points_earned = number,
            
            difficulty_relative = string, -- "easy", "appropriate", "hard"
            
            concept_mastery = number -- Mastery level for concept
        }
    },
    
    -- Learning Analytics
    learning_analytics = {
        concepts_mastered = {
            {
                concept = string,
                mastery_level = number,
                evidence_count = number
            }
        },
        
        learning_objectives_met = {
            {
                objective_id = string,
                achieved = boolean,
                score = number
            }
        },
        
        bloom_distribution = {      -- Performance by Bloom's level
            remember = number,
            understand = number,
            apply = number,
            analyze = number,
            evaluate = number,
            create = number
        },
        
        recommended_review = {string}, -- Topics to review
        
        next_steps = {
            {
                type = string,     -- "lesson", "practice", "assessment"
                resource_id = string,
                reason = string
            }
        }
    },
    
    -- Comparative Analysis
    comparison = {
        class_average = number,
        class_rank = number,
        
        historical_average = number, -- Student's historical avg
        
        peer_group_percentile = number,
        
        difficulty_adjusted_score = number -- Adjusted for quiz difficulty
    },
    
    -- Feedback
    feedback = {
        automatic = string,        -- System-generated feedback
        
        instructor = {
            comments = string,
            provided_by = string,
            provided_at = DateTime
        },
        
        peer_review = {
            {
                reviewer_id = string,
                comments = string,
                rating = number
            }
        }
    },
    
    -- Certification
    certification = {
        earned = boolean,
        certificate_id = string,
        issued_at = DateTime,
        
        badge_earned = string,
        
        competencies_certified = {string}
    },
    
    -- Metadata
    generated_at = DateTime,
    viewed_by_student = boolean,
    viewed_at = DateTime,
    
    shared_with_parent = boolean,
    
    included_in_grade = boolean,
    grade_weight = number
}
```

## Implementation Notes

### Question Types Implementation

Different question types require specific handling:

```python
class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"      # Single correct answer
    TRUE_FALSE = "true_false"                # Boolean answer
    MULTIPLE_SELECT = "multiple_select"      # Multiple correct answers
    SHORT_ANSWER = "short_answer"            # Text input
    ESSAY = "essay"                          # Long text input
    NUMERIC = "numeric"                      # Numeric input
    MATCHING = "matching"                    # Match pairs
    ORDERING = "ordering"                    # Sequence items
    FILL_BLANK = "fill_blank"               # Fill in blanks
    CODE = "code"                           # Code submission
    DRAWING = "drawing"                     # Drawing/diagram
    FILE_UPLOAD = "file_upload"             # File submission

def validate_answer(question_type: QuestionType, response: Any, answer: dict):
    """Validate response based on question type"""
    validators = {
        QuestionType.MULTIPLE_CHOICE: validate_choice,
        QuestionType.SHORT_ANSWER: validate_text,
        QuestionType.NUMERIC: validate_numeric,
        QuestionType.CODE: validate_code,
        # ... etc
    }
    return validators[question_type](response, answer)
```

### Adaptive Testing

For adaptive quizzes that adjust difficulty:

```lua
AdaptiveAlgorithm = {
    initial_difficulty = 3,        -- Start at medium
    
    adjustment_rules = {
        correct = {
            increase_difficulty = 0.5,
            max_difficulty = 5
        },
        incorrect = {
            decrease_difficulty = 0.5,
            min_difficulty = 1
        }
    },
    
    termination_criteria = {
        max_questions = 30,
        confidence_level = 0.95,
        standard_error = 0.3
    },
    
    ability_estimation = "maximum_likelihood" -- or "bayesian"
}
```

### Anti-Cheating Measures

```lua
IntegrityMonitoring = {
    browser_lockdown = {
        disable_copy_paste = true,
        disable_right_click = true,
        fullscreen_required = true,
        prevent_tab_switch = true
    },
    
    proctoring = {
        webcam_monitoring = true,
        screen_recording = true,
        identity_verification = true,
        
        ai_monitoring = {
            detect_multiple_faces = true,
            detect_phone_usage = true,
            detect_suspicious_movement = true
        }
    },
    
    response_analysis = {
        detect_pattern_copying = true,
        flag_rapid_responses = true,
        compare_ip_addresses = true,
        analyze_response_similarity = true
    }
}
```

### Question Pool Management

```python
class QuestionPoolSelector:
    def select_questions(self, pool_id: str, count: int, criteria: dict):
        """Select questions from pool based on criteria"""
        
        # Balance by difficulty
        difficulty_distribution = criteria.get('difficulty_distribution', {
            'easy': 0.3,
            'medium': 0.5,
            'hard': 0.2
        })
        
        # Balance by topic
        topic_coverage = criteria.get('topic_coverage', 'proportional')
        
        # Avoid recent questions
        exclude_recent = criteria.get('exclude_recent_days', 30)
        
        # Apply selection algorithm
        selected = self.balanced_random_selection(
            pool_id, count, difficulty_distribution,
            topic_coverage, exclude_recent
        )
        
        return selected
```

### Performance Optimization

1. **Question Caching**
   - Cache frequently used questions
   - Pre-render question content
   - Cache validation rules

2. **Batch Grading**
   - Process auto-gradable questions in batch
   - Queue manual grading tasks
   - Parallel processing for large quizzes

3. **Analytics Pipeline**
   - Stream response data to analytics
   - Batch calculate statistics
   - Update question difficulty indices periodically

---

*For tracking quiz attempts, see [Progress Models](progress-models.md). For overall learning analytics, see [Analytics Models](analytics-models.md).*