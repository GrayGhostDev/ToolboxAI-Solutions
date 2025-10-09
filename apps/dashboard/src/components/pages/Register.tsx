import * as React from 'react';
import {
  Box,
  Card,
  TextInput,
  Button,
  Text,
  Alert,
  Stack,
  ActionIcon,
  Divider,
  Paper,
  Select,
  PasswordInput,
  Group
} from '@mantine/core';

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { IconEye, IconEyeOff, IconMail, IconLock, IconUser, IconSchool } from '@tabler/icons-react';
import { register } from '../../services/api';
import { useAppDispatch } from '../../store';
import { signInSuccess } from '../../store/slices/userSlice';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from '../../config';

export default function Register() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    displayName: '',
    role: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const handleRoleChange = (e: any) => {
    setFormData(prev => ({ ...prev, role: e.target.value }));
    if (error) setError('');
  };

  const validateForm = () => {
    if (!formData.email || !formData.password || !formData.displayName || !formData.role) {
      return 'All fields are required';
    }
    if (formData.password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (formData.password !== formData.confirmPassword) {
      return 'Passwords do not match';
    }
    if (!/\S+@\S+\.\S+/.test(formData.email)) {
      return 'Please enter a valid email address';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await register({
        email: formData.email,
        password: formData.password,
        displayName: formData.displayName,
        role: formData.role,
      });
      
      // Store tokens
      localStorage.setItem(AUTH_TOKEN_KEY, response.accessToken);
      localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, response.refreshToken);
      
      // Update Redux state
      dispatch(signInSuccess({
        userId: response.user.id,
        email: response.user.email,
        displayName: response.user.displayName,
        avatarUrl: response.user.avatarUrl,
        role: response.user.role as any,
        token: response.accessToken,
        refreshToken: response.refreshToken,
        schoolId: response.user.schoolId,
        classIds: response.user.classIds,
      }));

      // Navigate to dashboard
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
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
          <Text size="xl" fw={700} mb="xs">
            Join ToolBoxAI
          </Text>
          <Text size="sm" style={{ opacity: 0.9 }}>
            Create your account for the Educational Platform
          </Text>
        </Box>

        <Box p="xl">
          <Box component="form" onSubmit={handleSubmit}>
            <Stack gap="md">
              {error && (
                <Alert color="red">
                  {error}
                </Alert>
              )}

              <TextInput
                name="displayName"
                label="Full Name"
                type="text"
                value={formData.displayName}
                onChange={handleChange}
                required
                disabled={loading}
                leftSection={<IconUser size={16} />}
              />

              <TextInput
                name="email"
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                disabled={loading}
                leftSection={<IconMail size={16} />}
              />

              <Select
                label="Role"
                value={formData.role}
                onChange={(value) => setFormData(prev => ({ ...prev, role: value || '' }))}
                disabled={loading}
                leftSection={<IconSchool size={16} />}
                required
                data={[
                  { value: 'Student', label: 'Student' },
                  { value: 'Teacher', label: 'Teacher' },
                  { value: 'Parent', label: 'Parent' },
                  { value: 'Admin', label: 'Administrator' },
                ]}
              />

              <PasswordInput
                name="password"
                label="Password"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={loading}
                leftSection={<IconLock size={16} />}
              />

              <PasswordInput
                name="confirmPassword"
                label="Confirm Password"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                disabled={loading}
                leftSection={<IconLock size={16} />}
              />

              <Button
                type="submit"
                fullWidth
                size="lg"
                disabled={loading}
                loading={loading}
                style={{
                  textTransform: 'none',
                  fontSize: '1rem',
                  fontWeight: 600,
                }}
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>

              <Box ta="center" mt="md">
                <Text size="sm" c="dimmed">
                  Already have an account?{' '}
                  <Link
                    to="/login"
                    style={{
                      color: 'inherit',
                      textDecoration: 'none',
                      fontWeight: 600,
                    }}
                  >
                    Sign in here
                  </Link>
                </Text>
              </Box>
            </Stack>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}