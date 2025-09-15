import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import time

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)
        self.user_agent = config.get('user_agent', 'Mozilla/5.0')

    @abstractmethod
    async def scrape(self, url: str) -> Dict:
        pass

    async def scrape_with_playwright(self, url: str, selector: Optional[str] = None) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.user_agent)

            try:
                await page.goto(url, wait_until='networkidle')

                if selector:
                    await page.wait_for_selector(selector, timeout=10000)

                content = await page.content()
                await browser.close()
                return content

            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                await browser.close()
                raise

    def scrape_with_requests(self, url: str) -> str:
        headers = {'User-Agent': self.user_agent}

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise

    def parse_html(self, html: str, selector: Optional[str] = None) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        texts = []

        if selector:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    texts.append(text)
        else:
            text = soup.get_text(strip=True)
            if text:
                texts.append(text)

        return texts

    def extract_metadata(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {
            'title': '',
            'description': '',
            'keywords': [],
            'author': '',
            'published_date': None
        }

        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')

        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords = meta_keywords.get('content', '')
            metadata['keywords'] = [k.strip() for k in keywords.split(',')]

        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author:
            metadata['author'] = meta_author.get('content', '')

        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            try:
                metadata['published_date'] = datetime.fromisoformat(
                    time_tag['datetime'].replace('Z', '+00:00')
                )
            except:
                pass

        return metadata