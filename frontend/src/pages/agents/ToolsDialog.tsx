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
    Paper,
    Switch,
} from '@mui/material';

export interface ToolConfig {
    name: string;
    description: string;
    enabled: boolean;
}

export interface ToolsDialogProps {
    open: boolean;
    onClose: () => void;
    tools: ToolConfig[];
    onToggleTool: (toolName: string, enabled: boolean) => void;
}

export const ToolsDialog: React.FC<ToolsDialogProps> = ({ open, onClose, tools, onToggleTool }) => (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Tools & Integrations</DialogTitle>
        <DialogContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
                Manage external tools and integrations available to your agents.
            </Typography>

            <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                    Available Tools
                </Typography>
                <Grid container spacing={2}>
                    {tools.map((tool) => (
                        <Grid item xs={12} sm={6} key={tool.name}>
                            <Paper sx={{ p: 2, border: '1px solid #e2e8f0' }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Box>
                                        <Typography variant="subtitle2">{tool.name}</Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {tool.description}
                                        </Typography>
                                    </Box>
                                    <Switch
                                        checked={tool.enabled}
                                        onChange={(e) => onToggleTool(tool.name, e.target.checked)}
                                    />
                                </Box>
                            </Paper>
                        </Grid>
                    ))}
                </Grid>
            </Box>
        </DialogContent>
        <DialogActions>
            <Button onClick={onClose}>Close</Button>
        </DialogActions>
    </Dialog>
);

