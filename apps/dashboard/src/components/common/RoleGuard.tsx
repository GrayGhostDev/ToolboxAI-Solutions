import * as React from "react";
import { useAppSelector } from "../../store";
import { UserRole } from "../../types";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";

interface Props {
  allow: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export default function RoleGuard({ allow, children, fallback }: Props) {
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);

  if (!isAuthenticated) {
    return (
      <Box sx={{ p: 4, textAlign: "center" }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          You must be logged in to access this page.
        </Alert>
        <Button variant="contained" onClick={(e: React.MouseEvent) => () => navigate("/login")}>
          Sign In
        </Button>
      </Box>
    );
  }

  if (!allow.includes(role)) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Box sx={{ p: 4, textAlign: "center" }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Access Denied
          </Typography>
          <Typography variant="body2">
            You don't have permission to access this section. This page is only available for:{" "}
            {allow.join(", ")}.
          </Typography>
        </Alert>
        <Button variant="contained" onClick={(e: React.MouseEvent) => () => navigate("/")}>
          Go to Dashboard
        </Button>
      </Box>
    );
  }

  return <>{children}</>;
}