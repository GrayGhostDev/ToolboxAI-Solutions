/**
 * RobloxAIAssistantEnhanced Component
 *
 * Enhanced AI-powered chat assistant with improved accessibility and responsiveness
 * Features include keyboard navigation, screen reader support, and mobile optimization
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  TextInput,
  ActionIcon,
  Text,
  Avatar,
  Badge,
  Stack,
  Loader,
  Button,
  Alert,
  Tooltip,
  List,
  Group,
  Skeleton,
  Progress,
  Collapse,
  Menu,
  Title,
  Textarea,
  useMantineTheme
} from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';

import {
  IconSend,
  IconRobot,
  IconUser,
  IconPaperclip,
  IconEye,
  IconSchool,
  IconX,
  IconRefresh,
  IconChevronDown,
  IconChevronUp,
  IconSparkles,
  IconCode,
  IconMicrophone,
  IconMicrophoneOff,
  IconVolume,
  IconVolumeOff,
  IconSettings,
  IconAccessible,
  IconArrowUp,
  IconPlayerStop,
  IconCopy,
  IconDownload,
} from '@tabler/icons-react';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
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
    isLoading?: boolean;
  };
}
interface A11ySettings {
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  screenReaderMode: boolean;
  keyboardNavigation: boolean;
  speechOutput: boolean;
}
export default function RobloxAIAssistantEnhanced() {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  // Responsive breakpoints
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(max-width: 1024px)');
  const isDesktop = useMediaQuery('(min-width: 1200px)');
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(true);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; messageId: string } | null>(null);
  // Accessibility state
  const [a11ySettings, setA11ySettings] = useState<A11ySettings>({
    highContrast: false,
    largeText: false,
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    screenReaderMode: false,
    keyboardNavigation: true,
    speechOutput: false,
  });
  // Voice input state
  const [isListening, setIsListening] = useState(false);
  const recognition = useRef<any>(null);
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    if (!a11ySettings.reducedMotion) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
    }
  }, [a11ySettings.reducedMotion]);
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);
  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognition.current = new SpeechRecognition();
      recognition.current.continuous = false;
      recognition.current.interimResults = true;
      recognition.current.lang = 'en-US';
      recognition.current.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result: any) => result.transcript)
          .join('');
        setInput(transcript);
      };
      recognition.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };
      recognition.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);
  // Speech synthesis for screen reader mode
  const speak = useCallback((text: string) => {
    if (a11ySettings.speechOutput && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
  }, [a11ySettings.speechOutput]);
  // Toggle voice input
  const toggleVoiceInput = useCallback(() => {
    if (!recognition.current) {
      dispatch(addNotification({
        message: 'Speech recognition not supported in this browser',
        type: 'warning',
      }));
      return;
    }
    if (isListening) {
      recognition.current.stop();
    } else {
      recognition.current.start();
      setIsListening(true);
    }
  }, [isListening, dispatch]);
  // Handle send message
  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return;
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);
    // Announce for screen readers
    if (a11ySettings.screenReaderMode) {
      const announcement = `You said: ${userMessage.content}. Waiting for AI response.`;
      speak(announcement);
    }
    // Add typing indicator message
    const typingMessage: Message = {
      id: `typing-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      metadata: { isLoading: true },
    };
    setMessages(prev => [...prev, typingMessage]);
    try {
      // Simulate API call with abort controller for cancellation
      abortControllerRef.current = new AbortController();
      // Simulated streaming response
      await new Promise((resolve) => {
        setTimeout(() => {
          const assistantMessage: Message = {
            id: `msg-${Date.now() + 1}`,
            role: 'assistant',
            content: `I'll help you create an educational Roblox environment. Based on your request "${userMessage.content}", I can generate interactive learning experiences with quizzes, terrain, and engaging gameplay elements.
Here's what I can create for you:
- Interactive quiz zones with automatic scoring
- Educational terrain that visualizes concepts
- NPC guides that explain topics
- Collectible items that teach as players explore
Would you like me to start with a specific subject area or learning objective?`,
            timestamp: new Date(),
            metadata: { generated: true },
          };
          // Remove typing indicator and add real message
          setMessages(prev => prev.filter(m => !m.metadata?.isLoading).concat(assistantMessage));
          // Announce response for screen readers
          if (a11ySettings.screenReaderMode) {
            speak(assistantMessage.content);
          }
          resolve(null);
        }, 1500);
      });
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError('Failed to get response. Please try again.');
        dispatch(addNotification({
          message: 'Failed to get AI response',
          type: 'error',
        }));
      }
      // Remove typing indicator
      setMessages(prev => prev.filter(m => !m.metadata?.isLoading));
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [input, isLoading, a11ySettings.screenReaderMode, dispatch, speak]);
  // Cancel ongoing request
  const handleCancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setMessages(prev => prev.filter(m => !m.metadata?.isLoading));
    }
  }, []);
  // Copy message to clipboard
  const handleCopyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
    dispatch(addNotification({
      message: 'Message copied to clipboard',
      type: 'success',
    }));
  }, [dispatch]);
  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!a11ySettings.keyboardNavigation) return;
    // Send message with Enter (Shift+Enter for new line)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
    // Cancel with Escape
    if (e.key === 'Escape' && isLoading) {
      handleCancelRequest();
    }
    // Navigate messages with arrow keys when not in input
    if (e.target !== inputRef.current) {
      if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        e.preventDefault();
        // Message navigation logic here
      }
    }
  }, [a11ySettings.keyboardNavigation, handleSendMessage, isLoading, handleCancelRequest]);
  // Render message with proper semantic markup
  const renderMessage = useCallback((message: Message) => {
    const isUser = message.role === 'user';
    const isLoading = message.metadata?.isLoading;
    return (
      <Box
        key={message.id}
        style={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          gap: '8px',
          padding: isMobile ? '8px' : '16px',
          cursor: 'pointer',
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = theme.colors.gray[0]}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        onClick={() => setSelectedMessageId(message.id)}
        onContextMenu={(e) => {
          e.preventDefault();
          setContextMenu({ x: e.clientX, y: e.clientY, messageId: message.id });
        }}
        role="article"
        aria-label={`${isUser ? 'Your message' : 'AI response'}: ${message.content.substring(0, 50)}...`}
      >
        <Avatar
          color={isUser ? 'blue' : 'grape'}
          size={isMobile ? 32 : 40}
          aria-hidden="true"
        >
          {isUser ? <IconUser size={20} /> : <IconRobot size={20} />}
        </Avatar>
        <Box style={{ flex: 1 }}>
          <Group align="center" mb="xs">
            <Text
              size={a11ySettings.largeText ? 'md' : 'sm'}
              c="dimmed"
            >
              {isUser ? 'You' : 'AI Assistant'}
            </Text>
            <Badge
              size="sm"
              variant="light"
              aria-label={`Sent at ${new Date(message.timestamp).toLocaleTimeString()}`}
            >
              {new Date(message.timestamp).toLocaleTimeString()}
            </Badge>
          </Group>
          {isLoading ? (
            <Stack gap="xs">
              <Skeleton height={16} width="80%" />
              <Skeleton height={16} width="60%" />
              <Skeleton height={16} width="70%" />
            </Stack>
          ) : (
            <Text
              size={a11ySettings.largeText ? 'md' : 'sm'}
              style={{
                fontFamily: message.content.includes('```') ? 'monospace' : 'inherit',
                whiteSpace: 'pre-wrap'
              }}
            >
              {message.content}
            </Text>
          )}
          {message.metadata?.error && (
            <Alert color="red" mt="sm">
              {message.metadata.error}
            </Alert>
          )}
        </Box>
      </Box>
    );
  }, [theme, isMobile, selectedMessageId, a11ySettings.largeText]);
  return (
    <Box
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: a11ySettings.highContrast ? theme.colors.gray[0] : theme.white,
      }}
      role="main"
      aria-label="Roblox AI Assistant Chat Interface"
    >
      {/* Header */}
      <Paper
        p="md"
        style={{
          borderBottom: `1px solid ${theme.colors.gray[3]}`,
          borderRadius: 0
        }}
        component="header"
      >
        <Group justify="space-between" align="center">
          <Group align="center">
            <Avatar color="blue">
              <IconSparkles size={20} />
            </Avatar>
            <Box>
              <Title order={3}>
                Roblox AI Assistant
              </Title>
              <Text size="sm" c="dimmed">
                {isLoading ? 'Generating response...' : 'Ready to help'}
              </Text>
            </Box>
          </Group>
          <Group>
            <Tooltip label="Accessibility Settings">
              <ActionIcon
                onClick={() => setA11ySettings(prev => ({ ...prev, speechOutput: !prev.speechOutput }))}
                aria-label="Toggle speech output"
              >
                {a11ySettings.speechOutput ? <IconVolume size={18} /> : <IconVolumeOff size={18} />}
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Toggle Preview">
              <ActionIcon
                onClick={() => setShowPreview(!showPreview)}
                aria-label="Toggle preview panel"
              >
                <IconEye size={18} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Clear Chat">
              <ActionIcon
                onClick={() => setMessages([])}
                aria-label="Clear all messages"
              >
                <IconX size={18} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Paper>
      {/* Messages Area */}
      <Box
        ref={messageListRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
        }}
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        <Stack gap="sm">
          {messages.map(renderMessage)}
        </Stack>
        <div ref={messagesEndRef} />
      </Box>
      {/* Input Area */}
      <Paper
        p="md"
        style={{
          borderTop: `1px solid ${theme.colors.gray[3]}`,
          borderRadius: 0
        }}
        component="footer"
      >
        {isLoading && (
          <Progress mb="md" aria-label="Loading response" />
        )}
        <Group align="flex-end">
          <Box style={{ flex: 1, position: 'relative' }}>
            <Textarea
              ref={inputRef}
              autosize
              maxRows={4}
              value={input}
              onChange={(event) => setInput(event.currentTarget.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me to create educational Roblox content..."
              disabled={isLoading}
              style={{
                fontSize: a11ySettings.largeText ? '18px' : '16px',
              }}
              leftSection={
                <ActionIcon
                  onClick={toggleVoiceInput}
                  size="sm"
                  color={isListening ? 'blue' : 'gray'}
                  aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
                >
                  {isListening ? <IconMicrophone size={16} /> : <IconMicrophoneOff size={16} />}
                </ActionIcon>
              }
              rightSection={
                <ActionIcon size="sm" aria-label="Attach file">
                  <IconPaperclip size={16} />
                </ActionIcon>
              }
              aria-label="Message input"
              aria-describedby="input-helper-text"
            />
          </Box>
          {isLoading ? (
            <ActionIcon
              onClick={handleCancelRequest}
              color="red"
              size="lg"
              aria-label="Cancel request"
            >
              <IconPlayerStop size={20} />
            </ActionIcon>
          ) : (
            <ActionIcon
              onClick={handleSendMessage}
              color="blue"
              size="lg"
              disabled={!input.trim()}
              aria-label="Send message"
            >
              <IconSend size={20} />
            </ActionIcon>
          )}
        </Group>
        <Text
          id="input-helper-text"
          size="xs"
          c="dimmed"
          mt="sm"
        >
          Press Enter to send, Shift+Enter for new line
        </Text>
      </Paper>
      {/* Context Menu */}
      <Menu opened={Boolean(contextMenu)} onClose={() => setContextMenu(null)}>
        <Menu.Item
          leftSection={<IconCopy size={16} />}
          onClick={() => {
            const message = messages.find(m => m.id === contextMenu?.messageId);
            if (message) handleCopyMessage(message.content);
            setContextMenu(null);
          }}
        >
          Copy
        </Menu.Item>
      </Menu>
    </Box>
  );
}