import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { UserRole } from "../../types";

interface UserState {
  userId?: string;
  email?: string;
  displayName?: string;
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
  isAuthenticated: false,
};

const userSlice = createSlice({
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