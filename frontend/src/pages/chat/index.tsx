import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Box,
    Typography,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    Button,
    CircularProgress,
    Alert,
    Chip,
    Paper,
    IconButton,
    Collapse,
    InputAdornment,
    Divider,
    Slider,
    Tooltip,
    useTheme,
    alpha,
    Drawer,
    Menu,
    Switch,
    FormControlLabel
} from '@mui/material';
import {
    Send as SendIcon,
    Refresh as RefreshIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
    Psychology as AIIcon,
    Search as SearchIcon,
    Clear as ClearIcon,
    AttachFile as AttachFileIcon,
    Image as ImageIcon,
    Mic as MicIcon,
    Videocam as VideoIcon,
    AutoAwesome as SparkleIcon,
    Settings as SettingsIcon,
    Tune as TuneIcon,
    IntegrationInstructions as IntegrationIcon,
    Help as HelpIcon,
    Info as InfoIcon,
    Star as StarIcon,
    StopCircle as StopCircleIcon,
    Stop as StopIcon,
    SmartToy as BotIcon,
    VolumeUp as VolumeUpIcon,
    History as HistoryIcon,
} from '@mui/icons-material';
import { anyllm } from '../../services/anyllm';
import { directApi } from '../../utils/api';
import { Provider, Model, Message, CompletionRequest, CompletionSettings, MessageContent, ToolDefinition, ToolCall } from '../../types/anyllm';
import ChatMessages from './ChatMessages';
import ChatHistorySidebar from './ChatHistorySidebar';
import { useChatHistory } from '../../contexts/ChatHistoryContext';
import { chatSessionsService } from '../../services/chatSessions';

// Add fade-in animation and pulse effect
const fadeInStyles = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.3;
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined' && !document.getElementById('chat-fade-in-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'chat-fade-in-styles';
    styleSheet.textContent = fadeInStyles;
    document.head.appendChild(styleSheet);
}

interface ThinkingBoxProps {
    thinking: string;
}

function ThinkingBox({ thinking }: ThinkingBoxProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <Box sx={{ mb: 2 }}>
            <Paper
                sx={{
                    p: 2,
                    bgcolor: 'grey.50',
                    border: '1px solid',
                    borderColor: 'grey.200'
                }}
            >
                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                        justifyContent: 'space-between'
                    }}
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AIIcon color="primary" />
                        <Typography variant="subtitle2" fontWeight="medium">
                            Thinking ({thinking.length} characters)
                        </Typography>
                    </Box>
                    <IconButton size="small">
                        {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                </Box>
                <Collapse in={isExpanded}>
                    <Box sx={{ mt: 1, p: 1, bgcolor: 'white', borderRadius: 1 }}>
                        <Typography
                            variant="body2"
                            component="pre"
                            sx={{
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                                maxHeight: 200,
                                overflow: 'auto'
                            }}
                        >
                            {thinking}
                        </Typography>
                    </Box>
                </Collapse>
            </Paper>
        </Box>
    );
}

const Chat: React.FC = () => {
    const theme = useTheme();
    const chatHistory = useChatHistory();

    const [providers, setProviders] = useState<Provider[]>([]);
    const [selectedProvider, setSelectedProvider] = useState<string>('');
    const [models, setModels] = useState<Model[]>([]);
    const [selectedModel, setSelectedModel] = useState<Model | null>(null);
    const [defaultModel, setDefaultModel] = useState<{provider: string, modelId: string} | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputMessage, setInputMessage] = useState<string>('');
    const [attachedFiles, setAttachedFiles] = useState<MessageContent[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
    const [modelFilter, setModelFilter] = useState<string>('');
    const [currentThinking, setCurrentThinking] = useState<string>('');
    const [completionSettings, setCompletionSettings] = useState<CompletionSettings>({
        temperature: 0.7,
        top_p: 1.0,
        max_tokens: 2048,
        presence_penalty: 0.0,
        frequency_penalty: 0.0,
        reasoning_effort: 'auto'
    });

    // New state for enhanced features
    // chatMode removed — tool calling replaces slash command modes
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
    const [settingsMenuAnchor, setSettingsMenuAnchor] = useState<null | HTMLElement>(null);
    const [expandedMenuSection, setExpandedMenuSection] = useState<string | null>(null);

    // Track if we're in a session
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

    // Voice chat state
    const [isRecording, setIsRecording] = useState<boolean>(false);
    const [transcribing, setTranscribing] = useState<boolean>(false);
    const [voiceModeEnabled, setVoiceModeEnabled] = useState<boolean>(false);
    const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

    // Tool calling state
    const [toolDefinitions, setToolDefinitions] = useState<ToolDefinition[]>([]);
    const [executingTools, setExecutingTools] = useState<string[]>([]);

    const chatInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const drawerRef = useRef<HTMLDivElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);
    const pendingToolCallsRef = useRef<Map<number, { id: string; name: string; arguments: string }>>(new Map());
    const toolMediaRef = useRef<MessageContent[]>([]);
    const titleGeneratedRef = useRef<Set<string>>(new Set());

    // Auto-scroll to bottom — throttled to avoid jank during streaming
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);
    const scrollThrottleRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        // Throttle scroll updates to max once per 150ms during streaming
        if (scrollThrottleRef.current) return;
        scrollToBottom();
        scrollThrottleRef.current = setTimeout(() => {
            scrollThrottleRef.current = null;
        }, 150);
    }, [messages, loading, executingTools, scrollToBottom]);

    // Stop streaming
    const stopStreaming = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setLoading(false);
        setExecutingTools([]);
        setCurrentThinking('');
    }, []);

    // Friendly labels for tool execution
    const getToolLabel = useCallback((name: string): string => {
        const labels: Record<string, string> = {
            web_search: 'Searching the web...',
            news_search: 'Searching news...',
            generate_image: 'Generating image...',
            text_to_speech: 'Generating audio...',
            generate_video: 'Generating video...',
            search_stock_images: 'Searching stock images...',
            search_stock_videos: 'Searching stock videos...',
            capture_screenshot: 'Capturing screenshot...',
            generate_music: 'Generating music...',
            execute_python: 'Running code...',
            enhance_image: 'Enhancing image...',
            download_media: 'Downloading media...',
            add_text_overlay: 'Adding text overlay...',
            list_social_platforms: 'Loading social platforms...',
            post_to_social_media: 'Posting to social media...',
            schedule_social_post: 'Scheduling social post...',
            create_social_draft: 'Creating social draft...',
        };
        return labels[name] || name.replace(/_/g, ' ') + '...';
    }, []);

    const loadProviders = useCallback(async () => {
        try {
            const providerList = await anyllm.getProviders();
            setProviders(providerList);
        } catch (err) {
            setError('Failed to load providers');
            console.error('Error loading providers:', err);
        }
    }, []);

    // Default model management
    const loadDefaultModel = useCallback(() => {
        try {
            const saved = localStorage.getItem('chat_default_model');
            if (saved) {
                const parsed = JSON.parse(saved);
                setDefaultModel(parsed);
                return parsed;
            }
        } catch (error) {
            console.warn('Failed to load default model:', error);
        }
        return null;
    }, []);

    const saveDefaultModel = useCallback(() => {
        if (selectedProvider && selectedModel) {
            const defaultConfig = {
                provider: selectedProvider,
                modelId: selectedModel.id
            };
            localStorage.setItem('chat_default_model', JSON.stringify(defaultConfig));
            setDefaultModel(defaultConfig);
        }
    }, [selectedProvider, selectedModel]);

    const resetDefaultModel = useCallback(() => {
        localStorage.removeItem('chat_default_model');
        setDefaultModel(null);
    }, []);

    const adjustSettingsForModel = useCallback((model: Model) => {
        if (!model.parameter_info) return;

        const info = model.parameter_info;
        const newSettings = { ...completionSettings };

        // Apply recommended defaults
        if (info.recommended_defaults.temperature !== undefined) {
            newSettings.temperature = info.recommended_defaults.temperature;
        }
        if (info.recommended_defaults.top_p !== undefined) {
            newSettings.top_p = info.recommended_defaults.top_p;
        }
        if (info.recommended_defaults.max_tokens) {
            newSettings.max_tokens = info.recommended_defaults.max_tokens;
        }

        // Disable unsupported parameters
        if (info.unsupported_params.includes('temperature')) {
            newSettings.temperature = 0;
        }
        if (info.unsupported_params.includes('top_p')) {
            newSettings.top_p = 1;
        }

        // Only enable reasoning effort if supported
        if (!info.supports_reasoning) {
            newSettings.reasoning_effort = undefined;
        }

        setCompletionSettings(newSettings);
    }, [completionSettings]);

    const loadModels = useCallback(async () => {
        if (!selectedProvider) return;

        try {
            setLoading(true);
            const modelList = await anyllm.getModels(selectedProvider);
            setModels(modelList);

            const selectedModelExistsInProvider = selectedModel
                ? modelList.some((m) => m.id === selectedModel.id)
                : false;

            // Use default model if available, otherwise prefer deepseek-chat, then first available
            if (modelList.length > 0 && !selectedModelExistsInProvider) {
                const defaultConfig = loadDefaultModel();
                let modelToSelect = modelList[0];

                // Try to find and use the default model if it exists
                if (defaultConfig && defaultConfig.provider === selectedProvider) {
                    const defaultModelInList = modelList.find(m => m.id === defaultConfig.modelId);
                    if (defaultModelInList) {
                        modelToSelect = defaultModelInList;
                    }
                } else {
                    // No user default — just use first available model
                }

                setSelectedModel(modelToSelect);
                adjustSettingsForModel(modelToSelect);
            }
        } catch (err) {
            setError(`Failed to load models for ${selectedProvider}`);
            console.error('Error loading models:', err);
        } finally {
            setLoading(false);
        }
    }, [selectedProvider, selectedModel, adjustSettingsForModel, loadDefaultModel]);

    useEffect(() => {
        loadProviders();
        // Load default model on component mount (user-saved or server default)
        const defaultConfig = loadDefaultModel();
        if (defaultConfig) {
            setSelectedProvider(defaultConfig.provider);
        } else {
            // Fetch server-configured default provider
            anyllm.getDefaultProvider().then(serverDefault => {
                setSelectedProvider(serverDefault);
            }).catch(() => {
                setSelectedProvider('deepseek');
            });
        }
        // Fetch tool definitions for LLM function calling
        directApi.get('/tools').then(res => {
            const tools = res.data?.tools || [];
            setToolDefinitions(tools);
        }).catch(err => {
            console.warn('Failed to load tool definitions:', err);
        });
    }, [loadProviders, loadDefaultModel]);

    useEffect(() => {
        if (selectedProvider) {
            loadModels();
        }
    }, [selectedProvider, loadModels]);

    const isParameterSupported = (param: string) => {
        if (!selectedModel?.parameter_info) return true; // Assume supported if no info
        return !selectedModel.parameter_info.unsupported_params.includes(param);
    };

    const getMaxTokensLabel = () => {
        if (!selectedModel?.parameter_info) return 'Max Tokens';
        return selectedModel.parameter_info.max_tokens_param === 'max_completion_tokens'
            ? 'Max Completion Tokens'
            : 'Max Tokens';
    };

    const handleFileUploaded = (content: MessageContent) => {
        setAttachedFiles(prev => [...prev, content]);
        setError('');
    };

    const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;

        const file = files[0];

        try {
            // Import the uploadFile function from utils
            const { uploadFile, getFileType } = await import('../../utils/fileUpload');

            const result = await uploadFile(file);

            // Validate that we got a valid URL
            if (!result.url) {
                throw new Error('Upload returned no file URL');
            }

            const fileType = getFileType(file);
            const content: MessageContent = {
                type: (fileType === 'unknown' ? 'text' : fileType) as 'text' | 'image' | 'audio' | 'video',
                url: result.url,
                filename: result.filename,
                size: result.size,
                mime_type: result.mime_type,
                alt_text: `Uploaded ${fileType}: ${file.name}`
            };

            handleFileUploaded(content);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Upload failed';
            setError(`Failed to upload file: ${errorMessage}`);
        } finally {
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleRemoveFile = (index: number) => {
        setAttachedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const buildMessageContent = (): MessageContent[] => {
        const content: MessageContent[] = [];

        // Add text content if present
        if (inputMessage.trim()) {
            content.push({
                type: 'text',
                text: inputMessage.trim()
            });
        }

        // Add attached files
        content.push(...attachedFiles);

        return content;
    };

    // Build a CompletionRequest with the current model settings
    const buildCompletionRequest = useCallback((conversationMessages: Message[]): CompletionRequest => {
        const baseRequest: CompletionRequest & { messages_multimodal?: Message[] } = {
            provider: selectedProvider,
            model: selectedModel!.id,
            messages: conversationMessages,
            messages_multimodal: conversationMessages,
            stream: true,
        };

        // Include tool definitions if available
        if (toolDefinitions.length > 0) {
            baseRequest.tools = toolDefinitions;
            baseRequest.tool_choice = 'auto';
        }

        if (selectedModel?.parameter_info) {
            const info = selectedModel.parameter_info;
            if (info.max_tokens_param === 'max_completion_tokens') {
                baseRequest.max_completion_tokens = completionSettings.max_tokens;
            } else {
                baseRequest.max_tokens = completionSettings.max_tokens;
            }
            if (!info.unsupported_params.includes('temperature')) baseRequest.temperature = completionSettings.temperature;
            if (!info.unsupported_params.includes('top_p')) baseRequest.top_p = completionSettings.top_p;
            if (!info.unsupported_params.includes('presence_penalty')) baseRequest.presence_penalty = completionSettings.presence_penalty;
            if (!info.unsupported_params.includes('frequency_penalty')) baseRequest.frequency_penalty = completionSettings.frequency_penalty;
            if (info.supports_reasoning && completionSettings.reasoning_effort) baseRequest.reasoning_effort = completionSettings.reasoning_effort;
        } else {
            baseRequest.temperature = completionSettings.temperature;
            baseRequest.top_p = completionSettings.top_p;
            baseRequest.max_tokens = completionSettings.max_tokens;
            baseRequest.presence_penalty = completionSettings.presence_penalty;
            baseRequest.frequency_penalty = completionSettings.frequency_penalty;
            if (completionSettings.reasoning_effort) baseRequest.reasoning_effort = completionSettings.reasoning_effort;
        }

        return baseRequest;
    }, [selectedProvider, selectedModel, completionSettings, toolDefinitions]);

    const playResponseAudio = useCallback(async (text: string) => {
        if (!text || isPlayingAudio) return;
        setIsPlayingAudio(true);
        try {
            const response = await directApi.post('/audio/speech', {
                text: text.substring(0, 2000),
                sync: true,
                provider: 'kokoro',
                voice: 'af_heart',
                response_format: 'mp3'
            });
            const audioUrl = response.data?.result?.audio_url;
            if (audioUrl) {
                const audio = new Audio(audioUrl);
                audioPlayerRef.current = audio;
                audio.onended = () => setIsPlayingAudio(false);
                audio.onerror = () => setIsPlayingAudio(false);
                await audio.play();
            } else {
                setIsPlayingAudio(false);
            }
        } catch {
            setIsPlayingAudio(false);
        }
    }, [isPlayingAudio]);

    // Run a completion with tool call loop support
    const runCompletionWithTools = useCallback(async (conversationMessages: Message[], depth = 0): Promise<string> => {
        if (depth > 5) {
            setError('Too many tool call iterations');
            setLoading(false);
            return '';
        }

        // Reset tool call tracking
        pendingToolCallsRef.current = new Map();
        toolMediaRef.current = [];

        // Add assistant placeholder
        const assistantMessage: Message = { role: 'assistant', content: [{ type: 'text', text: '' }] };
        setMessages([...conversationMessages, assistantMessage]);

        const completionRequest = buildCompletionRequest(conversationMessages);

        // Create abort controller for this request
        const controller = new AbortController();
        abortControllerRef.current = controller;
        let streamedAssistantText = '';
        let pendingContent = '';
        let rafId: number | null = null;

        try {
            await anyllm.chatWithProvider(completionRequest, {
                signal: controller.signal,
                onChunk: (chunk) => {
                    const choice = chunk.choices[0];
                    if (!choice) return;
                    const content = choice.delta?.content || '';
                    const thinking = choice.delta?.thinking || '';
                    streamedAssistantText += content;

                    // Accumulate tool calls from stream chunks
                    if (choice.delta?.tool_calls) {
                        for (const tc of choice.delta.tool_calls) {
                            const existing = pendingToolCallsRef.current.get(tc.index) || { id: '', name: '', arguments: '' };
                            if (tc.id) existing.id = tc.id;
                            if (tc.function?.name) existing.name += tc.function.name;
                            if (tc.function?.arguments) existing.arguments += tc.function.arguments;
                            pendingToolCallsRef.current.set(tc.index, existing);
                        }
                    }

                    // Batch content updates via requestAnimationFrame for smooth rendering
                    if (content) {
                        pendingContent += content;
                        if (!rafId) {
                            rafId = requestAnimationFrame(() => {
                                const batch = pendingContent;
                                pendingContent = '';
                                rafId = null;
                                setMessages(prev => {
                                    const updated = [...prev];
                                    const lastMessage = updated[updated.length - 1];
                                    if (lastMessage.role === 'assistant' && Array.isArray(lastMessage.content)) {
                                        const lastContent = lastMessage.content[lastMessage.content.length - 1];
                                        updated[updated.length - 1] = {
                                            ...lastMessage,
                                            content: [
                                                ...lastMessage.content.slice(0, -1),
                                                { ...lastContent, text: (lastContent.text || '') + batch }
                                            ]
                                        };
                                    }
                                    return updated;
                                });
                            });
                        }
                    }

                    if (thinking) {
                        setCurrentThinking(prev => prev + thinking);
                    }
                },
                onComplete: () => {
                    // Flush any remaining buffered content
                    if (rafId) {
                        cancelAnimationFrame(rafId);
                        rafId = null;
                    }
                    if (pendingContent) {
                        const remaining = pendingContent;
                        pendingContent = '';
                        setMessages(prev => {
                            const updated = [...prev];
                            const lastMessage = updated[updated.length - 1];
                            if (lastMessage.role === 'assistant' && Array.isArray(lastMessage.content)) {
                                const lastContent = lastMessage.content[lastMessage.content.length - 1];
                                updated[updated.length - 1] = {
                                    ...lastMessage,
                                    content: [
                                        ...lastMessage.content.slice(0, -1),
                                        { ...lastContent, text: (lastContent.text || '') + remaining }
                                    ]
                                };
                            }
                            return updated;
                        });
                    }
                    setCurrentThinking('');
                },
                onError: (err) => {
                    setError(err);
                    setLoading(false);
                    setCurrentThinking('');
                    setExecutingTools([]);
                }
            });

            // After streaming completes, check for tool calls
            const toolCalls = Array.from(pendingToolCallsRef.current.values());

            if (toolCalls.length > 0 && toolCalls.some(tc => tc.name)) {
                // Show tool execution status
                setExecutingTools(toolCalls.map(tc => tc.name));

                // Format tool calls for the assistant message
                const formattedToolCalls: ToolCall[] = toolCalls.map(tc => ({
                    id: tc.id,
                    type: 'function' as const,
                    function: { name: tc.name, arguments: tc.arguments }
                }));

                // Update assistant message with tool_calls
                let currentMessages: Message[] = [];
                setMessages(prev => {
                    currentMessages = [...prev];
                    const lastMsg = currentMessages[currentMessages.length - 1];
                    if (lastMsg.role === 'assistant') {
                        currentMessages[currentMessages.length - 1] = { ...lastMsg, tool_calls: formattedToolCalls };
                    }
                    return currentMessages;
                });

                // Execute each tool call
                const toolResultMessages: Message[] = [];
                for (const tc of toolCalls) {
                    try {
                        const args = JSON.parse(tc.arguments || '{}');
                        const response = await directApi.post('/tools/execute', { name: tc.name, arguments: args });
                        const result = response.data?.result || {};

                        toolResultMessages.push({
                            role: 'tool',
                            content: JSON.stringify(result),
                            tool_call_id: tc.id,
                        });

                        // Collect media URLs from tool results for inline display
                        if (result.image_url) toolMediaRef.current.push({ type: 'image', url: result.image_url, alt_text: `Generated image` });
                        if (result.audio_url) toolMediaRef.current.push({ type: 'audio', url: result.audio_url, alt_text: `Generated audio` });
                        if (result.video_url) toolMediaRef.current.push({ type: 'video', url: result.video_url, alt_text: `Generated video` });
                        if (result.screenshot_url) toolMediaRef.current.push({ type: 'image', url: result.screenshot_url, alt_text: `Screenshot` });
                        // For stock images, add first few
                        if (result.images) {
                            for (const img of result.images.slice(0, 4)) {
                                if (img.url) toolMediaRef.current.push({ type: 'image', url: img.url, alt_text: img.alt || 'Stock image' });
                            }
                        }
                        if (result.videos) {
                            for (const vid of result.videos.slice(0, 2)) {
                                if (vid.url) toolMediaRef.current.push({ type: 'video', url: vid.url, alt_text: 'Stock video' });
                            }
                        }
                    } catch (err) {
                        toolResultMessages.push({
                            role: 'tool',
                            content: JSON.stringify({ error: err instanceof Error ? err.message : 'Tool execution failed' }),
                            tool_call_id: tc.id,
                        });
                    }
                }

                setExecutingTools([]);

                // Add tool results and continue the conversation
                const updatedMessages = [...currentMessages, ...toolResultMessages];
                setMessages(updatedMessages);

                return await runCompletionWithTools(updatedMessages, depth + 1);
            } else {
                // Normal completion — no tool calls
                setLoading(false);

                // Append any collected tool media to the last assistant message
                if (toolMediaRef.current.length > 0) {
                    const media = [...toolMediaRef.current];
                    toolMediaRef.current = [];
                    setMessages(prev => {
                        const updated = [...prev];
                        const lastMsg = updated[updated.length - 1];
                        if (lastMsg.role === 'assistant' && Array.isArray(lastMsg.content)) {
                            updated[updated.length - 1] = {
                                ...lastMsg,
                                content: [...lastMsg.content, ...media],
                            };
                        }
                        return updated;
                    });
                }

                // Voice mode: auto-read response
                if (voiceModeEnabled) {
                    setMessages(prev => {
                        const last = prev[prev.length - 1];
                        if (last?.role === 'assistant' && Array.isArray(last.content)) {
                            const text = last.content.filter(c => c.type === 'text').map(c => c.text || '').join(' ');
                            if (text) playResponseAudio(text);
                        }
                        return prev;
                    });
                }

                return streamedAssistantText.trim();
            }
        } catch {
            setError('Failed to send message');
            setLoading(false);
            setCurrentThinking('');
            setExecutingTools([]);
            return '';
        }
    }, [buildCompletionRequest, voiceModeEnabled, playResponseAudio]);

    const handleSendMessage = async () => {
        const messageContent = buildMessageContent();
        if (messageContent.length === 0) return;
        if (!selectedProvider || !selectedModel) return;

        const userMessage: Message = {
            role: 'user',
            content: messageContent,
        };

        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setInputMessage('');
        setAttachedFiles([]);
        setError('');
        setCurrentThinking('');
        setLoading(true);

        let activeSessionId = currentSessionId;
        if (!activeSessionId) {
            try {
                const newSession = await chatHistory.createNewSession();
                activeSessionId = newSession.session_id;
                setCurrentSessionId(activeSessionId);
            } catch (err) {
                console.error('Failed to create chat session:', err);
                setError('Failed to create chat session');
                setLoading(false);
                return;
            }
        }

        // Generate title for first message of session
        if (activeSessionId && !titleGeneratedRef.current.has(activeSessionId)) {
            // Extract text from message content
            const messageText = messageContent
                .map((item): string => {
                    if (item.type === 'text') return item.text ?? '';
                    if (item.type === 'image') return '[Image]';
                    if (item.type === 'audio') return '[Audio]';
                    if (item.type === 'video') return '[Video]';
                    return '';
                })
                .join(' ');

            if (messageText.trim()) {
                // Generate title in background, don't await
                chatSessionsService.generateTitle({
                    message: messageText,
                    model_id: selectedModel.id,
                    provider: selectedProvider,
                }).then((generatedTitle) => {
                    if (generatedTitle) {
                        // Update session with generated title
                        chatHistory.updateSession(activeSessionId, { title: generatedTitle });
                        titleGeneratedRef.current.add(activeSessionId);
                    }
                }).catch((err) => {
                    console.error('Failed to generate title:', err);
                });
            }
        }

        const assistantText = await runCompletionWithTools(newMessages);

        // Persist the latest user/assistant turn to chat history storage
        if (activeSessionId) {
            const userText = messageContent
                .map((item): string => {
                    if (item.type === 'text') return item.text ?? '';
                    if (item.type === 'image') return '[Image]';
                    if (item.type === 'audio') return '[Audio]';
                    if (item.type === 'video') return '[Video]';
                    return '';
                })
                .join(' ')
                .trim();

            const messagesToPersist: Array<{ role: 'user' | 'assistant'; content: string }> = [];
            if (userText) {
                messagesToPersist.push({ role: 'user', content: userText });
            }
            if (assistantText) {
                messagesToPersist.push({ role: 'assistant', content: assistantText });
            }

            if (messagesToPersist.length > 0) {
                try {
                    await chatSessionsService.updateSession(activeSessionId, {
                        messages: messagesToPersist,
                    });
                } catch (err) {
                    console.error('Failed to persist chat messages:', err);
                }
            }
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const resetChat = async () => {
        setMessages([]);
        setCurrentThinking('');
        setError('');
        // Reset title generation tracking
        titleGeneratedRef.current.clear();
        // Create a new session for the fresh chat
        const newSession = await chatHistory.createNewSession();
        setCurrentSessionId(newSession.session_id);
    };

    // ------------------------------------------------------------------
    // Voice chat functions
    // ------------------------------------------------------------------
    const startRecording = async () => {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Microphone not supported in this browser');
            }

            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioDevices = devices.filter(d => d.kind === 'audioinput');
            if (audioDevices.length === 0) {
                throw new Error('No microphone found');
            }

            const stream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
            });

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.addEventListener('dataavailable', (e) => {
                audioChunksRef.current.push(e.data);
            });

            mediaRecorder.addEventListener('stop', async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                stream.getTracks().forEach(track => track.stop());

                if (audioBlob.size < 100) {
                    setError('Recording too short');
                    return;
                }

                setTranscribing(true);
                try {
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.webm');

                    const response = await directApi.agentSpeechToText(formData);
                    if (response.success && response.data) {
                        const text = (response.data as { text: string }).text;
                        if (text && text.trim()) {
                            setInputMessage(prev => prev + (prev ? ' ' : '') + text.trim());
                        } else {
                            setError('Could not understand audio. Try speaking more clearly.');
                        }
                    }
                } catch {
                    setError('Failed to transcribe audio');
                } finally {
                    setTranscribing(false);
                }
            });

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            let msg = 'Failed to start recording';
            if (err instanceof Error) {
                if (err.name === 'NotAllowedError') msg = 'Microphone access denied';
                else if (err.name === 'NotFoundError') msg = 'No microphone found';
                else msg = err.message;
            }
            setError(msg);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const stopAudioPlayback = () => {
        if (audioPlayerRef.current) {
            audioPlayerRef.current.pause();
            audioPlayerRef.current = null;
        }
        setIsPlayingAudio(false);
    };

    const filteredModels = models.filter(model =>
        model.id.toLowerCase().includes(modelFilter.toLowerCase())
    );

    // Suggestion chips for the empty state
    const suggestionChips = [
        { label: 'Create a short video', command: 'Create a short video about space exploration', icon: <VideoIcon sx={{ fontSize: 16 }} /> },
        { label: 'Generate an image', command: 'Generate an image of a futuristic city skyline at sunset', icon: <ImageIcon sx={{ fontSize: 16 }} /> },
        { label: 'Text to speech', command: 'Read this aloud: Welcome to Griot, your creative studio', icon: <MicIcon sx={{ fontSize: 16 }} /> },
        { label: 'Search the web', command: 'Search for the latest AI and technology news', icon: <SearchIcon sx={{ fontSize: 16 }} /> },
    ];

    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'row', bgcolor: 'background.default' }}>
            {/* Chat History Sidebar */}
            <ChatHistorySidebar
                currentSessionId={currentSessionId}
                onSessionSelect={async (sessionId) => {
                    if (sessionId) {
                        setCurrentSessionId(sessionId);
                        const sessionMessages = await chatHistory.loadSessionMessages(sessionId);
                        // Convert ChatMessage[] to Message[] format
                        setMessages(sessionMessages.map(msg => ({
                            role: msg.role as 'user' | 'assistant',
                            content: [{ type: 'text', text: msg.content }]
                        })));
                    } else {
                        setCurrentSessionId(null);
                        setMessages([]);
                    }
                }}
            />

            {/* Main Chat Area */}
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', flex: 1 }}>
                {/* Header with history toggle button */}
                <Box
                    sx={{
                        px: { xs: 2, sm: 3 },
                        py: 1.5,
                        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                    }}
                >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Tooltip title="Toggle chat history">
                            <IconButton
                                size="small"
                                onClick={() => chatHistory.setSidebarOpen(!chatHistory.sidebarOpen)}
                                sx={{
                                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                                    '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.15) },
                                }}
                            >
                                <HistoryIcon fontSize="small" color="primary" />
                            </IconButton>
                        </Tooltip>
                        <Typography variant="h6" fontWeight="600">
                            Griot Chat
                        </Typography>
                    </Box>
                </Box>

                {/* Error Alert */}
                {error && (
                    <Alert severity="error" sx={{ mx: { xs: 2, sm: 3 }, mt: 1 }} onClose={() => setError('')}>
                        {error}
                    </Alert>
                )}

            {/* Messages Container */}
            <Box
                sx={{
                    flexGrow: 1,
                    overflow: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    px: { xs: 2, sm: 3 },
                }}
            >
                {/* Thinking Box */}
                {currentThinking && <ThinkingBox thinking={currentThinking} />}

                {messages.length === 0 ? (
                    /* ── Empty State: Welcome Hero ── */
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            alignItems: 'center',
                            flex: 1,
                            textAlign: 'center',
                            gap: { xs: 2, sm: 3 },
                            py: { xs: 4, sm: 6 },
                            maxWidth: 640,
                            mx: 'auto',
                            width: '100%',
                        }}
                    >
                        {/* Gradient icon */}
                        <Box
                            sx={{
                                width: { xs: 72, sm: 88 },
                                height: { xs: 72, sm: 88 },
                                borderRadius: '50%',
                                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.12)}, ${alpha(theme.palette.secondary.main, 0.12)})`,
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                animation: 'fadeInUp 0.5s ease-out',
                            }}
                        >
                            <SparkleIcon sx={{ fontSize: { xs: 36, sm: 44 }, color: 'primary.main' }} />
                        </Box>

                        {/* Welcome text */}
                        <Box sx={{ animation: 'fadeInUp 0.6s ease-out' }}>
                            <Typography
                                variant="h4"
                                sx={{
                                    fontWeight: 700,
                                    color: 'text.primary',
                                    fontSize: { xs: '1.5rem', sm: '1.85rem', md: '2.1rem' },
                                    lineHeight: 1.2,
                                    mb: 1,
                                }}
                            >
                                What would you like to create?
                            </Typography>
                            <Typography
                                variant="body1"
                                color="text.secondary"
                                sx={{ fontSize: { xs: '0.9rem', sm: '1rem' }, maxWidth: 480, mx: 'auto' }}
                            >
                                Chat with AI, generate videos, images, audio, or search the web — all from one place.
                            </Typography>
                        </Box>

                        {/* Suggestion chips */}
                        <Box
                            sx={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                justifyContent: 'center',
                                gap: 1,
                                mt: 1,
                                animation: 'fadeInUp 0.7s ease-out',
                            }}
                        >
                            {suggestionChips.map((chip) => (
                                <Chip
                                    key={chip.label}
                                    icon={chip.icon}
                                    label={chip.label}
                                    variant="outlined"
                                    clickable
                                    onClick={() => {
                                        setInputMessage(chip.command);
                                        setTimeout(() => chatInputRef.current?.focus(), 50);
                                    }}
                                    sx={{
                                        borderRadius: '20px',
                                        px: 1,
                                        py: 2.5,
                                        fontSize: { xs: '0.8rem', sm: '0.875rem' },
                                        borderColor: alpha(theme.palette.divider, 0.3),
                                        transition: 'all 0.2s ease',
                                        '&:hover': {
                                            borderColor: theme.palette.primary.main,
                                            backgroundColor: alpha(theme.palette.primary.main, 0.06),
                                            transform: 'translateY(-1px)',
                                            boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.15)}`,
                                        },
                                    }}
                                />
                            ))}
                        </Box>
                    </Box>
                ) : (
                    /* ── Chat Messages ── */
                    <Box sx={{ py: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <ChatMessages
                            messages={messages}
                            loading={loading}
                            onCopyMessage={copyToClipboard}
                        />
                        {currentThinking && <ThinkingBox thinking={currentThinking} />}
                        {/* Tool execution chips */}
                        {executingTools.length > 0 && (
                            <Box sx={{ display: 'flex', justifyContent: 'flex-start', ml: 6.5, mb: 1, gap: 1, flexWrap: 'wrap' }}>
                                {executingTools.map((toolName, i) => (
                                    <Chip
                                        key={i}
                                        icon={<CircularProgress size={12} />}
                                        label={getToolLabel(toolName)}
                                        size="small"
                                        variant="outlined"
                                        color="info"
                                        sx={{ animation: 'fadeInUp 0.3s ease-out' }}
                                    />
                                ))}
                            </Box>
                        )}
                        {/* Typing indicator — shows until streaming text starts arriving */}
                        {loading && executingTools.length === 0 && (() => {
                            const lastMsg = messages[messages.length - 1];
                            const hasContent = lastMsg?.role === 'assistant' && Array.isArray(lastMsg.content)
                                && lastMsg.content.some(c => c.type === 'text' && c.text && c.text.trim().length > 0);
                            return !hasContent;
                        })() && (
                            <Box sx={{ display: 'flex', justifyContent: 'flex-start', gap: 1.5, mb: 2 }}>
                                <Box
                                    sx={{
                                        width: 40,
                                        height: 40,
                                        borderRadius: '50%',
                                        background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0,
                                        boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.3)}`,
                                    }}
                                >
                                    <BotIcon sx={{ fontSize: 20, color: 'white' }} />
                                </Box>
                                <Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                        <Typography variant="caption" color="text.secondary" fontWeight={500}>
                                            AI Assistant
                                        </Typography>
                                        <CircularProgress size={12} />
                                        <Typography variant="caption" color="text.secondary">
                                            Typing...
                                        </Typography>
                                    </Box>
                                    <Paper
                                        elevation={0}
                                        sx={{
                                            p: 2,
                                            background: alpha(theme.palette.background.paper, 0.9),
                                            borderRadius: '18px 18px 18px 6px',
                                            border: `1px solid ${alpha(theme.palette.divider, 0.12)}`,
                                            animation: 'fadeInUp 0.3s ease-out',
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                                            <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'text.disabled', animation: 'pulse 1.4s infinite', animationDelay: '0s' }} />
                                            <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'text.disabled', animation: 'pulse 1.4s infinite', animationDelay: '0.2s' }} />
                                            <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'text.disabled', animation: 'pulse 1.4s infinite', animationDelay: '0.4s' }} />
                                        </Box>
                                    </Paper>
                                </Box>
                            </Box>
                        )}
                        <div ref={messagesEndRef} />
                    </Box>
                )}
            </Box>

            {/* ── Input Bar (pinned at bottom) ── */}
            <Box
                sx={{
                    px: { xs: 2, sm: 3 },
                    pb: { xs: 1.5, sm: 2 },
                    pt: { xs: 1, sm: 1.5 },
                    borderTop: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
                }}
            >
                {/* Model selector row */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 1.5 }}>
                    <Chip
                        size="small"
                        label={selectedModel ? selectedModel.id : 'Select model'}
                        onClick={(e) => setSettingsMenuAnchor(e.currentTarget)}
                        icon={<TuneIcon sx={{ fontSize: 14 }} />}
                        variant="outlined"
                        sx={{
                            maxWidth: 240,
                            fontSize: '0.75rem',
                            height: 28,
                            borderColor: alpha(theme.palette.divider, 0.3),
                            '&:hover': {
                                borderColor: theme.palette.primary.main,
                                backgroundColor: alpha(theme.palette.primary.main, 0.04),
                            }
                        }}
                    />
                    {messages.length > 0 && (
                        <Tooltip title="New chat">
                            <IconButton size="small" onClick={resetChat} sx={{ width: 28, height: 28 }}>
                                <RefreshIcon sx={{ fontSize: 16 }} />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>

                {/* File Attachments */}
                {attachedFiles.length > 0 && (
                    <Box sx={{ mb: 1.5, display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                        {attachedFiles.map((file, index) => (
                            <Chip
                                key={index}
                                label={file.filename || `${file.type} file`}
                                onDelete={() => handleRemoveFile(index)}
                                size="small"
                                variant="outlined"
                                icon={<AttachFileIcon fontSize="small" />}
                                sx={{ fontSize: '0.75rem', height: 28 }}
                            />
                        ))}
                    </Box>
                )}

                {/* Input Container - agent-chat-ui inspired design */}
                <Box
                    sx={{
                        display: 'grid',
                        gridTemplateRows: '1fr auto',
                        gap: 0.5,
                        maxWidth: 800,
                        mx: 'auto',
                        width: '100%',
                    }}
                >
                    {/* Main input form with rounded-2xl and shadow */}
                    <Box
                        sx={{
                            borderRadius: '16px',
                            boxShadow: `0 1px 2px 0 ${alpha(theme.palette.divider, 0.1)}`,
                            border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                            backgroundColor: alpha(theme.palette.background.paper, 0.4),
                            overflow: 'hidden',
                            transition: 'all 0.2s ease',
                            '&:hover': {
                                borderColor: alpha(theme.palette.primary.main, 0.3),
                                boxShadow: `0 4px 6px -1px ${alpha(theme.palette.primary.main, 0.1)}`,
                            },
                            '&:focus-within': {
                                borderColor: theme.palette.primary.main,
                                boxShadow: `0 0 0 2px ${alpha(theme.palette.primary.main, 0.1)}`,
                            },
                        }}
                    >
                        <TextField
                            fullWidth
                            multiline
                            maxRows={8}
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Type your message..."
                            disabled={loading || (!selectedProvider || !selectedModel)}
                            inputRef={chatInputRef}
                            variant="standard"
                            InputProps={{
                                disableUnderline: true,
                                sx: {
                                    px: 2,
                                    py: 1,
                                    fontSize: { xs: '16px', sm: '15px' },
                                    '&.MuiInputBase-input': {
                                        '&::placeholder': {
                                            color: 'text.secondary',
                                            opacity: 0.7,
                                        },
                                    },
                                },
                            }}
                            sx={{
                                '& .MuiInputBase-root': {
                                    backgroundColor: 'transparent',
                                },
                            }}
                        />

                        {/* Bottom controls bar */}
                        <Box
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                px: 1.5,
                                pb: 1,
                            }}
                        >
                            {/* Hidden file input */}
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*,audio/*,video*"
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                                disabled={loading}
                            />

                            {/* Left side: Attach and Voice buttons */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {/* File Attach Button - agent-chat-ui style */}
                                <Box
                                    onClick={() => fileInputRef.current?.click()}
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 0.5,
                                        cursor: 'pointer',
                                        color: 'text.secondary',
                                        fontSize: '0.875rem',
                                        opacity: loading ? 0.5 : 1,
                                        pointerEvents: loading ? 'none' : 'auto',
                                        '&:hover': { color: 'text.primary' },
                                    }}
                                >
                                    <Box
                                        sx={{
                                            width: 20,
                                            height: 20,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            position: 'relative',
                                        }}
                                    >
                                        <AttachFileIcon sx={{ fontSize: 20 }} />
                                        {attachedFiles.length > 0 && (
                                            <Box
                                                sx={{
                                                    position: 'absolute',
                                                    top: -2,
                                                    right: -2,
                                                    width: 14,
                                                    height: 14,
                                                    borderRadius: '50%',
                                                    backgroundColor: 'primary.main',
                                                    color: 'primary.contrastText',
                                                    fontSize: '0.65rem',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontWeight: 'bold',
                                                }}
                                            >
                                                {attachedFiles.length}
                                            </Box>
                                        )}
                                    </Box>
                                </Box>

                                {/* Voice Input Button - simplified */}
                                <Box
                                    onClick={isRecording ? stopRecording : startRecording}
                                    sx={{
                                        cursor: loading || transcribing ? 'not-allowed' : 'pointer',
                                        color: isRecording ? 'error.main' : 'text.secondary',
                                        opacity: (loading || transcribing) ? 0.5 : 1,
                                        pointerEvents: (loading || transcribing) ? 'none' : 'auto',
                                        '&:hover': { color: isRecording ? 'error.main' : 'text.primary' },
                                    }}
                                >
                                    {transcribing ? (
                                        <CircularProgress size={16} />
                                    ) : isRecording ? (
                                        <StopCircleIcon sx={{ fontSize: 20 }} />
                                    ) : (
                                        <MicIcon sx={{ fontSize: 20 }} />
                                    )}
                                </Box>
                            </Box>

                            {/* Right side: Send/Stop button - agent-chat-ui circular style */}
                            {loading ? (
                                <Box
                                    onClick={stopStreaming}
                                    sx={{
                                        width: 36,
                                        height: 36,
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: 'pointer',
                                        bgcolor: alpha(theme.palette.error.main, 0.1),
                                        color: 'error.main',
                                        '&:hover': {
                                            bgcolor: alpha(theme.palette.error.main, 0.2),
                                        },
                                    }}
                                >
                                    <StopIcon sx={{ fontSize: 18 }} />
                                </Box>
                            ) : (
                                <Box
                                    onClick={handleSendMessage}
                                    sx={{
                                        width: 36,
                                        height: 36,
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: inputMessage.trim() && selectedProvider && selectedModel ? 'pointer' : 'default',
                                        bgcolor: inputMessage.trim() && selectedProvider && selectedModel
                                            ? theme.palette.primary.main
                                            : alpha(theme.palette.action.disabled, 0.1),
                                        color: inputMessage.trim() && selectedProvider && selectedModel
                                            ? 'primary.contrastText'
                                            : 'text.disabled',
                                        transition: 'all 0.2s ease',
                                        '&:hover': inputMessage.trim() && selectedProvider && selectedModel ? {
                                            bgcolor: theme.palette.primary.dark,
                                            transform: 'scale(1.05)',
                                        } : {},
                                    }}
                                >
                                    <SendIcon sx={{ fontSize: 16 }} />
                                </Box>
                            )}
                        </Box>
                    </Box>
                </Box>

                {/* Subtle hint */}
                {inputMessage.trim() === '' && (
                    <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                            mt: 0.75,
                            display: { xs: 'none', sm: 'block' },
                            textAlign: 'center',
                            fontSize: '0.7rem',
                        }}
                    >
                        Enter to send, Shift+Enter for new line
                    </Typography>
                )}
            </Box>

            {/* Settings Menu */}
            <Menu
                anchorEl={settingsMenuAnchor}
                open={Boolean(settingsMenuAnchor)}
                onClose={() => {
                    setSettingsMenuAnchor(null);
                    setExpandedMenuSection(null);
                }}
                PaperProps={{
                    sx: {
                        minWidth: expandedMenuSection ? 350 : 200,
                        maxHeight: expandedMenuSection ? 600 : 400,
                        overflow: 'auto'
                    }
                }}
            >
                {/* Model Configuration Section */}
                {expandedMenuSection === 'model' ? (
                    <Box sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <IconButton
                                size="small"
                                onClick={() => setExpandedMenuSection(null)}
                                sx={{ mr: 1 }}
                            >
                                <ExpandMoreIcon sx={{ transform: 'rotate(90deg)' }} />
                            </IconButton>
                            <Typography variant="subtitle2" fontWeight="600">
                                Model Configuration
                            </Typography>
                        </Box>

                        {/* Provider Selection */}
                        <FormControl fullWidth sx={{ mb: 2 }} size="small">
                            <InputLabel>Provider</InputLabel>
                            <Select
                                value={selectedProvider || ''}
                                label="Provider"
                                onChange={(e) => {
                                    setSelectedProvider(e.target.value);
                                    setModels([]);
                                    setSelectedModel(null);
                                    setMessages([]);
                                    setError('');
                                }}
                                disabled={loading}
                            >
                                {providers.map((provider) => (
                                    <MenuItem key={provider.name} value={provider.name}>
                                        {provider.display_name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        {/* Model Filter and Selection */}
                        {models.length > 0 && (
                            <>
                                <TextField
                                    fullWidth
                                    placeholder="Filter models..."
                                    value={modelFilter}
                                    onChange={(e) => setModelFilter(e.target.value)}
                                    size="small"
                                    sx={{ mb: 2 }}
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <SearchIcon fontSize="small" />
                                            </InputAdornment>
                                        ),
                                        endAdornment: modelFilter && (
                                            <InputAdornment position="end">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => setModelFilter('')}
                                                >
                                                    <ClearIcon fontSize="small" />
                                                </IconButton>
                                            </InputAdornment>
                                        )
                                    }}
                                />

                                <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                                    <InputLabel>Model</InputLabel>
                                    <Select
                                        value={selectedModel?.id || ''}
                                        label="Model"
                                        onChange={(e) => {
                                            const model = models.find(m => m.id === e.target.value);
                                            if (model) {
                                                setSelectedModel(model);
                                                adjustSettingsForModel(model);
                                                setError('');
                                                setTimeout(() => chatInputRef.current?.focus(), 100);
                                            }
                                        }}
                                        disabled={loading}
                                    >
                                        {modelFilter && filteredModels.length === 0 ? (
                                            <MenuItem disabled>
                                                No models match "{modelFilter}"
                                            </MenuItem>
                                        ) : (
                                            (() => {
                                                const displayModels = modelFilter ? filteredModels : models;
                                                const uniqueModels = displayModels.map(m => m.id).includes(selectedModel?.id || '')
                                                    ? displayModels
                                                    : selectedModel
                                                        ? [selectedModel, ...displayModels]
                                                        : displayModels;

                                                return uniqueModels.map((model) => (
                                                    <MenuItem key={model.id} value={model.id}>
                                                        <Box>
                                                            <Typography variant="body2">{model.id}</Typography>
                                                            {model.owned_by && (
                                                                <Typography variant="caption" color="textSecondary">
                                                                    {model.owned_by}
                                                                </Typography>
                                                            )}
                                                        </Box>
                                                    </MenuItem>
                                                ));
                                            })()
                                        )}
                                    </Select>
                                </FormControl>
                            </>
                        )}

                        {/* Temperature */}
                        {isParameterSupported('temperature') && (
                            <Box sx={{ mb: 2 }}>
                                <Typography gutterBottom variant="body2">
                                    Temperature: {completionSettings.temperature}
                                </Typography>
                                <Slider
                                    value={completionSettings.temperature}
                                    onChange={(_, value) => setCompletionSettings(prev => ({ ...prev, temperature: value as number }))}
                                    min={0}
                                    max={2}
                                    step={0.1}
                                    size="small"
                                    marks={[
                                        { value: 0, label: '0' },
                                        { value: 0.7, label: '0.7' },
                                        { value: 1, label: '1' },
                                        { value: 1.5, label: '1.5' },
                                        { value: 2, label: '2' }
                                    ]}
                                    valueLabelDisplay="auto"
                                />
                            </Box>
                        )}

                        {/* Max Tokens */}
                        <TextField
                            fullWidth
                            label={getMaxTokensLabel()}
                            type="number"
                            size="small"
                            value={completionSettings.max_tokens}
                            onChange={(e) => setCompletionSettings(prev => ({ ...prev, max_tokens: parseInt(e.target.value) || 2048 }))}
                            inputProps={{ min: 1, max: 32768 }}
                            sx={{ mb: 2 }}
                        />

                        {/* Top P */}
                        {isParameterSupported('top_p') && (
                            <Box sx={{ mb: 2 }}>
                                <Typography gutterBottom variant="body2">
                                    Top P: {completionSettings.top_p}
                                </Typography>
                                <Slider
                                    value={completionSettings.top_p}
                                    onChange={(_, value) => setCompletionSettings(prev => ({ ...prev, top_p: value as number }))}
                                    min={0}
                                    max={1}
                                    step={0.05}
                                    size="small"
                                    marks={[
                                        { value: 0, label: '0' },
                                        { value: 0.5, label: '0.5' },
                                        { value: 1, label: '1' }
                                    ]}
                                    valueLabelDisplay="auto"
                                />
                            </Box>
                        )}

                        {/* Presence Penalty */}
                        {isParameterSupported('presence_penalty') && (
                            <Box sx={{ mb: 2 }}>
                                <Typography gutterBottom variant="body2">
                                    Presence Penalty: {completionSettings.presence_penalty}
                                </Typography>
                                <Slider
                                    value={completionSettings.presence_penalty}
                                    onChange={(_, value) => setCompletionSettings(prev => ({ ...prev, presence_penalty: value as number }))}
                                    min={-2}
                                    max={2}
                                    step={0.1}
                                    size="small"
                                    marks={[
                                        { value: -2, label: '-2' },
                                        { value: 0, label: '0' },
                                        { value: 2, label: '2' }
                                    ]}
                                    valueLabelDisplay="auto"
                                />
                            </Box>
                        )}

                        {/* Frequency Penalty */}
                        {isParameterSupported('frequency_penalty') && (
                            <Box sx={{ mb: 2 }}>
                                <Typography gutterBottom variant="body2">
                                    Frequency Penalty: {completionSettings.frequency_penalty}
                                </Typography>
                                <Slider
                                    value={completionSettings.frequency_penalty}
                                    onChange={(_, value) => setCompletionSettings(prev => ({ ...prev, frequency_penalty: value as number }))}
                                    min={-2}
                                    max={2}
                                    step={0.1}
                                    size="small"
                                    marks={[
                                        { value: -2, label: '-2' },
                                        { value: 0, label: '0' },
                                        { value: 2, label: '2' }
                                    ]}
                                    valueLabelDisplay="auto"
                                />
                            </Box>
                        )}

                        {/* Model Info */}
                        {selectedModel?.parameter_info && (
                            <Alert severity="info" sx={{ mt: 1 }}>
                                <Typography variant="caption">
                                    <strong>Model:</strong> {selectedModel.id}
                                    {selectedModel.parameter_info.unsupported_params.length > 0 && (
                                        <>
                                            <br />
                                            • Unsupported: {selectedModel.parameter_info.unsupported_params.join(', ')}
                                        </>
                                    )}
                                    {selectedModel.parameter_info.supports_reasoning && (
                                        <>
                                            <br />
                                            • Supports reasoning effort
                                        </>
                                    )}
                                </Typography>
                            </Alert>
                        )}

                        {/* Set as Default Buttons */}
                        <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                            <Button
                                size="small"
                                variant="contained"
                                onClick={() => {
                                    saveDefaultModel();
                                    setSettingsMenuAnchor(null);
                                }}
                                disabled={!selectedProvider || !selectedModel}
                                fullWidth
                            >
                                Set as Default
                            </Button>
                            <Button
                                size="small"
                                variant="outlined"
                                color="secondary"
                                onClick={() => {
                                    resetDefaultModel();
                                    setSettingsMenuAnchor(null);
                                }}
                                fullWidth
                            >
                                Clear Defaults
                            </Button>
                        </Box>

                        {(defaultModel?.provider || defaultModel?.modelId) && (
                            <Alert severity="info" sx={{ mt: 1 }}>
                                <Typography variant="caption">
                                    <strong>Current Defaults:</strong>
                                    {defaultModel?.provider && <><br />• Provider: {defaultModel.provider}</>}
                                    {defaultModel?.modelId && <><br />• Model: {defaultModel.modelId}</>}
                                </Typography>
                            </Alert>
                        )}
                        
                        {!defaultModel && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                No default model set. Save current selection as default to auto-load it next time.
                            </Typography>
                        )}

                        {/* Default Settings */}
                        <Box sx={{ mt: 2, pt: 2, borderTop: `1px solid ${alpha(theme.palette.divider, 0.2)}` }}>

                        </Box>
                    </Box>
                ) : (
                    [
                        <MenuItem key="model-config" onClick={() => setExpandedMenuSection('model')}>
                            <TuneIcon sx={{ mr: 1 }} />
                            Model Configuration
                            <ExpandMoreIcon sx={{ ml: 'auto' }} />
                        </MenuItem>,
                        <Divider key="divider" />,
                        <MenuItem key="clear-chat" onClick={() => { resetChat(); setSettingsMenuAnchor(null); }}>
                            <RefreshIcon sx={{ mr: 1 }} />
                            Clear Chat
                        </MenuItem>,
                        <MenuItem key="help" onClick={() => { setSettingsMenuAnchor(null); }}>
                            <HelpIcon sx={{ mr: 1 }} />
                            Help & Shortcuts
                        </MenuItem>,
                        <MenuItem key="about" onClick={() => { setSettingsMenuAnchor(null); }}>
                            <InfoIcon sx={{ mr: 1 }} />
                            About
                        </MenuItem>
                    ]
                )}
            </Menu>

            {/* AI Configuration Drawer */}
            <Drawer
                anchor="right"
                open={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                sx={{
                    '& .MuiDrawer-paper': {
                        width: { xs: '85%', sm: 400 },
                        maxWidth: { xs: '320px', sm: 'none' },
                        p: { xs: 1.5, sm: 2 },
                        borderRadius: { xs: '16px 0 0 16px', sm: 0 },
                        height: { xs: '100vh', sm: '100vh' },
                        boxShadow: { xs: '-4px 0 20px rgba(0,0,0,0.15)', sm: 'none' }
                    }
                }}
                ref={drawerRef}
            >
                <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" fontWeight="600" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <SettingsIcon color="primary" />
                            AI Configuration
                        </Typography>
                        <IconButton onClick={() => setSidebarOpen(false)}>
                            <ClearIcon />
                        </IconButton>
                    </Box>

                    {/* Model Configuration Section */}
                    <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" fontWeight="600" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                            <TuneIcon color="primary" fontSize="small" />
                            Model Configuration
                        </Typography>

                        {/* Provider Selection */}
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>Provider</InputLabel>
                            <Select
                                value={selectedProvider || ''}
                                label="Provider"
                                onChange={(e) => {
                                    setSelectedProvider(e.target.value);
                                    setModels([]);
                                    setSelectedModel(null);
                                    setMessages([]);
                                    setError('');
                                }}
                                disabled={loading}
                            >
                                {providers.map((provider) => (
                                    <MenuItem key={provider.name} value={provider.name}>
                                        {provider.display_name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        {/* Model Filter */}
                        {models.length > 0 && (
                            <TextField
                                fullWidth
                                placeholder="Filter models..."
                                value={modelFilter}
                                onChange={(e) => setModelFilter(e.target.value)}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <SearchIcon />
                                        </InputAdornment>
                                    ),
                                    endAdornment: modelFilter && (
                                        <InputAdornment position="end">
                                            <IconButton
                                                size="small"
                                                onClick={() => setModelFilter('')}
                                            >
                                                <ClearIcon />
                                            </IconButton>
                                        </InputAdornment>
                                    )
                                }}
                                sx={{ mb: 2 }}
                            />
                        )}

                        {/* Model Selection */}
                        {models.length > 0 && (
                            <FormControl fullWidth>
                                <InputLabel>Model</InputLabel>
                                <Select
                                    value={selectedModel?.id || ''}
                                    label="Model"
                                    onChange={(e) => {
                                        const model = models.find(m => m.id === e.target.value);
                                        if (model) {
                                            setSelectedModel(model);
                                            adjustSettingsForModel(model);
                                            setError('');
                                            setTimeout(() => chatInputRef.current?.focus(), 100);
                                        }
                                    }}
                                    disabled={loading}
                                >
                                    {modelFilter && filteredModels.length === 0 ? (
                                        <MenuItem disabled>
                                            No models match "{modelFilter}"
                                        </MenuItem>
                                    ) : (
                                        (() => {
                                            const displayModels = modelFilter ? filteredModels : models;
                                            // Always include selected model even if it doesn't match the filter
                                            const uniqueModels = displayModels.map(m => m.id).includes(selectedModel?.id || '')
                                                ? displayModels
                                                : selectedModel
                                                    ? [selectedModel, ...displayModels]
                                                    : displayModels;

                                            return uniqueModels.map((model) => (
                                                <MenuItem key={model.id} value={model.id}>
                                                    <Box>
                                                        <Typography variant="body2">{model.id}</Typography>
                                                        {model.owned_by && (
                                                            <Typography variant="caption" color="textSecondary">
                                                                {model.owned_by}
                                                            </Typography>
                                                        )}
                                                    </Box>
                                                </MenuItem>
                                            ));
                                        })()
                                    )}
                                </Select>
                            </FormControl>
                        )}

                        {/* Default Model Controls */}
                        <Box sx={{ mt: 2, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                            <Typography variant="body2" fontWeight="600" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                                <StarIcon fontSize="small" color={defaultModel?.provider === selectedProvider && defaultModel?.modelId === selectedModel?.id ? 'warning' : 'disabled'} />
                                Default Model
                            </Typography>
                            
                            {!selectedProvider || !selectedModel ? (
                                <Typography variant="caption" color="text.secondary">
                                    Select a provider and model first to manage default settings.
                                    <br />Provider: {selectedProvider || 'None'} | Model: {selectedModel?.id || 'None'}
                                </Typography>
                            ) : defaultModel ? (
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                                                    Current default: {defaultModel.provider}/{defaultModel.modelId}
                                                    {defaultModel.provider === selectedProvider && defaultModel.modelId === selectedModel.id && 
                                                        <Chip label="Active" size="small" color="warning" sx={{ ml: 1, height: 16 }} />
                                                    }
                                                </Typography>
                                                
                                                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                                    <Button
                                                        size="small"
                                                        variant="contained"
                                                        onClick={saveDefaultModel}
                                                        disabled={defaultModel.provider === selectedProvider && defaultModel.modelId === selectedModel.id}
                                                        sx={{ fontSize: '0.75rem', py: 0.5 }}
                                                    >
                                                        Update Default
                                                    </Button>
                                                    <Button
                                                        size="small"
                                                        variant="outlined"
                                                        color="error"
                                                        onClick={resetDefaultModel}
                                                        sx={{ fontSize: '0.75rem', py: 0.5 }}
                                                    >
                                                        Remove Default
                                                    </Button>
                                                </Box>
                                            </Box>
                                        ) : (
                                            <Box>
                                                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                                                    No default model set. Save current selection as default to auto-load it next time.
                                                </Typography>
                                                <Button
                                                    size="small"
                                                    variant="contained"
                                                    startIcon={<StarIcon />}
                                                    onClick={saveDefaultModel}
                                                    sx={{ fontSize: '0.75rem', py: 0.5 }}
                                                >
                                                    Save as Default
                                                </Button>
                                            </Box>
                                        )}
                        </Box>
                    </Box>

                    {/* Voice Mode Toggle */}
                    <Box sx={{ mb: 2, p: 1.5, borderRadius: 2, bgcolor: alpha(theme.palette.primary.main, 0.04), border: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={voiceModeEnabled}
                                    onChange={(e) => setVoiceModeEnabled(e.target.checked)}
                                    size="small"
                                />
                            }
                            label={
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <VolumeUpIcon fontSize="small" />
                                    <Typography variant="body2">Voice Mode</Typography>
                                </Box>
                            }
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4.5, mt: -0.5 }}>
                            Auto-read responses aloud
                        </Typography>
                        {isPlayingAudio && (
                            <Button size="small" onClick={stopAudioPlayback} sx={{ mt: 1, ml: 4 }}>
                                Stop Audio
                            </Button>
                        )}
                    </Box>

                    {/* Quick Actions Section */}
                    <Box sx={{ mt: 'auto' }}>
                        <Typography variant="subtitle1" fontWeight="600" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                            <IntegrationIcon color="primary" fontSize="small" />
                            Quick Actions
                        </Typography>

                        {/* Quick Create Actions */}
                        <Box sx={{ mb: 2 }}>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                <Tooltip title="Generate image from text">
                                    <span>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            startIcon={<ImageIcon />}
                                            onClick={() => {
                                                const prompt = inputMessage.trim() || 'a beautiful landscape';
                                                setInputMessage(`Generate an image of ${prompt}`);
                                                setSidebarOpen(false);
                                                setTimeout(() => chatInputRef.current?.focus(), 100);
                                            }}
                                            disabled={loading}
                                            fullWidth
                                        >
                                            Generate Image
                                        </Button>
                                    </span>
                                </Tooltip>
                                <Tooltip title="Convert text to speech">
                                    <span>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            startIcon={<MicIcon />}
                                            onClick={() => {
                                                const text = inputMessage.trim() || 'Hello, this is a test of text to speech';
                                                setInputMessage(`Read this aloud: ${text}`);
                                                setSidebarOpen(false);
                                                setTimeout(() => chatInputRef.current?.focus(), 100);
                                            }}
                                            disabled={loading}
                                            fullWidth
                                        >
                                            Text to Speech
                                        </Button>
                                    </span>
                                </Tooltip>
                                <Tooltip title="Create short video">
                                    <span>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            startIcon={<VideoIcon />}
                                            onClick={() => {
                                                const topic = inputMessage.trim() || 'artificial intelligence';
                                                setInputMessage(`Create a short video about ${topic}`);
                                                setSidebarOpen(false);
                                                setTimeout(() => chatInputRef.current?.focus(), 100);
                                            }}
                                            disabled={loading}
                                            fullWidth
                                        >
                                            Create Video
                                        </Button>
                                    </span>
                                </Tooltip>
                            </Box>
                            <Divider sx={{ my: 2 }} />
                        </Box>

                        {/* Clear Chat Action */}
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={() => {
                                resetChat();
                                setSidebarOpen(false);
                            }}
                            disabled={loading}
                            fullWidth
                        >
                            Clear Chat
                        </Button>
                    </Box>
                </Box>
            </Drawer>
            </Box>
        </Box>
    );
};

export default Chat;
