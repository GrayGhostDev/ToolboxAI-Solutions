import * as React from "react";
import {
  Paper,
  Group,
  Text,
  ActionIcon,
  Select,
  Menu,
  Tooltip,
  Indicator,
  Box
} from "@mantine/core";
import {
  IconBell,
  IconMenu2,
  IconLanguage,
  IconMoon,
  IconSun,
  IconUser,
  IconLogout,
  IconSettings
} from "@tabler/icons-react";
import { UserRole } from "../../types";
import { useAppDispatch, useAppSelector } from "../../store";
import { toggleSidebar, setTheme, setLanguage } from "../../store/slices/uiSlice";
import { setRole, signOut } from "../../store/slices/userSlice";
import { useNavigate } from "react-router-dom";
import { LANGUAGES } from "../../config";
import { pusherService } from "../../services/pusher";
import ConnectionStatus from "../widgets/ConnectionStatus";
import AtomicAvatar from "../atomic/atoms/Avatar";

export default function Topbar() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  const displayName = useAppSelector((s) => s.user.displayName);
  const avatarUrl = useAppSelector((s) => s.user.avatarUrl);
  const theme = useAppSelector((s) => s.ui.theme);
  const language = useAppSelector((s) => s.ui.language);
  const notifications = useAppSelector((s) => s.ui.notifications);

  const handleSignOut = () => {
    // Disconnect Pusher before signing out
    pusherService.disconnect('User signed out');
    dispatch(signOut());
    navigate("/");
  };

  const handleSettings = () => {
    navigate("/settings");
  };

  return (
    <Paper
      h={64}
      style={{
        backdropFilter: "blur(8px)",
        background: theme === "dark"
          ? "linear-gradient(90deg, rgba(10, 10, 10, 0.95) 0%, rgba(26, 26, 26, 0.95) 100%)"
          : "linear-gradient(90deg, rgba(255, 255, 255, 0.95) 0%, rgba(245, 245, 255, 0.95) 100%)",
        borderBottom: "2px solid var(--mantine-color-cyan-6)",
        boxShadow: "0 4px 20px rgba(0, 188, 212, 0.3)",
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 101,
        display: "flex",
        alignItems: "center"
      }}
    >
      <Group style={{ height: "100%", paddingInline: "1rem", width: "100%" }} justify="space-between">
        <Group gap="md">
          {/* Menu Toggle */}
          <ActionIcon
            onClick={() => dispatch(toggleSidebar())}
            variant="subtle"
            size="lg"
            aria-label="Toggle navigation"
            color={theme === "dark" ? "gray" : "dark"}
          >
            <IconMenu2 size={20} />
          </ActionIcon>

          {/* Logo/Title */}
          <Text
            size="lg"
            fw={700}
            style={{
              background: "linear-gradient(135deg, #00bcd4, #e91e63)",
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              textShadow: "0 0 10px rgba(0, 188, 212, 0.5)"
            }}
          >
            🚀 Space Station Dashboard
          </Text>
        </Group>

        <Group gap="md">
          {/* Role Selector */}
          <Select
            value={role}
            onChange={(value) => value && dispatch(setRole(value as UserRole))}
            data={[
              { value: "admin", label: "Admin" },
              { value: "teacher", label: "Teacher" },
              { value: "student", label: "Student" },
              { value: "parent", label: "Parent" }
            ]}
            size="sm"
            styles={{
              input: {
                fontSize: "0.875rem",
                background: "linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))",
                border: "1px solid rgba(0, 188, 212, 0.3)",
                color: theme === "dark" ? "white" : "#1a1a2e",
                "&:focus": {
                  borderColor: "#00bcd4",
                },
              },
            }}
            aria-label="Select role"
          />

          {/* Connection Status */}
          <ConnectionStatus showLabel={true} size="small" />

          {/* Language Selector */}
          <Menu shadow="md" width={200}>
            <Menu.Target>
              <Tooltip label="Change language">
                <ActionIcon
                  variant="subtle"
                  size="lg"
                  aria-label="Language selector"
                  color={theme === "dark" ? "gray" : "dark"}
                >
                  <IconLanguage size={20} />
                </ActionIcon>
              </Tooltip>
            </Menu.Target>
            <Menu.Dropdown>
              {LANGUAGES.map((lang) => (
                <Menu.Item
                  key={lang.code}
                  onClick={() => dispatch(setLanguage(lang.code))}
                  style={{
                    fontWeight: language === lang.code ? 600 : 400
                  }}
                >
                  {lang.name}
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>

          {/* Theme Toggle */}
          <Tooltip label="Toggle theme">
            <ActionIcon
              onClick={() => dispatch(setTheme(theme === "light" ? "dark" : "light"))}
              variant="subtle"
              size="lg"
              aria-label="Toggle theme"
              color={theme === "dark" ? "gray" : "dark"}
            >
              {theme === "light" ? <IconMoon size={20} /> : <IconSun size={20} />}
            </ActionIcon>
          </Tooltip>

          {/* Notifications */}
          <Menu shadow="md" width={320}>
            <Menu.Target>
              <Tooltip label="Notifications">
                <Indicator
                  label={notifications.length}
                  size={16}
                  color="red"
                  disabled={notifications.length === 0}
                >
                  <ActionIcon
                    variant="subtle"
                    size="lg"
                    aria-label="Notifications"
                    color={theme === "dark" ? "gray" : "dark"}
                  >
                    <IconBell size={20} />
                  </ActionIcon>
                </Indicator>
              </Tooltip>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>Notifications</Menu.Label>
              {notifications.length === 0 ? (
                <Menu.Item disabled>
                  <Text size="sm" c="dimmed">
                    No new notifications
                  </Text>
                </Menu.Item>
              ) : (
                notifications.map((notif) => (
                  <Menu.Item key={notif?.id || Math.random()}>
                    <Text size="sm">{notif?.message}</Text>
                  </Menu.Item>
                ))
              )}
            </Menu.Dropdown>
          </Menu>

          {/* Profile Menu */}
          <Menu shadow="md" width={200}>
            <Menu.Target>
              <Tooltip label="Profile menu">
                <Box style={{ cursor: "pointer" }}>
                  {avatarUrl ? (
                    <AtomicAvatar
                      src={avatarUrl}
                      alt={displayName || "User"}
                      size="sm"
                      border={false}
                    />
                  ) : (
                    <ActionIcon
                      variant="subtle"
                      size="lg"
                      color={theme === "dark" ? "gray" : "dark"}
                    >
                      <IconUser size={20} />
                    </ActionIcon>
                  )}
                </Box>
              </Tooltip>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Label>{displayName || "Guest User"}</Menu.Label>
              <Menu.Item
                leftSection={<IconSettings size={16} />}
                onClick={handleSettings}
              >
                Settings
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item
                color="red"
                leftSection={<IconLogout size={16} />}
                onClick={handleSignOut}
              >
                Sign Out
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </Group>
    </Paper>
  );
}