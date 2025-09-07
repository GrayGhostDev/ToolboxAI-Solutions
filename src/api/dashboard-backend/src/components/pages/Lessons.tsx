import * as React from "react";
import Grid2 from "@mui/material/Unstable_Grid2";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import TableBody from "@mui/material/TableBody";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import SearchIcon from "@mui/icons-material/Search";
import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import RocketLaunchIcon from "@mui/icons-material/RocketLaunch";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { listLessons, deleteLesson, pushLessonToRoblox } from "../../services/api";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";
import CreateLessonDialog from "../dialogs/CreateLessonDialog";
import { Lesson } from "../../types/api";

export default function Lessons() {
  const dispatch = useAppDispatch();
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
    } catch (error) {
      console.error("Failed to fetch lessons:", error);
      // Use mock data for demo
      setLessons([
        {
          id: "1",
          title: "Introduction to Fractions",
          description: "Learn the basics of fractions",
          subject: "Math",
          status: "published",
          teacherId: "teacher1",
          classIds: ["class1"],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          content: {},
        },
        {
          id: "2",
          title: "Solar System Exploration",
          description: "Journey through our solar system",
          subject: "Science",
          status: "published",
          teacherId: "teacher1",
          classIds: ["class1", "class2"],
          robloxWorldId: "world123",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          content: {},
        },
        {
          id: "3",
          title: "Creative Writing Workshop",
          description: "Develop your creative writing skills",
          subject: "Language",
          status: "draft",
          teacherId: "teacher1",
          classIds: ["class3"],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          content: {},
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

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
    try {
      await pushLessonToRoblox(lesson.id);
      dispatch(
        addNotification({
          type: "success",
          message: `Lesson "${lesson.title}" pushed to Roblox successfully`,
        })
      );
    } catch (error) {
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to push lesson to Roblox",
        })
      );
    }
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
    <Grid2 container spacing={3}>
      <Grid2 xs={12}>
        <Card>
          <CardContent>
            <Stack
              direction={{ xs: "column", md: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", md: "center" }}
              gap={2}
            >
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Lessons
              </Typography>
              <Stack direction="row" gap={2} sx={{ width: { xs: "100%", md: "auto" } }}>
                <TextField
                  size="small"
                  placeholder="Search lessons..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  sx={{ minWidth: 250 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  New Lesson
                </Button>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 xs={12}>
        <Card>
          <CardContent sx={{ p: 0 }}>
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
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
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
                          color="primary"
                          variant="outlined"
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
                            color="success"
                            icon={<RocketLaunchIcon />}
                          />
                        ) : (
                          <Button
                            size="small"
                            startIcon={<RocketLaunchIcon />}
                            onClick={() => handlePushToRoblox(lesson)}
                          >
                            Push
                          </Button>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, lesson)}
                        >
                          <MoreVertIcon />
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
              <MenuItem onClick={handleMenuClose}>
                <EditIcon fontSize="small" sx={{ mr: 1 }} />
                Edit
              </MenuItem>
              <MenuItem onClick={handleMenuClose}>
                <ContentCopyIcon fontSize="small" sx={{ mr: 1 }} />
                Duplicate
              </MenuItem>
              {selectedLesson && !selectedLesson.robloxWorldId && (
                <MenuItem onClick={() => selectedLesson && handlePushToRoblox(selectedLesson)}>
                  <RocketLaunchIcon fontSize="small" sx={{ mr: 1 }} />
                  Push to Roblox
                </MenuItem>
              )}
              <MenuItem onClick={() => selectedLesson && handleDelete(selectedLesson)}>
                <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
                Delete
              </MenuItem>
            </Menu>
          </CardContent>
        </Card>
      </Grid2>

      <CreateLessonDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={fetchLessons}
      />
    </Grid2>
  );
}