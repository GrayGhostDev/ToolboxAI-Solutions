import * as React from "react";
import {
  Card,
  Text,
  Button,
  Stack,
  Switch,
  TextInput,
  Select,
  Checkbox,
  Radio,
  Divider,
  ActionIcon,
  Alert,
  Box,
  Tabs,
  Avatar,
  Badge,
  Grid,
  Group,
  Textarea
} from '@mantine/core';

import {
  IconUser,
  IconBell,
  IconShield,
  IconPalette,
  IconWorld,
  IconAccessible,
  IconDatabase,
  IconEdit,
  IconDeviceFloppy,
  IconX,
  IconCamera,
  IconTrash,
  IconDownload,
  IconKey,
  IconMail,
  IconDeviceMobile,
  IconSettings
} from "@tabler/icons-react";
import { useAppSelector, useAppDispatch } from "../../store";
import { setTheme } from "../../store/slices/uiSlice";

export default function Settings() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.user);
  const theme = useAppSelector((s) => s.ui.theme);
  const [activeTab, setActiveTab] = React.useState("0");
  const [editMode, setEditMode] = React.useState(false);
  const [adminSettings, setAdminSettings] = React.useState({
    agentDashboard: {
      teacherAccess: false,
      autoRefreshInterval: 30,
      maxConcurrentTasks: 10,
      enableResourceMonitoring: true,
      enableWorktreeCoordination: true,
    },
    systemLimits: {
      maxAgentsPerType: 5,
      taskQueueSize: 1000,
      enableAutoScaling: false,
      minAgents: 1,
      maxAgents: 10,
    },
  });
  const [profileData, setProfileData] = React.useState({
    displayName: (user as any).displayName || "John Doe",
    email: user.email || "john@example.com",
    phone: "+1 (555) 123-4567",
    bio: "Passionate educator dedicated to innovative learning",
    location: "San Francisco, CA",
    timezone: "PST",
  });

  const handleSaveProfile = () => {
    setEditMode(false);
    console.log("Saving profile:", profileData);
  };

  return (
    <Grid gutter="md">
      {/* Header */}
      <Grid.Col span={12}>
        <Card>
          <Group justify="space-between" align="center">
            <Text size="xl" fw={600}>
              Settings
            </Text>
            <Button leftSection={<IconDeviceFloppy size={16} />}>
              Save All Changes
            </Button>
          </Group>
        </Card>
      </Grid.Col>

      {/* Settings Tabs */}
      <Grid.Col span={12}>
        <Card>
          <Tabs value={activeTab} onTabChange={(value) => setActiveTab(value || "0")}>
            <Tabs.List>
              <Tabs.Tab value="0" leftSection={<IconUser size={16} />}>
                Profile
              </Tabs.Tab>
              <Tabs.Tab value="1" leftSection={<IconBell size={16} />}>
                Notifications
              </Tabs.Tab>
              <Tabs.Tab value="2" leftSection={<IconShield size={16} />}>
                Security
              </Tabs.Tab>
              <Tabs.Tab value="3" leftSection={<IconPalette size={16} />}>
                Appearance
              </Tabs.Tab>
              <Tabs.Tab value="4" leftSection={<IconWorld size={16} />}>
                Language
              </Tabs.Tab>
              <Tabs.Tab value="5" leftSection={<IconAccessible size={16} />}>
                Accessibility
              </Tabs.Tab>
              <Tabs.Tab value="6" leftSection={<IconDatabase size={16} />}>
                Data
              </Tabs.Tab>
              {user.role === "admin" && (
                <Tabs.Tab value="7" leftSection={<IconSettings size={16} />}>
                  Admin
                </Tabs.Tab>
              )}
            </Tabs.List>

            {/* Profile Tab */}
            <Tabs.Panel value="0" pt="md">
              <Grid gutter="md">
                <Grid.Col span={{ base: 12, md: 4 }}>
                  <Stack align="center" gap="md">
                    <Badge
                      variant="light"
                      size="xl"
                      style={{ position: "relative" }}
                    >
                      <Avatar
                        src={(user as any).avatarUrl}
                        size="xl"
                      >
                        {(user as any).displayName?.[0]}
                      </Avatar>
                      <ActionIcon
                        size="sm"
                        variant="filled"
                        style={{ position: "absolute", bottom: 0, right: 0 }}
                      >
                        <IconCamera size={14} />
                      </ActionIcon>
                    </Badge>
                    <Text size="lg" fw={600}>{profileData.displayName}</Text>
                    <Badge color="blue">{user.role}</Badge>
                    <Group gap="xs">
                      {!editMode ? (
                        <Button
                          variant="outline"
                          leftSection={<IconEdit size={16} />}
                          onClick={() => setEditMode(true)}
                        >
                          Edit Profile
                        </Button>
                      ) : (
                        <>
                          <Button
                            leftSection={<IconDeviceFloppy size={16} />}
                            onClick={handleSaveProfile}
                          >
                            Save
                          </Button>
                          <Button
                            variant="outline"
                            leftSection={<IconX size={16} />}
                            onClick={() => setEditMode(false)}
                          >
                            Cancel
                          </Button>
                        </>
                      )}
                    </Group>
                  </Stack>
                </Grid.Col>
                <Grid.Col span={{ base: 12, md: 8 }}>
                  <Stack gap="md">
                    <TextInput
                      label="Display Name"
                      value={profileData.displayName}
                      onChange={(e) => setProfileData({ ...profileData, displayName: e.target.value })}
                      disabled={!editMode}
                    />
                    <TextInput
                      label="Email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      disabled={!editMode}
                    />
                    <TextInput
                      label="Phone"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      disabled={!editMode}
                    />
                    <Textarea
                      label="Bio"
                      rows={3}
                      value={profileData.bio}
                      onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                      disabled={!editMode}
                    />
                    <Grid gutter="md">
                      <Grid.Col span={{ base: 12, md: 6 }}>
                        <TextInput
                          label="Location"
                          value={profileData.location}
                          onChange={(e) => setProfileData({ ...profileData, location: e.target.value })}
                          disabled={!editMode}
                        />
                      </Grid.Col>
                      <Grid.Col span={{ base: 12, md: 6 }}>
                        <Select
                          label="Timezone"
                          value={profileData.timezone}
                          onChange={(value) => setProfileData({ ...profileData, timezone: value || "PST" })}
                          disabled={!editMode}
                          data={[
                            { value: "PST", label: "PST" },
                            { value: "EST", label: "EST" },
                            { value: "CST", label: "CST" },
                            { value: "MST", label: "MST" },
                          ]}
                        />
                      </Grid.Col>
                    </Grid>
                  </Stack>
                </Grid.Col>
              </Grid>
            </Tabs.Panel>

            {/* Notifications Tab */}
            <Tabs.Panel value="1" pt="md">
              <Stack gap="md">
                <Alert color="blue">
                  <Text fw={600}>Notification Preferences</Text>
                  <Text size="sm">Choose how you want to receive notifications about important updates and activities.</Text>
                </Alert>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Email Notifications
                  </Text>
                  <Stack gap="sm">
                    <Checkbox defaultChecked label="New messages" />
                    <Checkbox defaultChecked label="Assignment updates" />
                    <Checkbox defaultChecked label="Grade posted" />
                    <Checkbox label="Weekly progress reports" />
                    <Checkbox label="System updates" />
                  </Stack>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Push Notifications
                  </Text>
                  <Stack gap="sm">
                    <Checkbox defaultChecked label="Direct messages" />
                    <Checkbox defaultChecked label="Class announcements" />
                    <Checkbox label="Achievement unlocked" />
                    <Checkbox label="Reminder for assignments" />
                  </Stack>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Notification Schedule
                  </Text>
                  <Radio.Group defaultValue="immediate">
                    <Stack gap="sm">
                      <Radio value="immediate" label="Immediately" />
                      <Radio value="hourly" label="Hourly digest" />
                      <Radio value="daily" label="Daily digest" />
                      <Radio value="weekly" label="Weekly digest" />
                    </Stack>
                  </Radio.Group>
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* Security Tab */}
            <Tabs.Panel value="2" pt="md">
              <Stack gap="md">
                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Password
                  </Text>
                  <Stack gap="md">
                    <Text size="sm" c="dimmed">
                      Last changed: 30 days ago
                    </Text>
                    <Button variant="outline" leftSection={<IconKey size={16} />}>
                      Change Password
                    </Button>
                  </Stack>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Two-Factor Authentication
                  </Text>
                  <Stack gap="md">
                    <Switch defaultChecked label="Enable two-factor authentication" />
                    <Group gap="md">
                      <Button variant="outline" leftSection={<IconDeviceMobile size={16} />}>
                        Configure Authenticator App
                      </Button>
                      <Button variant="outline" leftSection={<IconMail size={16} />}>
                        Configure Email 2FA
                      </Button>
                    </Group>
                  </Stack>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Active Sessions
                  </Text>
                  <Stack gap="md">
                    <Group justify="space-between" align="center">
                      <Box>
                        <Text fw={500}>Chrome on Windows</Text>
                        <Text size="sm" c="dimmed">San Francisco, CA • Active now</Text>
                      </Box>
                      <Badge color="green" size="sm">Current</Badge>
                    </Group>
                    <Group justify="space-between" align="center">
                      <Box>
                        <Text fw={500}>Safari on iPhone</Text>
                        <Text size="sm" c="dimmed">San Francisco, CA • 2 hours ago</Text>
                      </Box>
                      <Button size="sm" color="red">
                        Revoke
                      </Button>
                    </Group>
                  </Stack>
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* Appearance Tab */}
            <Tabs.Panel value="3" pt="md">
              <Stack gap="md">
                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Theme
                  </Text>
                  <Radio.Group
                    value={theme}
                    onChange={(value) => dispatch(setTheme(value as any))}
                  >
                    <Stack gap="sm">
                      <Radio value="light" label="Light" />
                      <Radio value="dark" label="Dark" />
                      <Radio value="auto" label="System default" />
                    </Stack>
                  </Radio.Group>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Color Scheme
                  </Text>
                  <Group gap="md">
                    {["#2563EB", "#9333EA", "#22C55E", "#EF4444", "#F59E0B"].map((color) => (
                      <Box
                        key={color}
                        style={{
                          width: 40,
                          height: 40,
                          backgroundColor: color,
                          borderRadius: 8,
                          cursor: "pointer",
                          border: "2px solid transparent",
                        }}
                      />
                    ))}
                  </Group>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Display Options
                  </Text>
                  <Stack gap="sm">
                    <Switch defaultChecked label="Show animations" />
                    <Switch defaultChecked label="Compact mode" />
                    <Switch label="High contrast" />
                  </Stack>
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* Language Tab */}
            <Tabs.Panel value="4" pt="md">
              <Stack gap="md">
                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Language Preference
                  </Text>
                  <Select
                    label="Language"
                    defaultValue="en"
                    data={[
                      { value: "en", label: "English" },
                      { value: "es", label: "Español" },
                      { value: "fr", label: "Français" },
                      { value: "de", label: "Deutsch" },
                      { value: "zh", label: "中文" },
                      { value: "ja", label: "日本語" },
                    ]}
                  />
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Regional Settings
                  </Text>
                  <Stack gap="md">
                    <Select
                      label="Date Format"
                      defaultValue="mm/dd/yyyy"
                      data={[
                        { value: "mm/dd/yyyy", label: "MM/DD/YYYY" },
                        { value: "dd/mm/yyyy", label: "DD/MM/YYYY" },
                        { value: "yyyy-mm-dd", label: "YYYY-MM-DD" },
                      ]}
                    />
                    <Select
                      label="Time Format"
                      defaultValue="12h"
                      data={[
                        { value: "12h", label: "12-hour" },
                        { value: "24h", label: "24-hour" },
                      ]}
                    />
                  </Stack>
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* Accessibility Tab */}
            <Tabs.Panel value="5" pt="md">
              <Stack gap="md">
                <Alert color="blue">
                  <Text fw={600}>Accessibility Features</Text>
                  <Text size="sm">Customize the platform to meet your accessibility needs.</Text>
                </Alert>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Visual
                  </Text>
                  <Stack gap="sm">
                    <Switch label="Large text" />
                    <Switch label="High contrast" />
                    <Switch label="Reduce motion" />
                    <Switch label="Screen reader optimization" />
                  </Stack>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Keyboard Navigation
                  </Text>
                  <Stack gap="sm">
                    <Switch defaultChecked label="Enable keyboard shortcuts" />
                    <Switch label="Show focus indicators" />
                    <Switch label="Tab navigation hints" />
                  </Stack>
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* Data Tab */}
            <Tabs.Panel value="6" pt="md">
              <Stack gap="md">
                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Data Management
                  </Text>
                  <Stack gap="md">
                    <Button variant="outline" leftSection={<IconDownload size={16} />}>
                      Download My Data
                    </Button>
                    <Button variant="outline" color="red" leftSection={<IconTrash size={16} />}>
                      Delete My Account
                    </Button>
                  </Stack>
                </Card>

                <Card variant="outline">
                  <Text size="lg" fw={600} mb="md">
                    Privacy Settings
                  </Text>
                  <Stack gap="sm">
                    <Switch defaultChecked label="Allow analytics" />
                    <Switch label="Share progress with parents" />
                    <Switch defaultChecked label="Show on leaderboards" />
                  </Stack>
                </Card>
              </Stack>
            </Tabs.Panel>

            {/* Admin Settings Tab - Only visible to admins */}
            {user.role === "admin" && (
              <Tabs.Panel value="7" pt="md">
                <Stack gap="md">
                  <Alert color="yellow">
                    <Text fw={600}>Administrator Settings</Text>
                    <Text size="sm">These settings affect system-wide behavior and should be changed carefully.</Text>
                  </Alert>

                  <Card variant="outline">
                    <Text size="lg" fw={600} mb="md">
                      Agent Dashboard Access
                    </Text>
                    <Stack gap="md">
                      <Switch
                        checked={adminSettings.agentDashboard.teacherAccess}
                        onChange={(e) =>
                          setAdminSettings({
                            ...adminSettings,
                            agentDashboard: {
                              ...adminSettings.agentDashboard,
                              teacherAccess: e.currentTarget.checked,
                            },
                          })
                        }
                        label="Allow teachers to access Agent Dashboard"
                        description="When enabled, teachers will see the Agent System option in their navigation menu"
                      />

                      <Divider />

                      <Text size="md" fw={600}>
                        Agent Dashboard Configuration
                      </Text>
                      <Stack gap="md">
                        <TextInput
                          type="number"
                          label="Auto-refresh Interval (seconds)"
                          value={adminSettings.agentDashboard.autoRefreshInterval}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              agentDashboard: {
                                ...adminSettings.agentDashboard,
                                autoRefreshInterval: parseInt(e.target.value) || 30,
                              },
                            })
                          }
                          min={5}
                          max={300}
                          description="How often the dashboard should refresh data"
                        />
                        <TextInput
                          type="number"
                          label="Max Concurrent Tasks"
                          value={adminSettings.agentDashboard.maxConcurrentTasks}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              agentDashboard: {
                                ...adminSettings.agentDashboard,
                                maxConcurrentTasks: parseInt(e.target.value) || 10,
                              },
                            })
                          }
                          min={1}
                          max={50}
                          description="Maximum number of tasks that can run simultaneously"
                        />
                        <Switch
                          checked={adminSettings.agentDashboard.enableResourceMonitoring}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              agentDashboard: {
                                ...adminSettings.agentDashboard,
                                enableResourceMonitoring: e.currentTarget.checked,
                              },
                            })
                          }
                          label="Enable Resource Monitoring"
                        />
                        <Switch
                          checked={adminSettings.agentDashboard.enableWorktreeCoordination}
                          onChange={(e) =>
                            setAdminSettings({
                              ...adminSettings,
                              agentDashboard: {
                                ...adminSettings.agentDashboard,
                                enableWorktreeCoordination: e.currentTarget.checked,
                              },
                            })
                          }
                          label="Enable Worktree Coordination"
                        />
                      </Stack>
                    </Stack>
                  </Card>

                  <Card variant="outline">
                    <Text size="lg" fw={600} mb="md">
                      System Limits
                    </Text>
                    <Stack gap="md">
                      <TextInput
                        type="number"
                        label="Max Agents Per Type"
                        value={adminSettings.systemLimits.maxAgentsPerType}
                        onChange={(e) =>
                          setAdminSettings({
                            ...adminSettings,
                            systemLimits: {
                              ...adminSettings.systemLimits,
                              maxAgentsPerType: parseInt(e.target.value) || 5,
                            },
                          })
                        }
                        min={1}
                        max={20}
                        description="Maximum number of agents of each type that can be created"
                      />
                      <TextInput
                        type="number"
                        label="Task Queue Size"
                        value={adminSettings.systemLimits.taskQueueSize}
                        onChange={(e) =>
                          setAdminSettings({
                            ...adminSettings,
                            systemLimits: {
                              ...adminSettings.systemLimits,
                              taskQueueSize: parseInt(e.target.value) || 1000,
                            },
                          })
                        }
                        min={100}
                        max={10000}
                        description="Maximum number of tasks that can be queued"
                      />

                      <Divider />

                      <Text size="md" fw={600}>Auto-scaling</Text>
                      <Switch
                        checked={adminSettings.systemLimits.enableAutoScaling}
                        onChange={(e) =>
                          setAdminSettings({
                            ...adminSettings,
                            systemLimits: {
                              ...adminSettings.systemLimits,
                              enableAutoScaling: e.currentTarget.checked,
                            },
                          })
                        }
                        label="Enable Auto-scaling"
                      />
                      {adminSettings.systemLimits.enableAutoScaling && (
                        <Grid gutter="md">
                          <Grid.Col span={6}>
                            <TextInput
                              type="number"
                              label="Min Agents"
                              value={adminSettings.systemLimits.minAgents}
                              onChange={(e) =>
                                setAdminSettings({
                                  ...adminSettings,
                                  systemLimits: {
                                    ...adminSettings.systemLimits,
                                    minAgents: parseInt(e.target.value) || 1,
                                  },
                                })
                              }
                              min={1}
                              max={10}
                            />
                          </Grid.Col>
                          <Grid.Col span={6}>
                            <TextInput
                              type="number"
                              label="Max Agents"
                              value={adminSettings.systemLimits.maxAgents}
                              onChange={(e) =>
                                setAdminSettings({
                                  ...adminSettings,
                                  systemLimits: {
                                    ...adminSettings.systemLimits,
                                    maxAgents: parseInt(e.target.value) || 10,
                                  },
                                })
                              }
                              min={1}
                              max={50}
                            />
                          </Grid.Col>
                        </Grid>
                      )}
                    </Stack>
                  </Card>

                  <Group justify="flex-end" gap="md">
                    <Button variant="outline" onClick={() => window.location.reload()}>
                      Reset to Defaults
                    </Button>
                    <Button
                      leftSection={<IconDeviceFloppy size={16} />}
                      onClick={() => {
                        // Save admin settings to backend
                        console.log("Saving admin settings:", adminSettings);
                        // TODO: Call API to save settings
                      }}
                    >
                      Save Admin Settings
                    </Button>
                  </Group>
                </Stack>
              </Tabs.Panel>
            )}
          </Tabs>
        </Card>
      </Grid.Col>
    </Grid>
  );
}