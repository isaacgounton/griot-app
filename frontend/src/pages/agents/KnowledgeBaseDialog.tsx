import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Box,
    Typography,
    Tooltip,
    LinearProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Grid,
    FormControlLabel,
    Switch,
    Slider,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import UploadIcon from '@mui/icons-material/Upload';
import StorageIcon from '@mui/icons-material/Storage';
import { alpha, useTheme } from '@mui/material/styles';

import { KnowledgeBase, SessionSettings } from '../../types/agents';

export interface KnowledgeBaseDialogProps {
    open: boolean;
    onClose: () => void;
    knowledgeBases: KnowledgeBase[];
    selectedKnowledgeBase: KnowledgeBase | null;
    onSelectKnowledgeBase: (knowledgeBase: KnowledgeBase) => void;
    onToggleKnowledgeBase: (knowledgeBaseId: string, enabled: boolean) => void;
    uploadingDocument: boolean;
    uploadProgress: number;
    onUploadDocument: (file: File) => void;
    sessionSettings: SessionSettings;
    onUpdateSessionSettings: (updates: Partial<SessionSettings>) => void;
}

export const KnowledgeBaseDialog: React.FC<KnowledgeBaseDialogProps> = ({
    open,
    onClose,
    knowledgeBases,
    selectedKnowledgeBase,
    onSelectKnowledgeBase,
    onToggleKnowledgeBase,
    uploadingDocument,
    uploadProgress,
    onUploadDocument,
    sessionSettings,
    onUpdateSessionSettings,
}) => {
    const theme = useTheme();

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>Knowledge Base</DialogTitle>
            <DialogContent>
                <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        Upload PDF documents to enhance your conversations with contextual information.
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                        <Tooltip
                            title={
                                knowledgeBases.length === 0
                                    ? 'Knowledge base features require database connectivity'
                                    : 'Upload PDF documents to enhance conversations'
                            }
                        >
                            <span>
                                <Button
                                    variant="outlined"
                                    component="label"
                                    startIcon={<UploadIcon />}
                                    disabled={uploadingDocument || knowledgeBases.length === 0}
                                >
                                    Upload Document
                                    <input
                                        type="file"
                                        hidden
                                        accept=".pdf"
                                        onChange={(e) => {
                                            const file = e.target.files?.[0];
                                            if (file) {
                                                onUploadDocument(file);
                                            }
                                        }}
                                    />
                                </Button>
                            </span>
                        </Tooltip>
                        {uploadingDocument && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1 }}>
                                <LinearProgress
                                    variant="determinate"
                                    value={uploadProgress}
                                    sx={{ flexGrow: 1 }}
                                />
                                <Typography variant="body2">{Math.round(uploadProgress)}%</Typography>
                            </Box>
                        )}
                    </Box>
                </Box>

                <Accordion>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>Knowledge Base Settings</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                        <Grid container spacing={2}>
                            <Grid item xs={12}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={sessionSettings.knowledge_base_enabled}
                                            onChange={(e) =>
                                                onUpdateSessionSettings({
                                                    knowledge_base_enabled: e.target.checked,
                                                })
                                            }
                                            disabled={knowledgeBases.length === 0}
                                        />
                                    }
                                    label="Enable Knowledge Base"
                                />
                                {knowledgeBases.length === 0 && (
                                    <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                                        Requires database connectivity
                                    </Typography>
                                )}
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="body2" gutterBottom>
                                    Chunk Size: 1024
                                </Typography>
                                <Slider
                                    value={1024}
                                    min={256}
                                    max={2048}
                                    step={128}
                                    disabled={knowledgeBases.length === 0}
                                    marks={[
                                        { value: 256, label: '256' },
                                        { value: 512, label: '512' },
                                        { value: 1024, label: '1024' },
                                        { value: 2048, label: '2048' },
                                    ]}
                                />
                            </Grid>
                            <Grid item xs={12}>
                                <Typography variant="body2" gutterBottom>
                                    Chunk Overlap: 256
                                </Typography>
                                <Slider
                                    value={256}
                                    min={0}
                                    max={512}
                                    step={64}
                                    disabled={knowledgeBases.length === 0}
                                    marks={[
                                        { value: 0, label: '0' },
                                        { value: 256, label: '256' },
                                        { value: 512, label: '512' },
                                    ]}
                                />
                            </Grid>
                        </Grid>
                    </AccordionDetails>
                </Accordion>

                {knowledgeBases.length > 0 && (
                    <Box sx={{ mt: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Your Knowledge Bases
                        </Typography>
                        <List>
                            {knowledgeBases.map((kb) => (
                                <ListItem
                                    key={kb.id}
                                    button
                                    selected={selectedKnowledgeBase?.id === kb.id}
                                    onClick={() => onSelectKnowledgeBase(kb)}
                                    sx={{
                                        borderRadius: 2,
                                        mb: 1,
                                        border: '1px solid',
                                        borderColor: 'divider',
                                    }}
                                >
                                    <ListItemIcon>
                                        <StorageIcon />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={kb.name}
                                        secondary={
                                            <Box>
                                                <Typography variant="body2" color="text.secondary" component="span">
                                                    {kb.description}
                                                </Typography>
                                                <Typography
                                                    variant="caption"
                                                    color="text.secondary"
                                                    component="span"
                                                    sx={{ display: 'block' }}
                                                >
                                                    {kb.document_count} documents •{' '}
                                                    {((kb.size || 0) / 1024 / 1024).toFixed(1)}MB
                                                </Typography>
                                            </Box>
                                        }
                                        primaryTypographyProps={{ component: 'div' }}
                                        secondaryTypographyProps={{ component: 'div' }}
                                    />
                                    <Switch
                                        checked={kb.enabled}
                                        onChange={(e) => onToggleKnowledgeBase(kb.id, e.target.checked)}
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Box>
                )}

                {knowledgeBases.length === 0 && (
                    <Box sx={{ mt: 3, p: 3, bgcolor: alpha(theme.palette.info.main, 0.1), borderRadius: 2 }}>
                        <Typography variant="h6" gutterBottom color="info.main">
                            <StorageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                            Knowledge Base Unavailable
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Knowledge base features require database connectivity. The database appears to be
                            unavailable in your current environment.
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            To use knowledge base features:
                        </Typography>
                        <Box component="ul" sx={{ mt: 1, pl: 3 }}>
                            <li>
                                <Typography variant="body2" color="text.secondary">
                                    Ensure your database is running and accessible
                                </Typography>
                            </li>
                            <li>
                                <Typography variant="body2" color="text.secondary">
                                    Check your database connection settings
                                </Typography>
                            </li>
                            <li>
                                <Typography variant="body2" color="text.secondary">
                                    Restart the application with proper database configuration
                                </Typography>
                            </li>
                        </Box>
                    </Box>
                )}
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>Close</Button>
            </DialogActions>
        </Dialog>
    );
};

