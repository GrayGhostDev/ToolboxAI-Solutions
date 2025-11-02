import React, { useState } from 'react';
import { Text, Box, Tabs, Paper, Badge } from '@mantine/core';
import {
  IconUsers,
  IconSchool,
  IconSettings,
  IconHistory,
  IconChartBar,
  IconShield,
  IconDatabase,
  IconPlugConnected,
} from '@tabler/icons-react';
import UserManagement from './UserManagement';
import Schools from './Schools';
import SystemSettings from './SystemSettings';
import ActivityLogs from './ActivityLogs';

interface TabPanelProps {
  children?: React.ReactNode;
  value: string;
}

function TabPanel(props: TabPanelProps) {
  const { children } = props;
  return <Box pt="lg">{children}</Box>;
}

const AdminControlPanel: React.FunctionComponent<Record<string, any>> = () => {
  const [activeTab, setActiveTab] = useState<string | null>('users');

  const tabs = [
    { value: 'users', label: 'Users', icon: <IconUsers size={16} /> },
    { value: 'schools', label: 'Schools', icon: <IconSchool size={16} /> },
    { value: 'settings', label: 'System Settings', icon: <IconSettings size={16} /> },
    { value: 'integrations', label: 'Integrations', icon: <IconPlugConnected size={16} /> },
    { value: 'security', label: 'Security', icon: <IconShield size={16} />, badge: '3' },
    { value: 'logs', label: 'Activity Logs', icon: <IconHistory size={16} />, badge: 'New' },
    { value: 'analytics', label: 'Analytics', icon: <IconChartBar size={16} /> },
    { value: 'storage', label: 'Storage', icon: <IconDatabase size={16} /> },
  ];

  return (
    <Box w="100%">
      <Text size="xl" fw={600} mb="lg">
        Admin Control Panel
      </Text>

      <Paper>
        <Tabs
          value={activeTab}
          onChange={setActiveTab}
          orientation="vertical"
          keepMounted={false}
        >
          <Box
            style={{
              display: 'flex',
              gap: 'var(--mantine-spacing-lg)',
              alignItems: 'flex-start',
            }}
          >
            <Tabs.List
              style={{
                minWidth: '220px',
                maxWidth: '260px',
                borderRight: '1px solid var(--mantine-color-gray-3)',
                padding: 'var(--mantine-spacing-md)',
                gap: '8px',
              }}
            >
              {tabs.map((tab) => (
                <Tabs.Tab
                  key={tab.value}
                  value={tab.value}
                  leftSection={tab.icon}
                  rightSection={
                    tab.badge && (
                      <Badge
                        size="xs"
                        color={tab.badge === 'New' ? 'blue' : 'red'}
                      >
                        {tab.badge}
                      </Badge>
                    )
                  }
                  style={{ justifyContent: 'space-between' }}
                >
                  {tab.label}
                </Tabs.Tab>
              ))}
            </Tabs.List>

            <Box style={{ flex: 1 }}>
              <Tabs.Panel value="users">
                <TabPanel value="users">
                  <UserManagement />
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="schools">
                <TabPanel value="schools">
                  <Schools />
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="settings">
                <TabPanel value="settings">
                  <SystemSettings />
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="integrations">
                <TabPanel value="integrations">
                  <Box p="lg">
                    <Text size="lg" fw={500} mb="xs">
                      Integrations Management
                    </Text>
                    <Text c="dimmed" mb="lg">
                      Configure and manage third-party integrations including LMS systems, authentication providers, and API connections.
                    </Text>

                    <Box mt="lg">
                      {/* Integration cards */}
                      <Paper p="md" mb="md">
                        <Text fw={500}>Canvas LMS</Text>
                        <Badge color="green" size="sm" mt="xs">
                          Connected
                        </Badge>
                        <Text size="sm" mt="xs">
                          Last sync: 2 hours ago
                        </Text>
                      </Paper>

                      <Paper p="md" mb="md">
                        <Text fw={500}>Schoology</Text>
                        <Badge color="red" size="sm" mt="xs">
                          Disconnected
                        </Badge>
                        <Text size="sm" mt="xs">
                          Click to configure
                        </Text>
                      </Paper>

                      <Paper p="md" mb="md">
                        <Text fw={500}>Google Classroom</Text>
                        <Badge color="orange" size="sm" mt="xs">
                          Pending
                        </Badge>
                        <Text size="sm" mt="xs">
                          Authentication required
                        </Text>
                      </Paper>
                    </Box>
                  </Box>
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="security">
                <TabPanel value="security">
                  <Box p="lg">
                    <Text size="lg" fw={500} mb="xs">
                      Security Settings
                    </Text>
                    <Text c="dimmed" mb="lg">
                      Manage security policies, authentication settings, and compliance requirements.
                    </Text>

                    <Box mt="lg">
                      <Paper p="lg" mb="md">
                        <Text fw={500} mb="sm">
                          Security Alerts
                        </Text>
                        <Badge color="red" mb="md">
                          3 new alerts
                        </Badge>
                        <Box mt="md">
                          <Text size="sm" c="red">
                            • 5 failed login attempts from IP 192.168.1.100
                          </Text>
                          <Text size="sm" c="orange">
                            • Password policy update required
                          </Text>
                          <Text size="sm" c="blue">
                            • SSL certificate expires in 30 days
                          </Text>
                        </Box>
                      </Paper>

                      <Paper p="lg" mb="md">
                        <Text fw={500} mb="sm">
                          Compliance Status
                        </Text>
                        <Box style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                          <Badge color="green">FERPA Compliant</Badge>
                          <Badge color="green">COPPA Compliant</Badge>
                          <Badge color="orange">GDPR Ready</Badge>
                        </Box>
                      </Paper>
                    </Box>
                  </Box>
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="logs">
                <TabPanel value="logs">
                  <ActivityLogs />
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="analytics">
                <TabPanel value="analytics">
                  <Box p="lg">
                    <Text size="lg" fw={500} mb="xs">
                      Platform Analytics
                    </Text>
                    <Text c="dimmed" mb="lg">
                      View detailed analytics about platform usage, performance metrics, and user engagement.
                    </Text>

                    <Box mt="lg" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
                      <Paper p="lg">
                        <Text size="xl" fw={700}>1,234</Text>
                        <Text size="sm" c="dimmed">
                          Total Users
                        </Text>
                      </Paper>

                      <Paper p="lg">
                        <Text size="xl" fw={700}>456</Text>
                        <Text size="sm" c="dimmed">
                          Active Sessions
                        </Text>
                      </Paper>

                      <Paper p="lg">
                        <Text size="xl" fw={700}>89%</Text>
                        <Text size="sm" c="dimmed">
                          System Uptime
                        </Text>
                      </Paper>

                      <Paper p="lg">
                        <Text size="xl" fw={700}>2.3s</Text>
                        <Text size="sm" c="dimmed">
                          Avg Response Time
                        </Text>
                      </Paper>
                    </Box>
                  </Box>
                </TabPanel>
              </Tabs.Panel>

              <Tabs.Panel value="storage">
                <TabPanel value="storage">
                  <Box p="lg">
                    <Text size="lg" fw={500} mb="xs">
                      Storage Management
                    </Text>
                    <Text c="dimmed" mb="lg">
                      Monitor and manage storage usage across the platform.
                    </Text>

                    <Box mt="lg">
                      <Paper p="lg">
                        <Text fw={500} mb="sm">
                          Storage Usage
                        </Text>
                        <Box mt="md">
                          <Text size="sm">
                            Used: 45.2 GB / 100 GB (45.2%)
                          </Text>
                          <Box style={{
                            width: '100%',
                            height: '20px',
                            backgroundColor: 'var(--mantine-color-gray-2)',
                            borderRadius: 'var(--mantine-radius-sm)',
                            marginTop: '8px',
                            position: 'relative',
                            overflow: 'hidden'
                          }}>
                            <Box style={{
                              width: '45.2%',
                              height: '100%',
                              backgroundColor: 'var(--mantine-color-blue-6)',
                              borderRadius: 'var(--mantine-radius-sm)'
                            }} />
                          </Box>
                        </Box>

                        <Box mt="lg">
                          <Text fw={500} mb="sm">
                            Storage Breakdown
                          </Text>
                          <Text size="sm">• User Files: 25.3 GB</Text>
                          <Text size="sm">• Course Content: 12.8 GB</Text>
                          <Text size="sm">• System Files: 5.1 GB</Text>
                          <Text size="sm">• Backups: 2.0 GB</Text>
                        </Box>
                      </Paper>
                    </Box>
                  </Box>
                </TabPanel>
              </Tabs.Panel>
            </Box>
          </Box>
        </Tabs>
      </Paper>
    </Box>
  );
};

export default AdminControlPanel;