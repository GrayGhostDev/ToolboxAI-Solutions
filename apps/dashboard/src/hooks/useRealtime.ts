/**
 * Real-time hooks for ToolboxAI Dashboard
 * Provides easy-to-use hooks for subscribing to Pusher channels and events
 */
import { useEffect, useState, useCallback } from 'react';
import { PusherService } from '../services/pusher';
import {
  WebSocketMessage,
  WebSocketState,
  WebSocketChannel,
  WebSocketEventHandler
} from '../types/websocket';
// Get singleton instance
const pusherService = PusherService.getInstance();
/**
 * Hook to monitor real-time connection status
 */
export const useRealtimeStatus = () => {
  const [connectionStatus, setConnectionStatus] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [isConnected, setIsConnected] = useState(false);
  useEffect(() => {
    // Subscribe to connection status updates
    const unsubscribe = pusherService.onConnectionStatusChange((status) => {
      setConnectionStatus(status);
      setIsConnected(status === WebSocketState.CONNECTED);
    });
    // Get initial status
    const initialStatus = pusherService.getConnectionState();
    setConnectionStatus(initialStatus);
    setIsConnected(initialStatus === WebSocketState.CONNECTED);
    return () => {
      unsubscribe();
    };
  }, []);
  return { connectionStatus, isConnected };
};
/**
 * Hook to subscribe to a specific channel
 */
export const useRealtimeChannel = (channelName: string, autoConnect = true) => {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  useEffect(() => {
    if (!channelName || !autoConnect) return;
    // Connect if not connected
    pusherService.connect().then(() => {
      // Subscribe to the channel
      pusherService.subscribe(channelName);
      setIsSubscribed(true);
    }).catch((error) => {
      console.error(`Failed to subscribe to channel ${channelName}:`, error);
      setIsSubscribed(false);
    });
    // Listen for messages on this channel
    const handleMessage = (message: WebSocketMessage) => {
      if (message.channel === channelName) {
        setLastMessage(message);
        setMessages(prev => [...prev, message]);
      }
    };
    pusherService.on('message', handleMessage);
    return () => {
      pusherService.off('message', handleMessage);
      pusherService.unsubscribe(channelName);
      setIsSubscribed(false);
    };
  }, [channelName, autoConnect]);
  const sendMessage = useCallback((event: string, data: any) => {
    if (!isSubscribed) {
      console.warn(`Not subscribed to channel ${channelName}`);
      return;
    }
    pusherService.send({
      channel: channelName,
      event,
      data,
      timestamp: Date.now(),
    });
  }, [channelName, isSubscribed]);
  const clearMessages = useCallback(() => {
    setMessages([]);
    setLastMessage(null);
  }, []);
  return {
    isSubscribed,
    lastMessage,
    messages,
    sendMessage,
    clearMessages,
  };
};
/**
 * Hook for listening to specific events
 */
export const useRealtimeEvent = (
  channelName: string,
  eventName: string,
  handler: WebSocketEventHandler,
  autoConnect = true
) => {
  const [isListening, setIsListening] = useState(false);
  useEffect(() => {
    if (!channelName || !eventName || !handler || !autoConnect) return;
    // Connect and subscribe
    pusherService.connect().then(() => {
      pusherService.subscribe(channelName);
      // Register event handler
      const wrappedHandler = (message: WebSocketMessage) => {
        if (message.channel === channelName && message.event === eventName) {
          handler(message);
        }
      };
      pusherService.on('message', wrappedHandler);
      setIsListening(true);
      return () => {
        pusherService.off('message', wrappedHandler);
        setIsListening(false);
      };
    }).catch((error) => {
      console.error(`Failed to listen to event ${eventName} on channel ${channelName}:`, error);
      setIsListening(false);
    });
  }, [channelName, eventName, handler, autoConnect]);
  return { isListening };
};
/**
 * Hook for presence channels (see who's online)
 */
export const useRealtimePresence = (channelName: string, userId?: string) => {
  const [members, setMembers] = useState<Map<string, any>>(new Map());
  const [myId, setMyId] = useState<string | undefined>(userId);
  useEffect(() => {
    if (!channelName || !channelName.startsWith('presence-')) return;
    // Connect and subscribe to presence channel
    pusherService.connect().then(() => {
      const channel = pusherService.getChannel(channelName);
      if (channel && 'members' in channel) {
        // It's a presence channel
        const presenceChannel = channel as any; // Type assertion for presence channel
        // Set initial members
        if (presenceChannel.members) {
          setMembers(new Map(Object.entries(presenceChannel.members.members)));
          setMyId(presenceChannel.members.myID);
        }
        // Listen for member events
        presenceChannel.bind('pusher:member_added', (member: any) => {
          setMembers(prev => new Map(prev).set(member.id, member.info));
        });
        presenceChannel.bind('pusher:member_removed', (member: any) => {
          setMembers(prev => {
            const newMembers = new Map(prev);
            newMembers.delete(member.id);
            return newMembers;
          });
        });
      }
    }).catch((error) => {
      console.error(`Failed to join presence channel ${channelName}:`, error);
    });
    return () => {
      // Cleanup will be handled by pusherService
    };
  }, [channelName, userId]);
  return {
    members: Array.from(members.values()),
    memberCount: members.size,
    myId,
    isPresent: (id: string) => members.has(id),
  };
};
/**
 * Hook for dashboard-specific real-time updates
 */
export const useDashboardUpdates = () => {
  const [updates, setUpdates] = useState<any[]>([]);
  const [lastUpdate, setLastUpdate] = useState<any>(null);
  useRealtimeEvent('dashboard-updates', 'update', (message) => {
    setLastUpdate(message.data);
    setUpdates(prev => [...prev, message.data]);
  });
  useRealtimeEvent('dashboard-updates', 'notification', (message) => {
    // Handle notifications
    console.log('Dashboard notification:', message.data);
  });
  const clearUpdates = useCallback(() => {
    setUpdates([]);
    setLastUpdate(null);
  }, []);
  return {
    updates,
    lastUpdate,
    clearUpdates,
  };
};
/**
 * Hook for content generation progress
 */
export const useContentGenerationProgress = (sessionId?: string) => {
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>('idle');
  const [result, setResult] = useState<any>(null);
  const channelName = sessionId ? `content-generation-${sessionId}` : 'content-generation';
  useRealtimeEvent(channelName, 'progress', (message) => {
    const { progress, status } = message.data;
    setProgress(progress || 0);
    setStatus(status || 'processing');
  });
  useRealtimeEvent(channelName, 'complete', (message) => {
    setProgress(100);
    setStatus('complete');
    setResult(message.data);
  });
  useRealtimeEvent(channelName, 'error', (message) => {
    setStatus('error');
    setResult(message.data);
  });
  const reset = useCallback(() => {
    setProgress(0);
    setStatus('idle');
    setResult(null);
  }, []);
  return {
    progress,
    status,
    result,
    reset,
  };
};
/**
 * Hook for agent status monitoring
 */
export const useAgentStatus = (agentId?: string) => {
  const [agentStatus, setAgentStatus] = useState<Record<string, any>>({});
  const [activeAgents, setActiveAgents] = useState<string[]>([]);
  const channelName = agentId ? `agent-status-${agentId}` : 'agent-status';
  useRealtimeEvent(channelName, 'status', (message) => {
    const { agentId, status } = message.data;
    setAgentStatus(prev => ({
      ...prev,
      [agentId]: status,
    }));
    if (status === 'active' && !activeAgents.includes(agentId)) {
      setActiveAgents(prev => [...prev, agentId]);
    } else if (status === 'inactive' && activeAgents.includes(agentId)) {
      setActiveAgents(prev => prev.filter(id => id !== agentId));
    }
  });
  return {
    agentStatus,
    activeAgents,
    isAgentActive: (id: string) => activeAgents.includes(id),
  };
};
/**
 * Hook for real-time collaboration features
 */
export const useCollaboration = (documentId: string, userId: string) => {
  const [cursors, setCursors] = useState<Map<string, { x: number; y: number; color: string }>>(new Map());
  const [selections, setSelections] = useState<Map<string, any>>(new Map());
  const channelName = `presence-document-${documentId}`;
  // Use presence channel for collaboration
  const { members, myId } = useRealtimePresence(channelName, userId);
  // Listen for cursor movements
  useRealtimeEvent(channelName, 'cursor-move', (message) => {
    const { userId, position, color } = message.data;
    if (userId !== myId) {
      setCursors(prev => new Map(prev).set(userId, { ...position, color }));
    }
  });
  // Listen for selection changes
  useRealtimeEvent(channelName, 'selection-change', (message) => {
    const { userId, selection } = message.data;
    if (userId !== myId) {
      setSelections(prev => new Map(prev).set(userId, selection));
    }
  });
  const sendCursorPosition = useCallback((x: number, y: number, color: string) => {
    pusherService.send({
      channel: channelName,
      event: 'cursor-move',
      data: {
        userId: myId,
        position: { x, y },
        color,
      },
      timestamp: Date.now(),
    });
  }, [channelName, myId]);
  const sendSelection = useCallback((selection: any) => {
    pusherService.send({
      channel: channelName,
      event: 'selection-change',
      data: {
        userId: myId,
        selection,
      },
      timestamp: Date.now(),
    });
  }, [channelName, myId]);
  return {
    collaborators: members,
    cursors: Array.from(cursors.entries()).map(([id, cursor]) => ({ id, ...cursor })),
    selections: Array.from(selections.entries()).map(([id, selection]) => ({ id, selection })),
    sendCursorPosition,
    sendSelection,
  };
};
// Export the service instance for direct access when needed
export { pusherService };