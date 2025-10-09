import * as React from 'react';
import {
  Modal,
  Button,
  TextInput,
  Textarea,
  Select,
  Stack,
  Group,
  Badge,
  Switch,
  Text,
  CloseButton
} from '@mantine/core';
import { IconX } from '@tabler/icons-react';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { usePusherChannel } from '../../hooks/usePusherEvents';
import { useApiCall } from '../../hooks/useApiCall';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const subjects = [
  'Math',
  'Science',
  'Language',
  'Arts',
  'Technology',
  'Social Studies',
  'Physical Education',
  'Life Skills',
];

export default function CreateLessonDialog({ open, onClose, onSuccess }: Props) {
  const dispatch = useAppDispatch();
  const { execute: createLesson, loading } = useApiCall();
  const [formData, setFormData] = React.useState({
    title: '',
    description: '',
    subject: 'Math',
    status: 'draft' as 'draft' | 'published',
    enableRoblox: false,
    tags: [] as string[],
  });
  const [tagInput, setTagInput] = React.useState('');

  // Pusher real-time updates for lesson creation progress
  usePusherChannel(
    'content-generation',
    {
      'lesson-creation-progress': (data: { status: string; progress: number; message?: string }) => {
        if (data.status === 'completed') {
          dispatch(
            addNotification({
              type: 'success',
              message: data.message || 'Lesson creation completed successfully!',
            })
          );
        } else if (data.status === 'error') {
          dispatch(
            addNotification({
              type: 'error',
              message: data.message || 'Error during lesson creation',
            })
          );
        }
      },
      'lesson-updated': (data: { lessonId: string; title: string; action: string }) => {
        dispatch(
          addNotification({
            type: 'info',
            message: `Lesson "${data.title}" has been ${data.action}`,
          })
        );
      },
    },
    { enabled: true }
  );

  const handleChange = (field: string, value: string) => {
    setFormData({
      ...formData,
      [field]: value,
    });
  };

  const handleSwitchChange = (field: string, checked: boolean) => {
    setFormData({
      ...formData,
      [field]: checked,
    });
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()],
      });
      setTagInput('');
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
          type: 'error',
          message: 'Please fill in all required fields',
        })
      );
      return;
    }

    try {
      await createLesson(
        'POST',
        '/lessons',
        {
          title: formData.title,
          description: formData.description,
          subject: formData.subject as any,
          status: formData.status,
        },
        {
          showNotification: false,  // We'll show our own notification
        }
      );

      dispatch(
        addNotification({
          type: 'success',
          message: `Lesson "${formData.title}" created successfully`,
        })
      );

      // Reset form
      setFormData({
        title: '',
        description: '',
        subject: 'Math',
        status: 'draft',
        enableRoblox: false,
        tags: [],
      });

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to create lesson:', error);
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to create lesson. Please try again.',
        })
      );
    }
  };

  return (
    <Modal
      opened={open}
      onClose={onClose}
      title="Create New Lesson"
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
          label="Lesson Title"
          required
          value={formData.title}
          onChange={(event) => handleChange('title', event.currentTarget.value)}
          placeholder="e.g., Introduction to Fractions"
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Textarea
          label="Description"
          required
          rows={3}
          value={formData.description}
          onChange={(event) => handleChange('description', event.currentTarget.value)}
          placeholder="Describe what students will learn in this lesson..."
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Select
          label="Subject"
          value={formData.subject}
          onChange={(value) => handleChange('subject', value || 'Math')}
          data={subjects.map(subject => ({ value: subject, label: subject }))}
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Select
          label="Status"
          value={formData.status}
          onChange={(value) => handleChange('status', value || 'draft')}
          data={[
            { value: 'draft', label: 'Draft' },
            { value: 'published', label: 'Published' }
          ]}
          styles={{
            label: { fontWeight: 600 }
          }}
        />

        <Switch
          label="Enable Roblox Integration"
          checked={formData.enableRoblox}
          onChange={(event) => handleSwitchChange('enableRoblox', event.currentTarget.checked)}
          styles={{
            label: { fontWeight: 600 },
            track: {
              '&[data-checked]': {
                background: 'linear-gradient(135deg, #00bcd4, #e91e63)'
              }
            }
          }}
        />

        <Stack spacing="xs">
          <TextInput
            label="Tags"
            value={tagInput}
            onChange={(event) => setTagInput(event.currentTarget.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                handleAddTag();
              }
            }}
            placeholder="Add tags and press Enter"
            description="Tags help organize and search for lessons"
            styles={{
              label: { fontWeight: 600 }
            }}
          />
          {formData.tags.length > 0 && (
            <Group spacing="xs" style={{ marginTop: 'var(--mantine-spacing-xs)' }}>
              {formData.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="filled"
                  style={{
                    background: 'linear-gradient(135deg, #00bcd4, #e91e63)',
                    cursor: 'pointer'
                  }}
                  rightSection={
                    <CloseButton
                      size="xs"
                      iconSize={10}
                      onClick={() => handleDeleteTag(tag)}
                      style={{ color: 'white' }}
                    />
                  }
                >
                  {tag}
                </Badge>
              ))}
            </Group>
          )}
        </Stack>

        <Group position="right" mt="md">
          <Button
            variant="default"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading}
            loading={loading}
            styles={{
              root: {
                background: 'linear-gradient(135deg, #00bcd4, #e91e63)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #00acc1, #d81b60)'
                }
              }
            }}
          >
            {loading ? 'Creating...' : 'Create Lesson'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}