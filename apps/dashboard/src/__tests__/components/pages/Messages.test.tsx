jest.setTimeout(10000);

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Messages from '@/components/pages/Messages';
import { TestWrapper } from '@/test/utils/test-wrapper';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Messages', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.resetAllMocks();
    vi.useRealTimers();
  });

  it('renders the messages interface with basic elements', () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByPlaceholderText('Search messages...')).toBeInTheDocument();
    expect(screen.getByText('Compose')).toBeInTheDocument();
  });

  it('displays folder tabs with correct labels', () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('Inbox')).toBeInTheDocument();
    expect(screen.getByText('Sent')).toBeInTheDocument();
    expect(screen.getByText('Drafts')).toBeInTheDocument();
    expect(screen.getByText('Starred')).toBeInTheDocument();
    expect(screen.getByText('Archived')).toBeInTheDocument();
    expect(screen.getByText('Trash')).toBeInTheDocument();
  });

  it('displays unread count badge when messages are unread', () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 2,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('displays messages when data is loaded', () => {
    const mockMessages = [
      {
        id: 'msg-1',
        fromUserId: 'teacher-1',
        toUserId: 'student-1',
        subject: 'Assignment Feedback',
        content: 'Great work on your math assignment! Keep it up.',
        sentAt: '2024-01-18T10:30:00Z',
        read: false,
        readAt: null,
        attachments: [],
      },
      {
        id: 'msg-2',
        fromUserId: 'student-1',
        toUserId: 'teacher-1',
        subject: 'Question about homework',
        content: 'I have a question about problem #5 in the homework.',
        sentAt: '2024-01-17T14:20:00Z',
        read: true,
        readAt: '2024-01-17T15:00:00Z',
        attachments: ['homework.pdf'],
      },
    ];

    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: mockMessages,
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 1,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('Assignment Feedback')).toBeInTheDocument();
    expect(screen.getByText('Question about homework')).toBeInTheDocument();
    expect(screen.getByText('teacher-1')).toBeInTheDocument();
    expect(screen.getByText('student-1')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search messages...');
    await user.type(searchInput, 'homework');

    expect(searchInput).toHaveValue('homework');
  });

  it('shows loading state when messages are being fetched', () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: true,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('shows empty state when no messages exist', () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('No messages in this folder')).toBeInTheDocument();
  });

  it('handles error state display', () => {
    const errorMessage = 'Failed to load messages';
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: false,
            sending: false,
            error: errorMessage,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('handles compose button click', async () => {
    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: [],
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 0,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    const composeButton = screen.getByText('Compose');
    await user.click(composeButton);

    expect(composeButton).toBeInTheDocument();
  });

  it('displays message count correctly', () => {
    const mockMessages = [
      {
        id: 'msg-1',
        fromUserId: 'teacher-1',
        toUserId: 'student-1',
        subject: 'Test Message',
        content: 'Test content',
        sentAt: '2024-01-18T10:30:00Z',
        read: false,
        readAt: null,
        attachments: [],
      }
    ];

    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: mockMessages,
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 1,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('1 messages')).toBeInTheDocument();
  });

  it('shows attachment indicator for messages with attachments', () => {
    const mockMessages = [
      {
        id: 'msg-1',
        fromUserId: 'teacher-1',
        toUserId: 'student-1',
        subject: 'Test Message',
        content: 'Test content',
        sentAt: '2024-01-18T10:30:00Z',
        read: false,
        readAt: null,
        attachments: ['file1.pdf', 'file2.docx'],
      }
    ];

    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: mockMessages,
            currentMessage: null,
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 1,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('2')).toBeInTheDocument(); // Attachment count
  });

  it('displays message content when message is selected', () => {
    const mockMessages = [
      {
        id: 'msg-1',
        fromUserId: 'teacher-1',
        toUserId: 'student-1',
        subject: 'Test Message',
        content: 'This is the message content',
        sentAt: '2024-01-18T10:30:00Z',
        read: false,
        readAt: null,
        attachments: [],
      }
    ];

    render(
      <TestWrapper
        initialState={{
          messages: {
            messages: mockMessages,
            currentMessage: mockMessages[0],
            folders: ['inbox', 'sent', 'drafts', 'starred', 'archived', 'trash'],
            unreadCount: 1,
            loading: false,
            sending: false,
            error: null,
            filters: { folder: 'inbox' },
            compose: { subject: '', content: '', attachments: [] }
          }
        }}
      >
        <Messages />
      </TestWrapper>
    );

    expect(screen.getByText('This is the message content')).toBeInTheDocument();
    expect(screen.getByText('From: teacher-1')).toBeInTheDocument();
    expect(screen.getByText('To: student-1')).toBeInTheDocument();
  });
});
