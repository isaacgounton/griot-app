#!/bin/bash

# Production deployment script for Griot with full API key management
# This script sets up the complete API key management system in production

set -e  # Exit on error

echo "🚀 Starting Griot Production Deployment"
echo "============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it first."
    exit 1
fi

print_status "Docker Compose found"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating template..."
    cp .env.example .env 2>/dev/null || true
    print_info "Please update .env file with your production values before continuing"
fi

print_status "Environment configuration checked"

# Build and start services
print_info "Building and starting services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
print_info "Waiting for services to initialize..."
sleep 30

# Check if PostgreSQL is ready
print_info "Checking PostgreSQL connectivity..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_status "PostgreSQL is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "PostgreSQL failed to start within timeout"
        exit 1
    fi
    
    echo "Waiting for PostgreSQL... ($attempt/$max_attempts)"
    sleep 2
    ((attempt++))
done

# Check if Redis is ready
print_info "Checking Redis connectivity..."
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    print_status "Redis is ready"
else
    print_warning "Redis may not be fully ready, but continuing..."
fi

# Check if API service is ready
print_info "Checking API service..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -s -f http://localhost:8000/docs >/dev/null 2>&1; then
        print_status "API service is ready"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "API service failed to start within timeout"
        docker-compose logs api
        exit 1
    fi
    
    echo "Waiting for API service... ($attempt/$max_attempts)"
    sleep 2
    ((attempt++))
done

# Display service status
print_info "Service Status:"
docker-compose ps

# Display API key management endpoints
print_status "API Key Management Endpoints Available:"
echo "📋 Dashboard: http://localhost:8000/dashboard"
echo "🔧 Admin Panel: http://localhost:8000/admin"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🔑 API Keys API: http://localhost:8000/dashboard/api-keys"

# Check for admin user creation in logs
print_info "Checking admin user setup..."
if docker-compose logs api 2>/dev/null | grep -q "Created initial admin user"; then
    print_status "Admin user created successfully"
    echo "   📧 Email: admin@griot.com"
    echo "   🔒 Password: admin123"
    print_warning "Please change the default password in production!"
elif docker-compose logs api 2>/dev/null | grep -q "Found.*existing users"; then
    print_status "Existing users found in database"
else
    print_warning "Could not determine admin user status. Check logs manually."
fi

# Check for API key creation in logs
print_info "Checking API key setup..."
API_KEY_FROM_LOGS=$(docker-compose logs api 2>/dev/null | grep "Created admin API key" | sed -n 's/.*Created admin API key: \(oui_sk_[a-f0-9]*\).*/\1/p' | tail -1)

if [ ! -z "$API_KEY_FROM_LOGS" ]; then
    print_status "Admin API key created successfully"
    echo "   🔑 API Key: $API_KEY_FROM_LOGS"
    print_warning "Save this API key securely - it won't be shown again!"
elif docker-compose logs api 2>/dev/null | grep -q "Found.*existing API key"; then
    print_status "Existing API keys found in database"
else
    print_warning "Could not determine API key status. Check logs manually."
fi

# Display environment recommendations
print_info "Production Environment Recommendations:"
echo "1. 🔐 Change default passwords"
echo "2. 🔑 Secure API keys properly"
echo "3. 🔒 Configure HTTPS with SSL certificates"
echo "4. 📊 Set up monitoring and logging"
echo "5. 💾 Configure database backups"
echo "6. 🌐 Set proper CORS origins for your domain"

# Display next steps
print_status "Deployment Complete!"
echo ""
echo "🎉 Your Griot is now running with full API key management!"
echo ""
echo "Next Steps:"
echo "1. Access the dashboard: http://localhost:8000/dashboard"
echo "2. Login with admin credentials (see above)"
echo "3. Create and manage API keys through the web interface"
echo "4. Test API endpoints with your generated keys"
echo "5. Configure your applications to use the API"
echo ""
echo "For API documentation, visit: http://localhost:8000/docs"
echo ""
print_warning "Remember to update production passwords and secure your environment!"

exit 0