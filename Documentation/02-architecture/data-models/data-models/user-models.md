# User Models

This document defines the data models for user management, authentication, and authorization within ToolBoxAI-Solutions.

## User Model

The core user account model that represents all system users regardless of role.

### Schema Definition

```lua
User = {
    -- Identity
    id = string,                    -- Unique user identifier (UUID)
    username = string,              -- Unique username
    email = string,                 -- Primary email address
    email_verified = boolean,       -- Email verification status

    -- Personal Information
    profile = {
        first_name = string,        -- First name
        last_name = string,         -- Last name
        display_name = string,      -- Preferred display name
        avatar_url = string,        -- Profile picture URL
        bio = string,              -- User biography (markdown)

        date_of_birth = DateTime,  -- Birth date (for COPPA compliance)
        gender = string,           -- Optional: "male", "female", "other", "prefer_not_to_say"

        phone_number = string,     -- Contact phone (encrypted)
        phone_verified = boolean,  -- Phone verification status

        address = {
            street = string,
            city = string,
            state = string,
            postal_code = string,
            country = string
        },

        timezone = string,         -- User's timezone (IANA format)
        locale = string,          -- Preferred language/locale

        emergency_contact = {
            name = string,
            relationship = string,
            phone = string,
            email = string
        }
    },

    -- Role and Permissions
    role = string,                 -- Primary role: "student", "teacher", "admin", "parent"
    secondary_roles = {string},    -- Additional roles
    permissions = {string},        -- Explicit permissions

    -- Account Status
    status = string,               -- "active", "inactive", "suspended", "pending"
    status_reason = string,        -- Reason for status

    -- Authentication
    auth = {
        password_hash = string,    -- Hashed password (bcrypt)
        last_password_change = DateTime,
        password_reset_token = string,
        password_reset_expires = DateTime,

        two_factor_enabled = boolean,
        two_factor_secret = string,  -- Encrypted TOTP secret
        backup_codes = {string},      -- Encrypted backup codes

        sso_providers = {
            {
                provider = string,    -- "google", "microsoft", "canvas"
                provider_id = string, -- External user ID
                linked_at = DateTime
            }
        },

        api_keys = {
            {
                key_id = string,
                key_hash = string,   -- Hashed API key
                name = string,       -- Key description
                permissions = {string},
                created_at = DateTime,
                last_used = DateTime,
                expires_at = DateTime
            }
        }
    },

    -- Preferences
    preferences = {
        theme = string,              -- "light", "dark", "system"
        language = string,           -- UI language preference

        notifications = {
            email = {
                enabled = boolean,
                frequency = string,  -- "immediate", "daily", "weekly"
                types = {string}    -- Notification types to receive
            },
            push = {
                enabled = boolean,
                types = {string}
            },
            sms = {
                enabled = boolean,
                types = {string}
            }
        },

        privacy = {
            profile_visibility = string,  -- "public", "school", "private"
            show_progress = boolean,
            show_achievements = boolean,
            allow_contact = boolean
        },

        accessibility = {
            high_contrast = boolean,
            font_size = string,      -- "small", "medium", "large", "extra-large"
            screen_reader = boolean,
            keyboard_navigation = boolean,
            reduce_motion = boolean,
            captions = boolean
        },

        learning = {
            difficulty_preference = string,  -- "easy", "medium", "hard", "adaptive"
            pace_preference = string,       -- "self-paced", "scheduled"
            reminder_frequency = string,    -- "none", "daily", "weekly"
            study_time_preference = string  -- Preferred study time
        }
    },

    -- Organization Association
    organization = {
        school_id = string,         -- School/district identifier
        district_id = string,       -- District identifier
        grade_level = number,       -- Current grade (for students)
        graduation_year = number,   -- Expected graduation year

        student_id = string,        -- School-specific student ID
        staff_id = string,         -- School-specific staff ID

        department = string,        -- Department (for staff)
        subjects = {string},       -- Subjects teaching/learning

        enrollment_date = DateTime, -- When joined organization
        exit_date = DateTime       -- When left organization
    },

    -- Timestamps
    created_at = DateTime,         -- Account creation
    updated_at = DateTime,         -- Last profile update
    last_login = DateTime,         -- Last successful login
    last_activity = DateTime,      -- Last system activity

    -- Compliance
    consent = {
        terms_accepted = boolean,
        terms_version = string,
        terms_accepted_at = DateTime,

        privacy_accepted = boolean,
        privacy_version = string,
        privacy_accepted_at = DateTime,

        cookies_accepted = boolean,
        cookies_accepted_at = DateTime,

        marketing_consent = boolean,
        data_sharing_consent = boolean,

        parental_consent = {        -- For users under 13
            provided = boolean,
            provider_id = string,   -- Parent user ID
            provided_at = DateTime,
            document_url = string
        }
    },

    -- Metadata
    metadata = {
        registration_source = string,  -- How user registered
        referral_code = string,       -- Referral tracking
        campaign_id = string,         -- Marketing campaign

        tags = {string},             -- Administrative tags
        notes = string,              -- Administrative notes

        custom_fields = {}          -- School-specific fields
    }
}
```text
### Database Schema (PostgreSQL)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,

    profile JSONB NOT NULL DEFAULT '{}',
    role VARCHAR(20) NOT NULL,
    secondary_roles TEXT[],
    permissions TEXT[],

    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    status_reason TEXT,

    auth JSONB NOT NULL DEFAULT '{}',
    preferences JSONB NOT NULL DEFAULT '{}',
    organization JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,

    consent JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_organization ON users USING GIN(organization);
CREATE INDEX idx_users_last_activity ON users(last_activity);
```text
## Role Model

Defines available roles and their default permissions.

### Schema Definition

```lua
Role = {
    id = string,                   -- Role identifier
    name = string,                 -- Display name
    description = string,          -- Role description

    -- Permission Management
    permissions = {
        -- Learning Management
        view_lessons = boolean,
        create_lessons = boolean,
        edit_lessons = boolean,
        delete_lessons = boolean,

        -- Assessment Management
        view_quizzes = boolean,
        create_quizzes = boolean,
        grade_quizzes = boolean,

        -- User Management
        view_users = boolean,
        create_users = boolean,
        edit_users = boolean,
        delete_users = boolean,

        -- Analytics Access
        view_own_analytics = boolean,
        view_class_analytics = boolean,
        view_school_analytics = boolean,
        view_district_analytics = boolean,

        -- System Administration
        manage_settings = boolean,
        manage_integrations = boolean,
        manage_billing = boolean,

        -- Content Management
        publish_content = boolean,
        moderate_content = boolean,

        -- Support Functions
        provide_support = boolean,
        escalate_issues = boolean
    },

    -- Role Hierarchy
    parent_role = string,          -- Inherits from this role

    -- Constraints
    constraints = {
        max_storage_gb = number,   -- Storage limit
        max_students = number,      -- Student limit (for teachers)
        max_courses = number,       -- Course limit

        allowed_features = {string}, -- Feature access list
        blocked_features = {string}, -- Explicitly blocked features

        time_restrictions = {
            allowed_hours = {       -- Access hours
                start = string,     -- "08:00"
                end = string       -- "17:00"
            },
            allowed_days = {string} -- ["monday", "tuesday", ...]
        }
    },

    -- UI Customization
    ui_config = {
        default_dashboard = string, -- Default dashboard view
        menu_items = {string},     -- Available menu items
        hidden_features = {string} -- Hidden UI elements
    },

    -- Metadata
    is_system = boolean,          -- System-defined role
    is_custom = boolean,          -- Organization-specific role
    created_at = DateTime,
    updated_at = DateTime
}
```text
## Session Model

Tracks active user sessions for security and analytics.

### Schema Definition

```lua
Session = {
    id = string,                   -- Session identifier
    user_id = string,              -- References users.id

    -- Session Data
    token = string,                -- Session token (JWT)
    refresh_token = string,        -- Refresh token

    -- Timing
    created_at = DateTime,         -- Session start
    expires_at = DateTime,         -- Session expiration
    last_activity = DateTime,      -- Last activity timestamp
    idle_time = number,           -- Minutes idle

    -- Device Information
    device = {
        ip_address = string,       -- Client IP (hashed)
        user_agent = string,       -- Browser user agent
        device_type = string,      -- "desktop", "mobile", "tablet"
        browser = string,          -- Browser name and version
        os = string,              -- Operating system

        fingerprint = string,      -- Device fingerprint
        trusted = boolean,        -- Trusted device flag

        location = {
            country = string,
            region = string,
            city = string,
            timezone = string
        }
    },

    -- Security
    security = {
        mfa_verified = boolean,    -- MFA verification status
        risk_score = number,       -- Session risk score (0-100)
        suspicious_activity = boolean,

        flags = {
            {
                type = string,     -- Flag type
                timestamp = DateTime,
                details = string
            }
        }
    },

    -- Activity Tracking
    activity = {
        page_views = number,       -- Total page views
        api_calls = number,        -- Total API calls

        last_pages = {string},     -- Last 10 pages visited
        last_actions = {
            {
                action = string,
                timestamp = DateTime,
                details = string
            }
        }
    },

    -- Status
    status = string,              -- "active", "expired", "revoked"
    revoked_at = DateTime,        -- When session was revoked
    revoked_by = string,         -- Who revoked the session
    revoke_reason = string       -- Reason for revocation
}
```text
## ParentChildRelation Model

Links parent accounts to their children for access and monitoring.

### Schema Definition

```lua
ParentChildRelation = {
    id = string,                  -- Relation identifier
    parent_id = string,           -- Parent user ID
    child_id = string,           -- Student user ID

    -- Relationship Details
    relationship_type = string,   -- "parent", "guardian", "emergency_contact"
    is_primary = boolean,        -- Primary guardian flag

    -- Permissions
    permissions = {
        view_progress = boolean,   -- Can view child's progress
        view_grades = boolean,     -- Can view grades
        view_attendance = boolean, -- Can view attendance

        receive_notifications = boolean, -- Receive notifications
        contact_teachers = boolean,     -- Can message teachers

        approve_activities = boolean,   -- Must approve activities
        manage_settings = boolean,      -- Can change child's settings

        access_level = string     -- "full", "limited", "view_only"
    },

    -- Verification
    verification = {
        verified = boolean,       -- Relationship verified
        verified_by = string,     -- Admin who verified
        verified_at = DateTime,   -- Verification timestamp

        document_type = string,   -- Verification document type
        document_url = string    -- Verification document URL
    },

    -- Communication Preferences
    communication = {
        preferred_contact = string, -- "email", "phone", "app"
        language = string,         -- Preferred language

        digest_frequency = string, -- "daily", "weekly", "monthly"
        urgent_alerts = boolean,  -- Receive urgent alerts

        topics = {                -- Notification topics
            academic = boolean,
            behavioral = boolean,
            attendance = boolean,
            health = boolean
        }
    },

    -- Status
    status = string,              -- "active", "pending", "suspended"
    created_at = DateTime,
    updated_at = DateTime,
    expires_at = DateTime        -- For temporary guardianship
}
```text
## Group Model

Represents user groups for bulk operations and permissions.

### Schema Definition

```lua
Group = {
    id = string,                  -- Group identifier
    name = string,                -- Group name
    description = string,         -- Group description

    -- Group Type
    type = string,                -- "class", "grade", "school", "custom"

    -- Membership
    members = {
        {
            user_id = string,     -- Member user ID
            role = string,        -- Role within group
            joined_at = DateTime,
            added_by = string    -- Who added the member
        }
    },

    member_count = number,        -- Total members

    -- Permissions
    permissions = {string},       -- Group-wide permissions
    inherited_from = string,      -- Parent group ID

    -- Settings
    settings = {
        auto_enroll = boolean,    -- Auto-enroll new users
        enrollment_rules = {      -- Auto-enrollment criteria
            grade_level = number,
            department = string,
            role = string
        },

        max_members = number,     -- Maximum group size
        require_approval = boolean, -- Require approval to join

        visibility = string,      -- "public", "private", "hidden"
        joinable = boolean       -- Can users request to join
    },

    -- Associated Resources
    resources = {
        courses = {string},       -- Associated course IDs
        lessons = {string},       -- Shared lesson IDs
        assignments = {string}    -- Group assignments
    },

    -- Metadata
    owner_id = string,           -- Group owner/creator
    organization_id = string,    -- Organization ID

    created_at = DateTime,
    updated_at = DateTime,
    archived = boolean,
    archived_at = DateTime
}
```text
## Implementation Notes

### Security Considerations

1. **Password Storage**
   - Use bcrypt with cost factor 12+
   - Implement password strength requirements
   - Enforce password history

2. **Token Management**
   - JWT tokens with short expiration (15 minutes)
   - Refresh tokens with longer expiration (7 days)
   - Implement token rotation on refresh

3. **Multi-Factor Authentication**
   - TOTP-based authentication
   - Backup codes for recovery
   - Optional SMS fallback

### COPPA Compliance

For users under 13:

- Require parental consent
- Limit data collection
- Restrict social features
- No behavioral advertising
- Provide parental access controls

### Performance Optimization

1. **Caching Strategy**
   - Cache user profiles in Redis
   - Cache permissions for fast authorization
   - Invalidate on profile updates

2. **Query Optimization**
   - Index frequently queried fields
   - Use partial indexes for status queries
   - Implement query result caching

---

_For related models, see [Progress Models](progress-models.md) for user activity tracking. For authentication implementation, see [API Documentation](../../03-api/authentication.md)._
