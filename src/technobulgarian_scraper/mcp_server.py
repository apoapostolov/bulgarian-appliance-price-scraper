from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from technomarket_fridge_scraper.comparison import build_report


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = DEFAULT_REPO_ROOT / "output"
DEFAULT_CONFIG = DEFAULT_REPO_ROOT / "config.toml"
EXPORT_PATTERN = re.compile(
    r"^bulgarian_appliance_price_scraper_(?P<store>[a-z]+)_(?P<appliance>[a-z_]+)_(?P<stamp>\d{8}_\d{6})$"
)
APPLIANCE_ALIASES = {
    "refrigerators": "refrigerator",
    "washing_machines": "washing_machine",
    "dishwashers": "dishwasher",
    "ovens": "oven",
    "hobs": "hob",
    "microwaves": "microwave",
}


def _import_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised when dependency is missing
        raise RuntimeError(
            "MCP support requires the 'mcp' package. Install the project dependencies first."
        ) from exc
    return FastMCP


def _clean_text(text: object | None) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split())


def _normalize_text(text: object | None) -> str:
    cleaned = _clean_text(text).upper()
    cleaned = re.sub(r"[^A-Z0-9]+", " ", cleaned)
    return " ".join(cleaned.split())


def _latest_json_exports(output_dir: Path) -> list[Path]:
    latest: dict[str, Path] = {}
    for path in output_dir.glob("bulgarian_appliance_price_scraper_*.json"):
        match = EXPORT_PATTERN.match(path.stem)
        if not match:
            continue
        prefix = f"bulgarian_appliance_price_scraper_{match.group('store')}_{match.group('appliance')}"
        previous = latest.get(prefix)
        if previous is None or path.stat().st_mtime > previous.stat().st_mtime:
            latest[prefix] = path
    return sorted(latest.values())


def _load_json_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _parse_export_metadata(path: Path) -> dict[str, str]:
    match = EXPORT_PATTERN.match(path.stem)
    if not match:
        return {
            "file": path.name,
            "store": "",
            "appliance_type": "",
            "timestamp": "",
        }
    appliance = match.group("appliance")
    return {
        "file": path.name,
        "store": match.group("store"),
        "appliance_type": APPLIANCE_ALIASES.get(appliance, appliance),
        "timestamp": match.group("stamp"),
    }


def _row_haystack(row: dict[str, object]) -> str:
    pieces: list[object] = [
        row.get("store"),
        row.get("category_name"),
        row.get("product_code"),
        row.get("sku"),
        row.get("brand"),
        row.get("name"),
        row.get("title"),
        row.get("ean"),
        row.get("url"),
    ]
    detail_specs = row.get("detail_specs")
    if isinstance(detail_specs, dict):
        pieces.extend(detail_specs.values())
    specs = row.get("specs")
    if isinstance(specs, dict):
        pieces.extend(specs.values())
    return _normalize_text(" ".join(_clean_text(piece) for piece in pieces if piece is not None))


def _match_score(row: dict[str, object], query: str) -> tuple[int, str]:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return 0, ""

    exact_fields = [
        ("ean", row.get("ean")),
        ("sku", row.get("sku")),
        ("product_code", row.get("product_code")),
        ("title", row.get("title")),
        ("name", row.get("name")),
    ]
    for field_name, value in exact_fields:
        if _normalize_text(value) == normalized_query:
            return 100 if field_name == "ean" else 90 if field_name in {"sku", "product_code"} else 80, f"exact_{field_name}"

    haystack = _row_haystack(row)
    if normalized_query in haystack:
        return 50, "substring"

    query_tokens = set(normalized_query.split())
    haystack_tokens = set(haystack.split())
    if query_tokens and query_tokens.issubset(haystack_tokens):
        return 40, "token_match"

    return 0, ""


def _latest_export_payloads(
    output_dir: Path,
    store: str | None = None,
    appliance_type: str | None = None,
) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for path in _latest_json_exports(output_dir):
        metadata = _parse_export_metadata(path)
        if store and metadata["store"] != store:
            continue
        if appliance_type and metadata["appliance_type"] != appliance_type:
            continue
        rows = _load_json_rows(path)
        payloads.append(
            {
                **metadata,
                "path": str(path),
                "rows": rows,
                "row_count": len(rows),
            }
        )
    return payloads


def _latest_export_for_store_type(
    output_dir: Path,
    store: str,
    appliance_type: str,
) -> dict[str, object] | None:
    payloads = _latest_export_payloads(output_dir, store=store, appliance_type=appliance_type)
    if not payloads:
        return None
    return payloads[-1]


def build_server():
    FastMCP = _import_fastmcp()
    server = FastMCP("bulgarian_appliance_price_scraper")

    @server.tool()
    def list_latest_exports(output_dir: str = "output") -> dict[str, object]:
        """List the latest JSON export for each store/appliance family."""
        output_path = Path(output_dir)
        exports = [
            {
                key: value
                for key, value in payload.items()
                if key != "rows"
            }
            for payload in _latest_export_payloads(output_path)
        ]
        return {
            "output_dir": str(output_path),
            "exports": exports,
        }

    @server.tool()
    def search_products(
        query: str,
        output_dir: str = "output",
        store: str | None = None,
        appliance_type: str | None = None,
        limit: int = 20,
    ) -> dict[str, object]:
        """Search the latest exports for products matching a SKU, EAN, or model query."""
        output_path = Path(output_dir)
        matches: list[dict[str, object]] = []
        for payload in _latest_export_payloads(output_path, store=store, appliance_type=appliance_type):
            for row in payload["rows"]:
                if not isinstance(row, dict):
                    continue
                score, reason = _match_score(row, query)
                if not score:
                    continue
                matches.append(
                    {
                        "store": row.get("store"),
                        "appliance_type": payload["appliance_type"],
                        "source_file": payload["file"],
                        "match_reason": reason,
                        "score": score,
                        "product_code": row.get("product_code"),
                        "sku": row.get("sku"),
                        "brand": row.get("brand"),
                        "name": row.get("name"),
                        "title": row.get("title"),
                        "ean": row.get("ean"),
                        "price_bgn": row.get("price_bgn"),
                        "url": row.get("url"),
                    }
                )

        matches.sort(
            key=lambda item: (
                -int(item["score"]),
                int(item["price_bgn"]) if isinstance(item.get("price_bgn"), int) else 10**12,
                _clean_text(item.get("store")),
                _clean_text(item.get("name")),
            )
        )
        return {
            "query": query,
            "output_dir": str(output_path),
            "limit": limit,
            "matches": matches[:limit],
        }

    @server.tool()
    def build_comparison_report(output_dir: str = "output") -> dict[str, object]:
        """Build the latest cross-store Markdown price comparison report."""
        output_path = Path(output_dir)
        markdown, source_files, groups = build_report(output_path)
        return {
            "output_dir": str(output_path),
            "source_files": [str(path) for path in source_files],
            "group_count": len(groups),
            "markdown": markdown,
        }

    @server.tool()
    def run_scrape(
        store: str,
        appliance_type: str,
        output_dir: str | None = None,
        config_path: str | None = None,
    ) -> dict[str, object]:
        """Run a fresh scrape for one store/appliance family and return the latest export."""
        command = [
            sys.executable,
            "-m",
            "bulgarian_appliance_price_scraper.scraper",
            "--store",
            store,
            "--appliance-type",
            appliance_type,
        ]
        if output_dir:
            command.extend(["--output-dir", output_dir])
        if config_path:
            command.extend(["--config", config_path])

        completed = subprocess.run(
            command,
            cwd=DEFAULT_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Scrape failed with exit code "
                f"{completed.returncode}:\n{completed.stderr.strip() or completed.stdout.strip()}"
            )

        resolved_output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        latest_export = _latest_export_for_store_type(resolved_output_dir, store, appliance_type)
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "latest_export": latest_export,
        }

    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bulgarian_appliance_price_scraper MCP server.")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],
        help="MCP transport to use.",
    )
    return parser.parse_args()


def main() -> int:
    _ = parse_args()
    server = build_server()
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
