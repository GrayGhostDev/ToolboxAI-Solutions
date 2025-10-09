// Helper types for easier usage
export type User = Database['public']['Tables']['users']['Row']
export type Course = Database['public']['Tables']['courses']['Row']
export type Lesson = Database['public']['Tables']['lessons']['Row']
export type Enrollment = Database['public']['Tables']['enrollments']['Row']
export type LessonProgress = Database['public']['Tables']['lesson_progress']['Row']
export type Assignment = Database['public']['Tables']['assignments']['Row']
export type Submission = Database['public']['Tables']['submissions']['Row']
export type Comment = Database['public']['Tables']['comments']['Row']
export type Achievement = Database['public']['Tables']['achievements']['Row']
export type UserAchievement = Database['public']['Tables']['user_achievements']['Row']

// Extended types with relationships
export interface CourseWithInstructor extends Course {
  instructor?: User
  lessons?: Lesson[]
  enrollment_count?: number
}

export interface LessonWithProgress extends Lesson {
  progress?: LessonProgress
  assignments?: Assignment[]
  comments?: CommentWithUser[]
}

export interface CommentWithUser extends Comment {
  user?: User
  replies?: CommentWithUser[]
}

export interface EnrollmentWithCourse extends Enrollment {
  course?: CourseWithInstructor
}

export interface SubmissionWithAssignment extends Submission {
  assignment?: Assignment
  user?: User
}
/**
 * TypeScript Types for ToolboxAI Educational Platform
 * Generated from Supabase Database Schema
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          username: string | null
          full_name: string | null
          avatar_url: string | null
          bio: string | null
          role: string
          created_at: string
          updated_at: string
          last_login_at: string | null
          is_active: boolean
        }
        Insert: {
          id?: string
          email: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          bio?: string | null
          role?: string
          created_at?: string
          updated_at?: string
          last_login_at?: string | null
          is_active?: boolean
        }
        Update: {
          id?: string
          email?: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          bio?: string | null
          role?: string
          created_at?: string
          updated_at?: string
          last_login_at?: string | null
          is_active?: boolean
        }
      }
      courses: {
        Row: {
          id: string
          title: string
          description: string | null
          thumbnail_url: string | null
          instructor_id: string | null
          difficulty_level: string
          is_published: boolean
          price: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          title: string
          description?: string | null
          thumbnail_url?: string | null
          instructor_id?: string | null
          difficulty_level?: string
          is_published?: boolean
          price?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          title?: string
          description?: string | null
          thumbnail_url?: string | null
          instructor_id?: string | null
          difficulty_level?: string
          is_published?: boolean
          price?: number
          created_at?: string
          updated_at?: string
        }
      }
      lessons: {
        Row: {
          id: string
          course_id: string
          title: string
          description: string | null
          content: string | null
          video_url: string | null
          order_index: number
          duration_minutes: number | null
          is_free: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          course_id: string
          title: string
          description?: string | null
          content?: string | null
          video_url?: string | null
          order_index: number
          duration_minutes?: number | null
          is_free?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          course_id?: string
          title?: string
          description?: string | null
          content?: string | null
          video_url?: string | null
          order_index?: number
          duration_minutes?: number | null
          is_free?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      enrollments: {
        Row: {
          id: string
          user_id: string
          course_id: string
          enrolled_at: string
          completed_at: string | null
          progress_percentage: number
        }
        Insert: {
          id?: string
          user_id: string
          course_id: string
          enrolled_at?: string
          completed_at?: string | null
          progress_percentage?: number
        }
        Update: {
          id?: string
          user_id?: string
          course_id?: string
          enrolled_at?: string
          completed_at?: string | null
          progress_percentage?: number
        }
      }
      lesson_progress: {
        Row: {
          id: string
          user_id: string
          lesson_id: string
          completed: boolean
          completed_at: string | null
          time_spent_minutes: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          lesson_id: string
          completed?: boolean
          completed_at?: string | null
          time_spent_minutes?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          lesson_id?: string
          completed?: boolean
          completed_at?: string | null
          time_spent_minutes?: number
          created_at?: string
          updated_at?: string
        }
      }
      assignments: {
        Row: {
          id: string
          lesson_id: string
          title: string
          description: string | null
          instructions: string | null
          due_date: string | null
          max_score: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          lesson_id: string
          title: string
          description?: string | null
          instructions?: string | null
          due_date?: string | null
          max_score?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          lesson_id?: string
          title?: string
          description?: string | null
          instructions?: string | null
          due_date?: string | null
          max_score?: number
          created_at?: string
          updated_at?: string
        }
      }
      submissions: {
        Row: {
          id: string
          assignment_id: string
          user_id: string
          content: string | null
          file_url: string | null
          score: number | null
          feedback: string | null
          submitted_at: string
          graded_at: string | null
        }
        Insert: {
          id?: string
          assignment_id: string
          user_id: string
          content?: string | null
          file_url?: string | null
          score?: number | null
          feedback?: string | null
          submitted_at?: string
          graded_at?: string | null
        }
        Update: {
          id?: string
          assignment_id?: string
          user_id?: string
          content?: string | null
          file_url?: string | null
          score?: number | null
          feedback?: string | null
          submitted_at?: string
          graded_at?: string | null
        }
      }
      comments: {
        Row: {
          id: string
          user_id: string
          lesson_id: string
          content: string
          parent_comment_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          lesson_id: string
          content: string
          parent_comment_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          lesson_id?: string
          content?: string
          parent_comment_id?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      achievements: {
        Row: {
          id: string
          name: string
          description: string | null
          icon_url: string | null
          points: number
          created_at: string
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          icon_url?: string | null
          points?: number
          created_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          icon_url?: string | null
          points?: number
          created_at?: string
        }
      }
      user_achievements: {
        Row: {
          id: string
          user_id: string
          achievement_id: string
          earned_at: string
        }
        Insert: {
          id?: string
          user_id: string
          achievement_id: string
          earned_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          achievement_id?: string
          earned_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}


