import asyncio
import re
import json
import logging
import os
from urllib.parse import urljoin
import aiohttp
import xml.etree.ElementTree as ET
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Celery with configuration
celery_app = Celery('crawler', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

# Define common product URL patterns
PRODUCT_PATTERNS = [
    re.compile(r'/product/'),
    re.compile(r'/item/'),
    re.compile(r'/p/'),
    re.compile(r'/prod/'),
    re.compile(r'/products/'),
]

# Set custom headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}


# Async function to fetch content
async def fetch(session, url):
    """
    Asynchronously fetches the content of a given URL using aiohttp.
    Returns the response text if successful, otherwise returns None.
    """
    try:
        async with session.get(url, headers=HEADERS, timeout=30) as response:
            if response.status == 200:
                return await response.text()
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
    return None


# Get sitemap URL from robots.txt
async def get_sitemap_url(domain):
    """
    Attempts to retrieve the sitemap URL from a website's robots.txt.
    Falls back to common sitemap locations if not found.
    """
    async with aiohttp.ClientSession() as session:
        robots_url = urljoin(domain, "/robots.txt")
        content = await fetch(session, robots_url)
        if content:
            for line in content.splitlines():
                if line.lower().startswith("sitemap:"):
                    return line.split(": ", 1)[1].strip()
        for sitemap in [urljoin(domain, "/sitemap.xml"), urljoin(domain, "/sitemap")]:
            content = await fetch(session, sitemap)
            if content:
                return sitemap
    return None


# Async recursive sitemap extraction with deduplication
async def extract_urls_from_sitemap(session, sitemap_url, seen_sitemaps):
    """
    Recursively extracts URLs from sitemap and nested sitemaps.
    Prevents duplicate sitemap processing using a seen_sitemaps set.
    """
    if sitemap_url in seen_sitemaps:
        return []
    seen_sitemaps.add(sitemap_url)
    content = await fetch(session, sitemap_url)
    if not content:
        return []

    urls = []
    try:
        root = ET.fromstring(content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        if root.tag.endswith('sitemapindex'):
            for sitemap in root.findall('ns:sitemap', namespaces=namespace):
                loc = sitemap.find('ns:loc', namespaces=namespace)
                if loc is not None:
                    nested_urls = await extract_urls_from_sitemap(session, loc.text, seen_sitemaps)
                    urls.extend(nested_urls)
        elif root.tag.endswith('urlset'):
            for url in root.findall('ns:url', namespaces=namespace):
                loc = url.find('ns:loc', namespaces=namespace)
                if loc is not None:
                    urls.append(loc.text)
    except ET.ParseError:
        pass
    return urls


# Celery task to process URLs
@celery_app.task(name='crawler.process_urls_chunk')
def process_urls_chunk(domain, urls):
    """
    Filters the URLs to identify potential product pages based on predefined patterns.
    Returns a dictionary mapping the domain to the found product URLs.
    """
    product_urls = [url for url in urls if any(pattern.search(url) for pattern in PRODUCT_PATTERNS)]
    return {domain: product_urls}


class EcommerceCrawler:
    """
    Main class for handling the crawling process across multiple domains.
    """

    def __init__(self, domains):
        self.domains = list(set(domains))  # Remove duplicate domains
        self.results = {}

    def chunk_domains(self, lst, chunk_size):
        """
        Splits the list into chunks of a given size.
        """
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    async def crawl_domain(self, domain):
        """
        Crawls a specific domain by fetching and processing its sitemap URLs.
        Utilizes Celery to process URLs asynchronously in chunks.
        """
        sitemap_url = await get_sitemap_url(domain)
        if sitemap_url:
            async with aiohttp.ClientSession() as session:
                all_urls = await extract_urls_from_sitemap(session, sitemap_url, set())
                tasks = []
                for chunk in self.chunk_domains(all_urls, 10):
                    task = process_urls_chunk.delay(domain, chunk)
                    tasks.append(task)
                for task in tasks:
                    result = task.get()
                    for domain, urls in result.items():
                        if domain not in self.results:
                            self.results[domain] = []
                        self.results[domain].extend(urls)
                logging.info(f"Crawled {domain}: Found {len(self.results.get(domain, []))} product pages.")

    def run(self):
        """
        Starts the crawling process asynchronously.
        """
        asyncio.run(self._run_async())
        return self.results

    async def _run_async(self):
        """
        Runs asynchronous crawling for all provided domains concurrently.
        """
        await asyncio.gather(*(self.crawl_domain(domain) for domain in self.domains))

    def save_results(self, filename="results.json"):
        """
        Saves the crawling results to a JSON file, appending to existing data if available.
        """
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        for domain, urls in self.results.items():
            if domain not in existing_data:
                existing_data[domain] = []
            existing_data[domain].extend(urls)
            existing_data[domain] = list(set(existing_data[domain]))

        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=4)
        logging.info(f"Results saved to {filename}")


# Example usage
domains = ["https://www.snitch.co.in"]
crawler = EcommerceCrawler(domains)

if __name__ == "__main__":
    results = crawler.run()
    crawler.save_results()
    for domain, urls in results.items():
        logging.info(f"{domain}: {len(urls)} product pages found.")
