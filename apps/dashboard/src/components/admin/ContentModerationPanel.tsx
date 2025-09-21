// @ts-nocheck - Temporary fix for Phase 3
/**
 * ContentModerationPanel Component
 * Content moderation and review interface for administrators
 */
import { memo, useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Tooltip from '@mui/material/Tooltip';
import Checkbox from '@mui/material/Checkbox';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import CardMedia from '@mui/material/CardMedia';
import Grid from '@mui/material/Grid';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Badge from '@mui/material/Badge';
import LinearProgress from '@mui/material/LinearProgress';
import Avatar from '@mui/material/Avatar';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import { useTheme } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Check as ApproveIcon,
  Close as RejectIcon,
  Flag as FlagIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  School as EducationIcon,
  Assessment as AssessmentIcon,
  Message as MessageIcon,
  Image as ImageIcon,
  VideoLibrary as VideoIcon,
  Description as DocumentIcon,
  Code as CodeIcon,
  Report as ReportIcon,
  Gavel as PolicyIcon,
  AutoAwesome as AIIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { usePusher } from '@/hooks/usePusher';
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
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  // Search and filter
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<ContentType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<ContentStatus | 'all'>('pending');
  // Selection
  const [selected, setSelected] = useState<string[]>([]);
  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  // Dialogs
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  // Setup Pusher for real-time updates
  const { subscribe, unsubscribe } = usePusher();
  useEffect(() => {
    const channel = 'content-moderation';
    const handleNewContent = (data: ContentItem) => {
      setContent(prev => [data, ...prev]);
    };
    const handleContentUpdate = (data: { id: string; status: ContentStatus }) => {
      setContent(prev =>
        prev.map(item =>
          item.id === data.id ? { ...item, status: data.status } : item
        )
      );
    };
    subscribe(channel, 'new-content', handleNewContent);
    subscribe(channel, 'content-updated', handleContentUpdate);
    return () => {
      unsubscribe(channel, 'new-content', handleNewContent);
      unsubscribe(channel, 'content-updated', handleContentUpdate);
    };
  }, [subscribe, unsubscribe]);
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
        return <EducationIcon />;
      case 'assessment':
        return <AssessmentIcon />;
      case 'message':
        return <MessageIcon />;
      case 'image':
        return <ImageIcon />;
      case 'video':
        return <VideoIcon />;
      case 'document':
        return <DocumentIcon />;
      case 'code':
        return <CodeIcon />;
      default:
        return <InfoIcon />;
    }
  };
  const getStatusColor = (status: ContentStatus) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'flagged':
        return 'error';
      case 'under_review':
        return 'info';
      default:
        return 'default';
    }
  };
  const getAIScoreColor = (score: number) => {
    if (score >= 80) return theme.palette.success.main;
    if (score >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };
  const filteredContent = content.filter(item => {
    const matchesSearch = searchTerm
      ? item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.description?.toLowerCase().includes(searchTerm.toLowerCase())
      : true;
    const matchesType = filterType === 'all' || item.type === filterType;
    const matchesStatus = filterStatus === 'all' || item.status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
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
  const paginatedContent = tabContent.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6" fontWeight="bold">
            Content Moderation
          </Typography>
          <Stack direction="row" spacing={1}>
            {allowBulkActions && selected.length > 0 && (
              <>
                <Button
                  size="small"
                  color="success"
                  startIcon={<ApproveIcon />}
                  onClick={(e: React.MouseEvent) => () => handleBulkAction('approve')}
                >
                  Approve ({selected.length})
                </Button>
                <Button
                  size="small"
                  color="error"
                  startIcon={<RejectIcon />}
                  onClick={(e: React.MouseEvent) => () => handleBulkAction('reject')}
                >
                  Reject ({selected.length})
                </Button>
              </>
            )}
            {showAIAssist && (
              <Button
                size="small"
                variant="outlined"
                startIcon={<AIIcon />}
              >
                AI Assist
              </Button>
            )}
          </Stack>
        </Stack>
        {/* Tabs */}
        <Tabs
          value={tabValue}
          onChange={(_, value) => setTabValue(value)}
          sx={{ mt: 2 }}
        >
          <Tab
            label={
              <Badge badgeContent={content.filter(c => c.status === 'pending').length} color="warning">
                Pending Review
              </Badge>
            }
          />
          <Tab
            label={
              <Badge badgeContent={content.filter(c => c.status === 'flagged').length} color="error">
                Flagged
              </Badge>
            }
          />
          <Tab
            label={
              <Badge badgeContent={content.filter(c => c.status === 'under_review').length} color="info">
                Under Review
              </Badge>
            }
          />
          <Tab label="All Content" />
        </Tabs>
        {/* Filters */}
        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <TextField
            size="small"
            placeholder="Search content..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ flex: 1, maxWidth: 300 }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={filterType}
              label="Type"
              onChange={(e) => setFilterType(e.target.value as ContentType | 'all')}
            >
              <MenuItem value="all">All Types</MenuItem>
              <MenuItem value="lesson">Lesson</MenuItem>
              <MenuItem value="assessment">Assessment</MenuItem>
              <MenuItem value="message">Message</MenuItem>
              <MenuItem value="video">Video</MenuItem>
              <MenuItem value="document">Document</MenuItem>
            </Select>
          </FormControl>
        </Stack>
      </Box>
      {/* Loading */}
      {loading && <LinearProgress />}
      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      )}
      {/* Content List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <Grid container spacing={2}>
          {paginatedContent.map(item => (
            <Grid item xs={12} md={6} lg={4} key={item.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderLeft: `4px solid ${theme.palette[getStatusColor(item.status)].main}`,
                }}
              >
                {item.thumbnail && (
                  <CardMedia
                    component="img"
                    height="140"
                    image={item.thumbnail}
                    alt={item.title}
                  />
                )}
                <CardContent sx={{ flex: 1 }}>
                  <Stack spacing={1}>
                    {/* Header */}
                    <Stack direction="row" alignItems="center" justifyContent="space-between">
                      <Chip
                        icon={getContentIcon(item.type)}
                        label={item.type}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={item.status}
                        size="small"
                        color={getStatusColor(item.status) as any}
                      />
                    </Stack>
                    {/* Title and description */}
                    <Typography variant="subtitle1" fontWeight="bold">
                      {item.title}
                    </Typography>
                    {item.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ height: 40, overflow: 'hidden' }}>
                        {item.description}
                      </Typography>
                    )}
                    {/* Author */}
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Avatar sx={{ width: 24, height: 24 }}>
                        {item.author.name.charAt(0)}
                      </Avatar>
                      <Typography variant="caption">
                        {item.author.name} • {format(new Date(item.createdAt), 'MMM dd, HH:mm')}
                      </Typography>
                    </Stack>
                    {/* AI Scores */}
                    {showAIAssist && item.aiScore && (
                      <Stack spacing={0.5}>
                        <Typography variant="caption" color="text.secondary">
                          AI Analysis
                        </Typography>
                        <Stack direction="row" spacing={2}>
                          <Tooltip title="Safety Score">
                            <Stack direction="row" alignItems="center" spacing={0.5}>
                              <PolicyIcon fontSize="small" sx={{ color: getAIScoreColor(item.aiScore.safety) }} />
                              <Typography variant="caption">{item.aiScore.safety}%</Typography>
                            </Stack>
                          </Tooltip>
                          <Tooltip title="Quality Score">
                            <Stack direction="row" alignItems="center" spacing={0.5}>
                              <ThumbUpIcon fontSize="small" sx={{ color: getAIScoreColor(item.aiScore.quality) }} />
                              <Typography variant="caption">{item.aiScore.quality}%</Typography>
                            </Stack>
                          </Tooltip>
                          <Tooltip title="Relevance Score">
                            <Stack direction="row" alignItems="center" spacing={0.5}>
                              <InfoIcon fontSize="small" sx={{ color: getAIScoreColor(item.aiScore.relevance) }} />
                              <Typography variant="caption">{item.aiScore.relevance}%</Typography>
                            </Stack>
                          </Tooltip>
                        </Stack>
                      </Stack>
                    )}
                    {/* Flags and reports */}
                    {(item.flags > 0 || item.reports.length > 0) && (
                      <Alert severity="warning" sx={{ py: 0.5 }}>
                        <Stack spacing={0.5}>
                          <Typography variant="caption">
                            {item.flags} flags, {item.reports.length} reports
                          </Typography>
                          {item.reports[0] && (
                            <Typography variant="caption">
                              Latest: {item.reports[0].reason}
                            </Typography>
                          )}
                        </Stack>
                      </Alert>
                    )}
                  </Stack>
                </CardContent>
                <CardActions>
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
                  <IconButton
                    size="small"
                    onClick={(e: React.MouseEvent) => () => {
                      setSelectedContent(item);
                      setViewDialogOpen(true);
                    }}
                  >
                    <ViewIcon />
                  </IconButton>
                  {item.status === 'pending' && (
                    <>
                      <IconButton
                        size="small"
                        color="success"
                        onClick={(e: React.MouseEvent) => () => handleApprove(item)}
                      >
                        <ApproveIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e: React.MouseEvent) => () => {
                          setSelectedContent(item);
                          setRejectDialogOpen(true);
                        }}
                      >
                        <RejectIcon />
                      </IconButton>
                    </>
                  )}
                  <IconButton
                    size="small"
                    onClick={(e: React.MouseEvent) => () => handleDelete(item)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
      {/* Pagination */}
      <TablePagination
        component="div"
        count={tabContent.length}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10));
          setPage(0);
        }}
      />
      {/* View Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Content Details</DialogTitle>
        <DialogContent>
          {selectedContent && (
            <Stack spacing={2}>
              <Typography variant="h6">{selectedContent.title}</Typography>
              {selectedContent.description && (
                <Typography>{selectedContent.description}</Typography>
              )}
              {selectedContent.content && (
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography>{selectedContent.content}</Typography>
                </Paper>
              )}
              <Divider />
              <Typography variant="subtitle2">Metadata</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Author
                  </Typography>
                  <Typography>{selectedContent.author.name}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Created
                  </Typography>
                  <Typography>
                    {format(new Date(selectedContent.createdAt), 'PPp')}
                  </Typography>
                </Grid>
              </Grid>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
      {/* Reject Dialog */}
      <Dialog
        open={rejectDialogOpen}
        onClose={() => setRejectDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Reject Content</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            <Typography>
              Please provide a reason for rejecting "{selectedContent?.title}"
            </Typography>
            <FormControl fullWidth>
              <InputLabel>Reason</InputLabel>
              <Select
                value={rejectReason}
                label="Reason"
                onChange={(e) => setRejectReason(e.target.value)}
              >
                <MenuItem value="inappropriate">Inappropriate Content</MenuItem>
                <MenuItem value="spam">Spam</MenuItem>
                <MenuItem value="copyright">Copyright Violation</MenuItem>
                <MenuItem value="quality">Low Quality</MenuItem>
                <MenuItem value="policy">Policy Violation</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
            <TextField
              multiline
              rows={3}
              label="Additional Comments"
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setRejectDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={(e: React.MouseEvent) => handleReject}
            disabled={!rejectReason}
          >
            Reject
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
});
ContentModerationPanel.displayName = 'ContentModerationPanel';
export default ContentModerationPanel;