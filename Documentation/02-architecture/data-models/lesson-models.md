# Lesson Models

This document defines the data models for educational content, including lessons, courses, modules, and associated learning resources.

## Lesson Model

Represents an individual lesson or learning unit within the platform.

### Schema Definition

```lua
Lesson = {
    -- Identification
    id = string,                    -- Unique lesson identifier (UUID)
    title = string,                 -- Lesson title
    slug = string,                  -- URL-friendly identifier
    version = number,               -- Content version number
    
    -- Description and Overview
    description = string,           -- Brief lesson description
    overview = string,              -- Detailed overview (markdown)
    thumbnail_url = string,         -- Lesson thumbnail image
    preview_url = string,           -- Preview video/content URL
    
    -- Educational Metadata
    education = {
        grade_level = number,       -- Target grade level
        grade_range = {
            min = number,           -- Minimum grade
            max = number           -- Maximum grade
        },
        
        subject = string,           -- Primary subject
        topics = {string},         -- Related topics/tags
        
        difficulty = string,        -- "beginner", "intermediate", "advanced"
        
        prerequisites = {string},   -- Required prior lessons
        
        learning_objectives = {
            {
                id = string,
                description = string,
                bloom_level = string, -- "remember", "understand", "apply", "analyze", "evaluate", "create"
                measurable = boolean
            }
        },
        
        standards = {               -- Curriculum standards alignment
            {
                system = string,    -- "common_core", "ngss", "state"
                code = string,      -- Standard code
                description = string
            }
        },
        
        skills = {                  -- Skills developed
            {
                name = string,
                category = string,  -- "cognitive", "technical", "soft"
                level = string     -- "introduction", "practice", "mastery"
            }
        },
        
        estimated_duration = number, -- Minutes to complete
        
        language = string,          -- Content language
        
        keywords = {string}        -- SEO/search keywords
    },
    
    -- Content Structure
    content = {
        sections = {
            {
                id = string,
                title = string,
                type = string,      -- "instruction", "activity", "assessment", "review"
                order = number,
                
                content = {
                    format = string, -- "text", "video", "interactive", "mixed"
                    
                    text = string,  -- Markdown content
                    
                    media = {
                        {
                            type = string,    -- "video", "audio", "image", "document"
                            url = string,
                            title = string,
                            duration = number, -- Seconds (for video/audio)
                            transcript = string
                        }
                    },
                    
                    interactive = {
                        type = string,        -- "simulation", "game", "exercise"
                        config = {},         -- Interactive element configuration
                        roblox_place_id = string -- Roblox environment ID
                    },
                    
                    resources = {
                        {
                            title = string,
                            type = string,   -- "worksheet", "reading", "reference"
                            url = string,
                            required = boolean
                        }
                    }
                },
                
                instructions = string,      -- Teacher instructions
                notes = string,            -- Additional notes
                
                duration = number,         -- Expected minutes
                
                optional = boolean,        -- Optional section
                
                unlock_condition = string  -- Condition to unlock section
            }
        },
        
        activities = {
            {
                id = string,
                title = string,
                type = string,            -- "individual", "group", "class"
                
                instructions = string,
                
                materials = {string},     -- Required materials
                
                deliverable = {
                    type = string,        -- "submission", "presentation", "discussion"
                    format = string,      -- Expected format
                    rubric_id = string   -- Grading rubric
                },
                
                collaboration = {
                    enabled = boolean,
                    min_group_size = number,
                    max_group_size = number
                },
                
                time_limit = number      -- Minutes allowed
            }
        },
        
        assessments = {
            {
                id = string,
                type = string,           -- "formative", "summative"
                quiz_id = string,        -- References quiz model
                weight = number,         -- Grade weight percentage
                
                timing = string,         -- "beginning", "middle", "end"
                
                retake_allowed = boolean,
                max_attempts = number
            }
        }
    },
    
    -- Roblox Integration
    roblox = {
        environment_id = string,        -- Generated environment ID
        place_id = string,              -- Roblox place ID
        
        blueprint = {                   -- Environment blueprint
            theme = string,
            layout = {},
            objects = {},
            scripts = {}
        },
        
        assets = {                      -- Required assets
            {
                id = string,
                type = string,
                url = string
            }
        },
        
        deployment_status = string,     -- "pending", "deployed", "failed"
        deployed_at = DateTime,
        
        access_code = string,          -- Student access code
        
        multiplayer = {
            enabled = boolean,
            max_players = number,
            mode = string              -- "collaborative", "competitive"
        }
    },
    
    -- Creator and Ownership
    creator = {
        user_id = string,              -- Creator user ID
        organization_id = string,      -- Organization ID
        
        attribution = string,          -- Attribution text
        license = string,             -- Content license
        
        collaborators = {
            {
                user_id = string,
                role = string,         -- "author", "reviewer", "contributor"
                added_at = DateTime
            }
        }
    },
    
    -- Publishing and Visibility
    publishing = {
        status = string,               -- "draft", "review", "published", "archived"
        
        published_at = DateTime,
        published_by = string,
        
        visibility = string,           -- "private", "organization", "public"
        
        featured = boolean,           -- Featured lesson flag
        
        sharing = {
            allow_copy = boolean,      -- Allow others to copy
            allow_modify = boolean,    -- Allow modifications
            require_attribution = boolean
        },
        
        marketplace = {
            listed = boolean,
            price = number,           -- Price if sold
            currency = string,
            
            purchases = number,       -- Number of purchases
            revenue = number         -- Total revenue generated
        }
    },
    
    -- Quality and Reviews
    quality = {
        review_status = string,       -- "pending", "approved", "rejected"
        reviewed_by = string,
        reviewed_at = DateTime,
        review_notes = string,
        
        ratings = {
            average = number,         -- Average rating (1-5)
            count = number,          -- Number of ratings
            
            breakdown = {
                five_star = number,
                four_star = number,
                three_star = number,
                two_star = number,
                one_star = number
            }
        },
        
        feedback = {
            {
                user_id = string,
                rating = number,
                comment = string,
                created_at = DateTime,
                helpful_count = number
            }
        },
        
        quality_score = number,      -- Internal quality score
        
        flags = {                    -- Content flags
            {
                type = string,       -- "inappropriate", "error", "outdated"
                reporter_id = string,
                description = string,
                created_at = DateTime,
                resolved = boolean
            }
        }
    },
    
    -- Usage Statistics
    statistics = {
        views = number,              -- Total views
        unique_viewers = number,     -- Unique users
        
        completions = number,        -- Times completed
        completion_rate = number,    -- Percentage who complete
        
        average_duration = number,   -- Average time to complete
        
        engagement_score = number,   -- Calculated engagement
        
        usage_by_day = {
            {
                date = DateTime,
                views = number,
                completions = number
            }
        },
        
        performance = {
            average_score = number,  -- Average assessment score
            pass_rate = number,     -- Percentage passing
            
            difficulty_rating = number -- User-reported difficulty
        }
    },
    
    -- Timestamps
    created_at = DateTime,
    updated_at = DateTime,
    last_accessed = DateTime,
    
    -- Metadata
    metadata = {
        import_source = string,     -- If imported from external source
        original_id = string,       -- Original ID if imported
        
        tags = {string},           -- Administrative tags
        
        seo = {
            meta_description = string,
            meta_keywords = {string},
            og_image = string
        },
        
        custom_fields = {}         -- Organization-specific fields
    }
}
```

## Course Model

Represents a complete course containing multiple lessons and modules.

### Schema Definition

```lua
Course = {
    -- Identification
    id = string,
    title = string,
    code = string,                 -- Course code (e.g., "MATH101")
    slug = string,
    
    -- Description
    description = string,
    syllabus = string,            -- Full syllabus (markdown)
    thumbnail_url = string,
    banner_url = string,
    
    -- Structure
    structure = {
        modules = {
            {
                id = string,
                title = string,
                description = string,
                order = number,
                
                lessons = {string},   -- Lesson IDs in order
                
                requirements = {
                    min_lessons = number,  -- Minimum lessons to complete
                    min_score = number,   -- Minimum average score
                    
                    prerequisites = {string} -- Required module IDs
                },
                
                duration = number,    -- Estimated hours
                
                available_from = DateTime,
                available_until = DateTime
            }
        },
        
        total_lessons = number,
        total_modules = number,
        
        sequencing = string,         -- "linear", "flexible", "adaptive"
        
        pacing = {
            mode = string,          -- "self-paced", "instructor-paced", "cohort-paced"
            
            schedule = {            -- For paced courses
                {
                    module_id = string,
                    start_date = DateTime,
                    end_date = DateTime
                }
            },
            
            recommended_hours_per_week = number
        }
    },
    
    -- Educational Information
    education = {
        level = string,            -- "elementary", "middle", "high", "college"
        grade_levels = {number},
        
        subject = string,
        department = string,
        
        credits = number,          -- Course credits
        
        prerequisites = {string},  -- Required course IDs
        
        learning_outcomes = {
            {
                description = string,
                assessment_method = string
            }
        },
        
        competencies = {string},   -- Competencies developed
        
        certification = {
            available = boolean,
            requirements = {},
            certificate_template = string
        }
    },
    
    -- Enrollment
    enrollment = {
        capacity = number,         -- Maximum students
        enrolled = number,         -- Current enrollment
        waitlist = number,        -- Waitlist count
        
        requirements = {
            approval_required = boolean,
            prerequisites_enforced = boolean,
            
            eligibility = {
                min_grade_level = number,
                max_grade_level = number,
                required_courses = {string}
            }
        },
        
        enrollment_period = {
            start = DateTime,
            end = DateTime
        },
        
        drop_deadline = DateTime,
        
        cost = {
            amount = number,
            currency = string,
            payment_required = boolean
        }
    },
    
    -- Instructors
    instructors = {
        {
            user_id = string,
            role = string,        -- "primary", "assistant", "guest"
            bio = string,
            office_hours = string,
            contact_info = {}
        }
    },
    
    -- Assessment and Grading
    grading = {
        scale = string,          -- "letter", "percentage", "pass_fail"
        
        weights = {              -- Grade component weights
            quizzes = number,
            assignments = number,
            projects = number,
            participation = number,
            final_exam = number
        },
        
        policies = {
            late_penalty = number,  -- Percentage per day
            makeup_allowed = boolean,
            extra_credit = boolean,
            
            grade_boundaries = {    -- For letter grades
                a_plus = number,
                a = number,
                a_minus = number,
                b_plus = number,
                -- etc.
            }
        }
    },
    
    -- Resources
    resources = {
        textbooks = {
            {
                title = string,
                author = string,
                isbn = string,
                required = boolean,
                url = string
            }
        },
        
        materials = {string},    -- Required materials
        
        external_resources = {
            {
                title = string,
                type = string,
                url = string,
                description = string
            }
        }
    },
    
    -- Communication
    communication = {
        announcements = {
            {
                id = string,
                title = string,
                content = string,
                author_id = string,
                created_at = DateTime,
                priority = string
            }
        },
        
        discussion_forum_id = string,
        
        contact_email = string,
        
        office_hours = {
            {
                day = string,
                start_time = string,
                end_time = string,
                location = string
            }
        }
    },
    
    -- Status and Publishing
    status = string,            -- "planning", "active", "completed", "archived"
    
    term = {
        name = string,         -- "Fall 2023"
        start_date = DateTime,
        end_date = DateTime
    },
    
    visibility = string,       -- "public", "organization", "enrolled"
    
    -- Statistics
    statistics = {
        total_enrollments = number,
        completion_rate = number,
        average_grade = number,
        
        satisfaction_rating = number,
        
        drop_rate = number,
        
        time_to_complete = number  -- Average days
    },
    
    -- Timestamps
    created_at = DateTime,
    updated_at = DateTime,
    published_at = DateTime,
    archived_at = DateTime
}
```

## Module Model

Represents a learning module or unit within a course.

### Schema Definition

```lua
Module = {
    id = string,
    course_id = string,
    
    title = string,
    description = string,
    
    learning_objectives = {string},
    
    content = {
        lessons = {string},       -- Ordered lesson IDs
        assignments = {string},
        resources = {string},
        
        introduction = string,    -- Module introduction content
        summary = string         -- Module summary content
    },
    
    requirements = {
        completion_criteria = string, -- "all", "percentage", "score"
        min_completion = number,     -- Minimum percentage/score
        
        time_limit = number,        -- Days to complete
        
        prerequisites = {string}    -- Required module IDs
    },
    
    assessment = {
        quiz_id = string,          -- Module quiz
        project_id = string,       -- Module project
        
        passing_score = number
    },
    
    order = number,               -- Position in course
    
    available = boolean,
    available_from = DateTime,
    available_until = DateTime,
    
    estimated_hours = number,
    
    created_at = DateTime,
    updated_at = DateTime
}
```

## Resource Model

Represents supplementary learning resources.

### Schema Definition

```lua
Resource = {
    id = string,
    
    title = string,
    description = string,
    
    type = string,               -- "document", "video", "link", "tool"
    format = string,            -- File format or media type
    
    url = string,               -- Resource location
    file_size = number,         -- Size in bytes
    
    thumbnail_url = string,
    
    metadata = {
        author = string,
        source = string,
        license = string,
        
        duration = number,      -- For video/audio (seconds)
        pages = number,        -- For documents
        
        language = string,
        
        accessibility = {
            transcript = string,
            captions = boolean,
            audio_description = boolean,
            alt_text = string
        }
    },
    
    categories = {string},      -- Resource categories
    tags = {string},           -- Resource tags
    
    related_to = {
        courses = {string},
        lessons = {string},
        topics = {string}
    },
    
    usage = {
        views = number,
        downloads = number,
        
        ratings = {
            average = number,
            count = number
        },
        
        bookmarks = number
    },
    
    permissions = {
        view = string,         -- "public", "enrolled", "licensed"
        download = boolean,
        share = boolean,
        embed = boolean
    },
    
    created_at = DateTime,
    updated_at = DateTime,
    created_by = string
}
```

## Implementation Notes

### Content Versioning

Implement content versioning to track changes:
```lua
ContentVersion = {
    content_id = string,
    version = number,
    changes = string,
    changed_by = string,
    changed_at = DateTime,
    snapshot = {}  -- Full content snapshot
}
```

### Content Delivery

1. **CDN Integration**
   - Store media files in CDN
   - Generate signed URLs for protected content
   - Implement adaptive bitrate streaming for videos

2. **Caching Strategy**
   - Cache frequently accessed lessons
   - Invalidate cache on content updates
   - Pre-cache upcoming lessons for enrolled students

### AI Content Generation

Integration points for AI agents:
```python
async def generate_lesson_content(lesson_plan: str):
    # Parse with LessonAnalysisAgent
    structured = await lesson_agent.parse(lesson_plan)
    
    # Generate environment with EnvironmentAgent
    environment = await env_agent.generate(structured)
    
    # Create Roblox blueprint
    blueprint = await roblox_agent.create_blueprint(environment)
    
    return Lesson(content=structured, roblox=blueprint)
```

---

*For assessment models, see [Quiz Models](quiz-models.md). For tracking student interaction with lessons, see [Progress Models](progress-models.md).*