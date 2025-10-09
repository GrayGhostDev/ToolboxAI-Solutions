import * as React from 'react';
import {
  Card,
  Text,
  Button,
  Stack,
  Avatar,
  Badge,
  ActionIcon,
  Box,
  Divider,
  Paper,
  Loader,
  Alert,
  Modal,
  TextInput,
  Textarea,
  MultiSelect,
  Grid,
  Group,
  NavLink
} from '@mantine/core';

import { useEffect, useState } from 'react';
import {
  IconSend,
  IconPaperclip,
  IconSearch,
  IconStar,
  IconTrash,
  IconArchive,
  IconArrowBackUp,
  IconArrowForwardUp,
  IconCheck,
  IconChecks,
  IconEdit,
  IconRefresh,
  IconInbox,
  IconSend2,
  IconMail
} from '@tabler/icons-react';
import { useAppSelector, useAppDispatch } from '../../store';
import {
  fetchMessages,
  sendMessage,
  replyToMessage,
  markAsRead,
  moveToFolder,
  deleteMessage,
  searchMessages,
  getUnreadCount,
  setFilters,
  setCurrentMessage,
  openCompose,
  closeCompose,
  updateCompose,
  clearError,
} from '../../store/slices/messagesSlice';
import type { Message } from '../../types/api';

// Using Message type from types/api.ts
// Additional local interfaces for UI state
interface Conversation {
  id: string;
  participants: Array<{
    name: string;
    avatar?: string;
    online?: boolean;
  }>;
  lastMessage: string;
  timestamp: string;
  unread: number;
  type: 'individual' | 'group' | 'announcement';
}

export default function Messages() {
  const dispatch = useAppDispatch();
  const {
    messages,
    currentMessage,
    folders,
    unreadCount,
    loading,
    sending,
    error,
    filters,
    compose
  } = useAppSelector((s) => s.messages);

  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [replyText, setReplyText] = useState('');
  const [showComposeDialog, setShowComposeDialog] = useState(false);
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([]);

  useEffect(() => {
    // Fetch initial messages
    dispatch(fetchMessages({ folder: filters.folder }));
    dispatch(getUnreadCount());
  }, [dispatch, filters.folder]);

  useEffect(() => {
    // Auto-refresh messages every 30 seconds
    const interval = setInterval(() => {
      dispatch(fetchMessages({ folder: filters.folder }));
      dispatch(getUnreadCount());
    }, 30000);
    return () => clearInterval(interval);
  }, [dispatch, filters.folder]);

  // Group messages by sender to create conversations
  const conversations: Conversation[] = React.useMemo(() => {
    const convMap = new Map<string, Conversation>();

    messages.forEach((msg) => {
      const senderId = msg.fromUserId;
      if (!convMap.has(senderId)) {
        convMap.set(senderId, {
          id: `conv-${senderId}`, // Make ID unique with prefix
          participants: [{
            name: msg.fromUserId, // In real app, would fetch user details
            avatar: undefined,
            online: false,
          }],
          lastMessage: msg.subject,
          timestamp: msg.sentAt,
          unread: msg.read ? 0 : 1,
          type: 'individual',
        });
      } else {
        const conv = convMap.get(senderId)!;
        if (!msg.read) conv.unread++;
        // Update last message if this is newer
        if (new Date(msg.sentAt) > new Date(conv.timestamp)) {
          conv.lastMessage = msg.subject;
          conv.timestamp = msg.sentAt;
        }
      }
    });

    return Array.from(convMap.values()).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [messages]);

  const handleTabChange = (tab: typeof filters.folder) => {
    dispatch(setFilters({ folder: tab }));
    dispatch(fetchMessages({ folder: tab }));
  };

  const handleMessageSelect = async (message: Message) => {
    dispatch(setCurrentMessage(message));
    if (!message.read) {
      dispatch(markAsRead(message.id));
    }
  };

  const handleRefresh = () => {
    dispatch(fetchMessages({ folder: filters.folder }));
    dispatch(getUnreadCount());
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    if (term.length > 2) {
      dispatch(searchMessages(term));
    } else if (term.length === 0) {
      dispatch(fetchMessages({ folder: filters.folder }));
    }
  };

  const filteredMessages = React.useMemo(() => {
    let filtered = messages;

    // Apply search filter locally
    if (searchTerm) {
      filtered = filtered.filter(
        (msg) =>
          msg.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
          msg.content.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  }, [messages, searchTerm]);

  const handleSendReply = async () => {
    if (replyText.trim() && currentMessage) {
      await dispatch(replyToMessage({
        messageId: currentMessage.id,
        content: replyText
      }));
      setReplyText('');
    }
  };

  const handleComposeSubmit = async () => {
    if (compose.subject && compose.content && selectedRecipients.length > 0) {
      await dispatch(sendMessage({
        toUserId: selectedRecipients[0], // API currently supports single recipient
        subject: compose.subject,
        content: compose.content,
        attachments: compose.attachments,
      }));
      setShowComposeDialog(false);
      dispatch(closeCompose());
      setSelectedRecipients([]);
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    await dispatch(deleteMessage(messageId));
    if (currentMessage?.id === messageId) {
      dispatch(setCurrentMessage(null));
    }
  };

  const handleArchiveMessage = async (messageId: string) => {
    await dispatch(moveToFolder({ messageId, folder: 'archived' }));
  };

  const handleStarMessage = async (messageId: string) => {
    await dispatch(moveToFolder({ messageId, folder: 'starred' }));
  };

  const getStatusIcon = (message: Message) => {
    if (message.read && message.readAt) {
      return <IconChecks size={16} style={{ color: 'var(--mantine-color-blue-6)' }} />;
    }
    if (message.sentAt) {
      return <IconCheck size={16} style={{ color: 'var(--mantine-color-gray-6)' }} />;
    }
    return null;
  };

  const getFolderIcon = (folder: string) => {
    switch (folder) {
      case 'inbox': return <IconInbox size={16} />;
      case 'sent': return <IconSend2 size={16} />;
      case 'drafts': return <IconMail size={16} />;
      case 'archived': return <IconArchive size={16} />;
      case 'starred': return <IconStar size={16} />;
      default: return <IconInbox size={16} />;
    }
  };

  if (loading && messages.length === 0) {
    return (
      <Box style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Loader />
      </Box>
    );
  }

  return (
    <Grid gutter="md" style={{ height: 'calc(100vh - 200px)' }}>
      {/* Conversations List */}
      <Grid.Col span={{ base: 12, md: 3 }}>
        <Card style={{ height: '100%' }}>
          <Stack style={{ height: '100%' }}>
            {/* Search */}
            <Box p="md">
              <TextInput
                placeholder="Search messages..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                leftSection={<IconSearch size={16} />}
              />
            </Box>

            {/* Tabs */}
            <Group gap="xs" px="md" pb="sm" style={{ flexWrap: 'wrap' }}>
              {(['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'] as const).map((tab) => (
                <Button
                  key={tab}
                  size="compact-sm"
                  variant={filters.folder === tab ? 'filled' : 'outline'}
                  leftSection={getFolderIcon(tab)}
                  onClick={() => handleTabChange(tab)}
                  rightSection={
                    tab === 'inbox' && unreadCount > 0 ? (
                      <Badge size="sm" color="red">{unreadCount}</Badge>
                    ) : null
                  }
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </Button>
              ))}
            </Group>

            <Divider />

            {/* Conversations */}
            <Stack style={{ flex: 1, overflow: 'auto' }} gap={0}>
              {conversations.map((conversation) => (
                <Box
                  key={conversation.id}
                  p="md"
                  style={{
                    cursor: 'pointer',
                    backgroundColor: selectedConversation?.id === conversation.id ?
                      'var(--mantine-color-blue-0)' : 'transparent'
                  }}
                  onClick={() => setSelectedConversation(conversation)}
                >
                  <Group align="flex-start" gap="md">
                    <Badge
                      size="sm"
                      color="red"
                      offset={8}
                      disabled={conversation.unread === 0}
                    >
                      <Avatar src={conversation.participants[0]?.avatar} size="md">
                        {conversation.participants[0]?.name?.[0] || '?'}
                      </Avatar>
                    </Badge>
                    <Stack gap="xs" style={{ flex: 1 }}>
                      <Group justify="space-between" align="center">
                        <Text size="sm" fw={conversation.unread > 0 ? 600 : 400}>
                          {conversation.participants[0]?.name}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {conversation.timestamp}
                        </Text>
                      </Group>
                      <Text
                        size="xs"
                        c="dimmed"
                        style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                        fw={conversation.unread > 0 ? 600 : 400}
                      >
                        {conversation.lastMessage}
                      </Text>
                    </Stack>
                  </Group>
                </Box>
              ))}
            </Stack>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Messages List */}
      <Grid.Col span={{ base: 12, md: 4 }}>
        <Card style={{ height: '100%' }}>
          <Stack style={{ height: '100%' }}>
            {/* Header */}
            <Group justify="space-between" align="center" p="md">
              <Group align="center" gap="xs">
                <Text size="lg" fw={600}>
                  {filters.folder.charAt(0).toUpperCase() + filters.folder.slice(1)}
                </Text>
                <Badge size="sm">{messages.length} messages</Badge>
              </Group>
              <Group gap="xs">
                <ActionIcon size="sm" onClick={handleRefresh} disabled={loading}>
                  <IconRefresh size={16} />
                </ActionIcon>
                <Button
                  leftSection={<IconEdit size={16} />}
                  size="sm"
                  onClick={() => {
                    dispatch(openCompose({}));
                    setShowComposeDialog(true);
                  }}
                >
                  Compose
                </Button>
              </Group>
            </Group>

            <Divider />

            {/* Messages */}
            {error && (
              <Alert
                color="red"
                onClose={() => dispatch(clearError())}
                style={{ margin: '0 16px 16px 16px' }}
                withCloseButton
              >
                {error}
              </Alert>
            )}
            <Stack style={{ flex: 1, overflow: 'auto' }} gap={0}>
              {filteredMessages.length === 0 ? (
                <Box p="xl" ta="center">
                  <Text c="dimmed">
                    {searchTerm ? 'No messages found matching your search' : 'No messages in this folder'}
                  </Text>
                </Box>
              ) : (
                filteredMessages.map((message) => (
                  <Box
                    key={message.id}
                    p="md"
                    style={{
                      cursor: 'pointer',
                      backgroundColor: currentMessage?.id === message.id ?
                        'var(--mantine-color-blue-0)' : !message.read ?
                        'var(--mantine-color-gray-0)' : 'transparent'
                    }}
                    onClick={() => handleMessageSelect(message)}
                  >
                    <Group align="flex-start" gap="md">
                      <Avatar>
                        {message.fromUserId?.charAt(0)?.toUpperCase() || '?'}
                      </Avatar>
                      <Stack gap="xs" style={{ flex: 1 }}>
                        <Group justify="space-between" align="flex-start">
                          <Box style={{ flex: 1 }}>
                            <Group align="center" gap="xs">
                              <Text size="sm" fw={!message.read ? 600 : 400}>
                                {message.fromUserId}
                              </Text>
                              {(message.attachments?.length ?? 0) > 0 && (
                                <Badge
                                  leftSection={<IconPaperclip size={12} />}
                                  size="sm"
                                  variant="light"
                                >
                                  {message.attachments?.length || 0}
                                </Badge>
                              )}
                            </Group>
                            <Text size="sm" fw={!message.read ? 600 : 500}>
                              {message.subject}
                            </Text>
                          </Box>
                          <Stack align="flex-end" gap="xs">
                            <Text size="xs" c="dimmed">
                              {new Date(message.sentAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </Text>
                            {getStatusIcon(message)}
                          </Stack>
                        </Group>
                        <Text
                          size="xs"
                          c="dimmed"
                          style={{
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {message.content ? `${message.content.substring(0, 100)}...` : 'No content'}
                        </Text>
                      </Stack>
                    </Group>
                  </Box>
                ))
              )}
            </Stack>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Message Content */}
      <Grid.Col span={{ base: 12, md: 5 }}>
        <Card style={{ height: '100%' }}>
          <Stack style={{ height: '100%' }}>
            {currentMessage ? (
              <>
                {/* Message Header */}
                <Group
                  justify="space-between"
                  align="center"
                  p="md"
                >
                  <Group align="center" gap="md">
                    <Avatar>
                      {currentMessage.fromUserId[0]?.toUpperCase()}
                    </Avatar>
                    <Box>
                      <Text size="lg" fw={600}>
                        {currentMessage.subject}
                      </Text>
                      <Group align="center" gap="xs">
                        <Text size="xs" c="dimmed">
                          From: {currentMessage.fromUserId}
                        </Text>
                        <Text size="xs" c="dimmed">
                          To: {currentMessage.toUserId}
                        </Text>
                      </Group>
                    </Box>
                  </Group>
                  <Group gap="xs">
                    <ActionIcon
                      size="sm"
                      onClick={() => handleStarMessage(currentMessage.id)}
                    >
                      <IconStar size={16} />
                    </ActionIcon>
                    <ActionIcon
                      size="sm"
                      onClick={() => setReplyText(`\n\n---\nReplying to: ${currentMessage.subject}`)}
                    >
                      <IconArrowBackUp size={16} />
                    </ActionIcon>
                    <ActionIcon
                      size="sm"
                      onClick={() => {
                        dispatch(openCompose({
                          subject: `Fwd: ${currentMessage.subject}`,
                          content: `\n\n--- Forwarded message ---\n${currentMessage.content}`
                        }));
                        setShowComposeDialog(true);
                      }}
                    >
                      <IconArrowForwardUp size={16} />
                    </ActionIcon>
                    <ActionIcon
                      size="sm"
                      onClick={() => handleArchiveMessage(currentMessage.id)}
                    >
                      <IconArchive size={16} />
                    </ActionIcon>
                    <ActionIcon
                      size="sm"
                      onClick={() => handleDeleteMessage(currentMessage.id)}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                </Group>

                <Divider />

                {/* Message Content */}
                <Box style={{ flex: 1, padding: 24, overflow: 'auto' }}>
                  <Text size="xs" c="dimmed" mb="md">
                    {new Date(currentMessage.sentAt).toLocaleString()}
                    {currentMessage.readAt && (
                      <span> • Read at {new Date(currentMessage.readAt).toLocaleString()}</span>
                    )}
                  </Text>
                  <Text style={{ whiteSpace: 'pre-wrap' }}>
                    {currentMessage.content}
                  </Text>
                  {currentMessage.attachments && currentMessage.attachments.length > 0 && (
                    <Group gap="xs" mt="md" style={{ flexWrap: 'wrap' }}>
                      {currentMessage.attachments.map((attachment, idx) => (
                        <Paper key={idx} p="sm" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <IconPaperclip size={16} />
                          <Text size="xs">
                            {attachment.split('/').pop() || `Attachment ${idx + 1}`}
                          </Text>
                        </Paper>
                      ))}
                    </Group>
                  )}
                </Box>

                <Divider />

                {/* Reply Box */}
                <Box p="md">
                  <Group align="flex-start" gap="xs">
                    <Textarea
                      placeholder="Type your reply..."
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          handleSendReply();
                        }
                      }}
                      disabled={sending}
                      rows={3}
                      style={{ flex: 1 }}
                    />
                    <Stack gap="xs">
                      <ActionIcon color="blue" disabled={sending}>
                        <IconPaperclip size={16} />
                      </ActionIcon>
                      <Button
                        onClick={handleSendReply}
                        disabled={!replyText.trim() || sending}
                        loading={sending}
                      >
                        <IconSend size={16} />
                      </Button>
                    </Stack>
                  </Group>
                  <Text size="xs" c="dimmed" mt="xs">
                    Press Ctrl+Enter to send
                  </Text>
                </Box>
              </>
            ) : (
              <Box
                style={{
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Text c="dimmed">
                  Select a message to view
                </Text>
              </Box>
            )}
          </Stack>
        </Card>
      </Grid.Col>

      {/* Compose Dialog */}
      <Modal
        opened={showComposeDialog}
        onClose={() => {
          setShowComposeDialog(false);
          dispatch(closeCompose());
        }}
        title="Compose New Message"
        size="lg"
      >
        <Stack gap="md" mt="md">
          <MultiSelect
            label="Recipients"
            placeholder="Enter email or username"
            value={selectedRecipients}
            onChange={setSelectedRecipients}
            data={[]} // In real app, would fetch user list
            searchable
            creatable
            getCreateLabel={(query) => `+ Add ${query}`}
            onCreate={(query) => {
              setSelectedRecipients([...selectedRecipients, query]);
              return query;
            }}
            required
          />
          <TextInput
            label="Subject"
            value={compose.subject}
            onChange={(e) => dispatch(updateCompose({ subject: e.target.value }))}
            required
          />
          <Textarea
            label="Message"
            value={compose.content}
            onChange={(e) => dispatch(updateCompose({ content: e.target.value }))}
            rows={6}
            required
          />
          <Group align="center">
            <ActionIcon>
              <IconPaperclip size={16} />
            </ActionIcon>
            <Text size="xs" c="dimmed">
              {compose.attachments?.length || 0} attachments
            </Text>
          </Group>

          <Group justify="flex-end" gap="xs">
            <Button
              variant="outline"
              onClick={() => {
                setShowComposeDialog(false);
                dispatch(closeCompose());
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleComposeSubmit}
              disabled={!compose.subject || !compose.content || selectedRecipients.length === 0 || sending}
              loading={sending}
              leftSection={<IconSend size={16} />}
            >
              {sending ? 'Sending...' : 'Send'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Grid>
  );
}
