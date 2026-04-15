/**
 * ChatHistorySidebar Component
 * Collapsible sidebar showing chat conversation history
 * Design inspired by agent-chat-ui with Material-UI components
 */

import React, { useState, useEffect } from 'react';
import {
    Box,
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    Typography,
    IconButton,
    CircularProgress,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Tooltip,
    Divider,
    Paper,
    useTheme,
    alpha,
} from '@mui/material';
import {
    Add as AddIcon,
    Close as CloseIcon,
    ChatBubbleOutline as ChatIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
} from '@mui/icons-material';
import { useChatHistory } from '../../contexts/ChatHistoryContext';
import { ChatSession } from '../../services/chatSessions';

interface ChatHistorySidebarProps {
    // eslint-disable-next-line no-unused-vars
    onSessionSelect?(sessionId: string | null): void;
    currentSessionId?: string | null;
}

export function ChatHistorySidebar({ onSessionSelect, currentSessionId }: ChatHistorySidebarProps) {
    const theme = useTheme();
    const {
        sessions,
        loading,
        sidebarOpen,
        setSidebarOpen,
        deleteSession,
        updateSession,
        createNewSession,
        loadSessions,
    } = useChatHistory();

    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
    const [editTitle, setEditTitle] = useState('');

    // Refresh sessions when sidebar opens (only if authenticated)
    useEffect(() => {
        if (sidebarOpen && localStorage.getItem('griot_api_key')) {
            loadSessions();
        }
    }, [sidebarOpen, loadSessions]);

    const handleSessionClick = (session: ChatSession) => {
        onSessionSelect?.(session.session_id);
    };

    const handleNewChat = async () => {
        const newSession = await createNewSession();
        onSessionSelect?.(newSession.session_id);
    };

    const handleDeleteClick = (session: ChatSession, e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedSession(session);
        setDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (selectedSession) {
            await deleteSession(selectedSession.session_id);
            if (currentSessionId === selectedSession.session_id) {
                onSessionSelect?.(null);
            }
        }
        setDeleteDialogOpen(false);
        setSelectedSession(null);
    };

    const handleEditClick = (session: ChatSession, e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedSession(session);
        setEditTitle(session.title || 'New Chat');
        setEditDialogOpen(true);
    };

    const handleEditSave = async () => {
        if (selectedSession) {
            await updateSession(selectedSession.session_id, { title: editTitle });
            setEditDialogOpen(false);
            setSelectedSession(null);
        }
    };

    const formatSessionTitle = (session: ChatSession) => {
        if (session.title) return session.title;
        const createdAt = new Date(session.created_at);
        return `Chat ${createdAt.toLocaleDateString()} ${createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    };

    const drawerContent = (
        <Box
            sx={{
                width: 300,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'background.paper',
                borderRight: `1px solid ${alpha(theme.palette.divider, 0.12)}`,
            }}
        >
            {/* Header */}
            <Box
                sx={{
                    p: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderBottom: `1px solid ${alpha(theme.palette.divider, 0.12)}`,
                }}
            >
                <Typography variant="h6" fontWeight="600">
                    Chat History
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="New chat">
                        <IconButton size="small" onClick={handleNewChat}>
                            <AddIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Close sidebar">
                        <IconButton size="small" onClick={() => setSidebarOpen(false)}>
                            <CloseIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* Sessions List */}
            <Box sx={{ flex: 1, overflow: 'auto', bgcolor: alpha(theme.palette.action.hover, 0.02) }}>
                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                        <CircularProgress size={24} />
                    </Box>
                ) : sessions.length === 0 ? (
                    <Box sx={{ p: 3, textAlign: 'center' }}>
                        <ChatIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                            No chat history yet
                        </Typography>
                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={<AddIcon />}
                            onClick={handleNewChat}
                            sx={{ mt: 2 }}
                        >
                            Start a new chat
                        </Button>
                    </Box>
                ) : (
                    <List dense sx={{ py: 1 }}>
                        {sessions.map((session, index) => (
                            <React.Fragment key={session.session_id}>
                                <ListItem
                                    disablePadding
                                    sx={{
                                        '& .session-actions': {
                                            opacity: 0,
                                            transform: 'translateX(4px)',
                                            transition: 'opacity 0.18s ease, transform 0.18s ease',
                                        },
                                        '&:hover .session-actions, &:focus-within .session-actions': {
                                            opacity: 1,
                                            transform: 'translateX(0)',
                                        },
                                    }}
                                    secondaryAction={
                                        <Box className="session-actions" sx={{ display: 'flex', gap: 0.25 }}>
                                            <IconButton
                                                size="small"
                                                onClick={(e) => handleEditClick(session, e)}
                                                sx={{
                                                    color: 'text.secondary',
                                                    '&:hover': {
                                                        color: 'text.primary',
                                                        bgcolor: alpha(theme.palette.text.primary, 0.06),
                                                    },
                                                }}
                                            >
                                                <EditIcon fontSize="small" />
                                            </IconButton>
                                            <IconButton
                                                size="small"
                                                onClick={(e) => handleDeleteClick(session, e)}
                                                sx={{
                                                    color: 'text.secondary',
                                                    '&:hover': {
                                                        color: 'error.main',
                                                        bgcolor: alpha(theme.palette.error.main, 0.1),
                                                    },
                                                }}
                                            >
                                                <DeleteIcon fontSize="small" />
                                            </IconButton>
                                        </Box>
                                    }
                                >
                                    <ListItemButton
                                        selected={currentSessionId === session.session_id}
                                        onClick={() => handleSessionClick(session)}
                                        sx={{
                                            py: 1.5,
                                            px: 2,
                                            mx: 1,
                                            my: 0.5,
                                            borderRadius: 1.5,
                                            '&.Mui-selected': {
                                                bgcolor: alpha(theme.palette.primary.main, 0.12),
                                                '&:hover': {
                                                    bgcolor: alpha(theme.palette.primary.main, 0.16),
                                                },
                                            },
                                        }}
                                    >
                                        <Box sx={{ mr: 1.5 }}>
                                            <ChatIcon
                                                fontSize="small"
                                                sx={{
                                                    color: currentSessionId === session.session_id
                                                        ? 'primary.main'
                                                        : 'text.disabled',
                                                }}
                                            />
                                        </Box>
                                        <ListItemText
                                            primary={
                                                <Typography
                                                    variant="body2"
                                                    sx={{
                                                        fontWeight: currentSessionId === session.session_id ? 500 : 400,
                                                        overflow: 'hidden',
                                                        textOverflow: 'ellipsis',
                                                        whiteSpace: 'nowrap',
                                                    }}
                                                >
                                                    {formatSessionTitle(session)}
                                                </Typography>
                                            }
                                            secondary={
                                                <Typography
                                                    variant="caption"
                                                    color="text.secondary"
                                                    sx={{ fontSize: '0.7rem' }}
                                                >
                                                    {new Date(session.created_at).toLocaleDateString()}
                                                </Typography>
                                            }
                                        />
                                    </ListItemButton>
                                </ListItem>
                                {index < sessions.length - 1 && (
                                    <Divider component="li" sx={{ ml: 2, mr: 2 }} />
                                )}
                            </React.Fragment>
                        ))}
                    </List>
                )}
            </Box>
        </Box>
    );

    return (
        <>
            {/* Mobile Drawer */}
            <Drawer
                anchor="left"
                open={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                sx={{
                    display: { xs: 'block', lg: 'none' },
                    '& .MuiDrawer-paper': {
                        width: 300,
                    },
                }}
            >
                {drawerContent}
            </Drawer>

            {/* Desktop Sidebar */}
            <Box
                sx={{
                    display: { xs: 'none', lg: 'flex' },
                    position: 'relative',
                    height: '100%',
                    transition: 'width 0.3s ease',
                    width: sidebarOpen ? 300 : 0,
                    overflow: 'hidden',
                }}
            >
                <Paper
                    elevation={0}
                    sx={{
                        width: 300,
                        height: '100%',
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
                    }}
                >
                    {drawerContent}
                </Paper>
            </Box>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>Delete Chat?</DialogTitle>
                <DialogContent>
                    <Typography variant="body2" color="text.secondary">
                        Are you sure you want to delete "{selectedSession?.title || 'this chat'}"? This action cannot be undone.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
                    <Button
                        onClick={handleDeleteConfirm}
                        color="error"
                        variant="outlined"
                        sx={{ borderWidth: 1.5 }}
                    >
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Edit Title Dialog */}
            <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Rename Chat</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        fullWidth
                        variant="outlined"
                        label="Chat title"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        sx={{ mt: 1 }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleEditSave} variant="contained">
                        Save
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
}

export default ChatHistorySidebar;
