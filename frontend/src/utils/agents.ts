import { DEFAULT_MODEL_PRICING } from '../constants/agents';

export const formatTimestamp = (timestamp: string) =>
    new Date(timestamp).toLocaleString();

export const formatDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const duration = end.getTime() - start.getTime();
    return `${(duration / 1000).toFixed(2)}s`;
};

export const calculateTokens = (text: string) =>
    Math.ceil(text.length / 4);

export const calculateCost = (tokens: number, model: string) => {
    const rate = DEFAULT_MODEL_PRICING[model] ?? 0.00001;
    return (tokens * rate).toFixed(6);
};

export const enhanceMessageContent = (content: string) => {
    if (!content) {
        return '';
    }

    let formatted = content.replace(/\r\n/g, '\n').trim();

    formatted = formatted.replace(
        /^([a-z0-9_]+\(.*?\))/i,
        (match) => `\`${match}\``
    );
    formatted = formatted.replace(
        /Here are some of the ([^:]+):\s*/i,
        'Here are some of the $1:\n\n'
    );

    if (formatted.includes(' - ')) {
        formatted = formatted.replace(
            /([.!?])\s+(?=[A-Z][^:\n]+ - )/g,
            '$1\n'
        );
        formatted = formatted.replace(
            /(^|\n)(?!- )([A-Z][^:\n]+ - )/g,
            (_match, prefix, item) => `${prefix}- ${item}`
        );
    }

    formatted = formatted.replace(/\n{3,}/g, '\n\n');
    return formatted.trim();
};

