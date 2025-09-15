import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import time

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

try:
    from fake_useragent import UserAgent
    _UA_PROVIDER_AVAILABLE = True
except Exception:
    _UA_PROVIDER_AVAILABLE = False

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)
        self.user_agent = config.get('user_agent', 'Mozilla/5.0')
        self.rotate_user_agent = config.get('rotate_user_agent', False)
        self.respect_robots = config.get('respect_robots', False)
        self.rate_limit_interval = float(config.get('rate_limit_interval', 0))
        self._last_request_time: Dict[str, float] = {}
        self._robots_cache: Dict[str, RobotFileParser] = {}

    @abstractmethod
    async def scrape(self, url: str) -> Dict:
        pass

    async def scrape_with_playwright(self, url: str, selector: Optional[str] = None) -> str:
        if self.respect_robots and not self.is_allowed(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")

        await self._async_rate_limit(url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.get_user_agent())

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
        if self.respect_robots and not self.is_allowed(url):
            raise PermissionError(f"Blocked by robots.txt: {url}")

        headers = {'User-Agent': self.get_user_agent()}

        for attempt in range(self.max_retries):
            try:
                self._rate_limit(url)
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

    # --- Helpers: robots.txt, UA rotation, rate limiting ---
    def is_allowed(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            robots_url = urlunparse((parsed.scheme, parsed.netloc, '/robots.txt', '', '', ''))
            if robots_url not in self._robots_cache:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                except Exception:
                    # If robots cannot be fetched, be conservative and allow
                    rp.parse("")
                self._robots_cache[robots_url] = rp
            rp = self._robots_cache[robots_url]
            return rp.can_fetch(self.get_user_agent(), url)
        except Exception:
            # Fail-open to avoid blocking all requests in case of parser errors
            return True

    def get_user_agent(self) -> str:
        if self.rotate_user_agent:
            # Try fake_useragent, fall back to a small pool
            if _UA_PROVIDER_AVAILABLE:
                try:
                    ua = UserAgent()
                    return ua.random
                except Exception:
                    pass
            return self._fallback_user_agent()
        return self.user_agent

    def _fallback_user_agent(self) -> str:
        pool = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15.5 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/114 Safari/537.36',
        ]
        idx = int(time.time()) % len(pool)
        return pool[idx]

    def _rate_limit(self, url: str):
        if self.rate_limit_interval <= 0:
            return
        domain = urlparse(url).netloc
        now = time.time()
        last = self._last_request_time.get(domain, 0)
        delta = now - last
        if delta < self.rate_limit_interval:
            time.sleep(self.rate_limit_interval - delta)
        self._last_request_time[domain] = time.time()

    async def _async_rate_limit(self, url: str):
        if self.rate_limit_interval <= 0:
            return
        domain = urlparse(url).netloc
        now = time.time()
        last = self._last_request_time.get(domain, 0)
        delta = now - last
        if delta < self.rate_limit_interval:
            await asyncio.sleep(self.rate_limit_interval - delta)
        self._last_request_time[domain] = time.time()
