/**
 * useTerminalServices Hook
 * 
 * React hook to access Terminal 2 verification and monitoring services
 * Provides easy access to terminal verification, sync, and performance monitoring
 * 
 * @fileoverview React hook for terminal services integration
 * @version 1.0.0
 */

import { useEffect, useState, useCallback } from 'react';
import { terminalVerifier } from '../utils/terminal-verify';
import { terminalSync } from '../services/terminal-sync';
import { performanceMonitor } from '../utils/performance-monitor';
import type { VerificationResult, TerminalMessage } from '../utils/terminal-verify';
import type { PerformanceSummary } from '../utils/performance-monitor';

// ================================
// TYPE DEFINITIONS
// ================================

export interface TerminalServicesStatus {
  verification: {
    isMonitoring: boolean;
    lastResults: VerificationResult[];
    lastCheck: string | null;
  };
  sync: {
    isConnected: boolean;
    connectionStatuses: Record<string, string>;
    messageStats: {
      sent: number;
      received: number;
      queued: number;
    };
  };
  performance: {
    isMonitoring: boolean;
    score: number;
    alerts: number;
    summary: PerformanceSummary | null;
  };
}

export interface UseTerminalServicesReturn {
  // Status
  status: TerminalServicesStatus;
  
  // Actions
  runVerification: () => Promise<VerificationResult[]>;
  sendMessage: (terminalId: string, message: Omit<TerminalMessage, 'id' | 'from' | 'timestamp'>) => Promise<boolean>;
  getPerformanceSummary: () => PerformanceSummary;
  
  // Control
  startMonitoring: () => void;
  stopMonitoring: () => void;
  
  // Utilities
  isHealthy: boolean;
  refresh: () => void;
}

// ================================
// HOOK IMPLEMENTATION
// ================================

export function useTerminalServices(): UseTerminalServicesReturn {
  const [status, setStatus] = useState<TerminalServicesStatus>({
    verification: {
      isMonitoring: false,
      lastResults: [],
      lastCheck: null
    },
    sync: {
      isConnected: false,
      connectionStatuses: {},
      messageStats: {
        sent: 0,
        received: 0,
        queued: 0
      }
    },
    performance: {
      isMonitoring: false,
      score: 0,
      alerts: 0,
      summary: null
    }
  });

  // ================================
  // STATUS UPDATES
  // ================================

  const updateStatus = useCallback(() => {
    // Verification status
    const verificationStatus = {
      isMonitoring: terminalVerifier.isMonitoring(),
      lastResults: [], // Would need to be tracked separately
      lastCheck: null
    };

    // Sync status
    const syncStats = terminalSync.getStats();
    const syncStatus = {
      isConnected: terminalSync.isTerminalConnected('terminal1'),
      connectionStatuses: terminalSync.getConnectionStatuses(),
      messageStats: {
        sent: syncStats.messagesSent,
        received: syncStats.messagesReceived,
        queued: terminalSync.getQueuedMessageCount()
      }
    };

    // Performance status
    const performanceSummary = performanceMonitor.isRunning() 
      ? performanceMonitor.getPerformanceSummary()
      : null;

    const performanceStatus = {
      isMonitoring: performanceMonitor.isRunning(),
      score: performanceSummary?.score || 0,
      alerts: performanceSummary?.alerts.filter(a => a.severity === 'critical' || a.severity === 'error').length || 0,
      summary: performanceSummary
    };

    setStatus({
      verification: verificationStatus,
      sync: syncStatus,
      performance: performanceStatus
    });
  }, []);

  // ================================
  // EVENT HANDLERS
  // ================================

  useEffect(() => {
    // Initial status update
    updateStatus();

    // Set up event listeners for status updates
    const handleSyncStatusChange = () => updateStatus();
    const handlePerformanceAlert = () => updateStatus();
    
    terminalSync.on('connection_status_changed', handleSyncStatusChange);
    terminalSync.on('message', handleSyncStatusChange);
    terminalSync.on('performance_alert', handlePerformanceAlert);

    // Update status every 30 seconds
    const statusInterval = setInterval(updateStatus, 30000);

    // Cleanup
    return () => {
      clearInterval(statusInterval);
      terminalSync.off('connection_status_changed', handleSyncStatusChange);
      terminalSync.off('message', handleSyncStatusChange);
      terminalSync.off('performance_alert', handlePerformanceAlert);
    };
  }, [updateStatus]);

  // ================================
  // ACTION HANDLERS
  // ================================

  const runVerification = useCallback(async (): Promise<VerificationResult[]> => {
    try {
      const results = await terminalVerifier.runVerification();
      updateStatus(); // Update status after verification
      return results;
    } catch (error) {
      console.error('❌ Verification failed:', error);
      throw error;
    }
  }, [updateStatus]);

  const sendMessage = useCallback(async (
    terminalId: string, 
    message: Omit<TerminalMessage, 'id' | 'from' | 'timestamp'>
  ): Promise<boolean> => {
    try {
      const success = await terminalSync.sendToTerminal(terminalId, message);
      updateStatus(); // Update status after sending
      return success;
    } catch (error) {
      console.error('❌ Send message failed:', error);
      return false;
    }
  }, [updateStatus]);

  const getPerformanceSummary = useCallback((): PerformanceSummary => {
    return performanceMonitor.getPerformanceSummary();
  }, []);

  const startMonitoring = useCallback(() => {
    try {
      if (!terminalVerifier.isMonitoring()) {
        terminalVerifier.startMonitoring();
      }
      if (!performanceMonitor.isRunning()) {
        performanceMonitor.startMonitoring();
      }
      if (!terminalSync.isTerminalConnected('terminal1')) {
        terminalSync.initialize().catch(error => {
          console.error('❌ Terminal sync initialization failed:', error);
        });
      }
      updateStatus();
      console.log('✅ Terminal monitoring started from hook');
    } catch (error) {
      console.error('❌ Failed to start monitoring:', error);
    }
  }, [updateStatus]);

  const stopMonitoring = useCallback(() => {
    try {
      if (terminalVerifier.isMonitoring()) {
        terminalVerifier.stopMonitoring();
      }
      if (performanceMonitor.isRunning()) {
        performanceMonitor.stopMonitoring();
      }
      updateStatus();
      console.log('🛑 Terminal monitoring stopped from hook');
    } catch (error) {
      console.error('❌ Failed to stop monitoring:', error);
    }
  }, [updateStatus]);

  const refresh = useCallback(() => {
    updateStatus();
  }, [updateStatus]);

  // ================================
  // COMPUTED VALUES
  // ================================

  const isHealthy = status.sync.isConnected && 
                   status.verification.isMonitoring && 
                   status.performance.isMonitoring &&
                   status.performance.alerts === 0;

  // ================================
  // RETURN HOOK INTERFACE
  // ================================

  return {
    status,
    runVerification,
    sendMessage,
    getPerformanceSummary,
    startMonitoring,
    stopMonitoring,
    isHealthy,
    refresh
  };
}

// ================================
// ADDITIONAL UTILITY HOOKS
// ================================

/**
 * Hook to monitor specific terminal connection
 */
export function useTerminalConnection(terminalId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastSeen, setLastSeen] = useState<string | null>(null);

  useEffect(() => {
    const updateConnectionStatus = () => {
      const connected = terminalSync.isTerminalConnected(terminalId);
      setIsConnected(connected);
      
      const statuses = terminalSync.getConnectionStatuses();
      setLastSeen(statuses[terminalId] || null);
    };

    // Initial check
    updateConnectionStatus();

    // Listen for connection changes
    const handler = (data: { terminalId: string; status: string }) => {
      if (data.terminalId === terminalId) {
        updateConnectionStatus();
      }
    };

    terminalSync.on('connection_status_changed', handler);

    // Regular updates
    const interval = setInterval(updateConnectionStatus, 10000);

    return () => {
      terminalSync.off('connection_status_changed', handler);
      clearInterval(interval);
    };
  }, [terminalId]);

  return { isConnected, lastSeen };
}

/**
 * Hook to listen for specific message types
 */
export function useTerminalMessages(messageType: string) {
  const [messages, setMessages] = useState<any[]>([]);
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    const handler = (payload: any, message: TerminalMessage) => {
      setLastMessage({ payload, message, timestamp: Date.now() });
      setMessages(prev => [...prev.slice(-19), { payload, message, timestamp: Date.now() }]); // Keep last 20
    };

    terminalSync.on(`message:${messageType}`, handler);

    return () => {
      terminalSync.off(`message:${messageType}`, handler);
    };
  }, [messageType]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastMessage(null);
  }, []);

  return { messages, lastMessage, clearMessages, messageCount: messages.length };
}

/**
 * Hook for performance monitoring alerts
 */
export function usePerformanceAlerts() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [criticalCount, setCriticalCount] = useState(0);

  useEffect(() => {
    const updateAlerts = () => {
      if (performanceMonitor.isRunning()) {
        const recentAlerts = performanceMonitor.getRecentAlerts(30); // Last 30 minutes
        setAlerts(recentAlerts);
        setCriticalCount(recentAlerts.filter(a => a.severity === 'critical').length);
      }
    };

    // Initial update
    updateAlerts();

    // Listen for new alerts
    terminalSync.on('performance_alert', updateAlerts);

    // Regular updates
    const interval = setInterval(updateAlerts, 60000); // Every minute

    return () => {
      terminalSync.off('performance_alert', updateAlerts);
      clearInterval(interval);
    };
  }, []);

  const clearAlerts = useCallback(() => {
    performanceMonitor.clearAlerts();
    setAlerts([]);
    setCriticalCount(0);
  }, []);

  return { alerts, criticalCount, clearAlerts };
}

export default useTerminalServices;