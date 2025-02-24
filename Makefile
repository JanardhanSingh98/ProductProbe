# Makefile for Ecommerce Crawler Project

# Variables
PYTHON=python3
CELERY=celery
REDIS=redis-server

# Default target
default: help

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Start Redis server
redis:
	$(REDIS) &

# Run Celery worker
celery:
	$(CELERY) -A main worker --loglevel=info

# Run the crawler script
crawl:
	$(PYTHON) main.py

# Run tests (if any are added later)
test:
	$(PYTHON) -m unittest discover tests

# Clean cache and output files
clean:
	rm -f *.pyc
	rm -rf __pycache__/
	rm -f discovered_product_urls.json

# Help command
help:
	@echo "Commands:"
	@echo "  install     Install project dependencies"
	@echo "  redis       Start Redis server"
	@echo "  celery      Start Celery worker"
	@echo "  crawl       Run the crawler"
	@echo "  test        Run tests"
	@echo "  clean       Clean temporary files"
