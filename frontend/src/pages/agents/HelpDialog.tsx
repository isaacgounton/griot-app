import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    Grid,
} from '@mui/material';

export interface HelpDialogProps {
    open: boolean;
    onClose: () => void;
}

const SHORTCUTS = [
    { key: 'Ctrl+K', description: 'Toggle Sidebar' },
    { key: 'Ctrl+S', description: 'Save Session' },
    { key: 'Ctrl+E', description: 'Export Session' },
    { key: 'Ctrl+I', description: 'Import Session' },
    { key: 'Ctrl+/', description: 'Focus Input' },
    { key: 'Ctrl+F', description: 'Search' },
    { key: 'Ctrl+D', description: 'Toggle Theme' },
    { key: 'Enter', description: 'Send Message' },
    { key: 'Shift+Enter', description: 'New Line' },
    { key: 'Escape', description: 'Stop Generation' },
];

export const HelpDialog: React.FC<HelpDialogProps> = ({ open, onClose }) => (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Help & Keyboard Shortcuts</DialogTitle>
        <DialogContent>
            <Typography variant="h6" gutterBottom>
                Keyboard Shortcuts
            </Typography>
            <Box sx={{ mb: 3 }}>
                <Grid container spacing={1}>
                    {SHORTCUTS.map((shortcut) => (
                        <Grid item xs={12} key={shortcut.key}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Typography variant="body2" fontWeight="600">
                                    {shortcut.key}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    {shortcut.description}
                                </Typography>
                            </Box>
                        </Grid>
                    ))}
                </Grid>
            </Box>

            <Typography variant="h6" gutterBottom>
                Tips
            </Typography>
            <Typography variant="body2" color="text.secondary">
                • Use the sidebar to switch between agents and sessions
                <br />
                • Click on agent cards to start new conversations
                <br />
                • Configure model settings in the advanced options
                <br />
                • Enable knowledge base to upload documents for context
                <br />
                • Use voice input for hands-free messaging
                <br />
                • Export your conversations in various formats
                <br />
                • Enable memory to maintain context across sessions
            </Typography>
        </DialogContent>
        <DialogActions>
            <Button onClick={onClose}>Close</Button>
        </DialogActions>
    </Dialog>
);

