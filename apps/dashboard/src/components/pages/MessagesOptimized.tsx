import * as React from "react";
import { useEffect, useState, memo, useMemo, useCallback } from "react";
import {
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  Avatar,
  Badge,
  Chip,
  IconButton,
  List,
  ListItemAvatar,
  ListItemText,
  ListItemButton,
  TextField,
  InputAdornment,
  Box,
  Divider,
  Paper,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Autocomplete,
} from "@mui/material";
import Grid2 from "@mui/material/Unstable_Grid2";
import SendIcon from "@mui/icons-material/Send";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import SearchIcon from "@mui/icons-material/Search";
import StarIcon from "@mui/icons-material/Star";
import DeleteIcon from "@mui/icons-material/Delete";
import ArchiveIcon from "@mui/icons-material/Archive";
import ReplyIcon from "@mui/icons-material/Reply";
import ForwardIcon from "@mui/icons-material/Forward";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import DoneAllIcon from "@mui/icons-material/DoneAll";
import CreateIcon from "@mui/icons-material/Create";
import RefreshIcon from "@mui/icons-material/Refresh";
import InboxIcon from "@mui/icons-material/Inbox";
import SendOutlinedIcon from "@mui/icons-material/SendOutlined";
import DraftsIcon from "@mui/icons-material/Drafts";

import { useAppSelector, useAppDispatch } from "../../store";
import VirtualizedList from "../common/VirtualizedList";
import { useOptimizedMemo, useOptimizedCallback, useDebouncedCallback, useRenderPerformance } from "../../hooks/usePerformance";

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
      elevation={message.isRead ? 0 : 1}
      sx={{
        margin: 1,
        height: 120, // Fixed height for virtual scrolling
        cursor: 'pointer',
        backgroundColor: message.isRead ? 'background.paper' : 'action.hover',
        '&:hover': {
          backgroundColor: 'action.selected',
        },
      }}
      onClick={handleClick}
    >
      <Box p={2} height="100%" display="flex" alignItems="center">
        <Avatar
          src={message.senderAvatar}
          sx={{ mr: 2, width: 40, height: 40 }}
        >
          {message.sender.charAt(0).toUpperCase()}
        </Avatar>

        <Box flexGrow={1} minWidth={0}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
            <Typography
              variant="subtitle2"
              fontWeight={message.isRead ? 'normal' : 'bold'}
              noWrap
            >
              {message.sender}
            </Typography>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Typography variant="caption" color="text.secondary">
                {formattedTime}
              </Typography>
              <IconButton
                size="small"
                onClick={handleStarToggle}
                color={message.isStarred ? 'warning' : 'default'}
              >
                <StarIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={handleDelete}>
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          <Typography
            variant="body2"
            fontWeight={message.isRead ? 'normal' : 'bold'}
            noWrap
            mb={0.5}
          >
            {message.subject}
          </Typography>

          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography
              variant="body2"
              color="text.secondary"
              noWrap
              sx={{ flexGrow: 1, mr: 1 }}
            >
              {message.preview}
            </Typography>

            <Box display="flex" gap={0.5}>
              {message.priority !== 'normal' && (
                <Chip
                  size="small"
                  label={message.priority}
                  color={priorityColor as any}
                  variant="outlined"
                />
              )}
              {message.hasAttachment && (
                <AttachFileIcon fontSize="small" color="action" />
              )}
              {message.threadCount > 1 && (
                <Chip
                  size="small"
                  label={message.threadCount}
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        </Box>
      </Box>
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
    { value: 'all', label: 'All Messages', icon: <InboxIcon /> },
    { value: 'unread', label: 'Unread', icon: <DraftsIcon /> },
    { value: 'starred', label: 'Starred', icon: <StarIcon /> },
    { value: 'sent', label: 'Sent', icon: <SendOutlinedIcon /> },
  ], [], 'MessageFilters:filterOptions');

  return (
    <Box display="flex" gap={2} mb={3} flexWrap="wrap">
      <TextField
        placeholder="Search messages..."
        defaultValue={searchTerm}
        onChange={handleSearchChange}
        size="small"
        sx={{ minWidth: 300, flexGrow: 1 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />

      <Box display="flex" gap={1}>
        {filterOptions.map((option) => (
          <Button
            key={option.value}
            variant={filterType === option.value ? 'contained' : 'outlined'}
            startIcon={option.icon}
            onClick={() => onFilterChange(option.value)}
            size="small"
          >
            {option.label}
          </Button>
        ))}
      </Box>

      <Box display="flex" gap={1}>
        <Button
          variant="contained"
          startIcon={<CreateIcon />}
          onClick={onCompose}
        >
          Compose
        </Button>
        <IconButton onClick={onRefresh} disabled={loading}>
          <RefreshIcon />
        </IconButton>
      </Box>
    </Box>
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
    <Box>
      <Typography variant="h4" component="h1" mb={3}>
        Messages
      </Typography>

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
        <Box display="flex" justifyContent="center" alignItems="center" height="400px">
          <CircularProgress />
        </Box>
      ) : filteredMessages.length === 0 ? (
        <Box display="flex" justifyContent="center" alignItems="center" height="400px">
          <Typography color="text.secondary">
            {searchTerm ? 'No messages match your search.' : 'No messages found.'}
          </Typography>
        </Box>
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

      {/* Message Detail Dialog */}
      <Dialog
        open={!!selectedMessage}
        onClose={() => setSelectedMessage(null)}
        maxWidth="md"
        fullWidth
      >
        {selectedMessage && (
          <>
            <DialogTitle>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">{selectedMessage.subject}</Typography>
                <Box>
                  <IconButton onClick={() => handleStarToggle(selectedMessage.id)}>
                    <StarIcon color={selectedMessage.isStarred ? "warning" : "inherit"} />
                  </IconButton>
                  <IconButton>
                    <ReplyIcon />
                  </IconButton>
                  <IconButton>
                    <ForwardIcon />
                  </IconButton>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box mb={2}>
                <Typography variant="subtitle2" color="text.secondary">
                  From: {selectedMessage.sender}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {selectedMessage.timestamp.toLocaleString()}
                </Typography>
              </Box>
              <Typography variant="body1">
                {selectedMessage.preview}
                {/* In real app, would show full message content */}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedMessage(null)}>Close</Button>
              <Button variant="contained" startIcon={<ReplyIcon />}>
                Reply
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Compose Dialog */}
      <Dialog
        open={composeOpen}
        onClose={() => setComposeOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Compose Message</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="To"
              fullWidth
              placeholder="Enter recipient..."
            />
            <TextField
              label="Subject"
              fullWidth
              placeholder="Enter subject..."
            />
            <TextField
              label="Message"
              multiline
              rows={6}
              fullWidth
              placeholder="Type your message..."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComposeOpen(false)}>Cancel</Button>
          <Button variant="contained" startIcon={<SendIcon />}>
            Send
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}