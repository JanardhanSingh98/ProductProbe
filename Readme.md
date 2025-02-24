# ProductProbe 🛒

**ProductProbe** is an advanced, scalable web crawler designed to extract product URLs from e-commerce websites. It efficiently handles large domain lists, processes sitemaps asynchronously using Celery, and saves the results in a structured JSON format.

## 🚀 Features

- ⚡ **Asynchronous** sitemap fetching and URL extraction
- 📌 **Celery integration** for scalable background task processing
- 🔍 Automatic detection of product pages using predefined indicators
- 🗂️ Handles **nested sitemaps** and various sitemap structures
- 🛡️ Robust error handling and optimized performance for large-scale crawling
- ❌ Duplicate domain filtering
- 💾 Persistent result saving with JSON file updates

## 📋 Requirements

- 🐍 Python 3.12+
- 🐘 Redis (for Celery task queue)

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## ⚙️ Project Structure

```
productprobe/
│
├── main.py              # Core crawler logic and URL extraction
├── celery_tasks.py      # Celery task definitions and configuration
├── tests/
│   └── main_test.py     # Unit tests for crawler functionalities
├── requirements.txt     # Project dependencies
├── README.md            # Project documentation
└── Makefile             # Automation commands for setup and execution
```

## 🔧 Usage

1. **Start Redis Server:**

```bash
redis-server
```

2. **Run Celery Worker:**

```bash
celery -A main worker --loglevel=info
```

3. **Run the Crawler:**

Add your list of domains and start the crawler:

```python
from main import EcommerceCrawler

domains = ["https://example.com", "https://testsite.com"]
crawler = EcommerceCrawler(domains)
crawler.run()
```

4. **Results:**

The extracted product URLs will be saved in `results.json`. If the file already exists, new results will be appended without overwriting existing data.

## ✅ Running Tests

Run all tests using:

```bash
python -m unittest tests/main_test.py
```

## 🛠️ Configuration

The crawler uses predefined product indicators to identify product pages. You can modify these indicators in `main.py`:

```python
PRODUCT_INDICATORS = ["/product/", "/item/", "/shop/"]
```

## 🙌 Acknowledgments 🤝

- Built with **Python**, **Celery**, and **Redis**
- Inspired by real-world e-commerce crawling challenges
- Developed with assistance from **ChatGPT**

