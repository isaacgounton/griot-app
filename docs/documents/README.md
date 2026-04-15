# Document Processing API

The Document Processing API provides powerful document conversion capabilities using Microsoft's MarkItDown library. Convert various document formats (PDF, Word, Excel, PowerPoint, etc.) to clean, LLM-optimized Markdown format.

## Overview

This API is designed for:

- **Document Analysis**: Convert documents for AI/LLM processing
- **Content Extraction**: Extract text from various file formats
- **Data Pipeline Integration**: Automated document processing workflows
- **Research & Analysis**: Convert research papers, reports, and documents

## Available Endpoints

### Document Conversion

- **Convert to Markdown**: `POST /api/v1/documents/to-markdown`
- **Get Supported Formats**: `GET /api/v1/documents/to-markdown/formats`

### Marker Processing

- **Process Document**: `POST /api/v1/documents/marker`
- **Get Supported Formats**: `GET /api/v1/documents/marker/formats`

### Language Extraction

- **Extract Language**: `POST /api/v1/documents/langextract`
- **Extract Language (JSON)**: `POST /api/v1/documents/langextract/json`
- **Get Available Models**: `GET /api/v1/documents/langextract/models`

### Job Status

- **Check Job Status**: `GET /api/v1/jobs/{job_id}/status`

## Quick Start

### 1. Check Available Formats

```bash
curl -X GET "https://your-api.com/api/v1/documents/to-markdown/formats" \
  -H "X-API-Key: your-key"
```

### 2. Convert Document from URL

```bash
curl -X POST "https://your-api.com/api/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -F "url=https://example.com/document.pdf" \
  -F "include_metadata=true"
```

### 3. Convert Uploaded Document

```bash
curl -X POST "https://your-api.com/api/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -F "file=@document.pdf" \
  -F "preserve_formatting=true"
```

### 4. Check Conversion Status

```bash
curl -X GET "https://your-api.com/api/v1/jobs/{job_id}/status" \
  -H "X-API-Key: your-key"
```

## Supported Formats

### Documents

- **PDF**: `.pdf` - PDF documents with text extraction
- **Microsoft Word**: `.docx`, `.doc` - Word documents with formatting
- **Microsoft Excel**: `.xlsx`, `.xls` - Spreadsheets with table conversion
- **Microsoft PowerPoint**: `.pptx`, `.ppt` - Presentations with slide content

### Text & Web

- **HTML**: `.html`, `.htm` - Web pages and HTML documents
- **Plain Text**: `.txt` - Simple text files
- **Markdown**: `.md` - Existing Markdown files

### Images (OCR)

- **JPEG**: `.jpg`, `.jpeg` - Image files with text extraction
- **PNG**: `.png` - PNG images with OCR
- **GIF**: `.gif` - GIF images with text extraction

## API Endpoints

### Get Supported Formats (To Markdown)

- **URL**: `GET /api/v1/documents/to-markdown/formats`
- **Auth**: API Key required
- **Response**: List of supported formats and features

### Convert Document (Async)

- **URL**: `POST /api/v1/documents/to-markdown`
- **Auth**: API Key required
- **Method**: Asynchronous job processing
- **Input**: File upload OR URL
- **Response**: Job ID for status polling

### Check Conversion Status

- **URL**: `GET /api/v1/jobs/{job_id}/status`
- **Auth**: API Key required
- **Response**: Job status and results

### Marker Processing

- **URL**: `POST /api/v1/documents/marker`
- **Auth**: API Key required
- **Method**: Document processing with Marker library
- **Response**: Processed document content

### Get Marker Supported Formats

- **URL**: `GET /api/v1/documents/marker/formats`
- **Auth**: API Key required
- **Response**: List of formats supported by Marker

### Language Extraction

- **URL**: `POST /api/v1/documents/langextract`
- **Auth**: API Key required
- **Method**: Extract language information from documents
- **Response**: Language detection results

### Language Extraction (JSON)

- **URL**: `POST /api/v1/documents/langextract/json`
- **Auth**: API Key required
- **Method**: Extract language information with JSON output
- **Response**: Structured language extraction results

### Get Language Models

- **URL**: `GET /api/v1/documents/langextract/models`
- **Auth**: API Key required
- **Response**: Available language detection models

## Features

### Structure Preservation

- **Headers**: H1-H6 hierarchy maintained
- **Lists**: Numbered and bulleted lists preserved
- **Tables**: Excel/Word tables converted to Markdown tables
- **Links**: Hyperlinks preserved where possible

### LLM Optimization

- **Token Efficiency**: Output optimized for AI/LLM processing
- **Clean Format**: Consistent Markdown formatting
- **Structured Data**: Logical document structure preserved

### Metadata Extraction

- **Document Properties**: Title, author, creation date (when available)
- **Statistics**: Word count, character count, processing time
- **File Information**: Original filename, detected file type

## Request Parameters

### File Upload Parameters

- `file` (file): Document file to convert
- `url` (string): URL of document to convert
- `include_metadata` (boolean): Include document metadata (default: true)
- `preserve_formatting` (boolean): Preserve structure (default: true)

### Options

- File size limit: 50MB for uploads
- Supported via URL: Any publicly accessible document
- Processing time: Varies by document size and complexity

## Response Format

### Job Response (Async)

```json
{
  "job_id": "abc-123-def-456"
}
```

### Status Response

```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "result": {
    "markdown_content": "# Document Title\\n\\nContent...",
    "original_filename": "document.pdf",
    "file_type": "PDF",
    "word_count": 1245,
    "character_count": 8932,
    "processing_time": 3.2,
    "metadata": {
      "title": "Document Title",
      "author": "Author Name"
    }
  },
  "error": null
}
```

### Direct Response (Sync)

```json
{
  "markdown_content": "# Document Title\\n\\nConverted content...",
  "original_filename": "document.pdf",
  "file_type": "PDF",
  "word_count": 1245,
  "character_count": 8932,
  "processing_time": 3.2,
  "metadata": {
    "title": "Document Title",
    "author": "Author Name"
  }
}
```

## Error Handling

### Common Error Responses

#### Service Unavailable (503)

```json
{
  "detail": "MarkItDown service is not available. Please install 'markitdown[all]' package."
}
```

#### Invalid File Type (400)

```json
{
  "detail": "Unsupported file type '.xyz'. Use /formats endpoint to see supported formats."
}
```

#### File Too Large (413)

```json
{
  "detail": "File size exceeds 50MB limit"
}
```

#### Missing Parameters (400)

```json
{
  "detail": "Either file or url parameter must be provided"
}
```

## Usage Examples

### Python Example

```python
import requests

# Convert document from URL
response = requests.post(
    "https://your-api.com/v1/documents/to-markdown",
    headers={"X-API-Key": "your-key"},
    data={
        "url": "https://example.com/document.pdf",
        "include_metadata": True,
        "preserve_formatting": True
    }
)

job_id = response.json()["job_id"]

# Check status
status_response = requests.get(
    f"https://your-api.com/v1/documents/to-markdown/{job_id}",
    headers={"X-API-Key": "your-key"}
)

result = status_response.json()
if result["status"] == "completed":
    markdown_content = result["result"]["markdown_content"]
    print(markdown_content)
```

### JavaScript Example

```javascript
// Convert document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('include_metadata', 'true');

const response = await fetch('/v1/documents/to-markdown', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-key'
  },
  body: formData
});

const { job_id } = await response.json();

// Poll for results
const checkStatus = async () => {
  const statusResponse = await fetch(`/v1/documents/to-markdown/${job_id}`, {
    headers: { 'X-API-Key': 'your-key' }
  });
  
  const result = await statusResponse.json();
  
  if (result.status === 'completed') {
    console.log(result.result.markdown_content);
  } else if (result.status === 'processing') {
    setTimeout(checkStatus, 2000); // Check again in 2 seconds
  }
};

checkStatus();
```

## Best Practices

### File Selection

- **PDF**: Best for formatted documents, reports, papers
- **Word**: Good for structured documents with headers/lists  
- **Excel**: Ideal for tabular data conversion
- **Images**: Use high-quality images for better OCR results

### Performance Tips

- Use async endpoints for files > 5MB
- Include metadata only when needed
- Consider file optimization before upload
- Use URLs when possible to avoid upload overhead

### Integration Patterns

- **Batch Processing**: Queue multiple documents
- **Pipeline Integration**: Chain with other API endpoints
- **Content Analysis**: Use with AI/LLM services for document analysis
- **Search Indexing**: Convert documents for search engines

## Rate Limits & Quotas

- **File Size**: 50MB maximum per upload
- **Concurrent Jobs**: Standard rate limiting applies
- **Processing Time**: Varies by document complexity
- **API Calls**: Standard API rate limits

## Dependencies

The document processing service requires:

- `markitdown[all]>=0.0.4`
- `python-docx>=1.0.1`
- `openpyxl>=3.1.5`  
- `pdfplumber>=0.11.4`
- `beautifulsoup4>=4.12.3`
- `lxml>=5.3.0`

These are automatically installed during deployment.

## Troubleshooting

### Common Issues

**"MarkItDown service is not available"**

- Solution: Dependencies not installed. Check deployment logs.

**"Unsupported file type"**

- Solution: Check `/formats` endpoint for supported formats.

**"File size exceeds limit"**

- Solution: Reduce file size or use URL-based conversion.

**Slow processing**

- Cause: Large or complex documents take time
- Solution: Use async endpoints and poll for results

**OCR not working on images**

- Cause: Poor image quality or missing text
- Solution: Use higher quality images with clear text

### Getting Help

- Check API documentation at `/docs`
- Review supported formats at `/v1/documents/formats`
- Monitor job status for error details
- Contact support with job IDs for specific issues
