import {
  Box,
  Button,
  Text,
  Paper,
  Stack,
  Grid,
  Container,
  ActionIcon,
  Avatar,
  Card,
  Group,
  TextInput,
  Chip,
  Badge,
  Alert,
  Loader,
  Progress,
  Modal,
  Title,
  Divider,
  Drawer,
  Tabs,
  Menu,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Autocomplete,
  Skeleton,
  Table,
  rem
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconStar,
  IconTrash,
  IconSearch,
  IconInbox,
  IconMail,
  IconSend,
  IconEdit,
  IconRefresh,
  IconPaperclip,
  IconReply,
  IconArrowForward
} from '@tabler/icons-react';
import * as React from 'react';
import { useEffect, useState, memo } from 'react';
import { useAppDispatch } from '../../store';
import VirtualizedList from '../common/VirtualizedList';
import { useOptimizedMemo, useOptimizedCallback, useDebouncedCallback, useRenderPerformance } from '../../hooks/usePerformance';
interface Message {
  id: string;
  subject: string;
  sender: string;
  senderAvatar?: string;
  timestamp: Date;
  preview: string;
  isRead: boolean;
  isStarred: boolean;
  priority: 'high' | 'normal' | 'low';
  hasAttachment: boolean;
  threadCount: number;
}
interface Conversation {
  id: string;
  messages: Message[];
  participants: string[];
  lastActivity: Date;
}
// Memoized message item component for virtual scrolling
const MessageItem = memo<{
  message: Message;
  onMessageClick: (message: Message) => void;
  onStarToggle: (messageId: string) => void;
  onDelete: (messageId: string) => void;
}>(({ message, onMessageClick, onStarToggle, onDelete }) => {
  const handleClick = useOptimizedCallback(() => {
    onMessageClick(message);
  }, [onMessageClick, message], 'MessageItem:handleClick');
  const handleStarToggle = useOptimizedCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onStarToggle(message.id);
  }, [onStarToggle, message.id], 'MessageItem:handleStarToggle');
  const handleDelete = useOptimizedCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(message.id);
  }, [onDelete, message.id], 'MessageItem:handleDelete');
  const formattedTime = useOptimizedMemo(() => {
    return message.timestamp.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  }, [message.timestamp], 'MessageItem:formattedTime');
  const priorityColor = useOptimizedMemo(() => {
    switch (message.priority) {
      case 'high': return 'error';
      case 'low': return 'info';
      default: return 'default';
    }
  }, [message.priority], 'MessageItem:priorityColor');
  return (
    <Paper
      shadow={message.isRead ? 'xs' : 'sm'}
      p="md"
      style={{
        margin: 1,
        height: 120, // Fixed height for virtual scrolling
        cursor: 'pointer',
        backgroundColor: message.isRead ? 'var(--mantine-color-gray-0)' : 'var(--mantine-color-blue-0)',
      }}
      onClick={handleClick}
    >
      <Group h="100%" align="center" spacing="md">
        <Avatar
          src={message.senderAvatar}
          size={40}
          radius="sm"
        >
          {message.sender.charAt(0).toUpperCase()}
        </Avatar>
        <Box style={{ flex: 1, minWidth: 0 }}>
          <Group justify="space-between" align="center" mb="xs">
            <Text
              size="sm"
              fw={message.isRead ? 400 : 700}
              truncate
            >
              {message.sender}
            </Text>
            <Group align="center" spacing={4}>
              <Text size="xs" c="dimmed">
                {formattedTime}
              </Text>
              <ActionIcon
                size="sm"
                variant="subtle"
                onClick={handleStarToggle}
                color={message.isStarred ? 'yellow' : 'gray'}
              >
                <IconStar size={14} />
              </ActionIcon>
              <ActionIcon size="sm" variant="subtle" onClick={handleDelete} color="red">
                <IconTrash size={14} />
              </ActionIcon>
            </Group>
          </Group>
          <Text
            size="sm"
            fw={message.isRead ? 400 : 600}
            truncate
            mb="xs"
          >
            {message.subject}
          </Text>
          <Group justify="space-between" align="center">
            <Text
              size="sm"
              c="dimmed"
              truncate
              style={{ flex: 1, marginRight: rem(8) }}
            >
              {message.preview}
            </Text>
            <Group spacing={4}>
              {message.priority !== 'normal' && (
                <Chip
                  size="xs"
                  variant="outline"
                  color={priorityColor as any}
                >
                  {message.priority}
                </Chip>
              )}
              {message.hasAttachment && (
                <IconPaperclip size={14} color="var(--mantine-color-gray-5)" />
              )}
              {message.threadCount > 1 && (
                <Chip
                  size="xs"
                  variant="outline"
                >
                  {message.threadCount}
                </Chip>
              )}
            </Group>
          </Group>
        </Box>
      </Group>
    </Paper>
  );
});
MessageItem.displayName = 'MessageItem';
// Memoized message filters component
const MessageFilters = memo<{
  searchTerm: string;
  onSearchChange: (value: string) => void;
  filterType: string;
  onFilterChange: (type: string) => void;
  onCompose: () => void;
  onRefresh: () => void;
  loading?: boolean;
}>(({ searchTerm, onSearchChange, filterType, onFilterChange, onCompose, onRefresh, loading }) => {
  const handleSearchChange = useDebouncedCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    onSearchChange(event.target.value);
  }, 300, [onSearchChange]);
  const filterOptions = useOptimizedMemo(() => [
    { value: 'all', label: 'All Messages', icon: <IconInbox size={16} /> },
    { value: 'unread', label: 'Unread', icon: <IconMail size={16} /> },
    { value: 'starred', label: 'Starred', icon: <IconStar size={16} /> },
    { value: 'sent', label: 'Sent', icon: <IconSend size={16} /> },
  ], [], 'MessageFilters:filterOptions');
  return (
    <Group mb="lg" wrap="wrap">
      <TextInput
        placeholder="Search messages..."
        defaultValue={searchTerm}
        onChange={handleSearchChange}
        size="sm"
        style={{ minWidth: 300, flex: 1 }}
        leftSection={<IconSearch size={16} />}
      />
      <Group spacing="xs">
        {filterOptions.map((option) => (
          <Button
            key={option.value}
            variant={filterType === option.value ? 'filled' : 'outline'}
            leftSection={option.icon}
            onClick={() => onFilterChange(option.value)}
            size="sm"
          >
            {option.label}
          </Button>
        ))}
      </Group>
      <Group spacing="xs">
        <Button
          variant="filled"
          leftSection={<IconEdit size={16} />}
          onClick={onCompose}
        >
          Compose
        </Button>
        <ActionIcon variant="subtle" onClick={onRefresh} loading={loading}>
          <IconRefresh size={16} />
        </ActionIcon>
      </Group>
    </Group>
  );
});
MessageFilters.displayName = 'MessageFilters';
export default function MessagesOptimized() {
  // Performance tracking
  useRenderPerformance('MessagesOptimized');
  const dispatch = useAppDispatch();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [composeOpen, setComposeOpen] = useState(false);
  // Memoized filtered and sorted messages
  const filteredMessages = useOptimizedMemo(() => {
    let filtered = messages;
    // Apply search filter
    if (searchTerm) {
      const lowercaseSearch = searchTerm.toLowerCase();
      filtered = filtered.filter(message =>
        message.subject.toLowerCase().includes(lowercaseSearch) ||
        message.sender.toLowerCase().includes(lowercaseSearch) ||
        message.preview.toLowerCase().includes(lowercaseSearch)
      );
    }
    // Apply type filter
    switch (filterType) {
      case 'unread':
        filtered = filtered.filter(m => !m.isRead);
        break;
      case 'starred':
        filtered = filtered.filter(m => m.isStarred);
        break;
      case 'sent':
        // This would filter sent messages if we had that data
        break;
    }
    // Sort by timestamp (newest first)
    return filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }, [messages, searchTerm, filterType], 'MessagesOptimized:filteredMessages');
  // Optimized event handlers
  const handleMessageClick = useOptimizedCallback((message: Message) => {
    setSelectedMessage(message);
    // Mark as read
    if (!message.isRead) {
      setMessages(prev => prev.map(m =>
        m.id === message.id ? { ...m, isRead: true } : m
      ));
    }
  }, [], 'MessagesOptimized:handleMessageClick');
  const handleStarToggle = useOptimizedCallback((messageId: string) => {
    setMessages(prev => prev.map(m =>
      m.id === messageId ? { ...m, isStarred: !m.isStarred } : m
    ));
  }, [], 'MessagesOptimized:handleStarToggle');
  const handleDelete = useOptimizedCallback((messageId: string) => {
    setMessages(prev => prev.filter(m => m.id !== messageId));
  }, [], 'MessagesOptimized:handleDelete');
  const handleCompose = useOptimizedCallback(() => {
    setComposeOpen(true);
  }, [], 'MessagesOptimized:handleCompose');
  const handleRefresh = useOptimizedCallback(async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In real app, would fetch from API
      generateMockMessages();
    } finally {
      setLoading(false);
    }
  }, [], 'MessagesOptimized:handleRefresh');
  // Mock data generation for demo
  const generateMockMessages = useOptimizedCallback(() => {
    const mockMessages: Message[] = Array.from({ length: 100 }, (_, i) => ({
      id: `msg-${i}`,
      subject: `Message Subject ${i + 1}`,
      sender: `User ${Math.floor(Math.random() * 20) + 1}`,
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      preview: `This is the preview text for message ${i + 1}. It shows the beginning of the message content...`,
      isRead: Math.random() > 0.3,
      isStarred: Math.random() > 0.8,
      priority: ['high', 'normal', 'low'][Math.floor(Math.random() * 3)] as any,
      hasAttachment: Math.random() > 0.7,
      threadCount: Math.floor(Math.random() * 5) + 1,
    }));
    setMessages(mockMessages);
  }, [], 'MessagesOptimized:generateMockMessages');
  useEffect(() => {
    generateMockMessages();
  }, [generateMockMessages]);
  // Render function for virtual list
  const renderMessageItem = useOptimizedCallback((message: Message) => (
    <MessageItem
      key={message.id}
      message={message}
      onMessageClick={handleMessageClick}
      onStarToggle={handleStarToggle}
      onDelete={handleDelete}
    />
  ), [handleMessageClick, handleStarToggle, handleDelete], 'MessagesOptimized:renderMessageItem');
  return (
    <Container size="xl">
      <Title order={4} mb="lg">
        Messages
      </Title>
      <MessageFilters
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        filterType={filterType}
        onFilterChange={setFilterType}
        onCompose={handleCompose}
        onRefresh={handleRefresh}
        loading={loading}
      />
      {loading && filteredMessages.length === 0 ? (
        <Group justify="center" align="center" style={{ height: 400 }}>
          <Loader size="lg" />
        </Group>
      ) : filteredMessages.length === 0 ? (
        <Group justify="center" align="center" style={{ height: 400 }}>
          <Text c="dimmed">
            {searchTerm ? 'No messages match your search.' : 'No messages found.'}
          </Text>
        </Group>
      ) : (
        /* Use virtual scrolling for large message lists */
        <VirtualizedList
          items={filteredMessages}
          itemHeight={140} // Includes margins
          height={600}
          renderItem={renderMessageItem}
          overscanCount={10}
        />
      )}
      {/* Message Detail Modal */}
      <Modal
        opened={!!selectedMessage}
        onClose={() => setSelectedMessage(null)}
        size="lg"
        title={
          selectedMessage && (
            <Group justify="space-between" align="center">
              <Title order={6}>{selectedMessage.subject}</Title>
              <Group spacing="xs">
                <ActionIcon
                  variant="subtle"
                  onClick={() => handleStarToggle(selectedMessage.id)}
                  color={selectedMessage.isStarred ? 'yellow' : 'gray'}
                >
                  <IconStar size={16} />
                </ActionIcon>
                <ActionIcon variant="subtle">
                  <IconReply size={16} />
                </ActionIcon>
                <ActionIcon variant="subtle">
                  <IconArrowForward size={16} />
                </ActionIcon>
              </Group>
            </Group>
          )
        }
      >
        {selectedMessage && (
          <>
            <Box mb="md">
              <Text size="sm" c="dimmed">
                From: {selectedMessage.sender}
              </Text>
              <Text size="xs" c="dimmed">
                {selectedMessage.timestamp.toLocaleString()}
              </Text>
            </Box>
            <Text size="md">
              {selectedMessage.preview}
              {/* In real app, would show full message content */}
            </Text>
            <Group justify="flex-end" mt="xl">
              <Button variant="subtle" onClick={() => setSelectedMessage(null)}>
                Close
              </Button>
              <Button variant="filled" leftSection={<IconReply size={16} />}>
                Reply
              </Button>
            </Group>
          </>
        )}
      </Modal>
      {/* Compose Modal */}
      <Modal
        opened={composeOpen}
        onClose={() => setComposeOpen(false)}
        size="lg"
        title="Compose Message"
      >
        <Stack spacing="md">
          <TextInput
            label="To"
            placeholder="Enter recipient..."
          />
          <TextInput
            label="Subject"
            placeholder="Enter subject..."
          />
          <TextInput
            label="Message"
            placeholder="Type your message..."
            minRows={6}
            autosize
          />
          <Group justify="flex-end" mt="xl">
            <Button variant="subtle" onClick={() => setComposeOpen(false)}>
              Cancel
            </Button>
            <Button variant="filled" leftSection={<IconSend size={16} />}>
              Send
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
