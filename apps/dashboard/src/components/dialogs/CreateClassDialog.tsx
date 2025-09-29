import React, { useState } from "react";
import {
  Modal,
  Button,
  TextInput,
  Textarea,
  Select,
  Stack,
  Group,
  NumberInput,
} from '@mantine/core';
import { usePusherChannel } from "../../hooks/usePusherEvents";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";


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
  const dispatch = useAppDispatch();
  const [className, setClassName] = useState(initialData?.name || "");
  const [grade, setGrade] = useState(initialData?.grade || "");
  const [schedule, setSchedule] = useState(initialData?.schedule || "");
  const [subject, setSubject] = useState(initialData?.subject || "Mathematics");
  const [room, setRoom] = useState(initialData?.room || "");
  const [description, setDescription] = useState(initialData?.description || "");

  // Pusher real-time updates for class management
  usePusherChannel(
    'class-updates',
    {
      'class-created': (data: { classId: string; name: string; creator: string }) => {
        dispatch(
          addNotification({
            type: "success",
            message: `New class "${data.name}" created by ${data.creator}`,
          })
        );
      },
      'class-updated': (data: { classId: string; name: string; changes: string[] }) => {
        dispatch(
          addNotification({
            type: "info",
            message: `Class "${data.name}" has been updated`,
          })
        );
      },
      'class-enrollment-changed': (data: { classId: string; name: string; studentCount: number }) => {
        dispatch(
          addNotification({
            type: "info",
            message: `Class "${data.name}" now has ${data.studentCount} students enrolled`,
          })
        );
      },
    },
    { enabled: true }
  );

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

  const subjects = [
    "Mathematics",
    "Science",
    "English",
    "History",
    "Computer Science",
    "Art",
    "Music",
    "Physical Education",
  ];

  return (
    <Modal
      opened={open}
      onClose={handleClose}
      title={editMode ? "Edit Class" : "Create New Class"}
      size="lg"
      styles={{
        title: {
          background: 'linear-gradient(135deg, #00bcd4, #e91e63)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          fontWeight: 'bold',
          fontSize: '1.5rem'
        },
        header: {
          paddingBottom: 'var(--mantine-spacing-md)'
        }
      }}
    >
      <Stack spacing="md">
        <TextInput
          label="Class Name"
          required
          value={className}
          onChange={(event) => setClassName(event.currentTarget.value)}
          placeholder="Enter class name"
          styles={{
            label: { fontWeight: 600 }
          }}
          data-testid="class-name-input"
        />

        <Select
          label="Subject"
          required
          value={subject}
          onChange={(value) => setSubject(value || "Mathematics")}
          data={subjects.map(sub => ({ value: sub, label: sub }))}
          styles={{
            label: { fontWeight: 600 }
          }}
          data-testid="subject-select"
        />

        <NumberInput
          label="Grade Level"
          required
          value={grade ? parseInt(grade) : undefined}
          onChange={(value) => setGrade(value?.toString() || "")}
          placeholder="Enter grade level"
          min={1}
          max={12}
          styles={{
            label: { fontWeight: 600 }
          }}
          data-testid="grade-input"
        />

        <TextInput
          label="Room"
          value={room}
          onChange={(event) => setRoom(event.currentTarget.value)}
          placeholder="e.g., Room 101"
          styles={{
            label: { fontWeight: 600 }
          }}
          data-testid="room-input"
        />

        <TextInput
          label="Schedule"
          value={schedule}
          onChange={(event) => setSchedule(event.currentTarget.value)}
          placeholder="e.g., Mon/Wed/Fri 10:00 AM"
          styles={{
            label: { fontWeight: 600 }
          }}
          data-testid="schedule-input"
        />

        <Textarea
          label="Description"
          value={description}
          onChange={(event) => setDescription(event.currentTarget.value)}
          placeholder="Class description (optional)"
          rows={3}
          styles={{
            label: { fontWeight: 600 }
          }}
          data-testid="description-input"
        />

        <Group position="right" mt="md">
          <Button
            variant="default"
            onClick={handleClose}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!className || !grade}
            styles={{
              root: {
                background: 'linear-gradient(135deg, #00bcd4, #e91e63)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #00acc1, #d81b60)'
                }
              }
            }}
            data-testid="save-class-button"
          >
            {editMode ? "Update" : "Create"} Class
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
};

export default CreateClassDialog;