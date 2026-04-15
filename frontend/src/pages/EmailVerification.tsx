import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
    Box,
    Container,
    Typography,
    Alert,
    CircularProgress,
    Button,
    Paper,
    Stack,
    useTheme,
    alpha,
    Fade,
} from '@mui/material';
import {
    CheckCircle,
    Error,
    Email,
    ArrowForward,
} from '@mui/icons-material';

const EmailVerification: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const theme = useTheme();

    const [loading, setLoading] = useState(true);
    const [verified, setVerified] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [resendLoading, setResendLoading] = useState(false);
    const [resendMessage, setResendMessage] = useState<string | null>(null);

    const token = searchParams.get('token');

    useEffect(() => {
        if (token) {
            verifyEmail(token);
        } else {
            setLoading(false);
            setError('No verification token provided');
        }
    }, [token]);

    const verifyEmail = async (verificationToken: string) => {
        try {
            const response = await fetch('/api/v1/auth/verify-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: verificationToken }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setVerified(true);
            } else {
                setError(data.detail || data.message || 'Verification failed');
            }
        } catch (err) {
            console.error('Verification error:', err);
            setError('An error occurred during verification');
        } finally {
            setLoading(false);
        }
    };

    const handleResendVerification = async () => {
        setResendLoading(true);
        setResendMessage(null);

        try {
            // For now, we'll just show a message since we don't have the user's email
            // In a real implementation, you'd need to get the email from somewhere
            setResendMessage('Please check your email for the verification link. If you didn\'t receive it, contact support.');
        } catch (err) {
            console.error('Resend error:', err);
            setResendMessage('Failed to resend verification email');
        } finally {
            setResendLoading(false);
        }
    };

    if (loading) {
        return (
            <Box
                sx={{
                    minHeight: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    bgcolor: 'background.default',
                }}
            >
                <CircularProgress size={60} />
                <Typography variant="h6" sx={{ mt: 2 }}>
                    Verifying your email...
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
            <Container component="main" maxWidth="sm">
                <Box
                    sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minHeight: '80vh',
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
                                textAlign: 'center',
                            }}
                        >
                            {verified ? (
                                <>
                                    <CheckCircle
                                        sx={{
                                            fontSize: 64,
                                            color: 'success.main',
                                            mb: 2,
                                        }}
                                    />
                                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
                                        Email Verified!
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                                        Your email has been successfully verified. You can now log in to your account.
                                    </Typography>
                                    <Button
                                        variant="contained"
                                        size="large"
                                        onClick={() => navigate('/login')}
                                        endIcon={<ArrowForward />}
                                        sx={{
                                            py: 1.5,
                                            px: 4,
                                            fontSize: '1rem',
                                            fontWeight: 600,
                                            borderRadius: 1.5,
                                        }}
                                    >
                                        Go to Login
                                    </Button>
                                </>
                            ) : (
                                <>
                                    <Error
                                        sx={{
                                            fontSize: 64,
                                            color: 'error.main',
                                            mb: 2,
                                        }}
                                    />
                                    <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
                                        Verification Failed
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                                        {error || 'We couldn\'t verify your email. The link may be expired or invalid.'}
                                    </Typography>

                                    {resendMessage && (
                                        <Alert severity="info" sx={{ mb: 3 }}>
                                            {resendMessage}
                                        </Alert>
                                    )}

                                    <Stack spacing={2}>
                                        <Button
                                            variant="outlined"
                                            onClick={handleResendVerification}
                                            disabled={resendLoading}
                                            startIcon={resendLoading ? <CircularProgress size={20} /> : <Email />}
                                            sx={{
                                                py: 1.5,
                                                fontSize: '1rem',
                                                fontWeight: 600,
                                                borderRadius: 1.5,
                                            }}
                                        >
                                            {resendLoading ? 'Sending...' : 'Resend Verification Email'}
                                        </Button>

                                        <Button
                                            variant="text"
                                            onClick={() => navigate('/login')}
                                            sx={{
                                                py: 1,
                                                fontSize: '0.9rem',
                                            }}
                                        >
                                            Back to Login
                                        </Button>
                                    </Stack>
                                </>
                            )}
                        </Paper>
                    </Fade>
                </Box>
            </Container>
        </Box>
    );
};

export default EmailVerification;