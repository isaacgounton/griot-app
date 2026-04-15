#!/bin/bash
set -e

echo "🚀 Griot Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_warning "Please copy .env.example to .env and configure your environment variables."
    echo "cp .env.example .env"
    exit 1
fi

print_status ".env file found"

# Check for required environment variables
required_vars=(
    "API_KEY"
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "S3_ACCESS_KEY"
    "S3_SECRET_KEY"
    "S3_BUCKET_NAME"
    "FRONTEND_URL"
)

echo "🔍 Checking required environment variables..."
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env || grep -q "^${var}=your_" .env; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing or unconfigured environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    print_warning "Please configure these variables in your .env file before deployment."
    exit 1
fi

print_status "All required environment variables are configured"

# Choose deployment mode
echo ""
echo "Select deployment mode:"
echo "1) Development (with hot reload)"
echo "2) Production (optimized)"
echo "3) Production with rebuild (slower, ensures latest changes)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        print_status "Starting in development mode..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
        ;;
    2)
        print_status "Starting in production mode..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        ;;
    3)
        print_status "Building and starting in production mode..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        ;;
    *)
        print_error "Invalid choice. Please select 1, 2, or 3."
        exit 1
        ;;
esac

if [ $choice -eq 2 ] || [ $choice -eq 3 ]; then
    echo ""
    print_status "Production deployment started!"
    echo ""
    echo "📊 To check status:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps"
    echo ""
    echo "📋 To view logs:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f api"
    echo ""
    echo "🔧 To stop:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
    echo ""
    
    # Wait for services to be healthy
    echo "⏳ Waiting for services to be healthy..."
    timeout=120
    counter=0
    
    while [ $counter -lt $timeout ]; do
        if docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps | grep -q "Up (healthy).*api"; then
            print_status "API service is healthy!"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        if [ $((counter % 10)) -eq 0 ]; then
            echo "⏳ Still waiting... (${counter}s/${timeout}s)"
        fi
    done
    
    if [ $counter -ge $timeout ]; then
        print_warning "Service health check timed out. Check logs with:"
        echo "docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs api"
    else
        # Test API endpoints
        api_port=$(grep "API_PORT" .env | cut -d'=' -f2)
        api_port=${api_port:-8000}
        
        echo ""
        echo "🧪 Testing API endpoints..."
        
        if curl -s "http://localhost:${api_port}/docs" > /dev/null; then
            print_status "API documentation accessible at: http://localhost:${api_port}/docs"
        else
            print_warning "API not responding yet. It may still be starting up."
        fi
        
        if curl -s "http://localhost:${api_port}/dashboard" > /dev/null; then
            print_status "Dashboard accessible at: http://localhost:${api_port}/dashboard"
        else
            print_warning "Dashboard not responding yet. It may still be starting up."
        fi
        
        echo ""
        print_status "🎉 Deployment completed successfully!"
        echo "API is running at: http://localhost:${api_port}"
    fi
fi