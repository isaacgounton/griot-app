import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Box, Typography, Paper, Alert, CircularProgress } from '@mui/material';

interface TextOverlayOptions {
  duration: number;
  font_size: number;
  font_color: string;
  box_color: string;
  box_opacity: number;
  box_padding: number;  // Changed from boxborderw to match new service
  position: string;
  y_offset: number;
  line_spacing: number;
  auto_wrap: boolean;
  max_chars_per_line: number;
}

interface VideoPreviewWithOverlayProps {
  videoUrl: string;
  text: string;
  options: TextOverlayOptions;
}

const VideoPreviewWithOverlay: React.FC<VideoPreviewWithOverlayProps> = ({
  videoUrl,
  text,
  options
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [videoLoaded, setVideoLoaded] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoDimensions, setVideoDimensions] = useState({ width: 0, height: 0 });

  // Intelligent text wrapping matching FFmpeg backend logic
  const intelligentTextWrapping = (text: string, maxWidthChars: number = 25, fontSize: number = 48): string => {
    // Character width estimation based on font size (matching backend logic)
    const avgCharWidth = fontSize * 0.6;
    const maxPixelWidth = maxWidthChars * avgCharWidth;

    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine: string[] = [];
    let currentWidth = 0;

    for (const word of words) {
      // Estimate visual width of word (matching backend algorithm)
      let wordWidth = 0;
      for (const char of word) {
        if ('mwMW@%'.includes(char)) {
          wordWidth += avgCharWidth * 1.3; // Wide characters
        } else if ('il1|!'.includes(char)) {
          wordWidth += avgCharWidth * 0.4; // Narrow characters
        } else if ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'.includes(char)) {
          wordWidth += avgCharWidth * 1.1; // Capital letters
        } else {
          wordWidth += avgCharWidth; // Normal characters
        }
      }

      const spaceWidth = currentLine.length > 0 ? avgCharWidth * 0.3 : 0;

      if (currentWidth + wordWidth + spaceWidth > maxPixelWidth && currentLine.length > 0) {
        lines.push(currentLine.join(' '));
        currentLine = [word];
        currentWidth = wordWidth;
      } else {
        currentLine.push(word);
        currentWidth += wordWidth + spaceWidth;
      }
    }

    if (currentLine.length > 0) {
      lines.push(currentLine.join(' '));
    }

    return lines.join('\\n'); // Return with FFmpeg-style newlines
  };

  // Draw text overlay on canvas
  const drawOverlay = useCallback(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    if (!canvas || !video || !videoLoaded || !text.trim()) {
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set canvas size to match video
    const videoWidth = video.videoWidth || video.offsetWidth;
    const videoHeight = video.videoHeight || video.offsetHeight;

    if (videoWidth && videoHeight) {
      canvas.width = videoWidth;
      canvas.height = videoHeight;

      // Scale canvas to fit container while maintaining aspect ratio
      const containerWidth = containerRef.current?.offsetWidth || 400;
      const aspectRatio = videoWidth / videoHeight;
      const displayWidth = Math.min(containerWidth, 800);
      const displayHeight = displayWidth / aspectRatio;

      canvas.style.width = `${displayWidth}px`;
      canvas.style.height = `${displayHeight}px`;
    }

    // Set font
    const fontSize = options.font_size || 48;
    ctx.font = `${fontSize}px Arial, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'alphabetic'; // Changed to match FFmpeg behavior

    // Handle text wrapping using FFmpeg-style logic
    const maxChars = options.max_chars_per_line || 25;
    const wrappedText = options.auto_wrap ? intelligentTextWrapping(text, maxChars, fontSize) : text;
    const lines = wrappedText.split('\\n').map(line => line.replace(/\\\\/g, '\\')); // Convert FFmpeg \\n to \n for canvas

    // Calculate position using FFmpeg-style coordinates
    let x = canvas.width / 2;
    let y = canvas.height / 2;

    const position = options.position || 'bottom-center';
    const yOffset = options.y_offset || 50;

    // Use FFmpeg position mapping
    switch (position) {
      case 'top-left':
        x = 30;
        y = 30 + fontSize;
        ctx.textAlign = 'left';
        break;
      case 'top-center':
        x = canvas.width / 2;
        y = yOffset + fontSize;
        ctx.textAlign = 'center';
        break;
      case 'top-right':
        x = canvas.width - 30;
        y = 30 + fontSize;
        ctx.textAlign = 'right';
        break;
      case 'center-left':
        x = 30;
        y = canvas.height / 2;
        ctx.textAlign = 'left';
        break;
      case 'center':
        x = canvas.width / 2;
        y = canvas.height / 2;
        ctx.textAlign = 'center';
        break;
      case 'center-right':
        x = canvas.width - 30;
        y = canvas.height / 2;
        ctx.textAlign = 'right';
        break;
      case 'bottom-left':
        x = 30;
        y = canvas.height - yOffset;
        ctx.textAlign = 'left';
        break;
      case 'bottom-center':
        x = canvas.width / 2;
        y = canvas.height - yOffset;
        ctx.textAlign = 'center';
        break;
      case 'bottom-right':
        x = canvas.width - 30;
        y = canvas.height - yOffset;
        ctx.textAlign = 'right';
        break;
    }

    // Calculate line spacing to match FFmpeg
    const lineSpacing = options.line_spacing || 8;
    const actualLineHeight = fontSize + lineSpacing;

    // Adjust starting Y for multi-line text
    const totalHeight = lines.length * actualLineHeight;
    let startY = y;

    if (lines.length > 1) {
      if (position.includes('top')) {
        startY = y; // Start from calculated position
      } else if (position.includes('bottom')) {
        startY = y - totalHeight + actualLineHeight; // Adjust up for multiple lines
      } else {
        startY = y - (totalHeight / 2) + (actualLineHeight / 2); // Center vertically
      }
    }

    lines.forEach((line, index) => {
      const lineY = startY + (index * actualLineHeight);

      // Draw background box matching FFmpeg boxborderw behavior
      if (options.box_color && options.box_opacity > 0) {
        const textMetrics = ctx.measureText(line);
        const textWidth = textMetrics.width;

        // FFmpeg box_padding is padding around text (support both old and new parameter names)
        const padding = options.box_padding || (options as any).boxborderw || 60;

        let boxX = x - textWidth / 2 - padding / 2;
        if (ctx.textAlign === 'left') {
          boxX = x - padding / 2;
        } else if (ctx.textAlign === 'right') {
          boxX = x - textWidth - padding / 2;
        }

        ctx.fillStyle = hexToRgba(options.box_color, options.box_opacity);
        ctx.fillRect(
          boxX,
          lineY - fontSize - 5, // Adjust to match FFmpeg box positioning
          textWidth + padding,
          fontSize + 15
        );
      }

      // Draw text
      ctx.fillStyle = options.font_color || 'white';
      ctx.fillText(line, x, lineY);
    });
  }, [videoLoaded, text, options]);

  // Convert hex color to rgba
  const hexToRgba = (hex: string, opacity: number): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (result) {
      const r = parseInt(result[1], 16);
      const g = parseInt(result[2], 16);
      const b = parseInt(result[3], 16);
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    return `rgba(0, 0, 0, ${opacity})`;
  };

  // Handle video load
  const handleVideoLoad = () => {
    const video = videoRef.current;
    if (!video) return;

    setVideoLoaded(true);
    setVideoError(null);
    setVideoDimensions({
      width: video.videoWidth,
      height: video.videoHeight
    });

    // Initial overlay draw
    setTimeout(drawOverlay, 100);
  };

  // Handle video error
  const handleVideoError = () => {
    setVideoError('Failed to load video. Please check the URL.');
    setVideoLoaded(false);
  };

  // Update overlay when options change
  useEffect(() => {
    if (videoLoaded) {
      drawOverlay();
    }
  }, [drawOverlay, videoLoaded]);

  // Handle video time update for continuous overlay
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      drawOverlay();
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('seeked', handleTimeUpdate);
    video.addEventListener('play', handleTimeUpdate);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('seeked', handleTimeUpdate);
      video.removeEventListener('play', handleTimeUpdate);
    };
  }, [drawOverlay]);

  if (!videoUrl.trim()) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center', bgcolor: '#f8fafc' }}>
        <Typography variant="body2" color="text.secondary">
          Enter a video URL to see the preview
        </Typography>
      </Paper>
    );
  }

  return (
    <Box ref={containerRef}>
      <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        🎬 Live Preview
      </Typography>

      <Paper sx={{ p: 2, bgcolor: '#f8fafc', position: 'relative' }}>
        {!videoLoaded && !videoError && (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
            <CircularProgress size={40} />
          </Box>
        )}

        {videoError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {videoError}
          </Alert>
        )}

        <Box sx={{ position: 'relative', display: 'inline-block' }}>
          <video
            ref={videoRef}
            src={videoUrl}
            onLoadedData={handleVideoLoad}
            onError={handleVideoError}
            controls
            style={{
              width: '100%',
              maxWidth: '800px',
              height: 'auto',
              borderRadius: '8px',
              display: videoLoaded ? 'block' : 'none'
            }}
          />

          <canvas
            ref={canvasRef}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              pointerEvents: 'none',
              borderRadius: '8px',
              display: videoLoaded ? 'block' : 'none'
            }}
          />
        </Box>

        {videoLoaded && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Resolution: {videoDimensions.width} × {videoDimensions.height}
            {text.trim() && (
              <> • Preview updates in real-time as you change settings</>
            )}
          </Typography>
        )}

        {videoLoaded && !text.trim() && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Enter text above to see the overlay preview
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

export default VideoPreviewWithOverlay;