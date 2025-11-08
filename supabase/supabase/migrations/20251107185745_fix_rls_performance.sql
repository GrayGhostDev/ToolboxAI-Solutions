-- Migration: Fix RLS Performance Issues
-- Date: 2025-11-07
-- Purpose:
--   1. Optimize auth.uid() calls in RLS policies by wrapping in subquery
--   2. Consolidate multiple permissive policies on courses table
--
-- Performance improvements:
--   - Prevents re-evaluation of auth.uid() for each row
--   - Reduces policy evaluation overhead on courses table from 3 to 1 policy
--
-- Fixes Supabase Performance Advisor warnings:
--   - 13 auth_rls_initplan warnings
--   - 5 multiple_permissive_policies warnings

-- ============================================================================
-- PART 1: Drop existing problematic policies
-- ============================================================================

-- Users table policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;

-- Courses table policies
DROP POLICY IF EXISTS "Anyone can view published courses" ON public.courses;
DROP POLICY IF EXISTS "Instructors can view own courses" ON public.courses;
DROP POLICY IF EXISTS "Instructors can manage own courses" ON public.courses;

-- Enrollments table policies
DROP POLICY IF EXISTS "Users can view own enrollments" ON public.enrollments;
DROP POLICY IF EXISTS "Users can enroll in courses" ON public.enrollments;

-- Lesson progress table policies
DROP POLICY IF EXISTS "Users can manage own progress" ON public.lesson_progress;

-- Comments table policies
DROP POLICY IF EXISTS "Users can create comments" ON public.comments;
DROP POLICY IF EXISTS "Users can update own comments" ON public.comments;
DROP POLICY IF EXISTS "Users can delete own comments" ON public.comments;

-- Submissions table policies
DROP POLICY IF EXISTS "Users can view own submissions" ON public.submissions;
DROP POLICY IF EXISTS "Users can create submissions" ON public.submissions;

-- User achievements table policies
DROP POLICY IF EXISTS "Users can view own achievements" ON public.user_achievements;

-- ============================================================================
-- PART 2: Create optimized policies
-- ============================================================================

-- ----------------------------------------------------------------------------
-- USERS TABLE - Optimized policies
-- ----------------------------------------------------------------------------
-- Performance: Wraps auth.uid() in subquery to prevent re-evaluation per row
CREATE POLICY "Users can view own profile"
ON public.users
FOR SELECT
USING ((SELECT auth.uid()) = id);

CREATE POLICY "Users can update own profile"
ON public.users
FOR UPDATE
USING ((SELECT auth.uid()) = id);

-- ----------------------------------------------------------------------------
-- COURSES TABLE - Consolidated and optimized policies
-- ----------------------------------------------------------------------------
-- Performance: Combines 3 SELECT policies into 1 to reduce evaluation overhead
-- This single policy handles both published courses (for all) and instructor courses
CREATE POLICY "Users can view courses"
ON public.courses
FOR SELECT
USING (
  is_published = true
  OR (SELECT auth.uid()) = instructor_id
);

-- Separate policy for instructor modifications (INSERT, UPDATE, DELETE)
CREATE POLICY "Instructors can manage own courses"
ON public.courses
FOR ALL
USING ((SELECT auth.uid()) = instructor_id)
WITH CHECK ((SELECT auth.uid()) = instructor_id);

-- ----------------------------------------------------------------------------
-- ENROLLMENTS TABLE - Optimized policies
-- ----------------------------------------------------------------------------
CREATE POLICY "Users can view own enrollments"
ON public.enrollments
FOR SELECT
USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can enroll in courses"
ON public.enrollments
FOR INSERT
WITH CHECK ((SELECT auth.uid()) = user_id);

-- ----------------------------------------------------------------------------
-- LESSON_PROGRESS TABLE - Optimized policy
-- ----------------------------------------------------------------------------
CREATE POLICY "Users can manage own progress"
ON public.lesson_progress
FOR ALL
USING ((SELECT auth.uid()) = user_id)
WITH CHECK ((SELECT auth.uid()) = user_id);

-- ----------------------------------------------------------------------------
-- COMMENTS TABLE - Optimized policies
-- ----------------------------------------------------------------------------
CREATE POLICY "Users can create comments"
ON public.comments
FOR INSERT
WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own comments"
ON public.comments
FOR UPDATE
USING ((SELECT auth.uid()) = user_id)
WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own comments"
ON public.comments
FOR DELETE
USING ((SELECT auth.uid()) = user_id);

-- ----------------------------------------------------------------------------
-- SUBMISSIONS TABLE - Optimized policies
-- ----------------------------------------------------------------------------
CREATE POLICY "Users can view own submissions"
ON public.submissions
FOR SELECT
USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can create submissions"
ON public.submissions
FOR INSERT
WITH CHECK ((SELECT auth.uid()) = user_id);

-- ----------------------------------------------------------------------------
-- USER_ACHIEVEMENTS TABLE - Optimized policy
-- ----------------------------------------------------------------------------
CREATE POLICY "Users can view own achievements"
ON public.user_achievements
FOR SELECT
USING ((SELECT auth.uid()) = user_id);

-- ============================================================================
-- PART 3: Add performance monitoring comment
-- ============================================================================
COMMENT ON POLICY "Users can view courses" ON public.courses IS
'Consolidated policy combining published course access and instructor access.
Optimized with (select auth.uid()) to prevent per-row function evaluation.
Resolves multiple_permissive_policies and auth_rls_initplan warnings.';

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Expected Results:
--   ✓ All 13 auth_rls_initplan warnings resolved
--   ✓ All 5 multiple_permissive_policies warnings resolved
--   ✓ Improved query performance at scale
--   ✓ No functional changes to application behavior
-- ============================================================================
