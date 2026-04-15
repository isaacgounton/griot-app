import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
} from '@mui/material';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';

export interface ImportSessionDialogProps {
    open: boolean;
    onClose: () => void;
    onImport: (file: File) => void;
}

export const ImportSessionDialog: React.FC<ImportSessionDialogProps> = ({
    open,
    onClose,
    onImport,
}) => (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Import Session</DialogTitle>
        <DialogContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                Select a session file to import (JSON, Markdown, or CSV format).
            </Typography>
            <Button
                variant="outlined"
                component="label"
                fullWidth
                startIcon={<FolderOpenIcon />}
                sx={{ mt: 2 }}
            >
                Select File
                <input
                    type="file"
                    hidden
                    accept=".json,.md,.txt,.csv"
                    onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                            onImport(file);
                        }
                    }}
                />
            </Button>
        </DialogContent>
        <DialogActions>
            <Button onClick={onClose}>Cancel</Button>
        </DialogActions>
    </Dialog>
);

