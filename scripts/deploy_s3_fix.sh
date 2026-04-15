#!/bin/bash

# Deploy URL fix to production
# This script removes presigned URL generation and fixes malformed URLs

echo "🚀 Deploying URL fix to production..."

# Build the updated API container
echo "🔨 Building updated API container..."
docker-compose build api

if [ $? -ne 0 ]; then
    echo "❌ Failed to build API container"
    exit 1
fi

# Restart the API service
echo "🔄 Restarting API service..."
docker-compose up -d api

if [ $? -ne 0 ]; then
    echo "❌ Failed to restart API service"
    exit 1
fi

# Wait for the service to start
echo "⏳ Waiting for API service to start..."
sleep 15

# Test the library endpoint
echo "🧪 Testing library endpoint..."
response=$(curl -s -H "X-API-Key: ${API_KEY:-your_api_key_here}" \
  "http://localhost:8005/api/v1/library/content?limit=1&offset=0&content_type=all")

if echo "$response" | grep -q '"content"'; then
    echo "✅ Library endpoint is responding"
    
    # Check if file URLs are populated
    if echo "$response" | grep -q '"file_url":"http'; then
        echo "✅ File URLs are being generated successfully"
    else
        echo "⚠️ File URLs are still empty - may need more time or additional fixes"
    fi
else
    echo "❌ Library endpoint is not responding properly"
    echo "Response: $response"
fi

echo "🎉 URL fix deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check the application logs: docker-compose logs -f api"
echo "2. Test the library at: http://localhost:8000/dashboard/library"
echo "3. Verify that images and media are displaying properly"
echo "4. URLs should now be clean without double prefixes"
