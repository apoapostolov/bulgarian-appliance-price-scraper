from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class Category:
    path: str
    name: str


@dataclass(frozen=True)
class ApplianceProfile:
    appliance_type: str
    hub_path: str
    category_root_name: str | None
    category_name_prefix: str | None
    category_texts: list[str]
    categories: list[Category]
    output_prefix: str
    metadata_cache_path: Path
    in_stock_only: bool
    fetch_product_details: bool


@dataclass(frozen=True)
class ScraperConfig:
    store: str
    base_url: str
    user_agent: str
    output_dir: Path
    render_timeout_ms: int
    chromium_binaries: list[str]
    appliance_type: str
    profile: ApplianceProfile
    categories: list[Category]


def _load_categories(items: list[dict] | None) -> list[Category]:
    categories: list[Category] = []
    for item in items or []:
        categories.append(Category(path=item["path"], name=item["name"]))
    return categories


def _load_profile(appliance_type: str, data: dict, store_name: str) -> ApplianceProfile:
    if "stores" in data:
        store_block = data["stores"].get(store_name)
        if store_block is None:
            raise KeyError(f"Unknown store: {store_name}")
        profiles = store_block.get("appliance_types", {})
        if appliance_type not in profiles:
            raise KeyError(f"Unknown appliance type: {appliance_type}")
        profile_data = profiles[appliance_type]
    else:
        profiles = data.get("appliance_types", {})
        if appliance_type not in profiles:
            raise KeyError(f"Unknown appliance type: {appliance_type}")
        profile_data = profiles[appliance_type]

    return ApplianceProfile(
        appliance_type=appliance_type,
        hub_path=profile_data.get("hub_path", ""),
        category_root_name=profile_data.get("category_root_name"),
        category_name_prefix=profile_data.get("category_name_prefix"),
        category_texts=list(profile_data.get("category_texts", [])),
        categories=_load_categories(profile_data.get("categories")),
        output_prefix=profile_data.get("output_prefix", f"technomarket_{appliance_type}s"),
        metadata_cache_path=Path(profile_data.get("metadata_cache_path", f"cache/{appliance_type}_metadata.json")),
        in_stock_only=bool(profile_data.get("in_stock_only", True)),
        fetch_product_details=bool(profile_data.get("fetch_product_details", True)),
    )


def load_config(
    config_path: Path,
    store_override: str | None = None,
    appliance_type_override: str | None = None,
) -> ScraperConfig:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    general = data.get("general", {})
    scraper = data.get("scraper", {})
    store = store_override or scraper.get("store", "technomarket")
    appliance_type = appliance_type_override or scraper.get("appliance_type", "refrigerator")
    profile = _load_profile(appliance_type, data, store)

    if "stores" in data:
        store_block = data["stores"][store]
        base_url = store_block.get("base_url", general.get("base_url", "https://www.technomarket.bg"))
        user_agent = store_block.get("user_agent", general.get("user_agent", "Mozilla/5.0"))
        output_dir = Path(store_block.get("output_dir", "output"))
        render_timeout_ms = int(store_block.get("render_timeout_ms", 15000))
        chromium_binaries = list(store_block.get("chromium_binaries", ["chromium"]))
        categories = profile.categories
    else:
        base_url = general.get("base_url", "https://www.technomarket.bg")
        user_agent = general.get("user_agent", "Mozilla/5.0")
        output_dir = Path(scraper.get("output_dir", "output"))
        render_timeout_ms = int(scraper.get("render_timeout_ms", 15000))
        chromium_binaries = list(scraper.get("chromium_binaries", ["chromium"]))
        categories = [
            Category(path=item["path"], name=item["name"])
            for item in scraper.get("categories", [])
        ]

    return ScraperConfig(
        store=store,
        base_url=base_url,
        user_agent=user_agent,
        output_dir=output_dir,
        render_timeout_ms=render_timeout_ms,
        chromium_binaries=chromium_binaries,
        appliance_type=appliance_type,
        profile=profile,
        categories=categories,
    )
