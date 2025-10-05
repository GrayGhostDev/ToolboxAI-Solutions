import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

/**
 * Dashboard Store - Modern state management with Zustand
 *
 * Replaces Redux for dashboard-specific state.
 * Uses Zustand for simpler, more performant state management.
 *
 * Official docs: https://docs.pmnd.rs/zustand
 *
 * Features:
 * - Persistent storage (localStorage)
 * - TypeScript support
 * - Devtools integration
 * - Minimal boilerplate
 */

interface Widget {
  id: string;
  type: string;
  title: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  visible: boolean;
}

interface DashboardState {
  // State
  sidebarOpen: boolean;
  activeView: 'grid' | 'list' | 'kanban';
  widgets: Widget[];
  selectedWidgetId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveView: (view: 'grid' | 'list' | 'kanban') => void;
  addWidget: (widget: Widget) => void;
  removeWidget: (id: string) => void;
  updateWidget: (id: string, updates: Partial<Widget>) => void;
  selectWidget: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  resetDashboard: () => void;
}

const initialState = {
  sidebarOpen: true,
  activeView: 'grid' as const,
  widgets: [],
  selectedWidgetId: null,
  isLoading: false,
  error: null,
};

/**
 * Dashboard store with persistent storage
 *
 * @example
 * ```tsx
 * function DashboardHeader() {
 *   const { sidebarOpen, toggleSidebar } = useDashboardStore();
 *
 *   return (
 *     <Button onClick={toggleSidebar}>
 *       {sidebarOpen ? 'Close' : 'Open'} Sidebar
 *     </Button>
 *   );
 * }
 * ```
 */
export const useDashboardStore = create<DashboardState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Sidebar actions
      toggleSidebar: () => set((state) => ({
        sidebarOpen: !state.sidebarOpen
      })),

      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // View actions
      setActiveView: (view) => set({ activeView: view }),

      // Widget actions
      addWidget: (widget) => set((state) => ({
        widgets: [...state.widgets, widget]
      })),

      removeWidget: (id) => set((state) => ({
        widgets: state.widgets.filter(w => w.id !== id),
        selectedWidgetId: state.selectedWidgetId === id ? null : state.selectedWidgetId
      })),

      updateWidget: (id, updates) => set((state) => ({
        widgets: state.widgets.map(w =>
          w.id === id ? { ...w, ...updates } : w
        )
      })),

      selectWidget: (id) => set({ selectedWidgetId: id }),

      // Loading and error actions
      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      // Reset to initial state
      resetDashboard: () => set(initialState),
    }),
    {
      name: 'dashboard-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      // Only persist specific fields
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        activeView: state.activeView,
        widgets: state.widgets,
      }),
    }
  )
);

// Selectors for computed values
export const selectVisibleWidgets = () =>
  useDashboardStore.getState().widgets.filter(w => w.visible);

export const selectWidgetById = (id: string) =>
  useDashboardStore.getState().widgets.find(w => w.id === id);

export const selectWidgetCount = () =>
  useDashboardStore.getState().widgets.length;

/**
 * Example usage in components:
 *
 * ```tsx
 * // Basic usage
 * function Sidebar() {
 *   const sidebarOpen = useDashboardStore((state) => state.sidebarOpen);
 *   const toggleSidebar = useDashboardStore((state) => state.toggleSidebar);
 *
 *   return (
 *     <div style={{ display: sidebarOpen ? 'block' : 'none' }}>
 *       <Button onClick={toggleSidebar}>Close</Button>
 *     </div>
 *   );
 * }
 *
 * // Using multiple values
 * function WidgetManager() {
 *   const { widgets, addWidget, removeWidget } = useDashboardStore();
 *
 *   return (
 *     <div>
 *       {widgets.map(widget => (
 *         <div key={widget.id}>
 *           {widget.title}
 *           <Button onClick={() => removeWidget(widget.id)}>Remove</Button>
 *         </div>
 *       ))}
 *       <Button onClick={() => addWidget({ ... })}>Add Widget</Button>
 *     </div>
 *   );
 * }
 *
 * // Using selectors for optimized re-renders
 * function WidgetList() {
 *   // Only re-renders when visible widgets change
 *   const widgets = useDashboardStore((state) =>
 *     state.widgets.filter(w => w.visible)
 *   );
 *
 *   return <div>{widgets.length} visible widgets</div>;
 * }
 * ```
 */
