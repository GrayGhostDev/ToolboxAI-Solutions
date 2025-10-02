/**
 * Clerk Sign-In Component (2025)
 * Uses Clerk's pre-built sign-in component with custom styling
 */

import React from 'react';
import { SignIn } from '@clerk/clerk-react';
import { Box, Container, Paper } from '@mantine/core';

const ClerkLogin = () => {
  return (
    <Container size="sm">
      <Paper
        p="xl"
        style={{
          marginTop: '2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        }}
      >
        <Box
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <SignIn
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
                  backgroundColor: '#1976d2',
                  '&:hover': {
                    backgroundColor: '#1565c0',
                  },
                },
                formFieldInput: {
                  borderRadius: '4px',
                },
                footerActionLink: {
                  color: '#1976d2',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                },
              },
              variables: {
                colorPrimary: '#1976d2',
                colorText: '#333',
                colorTextOnPrimaryBackground: '#fff',
                colorBackground: '#fff',
                colorInputBackground: '#f5f5f5',
                colorInputText: '#333',
                colorDanger: '#d32f2f',
                borderRadius: '4px',
                fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
              },
              layout: {
                socialButtonsVariant: 'iconButton',
                socialButtonsPlacement: 'top',
              },
            }}
            redirectUrl={import.meta.env.VITE_CLERK_AFTER_SIGN_IN_URL || '/dashboard'}
            signUpUrl={import.meta.env.VITE_CLERK_SIGN_UP_URL}
          />
        </Box>
      </Paper>
    </Container>
  );
};

export default ClerkLogin;