#!/usr/bin/env python3
"""Debug script to test DuckDuckGo HTML structure"""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import sys


async def test_duckduckgo_search(query: str):
    """Test DuckDuckGo search and inspect HTML structure"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        print(f"\n🔍 Testing URL: {url}\n")
        
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        # Wait a bit for content to load
        await page.wait_for_timeout(3000)
        
        # Take screenshot
        await page.screenshot(path='ddg_debug.png')
        print("📸 Screenshot saved: ddg_debug.png")
        
        # Get HTML content
        content = await page.content()
        
        # Save HTML to file
        with open('ddg_debug.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("💾 HTML saved: ddg_debug.html")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'lxml')
        
        # Test various selectors
        print("\n" + "="*60)
        print("TESTING SELECTORS:")
        print("="*60)
        
        selectors_to_test = [
            'div.result',
            'div.results',
            'div.web-result',
            'div.result__body',
            '.result',
            '[class*="result"]',
            'a.result__a',
            'a[class*="result"]',
        ]
        
        for selector in selectors_to_test:
            elements = soup.select(selector)
            print(f"\n{selector}: {len(elements)} found")
            if elements and len(elements) > 0:
                print(f"  First element: {str(elements[0])[:200]}...")
        
        # Check all divs with class
        print("\n" + "="*60)
        print("ALL DIV CLASSES:")
        print("="*60)
        div_classes = set()
        for div in soup.find_all('div', class_=True):
            classes = div.get('class')
            if isinstance(classes, list):
                div_classes.update(classes)
        for cls in sorted(div_classes):
            print(f"  .{cls}")
        
        # Check all links
        print("\n" + "="*60)
        print("ALL LINK CLASSES:")
        print("="*60)
        link_classes = set()
        for a in soup.find_all('a', class_=True):
            classes = a.get('class')
            if isinstance(classes, list):
                link_classes.update(classes)
        for cls in sorted(link_classes):
            print(f"  .{cls}")
        
        # Find potential result containers
        print("\n" + "="*60)
        print("POTENTIAL RESULT CONTAINERS:")
        print("="*60)
        
        # Look for divs that might contain results
        for div in soup.find_all('div', limit=50):
            classes = div.get('class', [])
            if any('result' in str(c).lower() for c in classes):
                print(f"\nFound: {classes}")
                # Check for links inside
                links = div.find_all('a', href=True)
                if links:
                    print(f"  Contains {len(links)} links")
                    if links[0].get('href'):
                        print(f"  First link: {links[0].get('href')[:100]}")
                    if links[0].get_text(strip=True):
                        print(f"  First link text: {links[0].get_text(strip=True)[:100]}")
        
        await browser.close()
        
        print("\n✅ Debug completed!")
        print("\nNext steps:")
        print("1. Check ddg_debug.png to see what the page looks like")
        print("2. Check ddg_debug.html to inspect the full HTML structure")
        print("3. Update selectors in scraper.py based on findings")


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Personal Injury Accident Lawyers near Carrollton"
    print(f"\n🚀 Testing DuckDuckGo with query: {query}")
    asyncio.run(test_duckduckgo_search(query))
