# Research Routes Documentation

This directory contains documentation for all research-related endpoints in the Media Master API.

## Available Endpoints

### News Research

- **Research News**: `POST /api/v1/research/news`
- **Get News Sources**: `GET /api/v1/research/news/sources`

### AI Video Search

- **Search Stock Videos**: `POST /api/v1/ai/video-search/stock-videos`

### AI Image Search

- **Search Stock Images**: `POST /api/v1/ai/image-search/stock-images`
- **Get Image Providers Status**: `GET /api/v1/ai/image-providers/status`

### Job Status

- **Check Job Status**: `GET /api/v1/jobs/{job_id}/status`

## Common Use Cases

### News Research

Conduct comprehensive news research and analysis using AI-powered search and summarization. Perfect for journalists, researchers, and content creators needing current information and insights.

### Stock Video Search

Find and license high-quality stock videos for your projects using AI-powered search capabilities. Access vast libraries of professional video content for various creative applications.

### Stock Image Search

Discover and license professional stock images using advanced AI search technology. Find the perfect visual assets for your marketing, design, and content creation needs.

## Advanced Features

### AI-Powered Search

- **Semantic Search**: Understand context and intent for more accurate results
- **Content Analysis**: Automatically categorize and tag content
- **Quality Filtering**: Ensure high-quality, relevant results
- **Rights Management**: Built-in licensing and usage rights tracking

### News Intelligence

- **Real-time Updates**: Access current news and trending topics
- **Source Verification**: Cross-reference multiple reliable sources
- **Bias Detection**: Analyze content for objectivity and perspective
- **Trend Analysis**: Identify emerging topics and patterns

### Media Asset Discovery

- **Visual Similarity**: Find images/videos similar to reference content
- **Style Matching**: Locate content matching specific aesthetic preferences
- **Usage Analytics**: Track popular and trending media assets
- **Metadata Enrichment**: Comprehensive tagging and categorization

## Error Handling

All research endpoints follow standard HTTP status codes:

- **200**: Successful operation
- **400**: Bad request (invalid parameters or malformed JSON)
- **401**: Unauthorized (missing or invalid API key)
- **404**: Resource not found (invalid job ID or endpoint)
- **422**: Validation error (invalid input parameters)
- **429**: Rate limit exceeded
- **500**: Internal server error (processing failure or system issues)

Detailed error messages are provided in the response body for debugging and error resolution.
