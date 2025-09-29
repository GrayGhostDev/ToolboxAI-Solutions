import { vi } from 'vitest';

// Configure test timeout for Vitest
vi.setConfig({ testTimeout: 10000 });

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { ThemeProvider, createTheme } from '@mantine/core/styles';
import { configureStore } from '@reduxjs/toolkit';
import { describe, it, expect, beforeEach } from 'vitest';
import RobloxAIAssistantEnhanced from '../RobloxAIAssistantEnhanced';
import { api } from '../../../services/api';
import { pusherService } from '../../../services/pusher';

// Mock dependencies
vi.mock('../../../services/api');
vi.mock('../../../services/pusher');
vi.mock('react-chat-elements', () => ({
  MessageList: ({ dataSource }: any) => (
    <div data-testid="message-list">
      {dataSource.map((msg: any) => (
        <div key={msg.id} data-testid={`message-${msg.id}`}>
          {msg.text}
        </div>
      ))}
    </div>
  ),
  Input: ({ value, onChange, onKeyPress, placeholder }: any) => (
    <input
      data-testid="chat-input"
      value={value}
      onChange={onChange}
      onKeyPress={onKeyPress}
      placeholder={placeholder}
    />
  ),
  Button: ({ text, onClick, disabled }: any) => (
    <button data-testid="send-button" onClick={(e: React.MouseEvent) => onClick} disabled={disabled}>
      {text}
    </button>
  ),
  ChatList: () => <div data-testid="chat-list" />,
  Popup: ({ show, text }: any) => show ? <div data-testid="popup">{text}</div> : null,
  Avatar: () => <div data-testid="avatar" />
}));

const mockStore = configureStore({
  reducer: {
    user: (state = { id: '1', name: 'Test User', avatar: '/test-avatar.png' }) => state
  }
});

const theme = createTheme();

const renderComponent = () => {
  return render(
    <Provider store={mockStore}>
      <ThemeProvider theme={theme}>
        <RobloxAIAssistantEnhanced />
      </ThemeProvider>
    </Provider>
  );
};

describe('RobloxAIAssistantEnhanced', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (pusherService.subscribe as any).mockReturnValue('sub-id');
  });

  it('renders the component with header and input', () => {
    renderComponent();
    
    expect(screen.getByText('Roblox AI Assistant')).toBeInTheDocument();
    expect(screen.getByText('Enhanced')).toBeInTheDocument();
    expect(screen.getByTestId('chat-input')).toBeInTheDocument();
    expect(screen.getByTestId('send-button')).toBeInTheDocument();
  });

  it('displays suggested prompts initially', () => {
    renderComponent();
    
    expect(screen.getByText('Quick Start Ideas:')).toBeInTheDocument();
    expect(screen.getByText('Create a math puzzle room for grade 5')).toBeInTheDocument();
    expect(screen.getByText('Design a space station for science experiments')).toBeInTheDocument();
  });

  it('sends message when send button is clicked', async () => {
    const mockResponse = {
      data: {
        message: {
          id: 'ai-msg-1',
          content: 'Great idea! Let me help you create that environment.'
        }
      }
    };
    (api.post as any).mockResolvedValue(mockResponse);

    renderComponent();
    
    const input = screen.getByTestId('chat-input');
    const sendButton = screen.getByTestId('send-button');
    
    fireEvent.change(input, { target: { value: 'Create a space station' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/roblox/chat', expect.objectContaining({
        message: 'Create a space station',
        conversation_id: expect.any(String)
      }));
    });
  });

  it('handles Enter key press to send message', async () => {
    const mockResponse = {
      data: {
        message: {
          id: 'ai-msg-1',
          content: 'Message received!'
        }
      }
    };
    (api.post as any).mockResolvedValue(mockResponse);

    renderComponent();
    
    const input = screen.getByTestId('chat-input');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalled();
    });
  });

  it('extracts Roblox spec from user input', async () => {
    const mockResponse = { data: { message: { id: '1', content: 'Spec extracted!' } } };
    (api.post as any).mockResolvedValue(mockResponse);

    renderComponent();
    
    const input = screen.getByTestId('chat-input');
    
    fireEvent.change(input, { 
      target: { value: 'Create an obby named Space Adventure with medium difficulty' } 
    });
    fireEvent.keyPress(input, { key: 'Enter' });
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/roblox/chat', expect.objectContaining({
        roblox_spec: expect.objectContaining({
          environment_name: 'Space Adventure',
          map_type: 'obby',
          difficulty: 'medium'
        })
      }));
    });
  });

  it('handles WebSocket streaming messages', () => {
    renderComponent();
    
    // Simulate WebSocket subscription callback
    const subscribeCallback = (pusherService.subscribe as any).mock.calls[0][1];
    
    // Start streaming
    subscribeCallback({ type: 'stream_start' });
    expect(screen.getByText('...')).toBeInTheDocument();
    
    // Add token
    subscribeCallback({ type: 'stream_token', content: 'Hello' });
    expect(screen.getByText('Hello')).toBeInTheDocument();
    
    // Add more tokens
    subscribeCallback({ type: 'stream_token', content: ' World' });
    expect(screen.getByText('Hello World')).toBeInTheDocument();
    
    // End streaming
    subscribeCallback({ type: 'stream_end' });
  });

  it('handles suggested prompt clicks', async () => {
    const mockResponse = { data: { message: { id: '1', content: 'Creating math puzzle!' } } };
    (api.post as any).mockResolvedValue(mockResponse);

    renderComponent();
    
    const mathPrompt = screen.getByText('Create a math puzzle room for grade 5');
    fireEvent.click(mathPrompt);
    
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/roblox/chat', expect.objectContaining({
        message: 'Create a math puzzle room for grade 5'
      }));
    });
  });

  it('toggles expansion state', () => {
    renderComponent();
    
    const expandButton = screen.getByLabelText(/expand|collapse/i);
    fireEvent.click(expandButton);
    
    // Component should still be functional after toggle
    expect(screen.getByTestId('chat-input')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (api.post as any).mockRejectedValue(new Error('API Error'));

    renderComponent();
    
    const input = screen.getByTestId('chat-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter' });
    
    await waitFor(() => {
      expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
    });
  });

  it('shows video call popup', () => {
    renderComponent();
    
    const videoButton = screen.getByLabelText('Video Call');
    fireEvent.click(videoButton);
    
    expect(screen.getByTestId('popup')).toBeInTheDocument();
    expect(screen.getByText('Video call feature coming soon!')).toBeInTheDocument();
  });

  it('prevents sending empty messages', () => {
    renderComponent();
    
    const sendButton = screen.getByTestId('send-button');
    expect(sendButton).toBeDisabled();
    
    const input = screen.getByTestId('chat-input');
    fireEvent.change(input, { target: { value: '   ' } }); // Only whitespace
    expect(sendButton).toBeDisabled();
  });
});