import * as React from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Box,
  Paper,
  Stack,
  Button,
  TextInput,
  PasswordInput,
  Text,
  Alert,
  Loader,
  Divider,
  Anchor,
} from '@mantine/core';
import {
  IconEye,
  IconEyeOff,
  IconMail,
  IconLock
} from '@tabler/icons-react';
import { login } from "../../services/api";
import { useAppDispatch } from "../../store";
import { signInSuccess } from "../../store/slices/userSlice";
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "../../config";
import { pusherService } from "../../services/pusher";
import { logger } from "../../utils/logger";

export default function LoginMantine() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (error) setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Set error immediately before any async operations for test visibility
    setError("");

    // Basic client-side validation
    if (!formData.email || !formData.password) {
      setError("Email and password are required");
      setLoading(false);
      return;
    }

    // Basic email format validation - check if it's not a username (contains _)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isUsername = formData.email.includes("_") || !formData.email.includes("@");
    if (!isUsername && !emailRegex.test(formData.email)) {
      setError("Please enter a valid email address or username");
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

      // Navigate to dashboard
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: "16px",
      }}
    >
      <Paper
        shadow="xl"
        style={{
          width: "100%",
          maxWidth: 400,
          borderRadius: "12px",
          overflow: "hidden",
        }}
      >
        <Box
          style={{
            padding: "24px",
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
            textAlign: "center",
          }}
        >
          <Text size="xl" fw={700} mb="xs">
            Welcome Back
          </Text>
          <Text size="sm" style={{ opacity: 0.9 }}>
            Sign in to ToolBoxAI Educational Platform
          </Text>
        </Box>

        <Box p="xl">
          <Box component="form" onSubmit={handleSubmit}>
            <Stack gap="lg">
              {error && (
                <Alert color="red" radius="sm">
                  {error}
                </Alert>
              )}

              <TextInput
                id="email-field"
                name="email"
                label="Username or Email"
                placeholder="e.g. john_teacher or john@teacher.com"
                value={formData.email}
                onChange={handleChange}
                required
                disabled={loading}
                description="Enter your username or email address"
                data-testid="email-input"
                leftSection={<IconMail size={16} />}
                radius="md"
              />

              <PasswordInput
                id="password-field"
                name="password"
                label="Password"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={loading}
                data-testid="password-input"
                leftSection={<IconLock size={16} />}
                visibilityToggleIcon={({ reveal, size }) =>
                  reveal ? <IconEyeOff size={size} /> : <IconEye size={size} />
                }
                visibilityToggleButtonProps={{
                  "data-testid": "password-visibility-toggle",
                }}
                radius="md"
              />

              <Button
                type="submit"
                fullWidth
                variant="filled"
                size="lg"
                disabled={loading}
                data-testid="login-submit"
                radius="md"
                style={{
                  fontSize: "1rem",
                  fontWeight: 600,
                }}
                leftSection={loading ? <Loader size="sm" /> : undefined}
              >
                {loading ? "Signing In..." : "Sign In"}
              </Button>

              <Box style={{ textAlign: "center" }}>
                <Anchor
                  component={Link}
                  to="/password-reset"
                  size="sm"
                  style={{ color: "#667eea" }}
                >
                  Forgot your password?
                </Anchor>
              </Box>

              <Divider label="Demo Credentials" labelPosition="center" />

              <Stack gap="xs">
                <Text size="xs" c="dimmed">
                  <strong>Admin:</strong> admin@toolboxai.com / Admin123!
                </Text>
                <Text size="xs" c="dimmed">
                  <strong>Teacher:</strong> jane.smith@school.edu / Teacher123!
                </Text>
                <Text size="xs" c="dimmed">
                  <strong>Student:</strong> alex.johnson@student.edu / Student123!
                </Text>
              </Stack>

              <Box style={{ textAlign: "center" }}>
                <Text size="sm" c="dimmed">
                  Don't have an account?{" "}
                  <Anchor
                    component={Link}
                    to="/register"
                    fw={600}
                  >
                    Sign up here
                  </Anchor>
                </Text>
              </Box>
            </Stack>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}