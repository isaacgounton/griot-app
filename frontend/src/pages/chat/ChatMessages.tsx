import React from 'react';
import {
    Box,
    Typography,
    Paper,
    IconButton,
    Tooltip,
    alpha,
    useTheme
} from '@mui/material';
import {
    ContentCopy as CopyIcon,
    SmartToy as BotIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Message } from '../../types/anyllm';
import { MessageContentDisplay } from './MediaDisplay';

interface ChatMessagesProps {
    messages: Message[];
    loading: boolean;
    onCopyMessage: (text: string) => void;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, loading, onCopyMessage }) => {
    const theme = useTheme();
    // Track which messages have been rendered before to avoid re-animating
    const renderedCountRef = React.useRef(0);

    if (messages.length === 0) {
        return null; // Let parent handle empty state
    }

    // Only animate messages that are genuinely new (not content updates to existing ones)
    const previousCount = renderedCountRef.current;
    renderedCountRef.current = messages.length;

    return (
        <>
            {messages.map((message, index) => {
                // Skip tool result messages (internal protocol, not user-facing)
                if (message.role === 'tool') return null;

                // Skip assistant messages that are purely tool_calls with no visible text
                if (message.role === 'assistant' && message.tool_calls && message.tool_calls.length > 0) {
                    const hasText = Array.isArray(message.content)
                        ? message.content.some(c => c.type === 'text' && c.text && c.text.trim().length > 0)
                        : typeof message.content === 'string' && message.content.trim().length > 0;
                    if (!hasText) return null;
                }

                const isUser = message.role === 'user';

                // Extract text for markdown rendering
                const textContent = Array.isArray(message.content)
                    ? message.content.filter(c => c.type === 'text').map(c => c.text || '').join('')
                    : typeof message.content === 'string' ? message.content : '';

                return (
                    <Box
                        key={index}
                        sx={{
                            display: 'flex',
                            justifyContent: isUser ? 'flex-end' : 'flex-start',
                            mb: 3,
                            // Only animate genuinely new messages, not streaming content updates
                            ...(index >= previousCount ? { animation: 'fadeInUp 0.3s ease-out' } : {}),
                            gap: 1.5
                        }}
                    >
                        {/* AI Avatar */}
                        {!isUser && (
                            <Box
                                sx={{
                                    width: 40,
                                    height: 40,
                                    borderRadius: '50%',
                                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0,
                                    boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.3)}`,
                                    mt: 0.5
                                }}
                            >
                                <BotIcon sx={{ fontSize: 20, color: 'white' }} />
                            </Box>
                        )}

                        <Box
                            sx={{
                                maxWidth: '75%',
                                display: 'flex',
                                flexDirection: 'column'
                            }}
                        >
                            {/* Message Header */}
                            <Typography
                                variant="caption"
                                sx={{
                                    color: 'text.secondary',
                                    mb: 0.5,
                                    ml: isUser ? 0 : 1,
                                    mr: isUser ? 1 : 0,
                                    fontWeight: 500,
                                    fontSize: '0.75rem'
                                }}
                            >
                                {isUser ? 'You' : 'AI Assistant'}
                            </Typography>

                            {/* Message Bubble */}
                            <Paper
                                elevation={0}
                                sx={{
                                    p: { xs: 2, sm: 2.5 },
                                    background: isUser
                                        ? `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`
                                        : theme.palette.background.paper,
                                    color: isUser ? 'white' : 'text.primary',
                                    borderRadius: isUser
                                        ? '18px 18px 6px 18px'
                                        : '18px 18px 18px 6px',
                                    boxShadow: isUser
                                        ? `0 4px 16px ${alpha(theme.palette.primary.main, 0.25)}`
                                        : `0 2px 12px ${alpha(theme.palette.grey[900], 0.08)}`,
                                    border: !isUser
                                        ? `1px solid ${alpha(theme.palette.divider, 0.12)}`
                                        : 'none',
                                    position: 'relative',
                                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                    '&:hover': {
                                        transform: 'translateY(-1px)',
                                        boxShadow: isUser
                                            ? `0 6px 20px ${alpha(theme.palette.primary.main, 0.3)}`
                                            : `0 4px 16px ${alpha(theme.palette.grey[900], 0.12)}`,
                                    },
                                }}
                            >
                                {/* Message Content */}
                                <Box sx={{ position: 'relative' }}>
                                    {message.content && (Array.isArray(message.content) ? message.content.length > 0 : message.content.length > 0) ? (
                                        <>
                                            {/* Multimodal content (images, audio, video) */}
                                            {Array.isArray(message.content) && message.content.some(c => c.type !== 'text') && (
                                                <MessageContentDisplay content={message.content.filter(c => c.type !== 'text')} />
                                            )}

                                            {/* Text content — Markdown for assistant, plain for user */}
                                            {textContent && (
                                                !isUser ? (
                                                    <Box sx={{
                                                        '& p': { margin: 0 },
                                                        '& p + p': { marginTop: '0.5em' },
                                                        '& ul, & ol': { pl: 2, m: 0 },
                                                        '& li': { mb: 0.5 },
                                                        '& pre': {
                                                            bgcolor: alpha(theme.palette.grey[900], 0.05),
                                                            p: 1.5,
                                                            borderRadius: 1,
                                                            overflow: 'auto',
                                                            fontSize: '0.875em',
                                                        },
                                                        '& code': {
                                                            bgcolor: alpha(theme.palette.primary.main, 0.08),
                                                            px: 0.5,
                                                            py: 0.25,
                                                            borderRadius: 0.5,
                                                            fontFamily: 'Monaco, Consolas, monospace',
                                                            fontSize: '0.875em',
                                                        },
                                                        '& pre code': {
                                                            bgcolor: 'transparent',
                                                            p: 0,
                                                        },
                                                    }}>
                                                        <ReactMarkdown
                                                            remarkPlugins={[remarkGfm]}
                                                            rehypePlugins={[rehypeHighlight]}
                                                            components={{
                                                                p: ({ children }) => <Typography variant="body2" component="div" sx={{ lineHeight: 1.7 }}>{children}</Typography>,
                                                                h1: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                h2: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                h3: ({ children }) => <Typography variant="subtitle1" component="div" sx={{ fontWeight: 'bold', mb: 0.5 }}>{children}</Typography>,
                                                                strong: ({ children }) => <Box component="strong" sx={{ fontWeight: 600 }}>{children}</Box>,
                                                                em: ({ children }) => <Box component="em" sx={{ fontStyle: 'italic' }}>{children}</Box>,
                                                            }}
                                                        >
                                                            {textContent}
                                                        </ReactMarkdown>
                                                    </Box>
                                                ) : (
                                                    <Typography
                                                        variant="body1"
                                                        sx={{
                                                            whiteSpace: 'pre-wrap',
                                                            lineHeight: 1.6,
                                                            fontSize: '0.95rem',
                                                            fontWeight: 400,
                                                        }}
                                                    >
                                                        {textContent}
                                                    </Typography>
                                                )
                                            )}
                                        </>
                                    ) : (
                                        loading && !isUser && index === messages.length - 1 && (
                                            <Typography variant="body2" color="text.secondary">
                                                ...
                                            </Typography>
                                        )
                                    )}

                                    {/* Action Buttons */}
                                    <Box
                                        sx={{
                                            position: 'absolute',
                                            top: -8,
                                            right: -8,
                                            display: 'flex',
                                            gap: 0.5,
                                            opacity: 0,
                                            transition: 'opacity 0.2s ease-in-out',
                                            '.MuiPaper-root:hover &': { opacity: 1 }
                                        }}
                                    >
                                        <Tooltip title="Copy message">
                                            <IconButton
                                                size="small"
                                                onClick={() => {
                                                    const copyText = Array.isArray(message.content)
                                                        ? message.content
                                                            .filter(c => c.type === 'text')
                                                            .map(c => c.text || '')
                                                            .join(' ')
                                                        : message.content || '';
                                                    onCopyMessage(copyText);
                                                }}
                                                sx={{
                                                    width: 28,
                                                    height: 28,
                                                    backgroundColor: alpha(theme.palette.background.paper, 0.9),
                                                    color: 'text.secondary',
                                                    '&:hover': {
                                                        backgroundColor: theme.palette.background.paper,
                                                        color: 'primary.main'
                                                    }
                                                }}
                                            >
                                                <CopyIcon sx={{ fontSize: 14 }} />
                                            </IconButton>
                                        </Tooltip>
                                    </Box>
                                </Box>
                            </Paper>
                        </Box>

                        {/* User Avatar */}
                        {isUser && (
                            <Box
                                sx={{
                                    width: 36,
                                    height: 36,
                                    borderRadius: '50%',
                                    background: `linear-gradient(135deg, ${alpha(theme.palette.grey[600], 0.8)}, ${alpha(theme.palette.grey[700], 0.8)})`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0,
                                    boxShadow: `0 2px 8px ${alpha(theme.palette.grey[500], 0.3)}`,
                                    mt: 0.5
                                }}
                            >
                                <Typography
                                    sx={{
                                        color: 'white',
                                        fontSize: '0.875rem',
                                        fontWeight: 600
                                    }}
                                >
                                    U
                                </Typography>
                            </Box>
                        )}
                    </Box>
                );
            })}
        </>
    );
};

export default ChatMessages;
