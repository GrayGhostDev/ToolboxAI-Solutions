/**
 * RobloxAIAssistantEnhanced Component
 *
 * Enhanced AI-powered chat assistant with improved accessibility and responsiveness
 * Features include keyboard navigation, screen reader support, and mobile optimization
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Stack,
  CircularProgress,
  Fade,
  Button,
  Divider,
  Alert,
  Tooltip,
  InputAdornment,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  useTheme,
  useMediaQuery,
  Skeleton,
  LinearProgress,
  Badge,
  Collapse,
  Menu,
  MenuItem,
  ListItemIcon,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  AttachFile,
  Preview,
  School,
  Clear,
  Refresh,
  ExpandMore,
  ExpandLess,
  AutoAwesome,
  Code,
  Mic,
  MicOff,
  VolumeUp,
  VolumeOff,
  Settings,
  Accessibility,
  KeyboardArrowUp,
  Stop,
  ContentCopy,
  Download,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useAppSelector, useAppDispatch } from '../../store';
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
  const theme = useTheme();
  const dispatch = useAppDispatch();

  // Responsive breakpoints
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

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
      <ListItem
        key={message.id}
        sx={{
          flexDirection: isUser ? 'row-reverse' : 'row',
          gap: 1,
          py: 2,
          px: isMobile ? 1 : 2,
          '&:hover': {
            bgcolor: theme.palette.action.hover,
          },
        }}
        selected={selectedMessageId === message.id}
        onClick={() => setSelectedMessageId(message.id)}
        onContextMenu={(e) => {
          e.preventDefault();
          setContextMenu({ x: e.clientX, y: e.clientY, messageId: message.id });
        }}
        role="article"
        aria-label={`${isUser ? 'Your message' : 'AI response'}: ${message.content.substring(0, 50)}...`}
      >
        <ListItemAvatar>
          <Avatar
            sx={{
              bgcolor: isUser ? theme.palette.primary.main : theme.palette.secondary.main,
              width: isMobile ? 32 : 40,
              height: isMobile ? 32 : 40,
            }}
            aria-hidden="true"
          >
            {isUser ? <Person /> : <SmartToy />}
          </Avatar>
        </ListItemAvatar>

        <ListItemText
          primary={
            <Box>
              <Typography
                variant={a11ySettings.largeText ? 'body1' : 'body2'}
                color="text.secondary"
                gutterBottom
              >
                {isUser ? 'You' : 'AI Assistant'}
                <Chip
                  label={new Date(message.timestamp).toLocaleTimeString()}
                  size="small"
                  sx={{ ml: 1 }}
                  aria-label={`Sent at ${new Date(message.timestamp).toLocaleTimeString()}`}
                />
              </Typography>

              {isLoading ? (
                <Box>
                  <Skeleton variant="text" width="80%" />
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="text" width="70%" />
                </Box>
              ) : (
                <Typography
                  variant={a11ySettings.largeText ? 'body1' : 'body2'}
                  component="div"
                  sx={{
                    '& p': { mb: 1 },
                    '& code': {
                      bgcolor: 'background.paper',
                      p: 0.5,
                      borderRadius: 0.5,
                      fontFamily: 'monospace',
                    },
                  }}
                >
                  {message.content}
                </Typography>
              )}
            </Box>
          }
          secondary={
            message.metadata?.error && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {message.metadata.error}
              </Alert>
            )
          }
        />
      </ListItem>
    );
  }, [theme, isMobile, selectedMessageId, a11ySettings.largeText]);

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: a11ySettings.highContrast ? 'background.default' : 'background.paper',
      }}
      role="main"
      aria-label="Roblox AI Assistant Chat Interface"
    >
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
        component="header"
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
            <AutoAwesome />
          </Avatar>
          <Box>
            <Typography variant="h6" component="h1">
              Roblox AI Assistant
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {isLoading ? 'Generating response...' : 'Ready to help'}
            </Typography>
          </Box>
        </Stack>

        <Stack direction="row" spacing={1}>
          <Tooltip title="Accessibility Settings">
            <IconButton
              onClick={() => setA11ySettings(prev => ({ ...prev, speechOutput: !prev.speechOutput }))}
              aria-label="Toggle speech output"
            >
              {a11ySettings.speechOutput ? <VolumeUp /> : <VolumeOff />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Toggle Preview">
            <IconButton
              onClick={() => setShowPreview(!showPreview)}
              aria-label="Toggle preview panel"
            >
              <Preview />
            </IconButton>
          </Tooltip>

          <Tooltip title="Clear Chat">
            <IconButton
              onClick={() => setMessages([])}
              aria-label="Clear all messages"
            >
              <Clear />
            </IconButton>
          </Tooltip>
        </Stack>
      </Paper>

      {/* Messages Area */}
      <Box
        ref={messageListRef}
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
        }}
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        <List>
          {messages.map(renderMessage)}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
        }}
        component="footer"
      >
        {isLoading && (
          <LinearProgress
            sx={{ mb: 2 }}
            aria-label="Loading response"
          />
        )}

        <Stack direction="row" spacing={1} alignItems="flex-end">
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to create educational Roblox content..."
            disabled={isLoading}
            variant="outlined"
            InputProps={{
              sx: {
                fontSize: a11ySettings.largeText ? '1.125rem' : '1rem',
              },
              startAdornment: (
                <InputAdornment position="start">
                  <IconButton
                    onClick={toggleVoiceInput}
                    size="small"
                    color={isListening ? 'primary' : 'default'}
                    aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
                  >
                    {isListening ? <Mic /> : <MicOff />}
                  </IconButton>
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton size="small" aria-label="Attach file">
                    <AttachFile />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            aria-label="Message input"
            aria-describedby="input-helper-text"
          />

          {isLoading ? (
            <IconButton
              onClick={handleCancelRequest}
              color="error"
              size="large"
              aria-label="Cancel request"
            >
              <Stop />
            </IconButton>
          ) : (
            <IconButton
              onClick={handleSendMessage}
              color="primary"
              size="large"
              disabled={!input.trim()}
              aria-label="Send message"
            >
              <Send />
            </IconButton>
          )}
        </Stack>

        <Typography
          id="input-helper-text"
          variant="caption"
          color="text.secondary"
          sx={{ mt: 1, display: 'block' }}
        >
          Press Enter to send, Shift+Enter for new line
        </Typography>
      </Paper>

      {/* Context Menu */}
      <Menu
        open={Boolean(contextMenu)}
        onClose={() => setContextMenu(null)}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu ? { top: contextMenu.y, left: contextMenu.x } : undefined
        }
      >
        <MenuItem
          onClick={() => {
            const message = messages.find(m => m.id === contextMenu?.messageId);
            if (message) handleCopyMessage(message.content);
            setContextMenu(null);
          }}
        >
          <ListItemIcon>
            <ContentCopy fontSize="small" />
          </ListItemIcon>
          <ListItemText>Copy</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
}