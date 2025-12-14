#!/bin/bash
# Deploy and test script for server

echo "🚀 Deploying to server..."
echo ""
echo "Instructions:"
echo "1. Upload these files to your server:"
echo "   - app/scraper.py (updated with debug logging)"
echo "   - deploy_and_test.sh (this file)"
echo ""
echo "2. On the server, run:"
echo "   chmod +x deploy_and_test.sh"
echo "   ./deploy_and_test.sh"
echo ""

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
sleep 10

echo ""
echo "🏥 Checking health..."
curl -s http://localhost:8765/health | jq '.' || echo "Health check failed"

echo ""
echo "🔍 Testing search..."
curl -s "http://localhost:8765/customsearch/v1?key=your_api_key&q=Personal+Injury+Accident+Lawyers+near+Carrollton" | jq '.items | length'

echo ""
echo "📋 Checking logs for debug files..."
docker exec tp-custom-search-api-api-1 ls -lh /app/logs/ 2>/dev/null || echo "No logs directory yet"

echo ""
echo "📝 To view debug HTML/screenshots:"
echo "   docker exec tp-custom-search-api-api-1 ls -lh /app/logs/"
echo "   docker cp tp-custom-search-api-api-1:/app/logs/ddg_search_*.html ."
echo "   docker cp tp-custom-search-api-api-1:/app/logs/ddg_search_*.png ."
echo ""
echo "📊 To check container logs:"
echo "   docker logs tp-custom-search-api-api-1"
echo ""
