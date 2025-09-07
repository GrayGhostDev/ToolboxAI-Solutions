import * as React from "react";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Chip from "@mui/material/Chip";
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import { createLesson } from "../../services/api";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const subjects = [
  "Math",
  "Science",
  "Language",
  "Arts",
  "Technology",
  "Social Studies",
  "Physical Education",
  "Life Skills",
];

export default function CreateLessonDialog({ open, onClose, onSuccess }: Props) {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = React.useState(false);
  const [formData, setFormData] = React.useState({
    title: "",
    description: "",
    subject: "Math",
    status: "draft" as "draft" | "published",
    enableRoblox: false,
    tags: [] as string[],
  });
  const [tagInput, setTagInput] = React.useState("");

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
  };

  const handleSwitchChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [field]: event.target.checked,
    });
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()],
      });
      setTagInput("");
    }
  };

  const handleDeleteTag = (tagToDelete: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((tag) => tag !== tagToDelete),
    });
  };

  const handleSave = async () => {
    if (!formData.title.trim() || !formData.description.trim()) {
      dispatch(
        addNotification({
          type: "error",
          message: "Please fill in all required fields",
        })
      );
      return;
    }

    setLoading(true);
    try {
      await createLesson({
        title: formData.title,
        description: formData.description,
        subject: formData.subject as any,
        status: formData.status,
      });

      dispatch(
        addNotification({
          type: "success",
          message: `Lesson "${formData.title}" created successfully`,
        })
      );

      // Reset form
      setFormData({
        title: "",
        description: "",
        subject: "Math",
        status: "draft",
        enableRoblox: false,
        tags: [],
      });

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error("Failed to create lesson:", error);
      dispatch(
        addNotification({
          type: "error",
          message: "Failed to create lesson. Please try again.",
        })
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Lesson</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            label="Lesson Title"
            fullWidth
            required
            value={formData.title}
            onChange={handleChange("title")}
            placeholder="e.g., Introduction to Fractions"
          />

          <TextField
            label="Description"
            fullWidth
            required
            multiline
            rows={3}
            value={formData.description}
            onChange={handleChange("description")}
            placeholder="Describe what students will learn in this lesson..."
          />

          <TextField
            select
            label="Subject"
            fullWidth
            value={formData.subject}
            onChange={handleChange("subject")}
          >
            {subjects.map((subject) => (
              <MenuItem key={subject} value={subject}>
                {subject}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Status"
            fullWidth
            value={formData.status}
            onChange={handleChange("status")}
          >
            <MenuItem value="draft">Draft</MenuItem>
            <MenuItem value="published">Published</MenuItem>
          </TextField>

          <FormControlLabel
            control={
              <Switch
                checked={formData.enableRoblox}
                onChange={handleSwitchChange("enableRoblox")}
              />
            }
            label="Enable Roblox Integration"
          />

          <Stack>
            <TextField
              label="Tags"
              fullWidth
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddTag();
                }
              }}
              placeholder="Add tags and press Enter"
              helperText="Tags help organize and search for lessons"
            />
            {formData.tags.length > 0 && (
              <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: "wrap" }}>
                {formData.tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => handleDeleteTag(tag)}
                    size="small"
                    sx={{ mb: 1 }}
                  />
                ))}
              </Stack>
            )}
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleSave} disabled={loading}>
          {loading ? "Creating..." : "Create Lesson"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}