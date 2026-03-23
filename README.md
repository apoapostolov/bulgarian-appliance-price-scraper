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
- Exposes a lightweight MCP server wrapper for agent consumers.

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

## MCP Server

The repository also includes a thin [Model Context Protocol](https://modelcontextprotocol.io/)
server wrapper for agents that prefer structured tool calls over parsing files
directly.

Install the project dependencies first:

```bash
pip install -e .
```

Run the server:

```bash
technobulgarian-scraper-mcp
```

Or launch it with Python:

```bash
python -m technobulgarian_scraper.mcp_server
```

Example client configuration:

```json
{
  "mcpServers": {
    "technobulgarian-scraper": {
      "command": "technobulgarian-scraper-mcp",
      "cwd": "/path/to/technobulgarian-scraper"
    }
  }
}
```

Available tools:

- `list_latest_exports` - list the latest JSON export for each store and
  appliance family
- `search_products` - search the latest exports by SKU, EAN, model, or title
- `build_comparison_report` - render the cross-store markdown comparison
  report
- `run_scrape` - trigger a fresh scrape for one store/appliance family

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
- BGN prices are stored as integer minor units with punctuation stripped out
  of the scraped price string.
- EUR prices preserve cents when present, so `1022.07` stays `1022.07` rather
  than `102207`.
