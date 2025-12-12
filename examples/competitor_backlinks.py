"""
Example: Competitor backlink finder using TP Custom Search API
Similar to your PHP BacklinkOpportunityFinder
"""

import requests
from typing import List, Dict
from urllib.parse import urlparse


API_URL = "http://localhost:8765/customsearch/v1"
API_KEY = "your-secret-api-key-here"


def search_by_competitor(competitor_domain: str, limit: int = 50) -> List[Dict]:
    """
    Search for backlinks referring to a competitor domain
    
    Args:
        competitor_domain: Competitor's domain (e.g., 'example.com')
        limit: Maximum number of opportunities to find
    
    Returns:
        List of backlink opportunities
    """
    # Clean domain
    competitor_domain = competitor_domain.replace('https://', '').replace('http://', '')
    competitor_domain = competitor_domain.replace('www.', '')
    
    all_opportunities = []
    seen_urls = set()
    
    # Build query variations (similar to your PHP code)
    queries = [
        f'"{competitor_domain}" -site:{competitor_domain}',
        f'"{competitor_domain}" (article OR blog OR post) -site:{competitor_domain}',
        f'"{competitor_domain}" (directory OR listing) -site:{competitor_domain}',
    ]
    
    for query in queries:
        print(f"Searching: {query}")
        
        # Paginate through results
        start_index = 1
        while len(all_opportunities) < limit and start_index <= 91:
            params = {
                "q": query,
                "key": API_KEY,
                "num": 10,
                "start": start_index
            }
            
            try:
                response = requests.get(API_URL, params=params)
                response.raise_for_status()
                results = response.json()
                
                items = results.get("items", [])
                if not items:
                    break
                
                for item in items:
                    url = item['link']
                    
                    # Skip if already seen
                    if url in seen_urls:
                        continue
                    
                    # Validate opportunity
                    if not is_valid_opportunity(url):
                        continue
                    
                    seen_urls.add(url)
                    
                    opportunity = {
                        'url': url,
                        'domain': extract_domain(url),
                        'title': item['title'],
                        'snippet': item['snippet'],
                        'type': detect_opportunity_type(item['title'], item['snippet']),
                        'keyword': f"competitor:{competitor_domain}"
                    }
                    
                    all_opportunities.append(opportunity)
                    
                    if len(all_opportunities) >= limit:
                        break
                
                start_index += 10
                
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
                break
        
        if len(all_opportunities) >= limit:
            break
    
    return all_opportunities


def is_valid_opportunity(url: str) -> bool:
    """Check if URL is a valid opportunity"""
    blacklist = [
        'facebook.com', 'twitter.com', 'linkedin.com',
        'instagram.com', 'youtube.com', 'pinterest.com',
        'reddit.com', 'quora.com', 'medium.com'
    ]
    
    url_lower = url.lower()
    for domain in blacklist:
        if domain in url_lower:
            return False
    
    return True


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    parsed = urlparse(url)
    host = parsed.netloc
    host = host.replace('www.', '')
    return host


def detect_opportunity_type(title: str, snippet: str) -> str:
    """Detect opportunity type from content"""
    text = (title + ' ' + snippet).lower()
    
    if any(keyword in text for keyword in ['guest post', 'write for us', 'contribute']):
        return 'blog'
    elif any(keyword in text for keyword in ['forum', 'community', 'discussion']):
        return 'forum'
    elif any(keyword in text for keyword in ['news', 'newspaper', 'journal']):
        return 'news'
    elif any(keyword in text for keyword in ['directory', 'listing']):
        return 'platform'
    
    return 'blog'


def main():
    """Example usage"""
    print("Competitor Backlink Finder")
    print("=" * 60)
    
    competitor = "example.com"
    print(f"\nSearching for backlinks to: {competitor}")
    print("This may take a few minutes...\n")
    
    opportunities = search_by_competitor(competitor, limit=20)
    
    print(f"\nFound {len(opportunities)} backlink opportunities:\n")
    
    for idx, opp in enumerate(opportunities, 1):
        print(f"{idx}. {opp['title']}")
        print(f"   Type: {opp['type']}")
        print(f"   Domain: {opp['domain']}")
        print(f"   URL: {opp['url']}")
        print(f"   Snippet: {opp['snippet'][:100]}...")
        print()


if __name__ == "__main__":
    main()
