import { Box, Button, Text, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card, Group, List, Divider, TextInput, Select, Badge, Alert, Loader, Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio, Switch, Slider, Rating, Skeleton, Table } from '@mantine/core';
/**
 * System Health Indicator Component
 *
 * Visual indicator for overall agent system health status.
 *
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React from 'react';
import { IconAlertTriangle, IconCircleCheck, IconX, IconWifiOff } from '@tabler/icons-react';

interface SystemHealthIndicatorProps {
  status: 'healthy' | 'degraded' | 'error';
  isConnected: boolean;
}

export const SystemHealthIndicator = ({
  status,
  isConnected,
}: SystemHealthIndicatorProps) => {
  const getHealthConfig = () => {
    if (!isConnected) {
      return {
        color: 'gray' as const,
        icon: <IconWifiOff />,
        label: 'Disconnected',
        tooltip: 'Not connected to real-time updates'
      };
    }

    switch (status) {
      case 'healthy':
        return {
          color: 'green' as const,
          icon: <IconCircleCheck />,
          label: 'Healthy',
          tooltip: 'All systems operational'
        };
      case 'degraded':
        return {
          color: 'orange' as const,
          icon: <IconAlertTriangle />,
          label: 'Degraded',
          tooltip: 'Some issues detected'
        };
      case 'error':
        return {
          color: 'red' as const,
          icon: <IconX />,
          label: 'Error',
          tooltip: 'Critical issues detected'
        };
      default:
        return {
          color: 'gray' as const,
          icon: <IconAlertTriangle />,
          label: 'Unknown',
          tooltip: 'Status unknown'
        };
    }
  };

  const config = getHealthConfig();

  return (
    <Tooltip label={config.tooltip}>
      <Badge
        color={config.color}
        leftSection={config.icon}
        size="lg"
      >
        {config.label}
      </Badge>
    </Tooltip>
  );
};

export default SystemHealthIndicator;