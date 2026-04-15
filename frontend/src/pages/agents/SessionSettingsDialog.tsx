import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Grid,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    LinearProgress,
    Alert,
    Typography,
    Slider,
    FormControlLabel,
    Switch,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import { Provider, Model } from '../../types/anyllm';
import { ModelConfig, SessionSettings } from '../../types/agents';

export interface SessionSettingsDialogProps {
    open: boolean;
    onClose: () => void;
    onSave: () => void;
    modelConfig: ModelConfig;
    sessionSettings: SessionSettings;
    providers: Provider[];
    models: Model[];
    providersLoading: boolean;
    modelsLoading: boolean;
    modelsError: string | null;
    onProviderChange: (provider: string) => void;
    onModelChange: (model: string) => void;
    onUpdateModelConfig: (updates: Partial<ModelConfig>) => void;
    onUpdateSessionSettings: (updates: Partial<SessionSettings>) => void;
}

export const SessionSettingsDialog: React.FC<SessionSettingsDialogProps> = ({
    open,
    onClose,
    onSave,
    modelConfig,
    sessionSettings,
    providers,
    models,
    providersLoading,
    modelsLoading,
    modelsError,
    onProviderChange,
    onModelChange,
    onUpdateModelConfig: _onUpdateModelConfig,
    onUpdateSessionSettings,
}) => {
    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Session Settings</DialogTitle>
            <DialogContent sx={{ pt: 2 }}>
                <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Model Configuration</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Grid container spacing={2} sx={{ mt: 0 }}>
                            <Grid item xs={12} sm={6}>
                                <FormControl fullWidth size="small">
                                    <InputLabel>Provider</InputLabel>
                                    <Select
                                        value={modelConfig.provider}
                                        onChange={(e) => onProviderChange(e.target.value as string)}
                                        label="Provider"
                                        disabled={providersLoading}
                                    >
                                        {providers.map((provider) => (
                                            <MenuItem key={provider.name} value={provider.name}>
                                                {provider.display_name || provider.name}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControl fullWidth size="small">
                                    <InputLabel>Model</InputLabel>
                                    <Select
                                        value={modelConfig.model}
                                        onChange={(e) => onModelChange(e.target.value as string)}
                                        label="Model"
                                        disabled={modelsLoading}
                                    >
                                        {models.map((model) => (
                                            <MenuItem key={model.id} value={model.id}>
                                                {model.id}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                            {modelsLoading && (
                                <Grid item xs={12}>
                                    <LinearProgress />
                                </Grid>
                            )}
                            {modelsError && (
                                <Grid item xs={12}>
                                    <Alert severity="warning">{modelsError}</Alert>
                                </Grid>
                            )}
                            <Grid item xs={12}>
                                <Typography variant="body2" gutterBottom>
                                    Temperature: {sessionSettings.temperature}
                                </Typography>
                                <Slider
                                    value={sessionSettings.temperature}
                                    onChange={(_, value) =>
                                        onUpdateSessionSettings({ temperature: value as number })
                                    }
                                    min={0}
                                    max={2}
                                    step={0.1}
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="body2" gutterBottom>
                                    Max Tokens: {sessionSettings.max_tokens}
                                </Typography>
                                <Slider
                                    value={sessionSettings.max_tokens}
                                    onChange={(_, value) =>
                                        onUpdateSessionSettings({ max_tokens: value as number })
                                    }
                                    min={100}
                                    max={8000}
                                    step={100}
                                />
                            </Grid>
                        </Grid>
                    </AccordionDetails>
                </Accordion>

                <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Features</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.stream}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ stream: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Stream Responses"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.auto_save}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ auto_save: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Auto-save"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.auto_title}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ auto_title: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Auto-generate Titles"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.smart_completions}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    smart_completions: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Smart Completions"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.voice_input}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ voice_input: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Voice Input"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.voice_output}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ voice_output: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Voice Output"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.sound_effects}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ sound_effects: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Sound Effects"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.notifications}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    notifications: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Notifications"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.memory_enabled}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    memory_enabled: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Enable Memory"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.knowledge_base_enabled}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    knowledge_base_enabled: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Knowledge Base"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.reasoning_enabled}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    reasoning_enabled: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Reasoning Mode"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.tool_metadata_enabled}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    tool_metadata_enabled: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Tool Metadata"
                                />
                            </Grid>
                        </Grid>
                    </AccordionDetails>
                </Accordion>

                <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Privacy & Debug</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.privacy_mode}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ privacy_mode: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Privacy Mode"
                                />
                            </Grid>
                            <Grid item xs={12} sm={6}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.debug_mode}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({ debug_mode: e.target.checked })
                                            }
                                        />
                                    }
                                    label="Debug Mode"
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.experimental_features}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    experimental_features: e.target.checked,
                                                })
                                            }
                                        />
                                    }
                                    label="Experimental Features"
                                />
                            </Grid>
                        </Grid>
                    </AccordionDetails>
                </Accordion>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Close</Button>
                <Button onClick={onSave} variant="contained">
                    Save Settings
                </Button>
            </DialogActions>
        </Dialog>
    );
};
