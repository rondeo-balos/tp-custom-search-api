import asyncio
import time
import logging
import os
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urlparse
from app.config import settings

logger = logging.getLogger(__name__)


class SearchScraper:
    """Search scraper using SearXNG meta-search engine"""
    
    def __init__(self):
        self.searxng_url = os.getenv("SEARXNG_URL", "http://searxng:8080")
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def initialize(self):
        """Initialize HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"Search scraper initialized with SearXNG at {self.searxng_url}")
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("Search scraper closed")
    
    async def search_google(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 1,
        language: Optional[str] = None,
        safe: str = "off"
    ) -> Dict[str, Any]:
        """
        Perform search using SearXNG and return results in Google Custom Search API format
        
        Args:
            query: Search query string
            num_results: Number of results to return (1-10)
            start_index: Starting position (1-based)
            language: Language restriction
            safe: Safe search setting
        
        Returns:
            Dict with search results matching Google's API format
        """
        await self.initialize()
        
        start_time = time.time()
        
        # Calculate page number from start_index
        page_num = ((start_index - 1) // num_results) + 1
        
        # Build SearXNG API request
        params = {
            'q': query,
            'format': 'json',
            'pageno': page_num,
            'language': language or 'en',
            'safesearch': 0 if safe == "off" else 1
        }
        
        try:
            logger.info(f"Querying SearXNG: {self.searxng_url}/search with query={query}")
            
            response = await self.client.get(
                f"{self.searxng_url}/search",
                params=params
            )
            response.raise_for_status()
            
            searxng_results = response.json()
            
            # Save debug info
            try:
                os.makedirs('/app/logs', exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                debug_file = f'/app/logs/searxng_results_{timestamp}.json'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(searxng_results, f, indent=2)
                logger.info(f"Debug JSON saved to {debug_file}")
            except Exception as e:
                logger.warning(f"Could not save debug files: {e}")
            
            # Convert SearXNG results to Google Custom Search API format
            results = self._convert_searxng_results(
                searxng_results, 
                query, 
                num_results, 
                start_index
            )
            
            # Add timing
            search_time = time.time() - start_time
            results['searchInformation']['searchTime'] = round(search_time, 3)
            results['searchInformation']['formattedSearchTime'] = f"{search_time:.2f}"
            
            logger.info(f"Search completed: {len(results.get('items', []))} results in {search_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise
    
    def _convert_searxng_results(
        self,
        searxng_data: Dict[str, Any],
        query: str,
        num_results: int,
        start_index: int
    ) -> Dict[str, Any]:
        """Convert SearXNG JSON results to Google Custom Search API format"""
        items = []
        
        # Get results from SearXNG response
        searxng_results = searxng_data.get('results', [])
        
        if not searxng_results:
            logger.warning("No results found in SearXNG response")
        else:
            logger.info(f"Found {len(searxng_results)} results from SearXNG")
        
        # Limit to requested number of results
        limited_results = searxng_results[:num_results]
        
        for idx, result in enumerate(limited_results):
            try:
                item = self._convert_searxng_item(result, start_index + idx)
                if item:
                    items.append(item)
            except Exception as e:
                logger.warning(f"Failed to convert result: {str(e)}")
                continue
        
        # Get total results count (SearXNG doesn't always provide this)
        total_results = searxng_data.get('number_of_results', len(searxng_results) * 100)
        
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
                    "count": len(items),
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
    
    def _convert_searxng_item(self, result: Dict[str, Any], position: int) -> Optional[Dict[str, Any]]:
        """Convert individual SearXNG result to Google Custom Search API format"""
        url = result.get('url')
        if not url:
            return None
        
        title = result.get('title', 'No title')
        content = result.get('content', '')
        
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
            "snippet": content,
            "htmlSnippet": content,
            "formattedUrl": formatted_url,
            "htmlFormattedUrl": formatted_url,
            "pagemap": {}
        }


# Global scraper instance
scraper = SearchScraper()
