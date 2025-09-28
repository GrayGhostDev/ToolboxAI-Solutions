/**
 * Core Pusher hook
 * Provides direct access to Pusher context and operations
 */

import { useContext } from 'react';
import { PusherContext } from '../../contexts/PusherContext';

export function usePusher() {
  const context = useContext(PusherContext);

  if (!context) {
    throw new Error('usePusher must be used within a PusherProvider');
  }

  return context;
}

// Keep backward compatibility
export const useWebSocket = usePusher;