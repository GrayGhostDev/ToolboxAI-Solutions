import { Notification } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import * as React from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { removeNotification } from '../../store/slices/uiSlice';

export function NotificationToast() {
  const dispatch = useAppDispatch();
  const notificationsList = useAppSelector((s) => s.ui.notifications);

  // Get the most recent notification
  const currentNotification = notificationsList[0];

  React.useEffect(() => {
    if (currentNotification) {
      const notificationId = notifications.show({
        title: currentNotification.type.charAt(0).toUpperCase() + currentNotification.type.slice(1),
        message: currentNotification.message,
        color: currentNotification.type === 'error' ? 'red' :
               currentNotification.type === 'warning' ? 'yellow' :
               currentNotification.type === 'success' ? 'green' : 'blue',
        autoClose: currentNotification.autoHide !== false ? 5000 : false,
        onClose: () => dispatch(removeNotification(currentNotification.id)),
        position: 'bottom-right',
      });

      // Clean up by removing from Redux when notification auto-closes
      if (currentNotification.autoHide !== false) {
        setTimeout(() => {
          dispatch(removeNotification(currentNotification.id));
        }, 5000);
      }
    }
  }, [currentNotification, dispatch]);

  // This component now uses Mantine's notification system
  // The actual notification is rendered by Mantine's NotificationsProvider
  return null;
}