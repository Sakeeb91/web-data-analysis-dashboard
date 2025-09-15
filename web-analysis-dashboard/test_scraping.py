#!/usr/bin/env python3
"""Test web scraping functionality"""

import requests
from bs4 import BeautifulSoup

def test_scraping():
    print("Testing Web Scraping")
    print("="*50)

    # Test URL (a simple, reliable site)
    test_url = "http://quotes.toscrape.com/"

    try:
        # Make request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()

        print(f"✓ Successfully fetched: {test_url}")
        print(f"  Status Code: {response.status_code}")

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title = soup.find('title')
        if title:
            print(f"  Page Title: {title.get_text(strip=True)}")

        # Extract some quotes
        quotes = soup.select('.quote')[:3]  # Get first 3 quotes
        print(f"\n  Found {len(soup.select('.quote'))} quotes on the page")
        print("\n  First 3 quotes:")
        print("-"*40)

        for i, quote in enumerate(quotes, 1):
            text = quote.select_one('.text')
            author = quote.select_one('.author')
            if text and author:
                print(f"  {i}. {text.get_text()}")
                print(f"     - {author.get_text()}\n")

        print("="*50)
        print("✓ Web scraping is working correctly!")
        return True

    except requests.RequestException as e:
        print(f"✗ Error scraping {test_url}: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_scraping()