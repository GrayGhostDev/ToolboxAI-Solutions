/**
 * RobloxAIChat Component
 *
 * AI-powered chat interface for creating Roblox educational environments.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Text,
  TextInput,
  Button,
  Stack,
  Group,
  Avatar,
  Badge,
  Loader,
  Alert,
  ScrollArea,
} from '@mantine/core';
import {
  IconSend,
  IconSparkles,
  IconRobot,
  IconUser,
  IconAlertCircle,
} from '@tabler/icons-react';
import { api } from '../../services/api';
import { useAppSelector } from '../../store';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export const RobloxAIChat: React.FC = () => {
  const currentUser = useAppSelector(state => state.user);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello ${currentUser.firstName || currentUser.displayName}! I'm your AI assistant for creating Roblox educational environments.

I can help you create immersive 3D learning experiences. To get started, tell me:

• What subject or topic do you want to teach?
• What grade level are your students?
• What learning objectives do you have in mind?
• What kind of environment or theme would work best?

Example: "Create a physics lab for 8th graders to learn Newton's laws of motion in a space station."`,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({ top: scrollAreaRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/roblox/ai/chat', {
        message: userMessage.content,
        context: {
          user_id: currentUser.id,
          role: currentUser.role,
          previous_messages: messages.slice(-5).map(m => ({ role: m.role, content: m.content })),
        },
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message || response.response || 'I understand! Creating your environment...',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (response.environment_id || response.task_id) {
        setTimeout(() => {
          setMessages(prev => [...prev, {
            id: (Date.now() + 2).toString(),
            role: 'assistant',
            content: '🎉 Environment generation started! Check the "Manage" tab for progress.',
            timestamp: new Date(),
          }]);
        }, 1500);
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'AI service unavailable';
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${errorMsg}. The AI chat endpoint may not be configured yet. Try the "Documentation" tab for manual creation guidance.`,
        timestamp: new Date(),
      }]);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper p="md" withBorder style={{ borderBottom: '2px solid var(--mantine-color-blue-6)' }}>
        <Group gap="sm">
          <Avatar color="violet" radius="xl"><IconRobot size={20} /></Avatar>
          <div>
            <Text fw={600} size="sm">Roblox Environment AI</Text>
            <Group gap={4}>
              <Badge size="xs" color="green" variant="dot">Online</Badge>
              <Text size="xs" c="dimmed">Powered by GPT-4</Text>
            </Group>
          </div>
        </Group>
      </Paper>

      {error && (
        <Alert color="red" icon={<IconAlertCircle size={16} />} title="Connection Issue" onClose={() => setError(null)} withCloseButton m="md">
          {error}. Backend endpoint may not be configured. Explore UI and check Documentation tab.
        </Alert>
      )}

      <ScrollArea style={{ flex: 1, padding: '1rem' }} viewportRef={scrollAreaRef}>
        <Stack gap="md">
          {messages.map((message) => (
            <Group key={message.id} gap="sm" align="flex-start" justify={message.role === 'user' ? 'flex-end' : 'flex-start'}>
              {message.role === 'assistant' && <Avatar color="violet" size="sm" radius="xl"><IconRobot size={14} /></Avatar>}
              <Paper p="sm" radius="md" withBorder style={{ maxWidth: '70%', background: message.role === 'user' ? 'linear-gradient(135deg, rgba(6, 147, 227, 0.1), rgba(155, 81, 224, 0.1))' : 'rgba(255, 255, 255, 0.05)' }}>
                <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>{message.content}</Text>
                <Text size="xs" c="dimmed" mt="xs">{message.timestamp.toLocaleTimeString()}</Text>
              </Paper>
              {message.role === 'user' && <Avatar color="blue" size="sm" radius="xl"><IconUser size={14} /></Avatar>}
            </Group>
          ))}
          {isLoading && (
            <Group gap="sm" align="flex-start">
              <Avatar color="violet" size="sm" radius="xl"><IconRobot size={14} /></Avatar>
              <Paper p="sm" radius="md" withBorder>
                <Group gap="xs"><Loader size="xs" /><Text size="sm" c="dimmed">AI is thinking...</Text></Group>
              </Paper>
            </Group>
          )}
        </Stack>
      </ScrollArea>

      <Paper p="md" withBorder style={{ borderTop: '2px solid var(--mantine-color-blue-6)' }}>
        <Group gap="sm" align="flex-end">
          <TextInput
            placeholder="Describe the educational environment you want to create..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
            disabled={isLoading}
            style={{ flex: 1 }}
            leftSection={<IconSparkles size={16} />}
          />
          <Button onClick={handleSendMessage} loading={isLoading} disabled={!inputValue.trim()} leftSection={<IconSend size={16} />} variant="gradient" gradient={{ from: 'blue', to: 'violet' }}>
            Send
          </Button>
        </Group>
        <Text size="xs" c="dimmed" mt="xs">Press Enter to send, Shift+Enter for new line</Text>
      </Paper>
    </Box>
  );
};

export default RobloxAIChat;
