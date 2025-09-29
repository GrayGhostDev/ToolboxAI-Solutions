import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import React from 'react';
import { ButtonMigrationExample } from '../migration/examples/ButtonMigration';
import { CardMigrationExample } from '../migration/examples/CardMigration';
import { MantineMigrationGuide } from '../migration/MantineMigrationGuide';
import { useMigrationPlanner } from '../../hooks/useMigration';

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
      id={`migration-tabpanel-${index}`}
      aria-labelledby={`migration-tab-${index}`}
      {...other}
    >
      {value === index && <Box style={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `migration-tab-${index}`,
    'aria-controls': `migration-tabpanel-${index}`,
  };
}

export default function MigrationDemo() {
  const [value, setValue] = React.useState(0);
  const { getMigrationProgress, getNextComponents, getMigrationPlan } = useMigrationPlanner();

  const progress = getMigrationProgress();
  const nextComponents = getNextComponents();
  const plan = getMigrationPlan();

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Container maxWidth="lg" style={{ py: 4 }}>
      <Typography order={3} component="h1" gutterBottom>
        Mantine Migration Demo
      </Typography>

      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Interactive demonstration of the MUI to Mantine migration process
      </Typography>

      {/* Migration Progress Summary */}
      <Box style={{
        mt: 3,
        p: 2,
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider'
      }}>
        <Typography order={6} gutterBottom>
          Migration Progress
        </Typography>
        <Box style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography size="sm" color="text.secondary">
              Total Components
            </Typography>
            <Typography order={4} color="primary.main">
              {progress.total}
            </Typography>
          </Box>
          <Box>
            <Typography size="sm" color="text.secondary">
              Completed
            </Typography>
            <Typography order={4} color="success.main">
              {progress.completed}
            </Typography>
          </Box>
          <Box>
            <Typography size="sm" color="text.secondary">
              In Progress
            </Typography>
            <Typography order={4} color="warning.main">
              {progress.inProgress}
            </Typography>
          </Box>
          <Box>
            <Typography size="sm" color="text.secondary">
              Progress
            </Typography>
            <Typography order={4} color="info.main">
              {progress.completionPercentage.toFixed(1)}%
            </Typography>
          </Box>
        </Box>
      </Box>

      <Box style={{ borderBottom: 1, borderColor: 'divider', mt: 4 }}>
        <Tabs value={value} onChange={handleChange} aria-label="migration demo tabs">
          <Tab label="Component Examples" {...a11yProps(0)} />
          <Tab label="Migration Guide" {...a11yProps(1)} />
          <Tab label="Migration Plan" {...a11yProps(2)} />
          <Tab label="Next Steps" {...a11yProps(3)} />
        </Tabs>
      </Box>

      <TabPanel value={value} index={0}>
        <Typography order={5} gutterBottom>
          Interactive Component Examples
        </Typography>
        <Typography size="md" color="text.secondary" paragraph>
          See side-by-side comparisons of MUI and Mantine components. Use the Migration Control Panel
          (bottom right) to switch between versions or enable comparison mode.
        </Typography>

        <Box style={{ mt: 4 }}>
          <Typography order={6} gutterBottom>
            Button Migration
          </Typography>
          <ButtonMigrationExample />
        </Box>

        <Box style={{ mt: 4 }}>
          <Typography order={6} gutterBottom>
            Card Migration
          </Typography>
          <CardMigrationExample />
        </Box>
      </TabPanel>

      <TabPanel value={value} index={1}>
        <MantineMigrationGuide />
      </TabPanel>

      <TabPanel value={value} index={2}>
        <Typography order={5} gutterBottom>
          Migration Plan Overview
        </Typography>
        <Typography size="md" color="text.secondary" paragraph>
          Comprehensive plan for migrating all components from MUI to Mantine.
        </Typography>

        <Box style={{ mt: 3 }}>
          <Typography order={6} gutterBottom>
            Component Status
          </Typography>
          <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
            {plan.map((component: any) => (
              <Box
                key={component.id}
                style={{
                  p: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  bgcolor: component.phase === 'complete' ? 'success.light' :
                          component.phase === 'development' ? 'warning.light' :
                          'background.paper'
                }}
              >
                <Typography variant="subtitle1" fontWeight="bold">
                  {component.name}
                </Typography>
                <Typography size="sm" color="text.secondary">
                  Phase: {component.phase} | Priority: {component.priority}
                </Typography>
                {component.notes && (
                  <Typography variant="caption" display="block" style={{ mt: 1 }}>
                    {component.notes}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={value} index={3}>
        <Typography order={5} gutterBottom>
          Next Components to Migrate
        </Typography>
        <Typography size="md" color="text.secondary" paragraph>
          These are the highest priority components ready for migration.
        </Typography>

        <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
          {nextComponents.map((component: any) => (
            <Box
              key={component.id}
              style={{
                p: 3,
                border: '2px solid',
                borderColor: 'primary.main',
                borderRadius: 2,
                bgcolor: 'primary.light',
                color: 'primary.contrastText'
              }}
            >
              <Typography order={6} gutterBottom>
                {component.name}
              </Typography>
              <Typography size="sm" style={{ opacity: 0.9 }}>
                Priority: {component.priority}
              </Typography>
              {component.notes && (
                <Typography size="sm" style={{ mt: 1, opacity: 0.8 }}>
                  {component.notes}
                </Typography>
              )}
            </Box>
          ))}
        </Box>

        {nextComponents.length === 0 && (
          <Box style={{
            textAlign: 'center',
            py: 4,
            bgcolor: 'success.light',
            borderRadius: 2,
            color: 'success.contrastText'
          }}>
            <Typography order={6} gutterBottom>
              🎉 All Components Migrated!
            </Typography>
            <Typography size="md">
              Congratulations! You've successfully migrated all planned components to Mantine.
            </Typography>
          </Box>
        )}

        <Box style={{ mt: 4, p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
          <Typography order={6} gutterBottom>
            Development Tools
          </Typography>
          <Typography size="sm" color="text.secondary">
            • Use the Migration Control Panel (bottom right) to test different versions
            • Set localStorage flag 'enableMantineMigration' to 'true' for global migration
            • Individual components can be controlled with 'migration-[component-id]' flags
          </Typography>
        </Box>
      </TabPanel>
    </Container>
  );
}