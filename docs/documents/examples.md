# Document Processing Examples

This document provides comprehensive examples for using the Document Processing API with various file formats and use cases.

## Basic Examples

### Convert PDF Document

```bash
# From URL
curl -X POST "https://your-api.com/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -F "url=https://example.com/research-paper.pdf" \
  -F "include_metadata=true" \
  -F "preserve_formatting=true"

# From file upload
curl -X POST "https://your-api.com/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -F "file=@research-paper.pdf" \
  -F "include_metadata=true"
```

### Convert Word Document

```bash
curl -X POST "https://your-api.com/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -F "url=https://example.com/report.docx" \
  -F "preserve_formatting=true"
```

### Convert Excel Spreadsheet

```bash
curl -X POST "https://your-api.com/v1/documents/to-markdown" \
  -H "X-API-Key: your-key" \
  -F "file=@data-analysis.xlsx" \
  -F "include_metadata=false"
```

## Programming Language Examples

### Python

#### Basic Conversion

```python
import requests
import time
import json

class DocumentConverter:
    def __init__(self, api_key, base_url="https://your-api.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def convert_from_url(self, url, include_metadata=True, preserve_formatting=True):
        """Convert document from URL"""
        data = {
            "url": url,
            "include_metadata": include_metadata,
            "preserve_formatting": preserve_formatting
        }
        
        response = requests.post(
            f"{self.base_url}/v1/documents/to-markdown",
            headers=self.headers,
            data=data
        )
        response.raise_for_status()
        
        job_id = response.json()["job_id"]
        return self.wait_for_completion(job_id)
    
    def convert_from_file(self, file_path, include_metadata=True):
        """Convert document from file upload"""
        with open(file_path, 'rb') as f:
            files = {"file": f}
            data = {
                "include_metadata": include_metadata,
                "preserve_formatting": True
            }
            
            response = requests.post(
                f"{self.base_url}/v1/documents/to-markdown",
                headers=self.headers,
                files=files,
                data=data
            )
            response.raise_for_status()
            
            job_id = response.json()["job_id"]
            return self.wait_for_completion(job_id)
    
    def wait_for_completion(self, job_id, timeout=300):
        """Wait for job completion with polling"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.base_url}/v1/documents/to-markdown/{job_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result["status"] == "completed":
                return result["result"]
            elif result["status"] == "failed":
                raise Exception(f"Conversion failed: {result.get('error', 'Unknown error')}")
            
            time.sleep(2)  # Poll every 2 seconds
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

# Usage
converter = DocumentConverter("your-api-key")

# Convert PDF from URL
result = converter.convert_from_url("https://example.com/document.pdf")
print(f"Converted {result['word_count']} words in {result['processing_time']:.2f} seconds")
print(result['markdown_content'])

# Convert local file
result = converter.convert_from_file("./local-document.docx")
with open("output.md", "w") as f:
    f.write(result['markdown_content'])
```

#### Batch Processing

```python
import asyncio
import aiohttp
from typing import List, Dict

class BatchDocumentConverter:
    def __init__(self, api_key, base_url="https://your-api.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    async def convert_multiple_urls(self, urls: List[str]) -> List[Dict]:
        """Convert multiple documents concurrently"""
        async with aiohttp.ClientSession() as session:
            # Start all conversions
            jobs = []
            for url in urls:
                job_id = await self._start_conversion(session, url)
                jobs.append(job_id)
            
            # Wait for all to complete
            results = []
            for job_id in jobs:
                result = await self._wait_for_job(session, job_id)
                results.append(result)
            
            return results
    
    async def _start_conversion(self, session, url):
        """Start a conversion job"""
        data = aiohttp.FormData()
        data.add_field('url', url)
        data.add_field('include_metadata', 'true')
        
        async with session.post(
            f"{self.base_url}/v1/documents/to-markdown",
            headers=self.headers,
            data=data
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return result["job_id"]
    
    async def _wait_for_job(self, session, job_id):
        """Wait for job completion"""
        while True:
            async with session.get(
                f"{self.base_url}/v1/documents/to-markdown/{job_id}",
                headers=self.headers
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                if result["status"] == "completed":
                    return result["result"]
                elif result["status"] == "failed":
                    raise Exception(f"Job {job_id} failed: {result.get('error')}")
                
                await asyncio.sleep(2)

# Usage
async def main():
    converter = BatchDocumentConverter("your-api-key")
    
    urls = [
        "https://example.com/doc1.pdf",
        "https://example.com/doc2.docx",
        "https://example.com/doc3.xlsx"
    ]
    
    results = await converter.convert_multiple_urls(urls)
    
    for i, result in enumerate(results):
        print(f"Document {i+1}: {result['word_count']} words")
        with open(f"output_{i+1}.md", "w") as f:
            f.write(result['markdown_content'])

# Run batch conversion
asyncio.run(main())
```

### JavaScript/Node.js

#### Basic Conversion

```javascript
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

class DocumentConverter {
    constructor(apiKey, baseUrl = 'https://your-api.com') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = { 'X-API-Key': apiKey };
    }

    async convertFromUrl(url, options = {}) {
        const { includeMetadata = true, preserveFormatting = true } = options;
        
        const formData = new FormData();
        formData.append('url', url);
        formData.append('include_metadata', includeMetadata.toString());
        formData.append('preserve_formatting', preserveFormatting.toString());

        try {
            const response = await axios.post(
                `${this.baseUrl}/v1/documents/to-markdown`,
                formData,
                { headers: { ...this.headers, ...formData.getHeaders() } }
            );

            const jobId = response.data.job_id;
            return await this.waitForCompletion(jobId);
        } catch (error) {
            throw new Error(`Conversion failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    async convertFromFile(filePath, options = {}) {
        const { includeMetadata = true } = options;
        
        const formData = new FormData();
        formData.append('file', fs.createReadStream(filePath));
        formData.append('include_metadata', includeMetadata.toString());
        formData.append('preserve_formatting', 'true');

        try {
            const response = await axios.post(
                `${this.baseUrl}/v1/documents/to-markdown`,
                formData,
                { headers: { ...this.headers, ...formData.getHeaders() } }
            );

            const jobId = response.data.job_id;
            return await this.waitForCompletion(jobId);
        } catch (error) {
            throw new Error(`Conversion failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    async waitForCompletion(jobId, timeout = 300000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            try {
                const response = await axios.get(
                    `${this.baseUrl}/v1/documents/to-markdown/${jobId}`,
                    { headers: this.headers }
                );

                const result = response.data;

                if (result.status === 'completed') {
                    return result.result;
                } else if (result.status === 'failed') {
                    throw new Error(`Conversion failed: ${result.error || 'Unknown error'}`);
                }

                await new Promise(resolve => setTimeout(resolve, 2000));
            } catch (error) {
                if (error.response?.status === 404) {
                    throw new Error(`Job ${jobId} not found`);
                }
                throw error;
            }
        }

        throw new Error(`Job ${jobId} did not complete within ${timeout / 1000} seconds`);
    }
}

// Usage
async function main() {
    const converter = new DocumentConverter('your-api-key');

    try {
        // Convert from URL
        const result = await converter.convertFromUrl('https://example.com/document.pdf');
        console.log(`Converted ${result.word_count} words in ${result.processing_time} seconds`);
        
        // Save to file
        fs.writeFileSync('output.md', result.markdown_content);
        console.log('Saved to output.md');

        // Convert local file
        const localResult = await converter.convertFromFile('./document.docx');
        console.log(`Local file: ${localResult.file_type} with ${localResult.word_count} words`);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

#### Frontend JavaScript (Browser)

```javascript
class DocumentConverterClient {
    constructor(apiKey, baseUrl = 'https://your-api.com') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    async convertFile(file, options = {}) {
        const { includeMetadata = true, preserveFormatting = true } = options;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('include_metadata', includeMetadata);
        formData.append('preserve_formatting', preserveFormatting);

        try {
            const response = await fetch(`${this.baseUrl}/v1/documents/to-markdown`, {
                method: 'POST',
                headers: {
                    'X-API-Key': this.apiKey
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Conversion failed');
            }

            const { job_id } = await response.json();
            return await this.pollForCompletion(job_id);
        } catch (error) {
            throw new Error(`Conversion failed: ${error.message}`);
        }
    }

    async pollForCompletion(jobId, onProgress = null) {
        while (true) {
            const response = await fetch(`${this.baseUrl}/v1/documents/to-markdown/${jobId}`, {
                headers: { 'X-API-Key': this.apiKey }
            });

            if (!response.ok) {
                throw new Error('Failed to check job status');
            }

            const result = await response.json();

            if (result.status === 'completed') {
                return result.result;
            } else if (result.status === 'failed') {
                throw new Error(`Conversion failed: ${result.error || 'Unknown error'}`);
            }

            if (onProgress) {
                onProgress(result.status);
            }

            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
}

// Usage in HTML page
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const converter = new DocumentConverterClient('your-api-key');
    const statusDiv = document.getElementById('status');
    const resultDiv = document.getElementById('result');

    try {
        statusDiv.textContent = 'Converting document...';
        
        const result = await converter.convertFile(file, {
            includeMetadata: true,
            preserveFormatting: true
        }, (status) => {
            statusDiv.textContent = `Status: ${status}`;
        });

        statusDiv.textContent = `Conversion completed! ${result.word_count} words processed.`;
        resultDiv.innerHTML = `<pre>${result.markdown_content}</pre>`;
        
        // Download result
        const blob = new Blob([result.markdown_content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${result.original_filename}.md`;
        a.click();
        
    } catch (error) {
        statusDiv.textContent = `Error: ${error.message}`;
    }
});
```

## Use Case Examples

### Research Paper Analysis

```python
# Convert and analyze research papers
def analyze_research_papers(paper_urls):
    converter = DocumentConverter("your-api-key")
    
    papers = []
    for url in paper_urls:
        result = converter.convert_from_url(url)
        
        paper_info = {
            'title': result.get('metadata', {}).get('title', 'Unknown'),
            'word_count': result['word_count'],
            'content': result['markdown_content'],
            'processing_time': result['processing_time']
        }
        
        # Extract sections (basic example)
        sections = extract_sections(result['markdown_content'])
        paper_info['sections'] = sections
        
        papers.append(paper_info)
    
    return papers

def extract_sections(markdown_content):
    """Extract main sections from markdown"""
    import re
    
    sections = {}
    current_section = None
    current_content = []
    
    for line in markdown_content.split('\n'):
        if re.match(r'^#+\s', line):  # Header line
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line.strip('#').strip()
            current_content = []
        else:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections
```

### Content Migration

```python
# Migrate content from various document formats
def migrate_document_library(document_paths, output_dir):
    converter = DocumentConverter("your-api-key")
    
    for doc_path in document_paths:
        try:
            result = converter.convert_from_file(doc_path)
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(doc_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}.md")
            
            # Add metadata header
            content = f"""---
title: {result.get('metadata', {}).get('title', base_name)}
original_file: {doc_path}
conversion_date: {datetime.now().isoformat()}
word_count: {result['word_count']}
file_type: {result['file_type']}
---

{result['markdown_content']}
"""
            
            # Save converted content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Converted: {doc_path} -> {output_path}")
            
        except Exception as e:
            print(f"Failed to convert {doc_path}: {e}")
```

### AI/LLM Integration

```python
# Prepare documents for AI analysis
import openai

def analyze_documents_with_ai(document_urls):
    converter = DocumentConverter("your-api-key")
    
    for url in document_urls:
        # Convert document
        result = converter.convert_from_url(url)
        markdown_content = result['markdown_content']
        
        # Analyze with AI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a document analyst. Provide a summary and key insights."},
                {"role": "user", "content": f"Analyze this document:\n\n{markdown_content}"}
            ]
        )
        
        analysis = response.choices[0].message.content
        
        # Save results
        output = {
            'document_url': url,
            'original_filename': result['original_filename'],
            'word_count': result['word_count'],
            'ai_analysis': analysis,
            'conversion_metadata': result.get('metadata', {})
        }
        
        print(f"Analyzed: {result['original_filename']}")
        print(f"Summary: {analysis[:200]}...")
```

## Error Handling Examples

### Robust Error Handling

```python
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

class RobustDocumentConverter:
    def __init__(self, api_key):
        self.converter = DocumentConverter(api_key)
        self.logger = logging.getLogger(__name__)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def convert_with_retry(self, url_or_path, is_file=False):
        """Convert with automatic retry on failure"""
        try:
            if is_file:
                return self.converter.convert_from_file(url_or_path)
            else:
                return self.converter.convert_from_url(url_or_path)
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error converting {url_or_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Conversion error for {url_or_path}: {e}")
            raise
    
    def safe_convert_batch(self, items):
        """Safely convert a batch of documents"""
        results = []
        failed = []
        
        for item in items:
            try:
                result = self.convert_with_retry(item['url'], item.get('is_file', False))
                results.append({
                    'url': item['url'],
                    'success': True,
                    'result': result
                })
            except Exception as e:
                self.logger.error(f"Failed to convert {item['url']}: {e}")
                failed.append({
                    'url': item['url'],
                    'success': False,
                    'error': str(e)
                })
        
        return results, failed
```

### Validation and Preprocessing

```python
def validate_and_convert(file_path_or_url, max_size_mb=50):
    """Validate file before conversion"""
    
    # Check if it's a URL or file path
    if file_path_or_url.startswith(('http://', 'https://')):
        # URL validation
        response = requests.head(file_path_or_url)
        response.raise_for_status()
        
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_size_mb * 1024 * 1024:
            raise ValueError(f"File too large: {int(content_length) / 1024 / 1024:.1f}MB > {max_size_mb}MB")
        
        converter = DocumentConverter("your-api-key")
        return converter.convert_from_url(file_path_or_url)
    
    else:
        # File path validation
        if not os.path.exists(file_path_or_url):
            raise FileNotFoundError(f"File not found: {file_path_or_url}")
        
        file_size = os.path.getsize(file_path_or_url)
        if file_size > max_size_mb * 1024 * 1024:
            raise ValueError(f"File too large: {file_size / 1024 / 1024:.1f}MB > {max_size_mb}MB")
        
        # Check file extension
        allowed_extensions = {'.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.txt', '.html', '.htm'}
        file_ext = os.path.splitext(file_path_or_url)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        converter = DocumentConverter("your-api-key")
        return converter.convert_from_file(file_path_or_url)
```

These examples demonstrate the flexibility and power of the Document Processing API for various use cases, from simple conversions to complex document analysis workflows.