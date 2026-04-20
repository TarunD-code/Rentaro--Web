import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Paper, alpha } from '@mui/material';
import { Refresh, Warning } from '@mui/icons-material';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error);
    console.error('Component stack:', errorInfo.componentStack);
    // You could send this to an error reporting service here (e.g. Sentry)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Box 
          sx={{ 
            height: '80vh', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            p: 3
          }}
        >
          <Paper 
            elevation={0} 
            sx={{ 
              p: 6, 
              borderRadius: 8, 
              textAlign: 'center',
              border: '1px solid',
              borderColor: 'divider',
              maxWidth: 500,
              bgcolor: 'background.paper'
            }}
          >
            <Box 
              sx={{ 
                width: 64, 
                height: 64, 
                borderRadius: '50%', 
                bgcolor: (theme) => alpha(theme.palette.error.main, 0.1),
                color: 'error.main',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 24px'
              }}
            >
              <Warning fontSize="large" />
            </Box>
            <Typography variant="h5" fontWeight={800} gutterBottom>
              Oops! Something went wrong
            </Typography>
            <Typography variant="body1" color="text.secondary" mb={4}>
              An unexpected error occurred in the application. We've been notified and are working on it.
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<Refresh />}
              onClick={() => window.location.reload()}
              sx={{ borderRadius: 3, px: 4, py: 1.5 }}
            >
              Reload Page
            </Button>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
