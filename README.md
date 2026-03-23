# technobulgarian_scraper

Scrapes appliance families on [Technomarket.bg](https://www.technomarket.bg/),
[Technopolis.bg](https://www.technopolis.bg/), and [Zora.bg](https://zora.bg/)
and exports the currently in-stock products to CSV and JSON.

## What it does

- Fetches HTML with `requests` and falls back to headless Chromium if needed.
- Parses the product cards from the live DOM.
- Supports the major Bulgarian appliance stores from the same command line.
- Follows each product page to collect richer specs and the EAN when available.
- Collects the product name, SKU, URL, normalized prices, energy class,
  listing specs, and product-page specs.
- Filters to items that have an active `Add to cart` button.
- Writes timestamped output files under `output/`.
- Generates a cross-store comparison markdown report when the full launcher runs.

## Appliance Types

Select the store with `--store` or the `scraper.store` config value, then
select the appliance type with `--appliance-type` or the
`scraper.appliance_type` config value. Each store/type combination has its own
config block in `config.toml`.

Configured types in this repo:

- `refrigerator`
- `washing_machine`
- `dishwasher`
- `oven`
- `hob`
- `microwave`

Each type defines its own hub path or concrete category pages, cache file, and
output prefix.

## Requirements

- Python 3.11+
- Chromium installed locally and available as `chromium` or `chromium-browser`

## Setup

```bash
cd technobulgarian-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run

```bash
python -m technobulgarian_scraper.scraper --store technomarket \
  --appliance-type refrigerator
python -m technobulgarian_scraper.scraper --store zora \
  --appliance-type microwave
```

To run every configured store and appliance family in sequence:

```bash
./run_all_appliance_types.sh
```

To generate the cross-store comparison report from existing JSON exports:

```bash
python -m technobulgarian_scraper.compare --output-dir output
```

This writes files like:

- `output/technobulgarian_scraper_technomarket_refrigerators_YYYYMMDD_HHMMSS.csv`
- `output/technobulgarian_scraper_technomarket_refrigerators_YYYYMMDD_HHMMSS.json`
- `output/technobulgarian_scraper_technopolis_refrigerators_YYYYMMDD_HHMMSS.csv`
- `output/technobulgarian_scraper_technopolis_refrigerators_YYYYMMDD_HHMMSS.json`
- `output/technobulgarian_scraper_zora_refrigerators_YYYYMMDD_HHMMSS.csv`
- `output/technobulgarian_scraper_zora_refrigerators_YYYYMMDD_HHMMSS.json`
- `output/technobulgarian_scraper_price_comparison.md`

## Cross-Store Comparison

The launcher writes a Markdown comparison report after a full scrape run.

It matches products across stores with this priority:

1. `EAN`
2. Normalized brand/model fingerprint when `EAN` is missing

The report table includes:

- Product name
- ID
- Best store offer
- Price per store

## AI Agents

Agents that support skills can use this repo as a purchase-research plugin.

Skill path:

- `skills/technobulgarian-scraper/SKILL.md`

To install it in an agent workspace, copy or symlink the `skills/`
subdirectory into the agent's skill directory, or point the agent at this
repository and load the skill directly from that path.

The skill tells agents how to:

- Read the latest JSON exports and comparison report
- Match products across stores by EAN first, then brand/model
- Compare price, energy class, capacity, dimensions, and other specs
- Turn the scraper output into buyer-guide recommendations
- Keep budget thresholds explicit and cite the store and product IDs used

## Notes

- The scraper treats a product as in stock when the card contains an active
  `data-action="addCart"` button.
- Technopolis products are parsed from the page state JSON and the rendered
  price card, which is more stable than scraping localized card text.
- Zora products are parsed from server-rendered product cards and the product
  page metadata blob.
- Technomarket listings and product pages are usually available in raw HTML,
  so `requests` is the fast path. Chromium remains as a fallback.
- Product details are fetched from each product page and cached per appliance
  type and store so the CSV/JSON includes richer metadata without duplicate
  page loads.
- Price fields are stored as integers with punctuation stripped out of the
  scraped price string.
