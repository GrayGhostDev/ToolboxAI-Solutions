import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { ReactNode } from 'react';

interface PageTransitionProps {
  children: ReactNode;
  variant?: 'fade' | 'slide' | 'scale';
}

/**
 * PageTransition - Smooth transitions between route changes
 * Uses framer-motion for animations
 * 
 * @example
 * <PageTransition variant="fade">
 *   {children}
 * </PageTransition>
 */
export function PageTransition({ children, variant = 'fade' }: PageTransitionProps) {
  const location = useLocation();

  const variants = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 },
    },
    slide: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 },
    },
    scale: {
      initial: { opacity: 0, scale: 0.95 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.95 },
    },
  };

  const selectedVariant = variants[variant];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={selectedVariant.initial}
        animate={selectedVariant.animate}
        exit={selectedVariant.exit}
        transition={{
          duration: 0.3,
          ease: [0.4, 0, 0.2, 1], // cubic-bezier easing
        }}
        style={{
          width: '100%',
          minHeight: 'inherit',
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
