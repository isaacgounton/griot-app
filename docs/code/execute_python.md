# Python Code Execution

The Python code execution endpoint allows you to execute Python code in a sandboxed environment with advanced security features, output capture, and both synchronous and asynchronous processing.

## Execute Python Code

Execute Python code with comprehensive safety checks and output handling.

### Endpoint

```
POST /api/v1/code/execute/python
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "code": "print('Hello, World!')",
  "timeout": 30,
  "sync": false
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| code | string | Yes | - | The Python code to execute |
| timeout | integer | No | 30 | Execution timeout in seconds (1-300) |
| sync | boolean | No | false | If True, return response immediately. If False (default), create async job |

### Security Features

The code execution service includes comprehensive security measures:

#### Input Validation
- **Syntax Checking**: Code is validated for syntax errors before execution
- **Length Limits**: Maximum 10KB of code per execution
- **Dangerous Pattern Detection**: Blocks potentially harmful operations
- **Timeout Protection**: Configurable timeout prevents infinite loops

#### Blocked Operations
The following operations are blocked for security:
- File system access (`open`, `file`)
- Network operations (`socket`, `urllib`, `requests`)
- System operations (`os`, `subprocess`)
- Dynamic code execution (`eval`, `exec`, `compile`)
- Input/output functions (`input`, `raw_input`)

### Response

#### Async Response (default)
```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

#### Sync Response (sync=true)
```json
{
  "job_id": null,
  "status": "completed",
  "result": {
    "result": "Hello, World!",
    "stdout": "Hello, World!\n",
    "stderr": "",
    "exit_code": 0
  }
}
```

### Examples

#### Basic Synchronous Execution
```bash
curl -X POST "http://localhost:8000/api/v1/code/execute/python" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "code": "print(\"Hello, World!\")",
    "sync": true
  }'
```

Response:
```json
{
  "job_id": null,
  "status": "completed",
  "result": {
    "result": "Hello, World!",
    "stdout": "Hello, World!\n",
    "stderr": "",
    "exit_code": 0
  }
}
```

#### Mathematical Computation
```bash
curl -X POST "http://localhost:8000/api/v1/code/execute/python" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "code": "import math\nresult = math.sqrt(16)\nprint(f\"Square root of 16: {result}\")",
    "sync": true
  }'
```

Response:
```json
{
  "job_id": null,
  "status": "completed",
  "result": {
    "result": 4.0,
    "stdout": "Square root of 16: 4.0\n",
    "stderr": "",
    "exit_code": 0
  }
}
```

#### Async Processing
```bash
curl -X POST "http://localhost:8000/api/v1/code/execute/python" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "code": "import time\ntime.sleep(2)\nprint(\"Delayed execution complete\")",
    "timeout": 60,
    "sync": false
  }'
```

Response:
```json
{
  "job_id": "j-456e7890-f12g-34h5-b678-527715285111"
}
```

#### Custom Timeout
```bash
curl -X POST "http://localhost:8000/api/v1/code/execute/python" \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "code": "import time\ntime.sleep(5)\nprint(\"This might timeout\")",
    "timeout": 3,
    "sync": true
  }'
```

Response:
```json
{
  "job_id": null,
  "status": "completed",
  "result": {
    "error": "Execution timed out after 3 seconds"
  }
}
```

## Code Validation

Validate Python code without executing it.

### Endpoint

```
GET /api/v1/code/validate
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| code | string | Yes | - | Python code to validate |
| timeout | integer | No | 30 | Timeout value to validate |

### Example

```bash
curl -X GET "http://localhost:8000/api/v1/code/validate" \
  -H 'X-API-Key: your-api-key' \
  -G \
  -d "code=print('Hello')&timeout=30"
```

Response:
```json
{
  "valid": true,
  "syntax_valid": true,
  "timeout_valid": true,
  "error": null,
  "code_length": 14,
  "timeout": 30,
  "checks": {
    "syntax": true,
    "dangerous_operations": true,
    "length_limit": true,
    "timeout_range": true
  }
}
```

#### Validation Error Example
```bash
curl -X GET "http://localhost:8000/api/v1/code/validate" \
  -H 'X-API-Key: your-api-key' \
  -G \
  -d "code=print('unclosed string"
```

Response:
```json
{
  "valid": false,
  "syntax_valid": false,
  "timeout_valid": true,
  "error": "Syntax error: EOL while scanning string literal",
  "code_length": 19,
  "timeout": 30,
  "checks": {
    "syntax": false,
    "dangerous_operations": true,
    "length_limit": true,
    "timeout_range": true
  }
}
```

## Job Status

All code execution jobs use the centralized job status system:

### Check Job Status

```
GET /api/v1/jobs/{job_id}/status
```

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/j-123e4567-e89b-12d3-a456-426614174000/status" \
  -H 'X-API-Key: your-api-key'
```

Response:
```json
{
  "success": true,
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "id": "j-123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "operation": "code_execution",
    "params": {
      "code": "print('Hello, World!')",
      "timeout": 30
    },
    "result": {
      "result": "Hello, World!",
      "stdout": "Hello, World!\n",
      "stderr": "",
      "exit_code": 0
    },
    "error": null,
    "created_at": "2024-12-15T10:30:00.123456",
    "updated_at": "2024-12-15T10:30:02.654321"
  }
}
```

## Advanced Examples

### Data Processing
```python
# Process a list of numbers
numbers = [1, 2, 3, 4, 5]
squared = [x**2 for x in numbers]
print(f"Original: {numbers}")
print(f"Squared: {squared}")
```

### String Manipulation
```python
# Text processing
text = "Hello, World! How are you?"
words = text.split()
word_count = len(words)
print(f"Word count: {word_count}")
print(f"Words: {words}")
```

### Mathematical Functions
```python
# Calculate factorial
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

result = factorial(5)
print(f"5! = {result}")
```

### List Comprehensions
```python
# Generate prime numbers
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [x for x in range(2, 20) if is_prime(x)]
print(f"Primes up to 20: {primes}")
```

## Error Handling

Common error responses:

### Syntax Error
```json
{
  "detail": "Code execution failed: Syntax error: invalid syntax"
}
```

### Security Violation
```json
{
  "detail": "Code execution failed: Potentially dangerous operation detected: import os"
}
```

### Timeout Error
```json
{
  "detail": "Code execution failed: Execution timed out after 30 seconds"
}
```

### Code Too Long
```json
{
  "detail": "Code execution failed: Code too long (maximum 10KB)"
}
```

## Use Cases

- **Data Processing**: Transform and analyze data in real-time
- **Mathematical Calculations**: Perform complex computations
- **Algorithm Testing**: Test algorithms before implementation
- **Educational Demonstrations**: Show programming concepts
- **Code Validation**: Check syntax without execution
- **Prototyping**: Quick code testing without local setup
- **Batch Processing**: Execute multiple code jobs asynchronously

## Best Practices

1. **Keep code simple**: Focus on computational tasks, not complex workflows
2. **Use appropriate timeouts**: Set reasonable timeout values for your operations
3. **Validate first**: Use the validation endpoint before expensive operations
4. **Async for long tasks**: Use async processing for computations that take more than a few seconds
5. **Error handling**: Include try-catch blocks in your code for robust execution
6. **Memory management**: Avoid creating large data structures that might exceed memory limits
7. **Security awareness**: Remember the sandbox restrictions and code accordingly

## Limitations

- **No file system access**: Cannot read/write files
- **No network operations**: Cannot make HTTP requests or network connections
- **No system calls**: Cannot access system resources or external programs
- **Memory limits**: Subject to system memory constraints
- **Execution time**: Limited by timeout settings (max 300 seconds)
- **Code size**: Maximum 10KB per execution

```