import {
  Title,
  Text,
  Button,
  Card,
  Grid,
  Stack,
  Progress,
  RingProgress,
  Badge,
  Table,
  Modal,
  Tabs,
  TextInput,
  Select,
  ActionIcon,
  Skeleton,
  Alert,
  Box,
  ScrollArea,
  Group
} from '@mantine/core';
import {
  IconShield,
  IconRefresh,
  IconSettings,
  IconDownload,
  IconAlertTriangle,
  IconInfoCircle,
  IconCircleCheck,
  IconUser,
  IconUsers,
  IconCheck,
  IconX
} from '@tabler/icons-react';
import * as React from 'react';

import { useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import {
  fetchComplianceStatus,
  fetchAuditLogs,
  fetchConsentRecords,
  recordConsent,
  revokeConsent,
  runComplianceAudit,
  exportComplianceReport,
  clearError,
} from '../../store/slices/complianceSlice';


export default function Compliance() {
  const dispatch = useAppDispatch();
  const role = useAppSelector((s) => s.user.role);
  const { 
    status, 
    auditLogs, 
    consentRecords, 
    pendingConsents, 
    overallScore, 
    loading, 
    error, 
    lastChecked 
  } = useAppSelector((s) => s.compliance);
  
  const [activeTab, setActiveTab] = React.useState('0');
  const [consentDialogOpen, setConsentDialogOpen] = React.useState(false);
  const [auditDialogOpen, setAuditDialogOpen] = React.useState(false);
  const [selectedRegulation, setSelectedRegulation] = React.useState<string>('');
  const [consentFormData, setConsentFormData] = React.useState({
    studentId: '',
    parentName: '',
    parentEmail: '',
    consentType: 'coppa' as 'coppa' | 'ferpa' | 'gdpr',
  });

  // Fetch compliance data on mount
  useEffect(() => {
    dispatch(fetchComplianceStatus());
    dispatch(fetchAuditLogs());
    dispatch(fetchConsentRecords());
  }, [dispatch]);

  // Auto-refresh compliance status every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      dispatch(fetchComplianceStatus());
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [dispatch]);


  const handleRefresh = () => {
    dispatch(fetchComplianceStatus());
    dispatch(fetchAuditLogs());
    dispatch(fetchConsentRecords());
  };

  const handleRecordConsent = async () => {
    const { studentId, consentType } = consentFormData;
    await dispatch(recordConsent({ 
      type: consentType, 
      userId: studentId,
      signature: 'digital_signature_placeholder'
    }));
    setConsentDialogOpen(false);
    setConsentFormData({
      studentId: '',
      parentName: '',
      parentEmail: '',
      consentType: 'coppa',
    });
  };

  const handleRevokeConsent = async (consentId: string) => {
    if (window.confirm('Are you sure you want to revoke this consent?')) {
      await dispatch(revokeConsent(consentId));
    }
  };

  const handleRunAudit = async () => {
    const regulation = selectedRegulation || 'all';
    await dispatch(runComplianceAudit(regulation as any));
    setAuditDialogOpen(false);
  };

  const handleExportReport = async (format: 'pdf' | 'csv' | 'json') => {
    const result = await dispatch(exportComplianceReport(format));
    if (exportComplianceReport.fulfilled.match(result)) {
      // Download the file
      window.open(result.payload.url, '_blank');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <IconCircleCheck color="green" />;
      case 'warning':
        return <IconAlertTriangle color="yellow" />;
      case 'violation':
        return <IconX color="red" />;
      default:
        return <IconInfoCircle color="cyan" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'success';
      case 'warning':
        return 'warning';
      case 'violation':
        return 'error';
      default:
        return 'default';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'success.main';
    if (score >= 70) return 'warning.main';
    return 'error.main';
  };

  return (
    <Grid>
      {/* Header */}
      <Grid.Col span={12}>
        <Card withBorder>
          <Stack p="md" gap="md">
            <Group justify="center" gap="md">
              <IconShield size={32} color="var(--mantine-color-blue-6)" />
              <Box>
                <Title order={3} size="lg">
                  Compliance Dashboard
                </Title>
                <Text size="sm" c="dimmed">
                  Last checked: {lastChecked ? new Date(lastChecked).toLocaleString() : 'Never'}
                </Text>
              </Box>
            </Group>
            <Group gap="sm" justify="center">
              <Button
                variant="outline"
                leftSection={<IconRefresh size={16} />}
                onClick={handleRefresh}
                loading={loading}
              >
                Refresh
              </Button>
              {role === 'admin' && (
                <>
                  <Button
                    variant="outline"
                    leftSection={<IconSettings size={16} />}
                    onClick={() => setAuditDialogOpen(true)}
                  >
                    Run Audit
                  </Button>
                  <Button
                    variant="filled"
                    leftSection={<IconDownload size={16} />}
                    onClick={() => handleExportReport('pdf')}
                  >
                    Export Report
                  </Button>
                </>
              )}
            </Group>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Overall Score Card */}
      <Grid.Col span={{ base: 12, md: 4 }}>
        <Card withBorder p="md">
          <Stack align="center" gap="md">
            <Text size="md" c="dimmed">
              Overall Compliance Score
            </Text>
            <RingProgress
              size={120}
              thickness={8}
              sections={[
                { value: overallScore, color: overallScore >= 90 ? 'green' : overallScore >= 70 ? 'orange' : 'red' }
              ]}
              label={
                <Text ta="center" fw={700} size="lg">
                  {overallScore}%
                </Text>
              }
            />
            <Badge
              color={overallScore >= 90 ? 'green' : overallScore >= 70 ? 'orange' : 'red'}
              size="lg"
            >
              {overallScore >= 90 ? 'Excellent' : overallScore >= 70 ? 'Good' : 'Needs Improvement'}
            </Badge>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Pending Actions Card */}
      <Grid.Col span={{ base: 12, md: 4 }}>
        <Card withBorder p="md">
          <Stack gap="md">
            <Title order={6} c="dimmed">
              Pending Actions
            </Title>
            <Stack gap="sm">
              <Group justify="space-between" align="center">
                <Group gap="sm">
                  <IconUsers color="var(--mantine-color-yellow-6)" />
                  <Box>
                    <Text fw={500}>Parent Consents</Text>
                    <Text size="sm" c="dimmed">{pendingConsents} pending</Text>
                  </Box>
                </Group>
                {pendingConsents > 0 && (
                  <Button size="xs" onClick={() => setConsentDialogOpen(true)}>
                    Review
                  </Button>
                )}
              </Group>
              <Group justify="space-between" align="center">
                <Group gap="sm">
                  <IconShield color="var(--mantine-color-cyan-6)" />
                  <Box>
                    <Text fw={500}>Policy Updates</Text>
                    <Text size="sm" c="dimmed">0 required</Text>
                  </Box>
                </Group>
              </Group>
              <Group justify="space-between" align="center">
                <Group gap="sm">
                  <IconAlertTriangle color="var(--mantine-color-red-6)" />
                  <Box>
                    <Text fw={500}>Compliance Issues</Text>
                    <Text size="sm" c="dimmed">{pendingConsents} to resolve</Text>
                  </Box>
                </Group>
              </Group>
            </Stack>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Quick Actions Card */}
      <Grid.Col span={{ base: 12, md: 4 }}>
        <Card withBorder p="md">
          <Stack gap="md">
            <Title order={6} c="dimmed">
              Quick Actions
            </Title>
            <Stack gap="sm">
              <Button
                fullWidth
                variant="outline"
                leftSection={<IconUser />}
                onClick={() => setConsentDialogOpen(true)}
              >
                Record Consent
              </Button>
              <Button
                fullWidth
                variant="outline"
                leftSection={<IconDownload />}
                onClick={() => handleExportReport('csv')}
              >
                Download Data
              </Button>
              <Button
                fullWidth
                variant="outline"
                leftSection={<IconSettings />}
                onClick={() => setActiveTab('3')}
              >
                Settings
              </Button>
            </Stack>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Compliance Status Cards */}
      <Grid.Col span={12}>
        <Card withBorder p="md">
          <Stack gap="md">
            <Title order={6} mb="sm">
              Regulatory Compliance
            </Title>
            <Grid>
              {status && Object.entries(status)
                .filter(([key]) => ['coppa', 'ferpa', 'gdpr'].includes(key))
                .map(([regulation, data]) => (
                <Grid.Col key={regulation} span={{ base: 12, sm: 6, md: 3 }}>
                  <Card withBorder p="md">
                    <Stack gap="sm">
                      <Group justify="space-between" align="center">
                        <Title order={6}>
                          {regulation.toUpperCase()}
                        </Title>
                        {getStatusIcon(data.status)}
                      </Group>
                      <Progress
                        value={data.score}
                        color={data.score >= 90 ? 'green' : data.score >= 70 ? 'orange' : 'red'}
                        size="md"
                        radius="md"
                      />
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">
                          Score: {data.score}%
                        </Text>
                        <Badge
                          color={getStatusColor(data.status) === 'success' ? 'green' :
                                 getStatusColor(data.status) === 'warning' ? 'orange' : 'red'}
                          size="sm"
                        >
                          {data.status}
                        </Badge>
                      </Group>
                      {data.issues.length > 0 && (
                        <Alert color="yellow" title={`${data.issues.length} Issues`} />
                      )}
                      <Text size="xs" c="dimmed">
                        Last audit: {new Date(data.lastAudit).toLocaleDateString()}
                      </Text>
                    </Stack>
                  </Card>
                </Grid.Col>
              ))}
              {loading && !status && (
                [...Array(4)].map((_, i) => (
                  <Grid.Col key={i} span={{ base: 12, sm: 6, md: 3 }}>
                    <Skeleton height={200} />
                  </Grid.Col>
                ))
              )}
            </Grid>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Tabbed Content */}
      <Grid.Col span={12}>
        <Card withBorder>
          <Tabs value={activeTab} onChange={(value) => setActiveTab(value || '0')}>
            <Tabs.List>
              <Tabs.Tab value="0">Audit Logs</Tabs.Tab>
              <Tabs.Tab value="1">Consent Records</Tabs.Tab>
              <Tabs.Tab value="2">Data Retention</Tabs.Tab>
              <Tabs.Tab value="3">Settings</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="0" p="md">
              <ScrollArea>
                <Table striped>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Timestamp</Table.Th>
                      <Table.Th>Action</Table.Th>
                      <Table.Th>User</Table.Th>
                      <Table.Th>Regulation</Table.Th>
                      <Table.Th>Status</Table.Th>
                      <Table.Th>Details</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {auditLogs.map((log) => (
                      <Table.Tr key={log.id}>
                        <Table.Td>{new Date(log.timestamp).toLocaleString()}</Table.Td>
                        <Table.Td>{log.action}</Table.Td>
                        <Table.Td>{log.userEmail}</Table.Td>
                        <Table.Td>
                          <Badge size="sm">{log.regulation}</Badge>
                        </Table.Td>
                        <Table.Td>
                          <Badge
                            color={log.status === 'Approved' ? 'green' : 'gray'}
                            size="sm"
                          >
                            {log.status}
                          </Badge>
                        </Table.Td>
                        <Table.Td>{log.details}</Table.Td>
                      </Table.Tr>
                    ))}
                    {auditLogs.length === 0 && (
                      <Table.Tr>
                        <Table.Td colSpan={6} ta="center">
                          No audit logs available
                        </Table.Td>
                      </Table.Tr>
                    )}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Tabs.Panel>

            <Tabs.Panel value="1" p="md">
              <ScrollArea>
                <Table striped>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Student</Table.Th>
                      <Table.Th>Parent</Table.Th>
                      <Table.Th>Type</Table.Th>
                      <Table.Th>Status</Table.Th>
                      <Table.Th>Date Provided</Table.Th>
                      <Table.Th>Expiry Date</Table.Th>
                      <Table.Th>Actions</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {consentRecords.map((consent) => (
                      <Table.Tr key={consent.id}>
                        <Table.Td>{consent.studentName}</Table.Td>
                        <Table.Td>{consent.parentName || 'N/A'}</Table.Td>
                        <Table.Td>
                          <Badge size="sm">{consent.consentType.toUpperCase()}</Badge>
                        </Table.Td>
                        <Table.Td>
                          <Badge
                            color={
                              consent.status === 'active'
                                ? 'green'
                                : consent.status === 'expired'
                                ? 'orange'
                                : 'red'
                            }
                            size="sm"
                          >
                            {consent.status}
                          </Badge>
                        </Table.Td>
                        <Table.Td>{new Date(consent.dateProvided).toLocaleDateString()}</Table.Td>
                        <Table.Td>
                          {consent.expiryDate
                            ? new Date(consent.expiryDate).toLocaleDateString()
                            : 'N/A'}
                        </Table.Td>
                        <Table.Td>
                          {consent.status === 'active' && (
                            <ActionIcon
                              size="sm"
                              color="red"
                              variant="subtle"
                              onClick={() => handleRevokeConsent(consent.id)}
                            >
                              <IconX size={16} />
                            </ActionIcon>
                          )}
                        </Table.Td>
                      </Table.Tr>
                    ))}
                    {consentRecords.length === 0 && (
                      <Table.Tr>
                        <Table.Td colSpan={7} ta="center">
                          No consent records available
                        </Table.Td>
                      </Table.Tr>
                    )}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Tabs.Panel>

            <Tabs.Panel value="2" p="md">
              <Stack gap="md">
                <Alert color="blue" title="Data Retention Policy">
                  All student data is retained according to regulatory requirements.
                  Data is automatically purged after the retention period expires.
                </Alert>
                <ScrollArea>
                  <Table striped>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Data Type</Table.Th>
                        <Table.Th>Retention Period</Table.Th>
                        <Table.Th>Next Purge</Table.Th>
                        <Table.Th>Status</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td>Student Records</Table.Td>
                        <Table.Td>5 years</Table.Td>
                        <Table.Td>2029-01-01</Table.Td>
                        <Table.Td>
                          <Badge color="green" size="sm">Active</Badge>
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Assessment Data</Table.Td>
                        <Table.Td>3 years</Table.Td>
                        <Table.Td>2027-01-01</Table.Td>
                        <Table.Td>
                          <Badge color="green" size="sm">Active</Badge>
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td>Activity Logs</Table.Td>
                        <Table.Td>1 year</Table.Td>
                        <Table.Td>2025-01-01</Table.Td>
                        <Table.Td>
                          <Badge color="green" size="sm">Active</Badge>
                        </Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>
                </ScrollArea>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="3" p="md">
              <Stack gap="lg">
                <Alert color="yellow" title="Settings">
                  Changes to compliance settings require administrator approval.
                </Alert>
                <Select
                  label="Auto-Audit Frequency"
                  value="monthly"
                  data={[
                    { value: 'weekly', label: 'Weekly' },
                    { value: 'monthly', label: 'Monthly' },
                    { value: 'quarterly', label: 'Quarterly' }
                  ]}
                />
                <Select
                  label="Data Retention Period"
                  value="5years"
                  data={[
                    { value: '1year', label: '1 Year' },
                    { value: '3years', label: '3 Years' },
                    { value: '5years', label: '5 Years' },
                    { value: '7years', label: '7 Years' }
                  ]}
                />
                <Group gap="sm">
                  <Button variant="filled" disabled>
                    Save Settings
                  </Button>
                  <Button variant="outline">Cancel</Button>
                </Group>
              </Stack>
            </Tabs.Panel>
          </Tabs>
        </Card>
      </Grid.Col>

      {/* Record Consent Modal */}
      <Modal
        opened={consentDialogOpen}
        onClose={() => setConsentDialogOpen(false)}
        title="Record Parent Consent"
        size="sm"
      >
        <Stack gap="md" mt="md">
          <TextInput
            label="Student ID"
            value={consentFormData.studentId}
            onChange={(e) => setConsentFormData({ ...consentFormData, studentId: e.target.value })}
          />
          <TextInput
            label="Parent Name"
            value={consentFormData.parentName}
            onChange={(e) => setConsentFormData({ ...consentFormData, parentName: e.target.value })}
          />
          <TextInput
            label="Parent Email"
            type="email"
            value={consentFormData.parentEmail}
            onChange={(e) => setConsentFormData({ ...consentFormData, parentEmail: e.target.value })}
          />
          <Select
            label="Consent Type"
            value={consentFormData.consentType}
            onChange={(value) => setConsentFormData({ ...consentFormData, consentType: value as any })}
            data={[
              { value: 'coppa', label: 'COPPA' },
              { value: 'ferpa', label: 'FERPA' },
              { value: 'gdpr', label: 'GDPR' }
            ]}
          />
        </Stack>
        <Group justify="flex-end" mt="lg">
          <Button variant="outline" onClick={() => setConsentDialogOpen(false)}>Cancel</Button>
          <Button variant="filled" onClick={handleRecordConsent}>
            Record Consent
          </Button>
        </Group>
      </Modal>

      {/* Run Audit Modal */}
      <Modal
        opened={auditDialogOpen}
        onClose={() => setAuditDialogOpen(false)}
        title="Run Compliance Audit"
        size="sm"
      >
        <Stack gap="md" mt="md">
          <Alert color="blue">
            Running an audit will check all compliance requirements and update the status.
          </Alert>
          <Select
            label="Regulation"
            value={selectedRegulation}
            onChange={(value) => setSelectedRegulation(value || '')}
            data={[
              { value: '', label: 'All Regulations' },
              { value: 'coppa', label: 'COPPA' },
              { value: 'ferpa', label: 'FERPA' },
              { value: 'gdpr', label: 'GDPR' }
            ]}
          />
        </Stack>
        <Group justify="flex-end" mt="lg">
          <Button variant="outline" onClick={() => setAuditDialogOpen(false)}>Cancel</Button>
          <Button variant="filled" onClick={handleRunAudit} leftSection={<IconCheck />}>
            Run Audit
          </Button>
        </Group>
      </Modal>

      {/* Error Alert */}
      {error && (
        <Grid.Col span={12}>
          <Alert color="red" title="Error" withCloseButton onClose={() => dispatch(clearError())}>
            {error}
          </Alert>
        </Grid.Col>
      )}
    </Grid>
  );
}
