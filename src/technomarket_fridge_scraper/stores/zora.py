from __future__ import annotations

from urllib.parse import urljoin
import json
import re

from bs4 import BeautifulSoup

from ..config import Category
from ..models import ApplianceProduct
from ..normalization import canonicalize_spec_value, parse_energy_class, parse_price_to_int


_LABEL_MAP = {
    "Функции": "functions",
    "Гаранция": "warranty_months",
    "Други": "other_features",
    "Мощност W": "power_w",
    "Мощност  W": "power_w",
    "Обем/Вместимост, литри": "capacity_l",
    "Обем/Вместимост": "capacity_l",
    "Обем": "capacity_l",
    "Вместимост": "capacity_l",
    "Брой кошници": "basket_count",
    "Брой комплекти за миене": "place_settings",
    "Таймер за отложен старт": "delay_timer",
    "Ниво на шума (dB)": "noise_level_db",
    "Размер по ширина": "width_cm",
    "Размер по височина": "height_cm",
    "Размер по дълбочина": "depth_cm",
    "Широчина": "width_cm",
    "Ширина": "width_cm",
    "Височина": "height_cm",
    "Дълбочина": "depth_cm",
    "Енергиен клас": "energy_class",
    "Тип": "type",
    "Цвят": "color",
    "Марка": "brand",
    "Тегло": "weight_kg",
    "Дисплей": "display",
    "1/2 зареждане": "half_load",
    "Инверторен мотор": "inverter_motor",
    "Материал на водосъдържателя": "tank_material",
    "Функция размразяване": "defrost_function",
    "Звуков сигнал при приключване на работа": "end_signal",
    "Размери": "dimensions_text",
}


_VALUE_TRANSLATIONS = {
    "type": {
        "Свободностояща": "freestanding",
        "Свободностоящ": "freestanding",
        "За вграждане": "built_in",
        "Фурна за вграждане": "built_in_oven",
        "Керамичен": "ceramic",
        "Индукционен": "induction",
        "Газов": "gas",
        "Комбиниран": "combined",
        "Пералня с предно зареждане": "front_loader",
        "Пералня с горно зареждане": "top_loader",
    },
    "color": {
        "Бял": "white",
        "Черен": "black",
        "Инокс": "inox",
        "Сребрист": "silver",
        "Сив": "gray",
        "Бежов": "beige",
    },
}


def _clean_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned or None


def _load_state(html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="js-cc-page-data")
    if not script or not script.string:
        return {}
    match = re.search(r"var cc_page_data = (\{.*\});", script.string, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def _canon_label(label: str) -> str:
    label = label.strip().rstrip(":").strip()
    label = " ".join(label.split())
    if label in _LABEL_MAP:
        return _LABEL_MAP[label]
    if re.fullmatch(r"[A-Z0-9][A-Z0-9 /&\\-]*", label):
        return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return re.sub(r"[^0-9A-Za-z]+", "_", label.lower()).strip("_")


def _parse_price_pair(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    if "<" in text and ">" in text:
        text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    eur_match = re.search(r"([\d.,\s]+)\s*€", text)
    bgn_match = re.search(r"([\d.,\s]+)\s*лв\.", text)
    price_eur = parse_price_to_int(eur_match.group(1).replace(" ", "")) if eur_match else None
    price_bgn = parse_price_to_int(bgn_match.group(1).replace(" ", "")) if bgn_match else None
    return price_bgn, price_eur


def extract_total_pages(soup: BeautifulSoup) -> int:
    pages = []
    for link in soup.select('a[href*="?page="]'):
        href = link.get("href", "")
        match = re.search(r"[?&]page=(\d+)", href)
        if match:
            pages.append(int(match.group(1)))
    return max(pages, default=1)


def discover_categories_from_html(html: str, category_texts: set[str]) -> list[Category]:
    soup = BeautifulSoup(html, "html.parser")
    categories: list[Category] = []
    seen: set[str] = set()
    for anchor in soup.select('a[href]'):
        text = _clean_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href", "")
        if not text or text not in category_texts:
            continue
        if href in seen:
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
    store: str = "zora",
) -> list[ApplianceProduct]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[ApplianceProduct] = []

    for inner in soup.select("div._product-inner"):
        link = inner.select_one("div._product-name a[href*='/product/']")
        if not link:
            continue
        title = _clean_text(link.get_text(" ", strip=True)) or ""
        href = link.get("href", "")
        url = urljoin(base_url, href)
        data_input = inner.select_one("input[data-product]")
        data_product = {}
        if data_input and data_input.get("data-product"):
            try:
                data_product = json.loads(data_input["data-product"])
            except json.JSONDecodeError:
                data_product = {}

        card_text = inner.get_text(" ", strip=True)
        in_stock = "Купи" in card_text or bool(data_product.get("price"))
        if in_stock_only and not in_stock:
            continue

        product_code = str(data_product.get("id") or "").strip()
        sku = ""
        brand = ""
        brand_match = re.match(r"([A-Za-z0-9&+.\- ]+?)\s+[A-Z0-9]", title)
        if brand_match:
            brand = brand_match.group(1).strip()
        energy_class = parse_energy_class(title)
        price_source = str(data_product.get("price") or card_text)
        price_bgn, price_eur = _parse_price_pair(_clean_text(price_source))

        properties = {}
        for item in inner.select("._product-details-properties li"):
            label = _clean_text(item.select_one("._product-details-properties-title").get_text(" ", strip=True) if item.select_one("._product-details-properties-title") else None)
            value = item.select_one("._product-details-properties-value")
            if not label or value is None:
                continue
            values = [_clean_text(node.get_text(" ", strip=True)) for node in value.find_all(["a", "span"]) if _clean_text(node.get_text(" ", strip=True))]
            value_text = ", ".join(values) if values else _clean_text(value.get_text(" ", strip=True))
            if label and value_text:
                key = _canon_label(label)
                properties[key] = canonicalize_spec_value(key, value_text)

        rows.append(
            ApplianceProduct(
                store=store,
                category_name=category_name,
                category_path=category_path,
                page=page,
                product_code=product_code,
                sku=sku or product_code,
                brand=brand,
                name=title,
                title=title,
                url=url,
                in_stock=in_stock,
                price_bgn=price_bgn,
                price_eur=price_eur,
                old_price_bgn=None,
                old_price_eur=None,
                energy_class=energy_class,
                specs=properties,
                detail_features=[],
                detail_specs={},
                ean=None,
            )
        )

    return rows


def extract_product_details(html: str) -> dict[str, object]:
    state = _load_state(html)
    detail_specs: dict[str, object] = {}
    detail_features: list[str] = []

    characteristics = BeautifulSoup(html, "html.parser").select_one("#product-characteristics")
    if characteristics:
        for item in characteristics.select("._product-details-properties li"):
            label_node = item.select_one("._product-details-properties-title")
            value_node = item.select_one("._product-details-properties-value")
            if not label_node or not value_node:
                continue
            label = _clean_text(label_node.get_text(" ", strip=True))
            if not label:
                continue
            value_nodes = value_node.find_all("a")
            if value_nodes:
                values = [_clean_text(node.get_text(" ", strip=True)) for node in value_nodes if _clean_text(node.get_text(" ", strip=True))]
                value_text = ", ".join(values)
            else:
                value_text = _clean_text(value_node.get_text(" ", strip=True))
            if not value_text:
                continue
            key = _canon_label(label)
            detail_specs[key] = canonicalize_spec_value(key, value_text)
            detail_features.append(f"{label}: {value_text}")

    brand = state.get("brand")
    sku = state.get("sku")
    ean = state.get("barcode")
    energy_class = None
    if isinstance(state.get("variants"), list) and state["variants"]:
        variant = state["variants"][0]
        if isinstance(variant, dict):
            energy_class = variant.get("energy_class") or variant.get("energyClass")

    meta_description = _clean_text(BeautifulSoup(html, "html.parser").find("meta", attrs={"name": "description"}).get("content") if BeautifulSoup(html, "html.parser").find("meta", attrs={"name": "description"}) else None)
    if meta_description and "dimensions" not in detail_specs:
        detail_specs["description"] = meta_description

    return {
        "detail_features": detail_features,
        "detail_specs": detail_specs,
        "ean": _clean_text(str(ean)) if ean else None,
        "brand": _clean_text(str(brand)) if brand else None,
        "sku": _clean_text(str(sku)) if sku else None,
        "energy_class": _clean_text(str(energy_class)) if energy_class else None,
    }
