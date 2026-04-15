import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  Grid,
  Fade,
  Grow,
  Chip,
  useTheme,
  alpha,
  Paper,
  Stack,
  IconButton,
  Tooltip,
  Slide,
  Zoom,
  Collapse,
} from '@mui/material';
import {
  VideoLibrary as _VideoLibrary,
  Security,
  ArrowForward,
  PlayCircle,
  AutoAwesome,
  Analytics,
  Share as _Share,
  PhotoLibrary as _PhotoLibrary,
  Code,
  RocketLaunch,
  VerifiedUser,
  Psychology,
  Architecture,
  Api,
  Storage,
  Transform as _Transform,
  Movie,
  ContentCopy,
  CheckCircle,
  Star,
  Celebration as _Celebration,
  ElectricBolt,
  Menu,
  KeyboardArrowDown,
} from '@mui/icons-material';

// Custom particle animation component
interface Particle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
}

const ParticleBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(0);
  const particlesRef = useRef<Particle[]>([]);
  const theme = useTheme();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    const createParticles = () => {
      const colors = [theme.palette.primary.main, '#6366F1', theme.palette.secondary.main];
      particlesRef.current = Array.from({ length: 50 }, (_, i) => ({
        id: i,
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 3 + 1,
        opacity: Math.random() * 0.5 + 0.1,
        color: colors[Math.floor(Math.random() * colors.length)],
      }));
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current.forEach(particle => {
        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Bounce off edges
        if (particle.x <= 0 || particle.x >= canvas.width) particle.vx *= -1;
        if (particle.y <= 0 || particle.y >= canvas.height) particle.vy *= -1;

        // Draw particle
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color + Math.floor(particle.opacity * 255).toString(16).padStart(2, '0');
        ctx.fill();
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    resizeCanvas();
    createParticles();
    animate();

    window.addEventListener('resize', resizeCanvas);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [theme.palette.primary.main, theme.palette.secondary.main]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        pointerEvents: 'none',
      }}
    />
  );
};

// Scroll Progress Indicator
const ScrollProgress: React.FC = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollTop;
      const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      const scroll = totalScroll / windowHeight;
      setProgress(scroll * 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: `${progress}%`,
        height: 4,
        background: `linear-gradient(90deg, #6366F1 0%, #EC4899 50%, #10B981 100%)`,
        zIndex: 1001,
        transition: 'width 0.1s ease-out',
        borderRadius: '0 2px 2px 0',
        boxShadow: `0 0 10px ${alpha('#6366F1', 0.5)}`,
      }}
    />
  );
};

// Top Navigation Bar (visible at page top)
const TopNavBar: React.FC<{ onLoginClick: () => void }> = ({ onLoginClick }) => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setMobileMenuOpen(false);
    }
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        transform: scrolled ? 'translateY(-100%)' : 'translateY(0)',
        opacity: scrolled ? 0 : 1,
      }}
    >
      <Container maxWidth="xl">
        <Paper
          sx={{
            mt: 2,
            px: 4,
            py: 2,
            borderRadius: 6,
            background: `rgba(255, 255, 255, 0.95)`,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${alpha('#6366F1', 0.1)}`,
            boxShadow: `0 8px 32px ${alpha('#000', 0.08)}`,
          }}
        >
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            {/* Logo */}
            <Typography
              variant="h5"
              sx={{
                fontWeight: 800,
                background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                cursor: 'pointer',
              }}
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            >
              Griot
            </Typography>

            {/* Navigation Links */}
            <Stack direction="row" spacing={1} sx={{ display: { xs: 'none', md: 'flex' } }}>
              {[
                { label: 'Demo', id: 'demo', icon: <PlayCircle sx={{ fontSize: 18 }} /> },
                { label: 'Features', id: 'features', icon: <AutoAwesome sx={{ fontSize: 18 }} /> },
                { label: 'Technical', id: 'technical', icon: <Architecture sx={{ fontSize: 18 }} /> },
              ].map((item) => (
                <Button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  startIcon={item.icon}
                  sx={{
                    color: 'text.secondary',
                    fontWeight: 600,
                    textTransform: 'none',
                    px: 3,
                    py: 1.5,
                    borderRadius: 4,
                    fontSize: '1rem',
                    '&:hover': {
                      bgcolor: alpha('#6366F1', 0.1),
                      color: '#6366F1',
                      transform: 'translateY(-1px)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Stack>

            {/* CTA Button */}
            <Button
              onClick={onLoginClick}
              variant="contained"
              startIcon={<RocketLaunch />}
              sx={{
                px: 4,
                py: 1.5,
                borderRadius: 4,
                background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
                fontWeight: 700,
                textTransform: 'none',
                fontSize: '1rem',
                boxShadow: `0 4px 16px ${alpha('#6366F1', 0.3)}`,
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 24px ${alpha('#6366F1', 0.4)}`,
                },
                transition: 'all 0.3s ease',
                display: { xs: 'none', sm: 'flex' },
              }}
            >
              Get Started
            </Button>

            {/* Mobile Menu Button */}
            <IconButton
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              sx={{
                display: { xs: 'flex', md: 'none' },
                color: '#6366F1',
                p: 1.5,
              }}
            >
              <Menu />
            </IconButton>
          </Stack>
        </Paper>

        {/* Mobile Menu Dropdown */}
        <Collapse in={mobileMenuOpen}>
          <Paper
            sx={{
              mt: 1,
              p: 3,
              borderRadius: 6,
              background: `rgba(255, 255, 255, 0.98)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${alpha('#6366F1', 0.1)}`,
              boxShadow: `0 8px 32px ${alpha('#000', 0.12)}`,
            }}
          >
            <Stack spacing={2}>
              {[
                { label: 'Demo', id: 'demo', icon: <PlayCircle sx={{ fontSize: 18 }} /> },
                { label: 'Features', id: 'features', icon: <AutoAwesome sx={{ fontSize: 18 }} /> },
                { label: 'Technical', id: 'technical', icon: <Architecture sx={{ fontSize: 18 }} /> },
              ].map((item) => (
                <Button
                  key={item.id}
                  onClick={() => scrollToSection(item.id)}
                  startIcon={item.icon}
                  fullWidth
                  sx={{
                    justifyContent: 'flex-start',
                    color: 'text.primary',
                    fontWeight: 600,
                    textTransform: 'none',
                    py: 2,
                    px: 3,
                    borderRadius: 4,
                    fontSize: '1rem',
                    '&:hover': {
                      bgcolor: alpha('#6366F1', 0.1),
                      color: '#6366F1',
                      transform: 'translateX(4px)',
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  {item.label}
                </Button>
              ))}

              {/* Mobile CTA Button */}
              <Button
                onClick={() => {
                  onLoginClick();
                  setMobileMenuOpen(false);
                }}
                variant="contained"
                startIcon={<RocketLaunch />}
                fullWidth
                sx={{
                  mt: 2,
                  py: 2,
                  borderRadius: 4,
                  background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
                  fontWeight: 700,
                  textTransform: 'none',
                  fontSize: '1rem',
                  boxShadow: `0 4px 16px ${alpha('#6366F1', 0.3)}`,
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 24px ${alpha('#6366F1', 0.4)}`,
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                Get Started
              </Button>
            </Stack>
          </Paper>
        </Collapse>
      </Container>
    </Box>
  );
};

// Enhanced Floating Navigation Component (appears on scroll)
const FloatingNav: React.FC<{ onLoginClick: () => void }> = ({ onLoginClick }) => {
  const [scrolled, setScrolled] = useState(false);
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setNavOpen(false);
    }
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        opacity: scrolled ? 1 : 0,
        visibility: scrolled ? 'visible' : 'hidden',
      }}
    >
      <Paper
        sx={{
          px: 4,
          py: 2,
          borderRadius: 8,
          background: `rgba(255, 255, 255, 0.95)`,
          backdropFilter: 'blur(20px)',
          border: `1px solid ${alpha('#6366F1', 0.2)}`,
          boxShadow: `0 20px 40px ${alpha('#000', 0.1)}`,
          display: 'flex',
          alignItems: 'center',
          gap: 3,
        }}
      >
        <Typography
          variant="h6"
          sx={{
            fontWeight: 800,
            background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mr: 2,
          }}
        >
          Griot
        </Typography>

        <Stack direction="row" spacing={2} sx={{ display: { xs: 'none', md: 'flex' } }}>
          {[
            { label: 'Demo', id: 'demo' },
            { label: 'Features', id: 'features' },
            { label: 'Tech', id: 'technical' },
          ].map((item) => (
            <Button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              sx={{
                color: 'text.secondary',
                fontWeight: 600,
                textTransform: 'none',
                px: 3,
                py: 1,
                borderRadius: 6,
                '&:hover': {
                  bgcolor: alpha('#6366F1', 0.1),
                  color: '#6366F1',
                },
                transition: 'all 0.3s ease',
              }}
            >
              {item.label}
            </Button>
          ))}
        </Stack>

        <Button
          onClick={onLoginClick}
          variant="contained"
          size="small"
          sx={{
            px: 4,
            py: 1.5,
            borderRadius: 6,
            background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
            fontWeight: 700,
            textTransform: 'none',
            boxShadow: `0 8px 20px ${alpha('#6366F1', 0.3)}`,
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: `0 12px 30px ${alpha('#6366F1', 0.4)}`,
            },
            transition: 'all 0.3s ease',
          }}
        >
          Get Started
        </Button>

        <IconButton
          onClick={() => setNavOpen(!navOpen)}
          sx={{
            display: { xs: 'flex', md: 'none' },
            color: '#6366F1',
          }}
        >
          <Menu />
        </IconButton>
      </Paper>

      {/* Mobile Menu */}
      <Collapse in={navOpen}>
        <Paper
          sx={{
            mt: 2,
            p: 3,
            borderRadius: 6,
            background: `rgba(255, 255, 255, 0.98)`,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${alpha('#6366F1', 0.2)}`,
            boxShadow: `0 20px 40px ${alpha('#000', 0.15)}`,
          }}
        >
          <Stack spacing={2}>
            {[
              { label: 'Demo', id: 'demo' },
              { label: 'Features', id: 'features' },
              { label: 'Technical', id: 'technical' },
            ].map((item) => (
              <Button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                fullWidth
                sx={{
                  justifyContent: 'flex-start',
                  color: 'text.primary',
                  fontWeight: 600,
                  textTransform: 'none',
                  py: 2,
                  borderRadius: 4,
                  '&:hover': {
                    bgcolor: alpha('#6366F1', 0.1),
                    color: '#6366F1',
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Stack>
        </Paper>
      </Collapse>
    </Box>
  );
};

const Home: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [copiedCode, setCopiedCode] = useState('');
  const [currentFeature, setCurrentFeature] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Mouse tracking for enhanced effects
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const codeExamples = [
    {
      title: 'AI Chat with Tools',
      language: 'javascript',
      description: 'Chat with an AI that can search, generate images, create audio, and more',
      code: `// Chat with AI — tools are auto-discovered from skills
const response = await fetch('/api/v1/anyllm/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'user', content: 'Search the web for latest AI news' }
    ],
    tools: await fetch('/api/v1/tools').then(r => r.json()),
    tool_choice: 'auto',
    stream: true
  })
});

// AI automatically calls web_search, generate_image,
// text_to_speech, transcribe_media, and 9 more tools`,
      id: 'chat',
    },
    {
      title: 'Generate AI Video',
      language: 'curl',
      description: 'Create videos from topics with AI scripts, TTS voiceover, and stock footage',
      code: `curl -X POST "https://your-server.com/api/v1/videos/topic-to-video" \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "The future of artificial intelligence",
    "duration": 60,
    "voice_provider": "kokoro",
    "voice_name": "af_bella",
    "resolution": "1080x1920",
    "auto_script": true,
    "stock_footage": true
  }'

# Response: {
#   "job_id": "abc-123",
#   "status": "processing",
#   "estimated_time": "2-3 minutes"
# }`,
      id: 'video',
    },
    {
      title: 'Text to Speech',
      language: 'curl',
      description: 'Convert text to natural speech with Kokoro, Edge TTS, and more',
      code: `# Generate speech with Kokoro TTS (built-in, no external API)
curl -X POST "https://your-server.com/api/v1/audio/speech" \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "Welcome to Griot!",
    "voice": "af_bella",
    "provider": "kokoro",
    "response_format": "mp3"
  }'

# Returns job_id → poll for S3 audio URL
# Providers: kokoro (built-in), edge, kitten
# 30+ natural voices available

# Or use the chat — just ask:
# "Read this text aloud: Hello world"
# The AI calls text_to_speech automatically`,
      id: 'tts',
    },
    {
      title: 'Image Generation',
      language: 'curl',
      description: 'Generate images from text prompts with Pollinations AI',
      code: `# Generate an image from a text description
curl -X POST "https://your-server.com/api/v1/pollinations/image/generate" \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "A futuristic city at sunset, cyberpunk style",
    "width": 1920,
    "height": 1080,
    "model": "flux",
    "enhance": true
  }'

# Returns job_id → poll for generated image URL
# Models auto-discovered from Pollinations API
# Also supports image-to-image editing

# Or just ask in the chat:
# "Generate an image of a mountain landscape"
# The AI calls generate_image automatically`,
      id: 'image',
    },
  ];

  // Auto-rotate code demos
  useEffect(() => {
    const codeExamplesLength = codeExamples.length;
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % codeExamplesLength);
    }, 4000);
    return () => clearInterval(interval);
  }, [codeExamples.length]);

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(''), 2000);
  };

  const mainFeatures = [
    {
      icon: <Psychology sx={{ fontSize: 48 }} />,
      title: 'AI Chat with Tools',
      description: 'Chat with an AI assistant that can search the web, generate images, create speech, transcribe audio, analyze images, extract YouTube transcripts, and more — 13 tools auto-discovered from modular skills.',
      color: '#6366F1',
      bgColor: '#EEF2FF',
      features: ['Web & News Search', 'Image Generation', 'Vision Analysis', 'Text to Speech', 'Media Transcription'],
      gradient: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
    },
    {
      icon: <Movie sx={{ fontSize: 48 }} />,
      title: 'AI Video Creation',
      description: 'Generate videos from topics with AI-written scripts, TTS voiceover, stock footage, captions, and transitions. Full pipeline from text prompt to finished video with S3 delivery.',
      color: '#EC4899',
      bgColor: '#FDF2F8',
      features: ['Topic-to-Video Pipeline', 'AI Script Generation', 'Stock Footage Integration', 'Multi-Style Captions', 'Audio Mixing'],
      gradient: 'linear-gradient(135deg, #EC4899 0%, #F472B6 100%)',
    },
    {
      icon: <Api sx={{ fontSize: 48 }} />,
      title: 'Multi-Provider AI',
      description: 'Connect to OpenAI, Anthropic, Google, DeepSeek, Groq, Mistral, and Pollinations through a single AnyLLM interface. Switch providers per request with automatic fallback.',
      color: '#10B981',
      bgColor: '#ECFDF5',
      features: ['AnyLLM Interface', 'OpenAI & Anthropic', 'Google & DeepSeek', 'Pollinations AI', 'Provider Fallback'],
      gradient: 'linear-gradient(135deg, #10B981 0%, #34D399 100%)',
    },
    {
      icon: <Code sx={{ fontSize: 48 }} />,
      title: 'Media Processing',
      description: 'Full media pipeline: image generation and editing, audio transcription, format conversion, video captions, text overlays, audio mixing, and document-to-markdown conversion.',
      color: '#F59E0B',
      bgColor: '#FFFBEB',
      features: ['Image Gen & Editing', 'Audio Transcription', 'Format Conversion', 'Video Captions', 'Document Parsing'],
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%)',
    },
    {
      icon: <AutoAwesome sx={{ fontSize: 48 }} />,
      title: 'Social Media Automation',
      description: 'Post to TikTok, Instagram, YouTube, LinkedIn, and X through Postiz integration. Schedule posts, attach media, generate AI captions, and manage all platforms from one place.',
      color: '#8B5CF6',
      bgColor: '#F5F3FF',
      features: ['Multi-Platform Posting', 'Post Scheduling', 'AI Caption Generation', 'Media Attachments', 'Postiz Integration'],
      gradient: 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)',
    },
    {
      icon: <Analytics sx={{ fontSize: 48 }} />,
      title: 'Developer Platform',
      description: 'RESTful API with OpenAPI docs, API key authentication, async job queues, PostgreSQL database, Redis caching, S3 storage, and a full admin dashboard.',
      color: '#06B6D4',
      bgColor: '#ECFEFF',
      features: ['API Key Auth', 'Async Job Queues', 'PostgreSQL + Redis', 'S3 Cloud Storage', 'Admin Dashboard'],
      gradient: 'linear-gradient(135deg, #06B6D4 0%, #22D3EE 100%)',
    },
  ];

  /* stats - reserved for future use
  const stats = [
    { number: '13+', label: 'AI Chat Tools', icon: <Psychology sx={{ fontSize: 32 }} />, color: '#6366F1' },
    { number: '30+', label: 'API Endpoints', icon: <Code sx={{ fontSize: 32 }} />, color: '#EC4899' },
    { number: '7+', label: 'LLM Providers', icon: <Science sx={{ fontSize: 32 }} />, color: '#10B981' },
    { number: '3', label: 'TTS Engines', icon: <Mic sx={{ fontSize: 32 }} />, color: '#F59E0B' },
  ]; */

  const technicalFeatures = [
    {
      icon: <ElectricBolt sx={{ fontSize: 32 }} />,
      title: 'Async Job Queues',
      description: 'Background processing with Redis-powered job queues and real-time status polling',
      color: '#6366F1',
    },
    {
      icon: <Security sx={{ fontSize: 32 }} />,
      title: 'API Key Auth',
      description: 'Secure API key authentication with per-user keys, usage tracking, and admin controls',
      color: '#EF4444',
    },
    {
      icon: <Storage sx={{ fontSize: 32 }} />,
      title: 'S3 Cloud Storage',
      description: 'All generated media uploaded to S3-compatible storage with persistent URL caching',
      color: '#10B981',
    },
    {
      icon: <Api sx={{ fontSize: 32 }} />,
      title: 'REST API + Docs',
      description: 'Full REST API with interactive OpenAPI documentation at /docs',
      color: '#8B5CF6',
    },
    {
      icon: <Architecture sx={{ fontSize: 32 }} />,
      title: 'Docker Ready',
      description: 'Containerized with Docker Compose — PostgreSQL, Redis, and API in one stack',
      color: '#06B6D4',
    },
    {
      icon: <Analytics sx={{ fontSize: 32 }} />,
      title: 'Modular Skills',
      description: 'Drop a skill file into the skills directory and it auto-loads into the AI chat',
      color: '#F59E0B',
    },
  ];

  const testimonials = [
    {
      name: 'Sarah Chen',
      role: 'Content Creator',
      company: 'TechCorp',
      content: 'The topic-to-video pipeline is a game changer. I can go from an idea to a finished video with captions in minutes.',
      avatar: '👩‍💻',
      rating: 5,
    },
    {
      name: 'Marcus Johnson',
      role: 'Content Creator',
      company: 'CreativeStudio',
      content: 'The built-in TTS voices sound natural, and being able to post directly to social media from the dashboard saves so much time.',
      avatar: '🎨',
      rating: 5,
    },
    {
      name: 'Elena Rodriguez',
      role: 'CTO',
      company: 'StartupXYZ',
      content: 'Clean REST API with great docs. I integrated image generation and TTS into my app in under an hour.',
      avatar: '👩‍💼',
      rating: 5,
    },
  ];

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', overflow: 'hidden', position: 'relative' }}>
      {/* Scroll Progress Indicator */}
      <ScrollProgress />

      {/* Top Navigation Bar */}
      <TopNavBar onLoginClick={() => navigate('/login')} />
      {/* Floating Navigation */}
      <FloatingNav onLoginClick={() => navigate('/login')} />

      {/* Animated Particle Background */}
      <ParticleBackground />

      {/* Mouse Follower Effect */}
      <Box
        sx={{
          position: 'fixed',
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${alpha('#6366F1', 0.05)} 0%, transparent 70%)`,
          pointerEvents: 'none',
          zIndex: 0,
          transform: `translate(${mousePosition.x - 150}px, ${mousePosition.y - 150}px)`,
          transition: 'transform 0.1s ease-out',
          filter: 'blur(20px)',
        }}
      />

      {/* Gradient Background Overlays */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: -2,
          background: `
            radial-gradient(circle at 20% 20%, ${alpha('#6366F1', 0.15)} 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, ${alpha('#EC4899', 0.15)} 0%, transparent 50%),
            radial-gradient(circle at 40% 60%, ${alpha('#10B981', 0.1)} 0%, transparent 50%)
          `,
        }}
      />

      {/* Hero Section */}
      <Box
        id="hero"
        data-animate
        sx={{
          pt: { xs: 12, md: 16 },
          pb: { xs: 8, md: 16 },
          position: 'relative',
          background: `linear-gradient(135deg, ${alpha('#6366F1', 0.02)} 0%, ${alpha('#EC4899', 0.02)} 100%)`,
        }}
      >
        <Container maxWidth="xl">
          <Fade in timeout={1000}>
            <Container maxWidth="xl">
              <Grid container spacing={8} alignItems="center">
                {/* Left Column - Main Content */}
                <Grid item xs={12} lg={7}>
                  <Box>
                    {/* Announcement Badge */}
                    <Box
                      sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        mb: 4,
                        px: 3,
                        py: 1,
                        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1))',
                        border: '1px solid rgba(99, 102, 241, 0.2)',
                        borderRadius: '50px',
                        color: '#6366F1',
                        fontWeight: 600,
                        fontSize: '0.9rem',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 8px 25px rgba(99, 102, 241, 0.15)',
                        },
                        transition: 'all 0.3s ease',
                      }}
                    >
                      <ElectricBolt sx={{ fontSize: 16, mr: 1 }} />
                      New: AI Chat with 13+ Built-in Tools
                    </Box>

                    {/* Main Headline */}
                    <Typography
                      variant="h1"
                      sx={{
                        fontSize: { xs: '3rem', sm: '4rem', md: '5rem' },
                        fontWeight: 900,
                        lineHeight: 1.1,
                        mb: 3,
                      }}
                    >
                      <Box
                        sx={{
                          background: 'linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%)',
                          backgroundClip: 'text',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                        }}
                      >
                        Where Intelligence
                      </Box>
                      <Box
                        sx={{
                          display: 'block',
                          background: 'linear-gradient(135deg, #6366F1, #EC4899)',
                          backgroundClip: 'text',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                        }}
                      >
                        Meets Creative Automation
                      </Box>
                    </Typography>

                    {/* Description */}
                    <Typography
                      variant="body1"
                      sx={{
                        fontSize: '1.2rem',
                        lineHeight: 1.7,
                        color: 'text.secondary',
                        mb: 6,
                        maxWidth: 600,
                      }}
                    >
                      Generate videos from topics, create images, convert text to speech, search the web,
                      transcribe media, and automate social posting — all from one AI-powered dashboard.
                    </Typography>

                    {/* CTA Buttons */}
                    <Stack
                      direction={{ xs: 'column', sm: 'row' }}
                      spacing={3}
                      sx={{ mb: 6 }}
                    >
                      <Button
                        variant="contained"
                        size="large"
                        onClick={() => navigate('/login')}
                        endIcon={<ArrowForward />}
                        sx={{
                          px: 6,
                          py: 3,
                          fontSize: '1.1rem',
                          fontWeight: 600,
                          borderRadius: 2,
                          textTransform: 'none',
                          background: 'linear-gradient(135deg, #6366F1, #EC4899)',
                          boxShadow: '0 10px 30px rgba(99, 102, 241, 0.3)',
                          minWidth: 200,
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 15px 40px rgba(99, 102, 241, 0.4)',
                          },
                          transition: 'all 0.3s ease',
                        }}
                      >
                        Get Started Free
                      </Button>
                      <Button
                        variant="outlined"
                        size="large"
                        href="/docs"
                        target="_blank"
                        sx={{
                          px: 6,
                          py: 3,
                          fontSize: '1.1rem',
                          fontWeight: 600,
                          borderRadius: 2,
                          textTransform: 'none',
                          borderWidth: 2,
                          borderColor: '#6366F1',
                          color: '#6366F1',
                          minWidth: 200,
                          textDecoration: 'none',
                          '&:hover': {
                            borderColor: '#EC4899',
                            color: '#EC4899',
                            background: 'rgba(236, 72, 153, 0.05)',
                            transform: 'translateY(-2px)',
                          },
                          transition: 'all 0.3s ease',
                        }}
                      >
                        View Documentation
                      </Button>
                    </Stack>

                    {/* Social Proof */}
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          color: 'text.secondary',
                          mb: 3,
                          fontWeight: 500,
                        }}
                      >
                        🚀 Join a growing community of developers and creators building with Griot
                      </Typography>

                      {/* Trust Indicators */}
                      <Stack
                        direction="row"
                        spacing={2}
                        alignItems="center"
                        sx={{
                          opacity: 0.8,
                        }}
                      >
                        <Chip
                          icon={<VerifiedUser />}
                          label="Open API"
                          size="small"
                          sx={{
                            bgcolor: alpha('#6366F1', 0.1),
                            color: '#6366F1',
                            fontWeight: 600,
                            border: `1px solid ${alpha('#6366F1', 0.2)}`,
                          }}
                        />
                        <Chip
                          icon={<Security />}
                          label="Self-Hostable"
                          size="small"
                          sx={{
                            bgcolor: alpha('#10B981', 0.1),
                            color: '#10B981',
                            fontWeight: 600,
                            border: `1px solid ${alpha('#10B981', 0.2)}`,
                          }}
                        />
                      </Stack>
                    </Box>
                  </Box>
                </Grid>

                {/* Right Column - Stats Cards */}
                <Grid item xs={12} lg={5}>
                  <Box
                    sx={{
                      position: 'relative',
                      display: { xs: 'none', lg: 'block' },
                    }}
                  >
                    {/* Main Stats Card */}
                    <Paper
                      elevation={24}
                      sx={{
                        p: 4,
                        borderRadius: 4,
                        background: 'linear-gradient(135deg, #ffffff, #f8f9fa)',
                        border: '1px solid rgba(99, 102, 241, 0.1)',
                        position: 'relative',
                        overflow: 'hidden',
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          height: 4,
                          background: 'linear-gradient(90deg, #6366F1, #EC4899, #10B981)',
                        },
                      }}
                    >
                      {/* Code Example Header */}
                      <Box sx={{ mb: 4 }}>
                        <Typography
                          variant="h6"
                          sx={{
                            fontWeight: 700,
                            mb: 2,
                            color: 'text.primary',
                            fontSize: '0.9rem',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                          }}
                        >
                          Trusted by Leading Companies
                        </Typography>
                        <Stack
                          direction="row"
                          spacing={3}
                          alignItems="center"
                          sx={{ mb: 3 }}
                        >
                          {['TechCorp', 'StartupXYZ', 'CreativeStudio'].map((company) => (
                            <Typography
                              key={company}
                              variant="body2"
                              sx={{
                                fontWeight: 700,
                                color: 'text.secondary',
                                fontSize: '0.95rem',
                                opacity: 0.8,
                              }}
                            >
                              {company}
                            </Typography>
                          ))}
                        </Stack>
                      </Box>

                      {/* Code Preview */}
                      <Box
                        sx={{
                          background: '#0D1117',
                          borderRadius: 2,
                          p: 3,
                          mb: 4,
                        }}
                      >
                        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#FF5F57' }} />
                          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#FFBD2E' }} />
                          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#28CA42' }} />
                        </Box>
                        <Typography
                          variant="body2"
                          sx={{
                            color: '#E6EDF3',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            lineHeight: 1.5,
                          }}
                        >
                          <Box component="span" sx={{ color: '#FF7B72' }}>const</Box>{' '}
                          <Box component="span" sx={{ color: '#79C0FF' }}>agent</Box>
                          {' = '}
                          <Box component="span" sx={{ color: '#FFA657' }}>await</Box>
                          {' '}
                          <Box component="span" sx={{ color: '#D2A8FF' }}>createAgent</Box>
                          ({'{'}
                          <br />
                          {'  '}
                          <Box component="span" sx={{ color: '#A5D6FF' }}>type</Box>
                          :{' '}
                          <Box component="span" sx={{ color: '#A5D6FF' }}>'research'</Box>
                          ,
                          <br />
                          {'  '}
                          <Box component="span" sx={{ color: '#A5D6FF' }}>memory</Box>
                          :{' '}
                          <Box component="span" sx={{ color: '#79C0FF' }}>true</Box>
                          <br />
                          {'})'};
                        </Typography>
                      </Box>

                      {/* Feature Pills */}
                      <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 4 }}>
                        {[
                          { label: '🤖 AI Agents', color: '#6366F1' },
                          { label: '🧠 Memory', color: '#EC4899' },
                          { label: '🔧 MCP Tools', color: '#10B981' },
                          { label: '⚡ Real-time', color: '#F59E0B' },
                        ].map((feature, index) => (
                          <Chip
                            key={index}
                            label={feature.label}
                            size="small"
                            sx={{
                              background: `${feature.color}15`,
                              color: feature.color,
                              fontWeight: 600,
                              fontSize: '0.75rem',
                              border: `1px solid ${feature.color}30`,
                            }}
                          />
                        ))}
                      </Stack>

                      {/* Stats Grid */}
                      <Grid container spacing={2}>
                        {[
                          { number: '6+', label: 'AI Agent Types', color: '#6366F1' },
                          { number: '40+', label: 'MCP Tools', color: '#EC4899' },
                          { number: '100+', label: 'AI Models', color: '#10B981' },
                          { number: '99.9%', label: 'Uptime', color: '#F59E0B' },
                        ].map((stat, index) => (
                          <Grid item xs={6} key={index}>
                            <Box
                              sx={{
                                p: 2,
                                borderRadius: 2,
                                background: `${stat.color}08`,
                                border: `1px solid ${stat.color}20`,
                                textAlign: 'center',
                                transition: 'all 0.3s ease',
                                '&:hover': {
                                  transform: 'translateY(-2px)',
                                  background: `${stat.color}15`,
                                  boxShadow: `0 8px 20px ${stat.color}25`,
                                },
                              }}
                            >
                              <Typography
                                variant="h5"
                                sx={{
                                  fontWeight: 800,
                                  color: stat.color,
                                  mb: 0.5,
                                  fontSize: '1.5rem',
                                }}
                              >
                                {stat.number}
                              </Typography>
                              <Typography
                                variant="caption"
                                sx={{
                                  color: 'text.secondary',
                                  fontWeight: 600,
                                  fontSize: '0.75rem',
                                  lineHeight: 1.2,
                                }}
                              >
                                {stat.label}
                              </Typography>
                            </Box>
                          </Grid>
                        ))}
                      </Grid>
                    </Paper>

                    {/* Floating Elements */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -20,
                        right: -20,
                        width: 100,
                        height: 100,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.1))',
                        animation: 'float 6s ease-in-out infinite',
                      }}
                    />
                    <Box
                      sx={{
                        position: 'absolute',
                        bottom: -30,
                        left: -30,
                        width: 120,
                        height: 120,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(245, 158, 11, 0.1))',
                        animation: 'float 8s ease-in-out infinite reverse',
                      }}
                    />
                  </Box>
                </Grid>
              </Grid>
            </Container>
          </Fade>

          {/* Add floating animation */}
          {/* Using a plain <style> tag instead of styled-jsx attributes (jsx/global)
              because styled-jsx is not configured in this Vite project. */}
          <style>{`
            @keyframes float {
              0%, 100% { transform: translateY(0px) rotate(0deg); }
              50% { transform: translateY(-20px) rotate(10deg); }
            }
          `}</style>

          {/* Hero section ends here - stats are now in the right column card */}
        </Container>
      </Box>

      {/* Interactive Code Demo Section */}
      <Box
        id="demo"
        data-animate
        sx={{
          py: { xs: 8, md: 16 },
          background: `linear-gradient(135deg, ${alpha('#6366F1', 0.02)} 0%, ${alpha('#10B981', 0.02)} 100%)`,
        }}
      >
        <Container maxWidth="xl">
          <Box textAlign="center" mb={{ xs: 4, md: 12 }}>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', sm: '3rem', md: '4rem' },
                fontWeight: 800,
                mb: 4,
                background: `linear-gradient(135deg, #6366F1 0%, #10B981 100%)`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              See It In Action
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: 'text.secondary',
                maxWidth: 800,
                mx: 'auto',
                lineHeight: 1.7,
                fontSize: '1.2rem',
                fontWeight: 400,
              }}
            >
              Powerful APIs that are incredibly easy to use. Get started in minutes with our comprehensive documentation and real-world examples.
            </Typography>
          </Box>

          <Grid container spacing={{ xs: 3, sm: 6 }} alignItems="stretch">
            <Grid item xs={12} lg={5}>
              <Stack spacing={{ xs: 2, sm: 3 }}>
                {codeExamples.map((example, index) => (
                  <Slide key={index} direction="right" in timeout={1000 + index * 200}>
                    <Paper
                      onClick={() => setCurrentFeature(index)}
                      sx={{
                        p: { xs: 2, sm: 4 },
                        borderRadius: 4,
                        cursor: 'pointer',
                        border: `3px solid ${currentFeature === index ? '#6366F1' : 'transparent'}`,
                        background: currentFeature === index
                          ? `linear-gradient(135deg, ${alpha('#6366F1', 0.1)} 0%, ${alpha('#EC4899', 0.05)} 100%)`
                          : alpha(theme.palette.background.paper, 0.7),
                        backdropFilter: 'blur(20px)',
                        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                        position: 'relative',
                        overflow: 'hidden',
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: `0 20px 40px ${alpha('#6366F1', 0.15)}`,
                          border: `3px solid ${alpha('#6366F1', 0.5)}`,
                        },
                        '&::before': currentFeature === index ? {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          height: 4,
                          background: 'linear-gradient(90deg, #6366F1, #EC4899)',
                        } : {},
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                        <Box
                          sx={{
                            width: 60,
                            height: 60,
                            borderRadius: 2,
                            background: currentFeature === index
                              ? 'linear-gradient(135deg, #6366F1, #EC4899)'
                              : alpha('#6366F1', 0.1),
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}
                        >
                          <Code sx={{
                            color: currentFeature === index ? 'white' : '#6366F1',
                            fontSize: 28,
                          }} />
                        </Box>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography
                            variant="h6"
                            sx={{
                              fontWeight: 700,
                              color: currentFeature === index ? '#6366F1' : 'text.primary',
                              mb: 1,
                            }}
                          >
                            {example.title}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'text.secondary',
                              mb: 2,
                              lineHeight: 1.5,
                            }}
                          >
                            {example.description}
                          </Typography>
                          <Chip
                            label={example.language.toUpperCase()}
                            size="small"
                            sx={{
                              bgcolor: currentFeature === index ? alpha('#6366F1', 0.2) : alpha('#6366F1', 0.1),
                              color: '#6366F1',
                              fontWeight: 600,
                              fontSize: '0.75rem',
                            }}
                          />
                        </Box>
                      </Box>
                    </Paper>
                  </Slide>
                ))}
              </Stack>
            </Grid>

            <Grid item xs={12} lg={7}>
              <Slide direction="left" in timeout={1500}>
                <Paper
                  sx={{
                    borderRadius: 6,
                    background: '#0D1117',
                    border: `2px solid ${alpha('#6366F1', 0.3)}`,
                    overflow: 'hidden',
                    position: 'relative',
                    boxShadow: `0 25px 50px ${alpha('#000', 0.3)}`,
                  }}
                >
                  {/* Enhanced Code Header */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      px: 4,
                      py: 3,
                      background: `linear-gradient(135deg, #161B22 0%, #21262D 100%)`,
                      borderBottom: `1px solid ${alpha('#6366F1', 0.2)}`,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#FF5F57' }} />
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#FFBD2E' }} />
                        <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#28CA42' }} />
                      </Box>
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#8B949E',
                          fontFamily: 'Monaco, "Cascadia Code", monospace',
                          fontWeight: 600,
                        }}
                      >
                        {codeExamples[currentFeature].title}
                      </Typography>
                    </Box>
                    <Tooltip title={copiedCode === codeExamples[currentFeature].id ? '✅ Copied!' : 'Copy code'}>
                      <IconButton
                        size="small"
                        onClick={() => copyCode(codeExamples[currentFeature].code, codeExamples[currentFeature].id)}
                        sx={{
                          color: '#8B949E',
                          '&:hover': {
                            color: '#6366F1',
                            bgcolor: alpha('#6366F1', 0.1),
                          },
                        }}
                      >
                        {copiedCode === codeExamples[currentFeature].id ? <CheckCircle /> : <ContentCopy />}
                      </IconButton>
                    </Tooltip>
                  </Box>

                  {/* Enhanced Code Content */}
                  <Box
                    component="pre"
                    sx={{
                      p: 4,
                      margin: 0,
                      color: '#E6EDF3',
                      fontSize: '0.95rem',
                      fontFamily: 'Monaco, "Cascadia Code", "Fira Code", monospace',
                      lineHeight: 1.7,
                      overflow: 'auto',
                      maxHeight: 500,
                      minHeight: 400,
                      background: `linear-gradient(135deg, #0D1117 0%, #161B22 100%)`,
                      // Syntax highlighting styles
                      '& .keyword': { color: '#FF7B72', fontWeight: 600 },
                      '& .string': { color: '#A5D6FF' },
                      '& .comment': { color: '#8B949E', fontStyle: 'italic' },
                      '& .number': { color: '#79C0FF' },
                      '& .operator': { color: '#FF7B72' },
                    }}
                  >
                    {codeExamples[currentFeature].code}
                  </Box>
                </Paper>
              </Slide>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Enhanced Main Features Section */}
      <Container maxWidth="xl" sx={{ py: { xs: 8, md: 20 } }}>
        <Box id="features" data-animate textAlign="center" mb={{ xs: 4, md: 12 }}>
          <Typography
            variant="h2"
            sx={{
              fontSize: { xs: '2.5rem', sm: '3.5rem', md: '4rem' },
              fontWeight: 800,
              mb: 4,
              background: `linear-gradient(135deg, #EC4899 0%, #6366F1 50%, #10B981 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Complete AI Platform
          </Typography>
          <Typography
            variant="h5"
            sx={{
              color: 'text.secondary',
              maxWidth: 900,
              mx: 'auto',
              lineHeight: 1.6,
              fontSize: '1.2rem',
              fontWeight: 400,
            }}
          >
            Everything you need to create AI-powered content.
            From intelligent agents with persistent memory to advanced media creation and enterprise-grade infrastructure.
          </Typography>
        </Box>

        <Grid container spacing={{ xs: 2, sm: 4 }}>
          {mainFeatures.map((feature, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Grow in timeout={1000 + index * 200}>
                <Paper
                  sx={{
                    p: { xs: 3, sm: 6 },
                    height: '100%',
                    borderRadius: 6,
                    border: `2px solid ${alpha(feature.color, 0.15)}`,
                    background: `linear-gradient(135deg, ${alpha(feature.bgColor, 0.4)} 0%, ${alpha(feature.bgColor, 0.1)} 100%)`,
                    transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    cursor: 'pointer',
                    '&:hover': {
                      transform: 'translateY(-12px) scale(1.02)',
                      boxShadow: `0 30px 80px ${alpha(feature.color, 0.25)}`,
                      border: `2px solid ${alpha(feature.color, 0.4)}`,
                      '& .feature-icon': {
                        transform: 'scale(1.2) rotate(10deg)',
                      },
                      '& .feature-gradient': {
                        opacity: 0.8,
                        transform: 'scale(1.2)',
                      },
                      '& .feature-content': {
                        transform: 'translateY(-2px)',
                      },
                      '& .feature-badge': {
                        opacity: 1,
                        transform: 'translateX(0)',
                      },
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: 5,
                      background: feature.gradient,
                    },
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: `linear-gradient(45deg, transparent 30%, ${alpha(feature.color, 0.05)} 50%, transparent 70%)`,
                      transform: 'translateX(-100%)',
                      transition: 'transform 0.6s',
                    },
                    '&:hover::after': {
                      transform: 'translateX(100%)',
                    },
                  }}
                >
                  {/* Background Gradient Overlay */}
                  <Box
                    className="feature-gradient"
                    sx={{
                      position: 'absolute',
                      top: -50,
                      right: -50,
                      width: 200,
                      height: 200,
                      borderRadius: '50%',
                      background: feature.gradient,
                      opacity: 0.1,
                      transition: 'all 0.4s ease',
                    }}
                  />

                  {/* New! Badge */}
                  <Box
                    className="feature-badge"
                    sx={{
                      position: 'absolute',
                      top: 20,
                      right: 20,
                      opacity: 0,
                      transform: 'translateX(20px)',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <Chip
                      label="Popular"
                      size="small"
                      sx={{
                        bgcolor: feature.color,
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '0.7rem',
                        height: 24,
                        '& .MuiChip-label': { px: 1 },
                      }}
                    />
                  </Box>

                  <Stack spacing={4} height="100%" position="relative" zIndex={1} className="feature-content" sx={{ transition: 'transform 0.3s ease' }}>
                    <Box
                      className="feature-icon"
                      sx={{
                        width: 100,
                        height: 100,
                        borderRadius: 4,
                        background: feature.gradient,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        transition: 'all 0.4s ease',
                        boxShadow: `0 10px 30px ${alpha(feature.color, 0.3)}`,
                      }}
                    >
                      {feature.icon}
                    </Box>

                    <Box>
                      <Typography
                        variant="h4"
                        sx={{
                          fontWeight: 800,
                          mb: 3,
                          color: 'text.primary',
                          fontSize: { xs: '1.5rem', md: '1.8rem' },
                        }}
                      >
                        {feature.title}
                      </Typography>
                      <Typography
                        variant="body1"
                        sx={{
                          color: 'text.secondary',
                          lineHeight: 1.7,
                          mb: 4,
                          fontSize: '1.1rem',
                        }}
                      >
                        {feature.description}
                      </Typography>
                    </Box>

                    <Stack spacing={2} sx={{ mt: 'auto' }}>
                      {feature.features.map((item, idx) => (
                        <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              background: feature.gradient,
                            }}
                          />
                          <Typography
                            variant="body2"
                            sx={{
                              color: 'text.secondary',
                              fontWeight: 500,
                              fontSize: '0.95rem',
                            }}
                          >
                            {item}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Stack>
                </Paper>
              </Grow>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Technical Features with Enhanced Design */}
      <Box
        id="technical"
        data-animate
        sx={{
          py: { xs: 8, md: 16 },
          background: `linear-gradient(135deg, ${alpha('#0F172A', 0.05)} 0%, ${alpha('#1E293B', 0.05)} 100%)`,
        }}
      >
        <Container maxWidth="lg">
          <Box textAlign="center" mb={{ xs: 4, md: 12 }}>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 800,
                mb: 4,
                fontSize: { xs: '1.75rem', sm: '2rem', md: '3rem' },
                background: `linear-gradient(135deg, #0F172A 0%, #334155 100%)`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Built for Scale & Performance
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: 'text.secondary',
                maxWidth: 700,
                mx: 'auto',
                lineHeight: 1.7,
                fontSize: '1.1rem',
              }}
            >
              Enterprise-grade infrastructure designed for high-performance applications with real-time processing and global scale.
            </Typography>
          </Box>

          <Grid container spacing={{ xs: 2, sm: 4 }}>
            {technicalFeatures.map((feature, index) => (
              <Grid item xs={6} sm={6} md={4} key={index}>
                <Fade in timeout={1000 + index * 150}>
                  <Card
                    sx={{
                      p: { xs: 2, sm: 4 },
                      height: '100%',
                      textAlign: 'center',
                      borderRadius: 4,
                      background: `linear-gradient(135deg, ${alpha(feature.color, 0.05)} 0%, ${alpha(feature.color, 0.02)} 100%)`,
                      backdropFilter: 'blur(20px)',
                      border: `2px solid ${alpha(feature.color, 0.1)}`,
                      transition: 'all 0.4s ease',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: `0 20px 40px ${alpha(feature.color, 0.2)}`,
                        border: `2px solid ${alpha(feature.color, 0.3)}`,
                      },
                    }}
                  >
                    <Box
                      sx={{
                        color: feature.color,
                        mb: 3,
                        display: 'flex',
                        justifyContent: 'center',
                      }}
                    >
                      <Box
                        sx={{
                          width: 60,
                          height: 60,
                          borderRadius: 2,
                          background: `linear-gradient(135deg, ${feature.color}, ${alpha(feature.color, 0.7)})`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                        }}
                      >
                        {feature.icon}
                      </Box>
                    </Box>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 700,
                        mb: 2,
                        fontSize: '1.1rem',
                      }}
                    >
                      {feature.title}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ lineHeight: 1.6 }}
                    >
                      {feature.description}
                    </Typography>
                  </Card>
                </Fade>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Enhanced Testimonials Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 8, md: 16 } }}>
        <Box textAlign="center" mb={8}>
          <Chip
            label="✨ Customer Love"
            sx={{
              mb: 4,
              px: 3,
              py: 1,
              fontSize: '1rem',
              fontWeight: 600,
              background: `linear-gradient(135deg, ${alpha('#EC4899', 0.15)}, ${alpha('#6366F1', 0.15)})`,
              color: '#EC4899',
              border: `2px solid ${alpha('#EC4899', 0.2)}`,
            }}
          />
          <Typography
            variant="h3"
            sx={{
              fontWeight: 800,
              mb: 3,
              background: `linear-gradient(135deg, #EC4899 0%, #6366F1 100%)`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontSize: { xs: '2rem', md: '3rem' },
            }}
          >
            Loved by Developers & Creators
          </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'text.secondary',
              maxWidth: 600,
              mx: 'auto',
              lineHeight: 1.6,
              fontSize: '1.2rem',
            }}
          >
            See what our community is saying about Griot
          </Typography>
        </Box>

        <Grid container spacing={{ xs: 2, sm: 4 }}>
          {testimonials.map((testimonial, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Fade in timeout={1200 + index * 200}>
                <Card
                  sx={{
                    p: { xs: 3, sm: 4 },
                    height: '100%',
                    borderRadius: 6,
                    border: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.background.paper, 0.9)} 100%)`,
                    backdropFilter: 'blur(20px)',
                    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: `0 25px 50px ${alpha(theme.palette.common.black, 0.15)}`,
                      border: `2px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                    },
                  }}
                >
                  {/* Decorative Quote */}
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 10,
                      right: 20,
                      fontSize: '4rem',
                      fontFamily: 'Georgia, serif',
                      color: alpha(theme.palette.primary.main, 0.1),
                      lineHeight: 1,
                      pointerEvents: 'none',
                      zIndex: 1,
                    }}
                  >
                    "
                  </Box>

                  <Stack spacing={3} height="100%" sx={{ position: 'relative', zIndex: 2 }}>
                    {/* Star Rating */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <Star
                          key={i}
                          sx={{
                            color: '#FFD700',
                            fontSize: 20,
                            filter: 'drop-shadow(0 2px 4px rgba(255,215,0,0.3))',
                          }}
                        />
                      ))}
                    </Box>

                    {/* Testimonial Content */}
                    <Typography
                      variant="body1"
                      sx={{
                        flex: 1,
                        fontStyle: 'italic',
                        lineHeight: 1.7,
                        color: 'text.primary',
                        fontSize: '1.1rem',
                        fontWeight: 500,
                        position: 'relative',
                        pl: 3,
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          left: 0,
                          top: 0,
                          bottom: 0,
                          width: 4,
                          background: `linear-gradient(135deg, #6366F1, #EC4899)`,
                          borderRadius: 2,
                        },
                      }}
                    >
                      "{testimonial.content}"
                    </Typography>

                    {/* Author Info */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mt: 'auto' }}>
                      <Box
                        sx={{
                          width: 60,
                          height: 60,
                          borderRadius: '50%',
                          background: 'linear-gradient(135deg, #6366F1, #EC4899)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '1.8rem',
                          boxShadow: `0 8px 20px ${alpha('#6366F1', 0.3)}`,
                          transition: 'transform 0.3s ease',
                          '&:hover': {
                            transform: 'scale(1.1)',
                          },
                        }}
                      >
                        {testimonial.avatar}
                      </Box>
                      <Box sx={{ flex: 1 }}>
                        <Typography
                          variant="h6"
                          fontWeight={700}
                          sx={{
                            color: 'text.primary',
                            mb: 0.5,
                          }}
                        >
                          {testimonial.name}
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'text.secondary',
                            fontWeight: 600,
                          }}
                        >
                          {testimonial.role}
                        </Typography>
                        <Typography
                          variant="caption"
                          sx={{
                            color: alpha(theme.palette.text.secondary, 0.7),
                            fontWeight: 500,
                          }}
                        >
                          {testimonial.company}
                        </Typography>
                      </Box>
                    </Box>
                  </Stack>
                </Card>
              </Fade>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* Enhanced CTA Section */}
      <Box
        id="cta"
        data-animate
        sx={{
          py: { xs: 10, md: 20 },
          background: `
            linear-gradient(135deg, ${alpha('#6366F1', 0.08)} 0%, ${alpha('#EC4899', 0.08)} 50%, ${alpha('#10B981', 0.08)} 100%),
            radial-gradient(circle at 30% 30%, ${alpha('#6366F1', 0.15)} 0%, transparent 50%),
            radial-gradient(circle at 70% 70%, ${alpha('#EC4899', 0.15)} 0%, transparent 50%)
          `,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Box textAlign="center">
            <Zoom in timeout={1000}>
              <Typography
                variant="h1"
                sx={{
                  fontSize: { xs: '2rem', sm: '3.5rem', md: '5rem' },
                  fontWeight: 900,
                  mb: 4,
                  background: `linear-gradient(135deg, #6366F1 0%, #EC4899 50%, #10B981 100%)`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Ready to Create with AI?
              </Typography>
            </Zoom>

            <Typography
              variant="h5"
              sx={{
                color: 'text.secondary',
                mb: 8,
                maxWidth: 800,
                mx: 'auto',
                lineHeight: 1.7,
                fontSize: '1.3rem',
                fontWeight: 400,
              }}
            >
              Generate videos, images, and audio. Search the web. Transcribe media. Post to social platforms.
              All from one dashboard with an AI chat that does it for you.
            </Typography>

            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={3}
              justifyContent="center"
              alignItems="center"
              sx={{ mb: 8 }}
              flexWrap="wrap"
            >
              {[
                '🎬 AI Video Generation',
                '🎨 Image Creation',
                '🎙️ Voice Synthesis',
                '📱 Social Automation',
                '⚡ Real-time Processing',
                '🚀 Enterprise Scale',
              ].map((tag, index) => (
                <Fade key={tag} in timeout={1500 + index * 100}>
                  <Chip
                    label={tag}
                    sx={{
                      px: 3,
                      py: 1,
                      fontSize: '1rem',
                      fontWeight: 600,
                      background: `linear-gradient(135deg, ${alpha('#6366F1', 0.15)}, ${alpha('#EC4899', 0.15)})`,
                      color: '#6366F1',
                      border: `2px solid ${alpha('#6366F1', 0.2)}`,
                      backdropFilter: 'blur(10px)',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: `0 8px 20px ${alpha('#6366F1', 0.3)}`,
                      },
                      transition: 'all 0.3s ease',
                    }}
                  />
                </Fade>
              ))}
            </Stack>

            <Zoom in timeout={2000}>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/login')}
                endIcon={<ArrowForward />}
                sx={{
                  px: 12,
                  py: 4,
                  fontSize: '1.4rem',
                  borderRadius: 8,
                  textTransform: 'none',
                  fontWeight: 800,
                  background: `linear-gradient(135deg, #6366F1 0%, #EC4899 50%, #10B981 100%)`,
                  boxShadow: `0 15px 60px ${alpha('#6366F1', 0.4)}`,
                  position: 'relative',
                  overflow: 'hidden',
                  '&:hover': {
                    background: `linear-gradient(135deg, #5855EB 0%, #DB2777 50%, #059669 100%)`,
                    transform: 'translateY(-4px)',
                    boxShadow: `0 25px 80px ${alpha('#6366F1', 0.5)}`,
                  },
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: '-100%',
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                    transition: 'left 0.6s',
                  },
                  '&:hover::before': {
                    left: '100%',
                  },
                  transition: 'all 0.4s ease',
                }}
              >
                Start Building Now - It's Free!
              </Button>
            </Zoom>
          </Box>
        </Container>
      </Box>

      {/* Enhanced Footer */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${alpha('#0F172A', 0.95)} 0%, ${alpha('#1E293B', 0.95)} 100%)`,
          color: 'white',
          py: 12,
          borderTop: `1px solid ${alpha('#6366F1', 0.2)}`,
          backdropFilter: 'blur(20px)',
        }}
      >
        <Container maxWidth="lg">
          <Grid container spacing={6}>
            <Grid item xs={12} md={6}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  mb: 3,
                }}
              >
                Griot
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  mb: 4,
                  lineHeight: 1.7,
                  color: alpha('#fff', 0.8),
                }}
              >
                The most comprehensive AI platform for intelligent agents, media generation, and workflow automation.
                Built with cutting-edge technology and designed for global scale.
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  color: alpha('#fff', 0.6),
                  mb: 4,
                }}
              >
                © 2026 Griot. Built with ❤️ in London, ON.
              </Typography>
              <Stack direction="row" spacing={2}>
                <Chip
                  icon={<VerifiedUser />}
                  label="Open REST API"
                  sx={{
                    bgcolor: alpha('#10B981', 0.2),
                    color: '#10B981',
                    fontWeight: 600,
                    border: `1px solid ${alpha('#10B981', 0.3)}`,
                  }}
                />
                <Chip
                  icon={<Security />}
                  label="Docker Ready"
                  sx={{
                    bgcolor: alpha('#6366F1', 0.2),
                    color: '#6366F1',
                    fontWeight: 600,
                    border: `1px solid ${alpha('#6366F1', 0.3)}`,
                  }}
                />
              </Stack>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  mb: 3,
                  color: '#fff',
                }}
              >
                Powered by Modern Tech Stack
              </Typography>
              <Grid container spacing={2}>
                {[
                  'Python 3.12', 'FastAPI', 'PostgreSQL', 'Redis',
                  'Docker', 'S3 Storage', 'React 19', 'TypeScript'
                ].map((tech) => (
                  <Grid item key={tech}>
                    <Chip
                      label={tech}
                      size="small"
                      sx={{
                        bgcolor: alpha('#fff', 0.1),
                        color: alpha('#fff', 0.8),
                        border: `1px solid ${alpha('#fff', 0.2)}`,
                        fontWeight: 500,
                      }}
                    />
                  </Grid>
                ))}
              </Grid>
              <Box sx={{ mt: 4 }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: alpha('#fff', 0.6),
                    mb: 2,
                  }}
                >
                  Ready to scale your media applications?
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/login')}
                  sx={{
                    color: '#6366F1',
                    borderColor: '#6366F1',
                    '&:hover': {
                      borderColor: '#EC4899',
                      color: '#EC4899',
                      bgcolor: alpha('#EC4899', 0.1),
                    },
                  }}
                >
                  Get Started Today
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Back to Top Button */}
      <BackToTopButton />
    </Box>
  );
};

// Back to Top Button
const BackToTopButton: React.FC = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setVisible(window.scrollY > 500);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <Fade in={visible}>
      <Box
        onClick={scrollToTop}
        sx={{
          position: 'fixed',
          bottom: 30,
          right: 30,
          width: 60,
          height: 60,
          borderRadius: '50%',
          background: `linear-gradient(135deg, #6366F1 0%, #EC4899 100%)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          zIndex: 1000,
          boxShadow: `0 10px 30px ${alpha('#6366F1', 0.4)}`,
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-3px) scale(1.1)',
            boxShadow: `0 15px 40px ${alpha('#6366F1', 0.5)}`,
          },
        }}
      >
        <KeyboardArrowDown
          sx={{
            color: 'white',
            fontSize: 28,
            transform: 'rotate(180deg)',
          }}
        />
      </Box>
    </Fade>
  );
};

export default Home;