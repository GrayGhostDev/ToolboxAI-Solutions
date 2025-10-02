import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import { Notification } from '@mantine/core';
import * as React from "react";
import { useAppSelector, useAppDispatch } from "../../store";
import { removeNotification } from "../../store/slices/uiSlice";

function SlideTransition(props: TransitionProps & { children: React.ReactElement<any, any> }) {
  return <Slide {...props} direction="up" />;
}

export function NotificationToast() {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector((s) => s.ui.notifications);

  // Get the most recent notification
  const currentNotification = notifications[0];

  const handleClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === "clickaway") {
      return;
    }
    if (currentNotification) {
      dispatch(removeNotification(currentNotification.id));
    }
  };

  if (!currentNotification) {
    return null;
  }

  return (
    <Notification
      onClose={handleClose}
      color={currentNotification.type === 'error' ? 'red' : currentNotification.type === 'warning' ? 'yellow' : currentNotification.type === 'success' ? 'green' : 'blue'}
      title={currentNotification.type === 'error' ? 'Error' : currentNotification.type === 'warning' ? 'Warning' : currentNotification.type === 'success' ? 'Success' : 'Info'}
      style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000 }}
    >
      {currentNotification.message}
    </Notification>
  );
}
