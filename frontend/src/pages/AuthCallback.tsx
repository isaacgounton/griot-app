import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Container,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  useTheme,
  alpha,
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';

const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setApiKey } = useAuth();
  const theme = useTheme();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Completing authentication...');

  useEffect(() => {
    const handleOAuthCallback = async () => {
      // Get parameters from URL
      const token = searchParams.get('token');
      const success = searchParams.get('success');
      const error = searchParams.get('error');
      const errorMessage = searchParams.get('message');

      // Handle success
      if (success === 'true' && token) {
        try {
          // Store the JWT token
          localStorage.setItem('api_key', token);

          // Update auth context
          if (setApiKey) {
            setApiKey(token);
          }

          setStatus('success');
          setMessage('Authentication successful! Redirecting to dashboard...');

          // Redirect to dashboard after a short delay
          setTimeout(() => {
            navigate('/dashboard', { replace: true });
          }, 1500);
        } catch (err) {
          console.error('Error storing token:', err);
          setStatus('error');
          setMessage('Failed to complete authentication. Please try again.');
        }
      }
      // Handle error
      else if (error) {
        setStatus('error');
        setMessage(errorMessage || 'OAuth authentication failed. Please try again.');

        // Redirect to login after delay
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      }
      // Handle missing parameters
      else {
        setStatus('error');
        setMessage('Invalid authentication response. Redirecting to login...');

        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 2000);
      }
    };

    handleOAuthCallback();
  }, [searchParams, navigate, setApiKey]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            backgroundColor: alpha(theme.palette.background.paper, 0.9),
          }}
        >
          {/* Loading State */}
          {status === 'loading' && (
            <Box>
              <CircularProgress size={60} sx={{ mb: 3 }} />
              <Typography variant="h6" gutterBottom>
                {message}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Please wait while we complete your authentication...
              </Typography>
            </Box>
          )}

          {/* Success State */}
          {status === 'success' && (
            <Box>
              <CheckCircle
                sx={{
                  fontSize: 60,
                  color: 'success.main',
                  mb: 2,
                }}
              />
              <Typography variant="h6" gutterBottom color="success.main">
                {message}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                You will be redirected shortly...
              </Typography>
            </Box>
          )}

          {/* Error State */}
          {status === 'error' && (
            <Box>
              <ErrorIcon
                sx={{
                  fontSize: 60,
                  color: 'error.main',
                  mb: 2,
                }}
              />
              <Typography variant="h6" gutterBottom color="error.main">
                Authentication Failed
              </Typography>
              <Alert severity="error" sx={{ mt: 2 }}>
                {message}
              </Alert>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                You will be redirected to login shortly...
              </Typography>
            </Box>
          )}
        </Paper>
      </Container>
    </Box>
  );
};

export default AuthCallback;
