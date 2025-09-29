import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { pusherService } from '../services/pusher';

interface Message {
  id: string;
  position: 'left' | 'right';
  type: 'text' | 'file' | 'system';
  text: string;
  date: Date;
  avatar?: string;
  status?: 'waiting' | 'sent' | 'received' | 'read';
}

interface RobloxSpec {
  environment_name?: string;
  theme?: string;
  map_type?: string;
  difficulty?: string;
  npc_count?: number;
  learning_objectives?: string[];
  terrain?: string;
}

interface UseRobloxChatOptions {
  conversationId?: string;
  onMessage?: (message: Message) => void;
  onError?: (error: string) => void;
}

export const useRobloxChat = (options: UseRobloxChatOptions = {}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(options.conversationId || null);

  const subscriptionRef = useRef<string | null>(null);

  // Extract Roblox specifications from text
  const extractRobloxSpec = useCallback((text: string): { spec: RobloxSpec; missingFields: string[] } => {
    const spec: RobloxSpec = {};
    const lower = text.toLowerCase();

    // Extract environment name
    const nameMatch = text.match(/(?:call it|named|name(?:d)?(?: as)?|title(?:d)?)\s+([\w\s'-]{3,40})/i);
    if (nameMatch) spec.environment_name = nameMatch[1].trim();

    // Extract map type
    if (lower.includes('obby')) spec.map_type = 'obby';
    else if (lower.includes('open world')) spec.map_type = 'open_world';
    else if (lower.includes('dungeon')) spec.map_type = 'dungeon';
    else if (lower.includes('lab')) spec.map_type = 'lab';
    else if (lower.includes('classroom')) spec.map_type = 'classroom';
    else if (lower.includes('puzzle')) spec.map_type = 'puzzle';

    // Extract theme
    const themeMatch = text.match(/(?:theme|style)\s*:\s*([^\n.]+)/i);
    if (themeMatch) spec.theme = themeMatch[1].trim();

    // Extract terrain
    const terrainMatch = text.match(/(?:terrain|biome)\s*:\s*([^\n.]+)/i);
    if (terrainMatch) spec.terrain = terrainMatch[1].trim();

    // Extract NPC count
    const npcMatch = text.match(/(?:npc|enemies|characters)\s*:?\s*(\d{1,3})/i);
    if (npcMatch) spec.npc_count = parseInt(npcMatch[1], 10);

    // Extract difficulty
    const diffMatch = text.match(/\b(easy|medium|hard)\b/i);
    if (diffMatch) spec.difficulty = diffMatch[1].toLowerCase();

    // Extract learning objectives
    const objectivesMatch = text.match(/(?:objective|learning objective|goal)s?\s*:?\s*([^\n]+)/i);
    if (objectivesMatch) {
      spec.learning_objectives = objectivesMatch[1]
        .split(/,|;|\band\b/i)
        .map(s => s.trim())
        .filter(Boolean);
    }

    // Determine missing required fields
    const required = ['environment_name', 'theme', 'map_type', 'learning_objectives'];
    const missing = required.filter(k =>
      !spec[k as keyof RobloxSpec] ||
      (Array.isArray(spec[k as keyof RobloxSpec]) && (spec[k as keyof RobloxSpec] as any[]).length === 0)
    );

    return { spec, missingFields: missing };
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'stream_start':
      case 'agent_chat_start': {
        setIsStreaming(true);
        const streamMessage: Message = {
          id: 'streaming',
          position: 'left',
          type: 'text',
          text: '...',
          date: new Date(),
          avatar: '/ai-avatar.png',
          status: 'waiting'
        };
        setMessages(prev => [...prev, streamMessage]);
        break;
      }

      case 'stream_token':
      case 'agent_chat_token': {
        setMessages(prev => {
          const msgs = [...prev];
          const streamIdx = msgs.findIndex(m => m.id === 'streaming');
          if (streamIdx !== -1) {
            const currentText = msgs[streamIdx].text === '...' ? '' : msgs[streamIdx].text;
            msgs[streamIdx].text = currentText + (data.content || data.token || '');
          }
          return msgs;
        });
        break;
      }

      case 'stream_end':
      case 'agent_chat_complete': {
        setIsStreaming(false);
        setMessages(prev => {
          const msgs = [...prev];
          const streamIdx = msgs.findIndex(m => m.id === 'streaming');
          if (streamIdx !== -1) {
            msgs[streamIdx].id = `msg_${Date.now()}`;
            msgs[streamIdx].status = 'received';
          }
          return msgs;
        });
        break;
      }

      case 'ai_message':
      case 'agent_followup': {
        const content = data.message?.content || data.question ||
          (Array.isArray(data.questions) ? data.questions.join('\n') : '');
        if (content) {
          const aiMessage: Message = {
            id: data.message?.id || `msg_${Date.now()}`,
            position: 'left',
            type: 'text',
            text: content,
            date: new Date(data.message?.timestamp || Date.now()),
            avatar: '/ai-avatar.png',
            status: 'received'
          };
          setMessages(prev => [...prev, aiMessage]);
          options.onMessage?.(aiMessage);
        }
        break;
      }

      case 'error': {
        const errorMsg = data.message || 'An error occurred';
        setError(errorMsg);
        options.onError?.(errorMsg);
        setIsStreaming(false);
        setIsLoading(false);
        break;
      }
    }
  }, [options]);

  // Setup WebSocket connection
  useEffect(() => {
    if (!conversationId) return;

    const connect = async () => {
      try {
        subscriptionRef.current = pusherService.subscribe(
          `ai-chat-${conversationId}`,
          handleWebSocketMessage
        );
        setError(null);
      } catch (err) {
        console.error('WebSocket connection error:', err);
        setError('Real-time connection error. Falling back to HTTP API.');
      }
    };

    connect();

    return () => {
      if (subscriptionRef.current) {
        try {
          pusherService.unsubscribe(subscriptionRef.current);
        } catch (e) {
          console.warn('Error unsubscribing from WebSocket:', e);
        }
      }
    };
  }, [conversationId, handleWebSocketMessage]);

  // Send message
  const sendMessage = useCallback(async (text: string, userId?: string) => {
    if (!text.trim() || isLoading) return;

    // Create conversation if needed
    let currentConversationId = conversationId;
    if (!currentConversationId) {
      currentConversationId = `conv_${Date.now()}`;
      setConversationId(currentConversationId);
    }

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      position: 'right',
      type: 'text',
      text: text.trim(),
      date: new Date(),
      avatar: '/default-avatar.png',
      status: 'sent'
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const { spec, missingFields } = extractRobloxSpec(text);

      const response = await api.post('/roblox/chat', {
        message: text,
        conversation_id: currentConversationId,
        user_id: userId,
        roblox_spec: spec,
        missing_fields: missingFields
      });

      if (response.data?.message) {
        const aiMessage: Message = {
          id: response.data.message.id || `msg_${Date.now()}`,
          position: 'left',
          type: 'text',
          text: response.data.message.content,
          date: new Date(),
          avatar: '/ai-avatar.png',
          status: 'received'
        };
        setMessages(prev => [...prev, aiMessage]);
        options.onMessage?.(aiMessage);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Failed to send message';
      setError(errorMsg);
      options.onError?.(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isLoading, extractRobloxSpec, options]);

  // Upload file
  const uploadFile = useCallback(async (file: File) => {
    if (!conversationId) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversation_id', conversationId);

    try {
      setIsLoading(true);
      const response = await api.post('/roblox/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const fileMessage: Message = {
        id: `msg_${Date.now()}`,
        position: 'right',
        type: 'file',
        text: `Uploaded: ${file.name}`,
        date: new Date(),
        status: 'sent'
      };
      setMessages(prev => [...prev, fileMessage]);

      return response.data;
    } catch (err: any) {
      const errorMsg = 'Failed to upload file';
      setError(errorMsg);
      options.onError?.(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, options]);

  // Clear conversation
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    isStreaming,
    error,
    conversationId,
    sendMessage,
    uploadFile,
    clearMessages,
    setError
  };
};
