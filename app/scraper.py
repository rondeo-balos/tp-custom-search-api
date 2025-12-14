import asyncio
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)


class SearchScraper:
    """Playwright-based search scraper using DuckDuckGo"""
    
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
                    '--disable-blink-features=AutomationControlled'
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
        Perform search using DuckDuckGo and return results in Google Custom Search API format
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-10)
            start_index: Starting position (1-based)
            language: Language restriction (ignored for DDG)
            safe: Safe search setting
        
        Returns:
            Dict with search results matching Google's API format
        """
        await self.initialize()
        
        start_time = time.time()
        
        # Build DuckDuckGo search URL
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        try:
            context = await self.browser.new_context(
                user_agent=settings.user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            logger.info(f"Navigating to: {search_url}")
            await page.goto(search_url, wait_until='domcontentloaded', timeout=settings.timeout)
            
            # Wait for results
            try:
                await page.wait_for_selector('div.result', timeout=15000)
                logger.info("Search results loaded successfully")
            except:
                logger.warning("Search results container not found")
            
            content = await page.content()
            
            # Save HTML for debugging
            try:
                os.makedirs('/app/logs', exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                debug_file = f'/app/logs/ddg_search_{timestamp}.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Debug HTML saved to {debug_file}")
                
                # Also save a screenshot
                screenshot_file = f'/app/logs/ddg_search_{timestamp}.png'
                await page.screenshot(path=screenshot_file, full_page=True)
                logger.info(f"Debug screenshot saved to {screenshot_file}")
            except Exception as e:
                logger.warning(f"Could not save debug files: {e}")
            
            await context.close()
            
            # Parse results
            results = self._parse_results(content, query, num_results, start_index)
            
            # Add timing
            search_time = time.time() - start_time
            results['searchInformation']['searchTime'] = round(search_time, 3)
            results['searchInformation']['formattedSearchTime'] = f"{search_time:.2f}"
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise
    
    def _parse_results(
        self,
        html: str,
        query: str,
        num_results: int,
        start_index: int
    ) -> Dict[str, Any]:
        """Parse DuckDuckGo search results HTML"""
        soup = BeautifulSoup(html, 'lxml')
        items = []
        
        # Try multiple selectors for DuckDuckGo results
        search_results = []
        selectors = [
            'div.result',
            'div.results_links',
            'div.web-result',
            'div[class*="result"]',
            '.result',
        ]
        
        for selector in selectors:
            search_results = soup.select(selector)
            if search_results:
                logger.info(f"Found {len(search_results)} results using selector: {selector}")
                break
        
        if not search_results:
            logger.warning(f"No results found with any selector. HTML length: {len(html)}")
            # Log first 1000 chars of HTML for debugging
            logger.debug(f"HTML preview: {html[:1000]}")
        
        # Handle pagination
        start_pos = start_index - 1
        end_pos = start_pos + num_results
        paginated_results = search_results[start_pos:end_pos]
        
        for idx, result in enumerate(paginated_results):
            try:
                item = self._parse_item(result, start_index + idx)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse result: {str(e)}")
                continue
        
        # Build response
        total_results = len(search_results) * 100  # Estimate
        
        response = {
            "kind": "customsearch#search",
            "url": {
                "type": "application/json",
                "template": "https://www.googleapis.com/customsearch/v1?q={searchTerms}"
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
        
        return response
    
    def _parse_item(self, result_elem, position: int) -> Optional[Dict[str, Any]]:
        """Parse individual DuckDuckGo result"""
        # Extract link
        link_elem = result_elem.select_one('a.result__a')
        if not link_elem or not link_elem.get('href'):
            return None
        
        url = link_elem.get('href')
        if not url.startswith('http'):
            return None
        
        # Extract title
        title = link_elem.get_text(strip=True) if link_elem else "No title"
        
        # Extract snippet
        snippet_elem = result_elem.select_one('a.result__snippet')
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
        
        # Parse URL
        parsed_url = urlparse(url)
        display_link = parsed_url.netloc.replace('www.', '')
        formatted_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        return {
            "kind": "customsearch#result",
            "title": title,
            "htmlTitle": title,
            "link": url,
            "displayLink": display_link,
            "snippet": snippet,
            "htmlSnippet": snippet,
            "formattedUrl": formatted_url,
            "htmlFormattedUrl": formatted_url,
            "pagemap": {}
        }


# Global scraper instance
scraper = SearchScraper()
