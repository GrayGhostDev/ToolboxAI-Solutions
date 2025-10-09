/**
 * Roblox Keyboard Shortcuts Modal
 *
 * Displays available keyboard shortcuts in a modal with Roblox styling.
 *
 * @module RobloxKeyboardShortcutsModal
 * @since 2025-10-01
 */

import { memo } from 'react';
import { Modal, Text, Grid, Box, Group, Badge, Stack } from '@mantine/core';
import { IconKeyboard } from '@tabler/icons-react';
import { type KeyboardShortcut, formatShortcut } from '../../hooks/useKeyboardShortcuts';

export interface RobloxKeyboardShortcutsModalProps {
  /** Whether modal is open */
  opened: boolean;
  /** Close handler */
  onClose: () => void;
  /** List of keyboard shortcuts to display */
  shortcuts: KeyboardShortcut[];
}

/**
 * Keyboard shortcuts help modal with Roblox theming
 *
 * @example
 * ```typescript
 * const [opened, setOpened] = useState(false);
 *
 * <RobloxKeyboardShortcutsModal
 *   opened={opened}
 *   onClose={() => setOpened(false)}
 *   shortcuts={dashboardShortcuts}
 * />
 * ```
 */
export const RobloxKeyboardShortcutsModal = memo<RobloxKeyboardShortcutsModalProps>(
  ({ opened, onClose, shortcuts }) => {
    // Group shortcuts by category
    const categorized = shortcuts.reduce((acc, shortcut) => {
      const category = shortcut.description.startsWith('Go to')
        ? 'Navigation'
        : shortcut.description.includes('Focus')
        ? 'Actions'
        : 'General';

      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(shortcut);
      return acc;
    }, {} as Record<string, KeyboardShortcut[]>);

    return (
      <Modal
        opened={opened}
        onClose={onClose}
        title={
          <Group gap="sm">
            <IconKeyboard size={24} />
            <Text size="xl" fw={700}>
              Keyboard Shortcuts
            </Text>
          </Group>
        }
        size="lg"
        centered
        styles={(theme) => ({
          title: {
            color: theme.colors.electricBlue[5],
            fontSize: theme.fontSizes.xl,
            fontWeight: 700,
          },
          header: {
            borderBottom: `2px solid ${theme.colors.electricBlue[5]}`,
            paddingBottom: theme.spacing.md,
          },
        })}
      >
        <Stack gap="xl">
          {Object.entries(categorized).map(([category, categoryShortcuts]) => (
            <Box key={category}>
              <Text
                size="lg"
                fw={600}
                mb="md"
                style={(theme) => ({ color: theme.colors.hotPink[5] })}
              >
                {category}
              </Text>

              <Stack gap="sm">
                {categoryShortcuts.map((shortcut, index) => (
                  <Grid key={index} gutter="md" align="center">
                    <Grid.Col span={{ base: 12, sm: 8 }}>
                      <Text size="sm">{shortcut.description}</Text>
                    </Grid.Col>
                    <Grid.Col span={{ base: 12, sm: 4 }}>
                      <Group justify="flex-end">
                        <Badge
                          variant="filled"
                          size="lg"
                          style={(theme) => ({
                            backgroundColor: theme.colors.deepSpace[7],
                            color: theme.colors.electricBlue[4],
                            fontFamily: 'monospace',
                            fontSize: theme.fontSizes.sm,
                            padding: `${theme.spacing.xs} ${theme.spacing.md}`,
                            border: `2px solid ${theme.colors.electricBlue[6]}`,
                            boxShadow: `0 0 10px ${theme.colors.electricBlue[5]}40`,
                          })}
                        >
                          {formatShortcut(shortcut)}
                        </Badge>
                      </Group>
                    </Grid.Col>
                  </Grid>
                ))}
              </Stack>
            </Box>
          ))}

          <Box
            p="md"
            style={(theme) => ({
              backgroundColor: theme.colors.deepSpace[8],
              border: `2px solid ${theme.colors.toxicGreen[6]}`,
              borderRadius: theme.radius.md,
            })}
          >
            <Group gap="sm">
              <Text size="sm" fw={600} style={(theme) => ({ color: theme.colors.toxicGreen[5] })}>
                💡 Tip:
              </Text>
              <Text size="sm">
                Press <Badge size="sm">?</Badge> at any time to open this help modal
              </Text>
            </Group>
          </Box>
        </Stack>
      </Modal>
    );
  }
);

RobloxKeyboardShortcutsModal.displayName = 'RobloxKeyboardShortcutsModal';
