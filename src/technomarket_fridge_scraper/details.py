from __future__ import annotations

from bs4 import BeautifulSoup

from .normalization import canonicalize_label, canonicalize_spec_value


def _clean_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned or None


def extract_product_details(html: str) -> dict[str, object]:
    soup = BeautifulSoup(html, "html.parser")

    overview_features: list[str] = []
    basics_section = soup.select_one("div.collapsible#basics")
    if basics_section:
        for item in basics_section.select("div.product-basic ul li"):
            text = _clean_text(item.get_text(" ", strip=True))
            if text:
                overview_features.append(text)

    detail_specs: dict[str, object] = {}
    specs_section = soup.select_one("div.collapsible#specifications")
    if specs_section:
        for row in specs_section.select("table tr"):
            label_cell = row.select_one("td.label")
            if not label_cell:
                continue
            label = _clean_text(label_cell.get_text(" ", strip=True))
            value_cell = row.find_all("td")
            if len(value_cell) < 2:
                continue
            value = _clean_text(value_cell[1].get_text(" ", strip=True))
            if label and value:
                key = canonicalize_label(label)
                if key == "Продукт":
                    continue
                detail_specs[key] = canonicalize_spec_value(key, value)

    point_and_place = soup.select_one("tm-pointandplace")
    ean = None
    if point_and_place:
        ean = _clean_text(point_and_place.get("ean"))

    return {
        "detail_features": overview_features,
        "detail_specs": detail_specs,
        "ean": ean,
    }
