from __future__ import annotations

from types import SimpleNamespace

from technomarket_fridge_scraper.scraper import write_markdown


def test_write_markdown_creates_table(tmp_path):
    path = tmp_path / "scrape.md"
    rows = [
        {
            "store": "technomarket",
            "category_name": "Хладилници с долна камера",
            "title": "LIEBHERR CBNsfc 572i",
            "product_code": "09220645",
            "price_bgn": 188900,
            "price_eur": 1022.07,
            "energy_class": "C",
            "url": "https://example.test",
        }
    ]
    config = SimpleNamespace(store="technomarket", appliance_type="refrigerator")

    write_markdown(path, rows, config)

    text = path.read_text(encoding="utf-8")
    assert "| Store | Category | Product | Product code | Price BGN | Price EUR | Energy class | URL |" in text
    assert "LIEBHERR CBNsfc 572i" in text
    assert "1 022.07" in text
