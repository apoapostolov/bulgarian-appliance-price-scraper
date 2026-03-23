from __future__ import annotations

from collections import OrderedDict
from csv import DictWriter
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import argparse
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .cache import ApplianceMetadataCache
from .config import Category, ScraperConfig, load_config
from .stores import STORE_BACKENDS
from .render import render_dom, render_dom_chromium


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config.toml"


def _format_category_name(prefix: str | None, name: str) -> str:
    cleaned = " ".join(name.split())
    if not prefix:
        return cleaned
    lowered = cleaned.lower()
    if lowered.startswith("всички "):
        return prefix
    return f"{prefix} {lowered}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Technomarket, Technopolis, and Zora appliances in stock.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to config.toml")
    parser.add_argument("--output-dir", type=Path, default=None, help="Override output directory")
    parser.add_argument("--store", type=str, default=None, help="Override the store profile")
    parser.add_argument("--appliance-type", type=str, default=None, help="Override the appliance profile")
    return parser.parse_args()


def discover_pages(config: ScraperConfig, category: Category) -> int:
    url = urljoin(config.base_url, category.path)
    renderer = render_dom_chromium if config.store == "technopolis" else render_dom
    html = renderer(
        url,
        config.render_timeout_ms,
        config.chromium_binaries,
        config.user_agent,
    )
    soup = BeautifulSoup(html, "html.parser")
    backend = STORE_BACKENDS[config.store]
    return backend.extract_total_pages(soup)


def discover_appliance_categories(config: ScraperConfig) -> list[Category]:
    discovered: list[Category]
    if config.profile.categories:
        discovered = [
            Category(
                path=category.path,
                name=_format_category_name(config.profile.category_name_prefix, category.name),
            )
            for category in config.profile.categories
        ]
    elif config.profile.category_texts:
        url = urljoin(config.base_url, config.profile.hub_path)
        renderer = render_dom_chromium if config.store == "technopolis" else render_dom
        html = renderer(
            url,
            config.render_timeout_ms,
            config.chromium_binaries,
            config.user_agent,
        )
        backend = STORE_BACKENDS[config.store]
        discovered = backend.discover_categories_from_html(html, set(config.profile.category_texts))
    else:
        discovered = [
            Category(
                path=category.path,
                name=_format_category_name(config.profile.category_name_prefix, category.name),
            )
            for category in config.categories
        ]

    categories = list(discovered)
    if config.profile.hub_path and config.profile.category_root_name:
        root_category = Category(path=config.profile.hub_path, name=config.profile.category_root_name)
        if not any(category.path == root_category.path for category in categories):
            categories.insert(0, root_category)
    return [
        Category(
            path=category.path,
            name=_format_category_name(config.profile.category_name_prefix, category.name),
        )
        for category in categories
    ]


def _build_page_url(config: ScraperConfig, category: Category, page: int) -> str:
    if page == 1:
        return urljoin(config.base_url, category.path)
    query_key = "currentPage" if config.store == "technopolis" else "page"
    query_value = page - 1 if query_key == "currentPage" else page
    return urljoin(config.base_url, f"{category.path}?{query_key}={query_value}")


def scrape_category(config: ScraperConfig, category: Category) -> list[dict]:
    rows: list[dict] = []
    total_pages = discover_pages(config, category)
    backend = STORE_BACKENDS[config.store]
    renderer = render_dom_chromium if config.store == "technopolis" else render_dom
    for page in range(1, total_pages + 1):
        page_url = _build_page_url(config, category, page)
        html = renderer(
            page_url,
            config.render_timeout_ms,
            config.chromium_binaries,
            config.user_agent,
        )
        products = backend.extract_products(
            html=html,
            base_url=config.base_url,
            category_name=category.name,
            category_path=category.path,
            page=page,
            in_stock_only=config.profile.in_stock_only,
            store=config.store,
        )
        rows.extend(product.to_dict() for product in products)
    return rows


def enrich_with_product_details(config: ScraperConfig, rows: list[dict]) -> list[dict]:
    if not config.profile.fetch_product_details:
        return rows

    cache = ApplianceMetadataCache.load(config.profile.metadata_cache_path)
    details_by_url: dict[str, dict[str, object]] = {}
    max_workers = min(4, len(rows)) or 1
    backend = STORE_BACKENDS[config.store]
    renderer = render_dom_chromium if config.store == "technopolis" else render_dom

    def fetch(url: str) -> dict[str, object]:
        html = renderer(
            url,
            config.render_timeout_ms,
            config.chromium_binaries,
            config.user_agent,
        )
        return backend.extract_product_details(html)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {}
        for row in rows:
            cached = cache.lookup(row["product_code"], row["url"])
            if cached is not None:
                details_by_url[row["url"]] = cached
                continue
            future = executor.submit(fetch, row["url"])
            future_to_url[future] = row
        for future in as_completed(future_to_url):
            row = future_to_url[future]
            url = row["url"]
            try:
                details = future.result()
                details_by_url[url] = details
                cache.store(row["product_code"], url, details)
            except Exception:
                details_by_url[url] = {
                    "detail_features": [],
                    "detail_specs": {},
                    "ean": None,
                }
    cache.save()

    enriched_rows: list[dict] = []
    for row in rows:
        enriched = dict(row)
        enriched.update(details_by_url.get(row["url"], {
            "detail_features": [],
            "detail_specs": {},
            "ean": None,
        }))
        enriched_rows.append(enriched)
    return enriched_rows


def dedupe_products(rows: list[dict]) -> list[dict]:
    unique: OrderedDict[tuple[str, str], dict] = OrderedDict()
    for row in rows:
        key = (row["store"], row["product_code"], row["url"])
        if key not in unique:
            unique[key] = row
    return list(unique.values())


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "store",
        "category_name",
        "category_path",
        "page",
        "product_code",
        "sku",
        "brand",
        "name",
        "title",
        "url",
        "in_stock",
        "price_bgn",
        "price_eur",
        "old_price_bgn",
        "old_price_eur",
        "energy_class",
        "specs",
        "detail_features",
        "detail_specs",
        "ean",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            csv_row["specs"] = json.dumps(row["specs"], ensure_ascii=False)
            csv_row["detail_features"] = json.dumps(row["detail_features"], ensure_ascii=False)
            csv_row["detail_specs"] = json.dumps(row["detail_specs"], ensure_ascii=False)
            writer.writerow(csv_row)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _format_price(value: int | float | None) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    left, right = f"{value:.2f}".split(".", 1)
    return f"{int(left):,}".replace(",", " ") + "." + right


def write_markdown(path: Path, rows: list[dict], config: ScraperConfig) -> None:
    lines = [
        f"# {config.store} {config.appliance_type.replace('_', ' ')} scrape",
        "",
        f"- Store: `{config.store}`",
        f"- Appliance type: `{config.appliance_type}`",
        f"- Rows: `{len(rows)}`",
        "",
        "| Store | Category | Product | Product code | Price BGN | Price EUR | Energy class | URL |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {store} | {category} | {product} | {code} | {price_bgn} | {price_eur} | {energy_class} | {url} |".format(
                store=row.get("store", ""),
                category=row.get("category_name", ""),
                product=row.get("title") or row.get("name") or "",
                code=row.get("product_code", ""),
                price_bgn=_format_price(row.get("price_bgn")),
                price_eur=_format_price(row.get("price_eur")),
                energy_class=row.get("energy_class") or "",
                url=row.get("url", ""),
            )
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    config = load_config(args.config, store_override=args.store, appliance_type_override=args.appliance_type)
    output_dir = args.output_dir or config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for category in discover_appliance_categories(config):
        all_rows.extend(scrape_category(config, category))
    rows = dedupe_products(all_rows)
    rows = enrich_with_product_details(config, rows)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"{config.profile.output_prefix}_{stamp}.csv"
    json_path = output_dir / f"{config.profile.output_prefix}_{stamp}.json"
    md_path = output_dir / f"{config.profile.output_prefix}_{stamp}.md"
    write_csv(csv_path, rows)
    write_json(json_path, rows)
    write_markdown(md_path, rows, config)

    print(f"Wrote {len(rows)} in-stock products")
    print(csv_path)
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
