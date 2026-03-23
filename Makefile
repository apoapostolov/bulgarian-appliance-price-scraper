PYTHON ?= python3

.PHONY: scrape scrape-all compare test

scrape:
	PYTHONPATH=src $(PYTHON) -m technobulgarian_scraper.scraper

scrape-all:
	PYTHONPATH=src ./run_all_appliance_types.sh

compare:
	PYTHONPATH=src $(PYTHON) -m technobulgarian_scraper.compare --output-dir output --output-file output/technobulgarian_scraper_price_comparison.md

test:
	PYTHONPATH=src TMPDIR=/tmp pytest
