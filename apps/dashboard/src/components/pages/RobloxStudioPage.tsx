/**
 * RobloxStudioPage Component
 *
 * A dedicated page for the Roblox Studio Integration
 * Ensures the component is displayed properly without overlaying other content
 */

import React from 'react';
import Box from '@mui/material/Box';
import RobloxStudioIntegration from '../roblox/RobloxStudioIntegration';

const RobloxStudioPage: React.FunctionComponent<Record<string, any>> = () => {
  // Simple, stable container without any complex positioning or scroll prevention
  return (
    <Box
      sx={{
        width: '100%',
        height: 'calc(100vh - 140px)',  // Simple height calculation for navbar + toolbar + padding
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',  // Contain children but no complex scroll prevention
        position: 'relative'
      }}
    >
      <RobloxStudioIntegration />
    </Box>
  );
};

export default RobloxStudioPage;