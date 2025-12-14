# Deployment Instructions

## What Changed
Added debug logging to `app/scraper.py` that will:
1. Save HTML content to `/app/logs/ddg_search_*.html`
2. Save screenshots to `/app/logs/ddg_search_*.png`
3. Try multiple CSS selectors to find DuckDuckGo results
4. Log which selector worked and how many results found

## Deploy to Server

### Option 1: Upload via Git
```bash
# On your machine
git add .
git commit -m "Add debug logging for DuckDuckGo scraper"
git push

# On server
cd /path/to/project
git pull
./deploy_and_test.sh
```

### Option 2: Upload Files Manually
Upload these files to server:
- `app/scraper.py`
- `deploy_and_test.sh`

Then on server:
```bash
chmod +x deploy_and_test.sh
./deploy_and_test.sh
```

## After Deployment

### Test the search
```bash
curl "http://localhost:8765/customsearch/v1?key=your_api_key&q=test+search"
```

### Check debug files
```bash
# List debug files
docker exec tp-custom-search-api-api-1 ls -lh /app/logs/

# Copy HTML to local
docker cp tp-custom-search-api-api-1:/app/logs/ddg_search_*.html .

# Copy screenshots to local
docker cp tp-custom-search-api-api-1:/app/logs/ddg_search_*.png .
```

### Check logs for selector info
```bash
docker logs tp-custom-search-api-api-1 | grep "Found.*results using selector"
```

### Download debug files to your machine
```bash
# On server, after running a search
scp user@your-server:/path/to/project/ddg_search_*.html .
scp user@your-server:/path/to/project/ddg_search_*.png .
```

## What to Look For

The logs will show:
- ✅ "Found X results using selector: div.result" - Good! Selectors are working
- ⚠️ "No results found with any selector" - DuckDuckGo structure changed
- 📸 Screenshot shows what the page actually looks like
- 📄 HTML file shows the actual structure we can inspect

## Next Steps Based on Findings

If selectors work but items still empty:
- Check the `_parse_item()` method selectors

If no selectors work:
- Open the HTML file and find the correct structure
- Update selectors in `app/scraper.py`

If page looks weird in screenshot:
- DuckDuckGo might be blocking or showing CAPTCHA
- Need to adjust user agent or add more stealth
