/**
 * RobloxAIAssistant Component
 *
 * AI-powered chat assistant for creating Roblox educational environments
 * Provides conversational interface with streaming responses and preview integration
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  ListItemText
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  AttachFile,
  Preview,
  School,
  Quiz,
  Terrain,
  Clear,
  Refresh,
  ExpandMore,
  ExpandLess,
  AutoAwesome,
  Code
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useAppSelector, useAppDispatch } from '../../store';
import { api } from '../../services/api';

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
  };
}

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
    text: "Create a math puzzle room for grade 5",
    category: "lesson"
  },
  {
    icon: <Terrain />,
    text: "Design a space station for science experiments",
    category: "environment"
  },
  {
    icon: <Quiz />,
    text: "Generate a history quiz about ancient Rome",
    category: "quiz"
  },
  {
    icon: <AutoAwesome />,
    text: "Build an interactive chemistry lab",
    category: "environment"
  }
];

export const RobloxAIAssistant: React.FC = () => {
  // State
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Redux
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(state => state.user);

  // WebSocket connection
  useEffect(() => {
    if (conversation?.id) {
      const wsUrl = `ws://127.0.0.1:8008/api/v1/ai-chat/ws/${conversation.id}`;
      const websocket = new WebSocket(wsUrl);

      websocket.onopen = () => {
        console.log('WebSocket connected to AI chat');
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Please try again.');
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
      };

      setWs(websocket);

      return () => {
        websocket.close();
      };
    }
  }, [conversation?.id]);

  // Handle WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'stream_start':
        setIsStreaming(true);
        setStreamingContent('');
        break;

      case 'stream_token':
        setStreamingContent(prev => prev + data.content);
        break;

      case 'stream_end':
        setIsStreaming(false);
        if (streamingContent) {
          const aiMessage: Message = {
            id: `msg_${Date.now()}`,
            role: 'assistant',
            content: streamingContent,
            timestamp: new Date(),
            metadata: { generated: true }
          };
          setMessages(prev => [...prev, aiMessage]);
          setStreamingContent('');
        }
        break;

      case 'ai_message':
        setMessages(prev => [...prev, data.message]);
        break;

      default:
        break;
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Initialize conversation
  const initializeConversation = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await api.post('/api/v1/ai-chat/conversations', {
        title: 'Roblox Educational Assistant',
        context: {
          user_role: currentUser.role,
          subject_preferences: []
        }
      });

      setConversation(response.data);
      setMessages(response.data.messages || []);
      setShowSuggestions(true);
    } catch (err: any) {
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
    if (!message.trim() || !conversation) return;

    try {
      setIsLoading(true);
      setError(null);
      setShowSuggestions(false);

      // Add user message immediately
      const userMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      setInputValue('');

      // Send via WebSocket for streaming
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'message',
          content: message
        }));
      } else {
        // Fallback to HTTP API
        const response = await api.post(`/api/v1/ai-chat/conversations/${conversation.id}/messages`, {
          message
        });

        // The AI response will come via WebSocket or background task
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle suggested prompt click
  const handleSuggestedPrompt = (prompt: string) => {
    sendMessage(prompt);
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
    sendMessage(message);
  };

  // Handle enter key
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage(inputValue);
    }
  };

  // Clear conversation
  const clearConversation = () => {
    setMessages([]);
    setError(null);
    setShowSuggestions(true);
    initializeConversation();
  };

  // Render message content with markdown
  const renderMessageContent = (content: string) => {
    return (
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus}
                language={match[1]}
                PreTag="div"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  return (
    <Paper
      elevation={3}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper'
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <SmartToy />
            </Avatar>
            <Box>
              <Typography variant="h6">Roblox AI Assistant</Typography>
              <Typography variant="caption" color="text.secondary">
                {isStreaming ? 'Typing...' : 'Ready to help'}
              </Typography>
            </Box>
          </Stack>

          <Stack direction="row" spacing={1}>
            <Tooltip title="Clear conversation">
              <IconButton onClick={clearConversation} size="small">
                <Clear />
              </IconButton>
            </Tooltip>
            <Tooltip title={isExpanded ? 'Collapse' : 'Expand'}>
              <IconButton onClick={() => setIsExpanded(!isExpanded)} size="small">
                {isExpanded ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Tooltip>
          </Stack>
        </Stack>
      </Box>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          display: isExpanded ? 'block' : 'none'
        }}
      >
        {/* Suggested Prompts */}
        {showSuggestions && messages.length <= 1 && (
          <Fade in={showSuggestions}>
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Quick Actions:
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
                {SUGGESTED_PROMPTS.map((prompt, index) => (
                  <Chip
                    key={index}
                    icon={prompt.icon}
                    label={prompt.text}
                    onClick={() => handleSuggestedPrompt(prompt.text)}
                    sx={{
                      cursor: 'pointer',
                      '&:hover': {
                        bgcolor: 'action.hover'
                      }
                    }}
                  />
                ))}
              </Stack>
            </Box>
          </Fade>
        )}

        {/* Messages List */}
        <List sx={{ width: '100%' }}>
          {messages.map((message) => (
            <ListItem
              key={message.id}
              alignItems="flex-start"
              sx={{
                flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                gap: 1
              }}
            >
              <ListItemAvatar>
                <Avatar
                  sx={{
                    bgcolor: message.role === 'user' ? 'secondary.main' : 'primary.main'
                  }}
                >
                  {message.role === 'user' ? <Person /> : <SmartToy />}
                </Avatar>
              </ListItemAvatar>

              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: message.role === 'user' ? 'action.hover' : 'background.default'
                }}
              >
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                  gutterBottom
                >
                  {message.role === 'user' ? 'You' : 'AI Assistant'}
                </Typography>
                <Box sx={{ '& p': { my: 1 } }}>
                  {renderMessageContent(message.content)}
                </Box>

                {/* Preview button if content has preview */}
                {message.metadata?.preview && (
                  <Button
                    startIcon={<Preview />}
                    size="small"
                    sx={{ mt: 1 }}
                    onClick={() => {
                      // Handle preview action
                      console.log('Show preview:', message.metadata?.preview);
                    }}
                  >
                    View 3D Preview
                  </Button>
                )}
              </Paper>
            </ListItem>
          ))}

          {/* Streaming Message */}
          {isStreaming && streamingContent && (
            <ListItem alignItems="flex-start">
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SmartToy />
                </Avatar>
              </ListItemAvatar>

              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: 'background.default'
                }}
              >
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                  gutterBottom
                >
                  AI Assistant
                </Typography>
                <Box sx={{ '& p': { my: 1 } }}>
                  {renderMessageContent(streamingContent)}
                  <CircularProgress size={16} sx={{ ml: 1 }} />
                </Box>
              </Paper>
            </ListItem>
          )}
        </List>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: isExpanded ? 'block' : 'none'
        }}
      >
        <Stack direction="row" spacing={1}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask me anything about creating Roblox educational content..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading || isStreaming}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <IconButton onClick={handleFileAttach} size="small" disabled={isLoading}>
                    <AttachFile />
                  </IconButton>
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => sendMessage(inputValue)}
                    disabled={!inputValue.trim() || isLoading || isStreaming}
                    color="primary"
                  >
                    {isLoading ? <CircularProgress size={20} /> : <Send />}
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
        </Stack>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept=".txt,.pdf,.doc,.docx,.json"
          onChange={handleFileSelect}
        />

        {/* Status */}
        {isStreaming && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            AI is thinking...
          </Typography>
        )}
      </Box>
    </Paper>
  );
};