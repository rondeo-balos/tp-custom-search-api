import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)


class SearchScraper:
    """Playwright-based search scraper"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def initialize(self):
        """Initialize Playwright browser"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            logger.info("Playwright browser initialized")
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            logger.info("Playwright browser closed")
    
    async def search_google(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 1,
        language: Optional[str] = None,
        safe: str = "off"
    ) -> Dict[str, Any]:
        """
        Perform Google search and return results in Google Custom Search API format
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-10)
            start_index: Starting position (1-based)
            language: Language restriction (e.g., 'lang_en')
            safe: Safe search setting ('off', 'medium', 'high')
        
        Returns:
            Dict with search results matching Google's API format
        """
        await self.initialize()
        
        start_time = time.time()
        
        # Build Google search URL
        search_url = self._build_google_url(query, num_results, start_index, language, safe)
        
        try:
            # Create new page with context and anti-detection
            context = await self.browser.new_context(
                user_agent=settings.user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            page = await context.new_page()
            
            # Add stealth scripts
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """)
            
            # Navigate to search results
            logger.info(f"Navigating to: {search_url}")
            
            # Add random delay to appear more human
            import random
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            await page.goto(search_url, wait_until='domcontentloaded', timeout=settings.timeout)
            
            # Wait for results to load - DuckDuckGo selector
            try:
                await page.wait_for_selector('div.result, div.results', timeout=15000)
                logger.info("Search results loaded successfully")
            except:
                logger.warning("Search results container not found")
                # Take screenshot for debugging
                try:
                    await page.screenshot(path='/app/logs/failed_search.png')
                    logger.info("Screenshot saved to /app/logs/failed_search.png")
                except:
                    pass
            
            # Get page content
            content = await page.content()
            
            # Debug: Log page title and first 1000 chars
            title = await page.title()
            logger.info(f"Page title: {title}")
            logger.info(f"HTML preview (first 1000 chars): {content[:1000]}")
            
            # Close context
            await context.close()
            
            # Parse results
            results = self._parse_google_results(content, query, num_results, start_index)
            
            # Add timing information
            search_time = time.time() - start_time
            results['searchInformation']['searchTime'] = round(search_time, 3)
            results['searchInformation']['formattedSearchTime'] = f"{search_time:.2f}"
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise
    
    def _build_google_url(
        self,
        query: str,
        num_results: int,
        start_index: int,
        language: Optional[str],
        safe: str
    ) -> str:
        """Build DuckDuckGo HTML search URL with parameters"""
        # Use DuckDuckGo HTML version (easier to scrape, no JS required)
        base_url = "https://html.duckduckgo.com/html/"
        params = [
            f"q={quote_plus(query)}"
        ]
        
        # DuckDuckGo HTML doesn't support pagination well, but we can work with it
        # We'll fetch more and slice client-side
        
        return f"{base_url}?{'&'.join(params)}"
    
    def _parse_google_results(
        self,
        html: str,
        query: str,
        num_results: int,
        start_index: int
    ) -> Dict[str, Any]:
        """Parse Google search results HTML"""
        soup = BeautifulSoup(html, 'lxml')
        
        items = []
        
        # Find search result containers - try multiple selectors
        search_results = soup.select('div.g')
        
        if not search_results:
        items = []
        
        # Find search result containers - DuckDuckGo HTML selectors
        search_results = soup.select('div.result')
        
        if not search_results:
            logger.warning(f"No results found. HTML preview: {html[:500]}")
        
        # Handle pagination (start_index)
        start_pos = start_index - 1
        end_pos = start_pos + num_results
        paginated_results = search_results[start_pos:end_pos]
        
        for idx, result in enumerate(paginated_results):r(e)}")
                continue
        
        # Extract total results estimate
        total_results = self._extract_total_results(soup)
        
        # Build response matching Google's format
        response = {
            "kind": "customsearch#search",
            "url": {
                "type": "application/json",
                "template": f"https://www.googleapis.com/customsearch/v1?q={{searchTerms}}"
            },
            "queries": {
                "request": [{
                    "title": f"Custom Search - {query}",
                    "totalResults": str(total_results),
                    "searchTerms": query,
                    "count": num_results,
                    "startIndex": start_index,
                    "inputEncoding": "utf8",
                    "outputEncoding": "utf8",
                    "safe": "off"
                }]
            },
            "searchInformation": {
                "searchTime": 0.0,
                "formattedSearchTime": "0.00",
                "totalResults": str(total_results),
                "formattedTotalResults": f"{total_results:,}"
            },
            "items": items
        }
        
        # Add next page query if more results available
        if len(items) == num_results and start_index + num_results <= settings.max_start_index:
            response["queries"]["nextPage"] = [{
                "title": f"Custom Search - {query}",
                "totalResults": str(total_results),
                "searchTerms": query,
                "count": num_results,
                "startIndex": start_index + num_results,
                "inputEncoding": "utf8",
                "outputEncoding": "utf8",
                "safe": "off"
            }]
        
        # Add previous page query if not on first page
        if start_index > 1:
            response["queries"]["previousPage"] = [{
                "title": f"Custom Search - {query}",
                "totalResults": str(total_results),
                "searchTerms": query,
                "count": num_results,
                "startIndex": max(1, start_index - num_results),
                "inputEncoding": "utf8",
                "outputEncoding": "utf8",
                "safe": "off"
            }]
        
        return response
    def _parse_search_item(self, result_elem, position: int) -> Optional[Dict[str, Any]]:
        """Parse individual search result (DuckDuckGo format)"""
        # Extract link from DuckDuckGo result
        link_elem = result_elem.select_one('a.result__a')
        if not link_elem or not link_elem.get('href'):
            return None
        
        url = link_elem.get('href')
        if not url.startswith('http'):
            return None
        
        # Extract title
        title_elem = result_elem.select_one('a.result__a')
        title = title_elem.get_text(strip=True) if title_elem else "No title"
        
        # Extract snippet
        snippet_elem = result_elem.select_one('a.result__snippet')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""3b, span.aCOpRe')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
        
        # Parse URL components
        parsed_url = urlparse(url)
        display_link = parsed_url.netloc
        formatted_url = f"{parsed_url.scheme}://{display_link}{parsed_url.path}"
        
        return {
            "kind": "customsearch#result",
            "title": title,
            "htmlTitle": self._html_escape(title),
            "link": url,
            "displayLink": display_link,
            "snippet": snippet,
            "htmlSnippet": self._html_escape(snippet),
            "formattedUrl": formatted_url,
            "htmlFormattedUrl": self._html_escape(formatted_url),
            "pagemap": {}
        }
    
    def _extract_total_results(self, soup: BeautifulSoup) -> int:
        """Extract total results count from Google results page"""
        # Try to find results stats
        stats_elem = soup.select_one('div#result-stats')
        if stats_elem:
            text = stats_elem.get_text()
            # Extract number from text like "About 1,234,567 results"
            import re
            match = re.search(r'About\s+([\d,]+)\s+results', text)
            if match:
                return int(match.group(1).replace(',', ''))
        
        # Default estimate
        return 10000
    
    @staticmethod
    def _html_escape(text: str) -> str:
        """Basic HTML escaping"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


# Global scraper instance
scraper = SearchScraper()
