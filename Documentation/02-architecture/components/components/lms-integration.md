# LMS Integration Module Design

## Overview

- Integrates with Canvas, Schoology, Google Classroom
- Handles authentication, API requests, data extraction

## SchoologyClient

- Authentication: OAuth2
- Endpoints: Course list, assignments, grades
- Data Extraction: Lesson content, student progress

## Content Processors

- Parse LMS data into platform models
- Map assignments to Roblox environments

## API Endpoints

- `/api/lms/courses`
- `/api/lms/assignments`
- `/api/lms/grades`
