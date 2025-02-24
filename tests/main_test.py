import json
import unittest
from unittest.mock import patch, AsyncMock
from main import EcommerceCrawler, process_urls_chunk


class TestEcommerceCrawler(unittest.TestCase):
    def setUp(self):
        self.domains = ["https://www.example.com", "https://www.testsite.com"]
        self.crawler = EcommerceCrawler(self.domains)

    @patch('crawler.get_sitemap_url', new_callable=AsyncMock)
    @patch('crawler.extract_urls_from_sitemap', new_callable=AsyncMock)
    def test_crawl_domain(self, mock_extract, mock_get_sitemap):
        mock_get_sitemap.return_value = "https://www.example.com/sitemap.xml"
        mock_extract.return_value = [
            "https://www.example.com/product/item1",
            "https://www.example.com/product/item2",
            "https://www.example.com/about"
        ]

        self.crawler.run()
        self.assertIn("https://www.example.com", self.crawler.results)
        self.assertEqual(len(self.crawler.results["https://www.example.com"]), 2)

    def test_process_urls_chunk(self):
        urls = [
            "https://www.example.com/product/item1",
            "https://www.example.com/product/item2",
            "https://www.example.com/about"
        ]
        result = process_urls_chunk("https://www.example.com", urls)
        self.assertEqual(len(result["https://www.example.com"]), 2)

    def test_save_results(self):
        self.crawler.results = {
            "https://www.example.com": [
                "https://www.example.com/product/item1"
            ]
        }
        self.crawler.save_results("test_results.json")
        with open("test_results.json", "r") as f:
            data = json.load(f)
        self.assertIn("https://www.example.com", data)
        self.assertEqual(len(data["https://www.example.com"]), 1)


if __name__ == '__main__':
    unittest.main()