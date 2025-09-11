# API Endpoints

This document lists the main API endpoints for ToolBoxAI-Solutions.

## Lessons
- `GET /api/lessons` — List lessons
- `GET /api/lessons/{id}` — Get lesson details
- `POST /api/lessons` — Create lesson
- `PUT /api/lessons/{id}` — Update lesson
- `DELETE /api/lessons/{id}` — Delete lesson

## Quizzes
- `GET /api/quizzes` — List quizzes
- `GET /api/quizzes/{id}` — Get quiz details
- `POST /api/quizzes` — Create quiz
- `PUT /api/quizzes/{id}` — Update quiz
- `DELETE /api/quizzes/{id}` — Delete quiz

## Gamification
- `GET /api/xp` — Get XP and level
- `POST /api/xp` — Award XP
- `GET /api/achievements` — List achievements
- `POST /api/achievements` — Unlock achievement

## Progress Tracking
- `GET /api/progress` — Get student progress
- `POST /api/progress` — Update progress

## Authentication
- `POST /api/auth/login` — Login
- `POST /api/auth/logout` — Logout
- `POST /api/auth/register` — Register
- `POST /api/auth/forgot-password` — Password reset

## Users
- `GET /api/users` — List users
- `GET /api/users/{id}` — Get user details
- `PUT /api/users/{id}` — Update user
- `DELETE /api/users/{id}` — Delete user
