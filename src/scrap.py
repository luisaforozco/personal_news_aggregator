# src/scraper.py
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
from urllib.parse import urlparse
import aiohttp
import asyncio
import ssl
import certifi  # Add this import

class NewsScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Updated URLs with www where needed
        self.news_sources = {
            'tech_news': [
                'https://news.ycombinator.com',
                'https://www.techcrunch.com',  # Added www
            ],
            'general_news': [
                'https://www.reuters.com',  # Added www
            ]
        }
        # Create SSL context
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch webpage content asynchronously"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(
                url, 
                headers=self.headers, 
                ssl=self.ssl_context,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    return await response.text()
                self.logger.error(f"Failed to fetch {url}: Status {response.status}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def parse_article(self, html: str, source_url: str) -> List[Dict]:
        """Parse HTML content for news articles"""
        articles = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Specific parsing for Hacker News
            if 'ycombinator' in source_url:
                for item in soup.select('.athing'):
                    try:
                        title_element = item.select_one('.titleline > a')
                        if title_element:
                            title = title_element.text.strip()
                            link = title_element['href']
                            
                            articles.append({
                                'title': title,
                                'link': link,
                                'source_url': source_url,
                                'scraped_at': datetime.utcnow().isoformat()
                            })
                    except Exception as e:
                        self.logger.error(f"Error parsing HN article: {str(e)}")
                        continue
            
            # Generic parsing for other sites
            else:
                for article in soup.find_all(['article', 'div.story']):  # Adjust selectors as needed
                    try:
                        title_element = article.find(['h1', 'h2', 'h3', '.title'])
                        link_element = article.find('a')
                        
                        if title_element and link_element:
                            title = title_element.text.strip()
                            link = link_element['href']
                            
                            # Make link absolute if it's relative
                            if not link.startswith('http'):
                                base_url = f"{urlparse(source_url).scheme}://{urlparse(source_url).netloc}"
                                link = f"{base_url}{link}"
                            
                            articles.append({
                                'title': title,
                                'link': link,
                                'source_url': source_url,
                                'scraped_at': datetime.utcnow().isoformat()
                            })
                    except Exception as e:
                        self.logger.error(f"Error parsing article: {str(e)}")
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing content from {source_url}: {str(e)}")
        
        return articles

    async def scrape_source(self, session: aiohttp.ClientSession, url: str) -> List[Dict]:
        """Scrape a single news source"""
        content = await self.fetch_page(session, url)
        if content:
            return self.parse_article(content, url)
        return []

    async def scrape_all_sources(self) -> Dict[str, List[Dict]]:
        """Scrape all configured news sources"""
        all_articles = {}
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            for category, urls in self.news_sources.items():
                tasks = [self.scrape_source(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                category_articles = []
                for result in results:
                    if isinstance(result, list):
                        category_articles.extend(result)
                    else:
                        self.logger.error(f"Error in scraping: {result}")
                
                all_articles[category] = category_articles
                
        return all_articles

    def print_articles(self, articles: Dict[str, List[Dict]]):
        """Print scraped articles in a readable format"""
        for category, category_articles in articles.items():
            print(f"\n=== {category.upper()} ===\n")
            
            if not category_articles:
                print("No articles found.")
                continue
                
            for i, article in enumerate(category_articles, 1):
                print(f"\nArticle {i}:")
                print("-" * 50)
                print(f"Title: {article.get('title', 'N/A')}")
                print(f"Link: {article.get('link', 'N/A')}")
                print(f"Source: {article.get('source_url', 'N/A')}")
                print(f"Scraped at: {article.get('scraped_at', 'N/A')}")
                print("-" * 50)

async def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize scraper
    scraper = NewsScraper()
    
    # Scrape articles
    articles = await scraper.scrape_all_sources()
    
    # Print articles
    scraper.print_articles(articles)

if __name__ == "__main__":
    asyncio.run(main())
