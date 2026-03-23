# Changelog

## 0.1.0 - 2026-03-23

First public release of `bulgarian-appliance-price-scraper`.

### Highlights

- Generic scraper for Bulgarian appliance catalogs across Technomarket,
  Technopolis, and Zora.
- Store-aware and appliance-aware configuration for refrigerators, washing
  machines, dishwashers, ovens, hobs, and microwaves.
- Live category discovery, product-page enrichment, and cached detail-page
  metadata.
- Normalized JSON, CSV, and Markdown exports with English field names,
  normalized prices, and structured appliance specs.
- Cross-store Markdown comparison report that matches products by EAN first,
  then normalized brand/model when needed.
- Thin MCP server wrapper for agent workflows and buyer-guide automation.
- Agent skill guidance for using scraper exports in purchase research.
