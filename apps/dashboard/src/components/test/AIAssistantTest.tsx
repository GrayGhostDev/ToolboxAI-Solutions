/**
 * AI Assistant Test Component
 * Simple test to verify AI Assistant functionality
 */

import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import { apiClient } from '../../services/api';

export const AIAssistantTest: React.FunctionComponent<Record<string, any>> = () => {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const testAIAssistant = async () => {
    if (!message.trim()) return;

    setLoading(true);
    try {
      console.log('Testing AI Assistant with message:', message);

      const result = await apiClient.request<any>({
        method: 'POST',
        url: '/api/v1/ai-chat/generate',
        data: { message },
        timeout: 30000
      });

      console.log('AI Assistant response:', result);
      setResponse(result.content || 'No response received');
    } catch (error) {
      console.error('AI Assistant test failed:', error);
      setResponse(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3, m: 2 }}>
      <Typography variant="h6" gutterBottom>
        AI Assistant Test
      </Typography>

      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          label="Test Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter a message to test the AI Assistant..."
          disabled={loading}
        />
      </Box>

      <Button
        variant="contained"
        onClick={(e: React.MouseEvent) => testAIAssistant}
        disabled={loading || !message.trim()}
        sx={{ mb: 2 }}
      >
        {loading ? 'Testing...' : 'Test AI Assistant'}
      </Button>

      {response && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Response:
          </Typography>
          <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {response}
            </Typography>
          </Paper>
        </Box>
      )}
    </Paper>
  );
};
