import * as React from "react";
import { useEffect, useState } from "react";
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
  ListItem,
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
import MoreVertIcon from "@mui/icons-material/MoreVert";
import StarIcon from "@mui/icons-material/Star";
import DeleteIcon from "@mui/icons-material/Delete";
import ArchiveIcon from "@mui/icons-material/Archive";
import ReplyIcon from "@mui/icons-material/Reply";
import ForwardIcon from "@mui/icons-material/Forward";
import CircleIcon from "@mui/icons-material/Circle";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import DoneAllIcon from "@mui/icons-material/DoneAll";
import CreateIcon from "@mui/icons-material/Create";
import RefreshIcon from "@mui/icons-material/Refresh";
import InboxIcon from "@mui/icons-material/Inbox";
import SendOutlinedIcon from "@mui/icons-material/SendOutlined";
import DraftsIcon from "@mui/icons-material/Drafts";
import { useAppSelector, useAppDispatch } from "../../store";
import {
  fetchMessages,
  fetchMessageById,
  sendMessage,
  replyToMessage,
  forwardMessage,
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
} from "../../store/slices/messagesSlice";
import type { Message } from "../../types/api";

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
  type: "individual" | "group" | "announcement";
}

export default function Messages() {
  const dispatch = useAppDispatch();
  const role = useAppSelector((s) => s.user.role);
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
  const [searchTerm, setSearchTerm] = useState("");
  const [replyText, setReplyText] = useState("");
  const [showComposeDialog, setShowComposeDialog] = useState(false);
  const [recipientSearch, setRecipientSearch] = useState("");
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
          type: "individual",
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
      setReplyText("");
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
      return <DoneAllIcon sx={{ fontSize: 16, color: "info.main" }} />;
    }
    if (message.sentAt) {
      return <CheckCircleIcon sx={{ fontSize: 16, color: "text.secondary" }} />;
    }
    return null;
  };
  
  const getFolderIcon = (folder: string) => {
    switch (folder) {
      case 'inbox': return <InboxIcon />;
      case 'sent': return <SendOutlinedIcon />;
      case 'drafts': return <DraftsIcon />;
      case 'archived': return <ArchiveIcon />;
      case 'starred': return <StarIcon />;
      default: return <InboxIcon />;
    }
  };
  
  if (loading && messages.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Grid2 container spacing={2} sx={{ height: "calc(100vh - 200px)" }}>
      {/* Conversations List */}
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ p: 0, height: "100%", display: "flex", flexDirection: "column" }}>
            {/* Search */}
            <Box sx={{ p: 2 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search messages..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>

            {/* Tabs */}
            <Stack direction="row" sx={{ px: 2, pb: 1 }} gap={1}>
              {(["inbox", "sent", "drafts", "starred", "archived", "trash"] as const).map((tab) => (
                <Chip
                  key={tab}
                  icon={getFolderIcon(tab)}
                  label={
                    <Stack direction="row" alignItems="center" gap={0.5}>
                      <span>{tab.charAt(0).toUpperCase() + tab.slice(1)}</span>
                      {tab === "inbox" && unreadCount > 0 && (
                        <Badge badgeContent={unreadCount} color="error" sx={{ ml: 1 }} />
                      )}
                    </Stack>
                  }
                  size="small"
                  onClick={() => handleTabChange(tab)}
                  color={filters.folder === tab ? "primary" : "default"}
                  variant={filters.folder === tab ? "filled" : "outlined"}
                />
              ))}
            </Stack>

            <Divider />

            {/* Conversations */}
            <List sx={{ flex: 1, overflow: "auto" }}>
              {conversations.map((conversation) => (
                <ListItemButton
                  key={conversation.id}
                  selected={selectedConversation?.id === conversation.id}
                  onClick={() => setSelectedConversation(conversation)}
                >
                  <ListItemAvatar>
                    <Badge
                      badgeContent={conversation.unread}
                      color="error"
                      invisible={conversation.unread === 0}
                    >
                      <Avatar src={conversation.participants[0]?.avatar}>
                        {conversation.participants[0]?.name?.[0] || '?'}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="body2" sx={{ fontWeight: conversation.unread > 0 ? 600 : 400 }}>
                          {conversation.participants[0]?.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {conversation.timestamp}
                        </Typography>
                      </Stack>
                    }
                    secondary={
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          fontWeight: conversation.unread > 0 ? 600 : 400,
                        }}
                      >
                        {conversation.lastMessage}
                      </Typography>
                    }
                  />
                </ListItemButton>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid2>

      {/* Messages List */}
      <Grid2 size={{ xs: 12, md: 4 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ p: 0, height: "100%", display: "flex", flexDirection: "column" }}>
            {/* Header */}
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" gap={1}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {filters.folder.charAt(0).toUpperCase() + filters.folder.slice(1)}
                </Typography>
                <Chip label={`${messages.length} messages`} size="small" />
              </Stack>
              <Stack direction="row" gap={1}>
                <IconButton size="small" onClick={handleRefresh} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
                <Button 
                  variant="contained" 
                  startIcon={<CreateIcon />} 
                  size="small"
                  onClick={() => {
                    dispatch(openCompose({}));
                    setShowComposeDialog(true);
                  }}
                >
                  Compose
                </Button>
              </Stack>
            </Stack>

            <Divider />

            {/* Messages */}
            {error && (
              <Alert severity="error" onClose={() => dispatch(clearError())} sx={{ mx: 2, mb: 2 }}>
                {error}
              </Alert>
            )}
            <List sx={{ flex: 1, overflow: "auto" }}>
              {filteredMessages.length === 0 ? (
                <Box sx={{ p: 4, textAlign: "center" }}>
                  <Typography color="text.secondary">
                    {searchTerm ? "No messages found matching your search" : "No messages in this folder"}
                  </Typography>
                </Box>
              ) : (
                filteredMessages.map((message) => (
                  <ListItemButton
                    key={message.id}
                    selected={currentMessage?.id === message.id}
                    onClick={() => handleMessageSelect(message)}
                    sx={{
                      bgcolor: !message.read ? "action.hover" : "transparent",
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar>
                        {message.fromUserId?.charAt(0)?.toUpperCase() || '?'}
                      </Avatar>
                    </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                        <Box sx={{ flex: 1 }}>
                          <Stack direction="row" alignItems="center" gap={1}>
                            <Typography variant="body2" sx={{ fontWeight: !message.read ? 600 : 400 }}>
                              {message.fromUserId}
                            </Typography>
                            {message.attachments?.length > 0 && (
                              <Chip
                                icon={<AttachFileIcon sx={{ fontSize: 14 }} />}
                                label={message.attachments.length}
                                size="small"
                                sx={{ height: 20 }}
                              />
                            )}
                          </Stack>
                          <Typography variant="body2" sx={{ fontWeight: !message.read ? 600 : 500 }}>
                            {message.subject}
                          </Typography>
                        </Box>
                        <Stack alignItems="flex-end" gap={0.5}>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(message.sentAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </Typography>
                          {getStatusIcon(message)}
                        </Stack>
                      </Stack>
                    }
                    secondary={
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          display: "block",
                        }}
                      >
                        {message.content ? `${message.content.substring(0, 100)}...` : 'No content'}
                      </Typography>
                    }
                  />
                  </ListItemButton>
                ))
              )}
            </List>
          </CardContent>
        </Card>
      </Grid2>

      {/* Message Content */}
      <Grid2 size={{ xs: 12, md: 5 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ p: 0, height: "100%", display: "flex", flexDirection: "column" }}>
            {currentMessage ? (
              <>
                {/* Message Header */}
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ p: 2 }}
                >
                  <Stack direction="row" alignItems="center" gap={2}>
                    <Avatar>
                      {currentMessage.fromUserId[0]?.toUpperCase()}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {currentMessage.subject}
                      </Typography>
                      <Stack direction="row" alignItems="center" gap={1}>
                        <Typography variant="caption" color="text.secondary">
                          From: {currentMessage.fromUserId}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          To: {currentMessage.toUserId}
                        </Typography>
                      </Stack>
                    </Box>
                  </Stack>
                  <Stack direction="row" gap={1}>
                    <IconButton 
                      size="small"
                      onClick={() => handleStarMessage(currentMessage.id)}
                    >
                      <StarIcon color="action" />
                    </IconButton>
                    <IconButton 
                      size="small"
                      onClick={() => setReplyText(`\n\n---\nReplying to: ${currentMessage.subject}`)}
                    >
                      <ReplyIcon />
                    </IconButton>
                    <IconButton 
                      size="small"
                      onClick={() => {
                        dispatch(openCompose({ 
                          subject: `Fwd: ${currentMessage.subject}`,
                          content: `\n\n--- Forwarded message ---\n${currentMessage.content}`
                        }));
                        setShowComposeDialog(true);
                      }}
                    >
                      <ForwardIcon />
                    </IconButton>
                    <IconButton 
                      size="small"
                      onClick={() => handleArchiveMessage(currentMessage.id)}
                    >
                      <ArchiveIcon />
                    </IconButton>
                    <IconButton 
                      size="small"
                      onClick={() => handleDeleteMessage(currentMessage.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Stack>
                </Stack>

                <Divider />

                {/* Message Content */}
                <Box sx={{ flex: 1, p: 3, overflow: "auto" }}>
                  <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                    {new Date(currentMessage.sentAt).toLocaleString()}
                    {currentMessage.readAt && (
                      <span> • Read at {new Date(currentMessage.readAt).toLocaleString()}</span>
                    )}
                  </Typography>
                  <Typography variant="body1" paragraph style={{ whiteSpace: 'pre-wrap' }}>
                    {currentMessage.content}
                  </Typography>
                  {currentMessage.attachments && currentMessage.attachments.length > 0 && (
                    <Stack direction="row" gap={1} mt={2} flexWrap="wrap">
                      {currentMessage.attachments.map((attachment, idx) => (
                        <Paper key={idx} sx={{ p: 1.5, display: "flex", alignItems: "center", gap: 1 }}>
                          <AttachFileIcon fontSize="small" />
                          <Typography variant="caption">
                            {attachment.split('/').pop() || `Attachment ${idx + 1}`}
                          </Typography>
                        </Paper>
                      ))}
                    </Stack>
                  )}
                </Box>

                <Divider />

                {/* Reply Box */}
                <Box sx={{ p: 2 }}>
                  <Stack direction="row" gap={1}>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      placeholder="Type your reply..."
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter" && e.ctrlKey) {
                          handleSendReply();
                        }
                      }}
                      disabled={sending}
                    />
                    <Stack gap={1}>
                      <IconButton color="primary" disabled={sending}>
                        <AttachFileIcon />
                      </IconButton>
                      <Button
                        variant="contained"
                        onClick={handleSendReply}
                        disabled={!replyText.trim() || sending}
                      >
                        {sending ? <CircularProgress size={20} /> : <SendIcon />}
                      </Button>
                    </Stack>
                  </Stack>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                    Press Ctrl+Enter to send
                  </Typography>
                </Box>
              </>
            ) : (
              <Box
                sx={{
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Typography color="text.secondary">
                  Select a message to view
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid2>
      
      {/* Compose Dialog */}
      <Dialog 
        open={showComposeDialog} 
        onClose={() => {
          setShowComposeDialog(false);
          dispatch(closeCompose());
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Compose New Message
        </DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <Autocomplete
              multiple
              options={[]} // In real app, would fetch user list
              value={selectedRecipients}
              onChange={(_, newValue) => setSelectedRecipients(newValue)}
              freeSolo
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Recipients"
                  placeholder="Enter email or username"
                  required
                />
              )}
            />
            <TextField
              fullWidth
              label="Subject"
              value={compose.subject}
              onChange={(e) => dispatch(updateCompose({ subject: e.target.value }))}
              required
            />
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Message"
              value={compose.content}
              onChange={(e) => dispatch(updateCompose({ content: e.target.value }))}
              required
            />
            <Stack direction="row" alignItems="center">
              <IconButton>
                <AttachFileIcon />
              </IconButton>
              <Typography variant="caption" color="text.secondary">
                {compose.attachments?.length || 0} attachments
              </Typography>
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setShowComposeDialog(false);
              dispatch(closeCompose());
            }}
          >
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={handleComposeSubmit}
            disabled={!compose.subject || !compose.content || selectedRecipients.length === 0 || sending}
            startIcon={sending ? <CircularProgress size={16} /> : <SendIcon />}
          >
            {sending ? 'Sending...' : 'Send'}
          </Button>
        </DialogActions>
      </Dialog>
    </Grid2>
  );
}