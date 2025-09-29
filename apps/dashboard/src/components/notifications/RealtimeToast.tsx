import * as React from "react";
import { notifications } from "@mantine/notifications";
import { PUSHER_ENABLED } from "../../config";
import { usePusherChannel } from "../../hooks/usePusherEvents";
import { IconSchool, IconTrophy, IconAlertCircle } from "@tabler/icons-react";

export default function RealtimeToast() {
  // Pusher event handlers
  const handleClassOnline = React.useCallback((data: any) => {
    notifications.show({
      title: "Class Online",
      message: `Class "${data?.className || 'Unknown'}" is now online!`,
      color: "blue",
      icon: <IconSchool size={20} />,
      autoClose: 6000,
    });
  }, []);

  const handleAchievementUnlocked = React.useCallback((data: any) => {
    notifications.show({
      title: "Achievement Unlocked",
      message: data?.message || 'Achievement unlocked!',
      color: "green",
      icon: <IconTrophy size={20} />,
      autoClose: 6000,
    });
  }, []);

  const handleAssignmentReminder = React.useCallback((data: any) => {
    notifications.show({
      title: "Assignment Reminder",
      message: data?.message || 'Assignment due soon',
      color: "yellow",
      icon: <IconAlertCircle size={20} />,
      autoClose: 6000,
    });
  }, []);

  // Use Pusher for real-time events
  usePusherChannel(
    'public',
    {
      'class-online': handleClassOnline,
      'achievement-unlocked': handleAchievementUnlocked,
      'assignment-reminder': handleAssignmentReminder,
    },
    {
      enabled: PUSHER_ENABLED,
    }
  );

  // Component doesn't render any UI - notifications are handled by Mantine's notification system
  return null;
}
