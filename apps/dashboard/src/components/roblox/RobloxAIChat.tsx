/**
 * RobloxAIChat Component
 * 
 * Interactive AI chat interface for guiding users through Roblox world creation
 * Provides real-time communication with AI agents to collect parameters and
 * generate personalized educational environments based on templates.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Chip,
  Stack,
  Avatar,
  IconButton,
  CircularProgress,
  Alert,
  Tooltip,
  useTheme,
  alpha
} from '@mui/material';
import {
  Send,
  AutoAwesome,
  School,
  Terrain,
  Quiz,
  Code,
  Mic,
  MicOff,
  Refresh,
  Clear,
  Download,
  Share
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../store';
import { pusherService } from '../../services/pusher';
import { api } from '../../services/api';
import {
  WebSocketMessageType,
  AgentChatUserMessage,
  AgentChatTokenMessage,
  AgentChatCompleteMessage,
  AgentFollowupMessage,
  RobloxAgentRequest,
  RobloxEnvProgressMessage,
  RobloxEnvReadyMessage,
  RobloxEnvErrorMessage,
  FollowupFieldType
} from '../../types/websocket';

interface ChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: {
    missingFields?: FollowupFieldType[];
    questions?: string[];
    spec?: any;
    progress?: number;
    stage?: string;
  };
}

interface RobloxSpec {
  environment_name?: string;
  theme?: string;
  map_type?: 'obby' | 'open_world' | 'dungeon' | 'lab' | 'classroom' | 'puzzle' | 'arena';
  terrain?: string;
  npc_count?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  learning_objectives?: string[];
  age_range?: string;
  assets?: string[];
  scripting?: string[];
  lighting?: string;
  weather?: string;
  notes?: string;
}

const SUGGESTED_PROMPTS = [
  {
    icon: <School />,
    text: "Create a math classroom for grade 5 students",
    category: "education"
  },
  {
    icon: <Terrain />,
    text: "Build a space station for science experiments",
    category: "environment"
  },
  {
    icon: <Quiz />,
    text: "Design a history quiz adventure in ancient Rome",
    category: "quiz"
  },
  {
    icon: <Code />,
    text: "Make an interactive coding playground",
    category: "programming"
  }
];

export const RobloxAIChat: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(state => state.user);
  
  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId] = useState(() => `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [currentSpec, setCurrentSpec] = useState<RobloxSpec>({});
  const [missingFields, setMissingFields] = useState<FollowupFieldType[]>([]);
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [generationStage, setGenerationStage] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedEnvironment, setGeneratedEnvironment] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const streamingMessageRef = useRef<string>('');
  
  // COMPLETELY DISABLED AUTO-SCROLL TO PREVENT PAGE JUMPING
  // const scrollToBottom = useCallback(() => {
  //   const messagesContainer = document.getElementById('chat-messages-container');
  //   if (messagesContainer) {
  //     messagesContainer.scrollTop = messagesContainer.scrollHeight;
  //   }
  // }, []);

  // useEffect(() => {
  //   setTimeout(scrollToBottom, 100);
  // }, [messages, scrollToBottom]);
  
  // Initialize WebSocket connection and subscriptions
  useEffect(() => {
    const initializeChat = async () => {
      try {
        if (!pusherService.isConnected()) {
          await pusherService.connect();
        }
        
        // Subscribe to agent chat events
        const subscriptionId = pusherService.subscribe(
          `agent-chat-${conversationId}`,
          handleWebSocketMessage
        );
        
        // Add welcome message
        addMessage({
          type: 'ai',
          content: "Hello! I'm your AI assistant for creating Roblox educational environments. I'll help you design the perfect world for your students. What kind of learning experience would you like to create?",
        });
        
        return () => {
          pusherService.unsubscribe(subscriptionId);
        };
      } catch (error) {
        console.error('Failed to initialize chat:', error);
        setError('Failed to connect to AI assistant. Please refresh the page.');
      }
    };
    
    initializeChat();
  }, [conversationId]);
  
  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    const { type, payload } = message;
    
    switch (type) {
      case WebSocketMessageType.AGENT_CHAT_TOKEN:
        handleStreamingToken(payload as AgentChatTokenMessage);
        break;
        
      case WebSocketMessageType.AGENT_CHAT_COMPLETE:
        handleStreamingComplete(payload as AgentChatCompleteMessage);
        break;
        
      case WebSocketMessageType.AGENT_FOLLOWUP:
        handleFollowupQuestions(payload as AgentFollowupMessage);
        break;
        
      case WebSocketMessageType.ROBLOX_ENV_PROGRESS:
        handleGenerationProgress(payload as RobloxEnvProgressMessage);
        break;
        
      case WebSocketMessageType.ROBLOX_ENV_READY:
        handleEnvironmentReady(payload as RobloxEnvReadyMessage);
        break;
        
      case WebSocketMessageType.ROBLOX_ENV_ERROR:
        handleGenerationError(payload as RobloxEnvErrorMessage);
        break;
    }
  }, []);
  
  // Handle streaming tokens
  const handleStreamingToken = useCallback((payload: AgentChatTokenMessage) => {
    if (payload.conversationId !== conversationId) return;
    
    streamingMessageRef.current += payload.token;
    
    setMessages(prev => {
      const updated = [...prev];
      const lastMessage = updated[updated.length - 1];
      
      if (lastMessage && lastMessage.isStreaming) {
        lastMessage.content = streamingMessageRef.current;
      } else {
        updated.push({
          id: payload.messageId,
          type: 'ai',
          content: streamingMessageRef.current,
          timestamp: new Date(),
          isStreaming: true
        });
      }
      
      return updated;
    });
  }, [conversationId]);
  
  // Handle streaming complete
  const handleStreamingComplete = useCallback((payload: AgentChatCompleteMessage) => {
    if (payload.conversationId !== conversationId) return;
    
    setMessages(prev => {
      const updated = [...prev];
      const lastMessage = updated[updated.length - 1];
      
      if (lastMessage && lastMessage.isStreaming) {
        lastMessage.content = payload.content;
        lastMessage.isStreaming = false;
      }
      
      return updated;
    });
    
    streamingMessageRef.current = '';
    setIsStreaming(false);
    setIsLoading(false);
  }, [conversationId]);
  
  // Handle followup questions
  const handleFollowupQuestions = useCallback((payload: AgentFollowupMessage) => {
    if (payload.conversationId !== conversationId) return;
    
    setMissingFields(payload.missingFields);
    
    if (payload.questions && payload.questions.length > 0) {
      addMessage({
        type: 'ai',
        content: payload.questions.join('\n\n'),
        metadata: {
          missingFields: payload.missingFields,
          questions: payload.questions
        }
      });
    }
  }, [conversationId]);
  
  // Handle generation progress
  const handleGenerationProgress = useCallback((payload: RobloxEnvProgressMessage) => {
    setGenerationProgress(payload.percentage);
    setGenerationStage(payload.stage);
    
    if (payload.message) {
      addMessage({
        type: 'system',
        content: payload.message,
        metadata: {
          progress: payload.percentage,
          stage: payload.stage
        }
      });
    }
  }, []);
  
  // Handle environment ready
  const handleEnvironmentReady = useCallback((payload: RobloxEnvReadyMessage) => {
    setIsGenerating(false);
    setGeneratedEnvironment(payload);
    
    addMessage({
      type: 'ai',
      content: `🎉 Your Roblox environment is ready! You can now preview, download, or share your creation.`,
    });
  }, []);
  
  // Handle generation error
  const handleGenerationError = useCallback((payload: RobloxEnvErrorMessage) => {
    setIsGenerating(false);
    setError(payload.error);
    
    addMessage({
      type: 'system',
      content: `❌ Generation failed: ${payload.error}`,
    });
  }, []);
  
  // Add message helper
  const addMessage = useCallback((message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }]);
  }, []);
  
  // Send message
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;
    
    // Add user message
    addMessage({
      type: 'user',
      content: content.trim()
    });
    
    setInputValue('');
    setIsLoading(true);
    setIsStreaming(true);
    streamingMessageRef.current = '';
    
    try {
      // Send to AI agent via WebSocket
      await pusherService.send(WebSocketMessageType.AGENT_CHAT_USER, {
        conversationId,
        text: content.trim(),
        context: {
          currentSpec,
          missingFields,
          userId: currentUser?.id,
          userRole: currentUser?.role
        }
      } as AgentChatUserMessage, {
        channel: `agent-chat-${conversationId}`
      });
      
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message. Please try again.');
      setIsLoading(false);
      setIsStreaming(false);
    }
  }, [conversationId, currentSpec, missingFields, currentUser, isLoading, addMessage]);
  
  // Handle input submit
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  }, [inputValue, sendMessage]);
  
  // Handle suggested prompt
  const handleSuggestedPrompt = useCallback((prompt: string) => {
    setInputValue(prompt);
    sendMessage(prompt);
  }, [sendMessage]);
  
  // Generate environment
  const generateEnvironment = useCallback(async () => {
    if (missingFields.length > 0) {
      addMessage({
        type: 'ai',
        content: `I still need some information: ${missingFields.join(', ')}. Please provide these details so I can create your environment.`
      });
      return;
    }
    
    setIsGenerating(true);
    setGenerationProgress(0);
    setGenerationStage('initializing');
    
    try {
      await pusherService.send(WebSocketMessageType.ROBLOX_AGENT_REQUEST, {
        conversationId,
        requestId: `req_${Date.now()}`,
        spec: currentSpec
      } as RobloxAgentRequest, {
        channel: `agent-chat-${conversationId}`
      });
      
      addMessage({
        type: 'system',
        content: '🚀 Starting environment generation...'
      });
      
    } catch (error) {
      console.error('Failed to start generation:', error);
      setError('Failed to start environment generation.');
      setIsGenerating(false);
    }
  }, [conversationId, currentSpec, missingFields, addMessage]);
  
  // Clear conversation
  const clearConversation = useCallback(() => {
    setMessages([]);
    setCurrentSpec({});
    setMissingFields([]);
    setGeneratedEnvironment(null);
    setError(null);
    
    addMessage({
      type: 'ai',
      content: "Hello! I'm ready to help you create a new Roblox educational environment. What would you like to build?"
    });
  }, [addMessage]);
  
  // Voice recording (placeholder)
  const toggleRecording = useCallback(() => {
    setIsRecording(!isRecording);
    // TODO: Implement voice recording functionality
  }, [isRecording]);

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        height: '600px', 
        display: 'flex', 
        flexDirection: 'column',
        bgcolor: theme.palette.background.paper,
        border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
      }}
    >
      {/* Header */}
      <Box sx={{ 
        p: 2, 
        borderBottom: `1px solid ${theme.palette.divider}`,
        bgcolor: alpha(theme.palette.primary.main, 0.05)
      }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
              <AutoAwesome />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight="bold">
                Roblox AI Assistant
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {isStreaming ? 'AI is typing...' : isGenerating ? `Generating (${generationProgress}%)` : 'Ready to help'}
              </Typography>
            </Box>
          </Stack>
          
          <Stack direction="row" spacing={1}>
            <Tooltip title="Clear conversation">
              <IconButton onClick={clearConversation} size="small">
                <Clear />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh connection">
              <IconButton onClick={() => window.location.reload()} size="small">
                <Refresh />
              </IconButton>
            </Tooltip>
          </Stack>
        </Stack>
      </Box>
      
      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          onClose={() => setError(null)}
          sx={{ m: 1 }}
        >
          {error}
        </Alert>
      )}
      
      {/* Messages */}
      <Box
        id="chat-messages-container"
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',  // Ensure relative positioning
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'rgba(0,0,0,0.1)',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(0,188,212,0.5)',
            borderRadius: '4px',
          },
        }}>
        {messages.length === 0 && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Welcome to Roblox AI Assistant! 🎮
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              I'll help you create amazing educational Roblox environments. Try one of these suggestions:
            </Typography>
            
            <Stack spacing={1} sx={{ mt: 2 }}>
              {SUGGESTED_PROMPTS.map((prompt, index) => (
                <Chip
                  key={index}
                  icon={prompt.icon}
                  label={prompt.text}
                  onClick={() => handleSuggestedPrompt(prompt.text)}
                  variant="outlined"
                  sx={{ 
                    justifyContent: 'flex-start',
                    '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.1) }
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}
        
        {messages.map((message) => (
          <Box key={message.id} sx={{ mb: 2 }}>
              <Stack 
                direction="row" 
                spacing={1}
                justifyContent={message.type === 'user' ? 'flex-end' : 'flex-start'}
              >
                {message.type !== 'user' && (
                  <Avatar 
                    sx={{ 
                      width: 32, 
                      height: 32,
                      bgcolor: message.type === 'ai' ? theme.palette.primary.main : theme.palette.grey[500]
                    }}
                  >
                    {message.type === 'ai' ? <AutoAwesome /> : '⚙️'}
                  </Avatar>
                )}
                
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    bgcolor: message.type === 'user' 
                      ? theme.palette.primary.main 
                      : message.type === 'system'
                      ? alpha(theme.palette.warning.main, 0.1)
                      : theme.palette.background.default,
                    color: message.type === 'user' ? theme.palette.primary.contrastText : 'inherit',
                    borderRadius: 2
                  }}
                >
                  <Typography 
                    variant="body2" 
                    sx={{ whiteSpace: 'pre-wrap' }}
                  >
                    {message.content}
                    {message.isStreaming && (
                      <Box component="span" sx={{ ml: 0.5 }}>
                        <CircularProgress size={12} />
                      </Box>
                    )}
                  </Typography>
                  
                  {message.metadata?.progress !== undefined && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {message.metadata.stage}: {message.metadata.progress}%
                      </Typography>
                    </Box>
                  )}
                </Paper>
                
                {message.type === 'user' && (
                  <Avatar sx={{ width: 32, height: 32 }}>
                    {currentUser?.firstName?.[0] || 'U'}
                  </Avatar>
                )}
              </Stack>
            </Box>
        ))}
        
        {/* Generation Progress */}
        {isGenerating && (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <CircularProgress variant="determinate" value={generationProgress} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              {generationStage}: {generationProgress}%
            </Typography>
          </Box>
        )}
        
        {/* Generated Environment Actions */}
        {generatedEnvironment && (
          <Box sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.1), borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              🎉 Environment Ready!
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Button
                size="small"
                startIcon={<Download />}
                onClick={() => window.open(generatedEnvironment.downloadUrl)}
              >
                Download
              </Button>
              <Button
                size="small"
                startIcon={<Share />}
                onClick={() => navigator.share?.({ url: generatedEnvironment.previewUrl })}
              >
                Share
              </Button>
            </Stack>
          </Box>
        )}
        
        {/* Scroll anchor removed to prevent page jumping */}
      </Box>
      
      {/* Input */}
      <Box sx={{ 
        p: 2, 
        borderTop: `1px solid ${theme.palette.divider}`,
        bgcolor: alpha(theme.palette.background.paper, 0.8)
      }}>
        <form onSubmit={handleSubmit}>
          <Stack direction="row" spacing={1} alignItems="flex-end">
            <TextField
              ref={inputRef}
              fullWidth
              multiline
              maxRows={3}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Describe the Roblox environment you'd like to create..."
              disabled={isLoading}
              variant="outlined"
              size="small"
            />
            
            <Tooltip title={isRecording ? "Stop recording" : "Voice input"}>
              <IconButton 
                onClick={toggleRecording}
                color={isRecording ? "error" : "default"}
                disabled={isLoading}
              >
                {isRecording ? <MicOff /> : <Mic />}
              </IconButton>
            </Tooltip>
            
            <Button
              type="submit"
              variant="contained"
              disabled={!inputValue.trim() || isLoading}
              endIcon={<Send />}
            >
              Send
            </Button>
          </Stack>
        </form>
        
        {missingFields.length === 0 && Object.keys(currentSpec).length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Button
              variant="outlined"
              color="success"
              onClick={generateEnvironment}
              disabled={isGenerating}
              startIcon={<AutoAwesome />}
              fullWidth
            >
              Generate Roblox Environment
            </Button>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default RobloxAIChat;