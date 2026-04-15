#!/bin/bash
set -e

echo "🎤 Setting up Griot with Piper TTS..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file to add your API keys and configuration"
    echo ""
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "🚀 Starting services with Piper TTS..."

# For development (with extended models)
if [ "${1:-}" = "dev" ]; then
    echo "🔧 Starting in development mode with extended language models..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
else
    # Production mode
    echo "🏭 Starting in production mode..."
    docker-compose up -d
fi

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are healthy
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Access your application at: http://localhost:8000"
    echo "🎵 Piper TTS models will be downloaded automatically on first run"
    echo ""
    echo "📊 To check model download progress:"
    echo "   docker-compose logs -f api | grep -i piper"
    echo ""
    echo "🛠️  Useful commands:"
    echo "   docker-compose logs -f          # View all logs"
    echo "   docker-compose down             # Stop services"
    echo "   docker-compose restart api      # Restart API service"
    echo ""
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose logs
    exit 1
fi