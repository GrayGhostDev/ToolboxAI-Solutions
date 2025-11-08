/**
 * Role-Based Analytics Service
 * 
 * Tracks feature usage, dashboard engagement, and user behavior
 * segmented by user role for insights and optimization.
 */

import type { UserRole } from '../types';

interface AnalyticsEvent {
  event: string;
  role: UserRole;
  userId: string;
  timestamp: string;
  properties?: Record<string, any>;
}

interface RoleMetrics {
  role: UserRole;
  activeUsers: number;
  sessionDuration: number;
  featuresUsed: string[];
  engagementScore: number;
}

class RoleBasedAnalytics {
  private events: AnalyticsEvent[] = [];
  private sessionStart: number = Date.now();

  /**
   * Track a feature usage event
   */
  trackFeatureUsage(
    feature: string,
    role: UserRole,
    userId: string,
    properties?: Record<string, any>
  ): void {
    const event: AnalyticsEvent = {
      event: 'feature_used',
      role,
      userId,
      timestamp: new Date().toISOString(),
      properties: {
        feature,
        ...properties,
      },
    };

    this.events.push(event);
    this.sendToAnalytics(event);

    // Log to console in development
    if (import.meta.env.DEV) {
      console.log('[Analytics]', feature, { role, userId, properties });
    }
  }

  /**
   * Track dashboard page view
   */
  trackPageView(
    page: string,
    role: UserRole,
    userId: string
  ): void {
    const event: AnalyticsEvent = {
      event: 'page_view',
      role,
      userId,
      timestamp: new Date().toISOString(),
      properties: {
        page,
        referrer: document.referrer,
      },
    };

    this.events.push(event);
    this.sendToAnalytics(event);
  }

  /**
   * Track user session
   */
  trackSession(role: UserRole, userId: string): void {
    const duration = Date.now() - this.sessionStart;

    const event: AnalyticsEvent = {
      event: 'session_end',
      role,
      userId,
      timestamp: new Date().toISOString(),
      properties: {
        duration,
        durationMinutes: Math.round(duration / 60000),
      },
    };

    this.events.push(event);
    this.sendToAnalytics(event);
  }

  /**
   * Track role-specific action
   */
  trackRoleAction(
    action: string,
    role: UserRole,
    userId: string,
    properties?: Record<string, any>
  ): void {
    const event: AnalyticsEvent = {
      event: `${role}_action`,
      role,
      userId,
      timestamp: new Date().toISOString(),
      properties: {
        action,
        ...properties,
      },
    };

    this.events.push(event);
    this.sendToAnalytics(event);
  }

  /**
   * Get role distribution metrics
   */
  async getRoleDistribution(): Promise<Record<UserRole, number>> {
    try {
      const response = await fetch('/api/analytics/role-distribution');
      const data = await response.json();
      return data.distribution;
    } catch (error) {
      console.error('Error fetching role distribution:', error);
      return {
        admin: 0,
        teacher: 0,
        student: 0,
        parent: 0,
      };
    }
  }

  /**
   * Get engagement metrics by role
   */
  async getRoleEngagement(role: UserRole): Promise<RoleMetrics> {
    try {
      const response = await fetch(`/api/analytics/role-engagement/${role}`);
      const data = await response.json();
      return data.metrics;
    } catch (error) {
      console.error('Error fetching role engagement:', error);
      return {
        role,
        activeUsers: 0,
        sessionDuration: 0,
        featuresUsed: [],
        engagementScore: 0,
      };
    }
  }

  /**
   * Get feature usage by role
   */
  async getFeatureUsageByRole(role: UserRole): Promise<Record<string, number>> {
    try {
      const response = await fetch(`/api/analytics/feature-usage/${role}`);
      const data = await response.json();
      return data.usage;
    } catch (error) {
      console.error('Error fetching feature usage:', error);
      return {};
    }
  }

  /**
   * Get dashboard engagement score
   */
  async getDashboardEngagement(role: UserRole, period: 'day' | 'week' | 'month'): Promise<number> {
    try {
      const response = await fetch(
        `/api/analytics/dashboard-engagement/${role}?period=${period}`
      );
      const data = await response.json();
      return data.score;
    } catch (error) {
      console.error('Error fetching dashboard engagement:', error);
      return 0;
    }
  }

  /**
   * Track role-based performance metrics
   */
  trackPerformance(
    metric: string,
    value: number,
    role: UserRole,
    userId: string
  ): void {
    const event: AnalyticsEvent = {
      event: 'performance_metric',
      role,
      userId,
      timestamp: new Date().toISOString(),
      properties: {
        metric,
        value,
      },
    };

    this.events.push(event);
    this.sendToAnalytics(event);
  }

  /**
   * Send analytics event to backend
   */
  private async sendToAnalytics(event: AnalyticsEvent): Promise<void> {
    try {
      // Send to backend analytics service
      await fetch('/api/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('clerkToken')}`,
        },
        body: JSON.stringify(event),
      });

      // Also send to external analytics if configured
      if (window.gtag) {
        window.gtag('event', event.event, {
          event_category: event.role,
          ...event.properties,
        });
      }

      // Sentry breadcrumb
      if (window.Sentry) {
        window.Sentry.addBreadcrumb({
          category: 'analytics',
          message: event.event,
          level: 'info',
          data: event.properties,
        });
      }
    } catch (error) {
      // Silently fail - don't interrupt user experience
      if (import.meta.env.DEV) {
        console.error('Analytics error:', error);
      }
    }
  }

  /**
   * Get all tracked events (for debugging)
   */
  getEvents(): AnalyticsEvent[] {
    return [...this.events];
  }

  /**
   * Clear tracked events
   */
  clearEvents(): void {
    this.events = [];
  }
}

// Singleton instance
export const roleAnalytics = new RoleBasedAnalytics();

// React hook for easy usage
export function useRoleAnalytics() {
  return {
    trackFeature: roleAnalytics.trackFeatureUsage.bind(roleAnalytics),
    trackPage: roleAnalytics.trackPageView.bind(roleAnalytics),
    trackSession: roleAnalytics.trackSession.bind(roleAnalytics),
    trackAction: roleAnalytics.trackRoleAction.bind(roleAnalytics),
    trackPerformance: roleAnalytics.trackPerformance.bind(roleAnalytics),
    getRoleDistribution: roleAnalytics.getRoleDistribution.bind(roleAnalytics),
    getRoleEngagement: roleAnalytics.getRoleEngagement.bind(roleAnalytics),
    getFeatureUsage: roleAnalytics.getFeatureUsageByRole.bind(roleAnalytics),
    getDashboardEngagement: roleAnalytics.getDashboardEngagement.bind(roleAnalytics),
  };
}

// Type definitions for window globals
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
    Sentry?: {
      addBreadcrumb: (breadcrumb: any) => void;
    };
  }
}

