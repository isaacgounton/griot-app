import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
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
    Box,
} from '@mui/material';

import { Provider, Model } from '../../types/anyllm';
import { ModelConfig } from '../../types/agents';

export interface ModelConfigurationDialogProps {
    open: boolean;
    onClose: () => void;
    onSave: () => void;
    modelConfig: ModelConfig;
    providers: Provider[];
    models: Model[];
    providersLoading: boolean;
    modelsLoading: boolean;
    modelsError: string | null;
    onProviderChange: (provider: string) => void;
    onModelChange: (model: string) => void;
    onUpdateModelConfig: (updates: Partial<ModelConfig>) => void;
    defaultProvider: string;
    defaultModel: string;
    onSetDefault: () => void;
    onClearDefault: () => void;
}

export const ModelConfigurationDialog: React.FC<ModelConfigurationDialogProps> = ({
    open,
    onClose,
    onSave,
    modelConfig,
    providers,
    models,
    providersLoading,
    modelsLoading,
    modelsError,
    onProviderChange,
    onModelChange,
    onUpdateModelConfig,
    defaultProvider,
    defaultModel,
    onSetDefault,
    onClearDefault,
}) => (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Model Configuration</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
            <Grid container spacing={2} sx={{ mt: 0 }}>
                <Grid item xs={12} sm={6}>
                    <FormControl fullWidth size="small">
                        <InputLabel>Provider</InputLabel>
                        <Select
                            value={modelConfig.provider || ''}
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
                            value={modelConfig.model || ''}
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
                        Temperature: {modelConfig.temperature}
                    </Typography>
                    <Slider
                        value={modelConfig.temperature}
                        onChange={(_, value) => onUpdateModelConfig({ temperature: value as number })}
                        min={0}
                        max={2}
                        step={0.1}
                        marks={[
                            { value: 0, label: 'Focused' },
                            { value: 0.7, label: 'Balanced' },
                            { value: 1.5, label: 'Creative' },
                            { value: 2, label: 'Random' },
                        ]}
                    />
                </Grid>
                <Grid item xs={12}>
                    <Typography variant="body2" gutterBottom>
                        Top P (Nucleus Sampling): {modelConfig.top_p}
                    </Typography>
                    <Slider
                        value={modelConfig.top_p}
                        onChange={(_, value) => onUpdateModelConfig({ top_p: value as number })}
                        min={0}
                        max={1}
                        step={0.05}
                        marks={[
                            { value: 0.1, label: '0.1' },
                            { value: 0.5, label: '0.5' },
                            { value: 0.9, label: '0.9' },
                            { value: 1, label: '1.0' },
                        ]}
                    />
                </Grid>
                <Grid item xs={12}>
                    <Typography variant="body2" gutterBottom>
                        Top K: {modelConfig.top_k}
                    </Typography>
                    <Slider
                        value={modelConfig.top_k}
                        onChange={(_, value) => onUpdateModelConfig({ top_k: value as number })}
                        min={0}
                        max={1}
                        step={0.1}
                        marks={[
                            { value: 0, label: 'Disabled' },
                            { value: 0.5, label: '0.5' },
                            { value: 1, label: '1.0' },
                        ]}
                    />
                </Grid>
                <Grid item xs={12}>
                    <Typography variant="body2" gutterBottom>
                        Max Tokens: {modelConfig.max_tokens}
                    </Typography>
                    <Slider
                        value={modelConfig.max_tokens}
                        onChange={(_, value) => onUpdateModelConfig({ max_tokens: value as number })}
                        min={100}
                        max={8000}
                        step={100}
                        marks={[
                            { value: 100, label: '100' },
                            { value: 1000, label: '1K' },
                            { value: 2000, label: '2K' },
                            { value: 4000, label: '4K' },
                            { value: 8000, label: '8K' },
                        ]}
                    />
                </Grid>
                <Grid item xs={12}>
                    <FormControlLabel
                        control={
                            <Switch
                                checked={modelConfig.stream}
                                onChange={(e) => onUpdateModelConfig({ stream: e.target.checked })}
                            />
                        }
                        label="Stream Responses"
                    />
                </Grid>

                {/* Default Settings Section */}
                <Grid item xs={12}>
                    <Typography variant="subtitle2" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                        Default Settings
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Button
                            size="small"
                            variant="outlined"
                            onClick={onSetDefault}
                            disabled={!modelConfig.provider || !modelConfig.model}
                            fullWidth
                        >
                            Set as Default
                        </Button>
                        <Button
                            size="small"
                            variant="outlined"
                            color="secondary"
                            onClick={onClearDefault}
                            fullWidth
                        >
                            Clear Defaults
                        </Button>
                    </Box>

                    {(defaultProvider || defaultModel) && (
                        <Alert severity="info" sx={{ mt: 1 }}>
                            <Typography variant="caption">
                                <strong>Current Defaults:</strong>
                                {defaultProvider && <><br />• Provider: {defaultProvider}</>}
                                {defaultModel && <><br />• Model: {defaultModel}</>}
                            </Typography>
                        </Alert>
                    )}
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

