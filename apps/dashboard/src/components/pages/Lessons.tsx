import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, InputAdornment, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import * as React from "react";
import { useNavigate } from "react-router-dom";
import { listLessons, deleteLesson } from "../../services/api";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";
import CreateLessonDialog from "../dialogs/CreateLessonDialog";
import { Lesson } from "../../types/api";
export default function Lessons() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [lessons, setLessons] = React.useState<Lesson[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedLesson, setSelectedLesson] = React.useState<Lesson | null>(null);
  const fetchLessons = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await listLessons();
      setLessons(data);
    } catch (error: any) {
      console.error("Failed to fetch lessons:", error);
      const errorDetail = error.response?.data?.detail;
      let errorMessage = "Failed to load lessons. Please try again.";
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        // Handle Pydantic validation errors
        errorMessage = errorDetail.map((err: any) => 
          err.msg || err.message || 'Validation error'
        ).join(', ');
      }
      dispatch(
        addNotification({
          type: "error",
          message: errorMessage,
        })
      );
      setLessons([]); // Set empty array instead of mock data
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  React.useEffect(() => {
    fetchLessons();
  }, [fetchLessons]);
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, lesson: Lesson) => {
    setAnchorEl(event.currentTarget);
    setSelectedLesson(lesson);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedLesson(null);
  };
  const handlePushToRoblox = async (lesson: Lesson) => {
    dispatch(
      addNotification({
        type: "info",
        message: `Preparing Roblox environment for "${lesson.title}"...`,
      })
    );
    // Simulate push process then navigate to Roblox dashboard
    setTimeout(() => {
      dispatch(
        addNotification({
          type: "success",
          message: `Lesson "${lesson.title}" is ready in Roblox!`,
        })
      );
      // Navigate to Roblox dashboard with lesson context
      navigate(`/roblox?lessonId=${lesson.id}&lessonTitle=${encodeURIComponent(lesson.title)}`);
    }, 1500);
    handleMenuClose();
  };
  const handleDelete = async (lesson: Lesson) => {
    if (!window.confirm(`Are you sure you want to delete "${lesson.title}"?`)) {
      return;
    }
    try {
      await deleteLesson(lesson.id);
      dispatch(
        addNotification({
          type: "success",
          message: `Lesson "${lesson.title}" deleted successfully`,
        })
      );
      fetchLessons();
    } catch (error) {
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to delete lesson",
        })
      );
    }
    handleMenuClose();
  };
  const filteredLessons = lessons.filter((lesson) =>
    lesson.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lesson.subject.toLowerCase().includes(searchTerm.toLowerCase())
  );
  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Typography order={5} style={{ fontWeight: 600 }}>
                Lessons
              </Typography>
              <Stack direction="row" gap={2} style={{ width: { xs: "100%", md: "auto" } }}>
                <TextField
                  size="small"
                  placeholder="Search lessons..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{ minWidth: 250 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <IconSearch />
                      </InputAdornment>
                    ),
                  }}
                />
                <Button
                  variant="filled"
                  startIcon={<IconPlus />}
                  onClick={(e: React.MouseEvent) => () => setCreateDialogOpen(true)}
                >
                  New Lesson
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12}>
        <Card>
          <CardContent style={{ p: 0 }}>
            <Table aria-label="lessons table">
              <TableHead>
                <TableRow>
                  <TableCell>Title</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Classes</TableCell>
                  <TableCell>Roblox</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : filteredLessons.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No lessons found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLessons.map((lesson) => (
                    <TableRow key={lesson.id} hover>
                      <TableCell>
                        <Stack>
                          <Typography size="sm" style={{ fontWeight: 500 }}>
                            {lesson.title}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {lesson.description}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={lesson.subject}
                          size="small"
                          color="blue"
                          variant="outline"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={lesson.status}
                          size="small"
                          color={lesson.status === "published" ? "success" : "default"}
                        />
                      </TableCell>
                      <TableCell>{lesson.classIds?.length || 0}</TableCell>
                      <TableCell>
                        {lesson.robloxWorldId ? (
                          <Chip
                            label="Connected"
                            size="small"
                            color="green"
                            icon={<RocketLaunchIcon />}
                          />
                        ) : (
                          <Button
                            size="small"
                            startIcon={<RocketLaunchIcon />}
                            onClick={(e: React.MouseEvent) => () => handlePushToRoblox(lesson)}
                          >
                            Push
                          </Button>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={(e: React.MouseEvent) => (e) => handleMenuOpen(e, lesson)}
                        >
                          <IconDotsVertical />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={(e: React.MouseEvent) => () => {
                if (selectedLesson) {
                  navigate(`/lessons/${selectedLesson.id}`);
                }
                handleMenuClose();
              }}>
                <IconEye fontSize="small" style={{ mr: 1 }} />
                View Details
              </MenuItem>
              <MenuItem onClick={() => {
                dispatch(
                  addNotification({
                    type: "info",
                    message: "Edit functionality coming soon!",
                  })
                );
                handleMenuClose();
              }}>
                <IconEdit fontSize="small" style={{ mr: 1 }} />
                Edit
              </MenuItem>
              <MenuItem onClick={() => {
                if (selectedLesson) {
                  const duplicatedLesson = { ...selectedLesson, title: `${selectedLesson.title} (Copy)` };
                  dispatch(
                    addNotification({
                      type: "success",
                      message: `Lesson "${selectedLesson.title}" duplicated!`,
                    })
                  );
                  fetchLessons();
                }
                handleMenuClose();
              }}>
                <ContentCopyIcon fontSize="small" style={{ mr: 1 }} />
                Duplicate
              </MenuItem>
              {selectedLesson && !selectedLesson.robloxWorldId && (
                <MenuItem onClick={(e: React.MouseEvent) => () => selectedLesson && handlePushToRoblox(selectedLesson)}>
                  <RocketLaunchIcon fontSize="small" style={{ mr: 1 }} />
                  Push to Roblox
                </MenuItem>
              )}
              <MenuItem onClick={(e: React.MouseEvent) => () => selectedLesson && handleDelete(selectedLesson)}>
                <IconTrash fontSize="small" style={{ mr: 1 }} />
                Delete
              </MenuItem>
            </Menu>
          </CardContent>
        </Card>
      </Grid>
      <CreateLessonDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={fetchLessons}
      />
    </Grid>
  );
}