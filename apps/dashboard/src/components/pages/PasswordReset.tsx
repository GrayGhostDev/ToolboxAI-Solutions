import * as React from 'react';
import {
  Box,
  Card,
  TextInput,
  Button,
  Text,
  Alert,
  Stack,
  Paper,
  Stepper,
  Title,
  Center,
  Container,
  Group
} from '@mantine/core';

import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { IconMail, IconLock, IconCircleCheck } from '@tabler/icons-react';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { apiClient } from '../../services/api';

export default function PasswordReset() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  
  const [activeStep, setActiveStep] = useState(token ? 1 : 0);
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const steps = ['Request Reset', 'Set New Password', 'Complete'];

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Please enter your email address');
      return;
    }
    
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await apiClient['request']({
        method: 'POST',
        url: '/auth/password-reset',
        data: { email },
      });
      
      dispatch(addNotification({
        type: 'success',
        message: 'Password reset email sent! Please check your inbox.',
        autoHide: false,
      }));
      
      setSuccess(true);
      setActiveStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send reset email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newPassword || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }
    
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await apiClient['request']({
        method: 'POST',
        url: '/auth/password-reset-confirm',
        data: { 
          token,
          new_password: newPassword,
        },
      });
      
      dispatch(addNotification({
        type: 'success',
        message: 'Password reset successful! You can now log in with your new password.',
        autoHide: false,
      }));
      
      setActiveStep(2);
      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password. The link may have expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Center
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 16,
      }}
    >
      <Paper
        shadow="xl"
        style={{
          width: '100%',
          maxWidth: 450,
          borderRadius: 12,
          overflow: 'hidden',
        }}
      >
        <Box
          p="xl"
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            textAlign: 'center',
          }}
        >
          <Title order={2} fw={700} mb="xs">
            Password Reset
          </Title>
          <Text size="sm" style={{ opacity: 0.9 }}>
            {token ? 'Set your new password' : 'Reset your ToolBoxAI password'}
          </Text>
        </Box>

        <Box p="xl">
          <Stepper active={activeStep} mb="xl">
            {steps.map((label, index) => (
              <Stepper.Step key={label} label={label} />
            ))}
          </Stepper>

          {error && (
            <Alert color="red" mb="md" radius="md">
              {error}
            </Alert>
          )}

          {/* Step 1: Request Reset */}
          {activeStep === 0 && !token && (
            <form onSubmit={handleRequestReset}>
              <Stack gap="lg">
                <Text size="sm" c="dimmed">
                  Enter your email address and we'll send you a link to reset your password.
                </Text>

                <TextInput
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                  leftSection={<IconMail size={16} />}
                  radius="md"
                />

                <Button
                  type="submit"
                  fullWidth
                  size="md"
                  disabled={loading}
                  radius="md"
                  style={{
                    padding: '12px 16px',
                    fontWeight: 600,
                  }}
                >
                  {loading ? 'Sending...' : 'Send Reset Email'}
                </Button>

                <Center>
                  <Text size="sm" c="dimmed">
                    Remember your password?{' '}
                    <Link
                      to="/login"
                      style={{
                        color: 'inherit',
                        textDecoration: 'none',
                        fontWeight: 600,
                      }}
                    >
                      Back to login
                    </Link>
                  </Text>
                </Center>
              </Stack>
            </form>
          )}

          {/* Step 2: Set New Password */}
          {activeStep === 1 && token && (
            <form onSubmit={handleResetPassword}>
              <Stack gap="lg">
                <Text size="sm" c="dimmed">
                  Please enter your new password below.
                </Text>

                <TextInput
                  label="New Password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  disabled={loading}
                  leftSection={<IconLock size={16} />}
                  radius="md"
                />

                <TextInput
                  label="Confirm New Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  leftSection={<IconLock size={16} />}
                  radius="md"
                />

                <Button
                  type="submit"
                  fullWidth
                  size="md"
                  disabled={loading}
                  radius="md"
                  style={{
                    padding: '12px 16px',
                    fontWeight: 600,
                  }}
                >
                  {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
              </Stack>
            </form>
          )}

          {/* Step 3: Success */}
          {activeStep === 2 && success && (
            <Stack gap="lg" align="center">
              <IconCircleCheck size={64} color="green" />

              <Title order={4} ta="center">
                {token ? 'Password Reset Successful!' : 'Reset Email Sent!'}
              </Title>

              <Text size="sm" c="dimmed" ta="center">
                {token
                  ? 'Your password has been successfully reset. Redirecting to login...'
                  : 'Please check your email for the password reset link. The link will expire in 1 hour.'
                }
              </Text>

              {!token && (
                <Button
                  fullWidth
                  onClick={() => navigate('/login')}
                  radius="md"
                  style={{
                    padding: '12px 16px',
                    fontWeight: 600,
                  }}
                >
                  Back to Login
                </Button>
              )}
            </Stack>
          )}
        </Box>
      </Paper>
    </Center>
  );
}