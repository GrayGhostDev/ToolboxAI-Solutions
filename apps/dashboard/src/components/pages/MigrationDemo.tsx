import React from 'react';
import { Container, Typography, Tabs, Tab, Box } from '@mui/material';
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
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        Mantine Migration Demo
      </Typography>

      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Interactive demonstration of the MUI to Mantine migration process
      </Typography>

      {/* Migration Progress Summary */}
      <Box sx={{
        mt: 3,
        p: 2,
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider'
      }}>
        <Typography variant="h6" gutterBottom>
          Migration Progress
        </Typography>
        <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Total Components
            </Typography>
            <Typography variant="h4" color="primary.main">
              {progress.total}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Completed
            </Typography>
            <Typography variant="h4" color="success.main">
              {progress.completed}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              In Progress
            </Typography>
            <Typography variant="h4" color="warning.main">
              {progress.inProgress}
            </Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Progress
            </Typography>
            <Typography variant="h4" color="info.main">
              {progress.completionPercentage.toFixed(1)}%
            </Typography>
          </Box>
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 4 }}>
        <Tabs value={value} onChange={handleChange} aria-label="migration demo tabs">
          <Tab label="Component Examples" {...a11yProps(0)} />
          <Tab label="Migration Guide" {...a11yProps(1)} />
          <Tab label="Migration Plan" {...a11yProps(2)} />
          <Tab label="Next Steps" {...a11yProps(3)} />
        </Tabs>
      </Box>

      <TabPanel value={value} index={0}>
        <Typography variant="h5" gutterBottom>
          Interactive Component Examples
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          See side-by-side comparisons of MUI and Mantine components. Use the Migration Control Panel
          (bottom right) to switch between versions or enable comparison mode.
        </Typography>

        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Button Migration
          </Typography>
          <ButtonMigrationExample />
        </Box>

        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Card Migration
          </Typography>
          <CardMigrationExample />
        </Box>
      </TabPanel>

      <TabPanel value={value} index={1}>
        <MantineMigrationGuide />
      </TabPanel>

      <TabPanel value={value} index={2}>
        <Typography variant="h5" gutterBottom>
          Migration Plan Overview
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Comprehensive plan for migrating all components from MUI to Mantine.
        </Typography>

        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Component Status
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
            {plan.map((component: any) => (
              <Box
                key={component.id}
                sx={{
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
                <Typography variant="body2" color="text.secondary">
                  Phase: {component.phase} | Priority: {component.priority}
                </Typography>
                {component.notes && (
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    {component.notes}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={value} index={3}>
        <Typography variant="h5" gutterBottom>
          Next Components to Migrate
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          These are the highest priority components ready for migration.
        </Typography>

        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
          {nextComponents.map((component: any) => (
            <Box
              key={component.id}
              sx={{
                p: 3,
                border: '2px solid',
                borderColor: 'primary.main',
                borderRadius: 2,
                bgcolor: 'primary.light',
                color: 'primary.contrastText'
              }}
            >
              <Typography variant="h6" gutterBottom>
                {component.name}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Priority: {component.priority}
              </Typography>
              {component.notes && (
                <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
                  {component.notes}
                </Typography>
              )}
            </Box>
          ))}
        </Box>

        {nextComponents.length === 0 && (
          <Box sx={{
            textAlign: 'center',
            py: 4,
            bgcolor: 'success.light',
            borderRadius: 2,
            color: 'success.contrastText'
          }}>
            <Typography variant="h6" gutterBottom>
              🎉 All Components Migrated!
            </Typography>
            <Typography variant="body1">
              Congratulations! You've successfully migrated all planned components to Mantine.
            </Typography>
          </Box>
        )}

        <Box sx={{ mt: 4, p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            Development Tools
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Use the Migration Control Panel (bottom right) to test different versions
            • Set localStorage flag 'enableMantineMigration' to 'true' for global migration
            • Individual components can be controlled with 'migration-[component-id]' flags
          </Typography>
        </Box>
      </TabPanel>
    </Container>
  );
}