from __future__ import annotations

from technomarket_fridge_scraper.comparison import group_compared_products, render_markdown


def test_group_compared_products_prefers_ean():
    rows = [
        {
            "store": "technomarket",
            "brand": "GORENJE",
            "name": "RK416EPS4",
            "title": "GORENJE RK416EPS4",
            "ean": "3838782766541",
            "price_bgn": 66303,
            "in_stock": True,
        },
        {
            "store": "technopolis",
            "brand": "",
            "name": "Refrigerator with bottom freezer GORENJE RK416EPS4 180.00 cm",
            "title": "Refrigerator with bottom freezer GORENJE RK416EPS4 180.00 cm",
            "ean": "3838782766541",
            "price_bgn": 68999,
            "in_stock": True,
        },
    ]

    groups = group_compared_products(rows)
    assert len(groups) == 1
    group = groups[0]
    assert group.product_id == "EAN 3838782766541"
    assert group.product_name == "GORENJE RK416EPS4"
    assert [offer["store"] for offer in group.offers] == ["technomarket", "technopolis"]


def test_group_compared_products_falls_back_to_brand_model():
    rows = [
        {
            "store": "technomarket",
            "brand": "BOSCH",
            "name": "WGG244F1BY",
            "title": "BOSCH WGG244F1BY",
            "ean": None,
            "price_bgn": 89999,
            "in_stock": True,
        },
        {
            "store": "technopolis",
            "brand": "",
            "name": "Washing machine BOSCH WGG244F1BY 9.0 kg",
            "title": "Washing machine BOSCH WGG244F1BY 9.0 kg",
            "ean": None,
            "price_bgn": 87999,
            "in_stock": True,
        },
    ]

    groups = group_compared_products(rows)
    assert len(groups) == 1
    assert groups[0].product_id == "BOSCH WGG244F1BY"


def test_render_markdown_contains_price_columns():
    rows = [
        {
            "store": "technomarket",
            "brand": "GORENJE",
            "name": "RK416EPS4",
            "title": "GORENJE RK416EPS4",
            "ean": "3838782766541",
            "price_bgn": 66303,
            "in_stock": True,
        },
        {
            "store": "technopolis",
            "brand": "",
            "name": "Refrigerator with bottom freezer GORENJE RK416EPS4 180.00 cm",
            "title": "Refrigerator with bottom freezer GORENJE RK416EPS4 180.00 cm",
            "ean": "3838782766541",
            "price_bgn": 68999,
            "in_stock": True,
        },
    ]
    groups = group_compared_products(rows)
    markdown = render_markdown(groups, [])
    assert "| Product name | ID | Best store offer | Price per store |" in markdown
    assert "technomarket" in markdown
    assert "EAN 3838782766541" in markdown
