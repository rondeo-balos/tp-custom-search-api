#!/bin/bash
# Deploy and test script for server

echo "🚀 Deploying Custom Search API with SearXNG..."

# Check if running on server
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Run this on the server!"
    exit 1
fi

echo "📦 Rebuilding Docker containers..."
docker-compose down
docker-compose up -d --build

echo ""
echo "⏳ Waiting for containers to start..."
sleep 15

echo ""
echo "🔍 Checking SearXNG (port 8766)..."
curl -s http://localhost:8766/ | head -n 20 || echo "SearXNG not ready yet"

echo ""
echo "🏥 Checking API health (port 8765)..."
curl -s http://localhost:8765/health | jq '.' || echo "API health check failed"

echo ""
echo "🔍 Testing search..."
curl -s "http://localhost:8765/customsearch/v1?key=your_api_key&q=test+search" | jq '.items | length'

echo ""
echo "📋 Checking debug logs..."
docker exec tp-custom-search-api ls -lh /app/logs/ 2>/dev/null || echo "No logs yet"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Useful commands:"
echo "   docker logs tp-custom-search-api         # API logs"
echo "   docker logs tp-search-searxng            # SearXNG logs"
echo "   docker exec tp-custom-search-api ls /app/logs/  # List debug files"
echo ""
echo "🌐 Access:"
echo "   API: http://your-server:8765"
echo "   SearXNG: http://your-server:8766"
