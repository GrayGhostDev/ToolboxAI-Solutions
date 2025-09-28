import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as api from '../../services/api';

interface ComplianceStatus {
  coppa: {
    status: 'compliant' | 'warning' | 'violation';
    score: number;
    issues: string[];
    lastAudit: string;
    nextAudit: string;
  };
  ferpa: {
    status: 'compliant' | 'warning' | 'violation';
    score: number;
    issues: string[];
    lastAudit: string;
    nextAudit: string;
  };
  gdpr: {
    status: 'compliant' | 'warning' | 'violation';
    score: number;
    issues: string[];
    lastAudit: string;
    nextAudit: string;
  };
  ccpa?: {
    status: 'compliant' | 'warning' | 'violation';
    score: number;
    issues: string[];
    lastAudit: string;
    nextAudit: string;
  };
}

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  userId: string;
  userEmail: string;
  regulation: string;
  status: string;
  details: string;
  ipAddress?: string;
}

interface ConsentRecord {
  id: string;
  studentId: string;
  studentName: string;
  parentId?: string;
  parentName?: string;
  parentEmail?: string;
  consentType: 'coppa' | 'ferpa' | 'gdpr' | 'marketing' | 'photos';
  status: 'active' | 'expired' | 'revoked' | 'pending';
  dateProvided: string;
  expiryDate?: string;
  revokedDate?: string;
  signatureUrl?: string;
}

interface DataRetentionPolicy {
  dataType: string;
  retentionDays: number;
  deletionSchedule: string;
  lastPurge?: string;
  nextPurge: string;
}

interface ComplianceState {
  status: ComplianceStatus | null;
  auditLogs: AuditLog[];
  consentRecords: ConsentRecord[];
  dataRetention: DataRetentionPolicy[];
  pendingConsents: number;
  overallScore: number;
  loading: boolean;
  error: string | null;
  lastChecked: string | null;
}

const initialState: ComplianceState = {
  status: null,
  auditLogs: [],
  consentRecords: [],
  dataRetention: [],
  pendingConsents: 0,
  overallScore: 0,
  loading: false,
  error: null,
  lastChecked: null,
};

// Async thunks
export const fetchComplianceStatus = createAsyncThunk(
  'compliance/fetchStatus',
  async () => {
    const response = await api.getComplianceStatus();
    return response;
  }
);

export const recordConsent = createAsyncThunk(
  'compliance/recordConsent',
  async ({ type, userId, parentId, signature }: { 
    type: 'coppa' | 'ferpa' | 'gdpr'; 
    userId: string; 
    parentId?: string;
    signature?: string;
  }) => {
    await api.recordConsent(type, userId);
    // Return the data for optimistic update
    return { type, userId, parentId, signature, timestamp: new Date().toISOString() };
  }
);

export const fetchAuditLogs = createAsyncThunk(
  'compliance/fetchAuditLogs',
  async (filters?: { regulation?: string; startDate?: string; endDate?: string }) => {
    // This would call a specific audit logs endpoint with filters
    console.error('Fetching audit logs with filters:', filters);
    
    // Apply filters to mock data generation
    let mockLogs: AuditLog[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        action: 'Data Access',
        userId: 'user1',
        userEmail: 'admin@school.edu',
        regulation: 'FERPA',
        status: 'Approved',
        details: 'Accessed student records for report generation',
        ipAddress: '192.168.1.1',
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        action: 'Consent Updated',
        userId: 'parent1',
        userEmail: 'parent@email.com',
        regulation: 'COPPA',
        status: 'Completed',
        details: 'Parent provided consent for data collection',
        ipAddress: '192.168.1.2',
      },
    ];
    
    // Apply filters if provided
    if (filters?.regulation) {
      mockLogs = mockLogs.filter(log => log.regulation === filters.regulation);
    }
    if (filters?.startDate) {
      mockLogs = mockLogs.filter(log => new Date(log.timestamp) >= new Date(filters.startDate!));
    }
    if (filters?.endDate) {
      mockLogs = mockLogs.filter(log => new Date(log.timestamp) <= new Date(filters.endDate!));
    }
    
    return mockLogs;
  }
);

export const fetchConsentRecords = createAsyncThunk(
  'compliance/fetchConsents',
  async (studentId?: string) => {
    // This would call a specific consent records endpoint for the student
    console.error('Fetching consent records for student:', studentId);
    
    // Generate mock data filtered by studentId if provided
    const mockConsents: ConsentRecord[] = [
      {
        id: '1',
        studentId: 'student1',
        studentName: 'John Doe',
        parentId: 'parent1',
        parentName: 'Jane Doe',
        parentEmail: 'jane.doe@email.com',
        consentType: 'coppa',
        status: 'active',
        dateProvided: new Date(Date.now() - 30 * 86400000).toISOString(),
        expiryDate: new Date(Date.now() + 335 * 86400000).toISOString(),
      },
      {
        id: '2',
        studentId: 'student2',
        studentName: 'Alice Smith',
        parentId: 'parent2',
        parentName: 'Bob Smith',
        parentEmail: 'bob.smith@email.com',
        consentType: 'ferpa',
        status: 'active',
        dateProvided: new Date(Date.now() - 60 * 86400000).toISOString(),
        expiryDate: new Date(Date.now() + 305 * 86400000).toISOString(),
      },
    ];
    
    // Filter by studentId if provided
    if (studentId) {
      return mockConsents.filter(consent => consent.studentId === studentId);
    }
    
    return mockConsents;
  }
);

export const revokeConsent = createAsyncThunk(
  'compliance/revokeConsent',
  async (consentId: string) => {
    // This would call an API to revoke consent
    return { consentId, revokedDate: new Date().toISOString() };
  }
);

export const runComplianceAudit = createAsyncThunk(
  'compliance/runAudit',
  async (regulation?: 'coppa' | 'ferpa' | 'gdpr' | 'all') => {
    // This would trigger a compliance audit
    return { regulation, timestamp: new Date().toISOString() };
  }
);

export const exportComplianceReport = createAsyncThunk(
  'compliance/exportReport',
  async (format: 'pdf' | 'csv' | 'json' = 'pdf') => {
    // This would generate and download a compliance report
    return { format, url: `/api/v1/compliance/report.${format}` };
  }
);

const complianceSlice = createSlice({
  name: 'compliance',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    updateConsentStatus: (state, action: PayloadAction<{ consentId: string; status: ConsentRecord['status'] }>) => {
      const consent = state.consentRecords.find(c => c.id === action.payload.consentId);
      if (consent) {
        consent.status = action.payload.status;
      }
    },
    addAuditLog: (state, action: PayloadAction<AuditLog>) => {
      state.auditLogs.unshift(action.payload);
      // Keep only the latest 100 logs
      if (state.auditLogs.length > 100) {
        state.auditLogs = state.auditLogs.slice(0, 100);
      }
    },
    incrementPendingConsents: (state) => {
      state.pendingConsents += 1;
    },
    decrementPendingConsents: (state) => {
      state.pendingConsents = Math.max(0, state.pendingConsents - 1);
    },
  },
  extraReducers: (builder) => {
    // Fetch compliance status
    builder
      .addCase(fetchComplianceStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchComplianceStatus.fulfilled, (state, action) => {
        state.loading = false;
        state.status = action.payload;
        state.lastChecked = new Date().toISOString();
        
        // Calculate overall score
        const scores = [];
        if (action.payload.coppa) scores.push(action.payload.coppa.score || 0);
        if (action.payload.ferpa) scores.push(action.payload.ferpa.score || 0);
        if (action.payload.gdpr) scores.push(action.payload.gdpr.score || 0);
        if (action.payload.ccpa) scores.push(action.payload.ccpa.score || 0);
        
        state.overallScore = scores.length > 0 
          ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
          : 0;
          
        // Count pending consents (issues)
        let pendingCount = 0;
        if (action.payload.coppa?.issues) pendingCount += action.payload.coppa.issues.length;
        if (action.payload.ferpa?.issues) pendingCount += action.payload.ferpa.issues.length;
        if (action.payload.gdpr?.issues) pendingCount += action.payload.gdpr.issues.length;
        state.pendingConsents = pendingCount;
      })
      .addCase(fetchComplianceStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch compliance status';
      });

    // Record consent
    builder
      .addCase(recordConsent.fulfilled, (state, action) => {
        // Add to consent records
        const newConsent: ConsentRecord = {
          id: Date.now().toString(),
          studentId: action.payload.userId,
          studentName: 'Student',
          parentId: action.payload.parentId,
          consentType: action.payload.type,
          status: 'active',
          dateProvided: action.payload.timestamp,
          expiryDate: new Date(Date.now() + 365 * 86400000).toISOString(),
        };
        state.consentRecords.unshift(newConsent);
        
        // Add audit log
        const auditLog: AuditLog = {
          id: Date.now().toString(),
          timestamp: action.payload.timestamp,
          action: 'Consent Recorded',
          userId: action.payload.userId,
          userEmail: 'user@email.com',
          regulation: action.payload.type.toUpperCase(),
          status: 'Completed',
          details: `${action.payload.type.toUpperCase()} consent recorded`,
        };
        state.auditLogs.unshift(auditLog);
        
        // Decrement pending consents
        state.pendingConsents = Math.max(0, state.pendingConsents - 1);
      });

    // Fetch audit logs
    builder
      .addCase(fetchAuditLogs.fulfilled, (state, action) => {
        state.auditLogs = action.payload;
      });

    // Fetch consent records
    builder
      .addCase(fetchConsentRecords.fulfilled, (state, action) => {
        state.consentRecords = action.payload;
      });

    // Revoke consent
    builder
      .addCase(revokeConsent.fulfilled, (state, action) => {
        const consent = state.consentRecords.find(c => c.id === action.payload.consentId);
        if (consent) {
          consent.status = 'revoked';
          consent.revokedDate = action.payload.revokedDate;
        }
      });
  },
});

export const { 
  clearError, 
  updateConsentStatus, 
  addAuditLog,
  incrementPendingConsents,
  decrementPendingConsents 
} = complianceSlice.actions;

export default complianceSlice.reducer;