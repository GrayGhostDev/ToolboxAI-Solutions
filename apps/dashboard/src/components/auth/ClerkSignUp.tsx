/**
 * Clerk Sign-Up Component (2025)
 * Uses Clerk's pre-built sign-up component with custom styling
 */

import React from 'react';
import { SignUp } from '@clerk/clerk-react';
import { Box, Container, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';

const StyledPaper = styled(Paper)(({ theme }) => ({
  marginTop: theme.spacing(8),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: theme.spacing(4),
  borderRadius: theme.spacing(2),
  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
}));

const ClerkSignUp= () => {
  return (
    <Container component="main" maxWidth="sm">
      <StyledPaper>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
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
            redirectUrl={import.meta.env.VITE_CLERK_AFTER_SIGN_UP_URL || '/dashboard'}
            signInUrl={import.meta.env.VITE_CLERK_SIGN_IN_URL}
            unsafeMetadata={{
              role: 'student', // Default role for new users
              onboardingCompleted: false,
            }}
          />
        </Box>
      </StyledPaper>
    </Container>
  );
};

export default ClerkSignUp;