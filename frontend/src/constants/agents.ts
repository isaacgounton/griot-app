import { Provider, Model } from '../types/anyllm';

export const DEFAULT_PROVIDERS: Provider[] = [
    { name: 'openai', display_name: 'OpenAI' },
];

export const DEFAULT_MODELS: Model[] = [
    { id: 'gpt-4o-mini', object: 'model' },
    { id: 'gpt-4o', object: 'model' },
    { id: 'gpt-4', object: 'model' },
    { id: 'gpt-3.5-turbo', object: 'model' },
];

export const DEFAULT_MODEL_PRICING: Record<string, number> = {
    'gpt-4o-mini': 0.00015,
    'gpt-4o': 0.000004,
};

