import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class WebScraper(BaseScraper):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.use_playwright = config.get('use_playwright', False)

    async def scrape(self, url: str, selector: Optional[str] = None) -> Dict:
        try:
            if self.use_playwright:
                html = await self.scrape_with_playwright(url, selector)
            else:
                html = self.scrape_with_requests(url)

            texts = self.parse_html(html, selector)
            metadata = self.extract_metadata(html)

            return {
                'url': url,
                'texts': texts,
                'metadata': metadata,
                'scraped_at': datetime.utcnow(),
                'success': True,
                'error': None
            }

        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            return {
                'url': url,
                'texts': [],
                'metadata': {},
                'scraped_at': datetime.utcnow(),
                'success': False,
                'error': str(e)
            }

    async def scrape_multiple(self, urls: List[Dict]) -> List[Dict]:
        tasks = []
        for url_config in urls:
            url = url_config.get('url')
            selector = url_config.get('selector')
            if url:
                tasks.append(self.scrape(url, selector))

        results = await asyncio.gather(*tasks)
        return results

class NewsScaper(WebScraper):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.article_selectors = {
            'default': 'article, .article-content, .post-content',
            'title': 'h1, .article-title, .post-title',
            'body': '.article-body, .post-body, .content-body',
            'date': 'time, .publish-date, .article-date'
        }

    async def scrape_article(self, url: str) -> Dict:
        result = await self.scrape(url, self.article_selectors['default'])

        if result['success'] and result['texts']:
            result['article'] = {
                'title': self._extract_title(result['texts']),
                'body': self._extract_body(result['texts']),
                'summary': self._create_summary(result['texts'])
            }

        return result

    def _extract_title(self, texts: List[str]) -> str:
        if texts:
            return texts[0][:200] if texts[0] else ''
        return ''

    def _extract_body(self, texts: List[str]) -> str:
        if len(texts) > 1:
            return ' '.join(texts[1:])
        elif texts:
            return texts[0]
        return ''

    def _create_summary(self, texts: List[str], max_length: int = 500) -> str:
        full_text = ' '.join(texts)
        if len(full_text) <= max_length:
            return full_text
        return full_text[:max_length] + '...'

class SocialMediaScraper(WebScraper):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.use_playwright = True

    async def scrape_posts(self, url: str, post_selector: str) -> List[Dict]:
        try:
            html = await self.scrape_with_playwright(url, post_selector)
            posts = self.parse_posts(html, post_selector)
            return posts
        except Exception as e:
            logger.error(f"Failed to scrape posts from {url}: {str(e)}")
            return []

    def parse_posts(self, html: str, selector: str) -> List[Dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        posts = []

        for element in soup.select(selector):
            post_text = element.get_text(strip=True)
            if post_text:
                posts.append({
                    'text': post_text,
                    'extracted_at': datetime.utcnow()
                })

        return posts