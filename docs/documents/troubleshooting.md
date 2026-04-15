# Document Processing Troubleshooting

This guide covers common issues and solutions when using the Document Processing API.

## Common Issues

### 0. YouTube Video Processing Failures (Coolify/Server Environments) 🔥

**Problem:** "Unable to process YouTube video" or "Video unavailable" errors when converting YouTube videos to Markdown on Coolify or other server environments.

**Symptoms:**

- YouTube video conversions work locally but fail on server
- "Video is not available" or "Access denied" errors
- HTTP 403 or similar errors during document processing

**Root Cause:** YouTube restricts access for server/headless environments and requires browser cookies for many videos.

**Solution: Use Cookie File Support** ⭐

Export cookies from your browser and provide them via the `cookies_url` parameter:

1. **Export cookies from your browser:**
   - Install browser extension like "Get cookies.txt" or "cookies.txt"
   - Visit YouTube and login to your account
   - Export cookies.txt file from the extension

2. **Host cookies file publicly:**
   - Upload to cloud storage (S3, Dropbox, GitHub raw, etc.)
   - Get a public URL to the cookies file
   - Update cookies weekly for best results

3. **Use cookies_url parameter in document conversion:**

   ```json
   {
     "file_url": "https://www.youtube.com/watch?v=example",
     "cookies_url": "https://your-storage.com/cookies.txt",
     "include_metadata": true,
     "preserve_formatting": true
   }
   ```

**Quick Test:**

```bash
# Test YouTube video conversion with cookies
curl -X POST "https://your-api.com/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "cookies_url": "https://your-cookies-url.com/cookies.txt",
    "include_metadata": true
  }'
```

**Security Notes:**

- Only use cookies from accounts you control
- Rotate cookies regularly (weekly recommended)
- Don't share cookie files publicly
- Use separate YouTube account for API access

### Service Unavailable

**Error Message:**

```json
{
  "detail": "MarkItDown service is not available. Please install 'markitdown[all]' package."
}
```

**Cause:** The MarkItDown library is not installed or failed to initialize.

**Solutions:**

1. **Check Installation:** Verify all dependencies are installed
2. **Restart Service:** Restart the API service after installing dependencies
3. **Check Logs:** Review application logs for installation errors

**Prevention:**

- Ensure all grouped requirements files include all necessary dependencies
- Use proper dependency versions in deployment

### File Format Issues

#### Unsupported File Type

**Error Message:**

```json
{
  "detail": "Unsupported file type '.xyz'. Use /formats endpoint to see supported formats."
}
```

**Solutions:**

1. Check supported formats: `GET /v1/documents/formats`
2. Convert file to supported format before upload
3. Verify file extension matches actual content

**Supported Formats:**

- Documents: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS
- Text: TXT, HTML, HTM, MD
- Images: JPG, JPEG, PNG, GIF (with OCR)

#### Corrupted or Invalid Files

**Symptoms:**

- Conversion fails with generic error
- Empty or minimal output
- Processing takes unusually long

**Solutions:**

1. **Verify File Integrity:** Open file in native application
2. **Re-save File:** Save in standard format from original application
3. **Try Different Source:** Use alternative version of document
4. **Check File Size:** Ensure file isn't corrupted during transfer

### Size and Performance Issues

#### File Size Limits

**Error Message:**

```json
{
  "detail": "File size exceeds 50MB limit"
}
```

**Solutions:**

1. **Compress File:** Reduce file size before upload
2. **Split Document:** Break large documents into smaller parts
3. **Use URL Method:** Host file externally and use URL parameter
4. **Optimize Content:** Remove unnecessary images or embedded objects

**File Size Optimization Tips:**

- **PDF:** Use "Save As" with optimization settings
- **Word:** Remove embedded images or compress them
- **Excel:** Delete unnecessary worksheets or data
- **PowerPoint:** Compress images and remove animations

#### Slow Processing

**Symptoms:**

- Jobs remain in "processing" state for extended periods
- Timeouts when checking job status

**Causes & Solutions:**

1. **Large Documents**
   - **Expected:** Large files take more time
   - **Solution:** Use async endpoints and poll patiently

2. **Complex Formatting**
   - **Cause:** Tables, images, complex layouts
   - **Solution:** Simplify document if possible

3. **Server Load**
   - **Cause:** High concurrent usage
   - **Solution:** Retry during off-peak hours

4. **Network Issues**
   - **Cause:** Slow download from URL
   - **Solution:** Use file upload instead of URL

### Network and Authentication Issues

#### Authentication Failures

**Error Message:**

```json
{
  "detail": "Invalid API key"
}
```

**Solutions:**

1. **Verify API Key:** Check key is correct and active
2. **Header Format:** Ensure using `X-API-Key` header
3. **Key Permissions:** Verify key has document processing permissions

**Correct Authentication:**

```bash
curl -H "X-API-Key: your-actual-key" ...
```

#### Network Timeouts

**Symptoms:**

- Connection timeouts during upload
- Unable to reach API endpoints

**Solutions:**

1. **Check Network:** Verify internet connectivity
2. **Firewall Rules:** Ensure API endpoints are accessible
3. **Retry Logic:** Implement exponential backoff
4. **Use Smaller Files:** Reduce upload size

### Conversion Quality Issues

#### Poor OCR Results

**Symptoms:**

- Garbled text from image files
- Missing text content
- Incorrect character recognition

**Solutions:**

1. **Image Quality:** Use higher resolution images
2. **Text Clarity:** Ensure text is clear and well-contrasted
3. **File Format:** Use PDF instead of images when possible
4. **Preprocessing:** Clean up images before conversion

**Image Quality Guidelines:**

- **Resolution:** Minimum 300 DPI for text
- **Contrast:** High contrast between text and background
- **Orientation:** Ensure text is properly oriented
- **Noise:** Remove artifacts, spots, or lines

#### Missing Formatting

**Symptoms:**

- Tables not converted properly
- Headers not recognized
- Lists appear as plain text

**Solutions:**

1. **Enable Formatting:** Set `preserve_formatting=true`
2. **Source Quality:** Use well-structured source documents
3. **File Format:** Use native formats (DOCX vs DOC)
4. **Post-processing:** Manually fix critical formatting

#### Incomplete Content

**Symptoms:**

- Missing pages or sections
- Truncated output
- Empty result

**Causes & Solutions:**

1. **Protected Documents**
   - **Cause:** Password-protected or restricted files
   - **Solution:** Remove protection before conversion

2. **Embedded Objects**
   - **Cause:** Complex embedded content
   - **Solution:** Flatten or extract content separately

3. **Non-standard Encoding**
   - **Cause:** Unusual character encoding
   - **Solution:** Re-save with UTF-8 encoding

### Job Management Issues

#### Job Not Found

**Error Message:**

```json
{
  "detail": "Job not found"
}
```

**Causes:**

- Job ID expired or invalid
- Job was completed and cleaned up
- Service restart cleared job queue

**Solutions:**

1. **Verify Job ID:** Check ID is correct
2. **Check Timing:** Jobs may expire after completion
3. **Restart Conversion:** Submit new job if needed

#### Jobs Stuck in Processing

**Symptoms:**

- Job status remains "processing" indefinitely
- No error messages

**Solutions:**

1. **Wait Longer:** Complex documents take time
2. **Check Logs:** Review server logs for issues
3. **Cancel and Retry:** Submit new job
4. **Contact Support:** Provide job ID for investigation

## Debugging Strategies

### Step-by-Step Diagnosis

1. **Verify API Access**

   ```bash
   curl -H "X-API-Key: your-key" \
        "https://your-api.com/v1/documents/formats"
   ```

2. **Test with Simple File**
   - Use small, simple PDF or TXT file
   - Verify basic functionality works

3. **Check File Specifics**
   - Try different file formats
   - Test with URL vs file upload
   - Verify file isn't corrupted

4. **Monitor Processing**
   - Poll job status regularly
   - Check for error messages
   - Note processing times

### Logging and Monitoring

#### Enable Detailed Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Log all API interactions
def log_conversion_attempt(file_info):
    logger.info(f"Starting conversion: {file_info}")
    
def log_conversion_result(result):
    logger.info(f"Conversion completed: {result.get('word_count', 0)} words")
```

#### Track Performance Metrics

```python
import time

class PerformanceTracker:
    def __init__(self):
        self.metrics = []
    
    def track_conversion(self, file_size, processing_time, word_count):
        self.metrics.append({
            'file_size_mb': file_size / (1024 * 1024),
            'processing_time': processing_time,
            'word_count': word_count,
            'words_per_second': word_count / processing_time if processing_time > 0 else 0,
            'timestamp': time.time()
        })
    
    def get_average_performance(self):
        if not self.metrics:
            return None
        
        return {
            'avg_processing_time': sum(m['processing_time'] for m in self.metrics) / len(self.metrics),
            'avg_words_per_second': sum(m['words_per_second'] for m in self.metrics) / len(self.metrics),
            'total_conversions': len(self.metrics)
        }
```

## Error Recovery Patterns

### Automatic Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError))
)
def robust_convert_document(url_or_path):
    try:
        converter = DocumentConverter("your-api-key")
        if url_or_path.startswith('http'):
            return converter.convert_from_url(url_or_path)
        else:
            return converter.convert_from_file(url_or_path)
    except Exception as e:
        logging.error(f"Conversion attempt failed: {e}")
        raise
```

### Graceful Degradation

```python
def convert_with_fallback(file_path):
    """Convert document with fallback options"""
    
    try:
        # Primary conversion attempt
        return robust_convert_document(file_path)
    
    except Exception as primary_error:
        logging.warning(f"Primary conversion failed: {primary_error}")
        
        try:
            # Fallback 1: Try without metadata
            converter = DocumentConverter("your-api-key")
            return converter.convert_from_file(file_path, include_metadata=False)
        
        except Exception as fallback_error:
            logging.warning(f"Fallback conversion failed: {fallback_error}")
            
            # Fallback 2: Extract text only (custom implementation)
            return extract_basic_text(file_path)

def extract_basic_text(file_path):
    """Basic text extraction as last resort"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    elif ext == '.pdf':
        # Use basic PDF text extraction
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            content = '\n'.join(page.extract_text() for page in reader.pages)
    else:
        raise ValueError(f"No fallback available for {ext}")
    
    return {
        'markdown_content': content,
        'word_count': len(content.split()),
        'character_count': len(content),
        'file_type': f"Basic {ext.upper()}",
        'processing_time': 0.1,
        'fallback_used': True
    }
```

## Performance Optimization

### Best Practices

1. **File Preparation**
   - Optimize files before conversion
   - Remove unnecessary content
   - Use appropriate file formats

2. **Batch Processing**
   - Group similar documents
   - Process during off-peak hours
   - Implement queue management

3. **Caching**
   - Cache conversion results
   - Avoid duplicate processing
   - Use content hashing for deduplication

4. **Monitoring**
   - Track conversion metrics
   - Monitor error rates
   - Set up alerts for failures

### Resource Management

```python
import asyncio
from asyncio import Semaphore

class ResourceManagedConverter:
    def __init__(self, api_key, max_concurrent=5):
        self.converter = DocumentConverter(api_key)
        self.semaphore = Semaphore(max_concurrent)
    
    async def convert_with_limits(self, files):
        """Convert files with concurrency limits"""
        
        async def limited_convert(file_path):
            async with self.semaphore:
                return await asyncio.to_thread(
                    self.converter.convert_from_file, 
                    file_path
                )
        
        tasks = [limited_convert(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful results from errors
        successful = []
        failed = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({'file': files[i], 'error': str(result)})
            else:
                successful.append({'file': files[i], 'result': result})
        
        return successful, failed
```

## Getting Help

### Information to Provide

When contacting support, include:

1. **Job Details**
   - Job ID (if available)
   - File information (size, type, source)
   - Request parameters used

2. **Error Information**
   - Complete error message
   - HTTP status codes
   - Timestamp of failure

3. **Environment Details**
   - API endpoint being used
   - Client library/language
   - Network configuration

4. **Reproduction Steps**
   - Exact steps taken
   - Sample files (if possible)
   - Expected vs actual behavior

### Self-Service Resources

1. **API Documentation:** `/docs` endpoint
2. **Supported Formats:** `GET /v1/documents/formats`
3. **Service Status:** Check if dependencies are properly installed
4. **Examples:** Review code examples in documentation

### Community Resources

- GitHub Issues: Report bugs and feature requests
- API Forums: Community discussions and tips
- Documentation: Comprehensive guides and examples
- Stack Overflow: Community Q&A with `document-processing-api` tag
