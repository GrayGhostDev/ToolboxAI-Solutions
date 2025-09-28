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
  Badge,
  Text,
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { usePusherChannel } from "../../hooks/usePusherEvents";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";

interface CreateAssessmentDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (assessmentData: any) => void;
}

const CreateAssessmentDialog: React.FunctionComponent<CreateAssessmentDialogProps> = ({
  open,
  onClose,
  onSave,
}) => {
  const dispatch = useAppDispatch();
  const [title, setTitle] = useState("");
  const [type, setType] = useState("quiz"); // Default to quiz
  const [classId, setClassId] = useState("");
  const [dueDate, setDueDate] = useState<Date | null>(null);
  const [maxSubmissions, setMaxSubmissions] = useState(1);
  const [description, setDescription] = useState("");

  // Pusher real-time updates for assessment activities
  usePusherChannel(
    'assessment-updates',
    {
      'assessment-created': (data: { assessmentId: string; title: string; type: string; classId: string }) => {
        dispatch(
          addNotification({
            type: "success",
            message: `New ${data.type} "${data.title}" has been created`,
          })
        );
      },
      'assessment-submitted': (data: { assessmentId: string; studentName: string; score?: number }) => {
        const scoreText = data.score ? ` with a score of ${data.score}%` : '';
        dispatch(
          addNotification({
            type: "info",
            message: `${data.studentName} submitted an assessment${scoreText}`,
          })
        );
      },
      'assessment-graded': (data: { assessmentId: string; title: string; avgScore: number; totalSubmissions: number }) => {
        dispatch(
          addNotification({
            type: "info",
            message: `Assessment "${data.title}" - Average score: ${data.avgScore}% (${data.totalSubmissions} submissions)`,
          })
        );
      },
    },
    { enabled: true }
  );

  const handleSave = () => {
    if (title && type && classId) { // classId is now required
      onSave({
        title,
        type,
        classId,
        dueDate: dueDate?.toISOString(),
        maxSubmissions,
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
    setMaxSubmissions(1);
    setDescription("");
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const assessmentTypes = [
    { value: "quiz", label: "Quiz" },
    { value: "test", label: "Test" },
    { value: "assignment", label: "Assignment" },
    { value: "project", label: "Project" },
  ];

  const classes = [
    { value: "class-1", label: "Mathematics 101" },
    { value: "class-2", label: "Science 202" },
    { value: "class-3", label: "History 303" },
    { value: "class-4", label: "English 404" },
  ];

  return (
    <Modal
      opened={open}
      onClose={handleClose}
      title="Create New Assessment"
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
          label="Assessment Title"
          required
          value={title}
          onChange={(event) => setTitle(event.currentTarget.value)}
          placeholder="e.g., Chapter 5 Quiz, Midterm Exam"
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Select
          label="Assessment Type"
          required
          value={type}
          onChange={(value) => setType(value || "quiz")}
          data={assessmentTypes}
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Select
          label="Class"
          required
          value={classId}
          onChange={(value) => setClassId(value || "")}
          data={classes}
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Textarea
          label="Description"
          value={description}
          onChange={(event) => setDescription(event.currentTarget.value)}
          placeholder="Describe the assessment objectives and instructions..."
          rows={3}
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <DateTimePicker
          label="Due Date"
          value={dueDate}
          onChange={setDueDate}
          placeholder="Optional: Set a due date for this assessment"
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <NumberInput
          label="Max Submissions"
          value={maxSubmissions}
          onChange={(value) => setMaxSubmissions(value || 1)}
          min={1}
          max={10}
          description="Number of submission attempts allowed"
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Stack spacing="xs">
          <Text size="sm" weight={600} color="dimmed">
            Assessment Status
          </Text>
          <Group spacing="xs">
            <Badge variant="filled" color="gray" size="sm">
              Draft
            </Badge>
            <Text size="xs" color="dimmed">
              You can publish this assessment after adding questions
            </Text>
          </Group>
        </Stack>

        <Group position="right" mt="md">
          <Button
            variant="default"
            onClick={handleClose}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!title || !type || !classId}
            styles={{
              root: {
                background: 'linear-gradient(135deg, #00bcd4, #e91e63)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #00acc1, #d81b60)'
                }
              }
            }}
          >
            Create Assessment
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
};

export default CreateAssessmentDialog;