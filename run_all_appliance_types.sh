#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIG_PATH="${CONFIG_PATH:-$ROOT_DIR/config.toml}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/output}"

mapfile -t STORE_APPLIANCE_TYPES < <(
  "$PYTHON_BIN" - <<'PY' "$CONFIG_PATH"
import sys
from pathlib import Path
import tomllib

config_path = Path(sys.argv[1])
data = tomllib.loads(config_path.read_text(encoding="utf-8"))
stores = data.get("stores", {})
for store_name, store_data in stores.items():
    profiles = store_data.get("appliance_types", {})
    for appliance_type in profiles.keys():
        print(f"{store_name}\t{appliance_type}")
PY
)

if [[ "${#STORE_APPLIANCE_TYPES[@]}" -eq 0 ]]; then
  echo "No store/appliance profiles found in $CONFIG_PATH" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

for entry in "${STORE_APPLIANCE_TYPES[@]}"; do
  store="${entry%%$'\t'*}"
  appliance_type="${entry#*$'\t'}"
  echo "Running ${store}/${appliance_type}"
  "$PYTHON_BIN" -m technobulgarian_scraper.scraper \
    --config "$CONFIG_PATH" \
    --output-dir "$OUTPUT_DIR" \
    --store "$store" \
    --appliance-type "$appliance_type"
done

echo "Building cross-store comparison report"
"$PYTHON_BIN" -m technobulgarian_scraper.compare \
  --output-dir "$OUTPUT_DIR" \
  --output-file "$OUTPUT_DIR/technobulgarian_scraper_price_comparison.md"
