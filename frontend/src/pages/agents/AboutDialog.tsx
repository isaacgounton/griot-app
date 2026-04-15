import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
} from '@mui/material';
import BookIcon from '@mui/icons-material/Book';
import ShareIcon from '@mui/icons-material/Share';

export interface AboutDialogProps {
    open: boolean;
    onClose: () => void;
}

export const AboutDialog: React.FC<AboutDialogProps> = ({ open, onClose }) => (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>About AI Agents</DialogTitle>
        <DialogContent>
            <Box sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" gutterBottom>
                    AI Agents 🤖
                </Typography>
                <Typography variant="body1" color="text.secondary" gutterBottom>
                    Enhanced AI Agent Interface
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                    Version 1.0.0
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    A feature-rich interface for interacting with AI agents, with advanced settings,
                    memory management, knowledge base integration, and more.
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                    <Button variant="outlined" size="small">
                        <BookIcon sx={{ mr: 1 }} />
                        Documentation
                    </Button>
                    <Button variant="outlined" size="small">
                        <ShareIcon sx={{ mr: 1 }} />
                        Share
                    </Button>
                </Box>
            </Box>
        </DialogContent>
        <DialogActions>
            <Button onClick={onClose}>Close</Button>
        </DialogActions>
    </Dialog>
);

