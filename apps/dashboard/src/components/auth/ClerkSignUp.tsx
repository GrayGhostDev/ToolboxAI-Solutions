/**
 * Clerk Sign-Up Component (2025)
 * Uses Clerk's pre-built sign-up component with custom styling
 * Migrated to Mantine v8
 */

import React from 'react';
import { SignUp } from '@clerk/clerk-react';
import { Box, Container, Paper } from '@mantine/core';

const ClerkSignUp = () => {
  return (
    <Container size="sm" style={{ marginTop: '4rem' }}>
      <Paper
        shadow="md"
        p="xl"
        radius="md"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Box style={{ width: '100%' }}>
          <SignUp
            appearance={{
              elements: {
                rootBox: {
                  width: '100%',
                },
                card: {
                  boxShadow: 'none',
                  border: 'none',
                },
                headerTitle: {
                  fontSize: '24px',
                  fontWeight: 600,
                  marginBottom: '8px',
                },
                headerSubtitle: {
                  fontSize: '14px',
                  color: '#666',
                },
                formButtonPrimary: {
                  backgroundColor: '#00bfff', // Electric blue
                  '&:hover': {
                    backgroundColor: '#0099cc',
                  },
                },
                formFieldInput: {
                  borderRadius: '4px',
                },
                footerActionLink: {
                  color: '#00bfff',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                },
              },
              variables: {
                colorPrimary: '#00bfff', // Electric blue from Roblox theme
                colorText: '#333',
                colorTextOnPrimaryBackground: '#fff',
                colorBackground: '#fff',
                colorInputBackground: '#f5f5f5',
                colorInputText: '#333',
                colorDanger: '#ff0055',
                borderRadius: '4px',
                fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
              },
              layout: {
                socialButtonsVariant: 'iconButton',
                socialButtonsPlacement: 'top',
              },
            }}
            redirectUrl={import.meta.env.VITE_CLERK_AFTER_SIGN_UP_URL || '/dashboard'}
            signInUrl={import.meta.env.VITE_CLERK_SIGN_IN_URL}
            unsafeMetadata={{
              role: 'student', // Default role for new users
              onboardingCompleted: false,
            }}
          />
        </Box>
      </Paper>
    </Container>
  );
};

export default ClerkSignUp;
