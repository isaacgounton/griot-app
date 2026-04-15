// Video Creation Components
export { default as VideoCreatorTab } from './tabs/VideoCreatorTab';
export { default as ScriptEditor } from './ScriptEditor';
export { default as JobStatusDisplay } from './JobStatusDisplay';

// Re-export types for convenience
export type {
  VideoScene,
  VideoCreationRequest,
  VideoCreationResult,
  VoiceInfo,
  VoiceProvider,
  ContentCreationJobStatus,
  ContentCreationJobResult,
  VideoCreatorFormState,
  MediaSettings,
  VideoSettings,
  ImageProviderSettings,
  ContentCreationUIState,
} from '../../types/contentCreation';

// Re-export hooks for convenience
export {
  useVideoCreation,
  useVoices,
} from '../../hooks/useContentCreation';
