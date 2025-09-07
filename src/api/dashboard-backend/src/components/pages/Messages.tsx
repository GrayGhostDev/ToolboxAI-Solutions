import * as React from "react";
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
import { useAppSelector } from "../../store";

interface Message {
  id: string;
  from: {
    name: string;
    avatar?: string;
    role: string;
  };
  to?: string;
  subject: string;
  preview: string;
  content: string;
  timestamp: string;
  read: boolean;
  starred: boolean;
  attachments?: number;
  category: "inbox" | "sent" | "draft" | "archived";
}

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
  const role = useAppSelector((s) => s.user.role);
  const [selectedMessage, setSelectedMessage] = React.useState<Message | null>(null);
  const [selectedConversation, setSelectedConversation] = React.useState<Conversation | null>(null);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [messageText, setMessageText] = React.useState("");
  const [activeTab, setActiveTab] = React.useState<"inbox" | "sent" | "draft" | "archived">("inbox");

  const messages: Message[] = [
    {
      id: "1",
      from: {
        name: "Sarah Johnson",
        avatar: "/avatar1.png",
        role: "Teacher",
      },
      subject: "Math Assignment Due Tomorrow",
      preview: "Don't forget to submit your algebra homework by...",
      content: "Don't forget to submit your algebra homework by tomorrow 3 PM. Please make sure to show all your work for full credit.",
      timestamp: "2024-01-29 10:30",
      read: false,
      starred: true,
      attachments: 2,
      category: "inbox",
    },
    {
      id: "2",
      from: {
        name: "Parent Portal",
        role: "System",
      },
      subject: "Weekly Progress Report",
      preview: "Your child has completed 85% of this week's...",
      content: "Your child has completed 85% of this week's assignments and earned 250 XP. Click here to view detailed progress.",
      timestamp: "2024-01-29 09:15",
      read: true,
      starred: false,
      category: "inbox",
    },
    {
      id: "3",
      from: {
        name: "Alex Chen",
        avatar: "/avatar2.png",
        role: "Student",
      },
      subject: "Group Project Meeting",
      preview: "Can we meet tomorrow after class to discuss...",
      content: "Can we meet tomorrow after class to discuss our science project? I've found some great resources we can use.",
      timestamp: "2024-01-28 16:45",
      read: true,
      starred: false,
      attachments: 1,
      category: "inbox",
    },
    {
      id: "4",
      from: {
        name: "Admin",
        role: "Admin",
      },
      subject: "New Roblox Experience Available",
      preview: "A new educational experience has been added...",
      content: "A new educational experience 'Space Explorer' has been added to your Roblox classroom. Students can now access it.",
      timestamp: "2024-01-28 14:20",
      read: false,
      starred: true,
      category: "inbox",
    },
  ];

  const conversations: Conversation[] = [
    {
      id: "1",
      participants: [
        { name: "Math Class 5A", avatar: "/class1.png" },
      ],
      lastMessage: "Tomorrow's quiz has been posted",
      timestamp: "10:30 AM",
      unread: 3,
      type: "group",
    },
    {
      id: "2",
      participants: [
        { name: "Sarah Johnson", avatar: "/avatar1.png", online: true },
      ],
      lastMessage: "Thanks for your help!",
      timestamp: "Yesterday",
      unread: 0,
      type: "individual",
    },
    {
      id: "3",
      participants: [
        { name: "Science Project Team", avatar: "/team.png" },
      ],
      lastMessage: "Meeting scheduled for 3 PM",
      timestamp: "2 days ago",
      unread: 5,
      type: "group",
    },
    {
      id: "4",
      participants: [
        { name: "School Announcements" },
      ],
      lastMessage: "Field trip permission forms due",
      timestamp: "3 days ago",
      unread: 1,
      type: "announcement",
    },
  ];

  const filteredMessages = messages.filter(
    (msg) =>
      msg.category === activeTab &&
      (msg.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
        msg.from.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        msg.preview.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSendMessage = () => {
    if (messageText.trim()) {
      console.log("Sending message:", messageText);
      setMessageText("");
    }
  };

  const getStatusIcon = (message: Message) => {
    if (message.category === "sent") {
      if (message.read) {
        return <DoneAllIcon sx={{ fontSize: 16, color: "info.main" }} />;
      }
      return <CheckCircleIcon sx={{ fontSize: 16, color: "text.secondary" }} />;
    }
    return null;
  };

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
              {(["inbox", "sent", "draft", "archived"] as const).map((tab) => (
                <Chip
                  key={tab}
                  label={tab.charAt(0).toUpperCase() + tab.slice(1)}
                  size="small"
                  onClick={() => setActiveTab(tab)}
                  color={activeTab === tab ? "primary" : "default"}
                  variant={activeTab === tab ? "filled" : "outlined"}
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
                        {conversation.participants[0]?.name[0]}
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
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
              </Typography>
              <Button variant="contained" startIcon={<CreateIcon />} size="small">
                Compose
              </Button>
            </Stack>

            <Divider />

            {/* Messages */}
            <List sx={{ flex: 1, overflow: "auto" }}>
              {filteredMessages.map((message) => (
                <ListItem
                  key={message.id}
                  button
                  selected={selectedMessage?.id === message.id}
                  onClick={() => setSelectedMessage(message)}
                  sx={{
                    bgcolor: !message.read ? "action.hover" : "transparent",
                  }}
                >
                  <ListItemAvatar>
                    <Avatar src={message.from.avatar}>
                      {message.from.name[0]}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                        <Box sx={{ flex: 1 }}>
                          <Stack direction="row" alignItems="center" gap={1}>
                            <Typography variant="body2" sx={{ fontWeight: !message.read ? 600 : 400 }}>
                              {message.from.name}
                            </Typography>
                            {message.starred && <StarIcon sx={{ fontSize: 16, color: "warning.main" }} />}
                            {message.attachments && (
                              <Chip
                                icon={<AttachFileIcon sx={{ fontSize: 14 }} />}
                                label={message.attachments}
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
                            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                        {message.preview}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid2>

      {/* Message Content */}
      <Grid2 size={{ xs: 12, md: 5 }}>
        <Card sx={{ height: "100%" }}>
          <CardContent sx={{ p: 0, height: "100%", display: "flex", flexDirection: "column" }}>
            {selectedMessage ? (
              <>
                {/* Message Header */}
                <Stack
                  direction="row"
                  justifyContent="space-between"
                  alignItems="center"
                  sx={{ p: 2 }}
                >
                  <Stack direction="row" alignItems="center" gap={2}>
                    <Avatar src={selectedMessage.from.avatar}>
                      {selectedMessage.from.name[0]}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {selectedMessage.subject}
                      </Typography>
                      <Stack direction="row" alignItems="center" gap={1}>
                        <Typography variant="caption" color="text.secondary">
                          From: {selectedMessage.from.name}
                        </Typography>
                        <Chip label={selectedMessage.from.role} size="small" sx={{ height: 18 }} />
                      </Stack>
                    </Box>
                  </Stack>
                  <Stack direction="row" gap={1}>
                    <IconButton size="small">
                      <StarIcon color={selectedMessage.starred ? "warning" : "action"} />
                    </IconButton>
                    <IconButton size="small">
                      <ReplyIcon />
                    </IconButton>
                    <IconButton size="small">
                      <ForwardIcon />
                    </IconButton>
                    <IconButton size="small">
                      <ArchiveIcon />
                    </IconButton>
                    <IconButton size="small">
                      <DeleteIcon />
                    </IconButton>
                    <IconButton size="small">
                      <MoreVertIcon />
                    </IconButton>
                  </Stack>
                </Stack>

                <Divider />

                {/* Message Content */}
                <Box sx={{ flex: 1, p: 3, overflow: "auto" }}>
                  <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                    {new Date(selectedMessage.timestamp).toLocaleString()}
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {selectedMessage.content}
                  </Typography>
                  {selectedMessage.attachments && (
                    <Stack direction="row" gap={1} mt={2}>
                      {Array.from({ length: selectedMessage.attachments }).map((_, idx) => (
                        <Paper key={idx} sx={{ p: 1.5, display: "flex", alignItems: "center", gap: 1 }}>
                          <AttachFileIcon fontSize="small" />
                          <Typography variant="caption">
                            Attachment {idx + 1}
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
                      rows={2}
                      placeholder="Type your reply..."
                      value={messageText}
                      onChange={(e) => setMessageText(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter" && e.ctrlKey) {
                          handleSendMessage();
                        }
                      }}
                    />
                    <Stack gap={1}>
                      <IconButton color="primary">
                        <AttachFileIcon />
                      </IconButton>
                      <Button
                        variant="contained"
                        onClick={handleSendMessage}
                        disabled={!messageText.trim()}
                      >
                        <SendIcon />
                      </Button>
                    </Stack>
                  </Stack>
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
    </Grid2>
  );
}