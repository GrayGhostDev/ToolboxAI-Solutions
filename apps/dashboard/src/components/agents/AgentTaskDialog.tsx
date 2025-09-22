/**
 * Agent Task Dialog Component
 * 
 * Dialog for executing tasks on agents with form inputs and real-time feedback.
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: string;
}

interface TaskRequest {
  agent_type: string;
  task_type: string;
  task_data: Record<string, any>;
  user_id?: string;
}

interface TaskResult {
  success: boolean;
  task_id?: string;
  result?: any;
  execution_time?: number;
  error?: string;
}

interface AgentTaskDialogProps {
  open: boolean;
  onClose: () => void;
  agent: AgentStatus | null;
  onExecute: (taskRequest: TaskRequest) => Promise<TaskResult>;
}

// Task type configurations for different agent types
const TASK_CONFIGURATIONS: Record<string, Record<string, any>> = {
  content_generator: {
    generate_content: {
      label: 'Generate Content',
      fields: [
        { name: 'subject', label: 'Subject', type: 'text', required: true },
        { name: 'grade_level', label: 'Grade Level', type: 'number', required: true, min: 1, max: 12 },
        { name: 'objectives', label: 'Learning Objectives', type: 'textarea', required: true, 
          placeholder: 'Enter learning objectives, one per line' },
      ]
    }
  },
  quiz_generator: {
    generate_quiz: {
      label: 'Generate Quiz',
      fields: [
        { name: 'subject', label: 'Subject', type: 'text', required: true },
        { name: 'objectives', label: 'Learning Objectives', type: 'textarea', required: true,
          placeholder: 'Enter learning objectives, one per line' },
        { name: 'num_questions', label: 'Number of Questions', type: 'number', required: true, min: 1, max: 50, default: 5 },
        { name: 'difficulty', label: 'Difficulty', type: 'select', required: true, default: 'medium',
          options: [
            { value: 'easy', label: 'Easy' },
            { value: 'medium', label: 'Medium' },
            { value: 'hard', label: 'Hard' }
          ]
        }
      ]
    }
  },
  terrain_generator: {
    generate_terrain: {
      label: 'Generate Terrain',
      fields: [
        { name: 'subject', label: 'Subject', type: 'text', required: true },
        { name: 'terrain_type', label: 'Terrain Type', type: 'select', required: true, default: 'educational',
          options: [
            { value: 'educational', label: 'Educational' },
            { value: 'landscape', label: 'Landscape' },
            { value: 'urban', label: 'Urban' },
            { value: 'fantasy', label: 'Fantasy' }
          ]
        },
        { name: 'complexity', label: 'Complexity', type: 'select', required: true, default: 'medium',
          options: [
            { value: 'simple', label: 'Simple' },
            { value: 'medium', label: 'Medium' },
            { value: 'complex', label: 'Complex' }
          ]
        },
        { name: 'features', label: 'Features', type: 'textarea', required: false,
          placeholder: 'Enter specific features, one per line (optional)' }
      ]
    }
  },
  script_generator: {
    generate_script: {
      label: 'Generate Script',
      fields: [
        { name: 'script_type', label: 'Script Type', type: 'select', required: true, default: 'ServerScript',
          options: [
            { value: 'ServerScript', label: 'Server Script' },
            { value: 'LocalScript', label: 'Local Script' },
            { value: 'ModuleScript', label: 'Module Script' }
          ]
        },
        { name: 'functionality', label: 'Functionality', type: 'textarea', required: true,
          placeholder: 'Describe what the script should do' },
        { name: 'requirements', label: 'Requirements', type: 'textarea', required: false,
          placeholder: 'Enter specific requirements, one per line (optional)' }
      ]
    }
  },
  code_reviewer: {
    review_code: {
      label: 'Review Code',
      fields: [
        { name: 'code', label: 'Code to Review', type: 'textarea', required: true, rows: 10,
          placeholder: 'Paste the code you want to review here' },
        { name: 'language', label: 'Language', type: 'select', required: true, default: 'lua',
          options: [
            { value: 'lua', label: 'Lua' },
            { value: 'luau', label: 'Luau' },
            { value: 'javascript', label: 'JavaScript' },
            { value: 'typescript', label: 'TypeScript' },
            { value: 'python', label: 'Python' }
          ]
        },
        { name: 'review_type', label: 'Review Type', type: 'select', required: true, default: 'comprehensive',
          options: [
            { value: 'security', label: 'Security Focus' },
            { value: 'performance', label: 'Performance Focus' },
            { value: 'comprehensive', label: 'Comprehensive Review' }
          ]
        }
      ]
    }
  }
};

export const AgentTaskDialog = ({
  open,
  onClose,
  agent,
  onExecute,
}: AgentTaskDialogProps) => {
  const [taskType, setTaskType] = useState('');
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Get available task types for the agent
  const availableTaskTypes = agent ? TASK_CONFIGURATIONS[agent.agent_type] || {} : {};
  const currentTaskConfig = taskType ? availableTaskTypes[taskType] : null;

  // Reset form when agent changes
  useEffect(() => {
    if (agent) {
      const firstTaskType = Object.keys(availableTaskTypes)[0];
      setTaskType(firstTaskType || '');
      setFormData({});
      setResult(null);
      setError(null);
    }
  }, [agent, availableTaskTypes]);

  // Set default values when task type changes
  useEffect(() => {
    if (currentTaskConfig) {
      const defaults: Record<string, any> = {};
      currentTaskConfig.fields.forEach((field: any) => {
        if (field.default !== undefined) {
          defaults[field.name] = field.default;
        }
      });
      setFormData(defaults);
    }
  }, [currentTaskConfig]);

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const processFieldValue = (field: any, value: any) => {
    // Convert textarea values to arrays if they contain line breaks
    if (field.type === 'textarea' && typeof value === 'string' && value.includes('\n')) {
      return value.split('\n').filter(line => line.trim() !== '');
    }
    
    // Convert number strings to numbers
    if (field.type === 'number' && typeof value === 'string') {
      return parseInt(value) || 0;
    }
    
    return value;
  };

  const handleExecute = async () => {
    if (!agent || !taskType || !currentTaskConfig) return;

    setExecuting(true);
    setError(null);
    setResult(null);

    try {
      // Process form data
      const processedData: Record<string, any> = {};
      currentTaskConfig.fields.forEach((field: any) => {
        const value = formData[field.name];
        processedData[field.name] = processFieldValue(field, value);
      });

      const taskRequest: TaskRequest = {
        agent_type: agent.agent_type,
        task_type: taskType,
        task_data: processedData
      };

      const taskResult = await onExecute(taskRequest);
      setResult(taskResult);

      if (!taskResult.success) {
        setError(taskResult.error || 'Task execution failed');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setExecuting(false);
    }
  };

  const renderField = (field: any) => {
    const value = formData[field.name] || '';

    switch (field.type) {
      case 'text':
        return (
          <TextField
            key={field.name}
            fullWidth
            label={field.label}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            required={field.required}
            placeholder={field.placeholder}
          />
        );

      case 'number':
        return (
          <TextField
            key={field.name}
            fullWidth
            type="number"
            label={field.label}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            required={field.required}
            inputProps={{ min: field.min, max: field.max }}
          />
        );

      case 'textarea':
        return (
          <TextField
            key={field.name}
            fullWidth
            multiline
            rows={field.rows || 4}
            label={field.label}
            value={value}
            onChange={(e) => handleFieldChange(field.name, e.target.value)}
            required={field.required}
            placeholder={field.placeholder}
          />
        );

      case 'select':
        return (
          <FormControl key={field.name} fullWidth required={field.required}>
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              label={field.label}
            >
              {field.options?.map((option: any) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      default:
        return null;
    }
  };

  if (!agent) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '60vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h6">
            Execute Task on {agent.agent_type.replace(/_/g, ' ')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Agent ID: {agent.agent_id}
          </Typography>
        </Box>
        <Chip
          label={agent.status.toUpperCase()}
          color={agent.status === 'idle' ? 'success' : 'default'}
          size="small"
        />
      </DialogTitle>

      <DialogContent>
        {Object.keys(availableTaskTypes).length === 0 ? (
          <Alert severity="warning">
            No task types available for this agent type.
          </Alert>
        ) : (
          <Box sx={{ mt: 1 }}>
            {/* Task Type Selection */}
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Task Type</InputLabel>
              <Select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                label="Task Type"
              >
                {Object.entries(availableTaskTypes).map(([key, config]: [string, any]) => (
                  <MenuItem key={key} value={key}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Task Configuration Form */}
            {currentTaskConfig && (
              <Grid container spacing={2}>
                {currentTaskConfig.fields.map((field: any) => (
                  <Grid item xs={12} key={field.name}>
                    {renderField(field)}
                  </Grid>
                ))}
              </Grid>
            )}

            {/* Execution Progress */}
            {executing && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" gutterBottom>
                  Executing task...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            {/* Error Display */}
            {error && (
              <Alert severity="error" sx={{ mt: 3 }}>
                {error}
              </Alert>
            )}

            {/* Result Display */}
            {result && (
              <Box sx={{ mt: 3 }}>
                {result.success ? (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    Task completed successfully in {result.execution_time?.toFixed(2)}s
                  </Alert>
                ) : (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    Task failed: {result.error}
                  </Alert>
                )}

                {result.result && (
                  <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>Task Result</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box
                        component="pre"
                        sx={{
                          backgroundColor: 'grey.100',
                          p: 2,
                          borderRadius: 1,
                          overflow: 'auto',
                          maxHeight: 300,
                          fontSize: '0.875rem',
                          fontFamily: 'monospace'
                        }}
                      >
                        {JSON.stringify(result.result, null, 2)}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                )}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} startIcon={<CloseIcon />}>
          Close
        </Button>
        <Button
          variant="contained"
          onClick={handleExecute}
          disabled={!taskType || executing || agent.status !== 'idle'}
          startIcon={<PlayIcon />}
        >
          {executing ? 'Executing...' : 'Execute Task'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AgentTaskDialog;
