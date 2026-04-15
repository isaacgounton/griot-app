
# Frontend build stage  
FROM node:18-alpine as frontend-builder
WORKDIR /frontend

# Copy package files and install dependencies (cache friendly)
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install --legacy-peer-deps --include=dev

# Copy source and build
COPY frontend/ ./
# Use relative URLs in production so API calls go to the same origin
ENV VITE_API_BASE_URL=""
RUN npm run build

# Base stage with dependencies
FROM python:3.12-slim as base

WORKDIR /app

# Install system dependencies including UV
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr tesseract-ocr-eng build-essential \
    wget git fontconfig curl ca-certificates postgresql-client redis-tools \
    libpq-dev && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock requirements-*.txt ./

# Install Python dependencies in stages to avoid memory/network issues
# Stage 1: Core web framework dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --requirement requirements-web.txt \
    && echo "Web framework dependencies installed"

# Stage 2: Database dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --requirement requirements-db.txt \
    && echo "Database dependencies installed"

# Stage 3: Authentication and security dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --requirement requirements-auth.txt \
    && echo "Auth/Security dependencies installed"

# Stage 4: Media processing dependencies (includes edge-tts, moviepy)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --requirement requirements-media.txt \
    && echo "Media processing dependencies installed"

# Stage 5: AI/LLM dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --requirement requirements-ai.txt \
    && echo "AI/LLM dependencies installed"

# Stage 6: Utility dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --requirement requirements-utils.txt \
    && echo "Utility dependencies installed"

# Stage 7: Heavy ML dependencies (installed last due to size/complexity)
# Install PyTorch CPU first, then other dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir torch>=2.0.0 torchvision>=0.15.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --requirement requirements-ml.txt \
    && pip cache purge \
    && rm -rf /tmp/* \
    && echo "ML dependencies installed"

# Final verification
RUN echo "All dependencies installed successfully"

# Create directories first (cached - done before app code)
RUN mkdir -p /usr/share/fonts/truetype/custom /app/temp/output /app/models/huggingface /tmp/huggingface_cache /app/cache/huggingface

# Ensure proper permissions for cache directories
RUN chmod -R 755 /tmp/huggingface_cache /app/models/huggingface /app/cache/huggingface

# Copy ONLY fonts directory separately to avoid cache invalidation from app/ changes
# Use a specific path that won't trigger rebuilds when other app files change
COPY app/static/fonts/ /usr/share/fonts/truetype/custom/
RUN fc-cache -f -v

# Test stage for dependency validation
FROM base as test
# Install additional test dependencies only
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir pytest pytest-asyncio black flake8 mypy pre-commit jupyter ipython \
    && echo "Test dependencies installed successfully"

# Development stage
FROM base as development
# Install additional development dependencies only
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir pytest pytest-asyncio black flake8 mypy pre-commit jupyter ipython \
    && echo "Development dependencies installed successfully"

# Copy scripts and make them executable (changes less frequently)
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Copy static files (changes less frequently than app code)
COPY app/static/ ./static/
COPY app/static/ ./static_backup/

# Copy frontend source for development builds
COPY frontend/ ./frontend/
WORKDIR /app/frontend
RUN --mount=type=cache,target=/root/.npm \
    npm install && npm run build
WORKDIR /app

# Copy application code LAST (changes most frequently - minimizes rebuild)
COPY app/ ./app/
COPY *.py ./

# Use reload for development (lazy loading - no model downloads at startup)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/app"]

# Production stage
FROM base as production

# Copy scripts and make them executable (changes less frequently)
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Copy static files (changes less frequently than app code)
COPY app/static/ ./static/
COPY app/static/ ./static_backup/

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Copy application code LAST (changes most frequently - minimizes rebuild)
COPY app/ ./app/
COPY *.py ./

# Expose the ports the app runs on
EXPOSE 8000
EXPOSE 8001

# Command to run the application using startup script
CMD ["./scripts/startup.sh"] 