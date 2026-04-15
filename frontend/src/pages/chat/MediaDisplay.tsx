import React from 'react';
import {
  Box,
  Card,
  CardMedia,
  CardActions,
  Typography,
  IconButton,
  Chip,
  Tooltip
} from '@mui/material';
import {
  Download as DownloadIcon,
  OpenInNew as OpenInNewIcon,
  Image as ImageIcon,
  Audiotrack as AudioIcon,
  Videocam as VideoIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { MessageContent } from '../../types/anyllm';

// Import highlight.js styles for code syntax highlighting
import 'highlight.js/styles/github.css';

// Helper function to parse and render slash commands
const renderTextWithCommands = (text: string) => {
  // Match slash commands at the start of text: /command followed by space or text
  const commandRegex = /^(\/\w+)(\s+.*)?$/;
  const match = text.match(commandRegex);

  if (match) {
    const command = match[1]; // e.g., "/search"
    const restOfText = match[2] || ''; // e.g., " elon"

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        <Chip
          label={command}
          size="small"
          color="primary"
          sx={{
            fontFamily: 'monospace',
            fontWeight: 600,
            fontSize: '0.875rem',
            height: '24px'
          }}
        />
        {restOfText && (
          <Typography component="span" sx={{ fontSize: '0.95rem' }}>
            {restOfText.trim()}
          </Typography>
        )}
      </Box>
    );
  }

  // No command found, return null to use default markdown rendering
  return null;
};

interface MediaDisplayProps {
  content: MessageContent;
  showDownload?: boolean;
}

export const MediaDisplay: React.FC<MediaDisplayProps> = ({
  content,
  showDownload = true
}) => {
  if (!content.url) return null;

  const handleDownload = () => {
    if (!content.url) return;
    const link = document.createElement('a');
    link.href = content.url;
    link.download = content.filename || `media.${content.type}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleOpenInNew = () => {
    window.open(content.url, '_blank');
  };

  const getFileIcon = () => {
    switch (content.type) {
      case 'image':
        return <ImageIcon />;
      case 'audio':
        return <AudioIcon />;
      case 'video':
        return <VideoIcon />;
      default:
        return <ImageIcon />;
    }
  };

  const renderMediaContent = () => {
    switch (content.type) {
      case 'image':
        return (
          <CardMedia
            component="img"
            image={content.url}
            alt={content.alt_text || 'Uploaded image'}
            sx={{
              maxHeight: 400,
              width: '100%',
              objectFit: 'contain'
            }}
          />
        );

      case 'audio':
        return (
          <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <AudioIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <audio
              controls
              style={{ width: '100%', maxWidth: '400px' }}
              src={content.url}
            >
              Your browser does not support the audio element.
            </audio>
          </Box>
        );

      case 'video':
        return (
          <Box sx={{ p: 2 }}>
            <video
              controls
              style={{
                width: '100%',
                maxHeight: '400px',
                borderRadius: '8px'
              }}
              src={content.url}
            >
              Your browser does not support the video element.
            </video>
          </Box>
        );

      default:
        return (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="text.secondary">
              Unsupported media type: {content.type}
            </Typography>
          </Box>
        );
    }
  };

  return (
    <Card
      sx={{
        maxWidth: 600,
        margin: '8px 0',
        border: '1px solid',
        borderColor: 'grey.200'
      }}
    >
      {renderMediaContent()}

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getFileIcon()}
          <Typography variant="caption" color="text.secondary">
            {content.filename}
          </Typography>
          {content.size && (
            <Chip
              label={`${(content.size / 1024 / 1024).toFixed(1)} MB`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>

        {showDownload && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Open in new tab">
              <IconButton size="small" onClick={handleOpenInNew}>
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download">
              <IconButton size="small" onClick={handleDownload}>
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </CardActions>
    </Card>
  );
};

interface MessageContentDisplayProps {
  content: MessageContent[];
}

export const MessageContentDisplay: React.FC<MessageContentDisplayProps> = ({ content }) => {
  return (
    <Box>
      {content.map((item, index) => (
        <Box key={index}>
          {item.type === 'text' ? (
            <>
              {/* Check if text contains a slash command at the start */}
              {renderTextWithCommands(item.text || '') || (
                <Box sx={{
                  mb: 1,
                  '& h1, & h2, & h3, & h4, & h5, & h6': {
                    marginTop: '1em',
                    marginBottom: '0.5em',
                    fontWeight: 'bold',
                    lineHeight: 1.2,
                    color: 'text.primary'
                  },
                  '& h1': { fontSize: '1.5em' },
                  '& h2': { fontSize: '1.25em' },
                  '& h3': { fontSize: '1.125em' },
                  '& h4': { fontSize: '1em' },
                  '& h5': { fontSize: '0.875em' },
                  '& h6': { fontSize: '0.75em' },
                  '& p': {
                    marginBottom: '0.75em',
                    lineHeight: 1.6,
                    wordBreak: 'break-word'
                  },
                  '& ul, & ol': {
                    marginBottom: '0.75em',
                    paddingLeft: '1.5em'
                  },
                  '& li': {
                    marginBottom: '0.25em',
                    lineHeight: 1.4
                  },
                  '& blockquote': {
                    borderLeft: '4px solid',
                    borderLeftColor: 'primary.main',
                    paddingLeft: '1em',
                    margin: '1em 0',
                    fontStyle: 'italic',
                    backgroundColor: 'grey.50',
                    padding: '0.5em 1em',
                    borderRadius: '0 4px 4px 0'
                  },
                  '& code': {
                    backgroundColor: 'grey.100',
                    padding: '0.125em 0.25em',
                    borderRadius: '3px',
                    fontFamily: 'monospace',
                    fontSize: '0.875em'
                  },
                  '& pre': {
                    backgroundColor: 'grey.900',
                    color: 'grey.100',
                    padding: '1em',
                    borderRadius: '4px',
                    overflow: 'auto',
                    margin: '1em 0',
                    '& code': {
                      backgroundColor: 'transparent',
                      color: 'inherit',
                      padding: 0
                    }
                  },
                  '& table': {
                    borderCollapse: 'collapse',
                    width: '100%',
                    margin: '1em 0',
                    border: '1px solid',
                    borderColor: 'grey.300'
                  },
                  '& th, & td': {
                    border: '1px solid',
                    borderColor: 'grey.300',
                    padding: '0.5em',
                    textAlign: 'left'
                  },
                  '& th': {
                    backgroundColor: 'grey.100',
                    fontWeight: 'bold'
                  },
                  '& a': {
                    color: 'primary.main',
                    textDecoration: 'underline',
                    '&:hover': {
                      textDecoration: 'none'
                    }
                  },
                  '& strong, & b': {
                    fontWeight: 'bold'
                  },
                  '& em, & i': {
                    fontStyle: 'italic'
                  },
                  '& del': {
                    textDecoration: 'line-through'
                  }
                }}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight]}
                    components={{
                      // Custom link component to open in new tab
                      a: ({ href, children, ...props }) => (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          {...props}
                        >
                          {children}
                        </a>
                      ),
                      // Custom code block component
                      code: ({ node, className, children, ...props }) => {
                        const isInline = !node || node.tagName !== 'pre';
                        if (isInline) {
                          return (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                        return (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        );
                      }
                    }}
                  >
                    {item.text || ''}
                  </ReactMarkdown>
                </Box>
              )}
            </>
          ) : (
            <MediaDisplay content={item} />
          )}
        </Box>
      ))}
    </Box>
  );
};