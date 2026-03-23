from __future__ import annotations

from urllib.parse import urljoin
import json
import re

from bs4 import BeautifulSoup

from ..config import Category
from ..models import ApplianceProduct
from ..normalization import canonicalize_label, canonicalize_spec_value, parse_price_to_number


def _load_state(html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="ng-state", attrs={"type": "application/json"})
    if not script or not script.string:
        return {}
    try:
        return json.loads(script.string)
    except json.JSONDecodeError:
        return {}


def _clean_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned or None


def _first_price_pair(card_text: str | None) -> tuple[int | float | None, int | float | None]:
    if not card_text:
        return None, None
    match = re.search(
        r"Price:\s*([\d.,]+)\s*€\s*/\s*([\d.,]+)\s*лв\.",
        card_text,
    )
    if not match:
        return None, None
    return parse_price_to_number(match.group(2)), parse_price_to_number(match.group(1))


def extract_total_pages(soup: BeautifulSoup) -> int:
    script = soup.find("script", id="ng-state", attrs={"type": "application/json"})
    if not script or not script.string:
        return 1
    try:
        state = json.loads(script.string)
    except json.JSONDecodeError:
        return 1
    results = (
        state.get("cx-state", {})
        .get("product", {})
        .get("search", {})
        .get("results", {})
    )
    pagination = results.get("pagination", {})
    total_pages = pagination.get("totalPages")
    if isinstance(total_pages, int) and total_pages > 0:
        return total_pages
    return 1


def discover_categories(config) -> list[Category]:
    if config.profile.categories:
        return config.profile.categories
    return config.categories


def discover_categories_from_html(
    html: str,
    category_texts: set[str] | None = None,
    path_prefix: str | None = None,
) -> list[Category]:
    soup = BeautifulSoup(html, "html.parser")
    categories: list[Category] = []
    seen: set[str] = set()
    nav_glyphs = {"«", "‹", "›", "»"}
    for anchor in soup.select('a[href*="/c/"]'):
        text = _clean_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href", "")
        if not text or href in seen:
            continue
        if text in nav_glyphs or text.isdigit():
            continue
        if not href.startswith("/en/") or "/c/" not in href:
            continue
        if path_prefix is not None:
            if not href.startswith(path_prefix):
                continue
            if "/filtar/" in href or "?" in href:
                continue
        elif category_texts is not None and text not in category_texts:
            continue
        seen.add(href)
        categories.append(Category(path=href, name=text))
    return categories


def extract_products(
    html: str,
    base_url: str,
    category_name: str,
    category_path: str,
    page: int,
    in_stock_only: bool = True,
    store: str = "technopolis",
) -> list[ApplianceProduct]:
    state = _load_state(html)
    results = (
        state.get("cx-state", {})
        .get("product", {})
        .get("search", {})
        .get("results", {})
    )
    products = results.get("products", [])
    soup = BeautifulSoup(html, "html.parser")
    rows: list[ApplianceProduct] = []

    for product in products:
        if not isinstance(product, dict):
            continue
        product_code = str(product.get("code", "")).strip()
        if not product_code:
            continue

        purchasable = bool(product.get("purchasable"))
        show_buy = bool(product.get("showBuyButton"))
        sold_out = bool(product.get("soldOut"))
        in_stock = purchasable and show_buy and not sold_out
        if in_stock_only and not in_stock:
            continue

        href = str(product.get("url", "")).strip()
        url = urljoin(base_url, href)
        card = soup.select_one(f'te-product-box[data-product-id="{product_code}"]')
        card_text = card.get_text(" ", strip=True) if card else None
        price_bgn, price_eur = _first_price_pair(card_text)

        title = _clean_text(str(product.get("nameHtml") or product.get("name") or "")) or ""
        brand = _clean_text(str(product.get("brand") or "")) or ""
        name = title
        if not brand and title:
            brand_match = re.match(r"([A-Z0-9&+.\- ]+?)\s+[A-Z0-9]", title)
            if brand_match:
                brand = brand_match.group(1).strip()
        energy_class = product.get("energyClass")
        if isinstance(energy_class, str):
            energy_class = energy_class.strip() or None

        rows.append(
            ApplianceProduct(
                store=store,
                category_name=category_name,
                category_path=category_path,
                page=page,
                product_code=product_code,
                sku=product_code,
                brand=brand,
                name=name,
                title=title or name,
                url=url,
                in_stock=in_stock,
                price_bgn=price_bgn,
                price_eur=price_eur,
                old_price_bgn=None,
                old_price_eur=None,
                energy_class=energy_class,
                specs={},
                detail_features=[],
                detail_specs={},
                ean=None,
            )
        )

    return rows


def extract_product_details(html: str) -> dict[str, object]:
    state = _load_state(html)
    product_state = state.get("cx-state", {}).get("product", {}).get("details", {}).get("entities", {})
    if not product_state:
        return {
            "detail_features": [],
            "detail_specs": {},
            "ean": None,
            "brand": None,
            "energy_class": None,
        }

    product_code, entity = next(iter(product_state.items()))
    meta = entity.get("meta", {})
    value = meta.get("value", {})
    attributes = entity.get("attributes", {}).get("value", {})
    details = entity.get("details", {}).get("value", {})
    variants = entity.get("variants", {}).get("value", {})

    detail_features: list[str] = []
    detail_specs: dict[str, object] = {}

    classifications = (
        attributes.get("classifications")
        or details.get("classifications")
        or variants.get("classifications")
        or []
    )
    for classification in classifications:
        if not isinstance(classification, dict):
            continue
        for feature in classification.get("features", []):
            if not isinstance(feature, dict):
                continue
            label = _clean_text(str(feature.get("name") or ""))
            feature_values = [
                _clean_text(str(item.get("value") or ""))
                for item in feature.get("featureValues", [])
                if isinstance(item, dict) and _clean_text(str(item.get("value") or ""))
            ]
            if not label or not feature_values:
                continue
            value_text = ", ".join(feature_values)
            key = canonicalize_label(label)
            detail_specs[key] = canonicalize_spec_value(key, value_text)
            if feature.get("listable", True):
                detail_features.append(f"{label}: {value_text}")

    ean = variants.get("ean") or details.get("ean") or attributes.get("ean")
    brand = variants.get("brand") or attributes.get("brand") or details.get("brand")
    energy_class = variants.get("energyClass") or details.get("energyClass") or attributes.get("energyClass")

    return {
        "detail_features": detail_features,
        "detail_specs": detail_specs,
        "ean": _clean_text(str(ean)) if ean else None,
        "brand": _clean_text(str(brand)) if brand else None,
        "energy_class": _clean_text(str(energy_class)) if energy_class else None,
    }
