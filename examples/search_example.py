"""
Example usage of TP Custom Search API
"""

import requests
import json

# API Configuration
API_URL = "http://localhost:8765/customsearch/v1"
API_KEY = "your-secret-api-key-here"


def search(query: str, num_results: int = 10, start_index: int = 1):
    """
    Perform a search using the custom search API
    
    Args:
        query: Search query string
        num_results: Number of results to return (1-10)
        start_index: Starting position (1-91)
    
    Returns:
        dict: Search results in Google Custom Search API format
    """
    params = {
        "q": query,
        "key": API_KEY,
        "num": num_results,
        "start": start_index
    }
    
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    
    return response.json()


def paginated_search(query: str, total_results: int = 30):
    """
    Perform paginated search to get more than 10 results
    
    Args:
        query: Search query string
        total_results: Total number of results to fetch
    
    Returns:
        list: All search result items
    """
    all_items = []
    start_index = 1
    
    while len(all_items) < total_results and start_index <= 91:
        print(f"Fetching results {start_index}-{start_index + 9}...")
        
        results = search(query, num_results=10, start_index=start_index)
        items = results.get("items", [])
        
        if not items:
            break
        
        all_items.extend(items)
        start_index += 10
    
    return all_items[:total_results]


def main():
    """Example usage"""
    
    # Simple search
    print("=" * 60)
    print("Example 1: Simple Search")
    print("=" * 60)
    
    results = search("python programming", num_results=5)
    
    print(f"\nQuery: {results['queries']['request'][0]['searchTerms']}")
    print(f"Total Results: {results['searchInformation']['formattedTotalResults']}")
    print(f"Search Time: {results['searchInformation']['formattedSearchTime']}s")
    print(f"\nTop {len(results['items'])} Results:\n")
    
    for idx, item in enumerate(results['items'], 1):
        print(f"{idx}. {item['title']}")
        print(f"   URL: {item['link']}")
        print(f"   {item['snippet'][:100]}...")
        print()
    
    # Paginated search
    print("=" * 60)
    print("Example 2: Paginated Search (30 results)")
    print("=" * 60)
    
    all_items = paginated_search("web scraping tutorial", total_results=30)
    
    print(f"\nFetched {len(all_items)} total results")
    print("\nAll URLs:")
    for idx, item in enumerate(all_items, 1):
        print(f"{idx}. {item['link']}")
    
    # Language-specific search
    print("\n" + "=" * 60)
    print("Example 3: Language-Specific Search")
    print("=" * 60)
    
    params = {
        "q": "machine learning",
        "key": API_KEY,
        "num": 5,
        "lr": "lang_en"  # English only
    }
    
    response = requests.get(API_URL, params=params)
    results = response.json()
    
    print(f"\nEnglish results for 'machine learning':")
    for item in results['items']:
        print(f"- {item['title']}")


if __name__ == "__main__":
    main()
