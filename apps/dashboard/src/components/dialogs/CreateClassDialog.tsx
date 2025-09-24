import React, { useState } from "react";
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';


interface CreateClassDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (classData: any) => void;
  editMode?: boolean;
  initialData?: any;
}

const CreateClassDialog: React.FunctionComponent<CreateClassDialogProps> = ({
  open,
  onClose,
  onSave,
  editMode = false,
  initialData = null,
}) => {
  const [className, setClassName] = useState(initialData?.name || "");
  const [grade, setGrade] = useState(initialData?.grade || "");
  const [schedule, setSchedule] = useState(initialData?.schedule || "");
  const [subject, setSubject] = useState(initialData?.subject || "Mathematics");
  const [room, setRoom] = useState(initialData?.room || "");
  const [description, setDescription] = useState(initialData?.description || "");

  React.useEffect(() => {
    if (initialData) {
      setClassName(initialData.name || "");
      setGrade(initialData.grade || initialData.grade_level || "");
      setSchedule(initialData.schedule || "");
      setSubject(initialData.subject || "Mathematics");
      setRoom(initialData.room || "");
      setDescription(initialData.description || "");
    }
  }, [initialData]);

  const handleSave = () => {
    if (className && grade) {
      onSave({
        name: className,
        grade_level: parseInt(grade),
        grade: parseInt(grade),
        schedule,
        subject,
        room,
        description,
      });
      // Reset form
      if (!editMode) {
        setClassName("");
        setGrade("");
        setSchedule("");
        setSubject("Mathematics");
        setRoom("");
        setDescription("");
      }
    }
  };

  const handleClose = () => {
    // Reset form if not in edit mode
    if (!editMode) {
      setClassName("");
      setGrade("");
      setSchedule("");
      setSubject("Mathematics");
      setRoom("");
      setDescription("");
    }
    onClose();
  };

  const handleSubjectChange = (event: SelectChangeEvent) => {
    setSubject(event.target.value);
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth role="dialog">
      <DialogTitle>{editMode ? "Edit Class" : "Create New Class"}</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <TextField
            label="Class Name"
            name="name"
            placeholder="Enter class name"
            value={className}
            onChange={(e) => setClassName(e.target.value)}
            fullWidth
            required
            autoFocus
            data-testid="class-name-input"
          />

          <FormControl fullWidth required>
            <InputLabel id="subject-label">Subject</InputLabel>
            <Select
              labelId="subject-label"
              id="subject-select"
              name="subject"
              value={subject}
              label="Subject"
              onChange={handleSubjectChange}
              data-testid="subject-select"
            >
              <MenuItem value="Mathematics">Mathematics</MenuItem>
              <MenuItem value="Science">Science</MenuItem>
              <MenuItem value="English">English</MenuItem>
              <MenuItem value="History">History</MenuItem>
              <MenuItem value="Computer Science">Computer Science</MenuItem>
              <MenuItem value="Art">Art</MenuItem>
              <MenuItem value="Music">Music</MenuItem>
              <MenuItem value="Physical Education">Physical Education</MenuItem>
            </Select>
          </FormControl>

          <TextField
            label="Grade Level"
            name="grade"
            type="number"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            fullWidth
            required
            inputProps={{ min: 1, max: 12 }}
            data-testid="grade-input"
          />

          <TextField
            label="Room"
            name="room"
            placeholder="e.g., Room 101"
            value={room}
            onChange={(e) => setRoom(e.target.value)}
            fullWidth
            data-testid="room-input"
          />

          <TextField
            label="Schedule"
            name="schedule"
            placeholder="e.g., Mon/Wed/Fri 10:00 AM"
            value={schedule}
            onChange={(e) => setSchedule(e.target.value)}
            fullWidth
            data-testid="schedule-input"
          />

          <TextField
            label="Description"
            name="description"
            placeholder="Class description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            multiline
            rows={3}
            data-testid="description-input"
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={(e: React.MouseEvent) => handleClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={(e: React.MouseEvent) => handleSave}
          variant="contained"
          disabled={!className || !grade}
          data-testid="save-class-button"
        >
          {editMode ? "Update" : "Create"} Class
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateClassDialog;