import * as React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Drawer,
  NavLink,
  Box,
  Text,
  Progress,
  Divider,
  Stack,
  Group,
  ScrollArea
} from "@mantine/core";
import {
  IconDashboard,
  IconSchool,
  IconUsers,
  IconClipboardCheck,
  IconTrophy,
  IconAward,
  IconShield,
  IconSettings,
  IconDeviceGamepad2,
  IconUser,
  IconMessage,
  IconChartBar,
  IconCode,
  IconFlag,
  IconPuzzle,
  IconRobot
} from "@tabler/icons-react";
import { UserRole } from "../../types";
import { useAppSelector } from "../../store";

const drawerWidth = 240;

interface Props {
  role: UserRole;
}

const roleMenus: Record<UserRole, { label: string; icon: React.ReactNode; path: string }[]> = {
  admin: [
    { label: "Overview", icon: <IconDashboard size={20} />, path: "/" },
    { label: "Schools", icon: <IconSchool size={20} />, path: "/schools" },
    { label: "Users", icon: <IconUsers size={20} />, path: "/users" },
    { label: "Compliance", icon: <IconShield size={20} />, path: "/compliance" },
    { label: "Analytics", icon: <IconTrophy size={20} />, path: "/analytics" },
    { label: "Agent System", icon: <IconRobot size={20} />, path: "/agents" },
    { label: "Roblox Studio", icon: <IconPuzzle size={20} />, path: "/roblox" },
    { label: "Integrations", icon: <IconCode size={20} />, path: "/integrations" },
    { label: "Settings", icon: <IconSettings size={20} />, path: "/settings" },
  ],
  teacher: [
    { label: "Overview", icon: <IconDashboard size={20} />, path: "/" },
    { label: "Classes", icon: <IconUsers size={20} />, path: "/classes" },
    { label: "Lessons", icon: <IconClipboardCheck size={20} />, path: "/lessons" },
    { label: "Assessments", icon: <IconChartBar size={20} />, path: "/assessments" },
    { label: "Roblox Studio", icon: <IconPuzzle size={20} />, path: "/roblox" },
    { label: "Reports", icon: <IconTrophy size={20} />, path: "/reports" },
    { label: "Messages", icon: <IconMessage size={20} />, path: "/messages" },
    { label: "Settings", icon: <IconSettings size={20} />, path: "/settings" },
  ],
  student: [
    { label: "Overview", icon: <IconDashboard size={20} />, path: "/" },
    { label: "Missions", icon: <IconFlag size={20} />, path: "/missions" },
    { label: "Progress", icon: <IconTrophy size={20} />, path: "/progress" },
    { label: "Rewards", icon: <IconAward size={20} />, path: "/rewards" },
    { label: "Leaderboard", icon: <IconTrophy size={20} />, path: "/leaderboard" },
    { label: "Avatar", icon: <IconUser size={20} />, path: "/avatar" },
    { label: "Play", icon: <IconDeviceGamepad2 size={20} />, path: "/play" },
    { label: "Settings", icon: <IconSettings size={20} />, path: "/settings" },
  ],
  parent: [
    { label: "Overview", icon: <IconDashboard size={20} />, path: "/" },
    { label: "Progress", icon: <IconTrophy size={20} />, path: "/progress" },
    { label: "Reports", icon: <IconChartBar size={20} />, path: "/reports" },
    { label: "Messages", icon: <IconMessage size={20} />, path: "/messages" },
    { label: "Settings", icon: <IconSettings size={20} />, path: "/settings" },
  ],
};

export default function Sidebar({ role }: Props) {
  const location = useLocation();
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);
  const xp = useAppSelector((s) => s.gamification.xp);
  const level = useAppSelector((s) => s.gamification.level);
  const nextLevelXP = useAppSelector((s) => s.gamification.nextLevelXP);
  const displayName = useAppSelector((s) => s.user.displayName);
  const firstName = useAppSelector((s) => s.user.firstName);

  const progress = ((xp % 100) / 100) * 100;

  // Roles are already normalized as lowercase strings matching UserRole
  const menuItems = roleMenus[role] || roleMenus.student;

  return (
    <Drawer
      opened={sidebarOpen}
      onClose={() => {}} // Controlled by Redux
      size={drawerWidth}
      position="left"
      withCloseButton={false}
      zIndex={100}
      styles={{
        drawer: {
          background: "linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%)",
          borderRight: "2px solid var(--mantine-color-cyan-6)",
          boxShadow: "0 0 20px rgba(0, 188, 212, 0.3)",
        },
      }}
    >
      <ScrollArea h="100vh">
        {/* Space for toolbar */}
        <Box h={64} />

        {/* User Info Section */}
        <Box
          p="md"
          mx="md"
          mb="xs"
          style={{
            textAlign: "center",
            background: "linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))",
            border: "1px solid rgba(0, 188, 212, 0.3)",
            borderRadius: "var(--mantine-radius-md)",
          }}
        >
          <Text
            size="lg"
            fw={700}
            mb="xs"
            style={{
              background: "linear-gradient(135deg, #00bcd4, #e91e63)",
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              textShadow: "0 0 10px rgba(0, 188, 212, 0.5)"
            }}
          >
            {firstName || displayName || role}
          </Text>

          {/* XP Progress for Students */}
          {role === "student" && (
            <Stack spacing={4} mt="sm">
              <Group position="apart">
                <Text size="xs" color="dimmed">
                  Level {level}
                </Text>
                <Text size="xs" color="dimmed">
                  {xp} / {nextLevelXP} XP
                </Text>
              </Group>
              <Progress
                value={progress}
                size="sm"
                radius="xl"
                styles={{
                  root: {
                    backgroundColor: "rgba(255,255,255,0.1)",
                  },
                  bar: {
                    background: "linear-gradient(90deg, #9333EA 0%, #14B8A6 100%)",
                  },
                }}
              />
            </Stack>
          )}
        </Box>

        <Divider color="rgba(255,255,255,0.1)" />

        {/* Navigation Menu */}
        <Stack spacing={4} p="xs" mt="sm">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                component={Link}
                to={item.path}
                label={item.label}
                icon={item.icon}
                active={isActive}
                styles={{
                  root: {
                    borderRadius: "var(--mantine-radius-md)",
                    transition: "all 0.3s ease",
                    color: "white",
                    "&[data-active]": {
                      background: "linear-gradient(135deg, #00bcd4, #e91e63)",
                      color: "white",
                      boxShadow: "0 4px 15px rgba(0, 188, 212, 0.4)",
                      "&:hover": {
                        background: "linear-gradient(135deg, #0097a7, #c2185b)",
                        boxShadow: "0 6px 20px rgba(0, 188, 212, 0.6)",
                      },
                    },
                    "&:hover": {
                      background: "linear-gradient(135deg, rgba(0, 188, 212, 0.1), rgba(233, 30, 99, 0.1))",
                      border: "1px solid rgba(0, 188, 212, 0.3)",
                      transform: "translateX(4px)",
                    },
                  },
                  label: {
                    fontSize: "0.875rem",
                    fontWeight: isActive ? 600 : 400,
                  },
                  icon: {
                    color: "inherit",
                  },
                }}
              />
            );
          })}
        </Stack>

        {/* Quick Stats for Teachers/Admins */}
        {(role === "teacher" || role === "admin") && (
          <>
            <Divider color="rgba(255,255,255,0.1)" />
            <Box p="md">
              <Text size="xs" color="dimmed" mb="xs">
                QUICK STATS
              </Text>
              <Stack spacing={4}>
                <Group position="apart">
                  <Text size="xs">Active Classes</Text>
                  <Text size="xs" fw={600}>
                    4
                  </Text>
                </Group>
                <Group position="apart">
                  <Text size="xs">Total Students</Text>
                  <Text size="xs" fw={600}>
                    86
                  </Text>
                </Group>
                <Group position="apart">
                  <Text size="xs">Pending Tasks</Text>
                  <Text size="xs" fw={600}>
                    12
                  </Text>
                </Group>
              </Stack>
            </Box>
          </>
        )}
      </ScrollArea>
    </Drawer>
  );
}