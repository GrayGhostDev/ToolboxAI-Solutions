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
} from "@mui/material";

interface CreateClassDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (classData: any) => void;
}

const CreateClassDialog: React.FC<CreateClassDialogProps> = ({
  open,
  onClose,
  onSave,
}) => {
  const [className, setClassName] = useState("");
  const [grade, setGrade] = useState("");
  const [schedule, setSchedule] = useState("");
  const [subject, setSubject] = useState("");

  const handleSave = () => {
    if (className && grade) {
      onSave({
        name: className,
        grade: parseInt(grade),
        schedule,
        subject,
      });
      // Reset form
      setClassName("");
      setGrade("");
      setSchedule("");
      setSubject("");
    }
  };

  const handleClose = () => {
    // Reset form
    setClassName("");
    setGrade("");
    setSchedule("");
    setSubject("");
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Class</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            label="Class Name"
            fullWidth
            value={className}
            onChange={(e) => setClassName(e.target.value)}
            required
            placeholder="e.g., Math 101, English Literature"
          />
          
          <FormControl fullWidth required>
            <InputLabel>Grade Level</InputLabel>
            <Select
              value={grade}
              label="Grade Level"
              onChange={(e) => setGrade(e.target.value)}
            >
              <MenuItem value="1">1st Grade</MenuItem>
              <MenuItem value="2">2nd Grade</MenuItem>
              <MenuItem value="3">3rd Grade</MenuItem>
              <MenuItem value="4">4th Grade</MenuItem>
              <MenuItem value="5">5th Grade</MenuItem>
              <MenuItem value="6">6th Grade</MenuItem>
              <MenuItem value="7">7th Grade</MenuItem>
              <MenuItem value="8">8th Grade</MenuItem>
              <MenuItem value="9">9th Grade</MenuItem>
              <MenuItem value="10">10th Grade</MenuItem>
              <MenuItem value="11">11th Grade</MenuItem>
              <MenuItem value="12">12th Grade</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Subject</InputLabel>
            <Select
              value={subject}
              label="Subject"
              onChange={(e) => setSubject(e.target.value)}
            >
              <MenuItem value="Math">Math</MenuItem>
              <MenuItem value="Science">Science</MenuItem>
              <MenuItem value="Language">Language Arts</MenuItem>
              <MenuItem value="Social Studies">Social Studies</MenuItem>
              <MenuItem value="Arts">Arts</MenuItem>
              <MenuItem value="Technology">Technology</MenuItem>
              <MenuItem value="Physical Education">Physical Education</MenuItem>
              <MenuItem value="Life Skills">Life Skills</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Schedule"
            fullWidth
            value={schedule}
            onChange={(e) => setSchedule(e.target.value)}
            placeholder="e.g., MWF 9:00-10:00 AM"
            helperText="Optional: Add class schedule information"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!className || !grade}
        >
          Create Class
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateClassDialog;