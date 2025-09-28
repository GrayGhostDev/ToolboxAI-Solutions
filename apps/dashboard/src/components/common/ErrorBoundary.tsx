import * as React from "react";
import { Alert, Box, Button, Text } from "@mantine/core";
import { IconAlertCircle, IconRefresh } from "@tabler/icons-react";

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      return (
        <Box
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "400px",
            padding: "var(--mantine-spacing-lg)",
          }}
        >
          <Alert
            icon={<IconAlertCircle size={20} />}
            title="Something went wrong"
            color="red"
            variant="filled"
            styles={{
              root: {
                maxWidth: 600,
                width: "100%",
              },
            }}
          >
            <Text size="sm" mb="md">
              {this.state.error?.message || "An unexpected error occurred"}
            </Text>
            <Button
              variant="outline"
              color="red"
              leftIcon={<IconRefresh size={16} />}
              onClick={this.resetError}
              size="sm"
            >
              Try Again
            </Button>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;