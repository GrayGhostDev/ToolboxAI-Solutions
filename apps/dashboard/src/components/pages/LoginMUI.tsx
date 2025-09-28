import * as React from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Visibility, VisibilityOff, Email, Lock } from "@mui/icons-material";
import { login } from "../../services/api";
import { useAppDispatch } from "../../store";
import { signInSuccess } from "../../store/slices/userSlice";
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "../../config";
import { pusherService } from "../../services/pusher";
import { logger } from "../../utils/logger";

export default function LoginMUI() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);
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
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        p: 2,
      }}
    >
      <Paper
        elevation={24}
        sx={{
          width: "100%",
          maxWidth: 400,
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            p: 3,
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
            textAlign: "center",
          }}
        >
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Welcome Back
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            Sign in to ToolBoxAI Educational Platform
          </Typography>
        </Box>

        <CardContent sx={{ p: 3 }}>
          <Box component="form" onSubmit={handleSubmit}>
            <Stack spacing={3}>
              {error && (
                <Alert severity="error" sx={{ borderRadius: 2 }}>
                  {error}
                </Alert>
              )}

              <TextField
                fullWidth
                id="email-field"
                name="email"
                label="Username or Email"
                type="email"
                placeholder="e.g. john_teacher or john@teacher.com"
                value={formData.email}
                onChange={handleChange}
                required
                disabled={loading}
                helperText="Enter your username or email address"
                inputProps={{
                  "data-testid": "email-input",
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Email color="action" />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2,
                  },
                }}
              />

              <TextField
                fullWidth
                id="password-field"
                name="password"
                label="Password"
                type={showPassword ? "text" : "password"}
                value={formData.password}
                onChange={handleChange}
                required
                disabled={loading}
                inputProps={{
                  "data-testid": "password-input",
                }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        disabled={loading}
                        aria-label="toggle password visibility"
                        data-testid="password-visibility-toggle"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2,
                  },
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                data-testid="login-submit"
                sx={{
                  borderRadius: 2,
                  py: 1.5,
                  textTransform: "none",
                  fontSize: "1rem",
                  fontWeight: 600,
                }}
              >
                {loading ? "Signing In..." : "Sign In"}
              </Button>

              <Box sx={{ textAlign: "center" }}>
                <Link
                  to="/password-reset"
                  style={{
                    color: "#667eea",
                    textDecoration: "none",
                    fontSize: "0.875rem",
                  }}
                >
                  Forgot your password?
                </Link>
              </Box>

              <Divider sx={{ my: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Demo Credentials
                </Typography>
              </Divider>

              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  <strong>Admin:</strong> admin@toolboxai.com / Admin123!
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>Teacher:</strong> jane.smith@school.edu / Teacher123!
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  <strong>Student:</strong> alex.johnson@student.edu / Student123!
                </Typography>
              </Stack>

              <Box sx={{ textAlign: "center", mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Don't have an account?{" "}
                  <Link
                    to="/register"
                    style={{
                      color: "inherit",
                      textDecoration: "none",
                      fontWeight: 600,
                    }}
                  >
                    Sign up here
                  </Link>
                </Typography>
              </Box>
            </Stack>
          </Box>
        </CardContent>
      </Paper>
    </Box>
  );
}