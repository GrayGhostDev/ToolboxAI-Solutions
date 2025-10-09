import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

/**
 * User Store - Authentication and user preferences
 *
 * Manages user state, authentication, and preferences.
 * Replaces Redux user slice with simpler Zustand store.
 */

interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'teacher' | 'student';
  avatar?: string;
  preferences: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    notifications: boolean;
    emailDigest: boolean;
  };
}

interface UserState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastLoginAt: Date | null;

  // Actions
  setUser: (user: User) => void;
  updateUser: (updates: Partial<User>) => void;
  updatePreferences: (preferences: Partial<User['preferences']>) => void;
  login: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      lastLoginAt: null,

      // Actions
      setUser: (user) => set({
        user,
        isAuthenticated: true,
        error: null,
      }),

      updateUser: (updates) => set((state) => ({
        user: state.user ? { ...state.user, ...updates } : null,
      })),

      updatePreferences: (preferences) => set((state) => ({
        user: state.user
          ? {
              ...state.user,
              preferences: { ...state.user.preferences, ...preferences },
            }
          : null,
      })),

      login: (user) => set({
        user,
        isAuthenticated: true,
        lastLoginAt: new Date(),
        error: null,
      }),

      logout: () => set({
        user: null,
        isAuthenticated: false,
        lastLoginAt: null,
        error: null,
      }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),
    }),
    {
      name: 'user-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        lastLoginAt: state.lastLoginAt,
      }),
    }
  )
);

// Selectors
export const selectIsAdmin = () =>
  useUserStore.getState().user?.role === 'admin';

export const selectIsTeacher = () =>
  useUserStore.getState().user?.role === 'teacher';

export const selectTheme = () =>
  useUserStore.getState().user?.preferences.theme || 'light';

/**
 * @example
 * ```tsx
 * function UserProfile() {
 *   const { user, updatePreferences } = useUserStore();
 *
 *   if (!user) return null;
 *
 *   return (
 *     <div>
 *       <h1>{user.name}</h1>
 *       <Switch
 *         checked={user.preferences.notifications}
 *         onChange={(e) =>
 *           updatePreferences({ notifications: e.currentTarget.checked })
 *         }
 *         label="Enable notifications"
 *       />
 *     </div>
 *   );
 * }
 * ```
 */
