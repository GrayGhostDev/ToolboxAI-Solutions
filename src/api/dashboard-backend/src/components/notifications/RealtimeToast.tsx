import * as React from "react";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import Avatar from "@mui/material/Avatar";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { wsService } from "../../services/ws";
import { ENABLE_WEBSOCKET } from "../../config";

export default function RealtimeToast() {
  const [message, setMessage] = React.useState<{
    text: string;
    type: "info" | "success" | "warning" | "error";
    icon?: string;
  } | null>(null);

  React.useEffect(() => {
    if (!ENABLE_WEBSOCKET) return;

    const handleClassOnline = (data: any) => {
      setMessage({
        text: `Class "${data.className}" is now online!`,
        type: "info",
        icon: "🏫",
      });
    };

    const handleAchievement = (data: any) => {
      setMessage({
        text: data.message,
        type: "success",
        icon: "🏆",
      });
    };

    const handleAssignmentReminder = (data: any) => {
      setMessage({
        text: data.message,
        type: "warning",
        icon: "📝",
      });
    };

    wsService.on("class_online", handleClassOnline);
    wsService.on("achievement_unlocked", handleAchievement);
    wsService.on("assignment_reminder", handleAssignmentReminder);

    return () => {
      wsService.off("class_online", handleClassOnline);
      wsService.off("achievement_unlocked", handleAchievement);
      wsService.off("assignment_reminder", handleAssignmentReminder);
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