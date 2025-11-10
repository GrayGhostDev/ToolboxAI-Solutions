import React, { useEffect, useMemo, useState } from 'react';
import { Card, Group, Badge, Text, Stack, Anchor } from '@mantine/core';

type PusherStatus = {
  connected: boolean;
  cluster?: string;
  channel?: string;
  socket_id?: string;
  since?: string;
  error?: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || `${location.protocol}//${location.host}`;

export function RealtimeStatusCard({ pollMs = 15000 }: { pollMs?: number }) {
  const [status, setStatus] = useState<PusherStatus | null>(null);
  const [ts, setTs] = useState<number>(Date.now());

  const endpoint = useMemo(() => `${API_BASE}/pusher/status`, []);

  useEffect(() => {
    let mounted = true;
    const fetchStatus = async () => {
      try {
        const res = await fetch(endpoint);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as PusherStatus;
        if (mounted) {
          setStatus(data);
          setTs(Date.now());
        }
      } catch (err) {
        if (mounted) {
          setStatus({ connected: false, error: (err as Error).message });
          setTs(Date.now());
        }
      }
    };
    fetchStatus();
    const id = window.setInterval(fetchStatus, pollMs);
    return () => {
      mounted = false;
      window.clearInterval(id);
    };
  }, [endpoint, pollMs]);

  const connected = !!status?.connected;
  const color = connected ? 'green' : 'red';

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Group justify="space-between" mb="xs">
        <Text fw={600}>Realtime Status</Text>
        <Badge color={color} variant="filled">
          {connected ? 'Connected' : 'Disconnected'}
        </Badge>
      </Group>
      <Stack gap="xs">
        <Text size="sm">
          Cluster: <Text span fw={500}>{status?.cluster || 'n/a'}</Text>
        </Text>
        <Text size="sm">
          Channel: <Text span fw={500}>{status?.channel || 'n/a'}</Text>
        </Text>
        <Text size="sm">
          Socket ID: <Text span fw={500}>{status?.socket_id || 'n/a'}</Text>
        </Text>
        {status?.since && (
          <Text size="sm">
            Since: <Text span fw={500}>{status.since}</Text>
          </Text>
        )}
        {status?.error && (
          <Text size="sm" c="red.6">
            Error: {status.error}
          </Text>
        )}
        <Text size="xs" c="dimmed">
          Endpoint: <Anchor size="xs" href={endpoint}>{endpoint}</Anchor> · Updated {new Date(ts).toLocaleTimeString()}
        </Text>
      </Stack>
    </Card>
  );
}

export default RealtimeStatusCard;

