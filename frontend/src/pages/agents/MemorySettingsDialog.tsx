import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Grid,
    FormControlLabel,
    Switch,
    Slider,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
} from '@mui/material';

import { MemorySettings } from '../../types/agents';

export interface MemorySettingsDialogProps {
    open: boolean;
    onClose: () => void;
    onSave: () => void;
    memorySettings: MemorySettings;
    onUpdateMemorySettings: (updates: Partial<MemorySettings>) => void;
}

export const MemorySettingsDialog: React.FC<MemorySettingsDialogProps> = ({
    open,
    onClose,
    onSave,
    memorySettings,
    onUpdateMemorySettings,
}) => (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>Memory Settings</DialogTitle>
        <DialogContent>
            <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
                Configure how the agent remembers and uses context from previous conversations.
            </Typography>

            <Grid container spacing={2}>
                <Grid item xs={12}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={memorySettings.short_term_enabled}
                                onChange={(e) =>
                                    onUpdateMemorySettings({ short_term_enabled: e.target.checked })
                                }
                            />
                        }
                        label="Short-term Memory"
                    />
                </Grid>
                <Grid item xs={12}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={memorySettings.long_term_enabled}
                                onChange={(e) =>
                                    onUpdateMemorySettings({ long_term_enabled: e.target.checked })
                                }
                            />
                        }
                        label="Long-term Memory"
                    />
                </Grid>
                <Grid item xs={12}>
                    <Typography variant="body2" gutterBottom>
                        History Runs: {memorySettings.history_runs}
                    </Typography>
                    <Slider
                        value={memorySettings.history_runs}
                        onChange={(_, value) =>
                            onUpdateMemorySettings({ history_runs: value as number })
                        }
                        min={0}
                        max={10}
                        step={1}
                        marks={[
                            { value: 0, label: '0' },
                            { value: 5, label: '5' },
                            { value: 10, label: '10' },
                        ]}
                    />
                </Grid>
                <Grid item xs={12}>
                    <FormControl fullWidth size="small">
                        <InputLabel>Memory Type</InputLabel>
                        <Select
                            value={memorySettings.memory_type}
                            onChange={(e) =>
                                onUpdateMemorySettings({ memory_type: e.target.value as typeof memorySettings.memory_type })
                            }
                            label="Memory Type"
                        >
                            <MenuItem value="conversation">Conversation</MenuItem>
                            <MenuItem value="semantic">Semantic</MenuItem>
                            <MenuItem value="episodic">Episodic</MenuItem>
                            <MenuItem value="procedural">Procedural</MenuItem>
                        </Select>
                    </FormControl>
                </Grid>
                <Grid item xs={12}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={memorySettings.auto_summarize}
                                onChange={(e) =>
                                    onUpdateMemorySettings({ auto_summarize: e.target.checked })
                                }
                            />
                        }
                        label="Auto-summarize Long Conversations"
                    />
                </Grid>
            </Grid>
        </DialogContent>
        <DialogActions>
            <Button onClick={onClose}>Close</Button>
            <Button onClick={onSave} variant="contained">
                Save
            </Button>
        </DialogActions>
    </Dialog>
);

