import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ClassData {
  id: string;
  name: string;
  grade_level: number;
  subject: string;
  teacher_id: string;
  teacher_name: string;
  student_count: number;
  schedule?: any;
  max_students: number;
  is_active: boolean;
  is_online: boolean;
  average_progress: number;
  created_at: string;
  updated_at: string;
}

interface ClassesState {
  list: ClassData[];
  selectedClass: ClassData | null;
  loading: boolean;
  error: string | null;
  lastFetch: number | null;
}

const initialState: ClassesState = {
  list: [],
  selectedClass: null,
  loading: false,
  error: null,
  lastFetch: null,
};

const classesSlice = createSlice({
  name: 'classes',
  initialState,
  reducers: {
    setClasses: (state, action: PayloadAction<ClassData[]>) => {
      state.list = action.payload;
      state.lastFetch = Date.now();
      state.error = null;
    },
    addClass: (state, action: PayloadAction<ClassData>) => {
      state.list.push(action.payload);
    },
    updateClass: (state, action: PayloadAction<ClassData>) => {
      const index = state.list.findIndex(c => c.id === action.payload.id);
      if (index !== -1) {
        state.list[index] = action.payload;
      }
      if (state.selectedClass?.id === action.payload.id) {
        state.selectedClass = action.payload;
      }
    },
    removeClass: (state, action: PayloadAction<string>) => {
      state.list = state.list.filter(c => c.id !== action.payload);
      if (state.selectedClass?.id === action.payload) {
        state.selectedClass = null;
      }
    },
    selectClass: (state, action: PayloadAction<ClassData | null>) => {
      state.selectedClass = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearClasses: (state) => {
      state.list = [];
      state.selectedClass = null;
      state.lastFetch = null;
    },
    enrollStudent: (state, action: PayloadAction<{ classId: string; studentId: string }>) => {
      const classItem = state.list.find(c => c.id === action.payload.classId);
      if (classItem) {
        classItem.student_count += 1;
      }
    },
    unenrollStudent: (state, action: PayloadAction<{ classId: string; studentId: string }>) => {
      const classItem = state.list.find(c => c.id === action.payload.classId);
      if (classItem && classItem.student_count > 0) {
        classItem.student_count -= 1;
      }
    },
    setClassOnlineStatus: (state, action: PayloadAction<{ classId: string; isOnline: boolean }>) => {
      const classItem = state.list.find(c => c.id === action.payload.classId);
      if (classItem) {
        classItem.is_online = action.payload.isOnline;
      }
      if (state.selectedClass?.id === action.payload.classId) {
        state.selectedClass.is_online = action.payload.isOnline;
      }
    },
  },
});

export const {
  setClasses,
  addClass,
  updateClass,
  removeClass,
  selectClass,
  setLoading,
  setError,
  clearClasses,
  enrollStudent,
  unenrollStudent,
  setClassOnlineStatus,
} = classesSlice.actions;

export default classesSlice.reducer;