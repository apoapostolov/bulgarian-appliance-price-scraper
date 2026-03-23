PYTHON ?= python3

.PHONY: scrape scrape-all compare mcp test

scrape:
	PYTHONPATH=src $(PYTHON) -m technobulgarian_scraper.scraper

scrape-all:
	PYTHONPATH=src ./run_all_appliance_types.sh

compare:
	PYTHONPATH=src $(PYTHON) -m technobulgarian_scraper.compare --output-dir output --output-file output/technobulgarian_scraper_price_comparison.md

mcp:
	PYTHONPATH=src $(PYTHON) -m technobulgarian_scraper.mcp_server

test:
	PYTHONPATH=src TMPDIR=/tmp pytest
