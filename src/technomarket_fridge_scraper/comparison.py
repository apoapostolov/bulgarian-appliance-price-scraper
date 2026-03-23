from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import argparse
import json
import re


@dataclass(frozen=True)
class ComparisonGroup:
    match_key: tuple[str, str]
    product_name: str
    product_id: str
    offers: list[dict[str, object]]


def _latest_json_exports(output_dir: Path) -> list[Path]:
    latest: dict[str, Path] = {}
    for path in output_dir.glob("bulgarian_appliance_price_scraper_*.json"):
        match = re.match(r"^(.*)_\d{8}_\d{6}$", path.stem)
        if not match:
            continue
        prefix = match.group(1)
        previous = latest.get(prefix)
        if previous is None or path.stat().st_mtime > previous.stat().st_mtime:
            latest[prefix] = path
    return sorted(latest.values())


def _load_rows(paths: list[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows.extend(item for item in payload if isinstance(item, dict))
    return rows


def _clean_text(text: object | None) -> str:
    if text is None:
        return ""
    return " ".join(str(text).split())


def _normalize_token(text: object | None) -> str:
    cleaned = _clean_text(text).upper()
    cleaned = re.sub(r"[^A-Z0-9]+", " ", cleaned)
    return " ".join(cleaned.split())


def _find_model_candidate(text: object | None) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9./_-]*", cleaned)
    for token in tokens:
        if re.search(r"\d", token) or any(char in token for char in "-_/"):
            upper = token.upper()
            if upper not in {"KG", "CM", "L", "W", "WATT", "LITERS"}:
                return upper
    return tokens[0].upper() if tokens else ""


_GENERIC_TITLE_WORDS = {
    "WASHING",
    "MACHINE",
    "MACHINES",
    "REFRIGERATOR",
    "REFRIGERATORS",
    "DISHWASHER",
    "DISHWASHERS",
    "MICROWAVE",
    "MICROWAVES",
    "OVEN",
    "OVENS",
    "HOB",
    "HOBS",
    "FREEZER",
    "FREEZERS",
    "BOTTOM",
    "TOP",
    "WITH",
    "SIDE",
    "BY",
    "AND",
    "DRYER",
    "DRYERS",
    "BUILT",
    "IN",
    "FREESTANDING",
    "COMPACT",
    "MINIBAR",
    "WINE",
    "COOLERS",
    "SHOW",
    "WINDOWS",
    "FOR",
}


def _extract_brand(row: dict[str, object]) -> str:
    brand = _clean_text(row.get("brand"))
    if brand:
        return brand
    detail_specs = row.get("detail_specs")
    if isinstance(detail_specs, dict):
        brand = _clean_text(detail_specs.get("brand"))
        if brand:
            return brand
    title = _clean_text(row.get("title") or row.get("name"))
    if not title:
        return ""
    model = _extract_model(row)
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9./_-]*", title)
    if model and model in title:
        model_index = next((index for index, token in enumerate(tokens) if token.upper() == model.upper()), None)
        if model_index is not None:
            for token in reversed(tokens[:model_index]):
                normalized = _normalize_token(token)
                if normalized and normalized not in _GENERIC_TITLE_WORDS and not re.search(r"\d", normalized):
                    return token.upper() if token.isupper() else token
    for token in reversed(tokens):
        normalized = _normalize_token(token)
        if normalized and normalized not in _GENERIC_TITLE_WORDS and not re.search(r"\d", normalized):
            return token.upper() if token.isupper() else token
    return _normalize_token(title).split(" ", 1)[0] if _normalize_token(title) else ""


def _extract_model(row: dict[str, object]) -> str:
    detail_specs = row.get("detail_specs")
    if isinstance(detail_specs, dict):
        model = _find_model_candidate(detail_specs.get("model"))
        if model:
            return model
    for key in ("sku", "name", "title"):
        model = _find_model_candidate(row.get(key))
        if model:
            return model
    return ""


def _comparison_key(row: dict[str, object]) -> tuple[str, str]:
    ean = _clean_text(row.get("ean"))
    if ean:
        return ("ean", ean)
    brand = _extract_brand(row)
    model = _extract_model(row)
    if brand and model:
        return ("brand_model", f"{_normalize_token(brand)}::{_normalize_token(model)}")
    title = _clean_text(row.get("title") or row.get("name") or row.get("product_code"))
    return ("title", _normalize_token(title))


def _display_name(row: dict[str, object]) -> str:
    brand = _extract_brand(row)
    model = _extract_model(row)
    if brand and model:
        return f"{brand} {model}"
    title = _clean_text(row.get("title") or row.get("name"))
    if title:
        return title
    return _clean_text(row.get("product_code"))


def _product_id(row: dict[str, object], match_key: tuple[str, str]) -> str:
    kind, value = match_key
    if kind == "ean":
        return f"EAN {value}"
    brand = _extract_brand(row)
    model = _extract_model(row)
    if brand and model:
        return f"{brand} {model}"
    if value:
        return value
    return _clean_text(row.get("product_code"))


def group_compared_products(rows: list[dict[str, object]]) -> list[ComparisonGroup]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if not row.get("in_stock", True):
            continue
        grouped[_comparison_key(row)].append(row)

    groups: list[ComparisonGroup] = []
    for match_key, items in grouped.items():
        stores = {str(item.get("store", "")) for item in items if item.get("store")}
        priced_items = [item for item in items if isinstance(item.get("price_bgn"), int)]
        if len(stores) < 2 or len(priced_items) < 2:
            continue
        best = min(priced_items, key=lambda item: int(item["price_bgn"]))
        best_store = str(best.get("store", ""))
        offers = sorted(
            (
                {
                    "store": str(item.get("store", "")),
                    "price_bgn": int(item["price_bgn"]),
                    "url": str(item.get("url", "")),
                }
                for item in priced_items
            ),
            key=lambda item: (item["price_bgn"], item["store"]),
        )
        groups.append(
            ComparisonGroup(
                match_key=match_key,
                product_name=_display_name(best),
                product_id=_product_id(best, match_key),
                offers=offers,
            )
        )

    groups.sort(key=lambda group: (group.product_name.lower(), group.product_id.lower()))
    return groups


def _format_bgn(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " BGN"


def render_markdown(groups: list[ComparisonGroup], source_files: list[Path]) -> str:
    lines = [
        "<!-- markdownlint-disable MD013 -->",
        "# Cross-store price comparison",
        "",
        "This report matches products using EAN first, then a normalized brand/model fingerprint when EAN is missing.",
        "",
    ]
    if source_files:
        lines.append("Sources:")
        for path in source_files:
            lines.append(f"- `{path.name}`")
        lines.append("")

    if not groups:
        lines.extend([
            "No products were found in 2 or more stores with comparable prices.",
            "",
        ])
        return "\n".join(lines)

    lines.extend([
        "| Product name | ID | Best store offer | Price per store |",
        "| --- | --- | --- | --- |",
    ])
    for group in groups:
        best_offer = min(group.offers, key=lambda item: (item["price_bgn"], item["store"]))
        prices = "; ".join(
            f"{offer['store']}: {_format_bgn(offer['price_bgn'])}"
            for offer in group.offers
        )
        lines.append(
            f"| {group.product_name} | {group.product_id} | "
            f"{best_offer['store']} {_format_bgn(best_offer['price_bgn'])} | "
            f"{prices} |"
        )
    lines.append("")
    lines.append("<!-- markdownlint-enable MD013 -->")
    return "\n".join(lines)


def build_report(output_dir: Path) -> tuple[str, list[Path], list[ComparisonGroup]]:
    source_files = _latest_json_exports(output_dir)
    rows = _load_rows(source_files)
    groups = group_compared_products(rows)
    return render_markdown(groups, source_files), source_files, groups


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a cross-store price comparison report.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory containing scraper JSON outputs")
    parser.add_argument("--output-file", type=Path, default=None, help="Path to the markdown report to write")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, _, _ = build_report(args.output_dir)
    output_file = args.output_file or args.output_dir / f"bulgarian_appliance_price_scraper_price_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_file.write_text(report, encoding="utf-8")
    print(output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
