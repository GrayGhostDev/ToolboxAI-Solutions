import * as React from "react";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import Avatar from "@mui/material/Avatar";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
// import { wsService } from "../../services/ws";
import { subscribeToChannel, unsubscribeFromChannel } from "../../services/websocket";
import { ENABLE_WEBSOCKET } from "../../config";
import { WebSocketMessageType } from "../../types/websocket";

export default function RealtimeToast() {
  const [message, setMessage] = React.useState<{
    text: string;
    type: "info" | "success" | "warning" | "error";
    icon?: string;
  } | null>(null);

  React.useEffect(() => {
    if (!ENABLE_WEBSOCKET) return;

    // Unified message handler for all public channel messages
    const handlePublicMessage = (message: any) => {
      switch (message.type) {
        case WebSocketMessageType.CLASS_ONLINE:
          setMessage({
            text: `Class "${message.payload?.className || 'Unknown'}" is now online!`,
            type: "info",
            icon: "🏫",
          });
          break;

        case WebSocketMessageType.ACHIEVEMENT_UNLOCKED:
          setMessage({
            text: message.payload?.message || 'Achievement unlocked!',
            type: "success",
            icon: "🏆",
          });
          break;

        case WebSocketMessageType.ASSIGNMENT_REMINDER:
          setMessage({
            text: message.payload?.message || 'Assignment due soon',
            type: "warning",
            icon: "📝",
          });
          break;
      }
    };

    // Single subscription with message type filtering
    const subscriptionId = subscribeToChannel(
      'public',
      handlePublicMessage,
      (msg) =>
        msg.type === WebSocketMessageType.CLASS_ONLINE ||
        msg.type === WebSocketMessageType.ACHIEVEMENT_UNLOCKED ||
        msg.type === WebSocketMessageType.ASSIGNMENT_REMINDER
    );

    return () => {
      unsubscribeFromChannel(subscriptionId);
    };
  }, []);

  const handleClose = () => {
    setMessage(null);
  };

  if (!message) {
    return null;
  }

  return (
    <Snackbar
      open={true}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: "top", horizontal: "center" }}
    >
      <Alert
        onClose={handleClose}
        severity={message.type}
        sx={{
          width: "100%",
          alignItems: "center",
        }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          {message.icon && (
            <Avatar sx={{ width: 24, height: 24, fontSize: "1rem", bgcolor: "transparent" }}>
              {message.icon}
            </Avatar>
          )}
          <Typography variant="body2">{message.text}</Typography>
        </Stack>
      </Alert>
    </Snackbar>
  );
}
