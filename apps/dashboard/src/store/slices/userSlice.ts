import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { UserRole } from "../../types";

interface UserState {
  userId?: string;
  id?: string; // Alias for userId
  email?: string;
  displayName?: string;
  firstName?: string;
  lastName?: string;
  avatarUrl?: string;
  role: UserRole;
  isAuthenticated: boolean;
  token?: string;
  refreshToken?: string;
  schoolId?: string;
  classIds?: string[];
}

const initialState: UserState = {
  role: "teacher",
  // Auto-authenticate in development, but not during E2E tests
  isAuthenticated: process.env.NODE_ENV === 'development' && !import.meta.env.VITE_E2E_TESTING,
  userId: import.meta.env.VITE_E2E_TESTING ? undefined : "dev-user-001",
  email: import.meta.env.VITE_E2E_TESTING ? undefined : "teacher@example.com",
  displayName: import.meta.env.VITE_E2E_TESTING ? undefined : "Development Teacher",
  firstName: import.meta.env.VITE_E2E_TESTING ? undefined : "Development",
  lastName: import.meta.env.VITE_E2E_TESTING ? undefined : "Teacher",
  token: import.meta.env.VITE_E2E_TESTING ? undefined : "dev-token",
};

export const userSlice = createSlice({
  name: "user",
  initialState,
  reducers: {
    setRole(state, action: PayloadAction<UserRole>) {
      state.role = action.payload;
    },
    setUser(state, action: PayloadAction<Partial<UserState>>) {
      Object.assign(state, action.payload);
    },
    signInSuccess(
      state,
      action: PayloadAction<{
        userId: string;
        email: string;
        displayName: string;
        avatarUrl?: string;
        role: UserRole;
        token: string;
        refreshToken: string;
        schoolId?: string;
        classIds?: string[];
      }>
    ) {
      state.isAuthenticated = true;
      state.userId = action.payload.userId;
      state.email = action.payload.email;
      state.displayName = action.payload.displayName;
      state.avatarUrl = action.payload.avatarUrl;
      state.role = action.payload.role;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      state.schoolId = action.payload.schoolId;
      state.classIds = action.payload.classIds;
    },
    signOut(state) {
      Object.assign(state, initialState);
    },
    updateToken(state, action: PayloadAction<{ token: string; refreshToken: string }>) {
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
    },
  },
});

export const { setRole, setUser, signInSuccess, signOut, updateToken } = userSlice.actions;
export default userSlice.reducer;
