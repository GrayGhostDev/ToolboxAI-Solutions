# API Endpoint Summary

Generated: 2025-09-10T10:49:00.285658
Total Endpoints: 69

## API v1

- **GET /api/v1/users** - Get Users V1

## API v2

- **GET /api/v2/users** - Get Users V2

## Admin API v1

- **GET /api/v1/admin/users** - List Users
- **POST /api/v1/admin/users** - Create User
- **PUT /api/v1/admin/users/{user_id}** - Update User
- **DELETE /api/v1/admin/users/{user_id}** - Delete User

## Administration

- **POST /admin/broadcast** - Admin Broadcast
- **GET /admin/status** - Get Admin Status

## Agent System

- **GET /agents/health** - Get Agents Health

## Analytics

- **GET /analytics/subject_mastery** - Get Subject Mastery
- **GET /analytics/weekly_xp** - Get Weekly Xp

## Analytics API v1

- **GET /api/v1/analytics/summary** - Get Dashboard Summary

## Assessments

- **GET /assessments/** - Get Assessments
- **POST /assessments/** - Create Assessment
- **GET /assessments/{assessment_id}** - Get Assessment Details
- **GET /assessments/{assessment_id}/results** - Get Assessment Results
- **GET /assessments/{assessment_id}/statistics** - Get Assessment Statistics
- **POST /assessments/{assessment_id}/submit** - Submit Assessment

## Authentication

- **POST /auth/login** - Login
- **POST /auth/refresh** - Refresh Access Token
- **POST /auth/token** - Create Access Token

## Classes

- **GET /classes/** - Get Classes
- **POST /classes/** - Create Class
- **GET /classes/{class_id}** - Get Class Details
- **PUT /classes/{class_id}** - Update Class
- **DELETE /classes/{class_id}** - Delete Class
- **GET /classes/{class_id}/students** - Get Class Students

## Compliance

- **GET /compliance/status** - Get Compliance Status

## Content API

- **POST /api/v1/content/generate** - Api Generate Content

## Content Generation

- **POST /generate_content** - Generate Content
- **POST /generate_quiz** - Generate Quiz
- **POST /generate_terrain** - Generate Terrain

## Content Management

- **GET /content/{content_id}** - Get Content

## Dashboard

- **GET /dashboard/admin** - Get Admin Dashboard
- **GET /dashboard/metrics** - Get Dashboard Metrics
- **GET /dashboard/notifications** - Get Notifications
- **GET /dashboard/overview/{role}** - Get Dashboard Overview
- **GET /dashboard/parent** - Get Parent Dashboard
- **GET /dashboard/quick-stats** - Get Quick Stats
- **GET /dashboard/student** - Get Student Dashboard
- **GET /dashboard/teacher** - Get Teacher Dashboard

## Gamification

- **GET /gamification/leaderboard** - Get Leaderboard

## LMS Integration

- **GET /lms/course/{course_id}** - Get Lms Course
- **GET /lms/courses** - List Lms Courses

## Lessons

- **GET /lessons** - Get Lessons
- **POST /lessons/** - Create Lesson
- **GET /lessons/{lesson_id}** - Get Lesson Details
- **PUT /lessons/{lesson_id}/progress** - Update Lesson Progress
- **GET /lessons/{lesson_id}/statistics** - Get Lesson Statistics

## Messages

- **GET /messages/** - Get Messages
- **POST /messages/** - Send Message
- **GET /messages/notifications/recent** - Get Recent Notifications
- **GET /messages/unread-count** - Get Unread Message Count
- **GET /messages/{message_id}** - Get Message Details
- **DELETE /messages/{message_id}** - Delete Message
- **PUT /messages/{message_id}/archive** - Archive Message
- **PUT /messages/{message_id}/read** - Mark Message As Read

## Plugin Management

- **POST /plugin/message** - Send Plugin Message
- **POST /plugin/register** - Register Plugin

## Reports

- **GET /reports/** - Get Reports
- **POST /reports/** - Generate Report
- **GET /reports/analytics/engagement** - Get Engagement Analytics
- **GET /reports/stats/overview** - Get Overview Statistics
- **GET /reports/templates** - Get Report Templates
- **GET /reports/{report_id}** - Get Report Details

## Reports API v1

- **GET /api/v1/reports/download/{report_id}** - Download Report
- **POST /api/v1/reports/generate** - Generate Report

## Schools

- **GET /schools/** - List Schools
- **POST /schools/** - Create School
- **GET /schools/{school_id}** - Get School

## System

- **GET /api/versions** - Get Api Versions
- **GET /health** - Health Check
- **GET /info** - Get Info
- **GET /metrics** - Get Metrics
- **GET /sentry/status** - Get Sentry Status
- **POST /sync** - Sync With Flask

## User Management

- **GET /api/v1/user/profile** - Get User Profile
- **PUT /api/v1/user/profile** - Update User Profile

## Users

- **GET /users/** - List Users
- **GET /users/{user_id}** - Get User
