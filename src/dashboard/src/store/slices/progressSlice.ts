import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as api from '../../services/api';
import type { StudentProgress, SubjectProgress, ProgressPoint } from '../../types/api';

interface ClassProgressData {
  classId: string;
  className: string;
  averageProgress: number;
  studentCount: number;
  topPerformers: Array<{
    studentId: string;
    displayName: string;
    progress: number;
    xp: number;
  }>;
  strugglingStudents: Array<{
    studentId: string;
    displayName: string;
    progress: number;
    areas: string[];
  }>;
  subjectBreakdown: SubjectProgress[];
  weeklyTrend: ProgressPoint[];
}

interface LessonAnalytics {
  lessonId: string;
  title: string;
  completionRate: number;
  averageScore: number;
  averageTimeMinutes: number;
  totalAttempts: number;
  masteryDistribution: {
    mastered: number;
    proficient: number;
    developing: number;
    struggling: number;
  };
}

interface ProgressState {
  studentProgress: Record<string, StudentProgress>;
  classProgress: Record<string, ClassProgressData>;
  lessonAnalytics: Record<string, LessonAnalytics>;
  currentStudentId: string | null;
  currentClassId: string | null;
  loading: boolean;
  error: string | null;
  filters: {
    dateRange: number; // days back
    subject?: string;
    classId?: string;
  };
  comparisons: {
    students: string[];
    isComparing: boolean;
    data: Record<string, StudentProgress>;
  };
}

const initialState: ProgressState = {
  studentProgress: {},
  classProgress: {},
  lessonAnalytics: {},
  currentStudentId: null,
  currentClassId: null,
  loading: false,
  error: null,
  filters: {
    dateRange: 30,
  },
  comparisons: {
    students: [],
    isComparing: false,
    data: {},
  },
};

// Async thunks
export const fetchStudentProgress = createAsyncThunk(
  'progress/fetchStudent',
  async ({ studentId, daysBack = 30 }: { studentId: string; daysBack?: number }) => {
    console.error('Fetching student progress for', studentId, 'with', daysBack, 'days back');
    const response = await api.getStudentProgress(studentId);
    return { 
      studentId, 
      data: response, 
      daysBack,
      fetchedAt: new Date().toISOString() 
    };
  }
);

export const fetchClassProgress = createAsyncThunk(
  'progress/fetchClass',
  async ({ classId, daysBack = 30 }: { classId: string; daysBack?: number }) => {
    console.error('Fetching class progress for', classId, 'with', daysBack, 'days back');
    const response = await api.getClassProgress(classId);
    return { 
      classId, 
      data: response, 
      daysBack,
      fetchedAt: new Date().toISOString() 
    };
  }
);

export const fetchLessonAnalytics = createAsyncThunk(
  'progress/fetchLessonAnalytics',
  async ({ lessonId, classId }: { lessonId: string; classId?: string }) => {
    const response = await api.getLessonAnalytics(lessonId, classId);
    return { lessonId, data: response };
  }
);

export const updateStudentProgress = createAsyncThunk(
  'progress/updateStudent',
  async ({ studentId, lessonId, data }: {
    studentId: string;
    lessonId: string;
    data: {
      completion_percentage: number;
      time_spent_minutes: number;
      attempts: number;
      score?: number;
    };
  }) => {
    const response = await api.updateProgress(studentId, lessonId, data);
    return response;
  }
);

export const recordAchievement = createAsyncThunk(
  'progress/recordAchievement',
  async ({ studentId, badgeId, xpEarned }: {
    studentId: string;
    badgeId: string;
    xpEarned: number;
  }) => {
    const response = await api.recordAchievement(studentId, { badgeId, xpEarned });
    return response;
  }
);

export const compareStudents = createAsyncThunk(
  'progress/compareStudents',
  async (studentIds: string[]) => {
    const promises = studentIds.map(id => api.getStudentProgress(id));
    const results = await Promise.all(promises);
    
    const data: Record<string, StudentProgress> = {};
    studentIds.forEach((id, index) => {
      data[id] = results[index];
    });
    
    return data;
  }
);

export const generateProgressReport = createAsyncThunk(
  'progress/generateReport',
  async ({ studentId, format = 'pdf' }: { studentId: string; format?: 'pdf' | 'csv' }) => {
    // This would call an API endpoint to generate a downloadable report in specified format
    console.error('Generating progress report for', studentId, 'in', format, 'format');
    
    const response = await api.getStudentProgress(studentId);
    
    // Return formatted response based on format type
    return {
      ...response,
      reportFormat: format,
      generatedAt: new Date().toISOString(),
      downloadUrl: `/api/reports/progress/${studentId}.${format}`
    };
  }
);

export const getSkillMastery = createAsyncThunk(
  'progress/getSkillMastery',
  async ({ studentId, skillId }: { studentId: string; skillId: string }) => {
    const response = await api.getSkillMastery(studentId, skillId);
    return response;
  }
);

const progressSlice = createSlice({
  name: 'progress',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<ProgressState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        dateRange: 30,
      };
    },
    setCurrentStudent: (state, action: PayloadAction<string | null>) => {
      state.currentStudentId = action.payload;
    },
    setCurrentClass: (state, action: PayloadAction<string | null>) => {
      state.currentClassId = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    startComparison: (state, action: PayloadAction<string[]>) => {
      state.comparisons = {
        students: action.payload,
        isComparing: true,
        data: {},
      };
    },
    endComparison: (state) => {
      state.comparisons = {
        students: [],
        isComparing: false,
        data: {},
      };
    },
    updateProgressCache: (state, action: PayloadAction<{
      studentId: string;
      updates: Partial<StudentProgress>;
    }>) => {
      const { studentId, updates } = action.payload;
      if (state.studentProgress[studentId]) {
        state.studentProgress[studentId] = {
          ...state.studentProgress[studentId],
          ...updates,
        };
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch student progress
    builder
      .addCase(fetchStudentProgress.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStudentProgress.fulfilled, (state, action) => {
        state.loading = false;
        state.studentProgress[action.payload.studentId] = action.payload.data;
        state.currentStudentId = action.payload.studentId;
      })
      .addCase(fetchStudentProgress.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch student progress';
      });

    // Fetch class progress
    builder
      .addCase(fetchClassProgress.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchClassProgress.fulfilled, (state, action) => {
        state.loading = false;
        state.classProgress[action.payload.classId] = action.payload.data;
        state.currentClassId = action.payload.classId;
      })
      .addCase(fetchClassProgress.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch class progress';
      });

    // Fetch lesson analytics
    builder
      .addCase(fetchLessonAnalytics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchLessonAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.lessonAnalytics[action.payload.lessonId] = action.payload.data;
        console.error('Lesson analytics loaded for:', action.payload.lessonId);
      })
      .addCase(fetchLessonAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch lesson analytics';
        console.error('Failed to fetch lesson analytics:', action.error);
      });

    // Update student progress
    builder
      .addCase(updateStudentProgress.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateStudentProgress.fulfilled, (state, action) => {
        state.loading = false;
        console.error('Student progress updated:', action.payload);
        // Refresh the student's progress data after update
        if (state.currentStudentId) {
          // In a real app, you might want to refetch the data or update locally
        }
      })
      .addCase(updateStudentProgress.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update progress';
      });

    // Record achievement
    builder
      .addCase(recordAchievement.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(recordAchievement.fulfilled, (state, action) => {
        state.loading = false;
        console.error('Achievement recorded:', action.payload);
        // Update the student's badges/achievements in the progress data
      })
      .addCase(recordAchievement.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to record achievement';
        console.error('Failed to record achievement:', action.error);
      });

    // Compare students
    builder
      .addCase(compareStudents.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(compareStudents.fulfilled, (state, action) => {
        state.loading = false;
        state.comparisons.data = action.payload;
        console.error('Student comparison completed:', Object.keys(action.payload).length, 'students');
      })
      .addCase(compareStudents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to compare students';
        state.comparisons.isComparing = false;
        console.error('Student comparison failed:', action.error);
      });

    // Generate progress report
    builder
      .addCase(generateProgressReport.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generateProgressReport.fulfilled, (state, action) => {
        state.loading = false;
        console.error('Progress report generated:', action.payload);
        // In a real implementation, this would trigger a download
      })
      .addCase(generateProgressReport.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to generate report';
        console.error('Report generation failed:', action.error);
      });

    // Get skill mastery
    builder
      .addCase(getSkillMastery.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getSkillMastery.fulfilled, (state, action) => {
        state.loading = false;
        // Update skill mastery data in the appropriate progress record
      })
      .addCase(getSkillMastery.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch skill mastery';
      });
  },
});

export const {
  setFilters,
  clearFilters,
  setCurrentStudent,
  setCurrentClass,
  clearError,
  startComparison,
  endComparison,
  updateProgressCache,
} = progressSlice.actions;

export default progressSlice.reducer;