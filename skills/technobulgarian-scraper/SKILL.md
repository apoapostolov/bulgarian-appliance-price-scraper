---
name: technobulgarian-scraper
description: Use technobulgarian_scraper outputs to compare Bulgarian appliance offers across Technomarket, Technopolis, and Zora, then turn the results into buyer-guide recommendations.
metadata:
  short-description: Compare Bulgarian appliance offers for buying guidance
---

# Technobulgarian Scraper

Use this skill when you need to turn scraper output into purchase guidance,
shortlists, or buyer guides for Bulgarian appliances.

## Source Of Truth

Use the latest files in `output/`:

- JSON exports for raw product data
- `technobulgarian_scraper_price_comparison.md` for cross-store matches

Prefer the newest timestamped export for each store and appliance type.

## Matching Rules

1. Match products by `ean` first.
2. If `ean` is missing, fall back to a normalized brand/model fingerprint.
3. Ignore rows that are not in stock.
4. Treat price fields as integers in BGN.

## Purchase Guidance Workflow

1. Identify the appliance type and budget target.
2. Read the latest JSON exports for the relevant stores.
3. Use the comparison report to find products sold in 2 or more stores.
4. Compare:
   - price
   - energy class
   - capacity / volume
   - dimensions
   - door opening or freezer position when relevant
   - warranty and key feature specs
5. Prefer the lowest priced acceptable option only when the specs are
   functionally equivalent.
6. If a higher-priced item materially improves efficiency, capacity, or fit,
   call out the tradeoff explicitly.

## Output Style

When producing a buyer guide, include:

- Product name
- Product ID or EAN
- Best store offer
- Price per store
- Why the recommendation wins
- Any caveats about missing specs or weak matching

Keep recommendations concrete and budget-aware. If a budget cap is provided,
state whether each candidate fits under it.

## Cautions

- Do not assume a title-only match is safe when EAN is missing.
- Do not compare out-of-stock rows.
- Do not convert BGN integer prices back into ambiguous formatted strings.
- If the comparison report is empty, fall back to the latest JSON exports and
  explain that there were no confident cross-store matches.
