# Troubleshooting Memory Issues and Job Processing Problems

## Problem Description

When processing resource-intensive tasks like video generation, the server may be killed due to memory constraints, even when you believe you have sufficient resources.

## Symptoms

1. Jobs get stuck in "PROCESSING" state
2. Server restarts unexpectedly with "Killed" message in logs
3. Docker containers being terminated by OOM (Out of Memory) killer
4. High memory usage during video processing tasks

## Root Causes

### 1. Docker Resource Limits
The production configuration (`docker-compose.prod.yml`) sets memory limits that may be too restrictive for high-end systems:
- API service: 8GB memory limit (increased from 2GB)
- PostgreSQL: 2GB memory limit (increased from 512MB)
- Redis: 512MB memory limit (increased from 128MB)

### 2. Multiple Workers
The production configuration uses 2 workers, which doubles memory consumption.

### 3. Memory-Intensive Operations
Video processing tasks can consume significant memory:
- AI model loading (especially for image generation)
- Video composition with MoviePy
- FFmpeg operations
- Audio processing
- Caption generation with complex effects

## Solutions

### 1. Increase Memory Limits (Recommended)

Create a `docker-compose.override.yml` file to increase resource limits:

```yaml
version: "3.8"

services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    # Use single worker for better resource management
    command: >
      sh -c "./scripts/startup.sh && 
      exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --worker-class uvicorn.workers.UvicornWorker"

  postgres:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  redis:
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
```

### 2. Use Single Worker Configuration

Modify the startup script or docker-compose to use only 1 worker instead of 2 to reduce memory consumption.

### 3. Monitor Memory Usage

The system now includes memory monitoring that logs usage during job processing. Check logs for memory usage patterns.

### 4. Optimize Job Processing

For memory-intensive operations:
- Process smaller video segments
- Use lower resolution when possible
- Reduce concurrent job processing
- Clean up temporary files more aggressively

## Monitoring Memory Usage

The system now logs memory usage automatically:
- Before and after job processing
- When memory usage exceeds 1GB
- Every 30 seconds during high usage

Example log entries:
```
💾 Memory usage (before job 5ff593b0-d777-4010-8016-86a5a42aeded): 450.2 MB
💾 Memory usage (after job 5ff593b0-d777-4010-8016-86a5a42aeded): 1250.7 MB
```

## Prevention Strategies

### 1. System Resource Planning
- Allocate at least 4GB RAM for the API service
- Ensure host system has sufficient swap space
- Monitor resource usage during peak processing times

### 2. Job Queue Management
- Limit concurrent video processing jobs
- Use job priorities to manage resource-intensive tasks
- Implement job timeouts to prevent stuck processes

### 3. Docker Configuration
- Use `docker-compose.override.yml` for local development
- Adjust resource limits based on your hardware
- Consider using `--memory-swap` for additional swap space

### 4. Video Processing Optimization
- Use appropriate video resolutions (1080p is usually sufficient)
- Limit video duration for processing
- Choose efficient codecs and formats
- Use `effect_type: "none"` for simpler image-to-video processing

## Quick Fixes

### 1. Immediate Solution
The docker-compose.prod.yml file has been updated with higher memory limits for systems with 16GB+ RAM. Simply restart your services:

```bash
# Restart services to apply new memory limits
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### 2. Reduce Concurrent Processing
In `app/services/job_queue.py`, you can reduce the max queue size:
```python
# Reduce from 10 to 3 to limit concurrent processing
job_queue = JobQueue(max_queue_size=3)
```

### 3. Use Lower Resolution
When creating videos, use lower resolutions:
```json
{
  "resolution": "720x1280",
  "frame_rate": 24
}
```

## Advanced Configuration

### Custom Resource Limits
For systems with different capabilities:

**High-End System (16GB+ RAM):**
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 12G
      reservations:
        memory: 6G
```

**Medium System (8GB RAM):**
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G
```

**Low-End System (4GB RAM):**
```yaml
api:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

## Docker Commands for Monitoring

```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Check Docker memory settings
docker inspect <container_name> | grep -i memory

# View container logs
docker-compose logs api
```

## When to Contact Support

If you continue to experience issues after implementing these solutions:
1. Provide system specifications (RAM, CPU)
2. Include relevant log files
3. Describe the specific operations being performed
4. Mention any error messages or patterns observed