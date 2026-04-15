import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import {
    Box,
    Typography,
    Card,
    CardContent,
    CardActions,
    Button,
    Grid,
    TextField,
    IconButton,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Chip,
    Paper,
    Divider,
    CircularProgress,
    Alert,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    useTheme,
    alpha,
    Tooltip,
    Tabs,
    Tab,
    Slider,
    Switch,
    FormControlLabel,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Menu,
    Snackbar,
    Backdrop,
    Drawer,
    InputAdornment,
    Avatar,
    ToggleButton,
    ToggleButtonGroup,
    LinearProgress as _LinearProgress,
    useMediaQuery,
} from '@mui/material';
import {
    SmartToy as BotIcon,
    Send as SendIcon,
    Search as SearchIcon,
    Psychology as AIIcon,
    Web as WebIcon,
    AttachMoney as FinanceIcon,
    Help as HelpIcon,
    Delete as DeleteIcon,
    History as HistoryIcon,
    Settings as SettingsIcon,
    ExpandMore as ExpandMoreIcon,
    Download as DownloadIcon,
    Upload as UploadIcon,
    Storage as StorageIcon,
    Memory as MemoryIcon,
    Info as InfoIcon,
    Stop as StopIcon,
    Refresh as RefreshIcon,
    Save as SaveIcon,
    Science as ScienceIcon,
    IntegrationInstructions as IntegrationIcon,
    AccountCircle as AccountIcon,
    Tune as TuneIcon,
    Sort as SortIcon,
    ViewList as ViewListIcon,
    ViewModule as ViewModuleIcon,
    VolumeUp as VolumeUpIcon,
    VolumeOff as VolumeOffIcon,
    Mic as MicIcon,
    MicOff as MicOffIcon,
    Book as BookIcon,
    NewReleases as NewsIcon,
    Star as StarIcon,
    Share as ShareIcon,
    Bookmark as BookmarkIcon,
    ContentCopy as ContentCopyIcon,
    Menu as MenuIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { Provider, Model } from '../../types/anyllm';
import { anyllm } from '../../services/anyllm';
import { directApi } from '../../utils/api';
import {
    Agent,
    Message,
    Session,
    SessionSettings,
    KnowledgeBase,
    MemorySettings,
    ModelConfig,
    ToolCall,
    SessionMetadata as _SessionMetadata,
} from '../../types/agents';
import { DEFAULT_MODELS, DEFAULT_PROVIDERS } from '../../constants/agents';
import {
    calculateCost,
    calculateTokens,
    formatTimestamp,
} from '../../utils/agents';
import { SessionSettingsDialog } from './SessionSettingsDialog';
import { KnowledgeBaseDialog } from './KnowledgeBaseDialog';
import { MemorySettingsDialog } from './MemorySettingsDialog';
import { ModelConfigurationDialog } from './ModelConfigurationDialog';
import { ToolsDialog, ToolConfig } from './ToolsDialog';
import { HelpDialog } from './HelpDialog';
import { AboutDialog } from './AboutDialog';
import { ImportSessionDialog } from './ImportSessionDialog';

const Agents: React.FC = () => {
    const theme = useTheme();
    const { apiKey } = useAuth();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    // Core State
    const [agents, setAgents] = useState<Agent[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [currentSession, setCurrentSession] = useState<Session | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [streamingResponse, setStreamingResponse] = useState('');

    // UI State
    const [showSettingsDialog, setShowSettingsDialog] = useState(false);
    const [showKnowledgeDialog, setShowKnowledgeDialog] = useState(false);
    const [showMemoryDialog, setShowMemoryDialog] = useState(false);
    const [showModelConfigDialog, setShowModelConfigDialog] = useState(false);
    const [showToolsDialog, setShowToolsDialog] = useState(false);
    const [showImportDialog, setShowImportDialog] = useState(false);
    const [showAboutDialog, setShowAboutDialog] = useState(false);
    const [showHelpDialog, setShowHelpDialog] = useState(false);

    // Sidebar State
    const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
    const [activeView, setActiveView] = useState<'agents' | 'sessions' | 'settings' | 'knowledge' | 'tools'>('agents');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    // Filter and Search State
    const [agentFilter, setAgentFilter] = useState('');
    const [sessionFilter, setSessionFilter] = useState('');
    const [selectedTab, setSelectedTab] = useState<'all' | 'agent' | 'team' | 'workflow'>('all');
    const [sortBy, setSortBy] = useState<'name' | 'created' | 'updated' | 'usage'>('created');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

    // Model Configuration State
    const [modelConfig, setModelConfig] = useState<ModelConfig>({
        provider: 'openai',
        model: 'gpt-4o-mini',
        temperature: 0.7,
        top_p: 0.9,
        top_k: 0.0,
        max_tokens: 2048,
        stream: true,
    });

    const [availableProviders, setAvailableProviders] = useState<Provider[]>(DEFAULT_PROVIDERS);
    const [availableModels, setAvailableModels] = useState<Model[]>(DEFAULT_MODELS);
    const [modelsLoading, setModelsLoading] = useState(false);
    const [modelsError, setModelsError] = useState<string | null>(null);
    // Cache for API responses to prevent redundant calls
    const [providersCache, _setProvidersCache] = useState<Map<string, any[]>>(new Map());
    const [modelsCache, _setModelsCache] = useState<Map<string, any[]>>(new Map());
    const [providersLoading, setProvidersLoading] = useState(false);

    const updateModelConfig = useCallback((updates: Partial<ModelConfig>) => {
        setModelConfig((prev) => ({ ...prev, ...updates }));
    }, []);

    // Session Settings State
    const [sessionSettings, setSessionSettings] = useState<SessionSettings>({
        provider: 'openai',
        model: 'gpt-4o-mini',
        temperature: 0.7,
        top_p: 0.9,
        top_k: 0.0,
        max_tokens: 2048,
        stream: true,
        memory_enabled: true,
        knowledge_base_enabled: false,
        reasoning_enabled: true,
        tool_metadata_enabled: true,
        theme: 'auto',
        language: 'en',
        export_format: 'json',
        auto_save: true,
        auto_title: true,
        smart_completions: true,
        voice_input: false,
        voice_output: false,
        sound_effects: true,
        notifications: true,
        privacy_mode: false,
        debug_mode: false,
        experimental_features: false,
    });

    const updateSessionSettings = useCallback((updates: Partial<SessionSettings>) => {
        setSessionSettings((prev) => ({ ...prev, ...updates }));
    }, []);

    // Memory Settings State
    const [memorySettings, setMemorySettings] = useState<MemorySettings>({
        short_term_enabled: true,
        long_term_enabled: true,
        history_runs: 5,
        memory_type: 'conversation',
        retention_days: 30,
        max_memories: 1000,
        auto_summarize: true,
        compression_ratio: 0.3,
        indexing_method: 'vector',
        search_method: 'semantic',
        privacy_level: 'private',
    });

    const updateMemorySettings = useCallback((updates: Partial<MemorySettings>) => {
        setMemorySettings((prev) => ({ ...prev, ...updates }));
    }, []);

    // Knowledge Base State
    const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
    const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<KnowledgeBase | null>(null);
    const [uploadingDocument, setUploadingDocument] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    const handleToggleKnowledgeBase = useCallback((knowledgeBaseId: string, enabled: boolean) => {
        setKnowledgeBases((prev) =>
            prev.map((kb) => (kb.id === knowledgeBaseId ? { ...kb, enabled } : kb))
        );
    }, []);

    // Audio State
    const [isRecording, setIsRecording] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);

    // Menu State
    const [settingsMenuAnchor, setSettingsMenuAnchor] = useState<null | HTMLElement>(null);
    const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);

    // Notification State
    const [notification, setNotification] = useState({
        open: false,
        message: '',
        severity: 'info' as 'success' | 'error' | 'warning' | 'info',
    });

    // Tool Event State
    const [toolEvents, setToolEvents] = useState<ToolCall[]>([]);
    const [showToolEvents, setShowToolEvents] = useState(true);

    const agentTools = useMemo<ToolConfig[]>(
        () => [
            { name: 'Web Search', description: 'Search the web for information', enabled: true },
            { name: 'Calculator', description: 'Perform mathematical calculations', enabled: true },
            { name: 'Code Interpreter', description: 'Execute code snippets', enabled: false },
            { name: 'Image Generation', description: 'Generate images from text', enabled: false },
            { name: 'File Operations', description: 'Read and write files', enabled: true },
            { name: 'Database Access', description: 'Query databases', enabled: false },
        ],
        []
    );

    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const drawerPaperRef = useRef<HTMLDivElement | null>(null);

    // Data Loading Functions
    const loadAgents = useCallback(async () => {
        try {
            const response = await directApi.getAgents();
            if (response.success && response.data) {
                setAgents(response.data as unknown as Agent[]);
            } else {
                console.error('Failed to load agents:', response.error);
                setAgents([]);
            }
        } catch (err) {
            console.error('Error loading agents:', err);
            setAgents([]);
        }
    }, []);

    const loadSessions = useCallback(async () => {
        try {
            const response = await directApi.getAgentSessions();
            if (response.success && response.data) {
                setSessions((response.data as any).sessions || []);
            } else {
                console.error('Failed to load sessions:', response.error);
                setSessions([]);
            }
        } catch (err) {
            console.error('Error loading sessions:', err);
            setSessions([]);
        }
    }, []);

    const loadKnowledgeBases = useCallback(async () => {
        try {
            const response = await directApi.getKnowledgeBases();
            if (response.success && response.data) {
                setKnowledgeBases(response.data as unknown as KnowledgeBase[]);
            } else {
                console.error('Failed to load knowledge bases:', response.error);
                setKnowledgeBases([]);
            }
        } catch (err) {
            console.error('Error loading knowledge bases:', err);
            setKnowledgeBases([]);
        }
    }, []);

    const loadUserPreferences = useCallback(async () => {
        try {
            const response = await directApi.getUserPreferences();
            if (response.success && response.data) {
                setSessionSettings(prev => ({ ...prev, ...(response.data as any)?.preferences }));
            } else {
                console.error('Failed to load user preferences:', response.error);
            }
        } catch (err) {
            console.error('Error loading user preferences:', err);
        }
    }, []);

    // Effects
    useEffect(() => {
        if (!apiKey) {
            return;
        }
        loadAgents();
        loadSessions();
        loadKnowledgeBases();
        loadUserPreferences();
    }, [apiKey, loadAgents, loadSessions, loadKnowledgeBases, loadUserPreferences]);

    useEffect(() => {
        if (sidebarOpen && isMobile && drawerPaperRef.current) {
            drawerPaperRef.current.focus();
        }
    }, [sidebarOpen, isMobile]);

    useEffect(() => {
        if (!apiKey) {
            return;
        }

        let cancelled = false;

        const fetchProviders = async () => {
            setProvidersLoading(true);
            try {
                // Check cache first
                const cachedProviders = providersCache.get('providers');
                if (cachedProviders) {
                    setAvailableProviders(cachedProviders);
                    setProvidersLoading(false);
                    return;
                }

                const providersList = await anyllm.getProviders();
                if (cancelled) return;

                if (providersList.length) {
                    setAvailableProviders(providersList);
                    // Cache the providers
                    providersCache.set('providers', providersList);
                } else {
                    setAvailableProviders(DEFAULT_PROVIDERS);
                    providersCache.set('providers', DEFAULT_PROVIDERS);
                }

                // Only switch provider if we don't have a valid one already
                const currentProviderExists = providersList.some((provider) => provider.name === modelConfig.provider);
                if (!currentProviderExists && providersList.length > 0) {
                    const firstProvider = providersList[0].name;
                    setModelConfig(prev => ({ ...prev, provider: firstProvider }));
                }
            } catch (err) {
                if (cancelled) return;
                console.error('Failed to load AnyLLM providers', err);
                setAvailableProviders(DEFAULT_PROVIDERS);
                providersCache.set('providers', DEFAULT_PROVIDERS);
            } finally {
                if (!cancelled) {
                    setProvidersLoading(false);
                }
            }
        };

        fetchProviders();

        return () => {
            cancelled = true;
        };
    }, [apiKey]); // Removed modelConfig.provider dependency to prevent cascade

    useEffect(() => {
        if (exportMenuAnchor && !document.body.contains(exportMenuAnchor)) {
            setExportMenuAnchor(null);
        }
    }, [exportMenuAnchor]);

    useEffect(() => {
        if (settingsMenuAnchor && !document.body.contains(settingsMenuAnchor)) {
            setSettingsMenuAnchor(null);
        }
    }, [settingsMenuAnchor]);

    useEffect(() => {
        if (!selectedAgent || !currentSession) {
            if (exportMenuAnchor) {
                setExportMenuAnchor(null);
            }
            // Don't auto-close settings menu - user should be able to access settings even without an active agent/session
            // if (settingsMenuAnchor) {
            //     setSettingsMenuAnchor(null);
            // }
        }
    }, [selectedAgent, currentSession, exportMenuAnchor]);

    useEffect(() => {
        if (!availableProviders.length) {
            return;
        }

        const providerExists = availableProviders.some((provider) => provider.name === modelConfig.provider);
        if (!providerExists) {
            const fallbackProvider = availableProviders[0]?.name || 'openai';
            if (fallbackProvider !== modelConfig.provider) {
                setModelConfig((prev) => ({ ...prev, provider: fallbackProvider }));
                setSessionSettings((prev) => ({ ...prev, provider: fallbackProvider }));
            }
        }
    }, [availableProviders, modelConfig.provider, setSessionSettings]);

    useEffect(() => {
        if (!apiKey || !modelConfig.provider) {
            return;
        }

        let cancelled = false;

        const fetchModels = async () => {
            setModelsLoading(true);
            setModelsError(null);

            try {
                // Check cache first
                const cacheKey = `models_${modelConfig.provider}`;
                const cachedModels = modelsCache.get(cacheKey);
                if (cachedModels) {
                    setAvailableModels(cachedModels);
                    setModelsLoading(false);
                    return;
                }

                const modelsList = await anyllm.getModels(modelConfig.provider);
                if (cancelled) return;

                let normalizedModels = modelsList.length ? modelsList : DEFAULT_MODELS;
                if (!modelsList.length) {
                    setModelsError('No models available for this provider. Showing defaults.');
                }

                if (modelConfig.provider === 'openai' && !normalizedModels.some((model) => model.id === 'gpt-5-mini')) {
                    normalizedModels = [{ id: 'gpt-5-mini', object: 'model' }, ...normalizedModels];
                }

                setAvailableModels(normalizedModels);
                // Cache the models
                modelsCache.set(cacheKey, normalizedModels);

                const currentModel = modelConfig.model;
                const validModels = normalizedModels.map((model) => model.id);
                if (!validModels.includes(currentModel)) {
                    const fallbackModel = validModels[0] || currentModel;
                    if (fallbackModel !== currentModel) {
                        setModelConfig((prev) => ({ ...prev, model: fallbackModel }));
                        setSessionSettings((prev) => ({ ...prev, model: fallbackModel }));
                    }
                }

                // Load saved default model or use first available
                if (normalizedModels.length > 0 && !validModels.includes(currentModel)) {
                    // Set to first model if current model is invalid
                    const firstModel = normalizedModels[0].id;
                    setModelConfig((prev) => ({ ...prev, model: firstModel }));
                    setSessionSettings((prev) => ({ ...prev, model: firstModel }));
                }
            } catch (err) {
                if (cancelled) return;
                console.error('Failed to load AnyLLM models', err);
                setModelsError('Failed to load models for this provider. Using defaults.');
                let fallbackModels = DEFAULT_MODELS;
                if (modelConfig.provider === 'openai' && !fallbackModels.some((model) => model.id === 'gpt-5-mini')) {
                    fallbackModels = [{ id: 'gpt-5-mini', object: 'model' }, ...fallbackModels];
                }
                setAvailableModels(fallbackModels);
                modelsCache.set(`models_${modelConfig.provider}`, fallbackModels);
                const fallbackModel = fallbackModels[0]?.id || modelConfig.model;
                if (fallbackModel !== modelConfig.model) {
                    setModelConfig((prev) => ({ ...prev, model: fallbackModel }));
                    setSessionSettings((prev) => ({ ...prev, model: fallbackModel }));
                }
            } finally {
                if (!cancelled) {
                    setModelsLoading(false);
                }
            }
        };

        // Debounce the API call to prevent excessive requests
        const timeoutId = setTimeout(fetchModels, 300);

        return () => {
            cancelled = true;
            clearTimeout(timeoutId);
        };
    }, [apiKey, modelConfig.provider, modelConfig.model]);

    const handleProviderChange = useCallback((providerName: string) => {
        setModelConfig((prev) => ({ ...prev, provider: providerName }));
        setSessionSettings((prev) => ({ ...prev, provider: providerName }));
    }, []);

    const handleModelChange = useCallback((modelId: string) => {
        setModelConfig((prev) => ({ ...prev, model: modelId }));
        setSessionSettings((prev) => ({ ...prev, model: modelId }));
    }, []);

    // Utility Functions
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const showNotification = useCallback((message: string, severity: 'success' | 'error' | 'warning' | 'info' = 'info') => {
        setNotification({ open: true, message, severity });
    }, []);

    // Define saveSession early so it can be used in useEffect keyboard shortcuts
    const saveSession = useCallback(async () => {
        if (!currentSession) return;

        try {
            const response = await directApi.updateAgentSession(currentSession.session_id, {
                messages,
                settings: { ...sessionSettings, provider: modelConfig.provider, model: modelConfig.model },
                metadata: {
                    total_messages: messages.length,
                    total_tokens: messages.reduce((sum, msg) => sum + (msg.tokens || 0), 0),
                    last_updated: new Date().toISOString(),
                },
            });

            if (!response.success) {
                throw new Error(response.error || 'Failed to save session');
            }

            showNotification('Session saved successfully', 'success');
        } catch (err) {
            console.error('Error saving session:', err);
            showNotification('Failed to save session', 'error');
        }
    }, [currentSession, messages, sessionSettings, modelConfig.provider, modelConfig.model, showNotification]);

    const enhanceMessageContent = useCallback((content: string) => {
        if (!content) return '';

        let formatted = content.replace(/\r\n/g, '\n').trim();

        formatted = formatted.replace(/^([a-z0-9_]+\(.*?\))/i, (match) => `\`${match}\``);
        formatted = formatted.replace(/Here are some of the ([^:]+):\s*/i, 'Here are some of the $1:\n\n');

        if (formatted.includes(' - ')) {
            formatted = formatted.replace(/([.!?])\s+(?=[A-Z][^:\n]+ - )/g, '$1\n');
            formatted = formatted.replace(/(^|\n)(?!- )([A-Z][^:\n]+ - )/g, (_match, prefix, item) => `${prefix}- ${item}`);
        }

        formatted = formatted.replace(/\n{3,}/g, '\n\n');
        return formatted.trim();
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamingResponse]);

    useEffect(() => {
        if (!currentSession) {
            return;
        }

        const sessionProvider = currentSession.provider || modelConfig.provider;
        const sessionModel = currentSession.model_id || modelConfig.model;

        setModelConfig((prev) => ({
            ...prev,
            provider: sessionProvider,
            model: sessionModel,
        }));

        setSessionSettings((prev) => ({
            ...prev,
            ...(currentSession.settings || {}),
            provider: sessionProvider,
            model: sessionModel,
        }));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentSession]);

    useEffect(() => {
        const handleKeyboardShortcuts = (e: KeyboardEvent) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'k':
                        e.preventDefault();
                        setSidebarOpen(!sidebarOpen);
                        break;
                    case 's':
                        e.preventDefault();
                        if (currentSession) {
                            saveSession();
                        }
                        break;
                    case 'i':
                        e.preventDefault();
                        setShowImportDialog(true);
                        break;
                    case '/':
                        e.preventDefault();
                        document.getElementById('message-input')?.focus();
                        break;
                    case 'f':
                        e.preventDefault();
                        document.getElementById('search-input')?.focus();
                        break;
                }
            }
        };

        window.addEventListener('keydown', handleKeyboardShortcuts);
        return () => window.removeEventListener('keydown', handleKeyboardShortcuts);
    }, [sidebarOpen, currentSession, saveSession]);

    const handleToggleTool = useCallback((toolName: string, enabled: boolean) => {
        showNotification(`${toolName} ${enabled ? 'enabled' : 'disabled'}`, 'success');
    }, [showNotification]);

    const closeNotification = () => {
        setNotification(prev => ({ ...prev, open: false }));
    };

    // Data Loading Functions
    const createSession = async (agent: Agent) => {
        try {
            setLoading(true);
            const response = await directApi.createAgentSession({
                agent_type: agent.id,
                model_id: modelConfig.model,
                provider: modelConfig.provider,
                settings: { ...sessionSettings, provider: modelConfig.provider, model: modelConfig.model },
                title: `Chat with ${agent.name}`,
                description: agent.description,
                metadata: {
                    tags: agent.capabilities || [],
                },
            });

            if (!response.success || !response.data) {
                throw new Error(response.error || 'Failed to create session');
            }

            const session = response.data as unknown as Session;
            setCurrentSession(session);
            setSelectedAgent(agents.find(a => a.id === session.agent_type) || null);
            setMessages([]);
            setSelectedAgent(agent);
            setActiveView('sessions');
            showNotification(`Started new session with ${agent.name}`, 'success');

            loadSessions();
        } catch (err) {
            setError('Failed to create session');
            console.error('Error creating session:', err);
            showNotification('Failed to create session', 'error');
        } finally {
            setLoading(false);
        }
    };

    const saveUserPreferences = async () => {
        try {
            const response = await directApi.updateUserPreferences({ preferences: { ...sessionSettings, provider: modelConfig.provider, model: modelConfig.model } });

            if (!response.success) {
                throw new Error(response.error || 'Failed to save preferences');
            }

            showNotification('Preferences saved', 'success');
        } catch (err) {
            console.error('Error saving preferences:', err);
            showNotification('Failed to save preferences', 'error');
        }
    };

    const handleSaveSettings = async () => {
        await saveUserPreferences();
        if (currentSession) {
            await saveSession();
        }
        setShowSettingsDialog(false);
    };

    const deleteSession = async (sessionId: string) => {
        try {
            const response = await directApi.deleteAgentSession(sessionId);

            if (!response.success) {
                throw new Error(response.error || 'Failed to delete session');
            }

            loadSessions();

            if (currentSession?.session_id === sessionId) {
                setCurrentSession(null);
                setMessages([]);
                setSelectedAgent(null);
            }

            showNotification('Session deleted successfully', 'success');
        } catch (err) {
            console.error('Error deleting session:', err);
            showNotification('Failed to delete session', 'error');
        }
    };

    const loadSession = async (session: Session, showToast: boolean = true) => {
        setCurrentSession(session);
        setSelectedAgent(agents.find(a => a.id === session.agent_type) || null);
        setActiveView('sessions');
        try {
            const response = await directApi.getAgentSessionHistory(session.session_id);
            if (response.success && response.data) {
                setMessages((response.data as any).messages || []);
            } else {
                setMessages([]);
            }
        } catch (err) {
            console.error('Error loading session history:', err);
            setMessages([]);
        }
        if (showToast) {
            showNotification(`Loaded session: ${session.title}`, 'success');
        }
    };

    const exportSession = async (format: 'json' | 'markdown' | 'txt' | 'csv') => {
        if (!currentSession) return;

        try {
            const response = await directApi.exportAgentSession(currentSession.session_id, format);

            if (!response.success || !response.data) {
                throw new Error(response.error || 'Failed to export session');
            }

            const blob = new Blob([JSON.stringify(response.data)], { type: 'application/octet-stream' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `session_${currentSession.session_id}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            showNotification(`Session exported as ${format.toUpperCase()}`, 'success');
        } catch (err) {
            console.error('Error exporting session:', err);
            showNotification('Failed to export session', 'error');
        }
    };

    const importSession = async (file: File) => {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await directApi.importAgentSessions(formData);

            if (!response.success || !response.data) {
                throw new Error(response.error || 'Failed to import session');
            }

            const session = response.data as unknown as Session;
            await loadSession(session, false);
            showNotification('Session imported successfully', 'success');
            setShowImportDialog(false);
            loadSessions();
        } catch (err) {
            console.error('Error importing session:', err);
            showNotification('Failed to import session', 'error');
        }
    };

    // Chat Functions
    const sendMessage = async () => {
        if (!inputMessage.trim() || !currentSession) return;

        const userMessage: Message = {
            id: `msg_${Date.now()}`,
            role: 'user',
            content: inputMessage.trim(),
            timestamp: new Date().toISOString(),
            tokens: calculateTokens(inputMessage.trim()),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setError('');
        setStreamingResponse('');
        setLoading(true);

        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const payload = {
                message: inputMessage.trim(),
                stream: modelConfig.stream,
                settings: {
                    ...modelConfig,
                    memory_enabled: memorySettings.short_term_enabled,
                    knowledge_base_enabled: sessionSettings.knowledge_base_enabled,
                    reasoning_enabled: sessionSettings.reasoning_enabled,
                },
            };

            const headers: Record<string, string> = {
                'Content-Type': 'application/json',
            };

            if (apiKey) {
                headers['X-API-Key'] = apiKey;
            }

            if (modelConfig.stream) {
                headers['Accept'] = 'text/event-stream';
            }

            const response = await fetch(`/api/v1/agents/sessions/${currentSession.session_id}/chat`, {
                method: 'POST',
                headers,
                body: JSON.stringify(payload),
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error(`Failed to send message: ${response.status} ${response.statusText}`);
            }

            if (modelConfig.stream && response.body) {
                const reader = response.body.getReader();
                if (!reader) {
                    throw new Error('No response stream');
                }

                const decoder = new TextDecoder();
                let assistantMessage = '';
                const messageId = `msg_${Date.now()}`;
                const startTime = new Date().toISOString();

                try {
                    let continueReading = true;
                    while (continueReading) {
                        const { done, value } = await reader.read();
                        if (done) {
                            continueReading = false;
                            break;
                        }

                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') {
                                    if (assistantMessage) {
                                        const msg: Message = {
                                            id: messageId,
                                            role: 'assistant',
                                            content: assistantMessage,
                                            timestamp: startTime,
                                            tokens: calculateTokens(assistantMessage),
                                            model: modelConfig.model,
                                            temperature: modelConfig.temperature,
                                            metadata: {
                                                model: modelConfig.model,
                                                temperature: modelConfig.temperature,
                                                top_p: modelConfig.top_p,
                                                top_k: modelConfig.top_k,
                                                max_tokens: modelConfig.max_tokens,
                                                tokens_used: calculateTokens(assistantMessage),
                                                cost: parseFloat(calculateCost(calculateTokens(assistantMessage), modelConfig.model)),
                                                latency: Date.now() - new Date(startTime).getTime(),
                                                tools_used: [],
                                                reasoning_time: 0,
                                                memory_used: memorySettings.short_term_enabled ? 'enabled' : 'disabled',
                                                knowledge_base_used: sessionSettings.knowledge_base_enabled,
                                            },
                                        };
                                        setMessages(prev => [...prev, msg]);
                                    }
                                    setStreamingResponse('');
                                    continueReading = false;
                                    break;
                                }

                                try {
                                    const parsed = JSON.parse(data);
                                    if (parsed.content) {
                                        assistantMessage += parsed.content;
                                        setStreamingResponse(assistantMessage);
                                    }
                                    if (parsed.tool_calls) {
                                        setToolEvents(prev => [...prev, ...parsed.tool_calls]);
                                    }
                                    if (parsed.metadata) {
                                        // Update metadata if needed
                                    }
                                } catch (parseError) {
                                    // Handle non-JSON data or malformed JSON
                                    console.warn('Failed to parse streaming data:', parseError, data);
                                    assistantMessage += data;
                                    setStreamingResponse(assistantMessage);
                                }
                            }
                        }
                    }
                } catch (streamError: unknown) {
                    // Handle stream reading errors (e.g., network issues, aborted requests)
                    if (streamError instanceof Error && streamError.name === 'AbortError') {
                        setStreamingResponse('');
                        return;
                    }
                    console.error('Error reading from stream:', streamError);
                    // Continue with partial message if we have content
                    if (assistantMessage) {
                        const msg: Message = {
                            id: messageId,
                            role: 'assistant',
                            content: assistantMessage,
                            timestamp: startTime,
                            tokens: calculateTokens(assistantMessage),
                            model: modelConfig.model,
                            temperature: modelConfig.temperature,
                            metadata: {
                                model: modelConfig.model,
                                temperature: modelConfig.temperature,
                                top_p: modelConfig.top_p,
                                top_k: modelConfig.top_k,
                                max_tokens: modelConfig.max_tokens,
                                tokens_used: calculateTokens(assistantMessage),
                                cost: parseFloat(calculateCost(calculateTokens(assistantMessage), modelConfig.model)),
                                latency: Date.now() - new Date(startTime).getTime(),
                                tools_used: [],
                                reasoning_time: 0,
                                memory_used: memorySettings.short_term_enabled ? 'enabled' : 'disabled',
                                knowledge_base_used: sessionSettings.knowledge_base_enabled,
                            },
                        };
                        setMessages(prev => [...prev, msg]);
                    }
                    setStreamingResponse('');
                } finally {
                    // Ensure reader is properly closed
                    try {
                        reader.releaseLock();
                    } catch {
                        // Ignore errors when releasing lock
                    }
                }
            } else {
                const data = await response.json();
                const assistantMessage: Message = {
                    id: `msg_${Date.now()}`,
                    role: 'assistant',
                    content: data.content,
                    timestamp: new Date().toISOString(),
                    tokens: calculateTokens(data.content),
                    model: modelConfig.model,
                    temperature: modelConfig.temperature,
                    tool_calls: data.tool_calls || [],
                    metadata: {
                        model: modelConfig.model,
                        temperature: modelConfig.temperature,
                        top_p: modelConfig.top_p,
                        top_k: modelConfig.top_k,
                        max_tokens: modelConfig.max_tokens,
                        tokens_used: calculateTokens(data.content),
                        cost: parseFloat(calculateCost(calculateTokens(data.content), modelConfig.model)),
                        latency: data.metadata?.latency || 0,
                        tools_used: data.tool_calls?.map((tc: { name: string }) => tc.name) || [],
                        reasoning_time: data.metadata?.reasoning_time || 0,
                        memory_used: memorySettings.short_term_enabled ? 'enabled' : 'disabled',
                        knowledge_base_used: sessionSettings.knowledge_base_enabled,
                    },
                };
                setMessages(prev => [...prev, assistantMessage]);
            }

            // Auto-save session if enabled
            if (sessionSettings.auto_save) {
                setTimeout(saveSession, 1000);
            }
        } catch (err: unknown) {
            if (err instanceof Error && err.name === 'AbortError') {
                return;
            }
            setError('Failed to send message');
            console.error('Error sending message:', err);
            showNotification('Failed to send message', 'error');
        } finally {
            setLoading(false);
            abortControllerRef.current = null;
        }
    };

    const stopStreaming = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setLoading(false);
        showNotification('Response stopped', 'info');
    };

    const regenerateResponse = async (messageId: string) => {
        const messageIndex = messages.findIndex(msg => msg.id === messageId);
        if (messageIndex === -1) return;

        const userMessage = messages[messageIndex - 1];
        if (!userMessage || userMessage.role !== 'user') return;

        // Remove the current assistant response
        setMessages(prev => prev.slice(0, messageIndex));

        // Resend the user message
        setInputMessage(userMessage.content);
        setTimeout(sendMessage, 100);
    };

    // Knowledge Base Functions
    const uploadDocument = async (file: File) => {
        if (!selectedKnowledgeBase) {
            showNotification('Please select a knowledge base first', 'warning');
            return;
        }

        setUploadingDocument(true);
        setUploadProgress(0);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('knowledge_base_id', selectedKnowledgeBase.id);

            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const progress = (e.loaded / e.total) * 100;
                    setUploadProgress(progress);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    showNotification('Document uploaded successfully', 'success');
                    loadKnowledgeBases();
                } else {
                    showNotification('Failed to upload document', 'error');
                }
                setUploadingDocument(false);
                setUploadProgress(0);
            });

            xhr.addEventListener('error', () => {
                showNotification('Failed to upload document', 'error');
                setUploadingDocument(false);
                setUploadProgress(0);
            });

            xhr.open('POST', `/api/v1/agents/knowledge-bases/${selectedKnowledgeBase.id}/documents`);
            xhr.setRequestHeader('X-API-Key', apiKey || '');
            xhr.send(formData);
        } catch (err) {
            console.error('Error uploading document:', err);
            showNotification('Failed to upload document', 'error');
            setUploadingDocument(false);
            setUploadProgress(0);
        }
    };

    // Voice Functions
    const startRecording = async () => {
        try {
            // Check if media devices are supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Media devices not supported in this browser');
            }

            // Check for available audio devices
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioDevices = devices.filter(device => device.kind === 'audioinput');

            if (audioDevices.length === 0) {
                throw new Error('No microphone found. Please connect a microphone and try again.');
            }

            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.addEventListener('dataavailable', (e) => {
                audioChunksRef.current.push(e.data);
            });

            mediaRecorder.addEventListener('stop', async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('audio', audioBlob);

                try {
                    const response = await directApi.agentSpeechToText(formData);

                    if (response.success && response.data) {
                        setInputMessage(prev => prev + (prev ? ' ' : '') + (response.data as any).text);
                        showNotification('Voice input processed', 'success');
                    } else {
                        showNotification(response.error || 'Failed to process voice input', 'error');
                    }
                } catch (err) {
                    console.error('Error processing voice input:', err);
                    showNotification('Failed to process voice input', 'error');
                }

                stream.getTracks().forEach(track => track.stop());
            });

            mediaRecorder.start();
            setIsRecording(true);
            showNotification('Recording started', 'info');
        } catch (err) {
            console.error('Error starting recording:', err);

            let errorMessage = 'Failed to start recording';

            if (err instanceof Error) {
                if (err.name === 'NotFoundError') {
                    errorMessage = 'No microphone found. Please connect a microphone and try again.';
                } else if (err.name === 'NotAllowedError') {
                    errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
                } else if (err.name === 'NotReadableError') {
                    errorMessage = 'Microphone is already in use by another application.';
                } else if (err.name === 'OverconstrainedError') {
                    errorMessage = 'Microphone does not meet the required constraints.';
                } else if (err.message.includes('Media devices not supported')) {
                    errorMessage = 'Voice recording is not supported in this browser.';
                } else {
                    errorMessage = err.message;
                }
            }

            showNotification(errorMessage, 'error');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            showNotification('Recording stopped', 'info');
        }
    };

    const speakText = (text: string) => {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.volume = 1.0; // Default volume
            utterance.addEventListener('start', () => setIsSpeaking(true));
            utterance.addEventListener('end', () => setIsSpeaking(false));
            speechSynthesis.speak(utterance);
        }
    };

    const stopSpeaking = () => {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
            setIsSpeaking(false);
        }
    };

    // UI Helper Functions
    const getAgentIcon = (agentType: string) => {
        const iconMap: Record<string, React.ReactNode> = {
            'web_agent': <WebIcon />,
            'agno_assist': <HelpIcon />,
            'finance_agent': <FinanceIcon />,
            'research_agent': <ScienceIcon />,
            'social_media_agent': <ShareIcon />,
            'content_team': <GroupsIcon />,
            'news_agency_team': <NewsIcon />,
            'blog_generator': <BookIcon />,
        };
        return iconMap[agentType] || <BotIcon />;
    };

    const filteredAgents = agents.filter(agent => {
        const matchesSearch = agent.name.toLowerCase().includes(agentFilter.toLowerCase()) ||
            agent.description.toLowerCase().includes(agentFilter.toLowerCase()) ||
            agent.tags?.some(tag => tag.toLowerCase().includes(agentFilter.toLowerCase()));
        const matchesTab = selectedTab === 'all' || agent.type === selectedTab;
        return matchesSearch && matchesTab;
    });

    const filteredSessions = sessions.filter(session => {
        const matchesSearch = session.title?.toLowerCase().includes(sessionFilter.toLowerCase()) ||
            session.description?.toLowerCase().includes(sessionFilter.toLowerCase()) ||
            session.tags?.some(tag => tag.toLowerCase().includes(sessionFilter.toLowerCase()));
        return matchesSearch;
    });

    const sortedSessions = [...filteredSessions].sort((a, b) => {
        let aValue: string | number | Date;
        let bValue: string | number | Date;

        switch (sortBy) {
            case 'name':
                aValue = a.title?.toLowerCase() || '';
                bValue = b.title?.toLowerCase() || '';
                break;
            case 'created':
                aValue = new Date(a.created_at);
                bValue = new Date(b.created_at);
                break;
            case 'updated':
                aValue = new Date(a.updated_at || a.created_at);
                bValue = new Date(b.updated_at || b.created_at);
                break;
            case 'usage':
                aValue = a.metadata?.total_messages || 0;
                bValue = b.metadata?.total_messages || 0;
                break;
            default:
                aValue = new Date(a.created_at);
                bValue = new Date(b.created_at);
        }

        if (sortOrder === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });

    const agentCounts = {
        all: agents.length,
        agent: agents.filter(a => a.type === 'agent').length,
        team: agents.filter(a => a.type === 'team').length,
        workflow: agents.filter(a => a.type === 'workflow').length,
    };

    const sidebarWidth = isMobile ? 360 : 420;

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
            {/* Header */}
            <Box sx={{
                p: isMobile ? 1.5 : 2,
                borderBottom: '1px solid #e2e8f0',
                bgcolor: 'background.paper',
                display: 'flex',
                alignItems: 'center',
                gap: isMobile ? 1.5 : 2,
                minHeight: isMobile ? 56 : 'auto'
            }}>
                <IconButton
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    sx={{
                        mr: isMobile ? 0.5 : 1,
                        p: isMobile ? 1.5 : 1,
                        '&:hover': {
                            bgcolor: 'action.hover'
                        }
                    }}
                    size={isMobile ? 'large' : 'medium'}
                >
                    <MenuIcon sx={{ fontSize: isMobile ? '1.5rem' : '1.25rem' }} />
                </IconButton>

                <Typography
                    variant={isMobile ? 'h6' : 'h6'}
                    sx={{
                        flexGrow: 1,
                        fontWeight: 600,
                        color: 'text.primary',
                        fontSize: isMobile ? '1.1rem' : '1.25rem',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                    }}
                >
                    AI Agents 🤖
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: isMobile ? 0.5 : 1 }}>
                    {!isMobile && (
                        <Tooltip title="Search (Ctrl+F)">
                            <IconButton size="small">
                                <SearchIcon />
                            </IconButton>
                        </Tooltip>
                    )}

                    <Tooltip title="Settings">
                        <IconButton
                            size={isMobile ? 'medium' : 'small'}
                            onClick={(e) => setSettingsMenuAnchor(e.currentTarget)}
                            sx={{ p: isMobile ? 1.5 : 1 }}
                        >
                            <SettingsIcon sx={{ fontSize: isMobile ? '1.25rem' : '1rem' }} />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mx: 2, mt: 1 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}

            {/* Main Content */}
            <Box sx={{
                display: 'flex',
                flexGrow: 1,
                minHeight: 0,
                px: isMobile ? 0 : 1,
                pb: isMobile ? 0 : 2,
                position: 'relative'
            }}>
                {/* Sidebar */}
                <Drawer
                    variant={isMobile ? 'temporary' : 'persistent'}
                    anchor="left"
                    open={sidebarOpen}
                    onClose={() => setSidebarOpen(false)}
                    sx={{
                        width: sidebarWidth,
                        flexShrink: 0,
                        '& .MuiDrawer-paper': {
                            width: isMobile ? '85vw' : sidebarWidth,
                            maxWidth: isMobile ? 320 : sidebarWidth,
                            boxSizing: 'border-box',
                            borderRight: '1px solid #e2e8f0',
                            position: isMobile ? 'fixed' : 'relative',
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            boxShadow: isMobile ? 'rgba(0, 0, 0, 0.16) 0px 3px 6px, rgba(0, 0, 0, 0.23) 0px 3px 6px' : 'none',
                            zIndex: isMobile ? 1300 : 'auto',
                            ...(isMobile ? {} : { top: 'auto', left: 'auto' }),
                        },
                    }}
                    ModalProps={{
                        keepMounted: isMobile, // Better mobile performance
                    }}
                    PaperProps={{
                        ref: drawerPaperRef,
                        tabIndex: -1,
                    }}
                >
                    <Box sx={{ p: 2, borderBottom: '1px solid #e2e8f0' }}>
                        <Typography variant="h6" fontWeight="600" sx={{ mb: 2 }}>
                            Navigation
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                            <Button
                                onClick={() => {
                                    setActiveView('agents');
                                    if (isMobile) setSidebarOpen(false);
                                }}
                                variant={activeView === 'agents' ? 'contained' : 'outlined'}
                                fullWidth
                                size={isMobile ? 'medium' : 'small'}
                                sx={{
                                    minHeight: isMobile ? 44 : 'auto',
                                    fontSize: isMobile ? '1rem' : '0.875rem',
                                    py: isMobile ? 1.5 : 0.5
                                }}
                            >
                                <BotIcon sx={{ mr: 1, fontSize: isMobile ? '1.2rem' : '1rem' }} />
                                Browse Agents
                            </Button>
                            <Button
                                onClick={() => {
                                    setActiveView('sessions');
                                    if (isMobile) setSidebarOpen(false);
                                }}
                                variant={activeView === 'sessions' ? 'contained' : 'outlined'}
                                fullWidth
                                size={isMobile ? 'medium' : 'small'}
                                sx={{
                                    minHeight: isMobile ? 44 : 'auto',
                                    fontSize: isMobile ? '1rem' : '0.875rem',
                                    py: isMobile ? 1.5 : 0.5
                                }}
                            >
                                <HistoryIcon sx={{ mr: 1, fontSize: isMobile ? '1.2rem' : '1rem' }} />
                                Recent Sessions
                            </Button>
                            <Button
                                onClick={() => {
                                    setShowSettingsDialog(true);
                                    if (isMobile) setSidebarOpen(false);
                                }}
                                variant={activeView === 'settings' ? 'contained' : 'outlined'}
                                fullWidth
                                size={isMobile ? 'medium' : 'small'}
                                sx={{
                                    minHeight: isMobile ? 44 : 'auto',
                                    fontSize: isMobile ? '1rem' : '0.875rem',
                                    py: isMobile ? 1.5 : 0.5
                                }}
                            >
                                <SettingsIcon sx={{ mr: 1, fontSize: isMobile ? '1.2rem' : '1rem' }} />
                                Settings
                            </Button>
                        </Box>
                    </Box>

                    {activeView === 'agents' && (
                        <Box sx={{ p: 2, overflow: 'auto', flexGrow: 1 }}>
                            {/* Agent Filter */}
                            <TextField
                                fullWidth
                                size="small"
                                placeholder="Search agents..."
                                value={agentFilter}
                                onChange={(e) => setAgentFilter(e.target.value)}
                                InputProps={{
                                    startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                                    id: 'search-input',
                                }}
                                sx={{ mb: 2 }}
                            />

                            {/* Category Tabs */}
                            <Tabs
                                value={selectedTab}
                                onChange={(_e, newValue) => setSelectedTab(newValue)}
                                variant="scrollable"
                                scrollButtons="auto"
                                sx={{ mb: 2 }}
                            >
                                <Tab label={`All (${agentCounts.all})`} value="all" />
                                <Tab label={`Agents (${agentCounts.agent})`} value="agent" />
                                <Tab label={`Teams (${agentCounts.team})`} value="team" />
                                <Tab label={`Workflows (${agentCounts.workflow})`} value="workflow" />
                            </Tabs>

                            {/* View Mode Toggle */}
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="body2" color="text.secondary">
                                    {filteredAgents.length} agents
                                </Typography>
                                <ToggleButtonGroup
                                    size="small"
                                    value={viewMode}
                                    exclusive
                                    onChange={(_, value) => value && setViewMode(value)}
                                >
                                    <ToggleButton value="grid">
                                        <ViewModuleIcon />
                                    </ToggleButton>
                                    <ToggleButton value="list">
                                        <ViewListIcon />
                                    </ToggleButton>
                                </ToggleButtonGroup>
                            </Box>

                            {/* Agent List/Grid */}
                            {viewMode === 'list' ? (
                                <List sx={{ p: 0 }}>
                                    {filteredAgents.map((agent) => (
                                        <ListItem
                                            key={agent.id}
                                            button
                                            onClick={() => createSession(agent)}
                                            sx={{
                                                borderRadius: 2,
                                                mb: 1,
                                                border: '1px solid',
                                                borderColor: 'divider',
                                                '&:hover': {
                                                    bgcolor: alpha(theme.palette.primary.main, 0.04),
                                                },
                                            }}
                                        >
                                            <ListItemIcon>
                                                {getAgentIcon(agent.id)}
                                            </ListItemIcon>
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <span>{agent.name}</span>
                                                        {agent.is_premium && (
                                                            <StarIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                                                        )}
                                                    </Box>
                                                }
                                                secondary={
                                                    <Box>
                                                        <Typography variant="body2" color="text.secondary" component="span">
                                                            {agent.description}
                                                        </Typography>
                                                        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                                                            {agent.tags?.map((tag) => (
                                                                <Chip key={tag} label={tag} size="small" variant="outlined" />
                                                            ))}
                                                        </Box>
                                                    </Box>
                                                }
                                                primaryTypographyProps={{ component: 'div' }}
                                                secondaryTypographyProps={{ component: 'div' }}
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            ) : (
                                <Grid container spacing={2}>
                                    {filteredAgents.map((agent) => (
                                        <Grid item xs={12} sm={6} key={agent.id}>
                                            <Card
                                                sx={{
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s',
                                                    '&:hover': {
                                                        transform: 'translateY(-2px)',
                                                        boxShadow: theme.shadows[4],
                                                    },
                                                    height: '100%',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                }}
                                                onClick={() => createSession(agent)}
                                            >
                                                <CardContent sx={{ flexGrow: 1 }}>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                                        {getAgentIcon(agent.id)}
                                                        <Typography variant="h6" fontWeight="600">
                                                            {agent.name}
                                                        </Typography>
                                                        {agent.is_premium && (
                                                            <StarIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                                                        )}
                                                    </Box>
                                                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                                        {agent.description}
                                                    </Typography>
                                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                        {agent.tags?.map((tag) => (
                                                            <Chip key={tag} label={tag} size="small" variant="outlined" />
                                                        ))}
                                                    </Box>
                                                </CardContent>
                                                <CardActions>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', px: 1, pb: 1 }}>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {agent.usage_count} uses
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            ⭐ {agent.rating}
                                                        </Typography>
                                                    </Box>
                                                </CardActions>
                                            </Card>
                                        </Grid>
                                    ))}
                                </Grid>
                            )}
                        </Box>
                    )}

                    {activeView === 'sessions' && (
                        <Box sx={{ p: 2, overflow: 'auto', flexGrow: 1 }}>
                            <TextField
                                fullWidth
                                size="small"
                                placeholder="Search sessions..."
                                value={sessionFilter}
                                onChange={(e) => setSessionFilter(e.target.value)}
                                InputProps={{
                                    startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
                                }}
                                sx={{ mb: 2 }}
                            />

                            {/* Sort Controls */}
                            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                                <FormControl size="small" sx={{ flexGrow: 1 }}>
                                    <InputLabel>Sort by</InputLabel>
                                    <Select
                                        value={sortBy}
                                        onChange={(e) => setSortBy(e.target.value as 'name' | 'created' | 'updated' | 'usage')}
                                        label="Sort by"
                                    >
                                        <MenuItem value="created">Created</MenuItem>
                                        <MenuItem value="updated">Updated</MenuItem>
                                        <MenuItem value="name">Name</MenuItem>
                                        <MenuItem value="usage">Usage</MenuItem>
                                    </Select>
                                </FormControl>
                                <ToggleButtonGroup
                                    size="small"
                                    value={sortOrder}
                                    exclusive
                                    onChange={(_, value) => value && setSortOrder(value)}
                                >
                                    <ToggleButton value="asc">
                                        <SortIcon sx={{ transform: 'rotate(180deg)' }} />
                                    </ToggleButton>
                                    <ToggleButton value="desc">
                                        <SortIcon />
                                    </ToggleButton>
                                </ToggleButtonGroup>
                            </Box>

                            <List sx={{ p: 0 }}>
                                {sortedSessions.map((session) => (
                                    <ListItem
                                        key={session.session_id}
                                        button
                                        onClick={() => loadSession(session)}
                                        secondaryAction={
                                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                                                {session.pinned && (
                                                    <BookmarkIcon sx={{ color: 'warning.main' }} />
                                                )}
                                                <IconButton
                                                    edge="end"
                                                    size="small"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        deleteSession(session.session_id);
                                                    }}
                                                >
                                                    <DeleteIcon />
                                                </IconButton>
                                            </Box>
                                        }
                                        sx={{
                                            borderRadius: 2,
                                            mb: 1,
                                            border: '1px solid',
                                            borderColor: 'divider',
                                            '&:hover': {
                                                bgcolor: alpha(theme.palette.primary.main, 0.04),
                                            },
                                        }}
                                    >
                                        <ListItemIcon>
                                            {getAgentIcon(session.agent_type)}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={
                                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                    <span>{session.title}</span>
                                                    {session.tags?.map((tag) => (
                                                        <Chip key={tag} label={tag} size="small" variant="outlined" />
                                                    ))}
                                                </Box>
                                            }
                                            secondary={
                                                <Box>
                                                    <Typography variant="body2" color="text.secondary" component="span">
                                                        {session.description}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary" component="span" sx={{ display: 'block' }}>
                                                        {formatTimestamp(session.created_at)}
                                                    </Typography>
                                                </Box>
                                            }
                                            primaryTypographyProps={{ component: 'div' }}
                                            secondaryTypographyProps={{ component: 'div' }}
                                        />
                                    </ListItem>
                                ))}
                            </List>

                            <Accordion sx={{ mb: 1 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                    <Typography>Memory Settings</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={memorySettings.short_term_enabled}
                                                onChange={(e) => setMemorySettings(prev => ({ ...prev, short_term_enabled: e.target.checked }))}
                                            />
                                        }
                                        label="Short-term Memory"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={memorySettings.long_term_enabled}
                                                onChange={(e) => setMemorySettings(prev => ({ ...prev, long_term_enabled: e.target.checked }))}
                                            />
                                        }
                                        label="Long-term Memory"
                                    />
                                    <Typography variant="body2" gutterBottom sx={{ mt: 2 }}>
                                        History Runs: {memorySettings.history_runs}
                                    </Typography>
                                    <Slider
                                        value={memorySettings.history_runs}
                                        onChange={(_, value) => setMemorySettings(prev => ({ ...prev, history_runs: value as number }))}
                                        min={0}
                                        max={10}
                                        step={1}
                                        marks={[
                                            { value: 0, label: '0' },
                                            { value: 5, label: '5' },
                                            { value: 10, label: '10' },
                                        ]}
                                    />
                                </AccordionDetails>
                            </Accordion>

                            <Accordion sx={{ mb: 1 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                    <Typography>Knowledge Base</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={sessionSettings.knowledge_base_enabled}
                                                onChange={(e) => setSessionSettings(prev => ({ ...prev, knowledge_base_enabled: e.target.checked }))}
                                            />
                                        }
                                        label="Enable Knowledge Base"
                                    />
                                    <Button
                                        variant="outlined"
                                        fullWidth
                                        startIcon={<UploadIcon />}
                                        onClick={() => setShowKnowledgeDialog(true)}
                                        sx={{ mt: 2 }}
                                    >
                                        Manage Knowledge Base
                                    </Button>
                                </AccordionDetails>
                            </Accordion>

                            <Accordion sx={{ mb: 1 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                    <Typography>Advanced Features</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={sessionSettings.reasoning_enabled}
                                                onChange={(e) => setSessionSettings(prev => ({ ...prev, reasoning_enabled: e.target.checked }))}
                                            />
                                        }
                                        label="Show Reasoning"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={sessionSettings.tool_metadata_enabled}
                                                onChange={(e) => setSessionSettings(prev => ({ ...prev, tool_metadata_enabled: e.target.checked }))}
                                            />
                                        }
                                        label="Show Tool Metadata"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={showToolEvents}
                                                onChange={(e) => setShowToolEvents(e.target.checked)}
                                            />
                                        }
                                        label="Show Tool Events"
                                    />
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={sessionSettings.experimental_features}
                                                onChange={(e) => setSessionSettings(prev => ({ ...prev, experimental_features: e.target.checked }))}
                                            />
                                        }
                                        label="Experimental Features"
                                    />
                                </AccordionDetails>
                            </Accordion>
                        </Box>
                    )}
                </Drawer>

                {/* Main Chat Area */}
                <Box sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    minWidth: 0,
                    width: isMobile ? '100%' : 'auto',
                    overflow: 'hidden'
                }}>
                    {selectedAgent && currentSession ? (
                        <>
                            {/* Chat Header */}
                            <Box sx={{
                                p: { xs: 1, sm: 2 },
                                borderBottom: '1px solid #e2e8f0',
                                bgcolor: 'background.paper',
                                display: 'flex',
                                alignItems: 'center',
                                gap: { xs: 1, sm: 2 },
                            }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexGrow: 1, overflow: 'hidden' }}>
                                    {getAgentIcon(selectedAgent.id)}
                                    <Box sx={{ overflow: 'hidden' }}>
                                        <Typography variant="h6" fontWeight="600" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }} noWrap>
                                            {selectedAgent.name}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" noWrap sx={{ display: { xs: 'none', sm: 'block' } }}>
                                            {selectedAgent.description}
                                        </Typography>
                                    </Box>
                                </Box>

                                <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, sm: 1 }, flexShrink: 0 }}>
                                    <Chip
                                        label={modelConfig.model}
                                        size="small"
                                        variant="outlined"
                                        sx={{ display: { xs: 'none', md: 'flex' } }}
                                    />
                                    <Chip
                                        label={`T: ${modelConfig.temperature}`}
                                        size="small"
                                        variant="outlined"
                                        sx={{ display: { xs: 'none', md: 'flex' } }}
                                    />
                                    <Tooltip title="Save Session (Ctrl+S)">
                                        <IconButton size="small" onClick={saveSession}>
                                            <SaveIcon />
                                        </IconButton>
                                    </Tooltip>
                                    <Tooltip title="Export Session (Ctrl+E)">
                                        <IconButton size="small" onClick={(e) => setExportMenuAnchor(e.currentTarget)}>
                                            <DownloadIcon />
                                        </IconButton>
                                    </Tooltip>
                                    <Tooltip title="Session Settings">
                                        <IconButton size="small" onClick={() => setShowSettingsDialog(true)}>
                                            <TuneIcon />
                                        </IconButton>
                                    </Tooltip>
                                </Box>
                            </Box>

                            {/* Messages Area */}
                            <Box sx={{
                                flexGrow: 1,
                                overflow: 'auto',
                                p: { xs: 1, sm: 2 },
                                display: 'flex',
                                flexDirection: 'column',
                                gap: { xs: 1.5, sm: 2 },
                            }}>
                                {messages.length === 0 && !streamingResponse ? (
                                    <Box
                                        sx={{
                                            display: 'flex',
                                            flexDirection: 'column',
                                            justifyContent: 'center',
                                            alignItems: 'center',
                                            height: '100%',
                                            textAlign: 'center',
                                            gap: 2,
                                        }}
                                    >
                                        <AIIcon sx={{ fontSize: { xs: 48, sm: 64, md: 80 }, color: 'primary.main' }} />
                                        <Box>
                                            <Typography variant="h6" color="text.primary" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                                                Start a conversation with {selectedAgent.name}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                Ask me anything! I'm here to help.
                                            </Typography>
                                        </Box>
                                        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                                            <Button variant="outlined" size="small">
                                                <HelpIcon sx={{ mr: 1 }} />
                                                View Capabilities
                                            </Button>
                                            <Button variant="outlined" size="small">
                                                <HistoryIcon sx={{ mr: 1 }} />
                                                View Examples
                                            </Button>
                                        </Box>
                                    </Box>
                                ) : (
                                    <>
                                        {messages.map((message, index) => (
                                            <Box
                                                key={message.id || index}
                                                sx={{
                                                    display: 'flex',
                                                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                                                    gap: 1,
                                                }}
                                            >
                                                {message.role === 'assistant' && (
                                                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                                                        {getAgentIcon(selectedAgent.id)}
                                                    </Avatar>
                                                )}
                                                <Box sx={{ maxWidth: { xs: '90%', sm: '80%', md: '70%' } }}>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5, flexWrap: 'wrap' }}>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {message.role === 'user' ? 'You' : selectedAgent.name}
                                                        </Typography>
                                                        {message.timestamp && (
                                                            <Typography variant="caption" color="text.secondary">
                                                                {formatTimestamp(message.timestamp)}
                                                            </Typography>
                                                        )}
                                                        {message.tokens && (
                                                            <Chip
                                                                label={`${message.tokens} tokens`}
                                                                size="small"
                                                                variant="outlined"
                                                                sx={{ display: { xs: 'none', sm: 'flex' } }}
                                                            />
                                                        )}
                                                        <Box sx={{ ml: 'auto' }}>
                                                            {message.role === 'assistant' && (
                                                                <>
                                                                    <Tooltip title="Regenerate">
                                                                        <IconButton size="small" onClick={() => regenerateResponse(message.id || index.toString())}>
                                                                            <RefreshIcon />
                                                                        </IconButton>
                                                                    </Tooltip>
                                                                    <Tooltip title="Copy">
                                                                        <IconButton size="small">
                                                                            <ContentCopyIcon />
                                                                        </IconButton>
                                                                    </Tooltip>
                                                                    {message.metadata?.cost && (
                                                                        <Typography variant="caption" color="text.secondary">
                                                                            ${message.metadata.cost}
                                                                        </Typography>
                                                                    )}
                                                                </>
                                                            )}
                                                        </Box>
                                                    </Box>
                                                    <Paper
                                                        elevation={1}
                                                        sx={{
                                                            p: 2,
                                                            background: message.role === 'user'
                                                                ? `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`
                                                                : alpha(theme.palette.background.paper, 0.9),
                                                            color: message.role === 'user' ? 'white' : 'text.primary',
                                                            borderRadius: message.role === 'user' ? '20px 20px 6px 20px' : '20px 20px 20px 6px',
                                                            position: 'relative',
                                                        }}
                                                    >
                                                        {message.reasoning && sessionSettings.reasoning_enabled && (
                                                            <Box sx={{ mb: 1, p: 1, bgcolor: alpha(theme.palette.info.main, 0.1), borderRadius: 1 }}>
                                                                <Typography variant="caption" color="info.main">
                                                                    <AIIcon sx={{ fontSize: 14, mr: 0.5 }} />
                                                                    Reasoning:
                                                                </Typography>
                                                                <Typography variant="body2" sx={{ mt: 0.5 }}>
                                                                    {message.reasoning}
                                                                </Typography>
                                                            </Box>
                                                        )}
                                                        <Box sx={{ '& p': { margin: 0 }, '& p + p': { marginTop: '0.5em' } }}>
                                                            <ReactMarkdown
                                                                remarkPlugins={[remarkGfm]}
                                                                rehypePlugins={[rehypeHighlight]}
                                                                components={{
                                                                    p: ({ children }) => <Typography variant="body2" component="div">{children}</Typography>,
                                                                    h1: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                    h2: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                    h3: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                    ul: ({ children }) => <Box component="ul" sx={{ pl: 2, m: 0 }}>{children}</Box>,
                                                                    ol: ({ children }) => <Box component="ol" sx={{ pl: 2, m: 0 }}>{children}</Box>,
                                                                    li: ({ children }) => <Box component="li" sx={{ mb: 0.5 }}>{children}</Box>,
                                                                    strong: ({ children }) => <Box component="strong" sx={{ fontWeight: 'bold' }}>{children}</Box>,
                                                                    em: ({ children }) => <Box component="em" sx={{ fontStyle: 'italic' }}>{children}</Box>,
                                                                    code: ({ children }) => <Box component="code" sx={{
                                                                        bgcolor: message.role === 'user' ? 'rgba(255,255,255,0.2)' : 'grey.100',
                                                                        px: 0.5,
                                                                        py: 0.25,
                                                                        borderRadius: 0.5,
                                                                        fontFamily: 'monospace',
                                                                        fontSize: '0.875em'
                                                                    }}>{children}</Box>,
                                                                    pre: ({ children }) => <Box component="pre" sx={{
                                                                        bgcolor: message.role === 'user' ? 'rgba(255,255,255,0.2)' : 'grey.100',
                                                                        p: 1,
                                                                        borderRadius: 1,
                                                                        overflow: 'auto',
                                                                        fontSize: '0.875em'
                                                                    }}>{children}</Box>,
                                                                }}
                                                            >
                                                                {enhanceMessageContent(message.content || '')}
                                                            </ReactMarkdown>
                                                        </Box>
                                                    </Paper>
                                                    {message.tool_calls && sessionSettings.tool_metadata_enabled && (
                                                        <Box sx={{ mt: 1 }}>
                                                            {message.tool_calls.map((toolCall) => (
                                                                <Paper
                                                                    key={toolCall.id}
                                                                    sx={{
                                                                        p: 1,
                                                                        bgcolor: alpha(theme.palette.info.main, 0.1),
                                                                        borderRadius: 1,
                                                                        mt: 0.5,
                                                                    }}
                                                                >
                                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                                                        <IntegrationIcon sx={{ fontSize: 16 }} />
                                                                        <Typography variant="caption" fontWeight="600">
                                                                            {toolCall.name}
                                                                        </Typography>
                                                                        {toolCall.duration && (
                                                                            <Typography variant="caption" color="text.secondary">
                                                                                ({toolCall.duration}ms)
                                                                            </Typography>
                                                                        )}
                                                                        <Chip
                                                                            label={toolCall.status || 'completed'}
                                                                            size="small"
                                                                            color={toolCall.status === 'failed' ? 'error' : 'success'}
                                                                        />
                                                                    </Box>
                                                                    {toolCall.result && (
                                                                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                                                                            {typeof toolCall.result === 'string'
                                                                                ? toolCall.result.slice(0, 200) + (toolCall.result.length > 200 ? '...' : '')
                                                                                : JSON.stringify(toolCall.result).slice(0, 200) + '...'
                                                                            }
                                                                        </Typography>
                                                                    )}
                                                                </Paper>
                                                            ))}
                                                        </Box>
                                                    )}
                                                </Box>
                                                {message.role === 'user' && (
                                                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                                                        <AccountIcon />
                                                    </Avatar>
                                                )}
                                            </Box>
                                        ))}
                                        {streamingResponse && (
                                            <Box sx={{ display: 'flex', justifyContent: 'flex-start', gap: 1 }}>
                                                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                                                    {getAgentIcon(selectedAgent.id)}
                                                </Avatar>
                                                <Box sx={{ maxWidth: { xs: '90%', sm: '80%', md: '70%' } }}>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {selectedAgent.name}
                                                        </Typography>
                                                        <CircularProgress size={12} />
                                                        <Typography variant="caption" color="text.secondary">
                                                            Typing...
                                                        </Typography>
                                                    </Box>
                                                    <Paper
                                                        elevation={1}
                                                        sx={{
                                                            p: 2,
                                                            background: alpha(theme.palette.background.paper, 0.9),
                                                            borderRadius: '20px 20px 20px 6px',
                                                        }}
                                                    >
                                                        <Box sx={{ '& p': { margin: 0 }, '& p + p': { marginTop: '0.5em' } }}>
                                                            <ReactMarkdown
                                                                remarkPlugins={[remarkGfm]}
                                                                rehypePlugins={[rehypeHighlight]}
                                                                components={{
                                                                    p: ({ children }) => <Typography variant="body2" component="div">{children}</Typography>,
                                                                    h1: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                    h2: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                    h3: ({ children }) => <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>{children}</Typography>,
                                                                    ul: ({ children }) => <Box component="ul" sx={{ pl: 2, m: 0 }}>{children}</Box>,
                                                                    ol: ({ children }) => <Box component="ol" sx={{ pl: 2, m: 0 }}>{children}</Box>,
                                                                    li: ({ children }) => <Box component="li" sx={{ mb: 0.5 }}>{children}</Box>,
                                                                    strong: ({ children }) => <Box component="strong" sx={{ fontWeight: 'bold' }}>{children}</Box>,
                                                                    em: ({ children }) => <Box component="em" sx={{ fontStyle: 'italic' }}>{children}</Box>,
                                                                    code: ({ children }) => <Box component="code" sx={{
                                                                        bgcolor: 'grey.100',
                                                                        px: 0.5,
                                                                        py: 0.25,
                                                                        borderRadius: 0.5,
                                                                        fontFamily: 'monospace',
                                                                        fontSize: '0.875em'
                                                                    }}>{children}</Box>,
                                                                    pre: ({ children }) => <Box component="pre" sx={{
                                                                        bgcolor: 'grey.100',
                                                                        p: 1,
                                                                        borderRadius: 1,
                                                                        overflow: 'auto',
                                                                        fontSize: '0.875em'
                                                                    }}>{children}</Box>,
                                                                }}
                                                            >
                                                                {enhanceMessageContent(streamingResponse)}
                                                            </ReactMarkdown>
                                                        </Box>
                                                    </Paper>
                                                </Box>
                                            </Box>
                                        )}
                                        {toolEvents.length > 0 && showToolEvents && (
                                            <Box sx={{ mt: 2, p: 2, bgcolor: alpha(theme.palette.info.main, 0.1), borderRadius: 2 }}>
                                                <Typography variant="subtitle2" gutterBottom>
                                                    <IntegrationIcon sx={{ fontSize: 16, mr: 0.5 }} />
                                                    Tool Events
                                                </Typography>
                                                {toolEvents.map((toolCall, index) => (
                                                    <Box key={index} sx={{ mb: 1 }}>
                                                        <Typography variant="body2" fontWeight="600">
                                                            {toolCall.name}
                                                        </Typography>
                                                        {toolCall.duration && (
                                                            <Typography variant="caption" color="text.secondary">
                                                                Duration: {toolCall.duration}ms
                                                            </Typography>
                                                        )}
                                                        {toolCall.result && (
                                                            <Typography variant="body2" sx={{ mt: 0.5 }}>
                                                                {typeof toolCall.result === 'string'
                                                                    ? toolCall.result.slice(0, 100) + (toolCall.result.length > 100 ? '...' : '')
                                                                    : JSON.stringify(toolCall.result).slice(0, 100) + '...'
                                                                }
                                                            </Typography>
                                                        )}
                                                    </Box>
                                                ))}
                                            </Box>
                                        )}
                                        <div ref={messagesEndRef} />
                                    </>
                                )}
                            </Box>

                            {/* Input Area */}
                            <Box sx={{
                                p: { xs: 1, sm: 2 },
                                borderTop: '1px solid #e2e8f0',
                                bgcolor: 'background.paper',
                            }}>
                                <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                                    <TextField
                                        fullWidth
                                        multiline
                                        maxRows={6}
                                        value={inputMessage}
                                        onChange={(e) => setInputMessage(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                sendMessage();
                                            }
                                        }}
                                        placeholder={`Ask ${selectedAgent.name} anything... (Ctrl+/ to focus)`}
                                        disabled={loading}
                                        variant="outlined"
                                        size="small"
                                        id="message-input"
                                        InputProps={{
                                            startAdornment: (
                                                <InputAdornment position="start">
                                                    <input
                                                        type="file"
                                                        ref={fileInputRef}
                                                        style={{ display: 'none' }}
                                                        onChange={(e) => {
                                                            const file = e.target.files?.[0];
                                                            if (file) {
                                                                // Handle file upload
                                                                showNotification(`File ${file.name} uploaded`, 'success');
                                                            }
                                                        }}
                                                    />
                                                    <Tooltip title="Upload file">
                                                        <IconButton size="small" onClick={() => fileInputRef.current?.click()}>
                                                            <UploadIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                </InputAdornment>
                                            ),
                                            endAdornment: (
                                                <InputAdornment position="end">
                                                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                                                        {sessionSettings.voice_input && (
                                                            <Tooltip title={isRecording ? "Stop recording" : "Start recording"}>
                                                                <IconButton
                                                                    size="small"
                                                                    onClick={isRecording ? stopRecording : startRecording}
                                                                    color={isRecording ? 'error' : 'default'}
                                                                >
                                                                    {isRecording ? <MicOffIcon /> : <MicIcon />}
                                                                </IconButton>
                                                            </Tooltip>
                                                        )}
                                                        {sessionSettings.voice_output && (
                                                            <Tooltip title={isSpeaking ? "Stop speaking" : "Speak last response"}>
                                                                <IconButton
                                                                    size="small"
                                                                    onClick={isSpeaking ? stopSpeaking : () => speakText(messages[messages.length - 1]?.content || '')}
                                                                    color={isSpeaking ? 'error' : 'default'}
                                                                >
                                                                    {isSpeaking ? <VolumeOffIcon /> : <VolumeUpIcon />}
                                                                </IconButton>
                                                            </Tooltip>
                                                        )}
                                                    </Box>
                                                </InputAdornment>
                                            ),
                                        }}
                                    />
                                    {loading ? (
                                        <Tooltip title="Stop response">
                                            <IconButton onClick={stopStreaming} color="error">
                                                <StopIcon />
                                            </IconButton>
                                        </Tooltip>
                                    ) : (
                                        <Tooltip title="Send message">
                                            <span style={{ display: 'inline-flex' }}>
                                                <IconButton
                                                    onClick={sendMessage}
                                                    disabled={!inputMessage.trim() || loading}
                                                    color="primary"
                                                >
                                                    <SendIcon />
                                                </IconButton>
                                            </span>
                                        </Tooltip>
                                    )}
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                                    <Typography variant="caption" color="text.secondary">
                                        {inputMessage.length} characters • ~{calculateTokens(inputMessage)} tokens
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                        <Typography variant="caption" color="text.secondary" noWrap>
                                            Model: {modelConfig.model}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary" noWrap>
                                            Temp: {modelConfig.temperature}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Box>
                        </>
                    ) : (
                        <Box
                            sx={{
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                alignItems: 'center',
                                height: '100%',
                                textAlign: 'center',
                                gap: 2,
                                p: { xs: 2, sm: 3 },
                            }}
                        >
                            <BotIcon sx={{ fontSize: { xs: 60, sm: 80, md: 120 }, color: 'primary.main' }} />
                            <Box>
                                <Typography variant="h4" color="text.primary" gutterBottom sx={{ fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' } }}>
                                    Welcome to AI Agents
                                </Typography>
                                <Typography variant="body1" color="text.secondary" sx={{ mb: 3, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
                                    Choose an agent from the sidebar to start a conversation
                                </Typography>
                                <Box sx={{
                                    display: 'flex',
                                    gap: { xs: 1, sm: 2 },
                                    justifyContent: 'center',
                                    flexWrap: 'wrap',
                                    flexDirection: { xs: 'column', md: 'row' },
                                    maxWidth: { xs: 280, md: 'auto' },
                                    mx: 'auto'
                                }}>
                                </Box>
                            </Box>
                            <Box sx={{ mt: { xs: 2, sm: 4 }, p: 2, bgcolor: alpha(theme.palette.info.main, 0.1), borderRadius: 2, maxWidth: 400, display: { xs: 'none', sm: 'block' } }}>
                                <Typography variant="body2" color="text.secondary">
                                    <strong>Keyboard Shortcuts:</strong><br />
                                    Ctrl+K: Toggle Sidebar<br />
                                    Ctrl+S: Save Session<br />
                                    Ctrl+E: Export Session<br />
                                    Ctrl+I: Import Session<br />
                                    Ctrl+/: Focus Input<br />
                                    Ctrl+F: Search<br />
                                    Ctrl+D: Toggle Theme
                                </Typography>
                            </Box>
                        </Box>
                    )}
                </Box>
            </Box>

            {/* Export Menu */}
            <Menu
                anchorEl={exportMenuAnchor}
                open={Boolean(exportMenuAnchor)}
                onClose={() => setExportMenuAnchor(null)}
            >
                <MenuItem onClick={() => { exportSession('json'); setExportMenuAnchor(null); }}>
                    Export as JSON
                </MenuItem>
                <MenuItem onClick={() => { exportSession('markdown'); setExportMenuAnchor(null); }}>
                    Export as Markdown
                </MenuItem>
                <MenuItem onClick={() => { exportSession('txt'); setExportMenuAnchor(null); }}>
                    Export as Text
                </MenuItem>
                <MenuItem onClick={() => { exportSession('csv'); setExportMenuAnchor(null); }}>
                    Export as CSV
                </MenuItem>
            </Menu>

            {/* Settings Menu */}
            <Menu
                anchorEl={settingsMenuAnchor}
                open={Boolean(settingsMenuAnchor)}
                onClose={() => setSettingsMenuAnchor(null)}
            >
                <MenuItem onClick={() => { setShowSettingsDialog(true); setSettingsMenuAnchor(null); }}>
                    <TuneIcon sx={{ mr: 1 }} />
                    Session Settings
                </MenuItem>
                <MenuItem onClick={() => { setShowModelConfigDialog(true); setSettingsMenuAnchor(null); }}>
                    <SettingsIcon sx={{ mr: 1 }} />
                    Model Configuration
                </MenuItem>
                <MenuItem onClick={() => { setShowMemoryDialog(true); setSettingsMenuAnchor(null); }}>
                    <MemoryIcon sx={{ mr: 1 }} />
                    Memory Settings
                </MenuItem>
                <MenuItem onClick={() => { setShowKnowledgeDialog(true); setSettingsMenuAnchor(null); }}>
                    <StorageIcon sx={{ mr: 1 }} />
                    Knowledge Base
                </MenuItem>
                <MenuItem onClick={() => { setShowToolsDialog(true); setSettingsMenuAnchor(null); }}>
                    <IntegrationIcon sx={{ mr: 1 }} />
                    Tools & Integrations
                </MenuItem>
                <Divider />
                <MenuItem onClick={() => { setShowHelpDialog(true); setSettingsMenuAnchor(null); }}>
                    <HelpIcon sx={{ mr: 1 }} />
                    Help & Shortcuts
                </MenuItem>
                <MenuItem onClick={() => { setShowAboutDialog(true); setSettingsMenuAnchor(null); }}>
                    <InfoIcon sx={{ mr: 1 }} />
                    About
                </MenuItem>
            </Menu>

            <SessionSettingsDialog
                open={showSettingsDialog}
                onClose={() => setShowSettingsDialog(false)}
                onSave={handleSaveSettings}
                modelConfig={modelConfig}
                sessionSettings={sessionSettings}
                providers={availableProviders}
                models={availableModels}
                providersLoading={providersLoading}
                modelsLoading={modelsLoading}
                modelsError={modelsError}
                onProviderChange={handleProviderChange}
                onModelChange={handleModelChange}
                onUpdateModelConfig={updateModelConfig}
                onUpdateSessionSettings={updateSessionSettings}
            />

            <KnowledgeBaseDialog
                open={showKnowledgeDialog}
                onClose={() => setShowKnowledgeDialog(false)}
                knowledgeBases={knowledgeBases}
                selectedKnowledgeBase={selectedKnowledgeBase}
                onSelectKnowledgeBase={(kb) => setSelectedKnowledgeBase(kb)}
                onToggleKnowledgeBase={handleToggleKnowledgeBase}
                uploadingDocument={uploadingDocument}
                uploadProgress={uploadProgress}
                onUploadDocument={uploadDocument}
                sessionSettings={sessionSettings}
                onUpdateSessionSettings={updateSessionSettings}
            />

            <MemorySettingsDialog
                open={showMemoryDialog}
                onClose={() => setShowMemoryDialog(false)}
                onSave={() => {
                    showNotification('Memory settings saved', 'success');
                    setShowMemoryDialog(false);
                }}
                memorySettings={memorySettings}
                onUpdateMemorySettings={updateMemorySettings}
            />

            <ModelConfigurationDialog
                open={showModelConfigDialog}
                onClose={() => setShowModelConfigDialog(false)}
                onSave={() => {
                    showNotification('Model configuration saved', 'success');
                    setShowModelConfigDialog(false);
                }}
                modelConfig={modelConfig}
                providers={availableProviders}
                models={availableModels}
                providersLoading={providersLoading}
                modelsLoading={modelsLoading}
                modelsError={modelsError}
                onProviderChange={handleProviderChange}
                onModelChange={handleModelChange}
                onUpdateModelConfig={updateModelConfig}
                defaultProvider={sessionSettings.provider || 'openai'}
                defaultModel={sessionSettings.model || 'gpt-4o-mini'}
                onSetDefault={() => showNotification('Default settings saved', 'success')}
                onClearDefault={() => showNotification('Default settings cleared', 'success')}
            />

            <ToolsDialog
                open={showToolsDialog}
                onClose={() => setShowToolsDialog(false)}
                tools={agentTools}
                onToggleTool={handleToggleTool}
            />

            <HelpDialog
                open={showHelpDialog}
                onClose={() => setShowHelpDialog(false)}
            />

            <AboutDialog
                open={showAboutDialog}
                onClose={() => setShowAboutDialog(false)}
            />

            <ImportSessionDialog
                open={showImportDialog}
                onClose={() => setShowImportDialog(false)}
                onImport={importSession}
            />

            {/* Notification Snackbar */}
            <Snackbar
                open={notification.open}
                autoHideDuration={3000}
                onClose={closeNotification}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert
                    onClose={closeNotification}
                    severity={notification.severity}
                    sx={{ width: '100%' }}
                >
                    {notification.message}
                </Alert>
            </Snackbar>

            {/* Loading Backdrop */}
            <Backdrop
                sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
                open={loading && !streamingResponse}
            />
        </Box>
    );
};

// Fix missing imports
const GroupsIcon = () => <span>👥</span>;

export default Agents;
