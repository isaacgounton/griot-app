# Static Files Directory

This directory contains static files served by the FastAPI application.

## Feedback Directory

The `feedback/` subdirectory contains the complete "Feedback Magic v1.0" Next.js application:

- **index.html** - Main feedback page
- **_next/** - Next.js build assets (JS, CSS, chunks)
- **logo.png** - Application logo
- **favicon.ico** - Browser favicon
- **Other assets** - SVG icons and additional resources

### Access

The feedback page is accessible at:
```
GET /media/feedback/
```

With API key authentication required via `X-API-Key` header.

### Technology

- Next.js application with modern React components
- Video.js for video playback
- Canvas overlay for annotations
- Responsive design with Tailwind CSS
- Dark theme with modern UI patterns