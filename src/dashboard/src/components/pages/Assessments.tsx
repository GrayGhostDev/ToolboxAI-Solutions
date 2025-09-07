import AddIcon from '@mui/icons-material/Add';
import AssessmentIcon from '@mui/icons-material/Assessment';
import FilterListIcon from '@mui/icons-material/FilterList';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import RefreshIcon from '@mui/icons-material/Refresh';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import * as React from 'react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  clearError,
  fetchAssessments,
  fetchSubmissions,
  setFilters,
} from '../../store/slices/assessmentsSlice';
import { createAssessment } from '../../services/api';
import { addNotification } from '../../store/slices/uiSlice';
import CreateAssessmentDialog from '../dialogs/CreateAssessmentDialog';

export default function Assessments() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { assessments, submissions, loading, error, filters } = useAppSelector(
    (state) => state.assessments
  );
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedAssessment, setSelectedAssessment] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  useEffect(() => {
    // Fetch assessments when component mounts
    dispatch(fetchAssessments());
    dispatch(fetchSubmissions({}));
  }, [dispatch]);

  const handleRefresh = () => {
    dispatch(fetchAssessments(filters));
    dispatch(fetchSubmissions({}));
  };

  const handleFilterChange = (filterType: string, value: any) => {
    const newFilters = { ...filters, [filterType]: value };
    dispatch(setFilters(newFilters));
    dispatch(fetchAssessments(newFilters));
  };

  const handleFilterMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterMenuClose = () => {
    setFilterAnchorEl(null);
  };

  // Calculate statistics from real data
  const activeAssessments = assessments.filter((a) => a.status === 'active').length;
  const pendingGrading = submissions.filter((s) => !s.gradedAt).length;
  const averageScore =
    submissions.length > 0
      ? Math.round(
          submissions
            .filter((s) => s.score !== undefined && s.score !== null)
            .reduce((acc, s) => acc + (s.score || 0), 0) /
            submissions.filter((s) => s.score !== undefined).length
        )
      : 0;
  const completionRate =
    assessments.length > 0
      ? Math.round(
          (assessments.filter((a) => a.submissions >= a.maxSubmissions).length /
            assessments.length) *
            100
        )
      : 0;

  const dueTodayCount = assessments.filter((a) => {
    if (!a.dueDate) return false;
    const dueDate = new Date(a.dueDate);
    const today = new Date();
    return dueDate.toDateString() === today.toDateString();
  }).length;

  if (loading && assessments.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  Assessments
                </Typography>
                <Stack direction="row" spacing={1}>
                  <IconButton onClick={handleRefresh} disabled={loading}>
                    <RefreshIcon />
                  </IconButton>
                  <IconButton onClick={handleFilterMenuOpen}>
                    <FilterListIcon />
                  </IconButton>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateDialogOpen(true)}
                  >
                    Create Assessment
                  </Button>
                </Stack>
              </Stack>
              <Menu
                anchorEl={filterAnchorEl}
                open={Boolean(filterAnchorEl)}
                onClose={handleFilterMenuClose}
              >
                <MenuItem
                  onClick={() => {
                    handleFilterChange('status', 'active');
                    handleFilterMenuClose();
                  }}
                >
                  Active Only
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleFilterChange('status', 'draft');
                    handleFilterMenuClose();
                  }}
                >
                  Drafts
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleFilterChange('type', 'quiz');
                    handleFilterMenuClose();
                  }}
                >
                  Quizzes
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleFilterChange('type', 'test');
                    handleFilterMenuClose();
                  }}
                >
                  Tests
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    handleFilterChange('type', undefined);
                    handleFilterMenuClose();
                  }}
                >
                  All Types
                </MenuItem>
              </Menu>
            </CardContent>
          </Card>
        </Grid>

        {/* Assessment Stats */}
        <Grid size={{ xs: 12, md: 3 }}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Active Assessments
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {activeAssessments}
                </Typography>
                {dueTodayCount > 0 && (
                  <Chip label={`${dueTodayCount} due today`} size="small" color="warning" />
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Pending Grading
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {pendingGrading}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={
                    submissions.length > 0
                      ? ((submissions.length - pendingGrading) / submissions.length) * 100
                      : 0
                  }
                />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Average Score
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {averageScore}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Class Average
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  Completion Rate
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {completionRate}%
                </Typography>
                <LinearProgress variant="determinate" value={completionRate} color="success" />
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Assessments */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Recent Assessments
              </Typography>
              {error && (
                <Alert severity="error" onClose={() => dispatch(clearError())} sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}
              <Stack spacing={2}>
                {assessments.length === 0 ? (
                  <Typography color="text.secondary" align="center" py={4}>
                    No assessments found. Create your first assessment to get started.
                  </Typography>
                ) : (
                  assessments.slice(0, 5).map((assessment) => (
                    <Box
                      key={assessment.id}
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        bgcolor: 'background.default',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': {
                          bgcolor: 'action.hover',
                        },
                      }}
                      onClick={() => setSelectedAssessment(assessment.id)}
                    >
                      <Stack direction="row" spacing={2} alignItems="center">
                        <AssessmentIcon color="primary" />
                        <Stack>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {assessment.title}
                          </Typography>
                          <Stack direction="row" spacing={1}>
                            <Chip
                              label={assessment.type}
                              size="small"
                              color={
                                assessment.type === 'quiz'
                                  ? 'info'
                                  : assessment.type === 'test'
                                  ? 'warning'
                                  : 'default'
                              }
                            />
                            <Chip
                              label={assessment.status}
                              size="small"
                              color={
                                assessment.status === 'active'
                                  ? 'success'
                                  : assessment.status === 'draft'
                                  ? 'default'
                                  : 'error'
                              }
                            />
                            <Typography variant="caption" color="text.secondary">
                              Submissions: {assessment.submissions}/{assessment.maxSubmissions}
                            </Typography>
                          </Stack>
                        </Stack>
                      </Stack>
                      <Stack alignItems="flex-end" spacing={1}>
                        <Stack direction="row" alignItems="center" spacing={1}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {assessment.averageScore ? `${assessment.averageScore}%` : 'Pending'}
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                            }}
                          >
                            <MoreVertIcon fontSize="small" />
                          </IconButton>
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          {assessment.dueDate
                            ? `Due: ${new Date(assessment.dueDate).toLocaleDateString()}`
                            : 'No due date'}
                        </Typography>
                      </Stack>
                    </Box>
                  ))
                )}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Create Assessment Dialog */}
      <CreateAssessmentDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSave={async (assessmentData) => {
          try {
            // Call API to create assessment
            const createdAssessment = await createAssessment(assessmentData);
            
            dispatch(
              addNotification({
                type: 'success',
                message: `Assessment "${createdAssessment.title}" created successfully!`,
              })
            );
            setCreateDialogOpen(false);
            // Refresh assessments list
            dispatch(fetchAssessments());
          } catch (error) {
            console.error('Failed to create assessment:', error);
            dispatch(
              addNotification({
                type: 'error',
                message: 'Failed to create assessment. Please try again.',
              })
            );
          }
        }}
      />
    </>
  );
}
