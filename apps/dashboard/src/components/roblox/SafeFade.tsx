import React, { useState, useEffect } from 'react';
import Fade from '@mui/material/Fade';
import FadeProps from '@mui/material/FadeProps';

interface SafeFadeProps extends Omit<FadeProps, 'in'> {
  in?: boolean;
  timeout?: number;
  appear?: boolean;
  children: React.ReactElement;
}

export const SafeFade: React.FunctionComponent<SafeFadeProps> = ({ 
  in: inProp = true, 
  timeout = 300, 
  appear = false,
  children,
  ...props 
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
      <Fade
        in={isVisible}
        timeout={timeout}
        appear={appear}
        {...props}
      >
        {children}
      </Fade>
    );
  } catch (error) {
    console.warn('SafeFade error:', error);
    // Fallback to showing content without animation
    return inProp ? children : null;
  }
};
