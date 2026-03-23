from __future__ import annotations

from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from .models import ApplianceProduct
from .normalization import (
    canonicalize_label,
    canonicalize_spec_value,
    parse_energy_class,
    parse_price_to_int,
)


def _first_text(node, selector: str) -> str | None:
    found = node.select_one(selector)
    if not found:
        return None
    text = found.get_text(" ", strip=True)
    return text or None


def _parse_price_pair(node) -> tuple[int | None, int | None]:
    if node is None:
        return None, None
    bgn = parse_price_to_int(_first_text(node, ".bgn_price"))
    eur = parse_price_to_int(_first_text(node, ".euro_price"))
    return bgn, eur


def extract_total_pages(soup: BeautifulSoup) -> int:
    pages = []
    for link in soup.select(".current-pages a[href]"):
        href = link.get("href", "")
        if "page=" in href:
            match = re.search(r"page=(\d+)", href)
            if match:
                pages.append(int(match.group(1)))
        elif link.get_text(strip=True).isdigit():
            pages.append(int(link.get_text(strip=True)))
    return max(pages, default=1)


def extract_products(
    html: str,
    base_url: str,
    category_name: str,
    category_path: str,
    page: int,
    in_stock_only: bool = True,
    store: str = "technomarket",
) -> list[ApplianceProduct]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[ApplianceProduct] = []

    for item in soup.find_all("tm-product-item"):
        product_code = item.get("data-product", "").strip()
        title_link = item.select_one("a.title")
        if not title_link:
            continue

        in_stock = item.select_one('button[data-action="addCart"]') is not None
        if in_stock_only and not in_stock:
            continue

        brand = _first_text(title_link, ".brand") or ""
        name = _first_text(title_link, ".name") or ""
        title = " ".join(part for part in [brand, name] if part).strip()
        href = title_link.get("href", "")
        url = urljoin(base_url, href)
        price_bgn, price_eur = _parse_price_pair(item.select_one(".price"))
        old_price_bgn, old_price_eur = _parse_price_pair(item.select_one(".old-price"))
        energy_class = parse_energy_class(_first_text(item, ".energy-class-label"))

        specs = {}
        for line in item.select(".specifications .line"):
            label = _first_text(line, ".label")
            value = _first_text(line, ".value")
            if label and value:
                key = canonicalize_label(label)
                if key == "Продукт":
                    continue
                specs[key] = canonicalize_spec_value(key, value)

        products.append(
            ApplianceProduct(
                store=store,
                category_name=category_name,
                category_path=category_path,
                page=page,
                product_code=product_code,
                sku=product_code,
                brand=brand,
                name=name,
                title=title or title_link.get_text(" ", strip=True),
                url=url,
                in_stock=in_stock,
                price_bgn=price_bgn,
                price_eur=price_eur,
                old_price_bgn=old_price_bgn,
                old_price_eur=old_price_eur,
                energy_class=energy_class,
                specs=specs,
                detail_features=[],
                detail_specs={},
                ean=None,
            )
        )

    return products
