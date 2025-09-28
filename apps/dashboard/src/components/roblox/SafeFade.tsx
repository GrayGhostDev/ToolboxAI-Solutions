import React, { useState, useEffect } from 'react';
import { Transition } from '@mantine/core';

interface SafeFadeProps {
  in?: boolean;
  duration?: number;
  appear?: boolean;
  children: React.ReactElement;
}

export const SafeFade: React.FunctionComponent<SafeFadeProps> = ({
  in: inProp = true,
  duration = 300,
  appear = false,
  children
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    // Ensure component is mounted before showing
    setIsMounted(true);
    const timer = setTimeout(() => {
      setIsVisible(inProp);
    }, 50); // Small delay to ensure DOM is ready

    return () => clearTimeout(timer);
  }, [inProp]);

  if (!isMounted) {
    return null;
  }

  try {
    return (
      <Transition
        mounted={isVisible}
        transition="fade"
        duration={duration}
        timingFunction="ease"
      >
        {(styles) => (
          <div style={styles}>
            {children}
          </div>
        )}
      </Transition>
    );
  } catch (error) {
    console.warn('SafeFade error:', error);
    // Fallback to showing content without animation
    return inProp ? children : null;
  }
};
