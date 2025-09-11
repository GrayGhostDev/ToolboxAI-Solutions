# Course Content Models

This document provides detailed specifications for the data models representing educational content within the platform, including courses, lessons, quizzes, and associated materials.

## Course Model

The Course model represents a complete educational program with multiple lessons and quizzes.

```lua
Course = {
	id = string,                 -- Unique identifier for the course
	title = string,              -- Course title
	description = string,        -- Course description
	imageUrl = string,           -- Cover image URL
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	status = string,             -- "draft", "published", "archived"
	educatorId = string,         -- ID of educator who created the course
	category = string,           -- Subject category
	tags = {string},             -- Keyword tags for searchability
	difficulty = string,         -- "beginner", "intermediate", "advanced"
	totalLessons = number,       -- Total number of lessons in the course
	totalQuizzes = number,       -- Total number of quizzes in the course
	estimatedHours = number,     -- Estimated hours to complete
	prerequisites = {CourseId},  -- Courses recommended before starting
	lessons = {LessonId},        -- Ordered list of lesson IDs
	quizzes = {QuizId},          -- Ordered list of quiz IDs
	students = {StudentId},      -- Enrolled students
	ratings = {                  -- Course ratings
		average = number,        -- Average rating (1-5)
		count = number,          -- Number of ratings
		distribution = {         -- Distribution of ratings
			"1": number,         -- Count of 1-star ratings
			"2": number,         -- Count of 2-star ratings
			"3": number,         -- Count of 3-star ratings
			"4": number,         -- Count of 4-star ratings
			"5": number          -- Count of 5-star ratings
		}
	},
	learningObjectives = {string}, -- List of what students will learn
	syllabus = string,           -- Course outline/syllabus content
	certificateTemplate = string -- Template ID for completion certificate
}
```text
### Example Course Object

```lua
{
	id = "CRS1001",
	title = "Mathematics 101",
	description = "Introduction to foundational mathematical concepts including algebra, geometry, and basic calculus.",
	imageUrl = "https://example.com/courses/math101.jpg",
	createdAt = "2023-01-10T08:00:00Z",
	updatedAt = "2023-09-15T14:30:00Z",
	status = "published",
	educatorId = "EDU54321",
	category = "Mathematics",
	tags = {"algebra", "geometry", "calculus", "beginner", "foundations"},
	difficulty = "beginner",
	totalLessons = 30,
	totalQuizzes = 10,
	estimatedHours = 45,
	prerequisites = {},  -- No prerequisites
	lessons = {"LSN1001", "LSN1002", "LSN1003", "LSN1004", "LSN1005"},
	quizzes = {"QZ1001", "QZ1002", "QZ1003"},
	students = {"STU12345", "STU12346", "STU12347"},
	ratings = {
		average = 4.7,
		count = 156,
		distribution = {
			"1": 2,
			"2": 4,
			"3": 10,
			"4": 35,
			"5": 105
		}
	},
	learningObjectives = {
		"Understand basic algebraic equations",
		"Apply geometric principles to solve real-world problems",
		"Grasp fundamental calculus concepts"
	},
	syllabus = "Week 1: Introduction to Algebra\nWeek 2: Linear Equations\nWeek 3: Quadratic Equations...",
	certificateTemplate = "TPL1001"
}
```text
## Lesson Model

The Lesson model represents individual units of educational content within a course.

```lua
Lesson = {
	id = string,                 -- Unique identifier for the lesson
	courseId = string,           -- ID of the parent course
	title = string,              -- Lesson title
	description = string,        -- Lesson description
	order = number,              -- Sequence order in the course
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	status = string,             -- "draft", "published", "archived"
	contentType = string,        -- "video", "text", "interactive", "mixed"
	contentUrl = string,         -- URL to main content (video, image)
	content = string,            -- Text content or transcript
	duration = number,           -- Estimated minutes to complete
	attachments = {              -- Additional learning materials
		{
			type = string,       -- "document", "image", "link"
			title = string,      -- Attachment title
			url = string,        -- URL to the attachment
			description = string -- Brief description of the attachment
		}
	},
	nextLessonId = string,       -- ID of next lesson (for navigation)
	previousLessonId = string,   -- ID of previous lesson (for navigation)
	hasQuiz = boolean,           -- Whether lesson has associated quiz
	quizId = string,             -- ID of associated quiz (if applicable)
	interactiveElements = {      -- Interactive elements in the lesson
		{
			type = string,       -- "poll", "question", "exercise"
			title = string,      -- Element title
			content = string,    -- Element content/question
			options = {string},  -- Possible responses (if applicable)
			correctAnswer = any  -- Correct answer (if applicable)
		}
	},
	learningObjectives = {string}, -- Specific objectives for this lesson
	keyTerms = {                 -- Key terminology introduced
		{
			term = string,       -- Term name
			definition = string  -- Term definition
		}
	},
	authorNotes = string,        -- Notes from the author for context
	visibilityConditions = {     -- Conditions for lesson visibility
		prerequisiteLessons = {LessonId}, -- Lessons that must be completed
		minGrade = number        -- Minimum grade required in previous quiz
	}
}
```text
### Example Lesson Object

```lua
{
	id = "LSN1001",
	courseId = "CRS1001",
	title = "Introduction to Algebra",
	description = "This lesson introduces the basic concepts of algebra and variables.",
	order = 1,
	createdAt = "2023-01-15T10:30:00Z",
	updatedAt = "2023-09-10T15:45:00Z",
	status = "published",
	contentType = "mixed",
	contentUrl = "https://example.com/videos/intro-algebra.mp4",
	content = "Algebra is the branch of mathematics that deals with symbols and the rules for manipulating those symbols...",
	duration = 45,
	attachments = {
		{
			type = "document",
			title = "Algebra Cheat Sheet",
			url = "https://example.com/documents/algebra-cheatsheet.pdf",
			description = "Quick reference guide for algebraic formulas"
		},
		{
			type = "image",
			title = "Variables Visualization",
			url = "https://example.com/images/variables-explained.jpg",
			description = "Visual representation of variables in equations"
		}
	},
	nextLessonId = "LSN1002",
	previousLessonId = null,
	hasQuiz = true,
	quizId = "QZ1001",
	interactiveElements = {
		{
			type = "exercise",
			title = "Solve for X",
			content = "If 2x + 3 = 9, what is the value of x?",
			options = ["2", "3", "4", "6"],
			correctAnswer = "3"
		}
	},
	learningObjectives = [
		"Understand what variables represent in equations",
		"Learn to solve basic algebraic equations",
		"Apply algebraic thinking to word problems"
	],
	keyTerms = {
		{
			term = "Variable",
			definition = "A symbol, usually a letter, that represents a value which may vary."
		},
		{
			term = "Equation",
			definition = "A statement asserting the equality of two expressions."
		}
	},
	authorNotes = "Start with concrete examples before moving to abstract concepts for beginners.",
	visibilityConditions = {
		prerequisiteLessons = [],
		minGrade = 0
	}
}
```text
## Quiz Model

The Quiz model represents assessments that test understanding of course content.

```lua
Quiz = {
	id = string,                 -- Unique identifier for the quiz
	courseId = string,           -- ID of the parent course
	lessonId = string,           -- ID of the associated lesson (if applicable)
	title = string,              -- Quiz title
	description = string,        -- Quiz description
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	timeLimit = number,          -- Time limit in minutes (0 for unlimited)
	passingScore = number,       -- Minimum score to pass (percentage)
	attemptLimit = number,       -- Maximum allowed attempts (0 for unlimited)
	shuffleQuestions = boolean,  -- Whether to randomize question order
	showCorrectAnswers = boolean, -- Show correct answers after submission
	questions = {                -- List of questions
		{
			id = string,         -- Question identifier
			type = string,       -- "multiple-choice", "true-false", "short-answer"
			text = string,       -- Question text
			options = {string},  -- Answer options (for multiple-choice)
			correctAnswer = any, -- Correct answer or index
			points = number,     -- Points awarded for correct answer
			explanation = string, -- Explanation of the correct answer
			difficulty = string, -- "easy", "medium", "hard"
			media = {            -- Optional media for the question
				type = string,   -- "image", "audio", "video"
				url = string,    -- URL to the media
				caption = string -- Caption for the media
			}
		}
	},
	totalPoints = number,        -- Sum of all question points
	feedback = {                 -- Customized feedback based on score
		{
			minScore = number,   -- Minimum score for this feedback
			maxScore = number,   -- Maximum score for this feedback
			message = string     -- Feedback message
		}
	},
	tags = {string},             -- Tags for categorizing questions
	isGraded = boolean,          -- Whether quiz affects final grade
	weight = number,             -- Weight in course grade calculation
	requiresProctoring = boolean, -- Whether proctoring is required
	availableFrom = DateTime,    -- When quiz becomes available
	availableUntil = DateTime,   -- When quiz becomes unavailable
	showResultsImmediately = boolean, -- Show results immediately after completion
	allowReview = boolean,       -- Allow students to review answers later
	prerequisites = {            -- Requirements to unlock quiz
		lessons = {LessonId},    -- Lessons that must be completed
		quizzes = {QuizId}       -- Quizzes that must be passed
	}
}
```text
### Example Quiz Object

```lua
{
	id = "QZ1001",
	courseId = "CRS1001",
	lessonId = "LSN1001",
	title = "Algebra Fundamentals Quiz",
	description = "Test your understanding of basic algebraic concepts.",
	createdAt = "2023-01-20T14:00:00Z",
	updatedAt = "2023-09-15T11:30:00Z",
	timeLimit = 30,
	passingScore = 70,
	attemptLimit = 3,
	shuffleQuestions = true,
	showCorrectAnswers = false,
	questions = {
		{
			id = "Q1001",
			type = "multiple-choice",
			text = "Solve for x: 3x + 5 = 20",
			options = ["x = 3", "x = 5", "x = 7", "x = 15"],
			correctAnswer = 1,  -- Second option (x = 5)
			points = 10,
			explanation = "To solve for x, subtract 5 from both sides: 3x = 15. Then divide by 3: x = 5.",
			difficulty = "easy",
			media = null
		},
		{
			id = "Q1002",
			type = "true-false",
			text = "All quadratic equations have exactly two solutions.",
			options = ["True", "False"],
			correctAnswer = 1,  -- False
			points = 5,
			explanation = "False. Quadratic equations can have zero, one, or two real solutions.",
			difficulty = "medium",
			media = null
		},
		{
			id = "Q1003",
			type = "short-answer",
			text = "What is the value of y in the equation 2y = 18?",
			options = [],
			correctAnswer = "9",
			points = 10,
			explanation = "Divide both sides by 2: y = 9.",
			difficulty = "easy",
			media = {
				type = "image",
				url = "https://example.com/images/equation-visualization.jpg",
				caption = "Visual representation of the equation"
			}
		}
	},
	totalPoints = 25,
	feedback = {
		{
			minScore = 0,
			maxScore = 50,
			message = "You need more practice with algebra fundamentals. Review the lesson material before trying again."
		},
		{
			minScore = 51,
			maxScore = 70,
			message = "You're getting there! Review the areas where you made mistakes and try again."
		},
		{
			minScore = 71,
			maxScore = 100,
			message = "Great job! You have a solid understanding of algebra fundamentals."
		}
	},
	tags = ["algebra", "equations", "beginner"],
	isGraded = true,
	weight = 0.15,  -- 15% of course grade
	requiresProctoring = false,
	availableFrom = "2023-02-01T00:00:00Z",
	availableUntil = "2023-12-31T23:59:59Z",
	showResultsImmediately = true,
	allowReview = true,
	prerequisites = {
		lessons = ["LSN1001"],
		quizzes = []
	}
}
```text
## Resource Model

The Resource model represents supplementary educational materials that can be used across multiple courses.

```lua
Resource = {
	id = string,                 -- Unique identifier for the resource
	title = string,              -- Resource title
	description = string,        -- Resource description
	type = string,               -- "document", "video", "audio", "image", "link"
	url = string,                -- URL to the resource
	fileFormat = string,         -- File format (e.g., "pdf", "mp4", "jpg")
	fileSize = number,           -- Size in bytes
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	createdBy = string,          -- ID of educator who created the resource
	tags = {string},             -- Tags for categorizing and searching
	license = string,            -- Usage license information
	accessLevel = string,        -- "public", "registered", "course-specific"
	courses = {CourseId},        -- Courses using this resource
	downloadable = boolean,      -- Whether students can download it
	version = string,            -- Version number for tracking updates
	metadata = {                 -- Additional metadata based on type
		-- For videos:
		duration = number,       -- Length in seconds
		resolution = string,     -- Video resolution

		-- For documents:
		pageCount = number,      -- Number of pages

		-- For images:
		dimensions = string,     -- Image dimensions

		-- Common:
		language = string,       -- Resource language
		authors = {string},      -- Original authors or creators
		publishedDate = DateTime -- Date of original publication
	}
}
```text
## Assignment Model

The Assignment model represents tasks assigned to students that require submission.

```lua
Assignment = {
	id = string,                 -- Unique identifier for the assignment
	courseId = string,           -- ID of the parent course
	lessonId = string,           -- ID of the associated lesson (if applicable)
	title = string,              -- Assignment title
	description = string,        -- Assignment description
	instructions = string,       -- Detailed instructions
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	dueDate = DateTime,          -- Submission deadline
	points = number,             -- Maximum points possible
	assignedTo = {StudentId},    -- Students assigned to complete
	submissionType = string,     -- "file", "text", "link", "media"
	allowedFileTypes = {string}, -- Allowed file formats for submission
	maxFileSize = number,        -- Maximum file size in MB
	rubric = {                   -- Grading criteria
		{
			criterion = string,  -- Name of criterion
			description = string, -- Description of criterion
			maxPoints = number,  -- Maximum points for this criterion
			levels = {           -- Performance levels
				{
					name = string, -- Level name (e.g., "Excellent")
					points = number, -- Points for this level
					description = string -- Description of this level
				}
			}
		}
	},
	groupAssignment = boolean,   -- Whether submission is by groups
	groupSizeMax = number,       -- Maximum group size (if applicable)
	peerReview = boolean,        -- Whether peer review is required
	peerReviewCount = number,    -- Number of peers to review (if applicable)
	allowLateSubmissions = boolean, -- Whether late submissions are accepted
	latePenalty = {              -- Penalty for late submissions
		type = string,           -- "percent", "points"
		value = number,          -- Amount of penalty
		interval = string,       -- "hour", "day", "week"
		maxPenalty = number      -- Maximum possible penalty
	},
	visibility = boolean,        -- Whether assignment is visible to students
	references = {               -- Reference materials
		{
			title = string,      -- Reference title
			url = string,        -- URL to reference
			description = string -- Brief description
		}
	}
}
```text
## Implementation Notes

1. **Content Versioning**: Implement a versioning system for course content to track changes over time and allow reverting to previous versions if needed.

2. **Media Storage**: Consider using a content delivery network (CDN) for storing and serving media files to ensure fast loading times across different regions.

3. **Accessibility**: Include accessibility metadata for all content to support students with diverse needs. This includes:
   - Alternative text for images
   - Transcripts for audio/video content
   - Descriptions of interactive elements

4. **Content Security**: Implement appropriate access controls to ensure content is only accessible to enrolled students and authorized educators.

5. **Question Banks**: Consider implementing a separate question bank system that allows reusing questions across different quizzes.

## Database Considerations

When implementing these models in a database system:

1. **Performance Optimization**:
   - Index commonly queried fields such as `courseId`, `lessonId`, and `status`
   - Consider denormalizing some data for read-heavy operations
   - Implement caching for frequently accessed content

2. **Storage Efficiency**:
   - Store large text content and media files in dedicated storage systems rather than directly in the database
   - Consider compression for text content where appropriate

3. **Query Patterns**:
   - Optimize for common query patterns like:
   - Retrieving all lessons for a course in correct order
   - Finding all resources used in a specific course
   - Accessing quiz questions with their options and correct answers

4. **Transactions**:
   - Use database transactions when updating related records (e.g., updating a course and its lessons)
   - Implement optimistic concurrency control for collaborative editing scenarios

5. **Backup and Recovery**:
   - Implement regular backups of course content
   - Consider point-in-time recovery options for accidental content deletion

# User Data Models

This document details the data models representing users in the educational platform system, including students, educators, and parents.

## Student Model

The Student model represents learners who engage with courses and educational content.

```lua
Student = {
	id = string,                 -- Unique identifier for the student
	username = string,           -- Student's username for login
	displayName = string,        -- Name displayed in the UI
	email = string,              -- Contact email
	avatarUrl = string,          -- URL to student's profile picture
	createdAt = DateTime,        -- Account creation timestamp
	lastLogin = DateTime,        -- Last login timestamp
	settings = {                 -- User preferences
		darkMode = boolean,      -- UI theme preference
		textSize = number,       -- Font size multiplier (0.8-1.5)
		voiceAssistance = boolean, -- Accessibility setting
		keyboardNavigation = boolean, -- Accessibility setting
		colorblindMode = string  -- Visual accessibility setting
	},
	level = number,              -- Current gamification level
	xp = number,                 -- Experience points accumulated
	enrolledCourses = {CourseId}, -- List of courses the student is enrolled in
	completedCourses = {CourseId}, -- List of completed courses
	currentTier = string,        -- Current reward tier (bronze, silver, gold)
	achievements = {AchievementId}, -- List of earned achievements
	badges = {BadgeId}           -- List of earned badges
}
```text
### Example Student Object

```lua
{
	id = "STU12345",
	username = "johndoe",
	displayName = "John Doe",
	email = "john.doe@example.com",
	avatarUrl = "https://example.com/avatars/johndoe.png",
	createdAt = "2023-01-15T08:30:00Z",
	lastLogin = "2023-10-28T14:22:15Z",
	settings = {
		darkMode = true,
		textSize = 1.2,
		voiceAssistance = false,
		keyboardNavigation = true,
		colorblindMode = "Normal Vision"
	},
	level = 10,
	xp = 7500,
	enrolledCourses = {"CRS1001", "CRS1002", "CRS1003"},
	completedCourses = {"CRS1001"},
	currentTier = "silver",
	achievements = {"ACH1001", "ACH1002", "ACH1003"},
	badges = {"BDG1001", "BDG1002"}
}
```text
## Educator Model

The Educator model represents teachers, instructors, or content creators who manage courses.

```lua
Educator = {
	id = string,                 -- Unique identifier for the educator
	username = string,           -- Educator's username for login
	displayName = string,        -- Name displayed in the UI
	email = string,              -- Contact email
	avatarUrl = string,          -- URL to educator's profile picture
	createdAt = DateTime,        -- Account creation timestamp
	lastLogin = DateTime,        -- Last login timestamp
	biography = string,          -- Professional background information
	credentials = {string},      -- List of qualifications or certifications
	managedCourses = {CourseId}, -- List of courses managed by the educator
	pendingGrades = number,      -- Count of assignments pending review
	settings = {                 -- User preferences
		darkMode = boolean,      -- UI theme preference
		textSize = number,       -- Font size multiplier (0.8-1.5)
		notificationPreferences = { -- Notification settings
			email = boolean,     -- Email notifications enabled
			inApp = boolean      -- In-app notifications enabled
		}
	}
}
```text
### Example Educator Object

```lua
{
	id = "EDU54321",
	username = "profsmith",
	displayName = "Dr. Smith",
	email = "prof.smith@example.edu",
	avatarUrl = "https://example.com/avatars/profsmith.png",
	createdAt = "2022-08-20T10:15:00Z",
	lastLogin = "2023-10-27T09:45:30Z",
	biography = "Mathematics professor with 15 years of teaching experience in advanced calculus and algebra.",
	credentials = {"PhD in Mathematics", "Certified Online Instructor", "Award-winning educator"},
	managedCourses = {"CRS1001", "CRS1004", "CRS1009"},
	pendingGrades = 23,
	settings = {
		darkMode = false,
		textSize = 1.0,
		notificationPreferences = {
			email = true,
			inApp = true
		}
	}
}
```text
## Parent Model

The Parent model represents guardians who monitor student progress and manage screen time.

```lua
Parent = {
	id = string,                 -- Unique identifier for the parent
	username = string,           -- Parent's username for login
	displayName = string,        -- Name displayed in the UI
	email = string,              -- Contact email
	createdAt = DateTime,        -- Account creation timestamp
	lastLogin = DateTime,        -- Last login timestamp
	linkedStudents = {StudentId}, -- List of students linked to this parent
	screenTimeSettings = {       -- Screen time management settings
		dailyLimit = number,     -- Daily usage limit in minutes
		breakInterval = number,  -- Required break interval in minutes
		studyHours = {           -- Allowed study time ranges
			start = Time,        -- Start time (e.g., "14:00")
			end = Time           -- End time (e.g., "18:00")
		}
	},
	notificationPreferences = {  -- Notification settings
		achievementEarned = boolean,  -- Notified when child earns achievement
		quizCompleted = boolean,      -- Notified when child completes quiz
		lowGrade = boolean,           -- Notified when child receives low grade
		dailyReport = boolean         -- Receives daily activity summary
	}
}
```text
### Example Parent Object

```lua
{
	id = "PAR98765",
	username = "parent_doe",
	displayName = "Parent Doe",
	email = "parent.doe@example.com",
	createdAt = "2023-01-20T15:45:00Z",
	lastLogin = "2023-10-26T20:10:05Z",
	linkedStudents = {"STU12345", "STU12346"},
	screenTimeSettings = {
		dailyLimit = 180,        -- 3 hours daily limit
		breakInterval = 30,      -- 30 minute break required
		studyHours = {
			start = "14:00",     -- Study permitted from 2pm
			end = "18:00"        -- Study until 6pm
		}
	},
	notificationPreferences = {
		achievementEarned = true,
		quizCompleted = true,
		lowGrade = true,
		dailyReport = true
	}
}
```text
## User Authentication Model

The Authentication model handles user credentials and login information across all user types.

```lua
Authentication = {
	userId = string,             -- Associated user ID (Student, Educator, or Parent)
	userType = string,           -- "student", "educator", or "parent"
	username = string,           -- Username for login
	passwordHash = string,       -- Securely hashed password
	salt = string,               -- Salt used for password hashing
	emailVerified = boolean,     -- Whether email has been verified
	twoFactorEnabled = boolean,  -- Whether 2FA is enabled
	recoveryEmail = string,      -- Secondary email for account recovery
	lastPasswordChange = DateTime, -- When password was last changed
	sessionTokens = {            -- Active session tokens
		{
			token = string,      -- Session token
			expires = DateTime,  -- Expiration date
			deviceInfo = string  -- Device that created this token
		}
	},
	loginAttempts = {            -- Recent login attempts
		{
			timestamp = DateTime, -- When attempt occurred
			success = boolean,    -- Whether attempt succeeded
			ipAddress = string,   -- IP address of attempt
			location = string     -- Geographic location of attempt
		}
	}
}
```text
## User Relationships Model

The UserRelationship model represents connections between different users in the system.

```lua
UserRelationship = {
	id = string,                 -- Unique identifier for the relationship
	userIdA = string,            -- First user in the relationship
	userTypeA = string,          -- Type of first user
	userIdB = string,            -- Second user in the relationship
	userTypeB = string,          -- Type of second user
	relationshipType = string,   -- "parent-child", "educator-student", "peer"
	createdAt = DateTime,        -- When relationship was established
	status = string,             -- "pending", "active", "inactive"
	permissions = {              -- Permissions granted by relationship
		viewProgress = boolean,  -- Can view progress
		manageSettings = boolean, -- Can manage settings
		receiveNotifications = boolean -- Can receive notifications
	}
}
```text
## Implementation Notes

1. **User Privacy**: All personal data should be handled according to relevant privacy regulations (GDPR, COPPA, etc.). Ensure proper consent mechanisms are in place, especially for students under age 18.

2. **Password Security**: Never store plain text passwords. Always use secure hashing algorithms with unique salts. Consider implementing password strength requirements.

3. **Data Validation**: All user input should be validated server-side. For example:
   - Email addresses should be properly formatted
   - Usernames should meet length and character requirements
   - User-provided URLs should be validated for security

4. **Parent-Child Linking**: Implement a secure verification process for linking parent accounts to student accounts to prevent unauthorized access.

5. **Access Control**: Implement role-based access control to ensure users can only access data appropriate for their role (Student, Educator, Parent).

6. **User Deletion**: Implement mechanisms to handle account deletion requests in compliance with privacy regulations, including cascading deletes or data anonymization.

## Database Considerations

When implementing these models in a database system:

1. Use indexing on frequently queried fields such as `id`, `username`, and `email`.

2. Consider sharding strategies for large user bases to maintain performance.

3. Implement efficient querying for user relationships to ensure parent-child lookups and educator-student relationships can be quickly retrieved.

4. Use database transactions for operations that modify multiple related records to maintain data integrity.

5. Consider caching strategies for frequently accessed user data to reduce database load.

# Educational Platform Data Models Documentation

This document provides a comprehensive overview of the data models used in the ToolboxAI-Solutions educational platform, focusing on user data, course content, and progress tracking. Understanding these models is essential for developers who need to work with the platform's data structures.

## Table of Contents

1. [User Data Models](#user-data-models)
2. [Course Content Models](#course-content-models)
3. [Progress Tracking Models](#progress-tracking-models)
4. [Gamification and Rewards Models](#gamification-and-rewards-models)
5. [Relationships Between Models](#relationships-between-models)
6. [Data Flow Diagrams](#data-flow-diagrams)

## User Data Models

### Student Model

The Student model represents learners who engage with courses and educational content.

```lua
Student = {
	id = string,                 -- Unique identifier for the student
	username = string,           -- Student's username for login
	displayName = string,        -- Name displayed in the UI
	email = string,              -- Contact email
	avatarUrl = string,          -- URL to student's profile picture
	createdAt = DateTime,        -- Account creation timestamp
	lastLogin = DateTime,        -- Last login timestamp
	settings = {                 -- User preferences
		darkMode = boolean,      -- UI theme preference
		textSize = number,       -- Font size multiplier (0.8-1.5)
		voiceAssistance = boolean, -- Accessibility setting
		keyboardNavigation = boolean, -- Accessibility setting
		colorblindMode = string  -- Visual accessibility setting
	},
	level = number,              -- Current gamification level
	xp = number,                 -- Experience points accumulated
	enrolledCourses = {CourseId}, -- List of courses the student is enrolled in
	completedCourses = {CourseId}, -- List of completed courses
	currentTier = string,        -- Current reward tier (bronze, silver, gold)
	achievements = {AchievementId}, -- List of earned achievements
	badges = {BadgeId}           -- List of earned badges
}
```text
### Educator Model

The Educator model represents teachers, instructors, or content creators who manage courses.

```lua
Educator = {
	id = string,                 -- Unique identifier for the educator
	username = string,           -- Educator's username for login
	displayName = string,        -- Name displayed in the UI
	email = string,              -- Contact email
	avatarUrl = string,          -- URL to educator's profile picture
	createdAt = DateTime,        -- Account creation timestamp
	lastLogin = DateTime,        -- Last login timestamp
	biography = string,          -- Professional background information
	credentials = {string},      -- List of qualifications or certifications
	managedCourses = {CourseId}, -- List of courses managed by the educator
	pendingGrades = number,      -- Count of assignments pending review
	settings = {                 -- User preferences
		darkMode = boolean,      -- UI theme preference
		textSize = number,       -- Font size multiplier (0.8-1.5)
		notificationPreferences = { -- Notification settings
			email = boolean,     -- Email notifications enabled
			inApp = boolean      -- In-app notifications enabled
		}
	}
}
```text
### Parent Model

The Parent model represents guardians who monitor student progress and manage screen time.

```lua
Parent = {
	id = string,                 -- Unique identifier for the parent
	username = string,           -- Parent's username for login
	displayName = string,        -- Name displayed in the UI
	email = string,              -- Contact email
	createdAt = DateTime,        -- Account creation timestamp
	lastLogin = DateTime,        -- Last login timestamp
	linkedStudents = {StudentId}, -- List of students linked to this parent
	screenTimeSettings = {       -- Screen time management settings
		dailyLimit = number,     -- Daily usage limit in minutes
		breakInterval = number,  -- Required break interval in minutes
		studyHours = {           -- Allowed study time ranges
			start = Time,        -- Start time (e.g., "14:00")
			end = Time           -- End time (e.g., "18:00")
		}
	},
	notificationPreferences = {  -- Notification settings
		achievementEarned = boolean,  -- Notified when child earns achievement
		quizCompleted = boolean,      -- Notified when child completes quiz
		lowGrade = boolean,           -- Notified when child receives low grade
		dailyReport = boolean         -- Receives daily activity summary
	}
}
```text
## Course Content Models

### Course Model

The Course model represents a complete educational program with multiple lessons and quizzes.

```lua
Course = {
	id = string,                 -- Unique identifier for the course
	title = string,              -- Course title
	description = string,        -- Course description
	imageUrl = string,           -- Cover image URL
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	status = string,             -- "draft", "published", "archived"
	educatorId = string,         -- ID of educator who created the course
	category = string,           -- Subject category
	tags = {string},             -- Keyword tags for searchability
	difficulty = string,         -- "beginner", "intermediate", "advanced"
	totalLessons = number,       -- Total number of lessons in the course
	totalQuizzes = number,       -- Total number of quizzes in the course
	estimatedHours = number,     -- Estimated hours to complete
	prerequisites = {CourseId},  -- Courses recommended before starting
	lessons = {LessonId},        -- Ordered list of lesson IDs
	quizzes = {QuizId},          -- Ordered list of quiz IDs
	students = {StudentId},      -- Enrolled students
	ratings = {                  -- Course ratings
		average = number,        -- Average rating (1-5)
		count = number,          -- Number of ratings
		distribution = {         -- Distribution of ratings
			"1": number,         -- Count of 1-star ratings
			"2": number,         -- Count of 2-star ratings
			"3": number,         -- Count of 3-star ratings
			"4": number,         -- Count of 4-star ratings
			"5": number          -- Count of 5-star ratings
		}
	}
}
```text
### Lesson Model

The Lesson model represents individual units of educational content within a course.

```lua
Lesson = {
	id = string,                 -- Unique identifier for the lesson
	courseId = string,           -- ID of the parent course
	title = string,              -- Lesson title
	description = string,        -- Lesson description
	order = number,              -- Sequence order in the course
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	status = string,             -- "draft", "published", "archived"
	contentType = string,        -- "video", "text", "interactive"
	contentUrl = string,         -- URL to main content (video, image)
	content = string,            -- Text content or transcript
	duration = number,           -- Estimated minutes to complete
	attachments = {              -- Additional learning materials
		{
			type = string,       -- "document", "image", "link"
			title = string,      -- Attachment title
			url = string         -- URL to the attachment
		}
	},
	nextLessonId = string,       -- ID of next lesson (for navigation)
	previousLessonId = string,   -- ID of previous lesson (for navigation)
	hasQuiz = boolean,           -- Whether lesson has associated quiz
	quizId = string              -- ID of associated quiz (if applicable)
}
```text
### Quiz Model

The Quiz model represents assessments that test understanding of course content.

```lua
Quiz = {
	id = string,                 -- Unique identifier for the quiz
	courseId = string,           -- ID of the parent course
	lessonId = string,           -- ID of the associated lesson (if applicable)
	title = string,              -- Quiz title
	description = string,        -- Quiz description
	createdAt = DateTime,        -- Creation timestamp
	updatedAt = DateTime,        -- Last update timestamp
	timeLimit = number,          -- Time limit in minutes (0 for unlimited)
	passingScore = number,       -- Minimum score to pass (percentage)
	attemptLimit = number,       -- Maximum allowed attempts (0 for unlimited)
	shuffleQuestions = boolean,  -- Whether to randomize question order
	showCorrectAnswers = boolean, -- Show correct answers after submission
	questions = {                -- List of questions
		{
			id = string,         -- Question identifier
			type = string,       -- "multiple-choice", "true-false", "short-answer"
			text = string,       -- Question text
			options = {string},  -- Answer options (for multiple-choice)
			correctAnswer = any, -- Correct answer or index
			points = number,     -- Points awarded for correct answer
			explanation = string -- Explanation of the correct answer
		}
	},
	totalPoints = number         -- Sum of all question points
}
```text
## Progress Tracking Models

### StudentCourseProgress Model

Tracks a student's progress through a specific course.

```lua
StudentCourseProgress = {
	studentId = string,          -- Student identifier
	courseId = string,           -- Course identifier
	enrolledAt = DateTime,       -- Enrollment timestamp
	lastAccessed = DateTime,     -- Last access timestamp
	status = string,             -- "in-progress", "completed", "paused"
	completedLessons = {         -- Lessons completed
		lessonId = string,       -- Lesson identifier
		completedAt = DateTime,  -- Completion timestamp
		timeSpent = number       -- Minutes spent on lesson
	},
	completedQuizzes = {         -- Quizzes completed
		quizId = string,         -- Quiz identifier
		completedAt = DateTime,  -- Completion timestamp
		attempts = number,       -- Number of attempts made
		score = number,          -- Highest score achieved (percentage)
		timeSpent = number       -- Minutes spent on quiz
	},
	currentLessonId = string,    -- Current lesson in progress
	progressPercentage = number, -- Overall course completion percentage
	certificateIssued = boolean, -- Whether course certificate was issued
	certificateUrl = string,     -- URL to downloadable certificate
	totalTimeSpent = number,     -- Total minutes spent in course
	notes = {                    -- Student's personal notes
		{
			lessonId = string,   -- Associated lesson
			text = string,       -- Note content
			createdAt = DateTime -- Creation timestamp
		}
	}
}
```text
### QuizAttempt Model

Records details of each attempt a student makes on a quiz.

```lua
QuizAttempt = {
	id = string,                 -- Unique identifier for the attempt
	studentId = string,          -- Student identifier
	quizId = string,             -- Quiz identifier
	courseId = string,           -- Course identifier
	startedAt = DateTime,        -- Start timestamp
	completedAt = DateTime,      -- Completion timestamp
	timeSpent = number,          -- Minutes spent
	score = number,              -- Score achieved (percentage)
	passed = boolean,            -- Whether the passing score was achieved
	answers = {                  -- Student's answers
		{
			questionId = string, -- Question identifier
			answer = any,        -- Student's answer
			correct = boolean,   -- Whether answer was correct
			pointsEarned = number -- Points earned for this answer
		}
	},
	feedback = string,           -- Educator feedback (if any)
	attemptNumber = number       -- Sequential attempt number for this quiz
}
```text
### ActivityLog Model

Records detailed student activity for analytics and parental monitoring.

```lua
ActivityLog = {
	id = string,                 -- Unique identifier for the log entry
	studentId = string,          -- Student identifier
	timestamp = DateTime,        -- When the activity occurred
	activityType = string,       -- "login", "lesson-start", "lesson-complete",
								-- "quiz-start", "quiz-complete", "achievement-earned"
	courseId = string,           -- Associated course (if applicable)
	lessonId = string,           -- Associated lesson (if applicable)
	quizId = string,             -- Associated quiz (if applicable)
	achievementId = string,      -- Associated achievement (if applicable)
	details = {                  -- Additional activity details
		timeSpent = number,      -- Minutes spent (if applicable)
		score = number,          -- Quiz score (if applicable)
		progress = number        -- Progress percentage (if applicable)
	},
	deviceInfo = {               -- Information about the device used
		type = string,           -- "desktop", "tablet", "mobile"
		browser = string,        -- Browser name and version
		os = string              -- Operating system
	}
}
```text
## Gamification and Rewards Models

### Achievement Model

Represents specific accomplishments that students can earn.

```lua
Achievement = {
	id = string,                 -- Unique identifier for the achievement
	title = string,              -- Achievement title
	description = string,        -- Achievement description
	imageUrl = string,           -- Badge icon URL
	createdAt = DateTime,        -- Creation timestamp
	category = string,           -- "learning", "participation", "milestone"
	difficulty = string,         -- "easy", "medium", "hard"
	xpReward = number,           -- XP awarded for earning this achievement
	criteria = {                 -- Requirements to earn achievement
		type = string,           -- "course-completion", "quiz-score",
								-- "lesson-streak", "time-spent"
		threshold = number,      -- Required number to achieve
		courseId = string,       -- Specific course (if applicable)
		quizId = string          -- Specific quiz (if applicable)
	},
	rarity = string,             -- "common", "uncommon", "rare", "legendary"
	visibleToAll = boolean       -- Whether achievement is visible before earning
}
```text
### Badge Model

Represents visual indicators of accomplishments displayed on student profiles.

```lua
Badge = {
	id = string,                 -- Unique identifier for the badge
	title = string,              -- Badge title
	description = string,        -- Badge description
	imageUrl = string,           -- Badge icon URL
	createdAt = DateTime,        -- Creation timestamp
	category = string,           -- "course", "skill", "special"
	tier = string,               -- "bronze", "silver", "gold", "platinum"
	associatedAchievements = {AchievementId}, -- Achievements that award this badge
	displayPriority = number,    -- Order priority for display (lower = higher priority)
	expiryDays = number          -- Days until badge expires (0 = never)
}
```text
### Challenge Model

Represents time-limited tasks that students can complete for rewards.

```lua
Challenge = {
	id = string,                 -- Unique identifier for the challenge
	title = string,              -- Challenge title
	description = string,        -- Challenge description
	createdAt = DateTime,        -- Creation timestamp
	startDate = DateTime,        -- When challenge becomes available
	endDate = DateTime,          -- When challenge expires
	xpReward = number,           -- XP awarded for completing the challenge
	badgeId = string,            -- Badge awarded (if applicable)
	requirements = {             -- Requirements to complete challenge
		type = string,           -- "lessons-completed", "quiz-score", "login-streak"
		target = number,         -- Target number to achieve
		courseId = string,       -- Specific course (if applicable)
		progress = number        -- Current progress (0-100%)
	},
	difficulty = string,         -- "easy", "medium", "hard"
	category = string,           -- "daily", "weekly", "special"
	completedBy = {StudentId}    -- Students who have completed this challenge
}
```text
### Reward Model

Represents items or benefits that students can purchase with XP.

```lua
Reward = {
	id = string,                 -- Unique identifier for the reward
	name = string,               -- Reward name
	description = string,        -- Reward description
	imageUrl = string,           -- Reward image URL
	createdAt = DateTime,        -- Creation timestamp
	cost = number,               -- XP cost to redeem
	category = string,           -- "avatar", "theme", "certificate", "boost"
	tier = string,               -- "basic", "bronze", "silver", "gold"
	availability = string,       -- "always", "limited", "seasonal"
	startDate = DateTime,        -- Start of availability period (if limited)
	endDate = DateTime,          -- End of availability period (if limited)
	limitedQuantity = number,    -- Total available (0 = unlimited)
	remainingQuantity = number,  -- Number still available
	redeemedBy = {StudentId},    -- Students who have redeemed this reward
	effects = {                  -- Reward effects when redeemed
		type = string,           -- "visual", "functional", "status"
		duration = number,       -- Duration in days (0 = permanent)
		multiplier = number      -- Effect multiplier (e.g., XP boost)
	}
}
```text
## Relationships Between Models

The following diagram outlines the key relationships between data models in the ToolboxAI-Solutions educational platform:

```text
Student
  ├── enrolledCourses → Course
  ├── completedCourses → Course
  ├── achievements → Achievement
  └── badges → Badge

Educator
  └── managedCourses → Course

Parent
  └── linkedStudents → Student

Course
  ├── educatorId → Educator
  ├── prerequisites → Course
  ├── lessons → Lesson
  ├── quizzes → Quiz
  └── students → Student

Lesson
  ├── courseId → Course
  ├── nextLessonId → Lesson
  ├── previousLessonId → Lesson
  └── quizId → Quiz

Quiz
  ├── courseId → Course
  └── lessonId → Lesson

StudentCourseProgress
  ├── studentId → Student
  ├── courseId → Course
  ├── completedLessons → Lesson
  ├── completedQuizzes → Quiz
  └── currentLessonId → Lesson

QuizAttempt
  ├── studentId → Student
  ├── quizId → Quiz
  └── courseId → Course

ActivityLog
  ├── studentId → Student
  ├── courseId → Course
  ├── lessonId → Lesson
  ├── quizId → Quiz
  └── achievementId → Achievement

Achievement
  ├── courseId → Course
  └── quizId → Quiz

Badge
  └── associatedAchievements → Achievement

Challenge
  ├── badgeId → Badge
  ├── courseId → Course
  └── completedBy → Student

Reward
  └── redeemedBy → Student
```text
## Data Flow Diagrams

### User Progress Flow

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Student   │────▶│    Lesson   │────▶│     Quiz    │────▶│ Achievement │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
		│                  │                  │                    │
		│                  │                  │                    │
		▼                  ▼                  ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│StudentCourse│     │  Activity   │     │QuizAttempt  │     │    Badge    │
│  Progress   │◀────│     Log     │◀────│             │◀────│             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
		│                                                          │
		│                                                          │
		▼                                                          ▼
┌─────────────┐                                            ┌─────────────┐
│     XP      │───────────────────────────────────────────▶│   Reward    │
│Accumulation │                                            │ Redemption  │
└─────────────┘                                            └─────────────┘
```text
### Parental Monitoring Flow

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Student   │────▶│  Activity   │────▶│    Parent   │
│  Activity   │     │     Log     │     │ Notification│
└─────────────┘     └─────────────┘     └─────────────┘
		│                  │                  │
		│                  │                  │
		▼                  ▼                  ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Screen   │     │  Progress   │     │  Parental   │
│Time Settings│◀────│   Reports   │◀────│   Portal    │
└─────────────┘     └─────────────┘     └─────────────┘
```text
### Educator Content Management Flow

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Educator   │────▶│    Course   │────▶│    Lesson   │────▶│     Quiz    │
│  Creation   │     │   Creation  │     │  Creation   │     │  Creation   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
		│                  │                  │                    │
		│                  │                  │                    │
		▼                  ▼                  ▼                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Student    │     │   Course    │     │    Quiz     │     │  Educator   │
│ Enrollment  │◀────│  Publishing │◀────│ Assessment  │◀────│  Dashboard  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```text