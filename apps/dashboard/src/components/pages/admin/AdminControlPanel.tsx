import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Tabs, 
  Tab,
  Paper,
  Badge,
  Chip
} from '@mui/material';
import {
  Group,
  School,
  Settings,
  History,
  Assessment,
  Security,
  Storage,
  IntegrationInstructions,
} from '@mui/icons-material';
import UserManagement from './UserManagement';
import Schools from './Schools';
import SystemSettings from './SystemSettings';
import ActivityLogs from './ActivityLogs';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `admin-tab-${index}`,
    'aria-controls': `admin-tabpanel-${index}`,
  };
}

const AdminControlPanel: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const tabs = [
    { label: 'Users', icon: <Group />, badge: null },
    { label: 'Schools', icon: <School />, badge: null },
    { label: 'System Settings', icon: <Settings />, badge: null },
    { label: 'Integrations', icon: <IntegrationInstructions />, badge: null },
    { label: 'Security', icon: <Security />, badge: '3' },
    { label: 'Activity Logs', icon: <History />, badge: 'New' },
    { label: 'Analytics', icon: <Assessment />, badge: null },
    { label: 'Storage', icon: <Storage />, badge: null },
  ];

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 600 }}>
        Admin Control Panel
      </Typography>
      
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="admin control panel tabs"
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              minHeight: 64,
              textTransform: 'none',
            },
          }}
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {tab.icon}
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <Chip
                      label={tab.badge}
                      size="small"
                      color={tab.badge === 'New' ? 'primary' : 'error'}
                      sx={{ height: 20, fontSize: '0.75rem' }}
                    />
                  )}
                </Box>
              }
              {...a11yProps(index)}
            />
          ))}
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          <UserManagement />
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Schools />
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <SystemSettings />
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Integrations Management
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Configure and manage third-party integrations including LMS systems, authentication providers, and API connections.
            </Typography>
            
            <Box sx={{ mt: 3 }}>
              {/* Integration cards */}
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6">Canvas LMS</Typography>
                <Chip label="Connected" color="success" size="small" sx={{ mt: 1 }} />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Last sync: 2 hours ago
                </Typography>
              </Paper>
              
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6">Schoology</Typography>
                <Chip label="Disconnected" color="error" size="small" sx={{ mt: 1 }} />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Click to configure
                </Typography>
              </Paper>
              
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6">Google Classroom</Typography>
                <Chip label="Pending" color="warning" size="small" sx={{ mt: 1 }} />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Authentication required
                </Typography>
              </Paper>
            </Box>
          </Box>
        </TabPanel>
        
        <TabPanel value={tabValue} index={4}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Security Settings
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Manage security policies, authentication settings, and compliance requirements.
            </Typography>
            
            <Box sx={{ mt: 3 }}>
              <Paper sx={{ p: 3, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Security Alerts
                </Typography>
                <Chip label="3 new alerts" color="error" />
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="error">
                    • 5 failed login attempts from IP 192.168.1.100
                  </Typography>
                  <Typography variant="body2" color="warning">
                    • Password policy update required
                  </Typography>
                  <Typography variant="body2" color="info">
                    • SSL certificate expires in 30 days
                  </Typography>
                </Box>
              </Paper>
              
              <Paper sx={{ p: 3, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Compliance Status
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Chip label="FERPA Compliant" color="success" />
                  <Chip label="COPPA Compliant" color="success" />
                  <Chip label="GDPR Ready" color="warning" />
                </Box>
              </Paper>
            </Box>
          </Box>
        </TabPanel>
        
        <TabPanel value={tabValue} index={5}>
          <ActivityLogs />
        </TabPanel>
        
        <TabPanel value={tabValue} index={6}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Platform Analytics
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              View detailed analytics about platform usage, performance metrics, and user engagement.
            </Typography>
            
            <Box sx={{ mt: 3, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h4">1,234</Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Users
                </Typography>
              </Paper>
              
              <Paper sx={{ p: 3 }}>
                <Typography variant="h4">456</Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Sessions
                </Typography>
              </Paper>
              
              <Paper sx={{ p: 3 }}>
                <Typography variant="h4">89%</Typography>
                <Typography variant="body2" color="text.secondary">
                  System Uptime
                </Typography>
              </Paper>
              
              <Paper sx={{ p: 3 }}>
                <Typography variant="h4">2.3s</Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Response Time
                </Typography>
              </Paper>
            </Box>
          </Box>
        </TabPanel>
        
        <TabPanel value={tabValue} index={7}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Storage Management
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              Monitor and manage storage usage across the platform.
            </Typography>
            
            <Box sx={{ mt: 3 }}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Storage Usage
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    Used: 45.2 GB / 100 GB (45.2%)
                  </Typography>
                  <Box sx={{ 
                    width: '100%', 
                    height: 20, 
                    bgcolor: 'grey.200', 
                    borderRadius: 1, 
                    mt: 1,
                    position: 'relative',
                    overflow: 'hidden'
                  }}>
                    <Box sx={{ 
                      width: '45.2%', 
                      height: '100%', 
                      bgcolor: 'primary.main',
                      borderRadius: 1
                    }} />
                  </Box>
                </Box>
                
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Storage Breakdown
                  </Typography>
                  <Typography variant="body2">• User Files: 25.3 GB</Typography>
                  <Typography variant="body2">• Course Content: 12.8 GB</Typography>
                  <Typography variant="body2">• System Files: 5.1 GB</Typography>
                  <Typography variant="body2">• Backups: 2.0 GB</Typography>
                </Box>
              </Paper>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default AdminControlPanel;