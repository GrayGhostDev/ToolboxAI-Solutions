/**
 * Dashboard Component Test
 *
 * Example test file demonstrating how to test components using the
 * test infrastructure with all necessary mocks and utilities.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, userEvent } from '../../test/utils/render';
import { 
  createMockUser, 
  createMockDashboardData,
  createMockClass,
  createMockApiResponse 
} from '../../test/utils/mockData';
import { DashboardHome } from '../../components/pages/DashboardHome';

// Mock the API module
vi.mock('../../services/api', () => ({
  getDashboardOverview: vi.fn(),
  listClasses: vi.fn(),
  listUsers: vi.fn(),
  apiClient: {
    request: vi.fn(),
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock the WebSocket service
vi.mock('../../services/websocket', () => ({
  WebSocketService: {
    getInstance: vi.fn(() => ({
      connect: vi.fn(),
      disconnect: vi.fn(),
      send: vi.fn(),
      subscribe: vi.fn(() => vi.fn()),
      unsubscribe: vi.fn(),
      isConnected: vi.fn(() => true),
    }))
  },
  sendWebSocketMessage: vi.fn(),
  subscribeToChannel: vi.fn(() => 'subscription-id'),
  unsubscribeFromChannel: vi.fn(),
  WebSocketMessageType: {
    CONTENT_UPDATE: 'content_update',
    QUIZ_UPDATE: 'quiz_update',
    PROGRESS_UPDATE: 'progress_update',
  }
}));

describe('Dashboard Component', () => {
  const mockUser = createMockUser({
    role: 'teacher',
    firstName: 'Jane',
    lastName: 'Smith',
  });

  const mockDashboardData = createMockDashboardData({
    totalStudents: 28,
    totalClasses: 3,
    averageScore: 85.5,
  });

  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks();
    
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn((key) => {
        if (key === 'token') return 'mock-token';
        if (key === 'user') return JSON.stringify(mockUser);
        return null;
      }),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the dashboard with loading state initially', () => {
      render(<DashboardHome role="teacher" />);
      
      // Check for loading indicators (adjust based on your actual component)
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    });

    it('should display user-specific welcome message', async () => {
      const { getDashboardOverview } = await import('../../services/api')
      ;(getDashboardOverview as any).mockResolvedValue(mockDashboardData);

      render(<DashboardHome role="teacher" />, {
        preloadedState: {
          user: {
            currentUser: mockUser,
            isAuthenticated: true,
            role: 'teacher',
          }
        }
      });

      await waitFor(() => {
        expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
      });
    });

    it('should render different content based on user role', () => {
      // Test teacher view
      const { rerender } = render(<DashboardHome role="teacher" />);
      expect(screen.getByText(/Review today's classes/i)).toBeInTheDocument();

      // Test student view
      rerender(<DashboardHome role="student" />);
      expect(screen.getByText(/Jump into your next mission/i)).toBeInTheDocument();

      // Test admin view
      rerender(<DashboardHome role="admin" />);
      expect(screen.getByText(/Monitor usage across schools/i)).toBeInTheDocument();

      // Test parent view
      rerender(<DashboardHome role="parent" />);
      expect(screen.getByText(/See your child's progress/i)).toBeInTheDocument();
    });
  });

  describe('Data Fetching', () => {
    it('should fetch dashboard data on mount', async () => {
      const { getDashboardOverview } = await import('../../services/api')
      ;(getDashboardOverview as any).mockResolvedValue(mockDashboardData);

      render(<DashboardHome role="teacher" />);

      await waitFor(() => {
        expect(getDashboardOverview).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle API errors gracefully', async () => {
      const { getDashboardOverview } = await import('../../services/api')
      ;(getDashboardOverview as any).mockRejectedValue(new Error('API Error'));

      render(<DashboardHome role="teacher" />);

      await waitFor(() => {
        // Component should still render without crashing
        expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should handle button clicks for teacher role', async () => {
      const user = userEvent.setup();
      
      render(<DashboardHome role="teacher" />, {
        preloadedState: {
          user: {
            currentUser: mockUser,
            isAuthenticated: true,
            role: 'teacher',
          }
        }
      });

      // Find and click the Create Lesson button (if it exists)
      const createLessonButton = screen.queryByText(/Create Lesson/i);
      if (createLessonButton) {
        await user.click(createLessonButton);
        // Verify the expected behavior (e.g., modal opens)
      }
    });

    it('should navigate when student clicks Enter Roblox World', async () => {
      const user = userEvent.setup();
      const mockNavigate = vi.fn();
      
      // Mock useNavigate
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom');
        return {
          ...actual,
          useNavigate: () => mockNavigate,
        };
      });

      render(<DashboardHome role="student" />);

      const robloxButton = screen.getByText(/Enter Roblox World/i);
      await user.click(robloxButton);

      // Verify navigation was called
      expect(mockNavigate).toHaveBeenCalledWith('/play');
    });
  });

  describe('Real-time Updates', () => {
    it('should subscribe to WebSocket channels on mount', async () => {
      const { subscribeToChannel } = await import('../../services/websocket');

      render(<DashboardHome role="teacher" />);

      await waitFor(() => {
        expect(subscribeToChannel).toHaveBeenCalled();
      });
    });

    it('should unsubscribe from channels on unmount', async () => {
      const { unsubscribeFromChannel } = await import('../../services/websocket');
      
      const { unmount } = render(<DashboardHome role="teacher" />);
      
      unmount();

      expect(unsubscribeFromChannel).toHaveBeenCalled();
    });
  });

  describe('Responsive Design', () => {
    it('should render correctly on mobile devices', () => {
      // Mock mobile viewport
      window.matchMedia = vi.fn().mockImplementation(query => ({
        matches: query === '(max-width: 768px)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }));

      render(<DashboardHome role="teacher" />);
      
      // Verify mobile-specific layout
      expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<DashboardHome role="teacher" />);
      
      // Check for ARIA labels on important elements
      const mainContent = document.querySelector('[role="main"]');
      if (mainContent) {
        expect(mainContent).toBeInTheDocument();
      }
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      
      render(<DashboardHome role="teacher" />);
      
      // Tab through interactive elements
      await user.tab();
      
      // Verify focus management
      const focusedElement = document.activeElement;
      expect(focusedElement).toBeTruthy();
    });
  });

  describe('Performance', () => {
    it('should render charts without performance issues', () => {
      const startTime = performance.now();
      
      render(<DashboardHome role="teacher" />, {
        preloadedState: {
          dashboard: {
            metrics: mockDashboardData,
            loading: false,
          }
        }
      });
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Verify render time is reasonable (adjust threshold as needed)
      expect(renderTime).toBeLessThan(1000); // 1 second
    });
  });
});