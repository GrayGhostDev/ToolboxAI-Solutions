import React, { useState, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver';
import { PerformanceSkeleton } from '../atomic/atoms/PerformanceSkeleton';

interface ProgressiveEnhancementProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
  delay?: number;
  priority?: 'high' | 'medium' | 'low';
  skeletonVariant?: 'dashboard' | 'card' | 'list' | 'chart' | 'navigation' | 'form';
  enableIntersectionObserver?: boolean;
}

// Hook for detecting network conditions
const useNetworkAware = () => {
  const [networkInfo, setNetworkInfo] = useState({
    effectiveType: '4g',
    saveData: false,
    downlink: 10
  });

  useEffect(() => {
    const updateNetworkInfo = () => {
      const connection = (navigator as any).connection;
      if (connection) {
        setNetworkInfo({
          effectiveType: connection.effectiveType || '4g',
          saveData: connection.saveData || false,
          downlink: connection.downlink || 10
        });
      }
    };

    updateNetworkInfo();

    const connection = (navigator as any).connection;
    if (connection) {
      connection.addEventListener('change', updateNetworkInfo);
      return () => connection.removeEventListener('change', updateNetworkInfo);
    }
  }, []);

  return networkInfo;
};

// Hook for CPU performance awareness
const useCPUAware = () => {
  const [cpuInfo, setCpuInfo] = useState({
    hardwareConcurrency: navigator.hardwareConcurrency || 4,
    deviceMemory: (navigator as any).deviceMemory || 4
  });

  const isLowEndDevice = cpuInfo.hardwareConcurrency <= 2 || cpuInfo.deviceMemory <= 2;

  return { ...cpuInfo, isLowEndDevice };
};

export const ProgressiveEnhancement: React.FC<ProgressiveEnhancementProps> = ({
  children,
  fallback,
  threshold = 0.1,
  rootMargin = '50px',
  delay = 0,
  priority = 'medium',
  skeletonVariant = 'card',
  enableIntersectionObserver = true
}) => {
  const [shouldRender, setShouldRender] = useState(priority === 'high');
  const [isVisible, setIsVisible] = useState(false);
  const networkInfo = useNetworkAware();
  const { isLowEndDevice } = useCPUAware();

  // Intersection observer for lazy loading
  const { ref, isIntersecting } = useIntersectionObserver({
    threshold,
    rootMargin,
    enabled: enableIntersectionObserver && !shouldRender
  });

  // Calculate adaptive delay based on device and network conditions
  const calculateAdaptiveDelay = useCallback(() => {
    let adaptiveDelay = delay;

    // Increase delay for slow networks
    if (networkInfo.effectiveType === 'slow-2g' || networkInfo.effectiveType === '2g') {
      adaptiveDelay += 1000;
    } else if (networkInfo.effectiveType === '3g') {
      adaptiveDelay += 500;
    }

    // Increase delay for low-end devices
    if (isLowEndDevice) {
      adaptiveDelay += 300;
    }

    // Respect data saver mode
    if (networkInfo.saveData) {
      adaptiveDelay += 500;
    }

    return adaptiveDelay;
  }, [delay, networkInfo, isLowEndDevice]);

  // Handle visibility and rendering logic
  useEffect(() => {
    if (priority === 'high') {
      setShouldRender(true);
      setIsVisible(true);
      return;
    }

    if (isIntersecting && !shouldRender) {
      const adaptiveDelay = calculateAdaptiveDelay();

      const timer = setTimeout(() => {
        setShouldRender(true);
        setIsVisible(true);
      }, adaptiveDelay);

      return () => clearTimeout(timer);
    }
  }, [isIntersecting, shouldRender, priority, calculateAdaptiveDelay]);

  // Don't render heavy components on data saver mode unless high priority
  if (networkInfo.saveData && priority !== 'high') {
    return (
      <Box ref={ref}>
        {fallback || <PerformanceSkeleton variant={skeletonVariant} animate={false} />}
      </Box>
    );
  }

  // Progressive rendering based on intersection and conditions
  if (!shouldRender) {
    return (
      <Box ref={ref} sx={{ minHeight: 200 }}>
        {fallback || <PerformanceSkeleton variant={skeletonVariant} />}
      </Box>
    );
  }

  return (
    <Box ref={ref}>
      {isVisible ? children : (fallback || <PerformanceSkeleton variant={skeletonVariant} />)}
    </Box>
  );
};

export default ProgressiveEnhancement;