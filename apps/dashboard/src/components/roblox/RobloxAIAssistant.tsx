/**
 * RobloxAIAssistant Component
 *
 * AI-powered chat assistant for creating Roblox educational environments
 * Provides conversational interface with streaming responses and preview integration
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Alert,
  ActionIcon,
  Avatar,
  Badge,
  Box,
  Button,
  Group,
  Loader,
  Paper,
  ScrollArea,
  Stack,
  Text,
  Textarea,
  Tooltip,
  useMantineTheme,
} from '@mantine/core';
import {
  IconSend as Send,
  IconRobot as SmartToy,
  IconUser as Person,
  IconPaperclip as AttachFile,
  IconEye as Preview,
  IconSchool as School,
  IconQuestionMark as Quiz,
  IconMountain as Terrain,
  IconX as Clear,
  IconChevronDown as ExpandMore,
  IconChevronUp as ExpandLess,
  IconSparkles as AutoAwesome,
  IconCode as CodeIcon,
} from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import { Code } from '@mantine/core';
import { useAppSelector, useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { apiClient } from '../../services/api';
import { ENABLE_WEBSOCKET, AUTH_TOKEN_KEY } from '../../config';
import { pusherService } from '../../services/pusher';
import { WebSocketMessageType } from '../../types/websocket';
import EnvironmentPreview from './EnvironmentPreview';

// Unique ID generator with counter to avoid Date.now() collisions
let messageIdCounter = 0;
const generateMessageId = (): string => {
  return `msg_${Date.now()}_${++messageIdCounter}`;
};

// Types
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    intent?: string;
    attachments?: any[];
    generated?: boolean;
    preview?: any;
    progress?: number;
    httpMode?: boolean;
    error?: boolean;
  };
}
// Helper function to validate message structure
const isValidMessage = (message: any): message is Message => {
  return (
    message &&
    typeof message === 'object' &&
    typeof message.id === 'string' &&
    typeof message.role === 'string' &&
    ['user', 'assistant', 'system'].includes(message.role) &&
    typeof message.content === 'string' &&
    message.timestamp instanceof Date
  );
};
interface Conversation {
  id: string;
  title: string;
  status: 'active' | 'archived' | 'generating';
  messages: Message[];
  created_at: Date;
  updated_at: Date;
}
interface SuggestedPrompt {
  icon: React.ReactNode;
  text: string;
  category: string;
}
// Suggested prompts for quick actions
const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  {
    icon: <School />,
    text: 'Create a 4th grade fractions pizza shop game',
    category: 'lesson',
  },
  {
    icon: <Terrain />,
    text: 'Build a 6th grade Ancient Egypt exploration world',
    category: 'environment',
  },
  {
    icon: <Quiz />,
    text: 'Design a 5th grade solar system simulation',
    category: 'quiz',
  },
  {
    icon: <AutoAwesome />,
    text: 'Make a 7th grade chemistry lab with experiments',
    category: 'environment',
  },
];
export const RobloxAIAssistant: React.FunctionComponent<Record<string, any>> = () => {
  // State
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    'connected' | 'disconnected' | 'connecting'
  >('disconnected');
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [showEnvironmentPreview, setShowEnvironmentPreview] = useState(false);
  const [currentEnvironmentId, setCurrentEnvironmentId] = useState<string | null>(null);
  const [currentEnvironmentDetails, setCurrentEnvironmentDetails] = useState<any>(null);
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Redux
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector((state) => state.user);
  // Real-time LLM response generation
  const generateLLMResponse = async (
    userMessage: string,
    conversationHistory: Message[] = []
  ): Promise<string> => {
    try {
      // Create context from conversation history
      const context = conversationHistory.map((msg) => `${msg.role}: ${msg.content}`).join('\n');
      // System prompt for educational Roblox environment creation
      const systemPrompt = `You are an AI assistant specialized in creating educational Roblox environments. Your role is to:
1. Analyze user requests for educational content
2. Ask specific follow-up questions to gather requirements
3. Guide users through the environment creation process
4. Provide personalized recommendations based on their needs
When a user requests an environment creation (like "Create 4th grade History world about US presidents"), follow this process:
1. ACKNOWLEDGE their request with enthusiasm
2. IDENTIFY what information you have (grade level, subject, topic)
3. ASK SPECIFIC follow-up questions for missing details:
   - Learning objectives: "What specific skills should students master?"
   - Class dynamics: "How many students will use this together?"
   - Duration: "How long should the experience last?"
   - Interaction style: "Should students work individually or collaborate?"
   - Assessment: "How would you like to track student progress?"
4. Once you have enough details, say "Perfect! I have everything I need to create your environment" and trigger creation
Be conversational, ask ONE question at a time, and build on their responses. Focus on understanding their specific educational goals.
IMPORTANT: When you have enough information to create an environment, end your response with the exact phrase "CREATING_ENVIRONMENT_NOW" to trigger the environment creation process.`;
      // Send to LLM API (using the correct backend format)
      const response = await apiClient.request({
        method: 'POST',
        url: '/api/v1/ai-chat/generate',
        data: {
          message: userMessage, // Backend expects just the user message string
        },
        timeout: 60000, // 60 seconds timeout for AI generation
      });
      return (
        (response as any).content ||
        "I'm here to help you create educational Roblox environments. What would you like to build?"
      );
    } catch (error) {
      console.error('LLM response generation failed:', error);
      // Check if it's a timeout error
      if (error && typeof error === 'object' && 'code' in error && error.code === 'ECONNABORTED') {
        setError(
          'AI response is taking longer than expected. Please try again or check your connection.'
        );
      } else if (error && typeof error === 'object' && 'response' in error) {
        const status = (error as any).response?.status;
        if (status === 500) {
          setError('AI service is temporarily unavailable. Please try again in a moment.');
        } else if (status === 401) {
          setError('Authentication expired. Please refresh the page and try again.');
        } else {
          setError('AI service error. Please try again.');
        }
      }
      // Fallback to intelligent static response
      return generateFallbackResponse(userMessage);
    }
  };
  // Fallback intelligent response for when LLM is unavailable
  const generateFallbackResponse = (userMessage: string): string => {
    const message = userMessage.toLowerCase();
    // Detect key elements
    const gradeMatch = message.match(/\b(\d+)(st|nd|rd|th)?\s*grade\b|\bgrade\s*(\d+)\b/);
    const grade = gradeMatch ? gradeMatch[1] || gradeMatch[3] : null;
    const subjects = {
      math: 'Mathematics',
      science: 'Science',
      history: 'History',
      english: 'English',
      geography: 'Geography',
      physics: 'Physics',
    };
    const detectedSubject = Object.entries(subjects).find(([key]) => message.includes(key))?.[1];
    const topics = {
      presidents: 'US Presidents',
      ww2: 'World War 2',
      fractions: 'Fractions',
      'solar system': 'Solar System',
      'civil war': 'Civil War',
    };
    const detectedTopic = Object.entries(topics).find(([key]) => message.includes(key))?.[1];
    if (message.includes('create') || message.includes('build') || message.includes('make')) {
      let response = "Great! I'd love to help you create that educational Roblox environment! ";
      if (detectedSubject && grade && detectedTopic) {
        response += `A ${detectedSubject} environment for ${grade}${getOrdinalSuffix(parseInt(grade))} grade focusing on ${detectedTopic} sounds fantastic!\n\n`;
        response += 'To make this perfect for your students, I need to know:\n\n';
        response += `🎯 **Learning Goals**: What specific skills about ${detectedTopic} should students master?\n`;
        response += '👥 **Class Size**: How many students will use this environment?\n';
        response += '⏱️ **Duration**: How long should the learning experience last?\n';
        response += '🎮 **Style**: Should students explore individually or work in teams?';
      } else {
        response += 'I can help you build an amazing educational world! To get started:\n\n';
        if (!grade) response += '📚 **Grade Level**: What grade are your students?\n';
        if (!detectedSubject) response += '📖 **Subject**: What subject are you teaching?\n';
        if (!detectedTopic) response += '🎯 **Topic**: What specific concept should they learn?\n';
        response += "\nOnce I have these details, I'll create a personalized Roblox environment!";
      }
      return response;
    }
    // Handle follow-up responses
    if (
      message.includes('students') ||
      message.includes('minutes') ||
      message.includes('individual') ||
      message.includes('team')
    ) {
      return (
        "Perfect! That's helpful information. Do you have any other specific requirements for the environment? For example:\n\n" +
        '• Should it include quizzes or assessments?\n' +
        '• Any specific activities or interactions you want?\n' +
        '• Should it connect to your curriculum standards?\n\n' +
        "Once I have all the details, I'll start creating your personalized Roblox environment!"
      );
    }
    return "I'm here to help you create educational Roblox environments! Try saying something like 'Create a 4th grade History world about US Presidents' and I'll guide you through the process!";
  };
  const getOrdinalSuffix = (num: number): string => {
    const j = num % 10;
    const k = num % 100;
    if (j === 1 && k !== 11) return 'st';
    if (j === 2 && k !== 12) return 'nd';
    if (j === 3 && k !== 13) return 'rd';
    return 'th';
  };
  // Check if user is providing follow-up details
  const isFollowUpResponse = (message: string): boolean => {
    const indicators = [
      'grade',
      'students',
      'minutes',
      'hour',
      'objective',
      'goal',
      'collaboration',
      'individual',
      'team',
      'class size',
      'duration',
    ];
    return indicators.some((indicator) => message.toLowerCase().includes(indicator));
  };
  // Check if user has provided enough details to create environment
  const hasEnoughDetails = (message: string, conversationHistory: Message[]): boolean => {
    const allText = conversationHistory.map((m) => m.content).join(' ') + ' ' + message;
    const text = allText.toLowerCase();
    // Check for essential details
    const hasGrade = /\b(\d+)(st|nd|rd|th)?\s*grade\b|\bgrade\s*(\d+)\b|\b(k|kindergarten)\b/.test(
      text
    );
    const hasSubject = /(math|science|history|english|geography|physics|chemistry|biology)/.test(
      text
    );
    const hasDuration = /(\d+\s*(min|minute|hour)|short|long|quick)/.test(text);
    const hasObjective = /(learn|teach|understand|practice|explore|objective|goal)/.test(text);
    // Need at least 3 out of 4 key details
    const detailCount = [hasGrade, hasSubject, hasDuration, hasObjective].filter(Boolean).length;
    return detailCount >= 3;
  };
  // Extract environment details from conversation
  const extractEnvironmentDetails = (conversationHistory: Message[]): any => {
    const allText = conversationHistory
      .map((m) => m.content)
      .join(' ')
      .toLowerCase();
    // Extract grade level
    const gradeMatch = allText.match(
      /\b(\d+)(st|nd|rd|th)?\s*grade\b|\bgrade\s*(\d+)\b|\b(k|kindergarten)\b/
    );
    const grade = gradeMatch ? gradeMatch[1] || gradeMatch[3] || 'K' : '';
    // Extract subject
    const subjects = {
      math: 'Mathematics',
      science: 'Science',
      history: 'History',
      english: 'English',
      geography: 'Geography',
      physics: 'Physics',
      chemistry: 'Chemistry',
      biology: 'Biology',
    };
    const detectedSubject =
      Object.entries(subjects).find(([key]) => allText.includes(key))?.[1] || '';
    // Extract topic/theme
    const topics = {
      presidents: 'US Presidents',
      ww2: 'World War 2',
      fractions: 'Fractions',
      'solar system': 'Solar System',
      'civil war': 'Civil War',
      'ancient egypt': 'Ancient Egypt',
      'chemistry lab': 'Chemistry Lab',
      'pizza shop': 'Pizza Shop',
      pizza: 'Pizza',
    };
    const detectedTopic = Object.entries(topics).find(([key]) => allText.includes(key))?.[1] || '';
    // Extract player count
    const playerMatch = allText.match(/(\d+)\s*students?|\b(\d+)\s*players?/);
    const maxPlayers = playerMatch ? parseInt(playerMatch[1] || playerMatch[2] || '20', 10) : 20;
    // Generate environment name
    const name =
      `${grade ? grade + 'th ' : ''}${detectedSubject || 'Educational'} ${detectedTopic || 'Environment'}`.trim();
    // Generate description
    const description = conversationHistory
      .filter((m) => m.role === 'user')
      .map((m) => m.content)
      .join(' ')
      .replace(/create|build|make|design/i, '')
      .trim();
    return {
      name: name || 'Custom Educational Environment',
      description: description || 'Educational environment created from conversation',
      grade_level: grade,
      subject: detectedSubject,
      max_players: maxPlayers,
      settings: {
        educational_mode: true,
        collaborative: allText.includes('team') || allText.includes('together'),
        assessment: allText.includes('quiz') || allText.includes('test'),
      },
    };
  };
  // Create environment from conversation
  const createEnvironmentFromConversation = async (conversationHistory: Message[]) => {
    try {
      const environmentDetails = extractEnvironmentDetails(conversationHistory);
      // Show creation progress
      const progressMessage: Message = {
        id: generateMessageId(),
        role: 'assistant',
        content: `🚀 **Creating Your Environment...**\n\nI'm now creating your "${environmentDetails.name}" environment based on our conversation. This will take a few moments.\n\n**Environment Details:**\n• Name: ${environmentDetails.name}\n• Grade Level: ${environmentDetails.grade_level || 'Any'}\n• Subject: ${environmentDetails.subject || 'General'}\n• Max Players: ${environmentDetails.max_players}\n\nPlease wait while I generate the environment and connect it to Roblox Studio...`,
        timestamp: new Date(),
        metadata: { generated: true, progress: 0 },
      };
      setMessages((prev) => [...prev, progressMessage]);
      // Call the environment creation API
      const response = await apiClient.request<any>({
        method: 'POST',
        url: '/api/v1/roblox/environment/create',
        data: environmentDetails,
        timeout: 120000, // 2 minutes timeout for environment creation
      });
      if (response.success) {
        // Success message with preview and deploy options
        const successMessage: Message = {
          id: generateMessageId(),
          role: 'assistant',
          content: `🎉 **Environment Created Successfully!**\n\nYour "${environmentDetails.name}" environment has been created and is ready in Roblox Studio!\n\n**Environment Details:**\n• Environment ID: ${response.environment_name}\n• Project Path: ${response.project_path || 'Generated'}\n• Rojo URL: ${response.rojo_url || 'Not available'}\n\n**Next Steps:**\n• Preview your environment below\n• Download the .rbxl file\n• Deploy to Roblox Studio\n\nYour environment is now ready for your students to explore!`,
          timestamp: new Date(),
          metadata: {
            generated: true,
            preview: {
              contentId: response.environment_name,
              type: 'roblox_environment',
              title: environmentDetails.name,
              previewUrl: `/environment-preview/${response.environment_name}`,
              downloadUrl: response.rojo_url,
              environmentDetails: environmentDetails,
            },
          },
        };
        setMessages((prev) => [...prev, successMessage]);
        // Show environment preview
        setCurrentEnvironmentId(response.environment_name);
        setCurrentEnvironmentDetails(environmentDetails);
        setShowEnvironmentPreview(true);
      } else {
        // Error message
        const errorMessage: Message = {
          id: generateMessageId(),
          role: 'assistant',
          content: `❌ **Environment Creation Failed**\n\nI encountered an issue while creating your environment: ${response.error || 'Unknown error'}\n\n**Troubleshooting:**\n• Make sure Roblox Studio is open with the Rojo plugin installed\n• Check that the Rojo server is running\n• Try again with a simpler description\n\nWould you like to try again or modify your request?`,
          timestamp: new Date(),
          metadata: { generated: true, error: true },
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Environment creation failed:', error);
      const errorMessage: Message = {
        id: generateMessageId(),
        role: 'assistant',
        content:
          "❌ **Environment Creation Failed**\n\nI encountered an error while creating your environment. This might be due to:\n\n• Roblox Studio not being open\n• Rojo plugin not installed or running\n• Network connectivity issues\n\n**Please try:**\n1. Opening Roblox Studio\n2. Installing the Rojo plugin\n3. Starting the Rojo server\n4. Trying your request again\n\nI'm here to help you create amazing educational environments!",
        timestamp: new Date(),
        metadata: { generated: true, error: true },
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };
  // Pusher connection for real-time chat
  useEffect(() => {
    console.log('Setting up WebSocket connection for AI chat');
    console.log('Conversation ID:', conversation?.id);
    console.log('WebSocket enabled:', ENABLE_WEBSOCKET);
    console.log('Pusher service available:', !!pusherService);
    if (conversation?.id) {
      const connectPusher = async () => {
        try {
          setConnectionStatus('connecting');
          const token = localStorage.getItem('toolboxai_auth_token');
          console.log('Auth token available:', !!token);
          // Check if Pusher is already connected
          if (pusherService.isConnected()) {
            console.log('Pusher already connected');
            setConnectionStatus('connected');
          } else {
            await pusherService.connect(token || undefined);
            console.log('Pusher connected for AI chat');
            setConnectionStatus('connected');
          }
          setError(null);
          // Subscribe to conversation channel
          const subscriptionId = pusherService.subscribe(
            `ai-chat-${conversation.id}`,
            (message) => {
              console.log('Pusher message received:', message);
              handleWebSocketMessage(message);
            }
          );
          return () => {
            pusherService.unsubscribe(subscriptionId);
            setConnectionStatus('disconnected');
          };
        } catch (error) {
          console.error('Pusher connection error:', error);
          setConnectionStatus('disconnected');
          setError('Real-time connection error. Falling back to HTTP API.');
        }
      };
      connectPusher();
    }
  }, [conversation?.id]);
  // Handle WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'stream_start': {
        setIsStreaming(true);
        setStreamingContent('');
        break;
      }
      case 'stream_token': {
        setStreamingContent((prev) => prev + data.content);
        break;
      }
      case 'stream_end': {
        setIsStreaming(false);
        if (streamingContent.trim()) {
          const aiMessage: Message = {
            id: generateMessageId(),
            role: 'assistant',
            content: streamingContent.trim(),
            timestamp: new Date(),
            metadata: { generated: true },
          };
          setMessages((prev) => [...prev, aiMessage]);
        }
        setStreamingContent('');
        break;
      }
      case 'ai_message': {
        console.log('AI message payload:', data.payload);
        // Handle different payload structures
        let messageData = null;
        // Case 1: Full message object in payload.message
        if (
          data.payload?.message &&
          typeof data.payload.message === 'object' &&
          data.payload.message.id
        ) {
          messageData = data.payload.message;
        }
        // Case 2: Simple string message (user message echo)
        else if (typeof data.payload?.message === 'string') {
          // This is likely a user message echo, not an AI response
          console.log('Received user message echo:', data.payload.message);
          return; // Don't add user message echoes to the chat
        }
        // Case 3: Direct payload is the message
        else if (data.payload && typeof data.payload === 'object' && data.payload.id) {
          messageData = data.payload;
        }
        if (messageData && isValidMessage(messageData)) {
          setMessages((prev) => [...prev, messageData]);
        } else {
          console.warn('Invalid message received:', data.payload);
          // Try to create a valid message from the payload
          if (data.payload && typeof data.payload === 'object') {
            const message = {
              id: data.payload.id || `msg_${Date.now()}`,
              role: data.payload.role || 'assistant',
              content:
                data.payload.content || data.payload.text || data.payload.message || 'No content',
              timestamp: data.payload.timestamp ? new Date(data.payload.timestamp) : new Date(),
              metadata: data.payload.metadata || {},
            };
            console.log('Created message from payload:', message);
            if (isValidMessage(message)) {
              setMessages((prev) => [...prev, message]);
            }
          }
        }
        break;
      }
      case 'ai_response': {
        console.log('AI response received:', data.payload);
        // Extract the message from the payload
        const aiMessage = data.payload?.message;
        if (aiMessage && isValidMessage(aiMessage)) {
          // Convert timestamp if it's a string
          if (typeof aiMessage.timestamp === 'string') {
            aiMessage.timestamp = new Date(aiMessage.timestamp);
          }
          console.log('Adding AI response to messages:', aiMessage);
          setMessages((prev) => [...prev, aiMessage]);
        } else {
          console.warn('Invalid AI response message:', data.payload);
        }
        break;
      }
      default:
        break;
    }
  };
  // Auto-scroll to bottom
  useEffect(() => {
    console.log('Messages updated:', messages.length, 'messages');
    console.log('Current messages:', messages);
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);
  // Initialize conversation
  const initializeConversation = async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('Initializing AI Assistant conversation...');
      console.log('Current user:', currentUser);
      // Use fallback user role if currentUser is not available
      const userRole = currentUser?.role || 'teacher';
      const response = await apiClient['request']<any>({
        method: 'POST',
        url: '/api/v1/ai-chat/conversations',
        data: {
          title: 'Roblox Educational Assistant',
          context: {
            user_role: userRole,
            subject_preferences: [],
          },
        },
      });
      console.log('Conversation created:', response);
      console.log('Messages from conversation:', response.messages);
      setConversation(response);
      setMessages(response.messages || []);
      setShowSuggestions(true);
      console.log('State updated - conversation and messages set');
    } catch (err: any) {
      console.error('Failed to initialize conversation:', err);
      setError(err.message || 'Failed to start conversation');
    } finally {
      setIsLoading(false);
    }
  };
  // Start conversation on mount
  useEffect(() => {
    initializeConversation();
  }, []);
  // Send message
  const sendMessage = async (message: string) => {
    if (!message.trim() || !conversation) {
      console.log('Cannot send message:', {
        message: message.trim(),
        conversation: !!conversation,
      });
      return;
    }
    console.log('Sending message:', message);
    console.log('WebSocket enabled:', ENABLE_WEBSOCKET);
    console.log('Pusher connected:', pusherService.isConnected());
    try {
      setIsLoading(true);
      setError(null);
      setShowSuggestions(false);
      // Add user message immediately
      const userMessage: Message = {
        id: generateMessageId(),
        role: 'user',
        content: message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setInputValue('');
      // Send via Pusher for real-time updates (if enabled)
      if (ENABLE_WEBSOCKET && pusherService.isConnected()) {
        try {
          console.log('Sending user message notification via Pusher...');
          await pusherService.send(
            WebSocketMessageType.AI_MESSAGE,
            {
              conversation_id: conversation.id,
              message: message,
            },
            {
              channel: `ai-chat-${conversation.id}`,
            }
          );
          console.log('User message notification sent via Pusher');
        } catch (pusherError) {
          console.error('Pusher notification failed:', pusherError);
          // Continue anyway - Pusher is just for real-time updates
        }
      }
      // Always call the AI generation API with streaming support
      try {
        console.log('Calling AI generation API with streaming...');
        // Create a temporary AI message for streaming content
        const aiMessageId = generateMessageId();
        const tempAiMessage: Message = {
          id: aiMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          metadata: { generated: true, streaming: true },
        };
        // Add the temporary message immediately for visual feedback
        setMessages((prev) => [...prev, tempAiMessage]);
        // Use fetch for streaming response
        const response = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8009'}/api/v1/ai-chat/generate`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem(AUTH_TOKEN_KEY) || 'dev-token'}`,
            },
            body: JSON.stringify({
              conversation_id: conversation.id,
              message: message,
            }),
          }
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let streamedContent = '';
        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n').filter((line) => line.trim());
            for (const line of lines) {
              try {
                const data = JSON.parse(line);
                if (data.type === 'token') {
                  streamedContent += data.content;
                  // Update the message content in real-time
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === aiMessageId ? { ...msg, content: streamedContent } : msg
                    )
                  );
                } else if (data.type === 'complete') {
                  // Final message received
                  const finalMessage = data.message;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === aiMessageId
                        ? {
                            ...msg,
                            content: finalMessage.content,
                            timestamp: new Date(finalMessage.timestamp),
                            metadata: { ...finalMessage.metadata, streaming: false },
                          }
                        : msg
                    )
                  );
                  console.log('AI streaming completed');
                } else if (data.type === 'error') {
                  console.error('Streaming error:', data.error);
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === aiMessageId ? { ...msg, content: `Error: ${data.error}` } : msg
                    )
                  );
                }
              } catch (e) {
                // Ignore JSON parse errors for incomplete chunks
              }
            }
          }
        }
        console.log('AI response streaming completed');
        // Check if this should trigger environment creation
        if (streamedContent && streamedContent.includes('CREATING_ENVIRONMENT_NOW')) {
          console.log('Triggering environment creation from conversation');
          await createEnvironmentFromConversation([
            ...messages,
            userMessage,
            {
              id: generateMessageId(),
              role: 'assistant',
              content: streamedContent,
              timestamp: new Date(),
            },
          ]);
        }
      } catch (httpError) {
        console.error('AI generation API failed:', httpError);
        // Provide more specific error messages
        if (
          httpError &&
          typeof httpError === 'object' &&
          'code' in httpError &&
          httpError.code === 'ECONNABORTED'
        ) {
          setError('AI generation timed out. Please check your connection and try again.');
        } else if (httpError && typeof httpError === 'object' && 'response' in httpError) {
          const status = (httpError as any).response?.status;
          if (status === 401) {
            setError('Authentication expired. Please refresh the page and try again.');
          } else if (status === 500) {
            setError('Server error. Please try again in a moment.');
          } else {
            setError('Failed to send message. Please try again.');
          }
        } else {
          setError('Failed to send message. Please try again.');
        }
      }
      // Use real-time LLM response - DISABLED (using HTTP API response above)
      /*setTimeout(async () => {
          try {
            let aiContent: string;
            // Generate LLM response which will analyze input and trigger environment creation if ready
            aiContent = await generateLLMResponse(message, messages);
            // Check if AI response indicates environment creation should be triggered
            if (aiContent.includes('CREATING_ENVIRONMENT_NOW') ||
                (hasEnoughDetails(message, messages) && aiContent.includes('Perfect! I have everything I need'))) {
              // Remove the trigger phrase from the displayed content
              const displayContent = aiContent.replace('CREATING_ENVIRONMENT_NOW', '').trim();
              // Add the AI response first
              const aiMessage: Message = {
                id: generateMessageId(),
                role: 'assistant',
                content: displayContent,
                timestamp: new Date(),
                metadata: { generated: true, httpMode: true }
              };
              setMessages(prev => [...prev, aiMessage]);
              // Trigger environment creation
              setTimeout(() => {
                createEnvironmentFromConversation([...messages, userMessage, aiMessage]);
              }, 1000);
              return; // Don't add the message again below
            }
            const aiMessage: Message = {
              id: generateMessageId(),
              role: 'assistant',
              content: aiContent,
              timestamp: new Date(),
              metadata: { generated: true, httpMode: true }
            };
            setMessages(prev => [...prev, aiMessage]);
          } catch (error) {
            console.error('AI response generation failed:', error);
            const errorMessage: Message = {
              id: generateMessageId(),
              role: 'assistant',
              content: 'I apologize, but I\'m having trouble processing your request right now. Please try again or rephrase your question.',
              timestamp: new Date(),
              metadata: { generated: true, httpMode: true, error: true }
            };
            setMessages(prev => [...prev, errorMessage]);
          }
        }, 500);*/
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };
  // Handle suggested prompt click
  const handleSuggestedPrompt = (prompt: string) => {
    void sendMessage(prompt);
  };
  // Handle file attachment
  const handleFileAttach = () => {
    fileInputRef.current?.click();
  };
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    // Handle file upload (implement actual upload logic)
    const message = `I've uploaded a file: ${file.name}. Please analyze it for educational content.`;
    void sendMessage(message);
  };
  // Handle enter key
  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(inputValue);
    }
  };
  // Clear conversation
  const clearConversation = () => {
    setMessages([]);
    setError(null);
    setShowSuggestions(true);
    void initializeConversation();
  };
  const theme = useMantineTheme();

  // Render message content with markdown
  const renderMessageContent = (content: string) => (
    <ReactMarkdown
      components={{
        code({ className, children, ...props }: any) {
          const inline = (props as any).inline;
          const match = /language-(\w+)/.exec(className || '');
          if (!inline && match) {
            return (
              <Code
                block
                style={{
                  backgroundColor: '#1e1e1e',
                  color: '#d4d4d4',
                  padding: '1rem',
                  borderRadius: '4px',
                  overflow: 'auto',
                }}
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </Code>
            );
          }
          return <Code {...props}>{children}</Code>;
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );

  const handleDeployEnvironment = async (contentId?: string) => {
    if (!contentId) return;
    try {
      await apiClient.request({
        method: 'POST',
        url: `/api/v1/roblox/deploy/${contentId}`,
      });
      dispatch(
        addNotification({
          type: 'success',
          message: 'Environment deployed to Roblox Studio!',
          autoHide: true,
        })
      );
    } catch (deployError) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to deploy to Roblox Studio',
          autoHide: true,
        })
      );
      console.error('Deploy to Roblox failed:', deployError);
    }
  };

  const renderPreviewActions = (message: Message) => {
    const preview = message.metadata?.preview;
    if (!preview?.contentId) return null;

    return (
      <Group gap="xs" mt="sm">
        <Button
          size="xs"
          variant="light"
          leftSection={<Preview size={14} />}
          onClick={() => window.open(`/environment-preview/${preview.contentId}`, '_blank')}
        >
          View 3D Environment
        </Button>
        <Button
          size="xs"
          variant="outline"
          leftSection={<CodeIcon size={14} />}
          onClick={() => void handleDeployEnvironment(preview.contentId)}
        >
          Deploy to Roblox
        </Button>
      </Group>
    );
  };

  const renderMessageBubble = (message: Message) => {
    const isUser = message.role === 'user';
    const label = isUser ? 'You' : 'AI Assistant';
    const avatar = (
      <Avatar radius="xl" color={isUser ? 'gray' : 'brand'}>
        {isUser ? <Person size={16} /> : <SmartToy size={16} />}
      </Avatar>
    );

    return (
      <Box key={message.id}>
        <Group align="flex-start" justify={isUser ? 'flex-end' : 'flex-start'} gap="sm">
          {!isUser && avatar}
          <Box style={{ maxWidth: '75%' }}>
            <Text size="xs" c="dimmed" mb={4}>
              {label}
            </Text>
            <Paper
              shadow="xs"
              radius="md"
              withBorder
              p="sm"
              style={{
                backgroundColor: isUser ? theme.colors.gray[0] : theme.white,
              }}
            >
              {renderMessageContent(message.content)}
              {renderPreviewActions(message)}
            </Paper>
          </Box>
          {isUser && avatar}
        </Group>
      </Box>
    );
  };

  const renderStreamingMessage = () => (
    <Box>
      <Group align="flex-start" gap="sm">
        <Avatar radius="xl" color="brand">
          <SmartToy size={16} />
        </Avatar>
        <Box style={{ maxWidth: '75%' }}>
          <Text size="xs" c="dimmed" mb={4}>
            AI Assistant
          </Text>
          <Paper shadow="xs" radius="md" withBorder p="sm">
            {renderMessageContent(streamingContent)}
            <Loader size="sm" mt="sm" />
          </Paper>
        </Box>
      </Group>
    </Box>
  );

  const statusBadge = (() => {
    switch (connectionStatus) {
      case 'connected':
        return { label: 'Connected', color: 'green' as const };
      case 'connecting':
        return { label: 'Connecting…', color: 'yellow' as const };
      default:
        return { label: 'Offline', color: 'gray' as const };
    }
  })();

  return (
    <Paper
      withBorder
      shadow="md"
      radius="lg"
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Box px="md" py="sm" style={{ borderBottom: `1px solid ${theme.colors.gray[3]}` }}>
        <Group justify="space-between" align="center">
          <Group align="center" gap="sm">
            <Avatar radius="xl" color="brand">
              <SmartToy size={18} />
            </Avatar>
            <Box>
              <Text size="lg" fw={600}>
                Roblox AI Assistant
              </Text>
              <Group gap={6} align="center">
                <Text size="xs" c="dimmed">
                  {isStreaming ? 'Typing…' : 'Ready to help'}
                </Text>
                <Badge variant="light" color={statusBadge.color} size="sm">
                  {statusBadge.label}
                </Badge>
              </Group>
            </Box>
          </Group>
          <Group gap="xs">
            <Tooltip label="Clear conversation">
              <ActionIcon
                variant="subtle"
                onClick={clearConversation}
                disabled={isLoading || isStreaming}
              >
                <Clear size={16} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label={isExpanded ? 'Collapse' : 'Expand'}>
              <ActionIcon variant="subtle" onClick={() => setIsExpanded((prev) => !prev)}>
                {isExpanded ? <ExpandLess size={16} /> : <ExpandMore size={16} />}
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Box>

      {isExpanded && (
        <Box
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {showSuggestions && messages.length <= 1 && (
            <Box px="md" py="sm">
              <Text size="xs" c="dimmed" mb={6}>
                Quick Actions
              </Text>
              <Group gap="xs">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <Button
                    key={prompt.text}
                    size="xs"
                    variant="light"
                    leftSection={prompt.icon as React.ReactElement}
                    onClick={() => handleSuggestedPrompt(prompt.text)}
                  >
                    {prompt.text}
                  </Button>
                ))}
              </Group>
            </Box>
          )}

          <ScrollArea style={{ flex: 1 }}>
            <Stack gap="sm" px="md" py="sm">
              {messages.filter(isValidMessage).map(renderMessageBubble)}
              {isStreaming && streamingContent && renderStreamingMessage()}
              {error && (
                <Alert color="red" variant="light" withCloseButton onClose={() => setError(null)}>
                  {error}
                </Alert>
              )}
              <div ref={messagesEndRef} />
            </Stack>
          </ScrollArea>
        </Box>
      )}

      {showEnvironmentPreview && currentEnvironmentId && (
        <Box px="md" py="sm" style={{ borderTop: `1px solid ${theme.colors.gray[3]}` }}>
          <EnvironmentPreview
            environmentId={currentEnvironmentId}
            environmentDetails={currentEnvironmentDetails}
            onClose={() => {
              setShowEnvironmentPreview(false);
              setCurrentEnvironmentId(null);
              setCurrentEnvironmentDetails(null);
            }}
          />
        </Box>
      )}

      {isExpanded && (
        <Box px="md" py="sm" style={{ borderTop: `1px solid ${theme.colors.gray[3]}` }}>
          <Group align="flex-end" gap="xs">
            <Textarea
              placeholder="Ask me anything about creating Roblox educational content..."
              value={inputValue}
              onChange={(event) => setInputValue(event.currentTarget.value)}
              onKeyDown={handleKeyDown}
              minRows={1}
              maxRows={4}
              autosize
              disabled={isLoading || isStreaming}
              style={{ flex: 1 }}
            />
            <Tooltip label="Attach file">
              <ActionIcon variant="subtle" onClick={handleFileAttach} disabled={isLoading}>
                <AttachFile size={18} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Send message">
              <ActionIcon
                color="brand"
                radius="xl"
                size="lg"
                onClick={() => void sendMessage(inputValue)}
                disabled={!inputValue.trim() || isLoading || isStreaming}
              >
                {isLoading ? <Loader size="sm" /> : <Send size={18} />}
              </ActionIcon>
            </Tooltip>
          </Group>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept=".txt,.pdf,.doc,.docx,.json"
            onChange={handleFileSelect}
          />
          {isStreaming && (
            <Text size="xs" c="dimmed" mt="xs">
              AI is thinking...
            </Text>
          )}
        </Box>
      )}
    </Paper>
  );
};
