import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Typography, Button, Paper } from '@mui/material';
import { Refresh } from '@mui/icons-material';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
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
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      
      return (
        <Paper 
          sx={{ 
            p: 4, 
            textAlign: 'center', 
            borderRadius: 4, 
            border: '1px dashed', 
            borderColor: 'divider',
            bgcolor: 'background.default'
          }}
        >
          <Typography variant="h6" fontWeight={700} gutterBottom>
            Something went wrong in this section
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            {this.state.error?.message || 'A runtime error occurred.'}
          </Typography>
          <Button 
            variant="outlined" 
            startIcon={<Refresh />} 
            onClick={() => this.setState({ hasError: false })}
          >
            Try Again
          </Button>
        </Paper>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
