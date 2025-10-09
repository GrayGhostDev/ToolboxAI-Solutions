import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import * as api from '../../services/api';
import type { Message } from '../../types/api';

interface MessagesState {
  messages: Message[];
  currentMessage: Message | null;
  folders: {
    inbox: Message[];
    sent: Message[];
    drafts: Message[];
    starred: Message[];
    archived: Message[];
    trash: Message[];
  };
  unreadCount: number;
  loading: boolean;
  sending: boolean;
  error: string | null;
  filters: {
    folder: 'inbox' | 'sent' | 'drafts' | 'starred' | 'archived' | 'trash' | 'all';
    unreadOnly: boolean;
    classId?: string;
    search?: string;
  };
  compose: {
    isOpen: boolean;
    recipients: string[];
    subject: string;
    content: string;
    attachments: string[];
    replyTo?: string;
  };
}

const initialState: MessagesState = {
  messages: [],
  currentMessage: null,
  folders: {
    inbox: [],
    sent: [],
    drafts: [],
    starred: [],
    archived: [],
    trash: [],
  },
  unreadCount: 0,
  loading: false,
  sending: false,
  error: null,
  filters: {
    folder: 'inbox',
    unreadOnly: false,
  },
  compose: {
    isOpen: false,
    recipients: [],
    subject: '',
    content: '',
    attachments: [],
  },
};

// Async thunks
export const fetchMessages = createAsyncThunk(
  'messages/fetchAll',
  async (filters?: {
    folder?: string;
    unreadOnly?: boolean;
    classId?: string;
    search?: string;
  }) => {
    // Check if we're in bypass mode
    const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (bypassAuth || useMockData) {
      // Import mock data
      const { mockMessages } = await import('../../services/mock-data');
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 100));

      // Filter messages based on folder
      let filteredMessages = mockMessages;
      if (filters?.folder === 'starred') {
        filteredMessages = mockMessages.filter(m => m.starred);
      } else if (filters?.unreadOnly) {
        filteredMessages = mockMessages.filter(m => !m.read);
      }

      return { messages: filteredMessages, folder: filters?.folder || 'inbox' };
    }

    const response = await api.listMessages(
      filters?.folder,
      {
        unread_only: filters?.unreadOnly,
        class_id: filters?.classId,
        search: filters?.search,
      }
    );
    return { messages: response, folder: filters?.folder || 'inbox' };
  }
);

export const fetchMessageById = createAsyncThunk(
  'messages/fetchById',
  async (messageId: string) => {
    const response = await api.getMessage(messageId);
    return response;
  }
);

export const sendMessage = createAsyncThunk(
  'messages/send',
  async (data: {
    toUserId: string | string[];
    subject: string;
    content: string;
    attachments?: string[];
    replyTo?: string;
    isAnnouncement?: boolean;
    classId?: string;
  }) => {
    const recipient_ids = Array.isArray(data.toUserId) ? data.toUserId : [data.toUserId];
    const response = await api.sendMessage({
      subject: data.subject,
      body: data.content,
      recipient_ids,
      class_id: data.classId,
    });
    return response;
  }
);

export const replyToMessage = createAsyncThunk(
  'messages/reply',
  async ({ messageId, content }: { messageId: string; content: string }) => {
    const response = await api.replyToMessage(messageId, { subject: '', body: content, recipient_ids: [] });
    return response;
  }
);

export const forwardMessage = createAsyncThunk(
  'messages/forward',
  async ({ messageId, toUserId, comment }: {
    messageId: string;
    toUserId: string | string[];
    comment?: string;
  }) => {
    const response = await api.forwardMessage(messageId, {
      subject: 'FWD',
      body: comment || '',
      recipient_ids: Array.isArray(toUserId) ? toUserId : [toUserId],
    });
    return response;
  }
);

export const markAsRead = createAsyncThunk(
  'messages/markRead',
  async (messageIds: string | string[]) => {
    const ids = Array.isArray(messageIds) ? messageIds : [messageIds];
    const promises = ids.map(id => api.markAsRead(id));
    await Promise.all(promises);
    return ids;
  }
);

export const moveToFolder = createAsyncThunk(
  'messages/moveToFolder',
  async ({ messageId, folder }: { messageId: string; folder: string }) => {
    const response = await api.moveToFolder(messageId, folder);
    return { messageId, folder, message: response };
  }
);

export const deleteMessage = createAsyncThunk(
  'messages/delete',
  async (messageId: string) => {
    await api.deleteMessage(messageId);
    return messageId;
  }
);

export const searchMessages = createAsyncThunk(
  'messages/search',
  async (query: string) => {
    const response = await api.searchMessages(query);
    return response;
  }
);

export const getUnreadCount = createAsyncThunk(
  'messages/unreadCount',
  async () => {
    const response = await api.getUnreadCount();
    return response;
  }
);

const messagesSlice = createSlice({
  name: 'messages',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<MessagesState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        folder: 'inbox',
        unreadOnly: false,
      };
    },
    setCurrentMessage: (state, action: PayloadAction<Message | null>) => {
      state.currentMessage = action.payload;
    },
    openCompose: (state, action: PayloadAction<Partial<MessagesState['compose']>>) => {
      state.compose = {
        ...state.compose,
        ...action.payload,
        isOpen: true,
      };
    },
    closeCompose: (state) => {
      state.compose = {
        isOpen: false,
        recipients: [],
        subject: '',
        content: '',
        attachments: [],
      };
    },
    updateCompose: (state, action: PayloadAction<Partial<MessagesState['compose']>>) => {
      state.compose = { ...state.compose, ...action.payload };
    },
    clearError: (state) => {
      state.error = null;
    },
    updateMessageInList: (state, action: PayloadAction<Message>) => {
      const index = state.messages.findIndex(m => m.id === action.payload.id);
      if (index !== -1) {
        state.messages[index] = action.payload;
      }
      
      // Update in folders
      Object.keys(state.folders).forEach(folder => {
        const folderIndex = state.folders[folder as keyof typeof state.folders].findIndex(
          m => m.id === action.payload.id
        );
        if (folderIndex !== -1) {
          state.folders[folder as keyof typeof state.folders][folderIndex] = action.payload;
        }
      });
    },
  },
  extraReducers: (builder) => {
    // Fetch messages
    builder
      .addCase(fetchMessages.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.loading = false;
        state.messages = action.payload.messages;
        const folderName = action.payload.folder as MessagesState['filters']['folder'];
        if (folderName !== 'all') {
          const folder = folderName as keyof typeof state.folders;
          state.folders[folder] = action.payload.messages;
        }
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch messages';
      });

    // Fetch message by ID
    builder
      .addCase(fetchMessageById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMessageById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentMessage = action.payload;
      })
      .addCase(fetchMessageById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch message';
      });

    // Send message
    builder
      .addCase(sendMessage.pending, (state) => {
        state.sending = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.sending = false;
        state.folders.sent.unshift(action.payload);
        state.compose = {
          isOpen: false,
          recipients: [],
          subject: '',
          content: '',
          attachments: [],
        };
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.sending = false;
        state.error = action.error.message || 'Failed to send message';
      });

    // Reply to message
    builder
      .addCase(replyToMessage.pending, (state) => {
        state.sending = true;
        state.error = null;
      })
      .addCase(replyToMessage.fulfilled, (state, action) => {
        state.sending = false;
        state.folders.sent.unshift(action.payload);
      })
      .addCase(replyToMessage.rejected, (state, action) => {
        state.sending = false;
        state.error = action.error.message || 'Failed to send reply';
      });

    // Forward message
    builder
      .addCase(forwardMessage.pending, (state) => {
        state.sending = true;
        state.error = null;
      })
      .addCase(forwardMessage.fulfilled, (state, action) => {
        state.sending = false;
        state.folders.sent.unshift(action.payload);
      })
      .addCase(forwardMessage.rejected, (state, action) => {
        state.sending = false;
        state.error = action.error.message || 'Failed to forward message';
      });

    // Mark as read
    builder
      .addCase(markAsRead.fulfilled, (state, action) => {
        action.payload.forEach(messageId => {
          const message = state.messages.find(m => m.id === messageId);
          if (message) {
            message.read = true;
          }
          
          // Update in folders
          Object.keys(state.folders).forEach(folder => {
            const folderMessage = state.folders[folder as keyof typeof state.folders].find(
              m => m.id === messageId
            );
            if (folderMessage) {
              folderMessage.read = true;
            }
          });
        });
        
        // Update unread count
        state.unreadCount = Math.max(0, state.unreadCount - action.payload.length);
      });

    // Move to folder
    builder
      .addCase(moveToFolder.fulfilled, (state, action) => {
        const { messageId, folder } = action.payload;
        
        // Remove from all folders
        Object.keys(state.folders).forEach(f => {
          state.folders[f as keyof typeof state.folders] = state.folders[
            f as keyof typeof state.folders
          ].filter(m => m.id !== messageId);
        });
        
        // Add to new folder
        if (folder !== 'all' && state.folders[folder as keyof typeof state.folders]) {
          state.folders[folder as keyof typeof state.folders].push(action.payload.message);
        }
      });

    // Delete message
    builder
      .addCase(deleteMessage.fulfilled, (state, action) => {
        state.messages = state.messages.filter(m => m.id !== action.payload);
        
        // Remove from all folders
        Object.keys(state.folders).forEach(folder => {
          state.folders[folder as keyof typeof state.folders] = state.folders[
            folder as keyof typeof state.folders
          ].filter(m => m.id !== action.payload);
        });
        
        if (state.currentMessage?.id === action.payload) {
          state.currentMessage = null;
        }
      });

    // Search messages
    builder
      .addCase(searchMessages.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchMessages.fulfilled, (state, action) => {
        state.loading = false;
        state.messages = action.payload;
      })
      .addCase(searchMessages.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to search messages';
      });

    // Get unread count
    builder
      .addCase(getUnreadCount.fulfilled, (state, action) => {
        state.unreadCount = action.payload;
      });
  },
});

export const {
  setFilters,
  clearFilters,
  setCurrentMessage,
  openCompose,
  closeCompose,
  updateCompose,
  clearError,
  updateMessageInList,
} = messagesSlice.actions;

export default messagesSlice.reducer;