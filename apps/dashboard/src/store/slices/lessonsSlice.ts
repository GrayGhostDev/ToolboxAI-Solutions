import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { type Lesson } from '../../types/api';

interface LessonsState {
  list: Lesson[];
  selectedLesson: Lesson | null;
  loading: boolean;
  error: string | null;
  lastFetch: number | null;
  filters: {
    classId?: string;
    subject?: string;
    status?: 'draft' | 'published' | 'archived';
  };
}

const initialState: LessonsState = {
  list: [],
  selectedLesson: null,
  loading: false,
  error: null,
  lastFetch: null,
  filters: {},
};

const lessonsSlice = createSlice({
  name: 'lessons',
  initialState,
  reducers: {
    setLessons: (state, action: PayloadAction<Lesson[]>) => {
      state.list = action.payload;
      state.lastFetch = Date.now();
      state.error = null;
    },
    addLesson: (state, action: PayloadAction<Lesson>) => {
      state.list.unshift(action.payload); // Add to beginning for newest first
    },
    updateLesson: (state, action: PayloadAction<Lesson>) => {
      const index = state.list.findIndex(l => l.id === action.payload.id);
      if (index !== -1) {
        state.list[index] = action.payload;
      }
      if (state.selectedLesson?.id === action.payload.id) {
        state.selectedLesson = action.payload;
      }
    },
    removeLesson: (state, action: PayloadAction<string>) => {
      state.list = state.list.filter(l => l.id !== action.payload);
      if (state.selectedLesson?.id === action.payload) {
        state.selectedLesson = null;
      }
    },
    selectLesson: (state, action: PayloadAction<Lesson | null>) => {
      state.selectedLesson = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setFilters: (state, action: PayloadAction<typeof initialState.filters>) => {
      state.filters = action.payload;
    },
    clearLessons: (state) => {
      state.list = [];
      state.selectedLesson = null;
      state.lastFetch = null;
      state.filters = {};
    },
    publishLesson: (state, action: PayloadAction<string>) => {
      const lesson = state.list.find(l => l.id === action.payload);
      if (lesson) {
        lesson.status = 'published';
      }
      if (state.selectedLesson?.id === action.payload) {
        state.selectedLesson.status = 'published';
      }
    },
    archiveLesson: (state, action: PayloadAction<string>) => {
      const lesson = state.list.find(l => l.id === action.payload);
      if (lesson) {
        lesson.status = 'archived';
      }
      if (state.selectedLesson?.id === action.payload) {
        state.selectedLesson.status = 'archived';
      }
    },
    setRobloxWorldId: (state, action: PayloadAction<{ lessonId: string; worldId: string }>) => {
      const lesson = state.list.find(l => l.id === action.payload.lessonId);
      if (lesson) {
        lesson.robloxWorldId = action.payload.worldId;
      }
      if (state.selectedLesson?.id === action.payload.lessonId) {
        state.selectedLesson.robloxWorldId = action.payload.worldId;
      }
    },
  },
});

export const {
  setLessons,
  addLesson,
  updateLesson,
  removeLesson,
  selectLesson,
  setLoading,
  setError,
  setFilters,
  clearLessons,
  publishLesson,
  archiveLesson,
  setRobloxWorldId,
} = lessonsSlice.actions;

export default lessonsSlice.reducer;