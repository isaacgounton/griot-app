# Griot Frontend

A modern React frontend for the Griot Video Creation Platform. Built with React 19, Material-UI, and TypeScript.

## Features

- **Video Creation**: Manual video creation with scene-by-scene control
- **AI Research**: Automatic topic research and video generation
- **Job Management**: Real-time tracking of video creation jobs
- **API Key Authentication**: Secure authentication using X-API-Key headers
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Material-UI Components**: Modern and accessible user interface

## Tech Stack

- **React 19.1.0** - Latest React with improved performance
- **Material-UI 5** - Modern React component library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **Axios** - HTTP client for API calls
- **React Router** - Client-side routing
- **React Query** - Data fetching and caching

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Access to Griot with valid API key

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd /home/etugrand/DEV.ai/Projects/griot/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

4. **Open your browser**:
   Navigate to `http://localhost:3000`

## Configuration

### API Endpoints

The frontend is configured to proxy API requests to the Griot backend:

- **Development**: `http://localhost:8000` (via Vite proxy)
- **Production**: Same domain as frontend

### Environment Variables

Create a `.env` file in the frontend directory if you need to override defaults:

```bash
# API Base URL (optional, defaults to same origin)
VITE_API_BASE_URL=http://localhost:8000

# Enable debug logging
VITE_DEBUG=true
```

## Usage

### 1. Login

- Enter your Griot key on the login page
- The key is stored securely in your browser's localStorage
- All API requests include the key in the `X-API-Key` header

### 2. Create Videos

**Manual Creation**:
- Navigate to "Create Video"
- Define scenes with narration text and search terms
- Configure video settings (voice, orientation, captions, etc.)
- Submit to start video creation job

**AI Research**:
- Navigate to "AI Research"
- Enter a topic for automated research
- Review generated content and customize settings
- Create video from researched content

### 3. Track Progress

- All video creation jobs are tracked in real-time
- View progress, status, and results on the video details page
- Download completed videos or access additional files

### 4. Manage Videos

- View all your videos on the main dashboard
- Filter by status, search by content
- Delete old videos to free up space

## API Integration

### Authentication

```typescript
// API key is automatically included in all requests
const response = await apiClient.post('/mcp/messages', data);
```

### MCP Protocol

The frontend uses Griot's MCP (Model Context Protocol) endpoints for video creation:

```typescript
// Create video via MCP
const response = await mcpApi.createShortVideo({
  scenes: [...],
  voice_provider: 'kokoro',
  voice_name: 'af_bella'
});
```

### Job Queue Integration

```typescript
// Poll job status until completion
const job = await apiUtils.pollJobStatus(jobId, (progress) => {
  console.log('Progress:', progress.status, progress.progress);
});
```

## Development

### Project Structure

```
src/
├── components/          # Reusable components
│   └── Layout.tsx      # Main layout wrapper
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication state
├── pages/              # Route components
│   ├── VideoList.tsx   # Video dashboard
│   ├── VideoCreator.tsx # Manual video creation
│   ├── VideoResearcher.tsx # AI research tool
│   ├── VideoDetails.tsx # Video status/playback
│   └── Login.tsx       # Authentication
├── types/              # TypeScript types
│   └── griot.ts      # API response types
├── utils/              # Utility functions
│   └── api.ts         # API client and helpers
└── styles/             # CSS files
    └── index.css      # Global styles
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript checks

### Code Style

- **TypeScript**: Strict mode enabled
- **ESLint**: Configured for React and TypeScript
- **Prettier**: Code formatting (install extension recommended)

## Deployment

### Production Build

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Docker Deployment

The frontend can be served using any static file server. For integration with the main Griot deployment:

1. Build the frontend:
   ```bash
   npm run build
   ```

2. Copy the `dist/` contents to the main Griot `app/static/frontend/` directory

3. Configure the Griot backend to serve the frontend files

### Environment Configuration

For production, ensure:
- API proxy is configured correctly
- HTTPS is enabled if required
- CORS settings allow frontend domain
- API keys are properly secured

## Troubleshooting

### Common Issues

**1. API Connection Failed**
- Verify the Griot backend is running
- Check API key is valid
- Confirm CORS settings

**2. Video Creation Fails**
- Check browser console for errors
- Verify all required fields are filled
- Ensure API key has necessary permissions

**3. Build Errors**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version (18+ required)
- Verify all dependencies are installed

### Debug Mode

Enable debug logging by setting:
```bash
VITE_DEBUG=true
```

This will show additional console logs for API requests and responses.

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Include error handling for API calls
4. Test on both desktop and mobile
5. Update documentation for new features

## License

This project is part of the Griot platform. See the main project license for details.