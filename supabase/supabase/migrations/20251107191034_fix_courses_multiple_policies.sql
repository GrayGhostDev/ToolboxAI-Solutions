-- Migration: Fix Multiple Permissive Policies on Courses Table
-- Date: 2025-11-07
-- Purpose:
--   Fix remaining multiple permissive policies warning by splitting
--   the "FOR ALL" instructor policy into separate INSERT/UPDATE/DELETE policies
--
-- Issue:
--   The previous migration used "FOR ALL" which includes SELECT operations,
--   causing duplicate SELECT policies:
--   - "Users can view courses" (FOR SELECT)
--   - "Instructors can manage own courses" (FOR ALL - includes SELECT)
--
-- Solution:
--   Split instructor management into three specific policies:
--   - INSERT policy (for creating courses)
--   - UPDATE policy (for editing courses)
--   - DELETE policy (for deleting courses)
--
-- This ensures only ONE SELECT policy exists on the courses table.

-- ============================================================================
-- Drop the problematic "FOR ALL" policy
-- ============================================================================

DROP POLICY IF EXISTS "Instructors can manage own courses" ON public.courses;

-- ============================================================================
-- Create separate policies for INSERT, UPDATE, DELETE
-- ============================================================================

-- Allow instructors to create their own courses
CREATE POLICY "Instructors can insert own courses"
ON public.courses
FOR INSERT
WITH CHECK ((SELECT auth.uid()) = instructor_id);

-- Allow instructors to update their own courses
CREATE POLICY "Instructors can update own courses"
ON public.courses
FOR UPDATE
USING ((SELECT auth.uid()) = instructor_id)
WITH CHECK ((SELECT auth.uid()) = instructor_id);

-- Allow instructors to delete their own courses
CREATE POLICY "Instructors can delete own courses"
ON public.courses
FOR DELETE
USING ((SELECT auth.uid()) = instructor_id);

-- ============================================================================
-- Verification
-- ============================================================================
-- After this migration, the courses table should have:
-- - 1 SELECT policy: "Users can view courses" (handles both published + instructor)
-- - 1 INSERT policy: "Instructors can insert own courses"
-- - 1 UPDATE policy: "Instructors can update own courses"
-- - 1 DELETE policy: "Instructors can delete own courses"
--
-- This resolves the multiple_permissive_policies warning while maintaining
-- the same functional behavior.
-- ============================================================================
