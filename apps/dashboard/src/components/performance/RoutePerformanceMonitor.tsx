import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { Box, Text, Badge, Group, Collapse, ActionIcon } from '@mantine/core';
import { IconChevronDown, IconChevronUp } from '@tabler/icons-react';

interface PerformanceMetric {
  route: string;
  loadTime: number;
  navigationType: string;
  timestamp: number;
  components: string[];
  wasTimeout: boolean;
}

interface RoutePerformanceMonitorProps {
  enabled?: boolean;
  maxEntries?: number;
  timeoutThreshold?: number;
}

export const RoutePerformanceMonitor: React.FC<RoutePerformanceMonitorProps> = ({
  enabled = process.env.NODE_ENV === 'development',
  maxEntries = 20,
  timeoutThreshold = 2000
}) => {
  const location = useLocation();
  const navigationType = useNavigationType();
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const loadStartTime = useRef<number>(Date.now());
  const currentRoute = useRef<string>('');

  useEffect(() => {
    if (!enabled) return;

    // Track navigation start
    loadStartTime.current = Date.now();
    currentRoute.current = location.pathname;

    // Set up performance observer for component loading
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const componentNames = entries
        .filter(entry => entry.name.includes('react') || entry.name.includes('component'))
        .map(entry => entry.name);

      // Calculate load time
      const loadTime = Date.now() - loadStartTime.current;
      const wasTimeout = loadTime > timeoutThreshold;

      const newMetric: PerformanceMetric = {
        route: currentRoute.current,
        loadTime,
        navigationType: navigationType || 'unknown',
        timestamp: Date.now(),
        components: componentNames,
        wasTimeout
      };

      setMetrics(prev => {
        const updated = [newMetric, ...prev].slice(0, maxEntries);

        // Log performance warnings
        if (wasTimeout) {
          console.warn(`Route ${currentRoute.current} took ${loadTime}ms to load (timeout threshold: ${timeoutThreshold}ms)`);
        }

        return updated;
      });
    });

    // Observe resource timing
    observer.observe({ entryTypes: ['resource', 'navigation', 'measure'] });

    // Cleanup after component likely loaded
    const cleanup = setTimeout(() => {
      observer.disconnect();
    }, 5000);

    return () => {
      observer.disconnect();
      clearTimeout(cleanup);
    };
  }, [location.pathname, navigationType, enabled, maxEntries, timeoutThreshold]);

  if (!enabled || metrics.length === 0) {
    return null;
  }

  const averageLoadTime = metrics.reduce((sum, metric) => sum + metric.loadTime, 0) / metrics.length;
  const timeoutCount = metrics.filter(m => m.wasTimeout).length;
  const slowestRoute = metrics.reduce((max, metric) =>
    metric.loadTime > max.loadTime ? metric : max, metrics[0]);

  return (
    <Box
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 9999,
        background: 'rgba(0, 0, 0, 0.9)',
        color: 'white',
        borderRadius: 8,
        padding: 12,
        minWidth: 280,
        maxWidth: 400,
        fontSize: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
      }}
    >
      <Group justify="space-between" align="center" mb="xs">
        <Text size="sm" fw={600}>Route Performance</Text>
        <ActionIcon
          variant="transparent"
          size="sm"
          c="white"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
        </ActionIcon>
      </Group>

      <Group gap="xs" mb="sm">
        <Badge color="blue" size="xs">
          Avg: {Math.round(averageLoadTime)}ms
        </Badge>
        <Badge color={timeoutCount > 0 ? 'red' : 'green'} size="xs">
          Timeouts: {timeoutCount}
        </Badge>
        <Badge color="violet" size="xs">
          Routes: {metrics.length}
        </Badge>
      </Group>

      <Collapse in={isExpanded}>
        <Box>
          {slowestRoute && (
            <Box mb="sm" p="xs" style={{ background: 'rgba(255,255,255,0.1)', borderRadius: 4 }}>
              <Text size="xs" fw={600} mb="xs">Slowest Route:</Text>
              <Text size="xs">{slowestRoute.route}</Text>
              <Text size="xs" c={slowestRoute.wasTimeout ? 'red' : 'yellow'}>
                {slowestRoute.loadTime}ms
              </Text>
            </Box>
          )}

          <Text size="xs" fw={600} mb="xs">Recent Routes:</Text>
          <Box style={{ maxHeight: 200, overflowY: 'auto' }}>
            {metrics.slice(0, 8).map((metric, index) => (
              <Group key={index} justify="space-between" mb="xs" p="xs"
                     style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 4 }}>
                <Box style={{ flex: 1, minWidth: 0 }}>
                  <Text size="xs" truncate>{metric.route}</Text>
                  <Text size="xs" c="dimmed">{metric.navigationType}</Text>
                </Box>
                <Badge
                  color={metric.wasTimeout ? 'red' : metric.loadTime > 1000 ? 'yellow' : 'green'}
                  size="xs"
                >
                  {metric.loadTime}ms
                </Badge>
              </Group>
            ))}
          </Box>

          {timeoutCount > 0 && (
            <Text size="xs" c="red" mt="sm" style={{ fontStyle: 'italic' }}>
              ⚠️ Some routes are exceeding timeout threshold. Consider optimizing lazy loading.
            </Text>
          )}
        </Box>
      </Collapse>
    </Box>
  );
};

export default RoutePerformanceMonitor;