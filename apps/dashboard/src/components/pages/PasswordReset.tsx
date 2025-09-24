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
import Paper from '@mui/material/Paper';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';

import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Email, Lock, CheckCircle } from "@mui/icons-material";
import { useAppDispatch } from "../../store";
import { addNotification } from "../../store/slices/uiSlice";
import { apiClient } from "../../services/api";

export default function PasswordReset() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  
  const [activeStep, setActiveStep] = useState(token ? 1 : 0);
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const steps = ["Request Reset", "Set New Password", "Complete"];

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError("Please enter your email address");
      return;
    }
    
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await apiClient['request']({
        method: "POST",
        url: "/auth/password-reset",
        data: { email },
      });
      
      dispatch(addNotification({
        type: "success",
        message: "Password reset email sent! Please check your inbox.",
        autoHide: false,
      }));
      
      setSuccess(true);
      setActiveStep(2);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to send reset email. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newPassword || !confirmPassword) {
      setError("Please fill in all fields");
      return;
    }
    
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await apiClient['request']({
        method: "POST",
        url: "/auth/password-reset-confirm",
        data: { 
          token,
          new_password: newPassword,
        },
      });
      
      dispatch(addNotification({
        type: "success",
        message: "Password reset successful! You can now log in with your new password.",
        autoHide: false,
      }));
      
      setActiveStep(2);
      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to reset password. The link may have expired.");
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
          maxWidth: 450,
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
            Password Reset
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            {token ? "Set your new password" : "Reset your ToolBoxAI password"}
          </Typography>
        </Box>

        <CardContent sx={{ p: 3 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
              {error}
            </Alert>
          )}

          {/* Step 1: Request Reset */}
          {activeStep === 0 && !token && (
            <Box component="form" onSubmit={handleRequestReset}>
              <Stack spacing={3}>
                <Typography variant="body2" color="text.secondary">
                  Enter your email address and we'll send you a link to reset your password.
                </Typography>
                
                <TextField
                  fullWidth
                  label="Email Address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
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

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    textTransform: "none",
                    fontSize: "1rem",
                    fontWeight: 600,
                  }}
                >
                  {loading ? "Sending..." : "Send Reset Email"}
                </Button>

                <Box sx={{ textAlign: "center" }}>
                  <Typography variant="body2" color="text.secondary">
                    Remember your password?{" "}
                    <Link
                      to="/login"
                      style={{
                        color: "inherit",
                        textDecoration: "none",
                        fontWeight: 600,
                      }}
                    >
                      Back to login
                    </Link>
                  </Typography>
                </Box>
              </Stack>
            </Box>
          )}

          {/* Step 2: Set New Password */}
          {activeStep === 1 && token && (
            <Box component="form" onSubmit={handleResetPassword}>
              <Stack spacing={3}>
                <Typography variant="body2" color="text.secondary">
                  Please enter your new password below.
                </Typography>
                
                <TextField
                  fullWidth
                  label="New Password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Lock color="action" />
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
                  label="Confirm New Password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Lock color="action" />
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
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    textTransform: "none",
                    fontSize: "1rem",
                    fontWeight: 600,
                  }}
                >
                  {loading ? "Resetting..." : "Reset Password"}
                </Button>
              </Stack>
            </Box>
          )}

          {/* Step 3: Success */}
          {activeStep === 2 && success && (
            <Stack spacing={3} alignItems="center">
              <CheckCircle sx={{ fontSize: 64, color: "success.main" }} />
              
              <Typography variant="h6" textAlign="center">
                {token ? "Password Reset Successful!" : "Reset Email Sent!"}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" textAlign="center">
                {token 
                  ? "Your password has been successfully reset. Redirecting to login..."
                  : "Please check your email for the password reset link. The link will expire in 1 hour."
                }
              </Typography>

              {!token && (
                <Button
                  fullWidth
                  variant="contained"
                  onClick={(e: React.MouseEvent) => () => navigate("/login")}
                  sx={{
                    borderRadius: 2,
                    py: 1.5,
                    textTransform: "none",
                    fontSize: "1rem",
                    fontWeight: 600,
                  }}
                >
                  Back to Login
                </Button>
              )}
            </Stack>
          )}
        </CardContent>
      </Paper>
    </Box>
  );
}