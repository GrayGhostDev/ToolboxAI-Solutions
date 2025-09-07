import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Chip,
  Box,
  Typography,
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";

interface CreateAssessmentDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (assessmentData: any) => void;
}

const CreateAssessmentDialog: React.FC<CreateAssessmentDialogProps> = ({
  open,
  onClose,
  onSave,
}) => {
  const [title, setTitle] = useState("");
  const [type, setType] = useState("quiz"); // Default to quiz
  const [classId, setClassId] = useState("");
  const [dueDate, setDueDate] = useState<Date | null>(null);
  const [maxSubmissions, setMaxSubmissions] = useState("1");
  const [description, setDescription] = useState("");

  const handleSave = () => {
    if (title && type && classId) { // classId is now required
      onSave({
        title,
        type,
        classId,
        dueDate: dueDate?.toISOString(),
        maxSubmissions: parseInt(maxSubmissions),
        description,
        status: "draft",
        questions: [], // Include empty questions array as required by backend
      });
      // Reset form
      resetForm();
    }
  };

  const resetForm = () => {
    setTitle("");
    setType("quiz"); // Reset to default
    setClassId("");
    setDueDate(null);
    setMaxSubmissions("1");
    setDescription("");
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Assessment</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            label="Assessment Title"
            fullWidth
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="e.g., Chapter 5 Quiz, Midterm Exam"
            autoFocus
          />
          
          <FormControl fullWidth required>
            <InputLabel>Assessment Type</InputLabel>
            <Select
              value={type}
              label="Assessment Type"
              onChange={(e) => setType(e.target.value)}
            >
              <MenuItem value="quiz">Quiz</MenuItem>
              <MenuItem value="test">Test</MenuItem>
              <MenuItem value="assignment">Assignment</MenuItem>
              <MenuItem value="project">Project</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth required>
            <InputLabel>Class</InputLabel>
            <Select
              value={classId}
              label="Class"
              onChange={(e) => setClassId(e.target.value)}
            >
              <MenuItem value="class-1">Mathematics 101</MenuItem>
              <MenuItem value="class-2">Science 202</MenuItem>
              <MenuItem value="class-3">History 303</MenuItem>
              <MenuItem value="class-4">English 404</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the assessment objectives and instructions..."
          />

          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DateTimePicker
              label="Due Date"
              value={dueDate}
              onChange={(newValue) => setDueDate(newValue)}
              slotProps={{
                textField: {
                  fullWidth: true,
                  helperText: "Optional: Set a due date for this assessment",
                },
              }}
            />
          </LocalizationProvider>

          <TextField
            label="Max Submissions"
            type="number"
            fullWidth
            value={maxSubmissions}
            onChange={(e) => setMaxSubmissions(e.target.value)}
            inputProps={{ min: 1, max: 10 }}
            helperText="Number of submission attempts allowed"
          />

          <Box>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Assessment Status
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
              <Chip label="Draft" color="default" size="small" />
              <Typography variant="caption" sx={{ pt: 0.5 }}>
                You can publish this assessment after adding questions
              </Typography>
            </Stack>
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!title || !type || !classId}
        >
          Create Assessment
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateAssessmentDialog;