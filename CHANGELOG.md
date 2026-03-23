# Changelog

## 2026-03-23

- Renamed the project to `technobulgarian_scraper`.
- Added a generic `technobulgarian_scraper` entry point and kept compatibility
  shims for the earlier appliance package names.
- Reworked the config into per-store, per-appliance profiles under
  `stores.*.appliance_types.*`.
- Added the `--store` and `--appliance-type` flags so the same scraper can
  target refrigerator, washing machine, dishwasher, oven, hob, and microwave
  catalogs from Technomarket, Technopolis, and Zora.
- Added `run_all_appliance_types.sh` to run every configured store and
  appliance profile in sequence.
- Renamed generated output prefixes to the `technobulgarian_scraper_*` family.
- Added Technopolis and Zora backends alongside the Technomarket backend.
- Added a cross-store Markdown comparison report that groups the same product
  across stores and highlights the lowest BGN offer.
- Added an MCP server wrapper for agent workflows and documented how to run it.
- Removed MCP client examples that were not useful.
- Removed stale fridge-specific cache and output snapshots from the repository.
