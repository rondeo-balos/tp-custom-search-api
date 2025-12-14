# tp-custom-search-api
Searches over a website or collection of websites

✨ Key Features
1. 100% Google Custom Search API Compatible
  - Same endpoint structure: /customsearch/v1
  - Identical query parameters: q, key, num, start, etc.
  - Same JSON response format with items, queries, searchInformation

2. Response Format Matches Google's API
```
{
  "kind": "customsearch#search",
  "queries": { "request": [...], "nextPage": [...] },
  "searchInformation": { "searchTime": 2.45, "totalResults": "1234567" },
  "items": [...]
}
```

3. Drop-in Replacement for Your PHP Code
 - Just change the API URL from googleapis.com to your server
 - All parameters work identically
 - Response structure matches your existing parsing logic

4. Production Ready
 - Docker & Docker Compose support
 - SearXNG meta-search engine (no CAPTCHA blocking!)
 - API key authentication
 - Rate limiting (100 calls/hour default)
 - 7-day caching
 - Health checks & statistics endpoints

🔍 How It Works
- Uses SearXNG meta-search engine to aggregate results from multiple search engines
- SearXNG runs in a separate container and handles all the bot detection challenges
- Your API queries SearXNG instead of directly scraping search engines
- No more CAPTCHA issues!

🚀 Quick Start
```
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Configure
cp .env.example .env
# Edit .env and set API_KEY

# 3. Run
python -m app.main
```
Or with Docker:
```
docker-compose up -d
```

📡 Usage Example
```
curl "http://localhost:8000/customsearch/v1?q=python+programming&key=your-api-key&num=10"
```

Check the `examples` folder for Python examples showing how to use it for competitor backlink finding (similar to your PHP service).

