import React, { useState } from 'react';
import {
  Container,
  Paper,
  Title,
  Text,
  TextInput,
  PasswordInput,
  Stack,
  Alert,
  Divider,
  Anchor,
  Group,
  Box,
  Gradient,
  rem
} from '@mantine/core';
import AtomicButton from '../atomic/atoms/Button';
import { notifications } from '@mantine/notifications';
import {
  IconMail,
  IconLock,
  IconAlertCircle,
  IconCheck
} from '@tabler/icons-react';
import { Link, useNavigate } from 'react-router-dom';
import { login } from '../../services/api';
import { useAppDispatch } from '../../store';
import { signInSuccess } from '../../store/slices/userSlice';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from '../../config';
import { pusherService } from '../../services/pusher';
import { logger } from '../../utils/logger';

export default function LoginMantine() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: string) => (value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.email || !formData.password) {
      setError('Email and password are required');
      return false;
    }

    // Basic email format validation - check if it's not a username (contains _)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isUsername = formData.email.includes('_') || !formData.email.includes('@');
    if (!isUsername && !emailRegex.test(formData.email)) {
      setError('Please enter a valid email address or username');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      const response = await login(formData.email, formData.password);

      // Debug logging to see response structure
      logger.debug('Login response structure', response);

      // Map backend response to expected format (backend uses snake_case)
      const accessToken = response.accessToken || (response as any).access_token;
      const refreshToken = response.refreshToken || (response as any).refresh_token;

      // Store tokens
      localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
      localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);

      // Connect to Pusher for realtime features after successful login
      // Don't let Pusher errors prevent login
      try {
        pusherService.connect();
        logger.info('Connected to Pusher for realtime features');
      } catch (pusherError) {
        logger.warn('Pusher connection failed, continuing without realtime features', pusherError);
      }

      // Get role from either user object or top-level
      const userRole = response.user?.role || response.role || 'student';
      logger.debug('Setting user role', { role: userRole });

      // Update Redux state
      dispatch(signInSuccess({
        userId: response.user?.id || 1,
        email: response.user?.email || formData.email,
        displayName: response.user?.displayName || response.user?.username || formData.email.split('@')[0],
        avatarUrl: response.user?.avatarUrl,
        role: userRole as any,
        token: accessToken,
        refreshToken: refreshToken,
        schoolId: response.user.schoolId,
        classIds: response.user.classIds,
      }));

      // Show success notification
      notifications.show({
        title: 'Welcome back!',
        message: 'You have successfully signed in.',
        color: 'green',
        icon: <IconCheck size={rem(18)} />,
      });

      // Navigate to dashboard
      navigate('/');
    } catch (err: any) {
      const errorMessage = err.message || 'Login failed. Please check your credentials.';
      setError(errorMessage);

      // Show error notification
      notifications.show({
        title: 'Login Failed',
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle size={rem(18)} />,
      });
    } finally {
      setLoading(false);
    }
  };

  const demoCredentials = [
    { role: 'Admin', email: 'admin@toolboxai.com', password: 'Admin123!' },
    { role: 'Teacher', email: 'jane.smith@school.edu', password: 'Teacher123!' },
    { role: 'Student', email: 'alex.johnson@student.edu', password: 'Student123!' },
  ];

  const fillDemoCredentials = (email: string, password: string) => {
    setFormData({ email, password });
    setError('');
  };

  return (
    <Box
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, var(--mantine-color-roblox-blue-6) 0%, var(--mantine-color-roblox-purple-6) 100%)',
        padding: 'var(--mantine-spacing-md)',
      }}
    >
      <Container size={420} my={rem(40)}>
        <Paper
          withBorder
          shadow="xl"
          p="xl"
          radius="lg"
          style={{
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Header with gradient background */}
          <Box
            style={{
              margin: 'calc(var(--mantine-spacing-xl) * -1)',
              marginBottom: 'var(--mantine-spacing-xl)',
              padding: 'var(--mantine-spacing-xl)',
              background: 'linear-gradient(135deg, var(--mantine-color-roblox-blue-6) 0%, var(--mantine-color-roblox-purple-6) 100%)',
              color: 'white',
              textAlign: 'center',
              borderRadius: 'var(--mantine-radius-lg) var(--mantine-radius-lg) 0 0',
            }}
          >
            <Title order={2} fw={700} mb="xs">
              Welcome Back
            </Title>
            <Text size="sm" style={{ opacity: 0.9 }}>
              Sign in to ToolBoxAI Educational Platform
            </Text>
          </Box>

          <form onSubmit={handleSubmit}>
            <Stack gap="lg">
              {error && (
                <Alert
                  variant="light"
                  color="red"
                  icon={<IconAlertCircle size={rem(16)} />}
                  radius="md"
                  data-testid="login-error-alert"
                >
                  {error}
                </Alert>
              )}

              <TextInput
                label="Username or Email"
                placeholder="e.g. john_teacher or john@teacher.com"
                value={formData.email}
                onChange={(event) => handleChange('email')(event.currentTarget.value)}
                required
                disabled={loading}
                leftSection={<IconMail size={rem(16)} />}
                data-testid="email-input"
                description="Enter your username or email address"
              />

              <PasswordInput
                label="Password"
                value={formData.password}
                onChange={(event) => handleChange('password')(event.currentTarget.value)}
                required
                disabled={loading}
                leftSection={<IconLock size={rem(16)} />}
                data-testid="password-input"
              />

              <AtomicButton
                type="submit"
                fullWidth
                size="md"
                loading={loading}
                loadingText="Signing In..."
                data-testid="login-submit"
                variant="primary"
                robloxTheme={true}
              >
                Sign In
              </AtomicButton>

              <Group justify="center">
                <Anchor
                  component={Link}
                  to="/password-reset"
                  size="sm"
                  c="roblox-blue.6"
                >
                  Forgot your password?
                </Anchor>
              </Group>

              <Divider label="Demo Credentials" labelPosition="center" />

              <Stack gap="xs">
                {demoCredentials.map((cred) => (
                  <Group
                    key={cred.role}
                    justify="space-between"
                    p="xs"
                    style={{
                      border: '1px solid var(--mantine-color-gray-3)',
                      borderRadius: 'var(--mantine-radius-sm)',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s',
                    }}
                    onClick={() => fillDemoCredentials(cred.email, cred.password)}
                  >
                    <Box>
                      <Text size="sm" fw={600}>
                        {cred.role}
                      </Text>
                      <Text size="xs" c="dimmed">
                        {cred.email}
                      </Text>
                    </Box>
                    <AtomicButton
                      size="xs"
                      variant="secondary"
                      robloxTheme={true}
                      onClick={(e) => {
                        e.stopPropagation();
                        fillDemoCredentials(cred.email, cred.password);
                      }}
                    >
                      Use
                    </AtomicButton>
                  </Group>
                ))}
              </Stack>

              <Group justify="center" mt="md">
                <Text size="sm" c="dimmed">
                  Don't have an account?{' '}
                  <Anchor
                    component={Link}
                    to="/register"
                    fw={600}
                    c="roblox-blue.6"
                  >
                    Sign up here
                  </Anchor>
                </Text>
              </Group>
            </Stack>
          </form>
        </Paper>
      </Container>
    </Box>
  );
}