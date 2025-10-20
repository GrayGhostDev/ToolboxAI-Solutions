/**
 * ContentModerationPanel Component
 * Content moderation and review interface for administrators
 */

import { memo, useState, useEffect, type ChangeEvent } from 'react';
import {
  Box,
  Paper,
  Text,
  Button,
  Stack,
  TextInput,
  Select,
  Modal,
  Alert,
  Tooltip,
  Checkbox,
  Card,
  Grid,
  Tabs,
  Badge,
  Avatar,
  ActionIcon,
  Group,
  Divider,
  useMantineTheme,
  Progress,
} from '@mantine/core';
import {
  IconSearch,
  IconCheck,
  IconX,
  IconEye,
  IconTrash,
  IconInfoCircle,
  IconSchool,
  IconClipboardList,
  IconMessage,
  IconPhoto,
  IconVideo,
  IconFileText,
  IconCode,
  IconGavel,
  IconSparkles,
  IconThumbUp,
} from '@tabler/icons-react';
import { format } from 'date-fns';
import { usePusherChannel } from '@/hooks/usePusher';

const TabsList: any = (Tabs as any).List;
const TabsTab: any = (Tabs as any).Tab;
const GridCol: any = (Grid as any).Col;
const CardSection: any = (Card as any).Section;

export type ContentType = 'lesson' | 'assessment' | 'message' | 'image' | 'video' | 'document' | 'code';
export type ContentStatus = 'pending' | 'approved' | 'rejected' | 'flagged' | 'under_review';
export type ModerationReason = 'inappropriate' | 'spam' | 'copyright' | 'quality' | 'policy_violation' | 'other';

export interface ContentItem {
  id: string;
  type: ContentType;
  title: string;
  description?: string;
  content?: string;
  author: {
    id: string;
    name: string;
    role: string;
    avatar?: string;
  };
  status: ContentStatus;
  createdAt: string;
  reviewedAt?: string;
  reviewedBy?: {
    id: string;
    name: string;
  };
  flags: number;
  reports: Array<{
    id: string;
    reason: ModerationReason;
    description: string;
    reportedBy: string;
    createdAt: string;
  }>;
  metadata?: {
    fileSize?: number;
    duration?: number;
    language?: string;
    tags?: string[];
  };
  aiScore?: {
    safety: number;
    quality: number;
    relevance: number;
  };
  thumbnail?: string;
}

export interface ContentModerationPanelProps {
  onContentApprove?: (contentId: string) => void;
  onContentReject?: (contentId: string, reason: string) => void;
  onContentDelete?: (contentId: string) => void;
  onContentView?: (content: ContentItem) => void;
  showAIAssist?: boolean;
  allowBulkActions?: boolean;
}

export const ContentModerationPanel = memo<ContentModerationPanelProps>(({
  onContentApprove,
  onContentReject,
  onContentDelete,
  onContentView,
  showAIAssist = true,
  allowBulkActions = true,
}) => {
  const theme = useMantineTheme();
  const [tabValue, setTabValue] = useState(0);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination
  const [page, setPage] = useState(0);
  const rowsPerPage = 10;

  // Search and filter
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<ContentType | 'all'>('all');

  // Selection
  const [selected, setSelected] = useState<string[]>([]);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);

  // Dialogs
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  usePusherChannel(
    'content-moderation',
    {
      'new-content': (data: ContentItem) => {
        setContent((prev) => [data, ...prev]);
      },
      'content-updated': (data: { id: string; status: ContentStatus }) => {
        setContent((prev) =>
          prev.map((item) =>
            item.id === data.id ? { ...item, status: data.status } : item
          )
        );
      },
    },
    { dependencies: [] }
  );

  // Fetch content
  useEffect(() => {
    fetchContent();
  }, []);

  const fetchContent = async () => {
    setLoading(true);
    try {
      // Mock data for demonstration
      const mockContent: ContentItem[] = [
        {
          id: '1',
          type: 'lesson',
          title: 'Introduction to Algebra',
          description: 'Basic algebraic concepts for beginners',
          author: {
            id: 'teacher1',
            name: 'Sarah Johnson',
            role: 'teacher',
          },
          status: 'pending',
          createdAt: new Date().toISOString(),
          flags: 0,
          reports: [],
          aiScore: {
            safety: 98,
            quality: 85,
            relevance: 92,
          },
        },
        {
          id: '2',
          type: 'assessment',
          title: 'Physics Quiz Chapter 3',
          description: 'Assessment on force and motion',
          author: {
            id: 'teacher2',
            name: 'Michael Brown',
            role: 'teacher',
          },
          status: 'pending',
          createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          flags: 0,
          reports: [],
          aiScore: {
            safety: 100,
            quality: 78,
            relevance: 88,
          },
        },
        {
          id: '3',
          type: 'message',
          title: 'Student Question',
          content: 'Can someone help with this problem?',
          author: {
            id: 'student1',
            name: 'John Smith',
            role: 'student',
          },
          status: 'flagged',
          createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          flags: 3,
          reports: [
            {
              id: 'r1',
              reason: 'spam',
              description: 'Repeated posting',
              reportedBy: 'user123',
              createdAt: new Date().toISOString(),
            },
          ],
          aiScore: {
            safety: 65,
            quality: 40,
            relevance: 30,
          },
        },
        {
          id: '4',
          type: 'video',
          title: 'Chemistry Lab Experiment',
          description: 'Lab safety and procedure demonstration',
          author: {
            id: 'teacher3',
            name: 'Emily Davis',
            role: 'teacher',
          },
          status: 'approved',
          createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          reviewedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          reviewedBy: {
            id: 'admin1',
            name: 'Admin User',
          },
          flags: 0,
          reports: [],
          metadata: {
            duration: 1200, // 20 minutes
            fileSize: 250 * 1024 * 1024, // 250MB
          },
          aiScore: {
            safety: 100,
            quality: 95,
            relevance: 98,
          },
          thumbnail: 'https://via.placeholder.com/150',
        },
        {
          id: '5',
          type: 'document',
          title: 'Study Guide - World History',
          description: 'Comprehensive guide for final exam',
          author: {
            id: 'teacher1',
            name: 'Sarah Johnson',
            role: 'teacher',
          },
          status: 'under_review',
          createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          flags: 1,
          reports: [
            {
              id: 'r2',
              reason: 'copyright',
              description: 'Contains copyrighted material',
              reportedBy: 'user456',
              createdAt: new Date().toISOString(),
            },
          ],
          aiScore: {
            safety: 90,
            quality: 82,
            relevance: 95,
          },
        },
      ];

      setContent(mockContent);
    } catch (err) {
      setError('Failed to fetch content');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (contentItem: ContentItem) => {
    setContent(prev =>
      prev.map(item =>
        item.id === contentItem.id
          ? { ...item, status: 'approved', reviewedAt: new Date().toISOString() }
          : item
      )
    );
    onContentApprove?.(contentItem.id);
  };

  const handleReject = async () => {
    if (selectedContent && rejectReason) {
      setContent(prev =>
        prev.map(item =>
          item.id === selectedContent.id
            ? { ...item, status: 'rejected', reviewedAt: new Date().toISOString() }
            : item
        )
      );
      onContentReject?.(selectedContent.id, rejectReason);
      setRejectDialogOpen(false);
      setRejectReason('');
      setSelectedContent(null);
    }
  };

  const handleBulkAction = (action: 'approve' | 'reject' | 'delete') => {
    selected.forEach(id => {
      const item = content.find(c => c.id === id);
      if (item) {
        switch (action) {
          case 'approve':
            handleApprove(item);
            break;
          case 'reject':
            // Open reject dialog for bulk reject
            break;
          case 'delete':
            handleDelete(item);
            break;
        }
      }
    });
    setSelected([]);
  };

  const handleDelete = async (contentItem: ContentItem) => {
    setContent(prev => prev.filter(item => item.id !== contentItem.id));
    onContentDelete?.(contentItem.id);
  };

  const getContentIcon = (type: ContentType) => {
    switch (type) {
      case 'lesson':
        return <IconSchool size={16} />;
      case 'assessment':
        return <IconClipboardList size={16} />;
      case 'message':
        return <IconMessage size={16} />;
      case 'image':
        return <IconPhoto size={16} />;
      case 'video':
        return <IconVideo size={16} />;
      case 'document':
        return <IconFileText size={16} />;
      case 'code':
        return <IconCode size={16} />;
      default:
        return <IconInfoCircle size={16} />;
    }
  };

  const getStatusColor = (status: ContentStatus): string => {
    switch (status) {
      case 'pending':
        return theme.colors.yellow[6];
      case 'approved':
        return theme.colors.green[6];
      case 'rejected':
        return theme.colors.red[6];
      case 'flagged':
        return theme.colors.red[6];
      case 'under_review':
        return theme.colors.blue[6];
      default:
        return theme.colors.gray[6];
    }
  };

  const getAIScoreColor = (score: number) => {
    if (score >= 80) return theme.colors.green[6];
    if (score >= 60) return theme.colors.yellow[6];
    return theme.colors.red[6];
  };

  const filteredContent = content.filter(item => {
    const matchesSearch = searchTerm
      ? item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchTerm.toLowerCase())
      : true;

    const matchesType = filterType === 'all' || item.type === filterType;

    return matchesSearch && matchesType;
  });

  const getTabContent = () => {
    switch (tabValue) {
      case 0: // Pending Review
        return filteredContent.filter(c => c.status === 'pending');
      case 1: // Flagged
        return filteredContent.filter(c => c.status === 'flagged');
      case 2: // Under Review
        return filteredContent.filter(c => c.status === 'under_review');
      case 3: // All Content
        return filteredContent;
      default:
        return [];
    }
  };

  const tabContent = getTabContent();
  const totalPages = Math.max(1, Math.ceil(tabContent.length / rowsPerPage));
  const paginatedContent = tabContent.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  useEffect(() => {
    if (page > totalPages - 1) {
      setPage(Math.max(totalPages - 1, 0));
    }
  }, [page, totalPages]);

  return (
    <Paper style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box p="md" style={{ borderBottom: `1px solid ${theme.colors.gray[3]}` }}>
        <Group justify="space-between" align="center">
          <Text size="lg" fw={700}>
            Content Moderation
          </Text>
          <Group gap="xs">
            {allowBulkActions && selected.length > 0 && (
              <>
                <Button
                  size="sm"
                  color="green"
                  leftSection={<IconCheck size={16} />}
                  onClick={() => handleBulkAction('approve')}
                >
                  Approve ({selected.length})
                </Button>
                <Button
                  size="sm"
                  color="red"
                  leftSection={<IconX size={16} />}
                  onClick={() => handleBulkAction('reject')}
                >
                  Reject ({selected.length})
                </Button>
              </>
            )}
            {showAIAssist && (
              <Button
                size="sm"
                variant="outline"
                leftSection={<IconSparkles size={16} />}
              >
                AI Assist
              </Button>
            )}
          </Group>
        </Group>

        {/* Tabs */}
        <Tabs
          value={tabValue.toString()}
          onChange={(value: string | null) => setTabValue(Number(value ?? 0))}
          mt="md"
        >
          <TabsList>
            <TabsTab value="0">
              <Group gap={6} align="center">
                <span>Pending Review</span>
                <Badge size="sm" color="yellow" variant="light">
                  {content.filter((c) => c.status === 'pending').length}
                </Badge>
              </Group>
            </TabsTab>
            <TabsTab value="1">
              <Group gap={6} align="center">
                <span>Flagged</span>
                <Badge size="sm" color="red" variant="light">
                  {content.filter((c) => c.status === 'flagged').length}
                </Badge>
              </Group>
            </TabsTab>
            <TabsTab value="2">
              <Group gap={6} align="center">
                <span>Under Review</span>
                <Badge size="sm" color="blue" variant="light">
                  {content.filter((c) => c.status === 'under_review').length}
                </Badge>
              </Group>
            </TabsTab>
            <TabsTab value="3">All Content</TabsTab>
          </TabsList>
        </Tabs>

        {/* Filters */}
        <Group gap="md" mt="md">
          <TextInput
            size="sm"
            placeholder="Search content..."
            value={searchTerm}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setSearchTerm(event.currentTarget.value)}
            leftSection={<IconSearch size={16} />}
            style={{ flex: 1, maxWidth: 300 }}
          />
          <Select
            size="sm"
            placeholder="Type"
            value={filterType}
            onChange={(value: string | null) => setFilterType((value as ContentType | null) ?? 'all')}
            data={[
              { value: 'all', label: 'All Types' },
              { value: 'lesson', label: 'Lesson' },
              { value: 'assessment', label: 'Assessment' },
              { value: 'message', label: 'Message' },
              { value: 'video', label: 'Video' },
              { value: 'document', label: 'Document' },
            ]}
            style={{ minWidth: 120 }}
          />
        </Group>
      </Box>

      {/* Loading */}
      {loading && <Progress value={100} animated />}

      {/* Error */}
      {error && (
        <Alert color="red" m="md">
          {error}
        </Alert>
      )}

      {/* Content List */}
      <Box style={{ flex: 1, overflow: 'auto' }} p="md">
        <Grid>
          {paginatedContent.map(item => (
            <GridCol span={{ base: 12, md: 6, lg: 4 }} key={item.id}>
              <Card
                style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderLeft: `4px solid ${getStatusColor(item.status)}`,
                }}
              >
                {item.thumbnail && (
                  <CardSection>
                    <img
                      src={item.thumbnail}
                      alt={item.title}
                      style={{ height: 140, width: '100%', objectFit: 'cover' }}
                    />
                  </CardSection>
                )}
                <CardSection p="md" style={{ flex: 1 }}>
                  <Stack gap="xs">
                    {/* Header */}
                    <Group justify="space-between" align="center">
                      <Badge
                        size="sm"
                        variant="light"
                        color="gray"
                        leftSection={getContentIcon(item.type)}
                        style={{ textTransform: 'capitalize' }}
                      >
                        {item.type}
                      </Badge>
                      <Badge
                        size="sm"
                        style={{ backgroundColor: getStatusColor(item.status), color: 'white', textTransform: 'capitalize' }}
                      >
                        {item.status}
                      </Badge>
                    </Group>

                    {/* Title and description */}
                    <Text size="sm" fw={700}>
                      {item.title}
                    </Text>
                    {item.description && (
                      <Text size="xs" c="dimmed" style={{ height: 40, overflow: 'hidden' }}>
                        {item.description}
                      </Text>
                    )}

                    {/* Author */}
                    <Group gap="xs" align="center">
                      <Avatar size={24} radius="xl">
                        {item.author.name.charAt(0)}
                      </Avatar>
                      <Text size="xs">
                        {item.author.name} • {format(new Date(item.createdAt), 'MMM dd, HH:mm')}
                      </Text>
                    </Group>

                    {/* AI Scores */}
                    {showAIAssist && item.aiScore && (
                      <Stack gap="xs">
                        <Text size="xs" c="dimmed">
                          AI Analysis
                        </Text>
                        <Group gap="md">
                          <Tooltip label="Safety Score">
                            <Group gap="xs" align="center">
                              <IconGavel size={14} style={{ color: getAIScoreColor(item.aiScore.safety) }} />
                              <Text size="xs">{item.aiScore.safety}%</Text>
                            </Group>
                          </Tooltip>
                          <Tooltip label="Quality Score">
                            <Group gap="xs" align="center">
                              <IconThumbUp size={14} style={{ color: getAIScoreColor(item.aiScore.quality) }} />
                              <Text size="xs">{item.aiScore.quality}%</Text>
                            </Group>
                          </Tooltip>
                          <Tooltip label="Relevance Score">
                            <Group gap="xs" align="center">
                              <IconInfoCircle size={14} style={{ color: getAIScoreColor(item.aiScore.relevance) }} />
                              <Text size="xs">{item.aiScore.relevance}%</Text>
                            </Group>
                          </Tooltip>
                        </Group>
                      </Stack>
                    )}

                    {/* Flags and reports */}
                    {(item.flags > 0 || item.reports.length > 0) && (
                      <Alert color="yellow" py="xs">
                        <Stack gap="xs">
                          <Text size="xs">
                            {item.flags} flags, {item.reports.length} reports
                          </Text>
                          {item.reports[0] && (
                            <Text size="xs">
                              Latest: {item.reports[0].reason}
                            </Text>
                          )}
                        </Stack>
                      </Alert>
                    )}
                  </Stack>
                </CardSection>
                <CardSection p="xs" style={{ borderTop: `1px solid ${theme.colors.gray[3]}` }}>
                  <Group justify="space-between" align="center">
                    <Group gap="xs">
                      {allowBulkActions && (
                        <Checkbox
                          checked={selected.includes(item.id)}
                          onChange={() => {
                            if (selected.includes(item.id)) {
                              setSelected(prev => prev.filter(id => id !== item.id));
                            } else {
                              setSelected(prev => [...prev, item.id]);
                            }
                          }}
                        />
                      )}
                      <ActionIcon
                        size="sm"
                        variant="subtle"
                        onClick={() => {
                          setSelectedContent(item);
                          setViewDialogOpen(true);
                          onContentView?.(item);
                        }}
                      >
                        <IconEye size={16} />
                      </ActionIcon>
                      {item.status === 'pending' && (
                        <>
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            color="green"
                            onClick={() => handleApprove(item)}
                          >
                            <IconCheck size={16} />
                          </ActionIcon>
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            color="red"
                            onClick={() => {
                              setSelectedContent(item);
                              setRejectDialogOpen(true);
                            }}
                          >
                            <IconX size={16} />
                          </ActionIcon>
                        </>
                      )}
                    </Group>
                    <ActionIcon
                      size="sm"
                      variant="subtle"
                      color="red"
                      onClick={() => handleDelete(item)}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Group>
                </CardSection>
              </Card>
            </GridCol>
          ))}
        </Grid>
      </Box>

      {/* Pagination */}
      <Box p="md" style={{ borderTop: `1px solid ${theme.colors.gray[3]}` }}>
        <Group justify="space-between" align="center">
          <Text size="sm" c="dimmed">
            Showing {tabContent.length === 0 ? 0 : page * rowsPerPage + 1}-
            {Math.min((page + 1) * rowsPerPage, tabContent.length)} of {tabContent.length} items
          </Text>
          <Group gap="xs">
            <Button
              size="xs"
              variant="light"
              onClick={() => setPage((prev) => Math.max(prev - 1, 0))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <Text size="sm" c="dimmed">
              {page + 1} / {totalPages}
            </Text>
            <Button
              size="xs"
              variant="light"
              onClick={() => setPage((prev) => Math.min(prev + 1, totalPages - 1))}
              disabled={page >= totalPages - 1}
            >
              Next
            </Button>
          </Group>
        </Group>
      </Box>

      {/* View Dialog */}
      <Modal
        opened={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        title="Content Details"
        size="lg"
      >
        {selectedContent && (
          <Stack gap="md">
            <Text size="lg" fw={700}>{selectedContent.title}</Text>
            {selectedContent.description && (
              <Text>{selectedContent.description}</Text>
            )}
            {selectedContent.content && (
              <Paper withBorder p="md">
                <Text>{selectedContent.content}</Text>
              </Paper>
            )}
            <Divider />
            <Text size="sm" fw={600}>Metadata</Text>
            <Grid>
              <GridCol span={6}>
                <Text size="xs" c="dimmed">Author</Text>
                <Text size="sm">{selectedContent.author.name}</Text>
              </GridCol>
              <GridCol span={6}>
                <Text size="xs" c="dimmed">Created</Text>
                <Text size="sm">
                  {format(new Date(selectedContent.createdAt), 'PPp')}
                </Text>
              </GridCol>
            </Grid>
            <Group justify="flex-end" mt="md">
              <Button variant="light" onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>

      {/* Reject Dialog */}
      <Modal
        opened={rejectDialogOpen}
        onClose={() => setRejectDialogOpen(false)}
        title="Reject Content"
        size="md"
      >
        <Stack gap="md">
          <Text>
            Please provide a reason for rejecting "{selectedContent?.title}"
          </Text>
          <Select
            label="Reason"
            placeholder="Select reason"
            value={rejectReason}
            onChange={(value: string | null) => setRejectReason(value ?? '')}
            data={[
              { value: 'inappropriate', label: 'Inappropriate Content' },
              { value: 'spam', label: 'Spam' },
              { value: 'copyright', label: 'Copyright Violation' },
              { value: 'quality', label: 'Low Quality' },
              { value: 'policy', label: 'Policy Violation' },
              { value: 'other', label: 'Other' },
            ]}
          />
          <TextInput
            label="Additional Comments"
            placeholder="Optional additional comments"
          />
          <Group justify="flex-end" mt="md">
            <Button variant="light" onClick={() => setRejectDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              color="red"
              onClick={handleReject}
              disabled={!rejectReason}
            >
              Reject
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Paper>
  );
});

ContentModerationPanel.displayName = 'ContentModerationPanel';

export default ContentModerationPanel;
