import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as api from '../../services/api';
import type { Assessment, AssessmentSubmission, Question } from '../../types/api';

interface AssessmentsState {
  assessments: Assessment[];
  currentAssessment: Assessment | null;
  submissions: AssessmentSubmission[];
  currentSubmission: AssessmentSubmission | null;
  loading: boolean;
  submitting: boolean;
  error: string | null;
  filters: {
    classId?: string;
    type?: 'quiz' | 'test' | 'assignment' | 'project';
    status?: 'draft' | 'active' | 'closed' | 'graded';
  };
}

const initialState: AssessmentsState = {
  assessments: [],
  currentAssessment: null,
  submissions: [],
  currentSubmission: null,
  loading: false,
  submitting: false,
  error: null,
  filters: {},
};

// Async thunks
export const fetchAssessments = createAsyncThunk(
  'assessments/fetchAll',
  async (filters?: { classId?: string; type?: string; status?: string }) => {
    const response = await api.listAssessments(filters);
    return response;
  }
);

export const fetchAssessmentById = createAsyncThunk(
  'assessments/fetchById',
  async (assessmentId: string) => {
    const response = await api.getAssessment(assessmentId);
    return response;
  }
);

export const createAssessment = createAsyncThunk(
  'assessments/create',
  async (data: {
    title: string;
    type: 'quiz' | 'test' | 'assignment' | 'project';
    classId: string;
    questions: Question[];
    dueDate?: string;
    maxSubmissions?: number;
  }) => {
    const response = await api.createAssessment(data);
    return response;
  }
);

export const updateAssessment = createAsyncThunk(
  'assessments/update',
  async ({ id, data }: { id: string; data: Partial<Assessment> }) => {
    const response = await api.updateAssessment(id, data);
    return response;
  }
);

export const deleteAssessment = createAsyncThunk(
  'assessments/delete',
  async (assessmentId: string) => {
    await api.deleteAssessment(assessmentId);
    return assessmentId;
  }
);

export const submitAssessment = createAsyncThunk(
  'assessments/submit',
  async ({ assessmentId, answers, timeSpent }: {
    assessmentId: string;
    answers: any[];
    timeSpent?: number;
  }) => {
    const response = await api.submitAssessment(assessmentId, {
      answers,
      time_spent_minutes: timeSpent,
    });
    return response;
  }
);

export const fetchSubmissions = createAsyncThunk(
  'assessments/fetchSubmissions',
  async ({ assessmentId, studentId }: { assessmentId?: string; studentId?: string }) => {
    const response = await api.getSubmissions(assessmentId, studentId);
    return response;
  }
);

export const gradeSubmission = createAsyncThunk(
  'assessments/gradeSubmission',
  async ({ submissionId, score, feedback }: {
    submissionId: string;
    score: number;
    feedback?: string;
  }) => {
    const response = await api.gradeSubmission(submissionId, { score, feedback });
    return response;
  }
);

const assessmentsSlice = createSlice({
  name: 'assessments',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<AssessmentsState['filters']>) => {
      state.filters = action.payload;
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setCurrentAssessment: (state, action: PayloadAction<Assessment | null>) => {
      state.currentAssessment = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateAssessmentInList: (state, action: PayloadAction<Assessment>) => {
      const index = state.assessments.findIndex(a => a.id === action.payload.id);
      if (index !== -1) {
        state.assessments[index] = action.payload;
      }
    },
  },
  extraReducers: (builder) => {
    // Fetch assessments
    builder
      .addCase(fetchAssessments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAssessments.fulfilled, (state, action) => {
        state.loading = false;
        state.assessments = action.payload;
      })
      .addCase(fetchAssessments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch assessments';
      });

    // Fetch assessment by ID
    builder
      .addCase(fetchAssessmentById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAssessmentById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentAssessment = action.payload;
      })
      .addCase(fetchAssessmentById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch assessment';
      });

    // Create assessment
    builder
      .addCase(createAssessment.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createAssessment.fulfilled, (state, action) => {
        state.loading = false;
        state.assessments.push(action.payload);
        state.currentAssessment = action.payload;
      })
      .addCase(createAssessment.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to create assessment';
      });

    // Update assessment
    builder
      .addCase(updateAssessment.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateAssessment.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.assessments.findIndex(a => a.id === action.payload.id);
        if (index !== -1) {
          state.assessments[index] = action.payload;
        }
        if (state.currentAssessment?.id === action.payload.id) {
          state.currentAssessment = action.payload;
        }
      })
      .addCase(updateAssessment.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to update assessment';
      });

    // Delete assessment
    builder
      .addCase(deleteAssessment.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteAssessment.fulfilled, (state, action) => {
        state.loading = false;
        state.assessments = state.assessments.filter(a => a.id !== action.payload);
        if (state.currentAssessment?.id === action.payload) {
          state.currentAssessment = null;
        }
      })
      .addCase(deleteAssessment.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to delete assessment';
      });

    // Submit assessment
    builder
      .addCase(submitAssessment.pending, (state) => {
        state.submitting = true;
        state.error = null;
      })
      .addCase(submitAssessment.fulfilled, (state, action) => {
        state.submitting = false;
        state.currentSubmission = action.payload;
        state.submissions.push(action.payload);
      })
      .addCase(submitAssessment.rejected, (state, action) => {
        state.submitting = false;
        state.error = action.error.message || 'Failed to submit assessment';
      });

    // Fetch submissions
    builder
      .addCase(fetchSubmissions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSubmissions.fulfilled, (state, action) => {
        state.loading = false;
        state.submissions = action.payload;
      })
      .addCase(fetchSubmissions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch submissions';
      });

    // Grade submission
    builder
      .addCase(gradeSubmission.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(gradeSubmission.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.submissions.findIndex(s => s.id === action.payload.id);
        if (index !== -1) {
          state.submissions[index] = action.payload;
        }
        if (state.currentSubmission?.id === action.payload.id) {
          state.currentSubmission = action.payload;
        }
      })
      .addCase(gradeSubmission.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to grade submission';
      });
  },
});

export const {
  setFilters,
  clearFilters,
  setCurrentAssessment,
  clearError,
  updateAssessmentInList,
} = assessmentsSlice.actions;

export default assessmentsSlice.reducer;