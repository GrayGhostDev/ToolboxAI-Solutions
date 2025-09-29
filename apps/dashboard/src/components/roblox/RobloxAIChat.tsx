/**
 * RobloxAIChat Component
 *
 * Interactive AI chat interface for guiding users through Roblox world creation
 * Provides real-time communication with AI agents to collect parameters and
 * generate personalized educational environments based on templates.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, Paper, Text, TextInput, Button, Badge, Stack, Avatar, ActionIcon, Loader, Alert, Tooltip, Group, useMantineTheme, Textarea, Progress } from '@mantine/core';
import {
  IconSend,
  IconSparkles,
  IconSchool,
  IconMountain,
  IconQuestionMark,
  IconCode,
  IconMicrophone,
  IconMicrophoneOff,
  IconRefresh,
  IconX,
  IconDownload,
  IconShare
} from '@tabler/icons-react';
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
    icon: <IconSchool />,
    text: "Create a math classroom for grade 5 students",
    category: "education"
  },
  {
    icon: <IconMountain />,
    text: "Build a space station for science experiments",
    category: "environment"
  },
  {
    icon: <IconQuestionMark />,
    text: "Design a history quiz adventure in ancient Rome",
    category: "quiz"
  },
  {
    icon: <IconCode />,
    text: "Make an interactive coding playground",
    category: "programming"
  }
];

export const RobloxAIChat: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
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
      shadow="md"
      style={{
        height: '600px',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.colors.gray[0],
        border: `1px solid ${theme.colors.blue[2]}`
      }}
    >
      {/* Header */}
      <Box style={{
        padding: theme.spacing.md,
        borderBottom: `1px solid ${theme.colors.gray[3]}`,
        backgroundColor: theme.colors.blue[0]
      }}>
        <Group position="apart" align="center">
          <Group spacing={theme.spacing.md}>
            <Avatar color="blue">
              <IconSparkles />
            </Avatar>
            <div>
              <Text weight={700} size="lg">
                Roblox AI Assistant
              </Text>
              <Text size="xs" color="dimmed">
                {isStreaming ? 'AI is typing...' : isGenerating ? `Generating (${generationProgress}%)` : 'Ready to help'}
              </Text>
            </div>
          </Group>

          <Group spacing={theme.spacing.xs}>
            <Tooltip label="Clear conversation">
              <ActionIcon onClick={clearConversation} size="sm">
                <IconX />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Refresh connection">
              <ActionIcon onClick={() => window.location.reload()} size="sm">
                <IconRefresh />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert
          color="red"
          onClose={() => setError(null)}
          style={{ margin: theme.spacing.xs }}
          withCloseButton
        >
          {error}
        </Alert>
      )}

      {/* Messages */}
      <Box
        id="chat-messages-container"
        style={{
          flex: 1,
          overflow: 'auto',
          padding: theme.spacing.xs,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative'
        }}
      >
        {messages.length === 0 && (
          <Box style={{ padding: theme.spacing.lg, textAlign: 'center' }}>
            <Text size="xl" weight={600} mb="md">
              Welcome to Roblox AI Assistant! 🎮
            </Text>
            <Text size="sm" color="dimmed" mb="md">
              I'll help you create amazing educational Roblox environments. Try one of these suggestions:
            </Text>

            <Stack spacing={theme.spacing.xs} mt="md">
              {SUGGESTED_PROMPTS.map((prompt, index) => (
                <Badge
                  key={index}
                  leftSection={prompt.icon}
                  variant="outline"
                  size="lg"
                  style={{
                    cursor: 'pointer',
                    justifyContent: 'flex-start',
                    padding: theme.spacing.sm,
                    minHeight: '40px',
                    width: '100%'
                  }}
                  onClick={() => handleSuggestedPrompt(prompt.text)}
                >
                  {prompt.text}
                </Badge>
              ))}
            </Stack>
          </Box>
        )}

        {messages.map((message) => (
          <Box key={message.id} mb="md">
            <Group
              spacing={theme.spacing.xs}
              position={message.type === 'user' ? 'right' : 'left'}
            >
              {message.type !== 'user' && (
                <Avatar
                  size={32}
                  color={message.type === 'ai' ? 'blue' : 'gray'}
                >
                  {message.type === 'ai' ? <IconSparkles /> : '⚙️'}
                </Avatar>
              )}

              <Paper
                shadow="xs"
                style={{
                  padding: theme.spacing.md,
                  maxWidth: '70%',
                  backgroundColor: message.type === 'user'
                    ? theme.colors.blue[6]
                    : message.type === 'system'
                    ? theme.colors.yellow[1]
                    : theme.colors.gray[0],
                  color: message.type === 'user' ? 'white' : 'inherit',
                  borderRadius: theme.radius.md
                }}
              >
                <Text
                  size="sm"
                  style={{ whiteSpace: 'pre-wrap' }}
                >
                  {message.content}
                  {message.isStreaming && (
                    <span style={{ marginLeft: theme.spacing.xs }}>
                      <Loader size={12} />
                    </span>
                  )}
                </Text>

                {message.metadata?.progress !== undefined && (
                  <Box mt="xs">
                    <Text size="xs" color="dimmed">
                      {message.metadata.stage}: {message.metadata.progress}%
                    </Text>
                  </Box>
                )}
              </Paper>

              {message.type === 'user' && (
                <Avatar size={32}>
                  {currentUser?.firstName?.[0] || 'U'}
                </Avatar>
              )}
            </Group>
          </Box>
        ))}

        {/* Generation Progress */}
        {isGenerating && (
          <Box style={{ padding: theme.spacing.md, textAlign: 'center' }}>
            <Progress value={generationProgress} animated />
            <Text size="sm" mt="xs">
              {generationStage}: {generationProgress}%
            </Text>
          </Box>
        )}

        {/* Generated Environment Actions */}
        {generatedEnvironment && (
          <Box style={{
            padding: theme.spacing.md,
            backgroundColor: theme.colors.green[1],
            borderRadius: theme.radius.sm
          }}>
            <Text weight={600} mb="xs">
              🎉 Environment Ready!
            </Text>
            <Group spacing={theme.spacing.xs} mt="xs">
              <Button
                size="xs"
                leftIcon={<IconDownload />}
                onClick={() => window.open(generatedEnvironment.downloadUrl)}
              >
                Download
              </Button>
              <Button
                size="xs"
                leftIcon={<IconShare />}
                onClick={() => navigator.share?.({ url: generatedEnvironment.previewUrl })}
              >
                Share
              </Button>
            </Group>
          </Box>
        )}

        {/* Scroll anchor removed to prevent page jumping */}
      </Box>

      {/* Input */}
      <Box style={{
        padding: theme.spacing.md,
        borderTop: `1px solid ${theme.colors.gray[3]}`,
        backgroundColor: theme.colors.gray[0]
      }}>
        <form onSubmit={handleSubmit}>
          <Group spacing={theme.spacing.xs} align="end">
            <Textarea
              ref={inputRef}
              style={{ flex: 1 }}
              maxRows={3}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Describe the Roblox environment you'd like to create..."
              disabled={isLoading}
              size="sm"
            />

            <Tooltip label={isRecording ? "Stop recording" : "Voice input"}>
              <ActionIcon
                onClick={toggleRecording}
                color={isRecording ? "red" : "gray"}
                disabled={isLoading}
              >
                {isRecording ? <IconMicrophoneOff /> : <IconMicrophone />}
              </ActionIcon>
            </Tooltip>

            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              rightIcon={<IconSend />}
            >
              Send
            </Button>
          </Group>
        </form>

        {missingFields.length === 0 && Object.keys(currentSpec).length > 0 && (
          <Box mt="xs">
            <Button
              variant="outline"
              color="green"
              onClick={generateEnvironment}
              disabled={isGenerating}
              leftIcon={<IconSparkles />}
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