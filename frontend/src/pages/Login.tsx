import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Container,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Paper,
  Stack,
  Divider,
  useTheme,
  alpha,
  Fade,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  VideoLibrary,
  Person,
  LockOpen,
  ArrowForward,
} from '@mui/icons-material';

interface Particle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
}

const AnimatedBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const particlesRef = useRef<Particle[]>([]);
  const theme = useTheme();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Create particles
    const colors = [theme.palette.primary.main, '#6366F1', theme.palette.secondary.main];
    particlesRef.current = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 2 + 1,
      opacity: Math.random() * 0.3 + 0.1,
    }));

    const animate = () => {
      ctx.fillStyle = alpha(theme.palette.background.paper, 0.8);
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;

        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;

        ctx.fillStyle = colors[particle.id % colors.length];
        ctx.globalAlpha = particle.opacity;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.globalAlpha = 1;
      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationRef.current);
    };
  }, [theme]);

  return (
    <Box
      component="canvas"
      ref={canvasRef}
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
      }}
    />
  );
};

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const theme = useTheme();
  const location = useLocation();

  // Username/Password state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [emailVerificationError, setEmailVerificationError] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [justRegistered, setJustRegistered] = useState(false);

  useEffect(() => {
    // Check if user just registered
    const state = location.state as { justRegistered?: boolean; email?: string };
    if (state?.justRegistered) {
      setJustRegistered(true);
      if (state.email) {
        setUserEmail(state.email);
      }
    }
  }, [location.state]);

  const handleUsernameLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await login(username, password);
      setSuccess('Login successful! Redirecting...');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err) {
      const error = err as Error;
      console.error('Login error:', error);

      // Check if this is an email verification error
      if (error.message && error.message.includes('verify your email')) {
        setEmailVerificationError(true);
        setUserEmail(username); // Store the username/email for potential resend
        setError('Your email address has not been verified. Please check your inbox for the verification link.');
      } else {
        setError(error.message || 'Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
      <AnimatedBackground />

      <Container component="main" maxWidth="sm" sx={{ position: 'relative', zIndex: 1 }}>
        <Box
          sx={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            py: 4,
          }}
        >
          <Fade in timeout={800}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 3, sm: 4 },
                width: '100%',
                backdropFilter: 'blur(10px)',
                backgroundColor: alpha(theme.palette.background.paper, 0.9),
                border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
                borderRadius: 3,
              }}
            >
              {/* Header */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mb: 4,
                  textAlign: 'center',
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 60,
                    height: 60,
                    borderRadius: 2,
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    mb: 2,
                  }}
                >
                  <VideoLibrary sx={{ fontSize: 32, color: 'white' }} />
                </Box>

                <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 0.5 }}>
                  Griot
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  AI-Powered Video Creation Platform
                </Typography>
              </Box>

              {justRegistered && (
                <Alert
                  severity="info"
                  sx={{ mb: 3 }}
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => setJustRegistered(false)}
                    >
                      Dismiss
                    </Button>
                  }
                >
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Check Your Email</strong>
                  </Typography>
                  <Typography variant="body2">
                    We've sent a verification link to {userEmail || 'your email'}. Please verify your email before logging in.
                  </Typography>
                </Alert>
              )}

              {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                  {error}
                </Alert>
              )}

              {emailVerificationError && (
                <Alert
                  severity="warning"
                  sx={{ mb: 3 }}
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => {
                        setEmailVerificationError(false);
                        setError(null);
                      }}
                    >
                      Dismiss
                    </Button>
                  }
                >
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Email Verification Required</strong>
                  </Typography>
                  <Typography variant="body2">
                    Please check your email for the verification link. If you didn't receive it, you can try registering again or contact support.
                  </Typography>
                </Alert>
              )}

              {success && (
                <Alert severity="success" sx={{ mb: 3 }}>
                  {success}
                </Alert>
              )}

              {/* Login Form */}
              <Box component="form" onSubmit={handleUsernameLogin}>
                <TextField
                  fullWidth
                  label="Username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  margin="normal"
                  disabled={loading}
                  placeholder="Enter your username"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Person sx={{ color: 'action.active' }} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 1.5,
                    },
                  }}
                />

                <TextField
                  fullWidth
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  margin="normal"
                  disabled={loading}
                  placeholder="Enter your password"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockOpen sx={{ color: 'action.active' }} />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                          disabled={loading}
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 1.5,
                    },
                  }}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  endIcon={loading ? undefined : <ArrowForward />}
                  sx={{
                    mt: 3,
                    mb: 2,
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600,
                    borderRadius: 1.5,
                  }}
                >
                  {loading ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    'Sign In'
                  )}
                </Button>
              </Box>

              <Divider sx={{ my: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  OR
                </Typography>
              </Divider>

              {/* OAuth Buttons */}
              <Stack spacing={1.5} sx={{ mb: 2 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  onClick={() => {
                    window.location.href = '/api/v1/auth/oauth/google/login';
                  }}
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    borderRadius: 1.5,
                    borderColor: alpha(theme.palette.divider, 0.3),
                    color: 'text.primary',
                    fontWeight: 600,
                    textTransform: 'none',
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      backgroundColor: alpha(theme.palette.primary.main, 0.05),
                    },
                  }}
                  startIcon={
                    <Box
                      component="img"
                      src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJNMTcuNiA5LjJsLS4xLTEuOEg5djMuNGg0LjhDMTMuNiAxMiAxMyAxMyAxMiAxMy42djIuMmgzYTguOCA4LjggMCAwIDAgMi42LTYuNnoiIGZpbGw9IiM0Mjg1RjQiIGZpbGwtcnVsZT0ibm9uemVybyIvPjxwYXRoIGQ9Ik05IDE4YzIuNCAwIDQuNS0uOCA2LTIuMmwtMy0yLjJhNS40IDUuNCAwIDAgMS04LTIuOUgxVjEzYTkgOSAwIDAgMCA4IDV6IiBmaWxsPSIjMzRBODUzIiBmaWxsLXJ1bGU9Im5vbnplcm8iLz48cGF0aCBkPSJNNCAxMC43YTUuNCA1LjQgMCAwIDEgMC0zLjRWNUgxYTkgOSAwIDAgMCAwIDhsMy0yLjN6IiBmaWxsPSIjRkJCQzA1IiBmaWxsLXJ1bGU9Im5vbnplcm8iLz48cGF0aCBkPSJNOSAzLjZjMS4zIDAgMi41LjQgMy40IDEuM0wxNSAyLjNBOSA5IDAgMCAwIDEgNWwzIDIuNGE1LjQgNS40IDAgMCAxIDUtMy43eiIgZmlsbD0iI0VBNDMzNSIgZmlsbC1ydWxlPSJub256ZXJvIi8+PHBhdGggZD0iTTAgMGgxOHYxOEgweiIvPjwvZz48L3N2Zz4="
                      alt="Google"
                      sx={{ width: 20, height: 20 }}
                    />
                  }
                >
                  Continue with Google
                </Button>

                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  onClick={() => {
                    window.location.href = '/api/v1/auth/oauth/github/login';
                  }}
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    borderRadius: 1.5,
                    borderColor: alpha(theme.palette.divider, 0.3),
                    color: 'text.primary',
                    fontWeight: 600,
                    textTransform: 'none',
                    '&:hover': {
                      borderColor: '#333',
                      backgroundColor: alpha('#333', 0.05),
                    },
                  }}
                  startIcon={
                    <Box
                      component="img"
                      src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGNsaXAtcnVsZT0iZXZlbm9kZCIgZD0iTTEwIDBDNC40NzcgMCAwIDQuNDc3IDAgMTBjMCA0LjQyIDIuODY1IDguMTY2IDYuODM5IDkuNDg5LjUuMDkyLjY4Mi0uMjE3LjY4Mi0uNDgyIDAtLjIzNy0uMDA4LS44NjYtLjAxMy0xLjcwMi0yLjc4Mi42MDUtMy4zNjktMS4zNC0zLjM2OS0xLjM0LS40NTUtMS4xNTgtMS4xMS0xLjQ2Ni0xLjExLTEuNDY2LS45MDgtLjYyLjA2OS0uNjA4LjA2OS0uNjA4IDEuMDAzLjA3IDEuNTMxIDEuMDMgMS41MzEgMS4wMy44OTIgMS41MjkgMi4zNDEgMS4wODcgMi45MS44MzEuMDkxLS42NDYuMzUtMS4wODYuNjM2LTEuMzM2LTIuMjItLjI1My00LjU1NS0xLjExLTQuNTU1LTQuOTQzIDAtMS4wOTEuMzktMi4wMDIgMS4wMjktMi43MDctLjEwMy0uMjUzLS40NDYtMS4yNy4wOTgtMi42NDcgMCAwIC44NC0uMjY5IDIuNzUgMS4wMzVBOS41NzggOS41NzggMCAwIDEgMTAgNC44MzZhOS41NzcgOS41NzcgMCAwIDEgMi41MDQuMzM3YzEuOTA5LTEuMzA0IDIuNzQ3LTEuMDM1IDIuNzQ3LTEuMDM1LjU0NiAxLjM3Ny4yMDMgMi4zOTQuMSAyLjY0Ny42NCouNzA1IDEuMDI3IDEuNjE2IDEuMDI3IDIuNzA3IDAgMy44NC0yLjMzOCA0LjY4Ny00LjU2NiA0LjkzNS4zNTkuMzA5LjY3OC45MTguNjc4IDEuODUyIDAgMS4zMzYtLjAxMiAyLjQxNS0uMDEyIDIuNzQzIDAgLjI2Ny4xOC41NzguNjg4LjQ4QzE3LjEzNyAxOC4xNjMgMjAgMTQuNDIgMjAgMTBjMC01LjUyMy00LjQ3Ny0xMC0xMC0xMHoiIGZpbGw9IiMxODE3MTciLz48L3N2Zz4="
                      alt="GitHub"
                      sx={{ width: 20, height: 20 }}
                    />
                  }
                >
                  Continue with GitHub
                </Button>

                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  onClick={() => {
                    window.location.href = '/api/v1/auth/oauth/discord/login';
                  }}
                  disabled={loading}
                  sx={{
                    py: 1.5,
                    borderRadius: 1.5,
                    borderColor: alpha(theme.palette.divider, 0.3),
                    color: 'text.primary',
                    fontWeight: 600,
                    textTransform: 'none',
                    '&:hover': {
                      borderColor: '#5865F2',
                      backgroundColor: alpha('#5865F2', 0.05),
                    },
                  }}
                  startIcon={
                    <Box
                      component="img"
                      src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMjAuMzE3IDQuMzY5NWE0Ljk1IDQuOTUgMCAwIDAtLjEzNzMtLjA0MTRjLTEuNzgzLS41MTk4LTMuNzY1LS44NjM3LTUuODgyNS0uOTYwOGExNC43NiAxNC43NiAwIDAgMC0uNTA1NS4wMDRjLTEuODI1NS4xMzE3LTMuNTM1LjQ3NjUtNS4wNDU1Ljk2MDhhNS4yNSA1LjI1IDAgMCAwLS4xMzQuMDQxNGMtMS4wODM1IDEuODc5NS0xLjkzMiA0LjEwMDUtMi40MjQ1IDYuNjE4YTcuNDcgNy40NyAwIDAgMC0uMDM1NS41MzdjLjAwMTUuODI3LjA1NDUgMS42NDEuMTU2IDIuNDI1NS4wMDE1LjAxNjUuMDA0LjAzMy4wMDY1LjA0OTUuMDA4LjA3NjUuMDE5NS4xNTIuMDMyNS4yMjcuMDU3NS40MjYuMTM1Ljg0MS4yMzMgMS4yNDA1LjAzNi4xNDc1LjA3NC4yOTMuMTE0LjQzODUuMjQxNS44NzQ1LjU0NSAxLjY5NS45MTMgMi40NDg1YTE0LjQ1NSAxNC40NTUgMCAwIDAgLjg3MiAxLjY4Yy4wMTIuMDIuMDI0LjA0LjAzNjUuMDU5NS4xNzM1LjI2MjUuMzYuNTEyNS41NTk1Ljc0Ny4wMzguMDQ1LjA3Ni4wODk1LjExNDUuMTM0YTEzLjcgMTMuNyAwIDAgMCAxLjUyMDUgMS41MzJjLjA0NjUuMDM4NS4wOTMuMDc3LjE0LjExNDVhMTMuODMgMTMuODMgMCAwIDAgMi43MzQgMS42NjY1Yy4wNDguMDIxNS4wOTYuMDQzNS4xNDQuMDY1YTE0LjQgMTQuNCAwIDAgMCAzLjE1MjUuOTg5Yy4wNDkuMDA4LjA5NzkuMDE0NS4xNDcuMDIwNWExNC42IDE0LjYgMCAwIDAgMy4wODUuMDA3Yy4wNDktLjAwNy4wOTgtLjAxMzUuMTQ3LS4wMjA1YTE0LjQgMTQuNCAwIDAgMCAzLjE1MjUtLjk4OWMuMDQ4LS4wMjE1LjA5Ni0uMDQzNS4xNDQtLjA2NWExMy44MyAxMy44MyAwIDAgMCAyLjczNC0xLjY2NjVjLjA0Ny0uMDM3NS4wOTM1LS4wNzYuMTQtLjExNDVhMTMuNyAxMy43IDAgMCAwIDEuNTIwNS0xLjUzMmMuMDM4NS0uMDQ0NS4wNzY1LS4wODkuMTE0NS0uMTM0LjE5OTUtLjIzNDUuMzg2LS40ODQ1LjU1OTUtLjc0Ny4wMTI1LS4wMTk1LjAyNDUtLjAzOTUuMDM2NS0uMDU5NWE0LjQ4OCA0LjQ4OCAwIDAgMCAuMTQyLS4yNjE1IDguMjUgOC4yNSAwIDAgMCAuNzMtMS40MTg1Yy4zNjgtLjc1MzUuNjcxNS0xLjU3NC45MTMtMi40NDg1LjA0LS4xNDU1LjA3OC0uMjkxLjExNC0uNDM4NS4wOTgtLjM5OTUuMTc1NS0uODE0NS4yMzMtMS4yNDA1LjAxMy0uMDc1LjAyNDUtLjE1MDUuMDMyNS0uMjI3LjAwMjUtLjAxNjUuMDA1LS4wMzMuMDA2NS0uMDQ5NS4xMDE1LS43ODQ1LjE1NDUtMS41OTg1LjE1Ni0yLjQyNTVhNy40NyA3LjQ3IDAgMCAwLS4wMzU1LS41MzdjLS40OTI1LTIuNTE3NS0xLjM0MS00LjczODUtMi40MjQ1LTYuNjE4ek05LjQwNyAxNS4xOTE1Yy0xLjIwNDUgMC0yLjE3ODUtMS4yMDQ1LTIuMTc4NS0yLjY4MyAwLTEuNDc4NS45NzQtMi42ODMgMi4xNzg1LTIuNjgzIDEuMjA0NSAwIDIuMTc4NSAxLjIwNDUgMi4xNzg1IDIuNjgzIDAgMS40Nzg1LS45NzQgMi42ODMtMi4xNzg1IDIuNjgzem01LjE4NiAwYy0xLjIwNDUgMC0yLjE3ODUtMS4yMDQ1LTIuMTc4NS0yLjY4MyAwLTEuNDc4NS45NzQtMi42ODMgMi4xNzg1LTIuNjgzIDEuMjA0NSAwIDIuMTc4NSAxLjIwNDUgMi4xNzg1IDIuNjgzIDAgMS40Nzg1LS45NzQgMi42ODMtMi4xNzg1IDIuNjgzeiIgZmlsbD0iIzU4NjVGMiIvPjwvc3ZnPg=="
                      alt="Discord"
                      sx={{ width: 20, height: 20 }}
                    />
                  }
                >
                  Continue with Discord
                </Button>
              </Stack>

              <Divider sx={{ my: 2 }} />

              {/* Footer */}
              <Stack spacing={2} sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.secondary" align="center">
                  Don't have an account?{' '}
                  <Typography
                    component="span"
                    variant="body2"
                    sx={{
                      color: 'primary.main',
                      cursor: 'pointer',
                      fontWeight: 600,
                      '&:hover': { textDecoration: 'underline' },
                    }}
                    onClick={() => navigate('/register')}
                  >
                    Sign up here
                  </Typography>
                </Typography>
              </Stack>
            </Paper>
          </Fade>
        </Box>
      </Container>
    </Box>
  );
};

export default Login;