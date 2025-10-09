import React, { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

interface RoutePreloaderProps {
  enabled?: boolean;
  aggressivePreload?: boolean;
}

interface PreloadMap {
  [key: string]: {
    import: () => Promise<any>;
    priority: 'high' | 'medium' | 'low';
    preloaded: boolean;
  };
}

// Route-based preloading map for intelligent prefetching
const PRELOAD_MAP: PreloadMap = {
  // From dashboard, likely next routes by role
  '/': {
    import: () => import('../pages/DashboardHome'),
    priority: 'high',
    preloaded: false
  },
  '/lessons': {
    import: () => import('../pages/Lessons'),
    priority: 'high',
    preloaded: false
  },
  '/classes': {
    import: () => import('../pages/Classes'),
    priority: 'high',
    preloaded: false
  },
  '/assessments': {
    import: () => import('../pages/Assessments'),
    priority: 'high',
    preloaded: false
  },
  '/play': {
    import: () => import('../pages/student/Play'),
    priority: 'high',
    preloaded: false
  },
  '/rewards': {
    import: () => import('../pages/Rewards'),
    priority: 'high',
    preloaded: false
  },
  '/reports': {
    import: () => import('../pages/Reports'),
    priority: 'medium',
    preloaded: false
  },
  '/settings': {
    import: () => import('../pages/Settings'),
    priority: 'medium',
    preloaded: false
  },
  '/analytics': {
    import: () => import('../pages/admin/Analytics'),
    priority: 'medium',
    preloaded: false
  },
  '/users': {
    import: () => import('../pages/admin/Users'),
    priority: 'medium',
    preloaded: false
  },
  // Heavy 3D components - load only on demand
  '/roblox': {
    import: () => import('../pages/TeacherRobloxDashboard'),
    priority: 'low',
    preloaded: false
  },
  '/roblox-studio': {
    import: () => import('../pages/RobloxStudioPage'),
    priority: 'low',
    preloaded: false
  }
};

// Common navigation patterns for predictive loading
const NAVIGATION_PATTERNS = {
  '/': ['/lessons', '/classes', '/play', '/settings'],
  '/lessons': ['/assessments', '/classes', '/reports'],
  '/classes': ['/lessons', '/assessments', '/reports'],
  '/assessments': ['/lessons', '/classes', '/reports'],
  '/play': ['/rewards', '/progress', '/missions'],
  '/rewards': ['/play', '/progress', '/leaderboard'],
  '/reports': ['/analytics', '/classes', '/lessons'],
  '/settings': [], // Settings is usually destination, not pathway
  '/analytics': ['/users', '/reports', '/observability'],
  '/users': ['/analytics', '/schools']
};

export const RoutePreloader: React.FC<RoutePreloaderProps> = ({
  enabled = process.env.NODE_ENV === 'development',
  aggressivePreload = false
}) => {
  const location = useLocation();
  const [preloadQueue, setPreloadQueue] = useState<string[]>([]);
  const [isPreloading, setIsPreloading] = useState(false);
  const [stats, setStats] = useState({
    preloaded: 0,
    failed: 0,
    totalTime: 0
  });

  // Preload a single route with error handling
  const preloadRoute = useCallback(async (route: string) => {
    const routeConfig = PRELOAD_MAP[route];
    if (!routeConfig || routeConfig.preloaded) return;

    const startTime = Date.now();
    try {
      await routeConfig.import();
      routeConfig.preloaded = true;

      const loadTime = Date.now() - startTime;
      setStats(prev => ({
        preloaded: prev.preloaded + 1,
        failed: prev.failed,
        totalTime: prev.totalTime + loadTime
      }));

      console.debug(`Preloaded ${route} in ${loadTime}ms`);
    } catch (error) {
      console.warn(`Failed to preload ${route}:`, error);
      setStats(prev => ({
        ...prev,
        failed: prev.failed + 1
      }));
    }
  }, []);

  // Process preload queue with throttling
  const processPreloadQueue = useCallback(async () => {
    if (isPreloading || preloadQueue.length === 0) return;

    setIsPreloading(true);
    const route = preloadQueue[0];
    setPreloadQueue(prev => prev.slice(1));

    await preloadRoute(route);

    // Small delay to prevent blocking main thread
    setTimeout(() => setIsPreloading(false), 100);
  }, [preloadQueue, isPreloading, preloadRoute]);

  // Add route to preload queue with priority
  const enqueuePreload = useCallback((route: string, priority: 'high' | 'medium' | 'low' = 'medium') => {
    if (!enabled || !PRELOAD_MAP[route] || PRELOAD_MAP[route].preloaded) return;

    setPreloadQueue(prev => {
      if (prev.includes(route)) return prev;

      const newQueue = [...prev];
      if (priority === 'high') {
        newQueue.unshift(route);
      } else {
        newQueue.push(route);
      }
      return newQueue;
    });
  }, [enabled]);

  // Preload based on current route and navigation patterns
  useEffect(() => {
    if (!enabled) return;

    const currentPath = location.pathname;
    const likelyNextRoutes = NAVIGATION_PATTERNS[currentPath] || [];

    // Preload likely next routes based on current location
    likelyNextRoutes.forEach(route => {
      const routeConfig = PRELOAD_MAP[route];
      if (routeConfig) {
        enqueuePreload(route, routeConfig.priority);
      }
    });

    // If aggressive preload is enabled, preload all high priority routes
    if (aggressivePreload) {
      Object.entries(PRELOAD_MAP).forEach(([route, config]) => {
        if (config.priority === 'high') {
          enqueuePreload(route, 'high');
        }
      });
    }
  }, [location.pathname, enabled, aggressivePreload, enqueuePreload]);

  // Process queue when it changes
  useEffect(() => {
    if (preloadQueue.length > 0 && !isPreloading) {
      const timer = setTimeout(processPreloadQueue, 50);
      return () => clearTimeout(timer);
    }
  }, [preloadQueue, processPreloadQueue, isPreloading]);

  // Hover preloading for links
  useEffect(() => {
    if (!enabled) return;

    const handleLinkHover = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const link = target.closest('a');

      if (link && link.href) {
        const url = new URL(link.href);
        const route = url.pathname;

        if (PRELOAD_MAP[route]) {
          enqueuePreload(route, 'medium');
        }
      }
    };

    // Add hover listeners to all links
    document.addEventListener('mouseover', handleLinkHover);
    return () => document.removeEventListener('mouseover', handleLinkHover);
  }, [enabled, enqueuePreload]);

  // Intersection observer for visible links
  useEffect(() => {
    if (!enabled || !window.IntersectionObserver) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const target = entry.target as HTMLElement;
            const link = target.closest('a');

            if (link && link.href) {
              const url = new URL(link.href);
              const route = url.pathname;

              if (PRELOAD_MAP[route]) {
                // Lower priority for intersection-based preloading
                enqueuePreload(route, 'low');
              }
            }
          }
        });
      },
      { threshold: 0.1 }
    );

    // Observe all navigation links
    const links = document.querySelectorAll('nav a, [data-preload="true"]');
    links.forEach(link => observer.observe(link));

    return () => observer.disconnect();
  }, [enabled, enqueuePreload]);

  // Development stats display
  if (enabled && process.env.NODE_ENV === 'development') {
    return (
      <div
        style={{
          position: 'fixed',
          bottom: 80,
          right: 20,
          background: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '6px',
          fontSize: '11px',
          zIndex: 10000,
          fontFamily: 'monospace'
        }}
      >
        <div>Preloaded: {stats.preloaded}</div>
        <div>Failed: {stats.failed}</div>
        <div>Avg: {stats.preloaded > 0 ? Math.round(stats.totalTime / stats.preloaded) : 0}ms</div>
        <div>Queue: {preloadQueue.length}</div>
        {isPreloading && <div style={{ color: '#00ff00' }}>Loading...</div>}
      </div>
    );
  }

  return null;
};

export default RoutePreloader;