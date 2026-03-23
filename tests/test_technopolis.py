import json

from bs4 import BeautifulSoup

from technomarket_fridge_scraper.stores.technopolis import (
    discover_categories_from_html,
    extract_product_details,
    extract_products,
    extract_total_pages,
)


LISTING_STATE = {
    "cx-state": {
        "product": {
            "search": {
                "results": {
                    "pagination": {"totalPages": 3},
                    "products": [
                        {
                            "code": "653705",
                            "url": "/en/Peralni-s-predno-zarezhdane/Peralnya-MIDEA-MF100W60-W-HR/p/653705",
                            "nameHtml": "Washing machine MIDEA MF100W60/W-HR",
                            "energyClass": "D",
                            "purchasable": True,
                            "showBuyButton": True,
                            "soldOut": False,
                        }
                    ],
                }
            }
        }
    }
}


DETAIL_STATE = {
    "cx-state": {
        "product": {
            "details": {
                "entities": {
                    "653705": {
                        "attributes": {
                            "value": {
                                "classifications": [
                                    {
                                        "features": [
                                            {
                                                "name": "MODEL",
                                                "listable": True,
                                                "featureValues": [{"value": "MF100W60/W-HR"}],
                                            },
                                            {
                                                "name": "WASHING CAPACITY",
                                                "listable": True,
                                                "featureValues": [{"value": "6.0 kg"}],
                                            },
                                            {
                                                "name": "WIDTH",
                                                "listable": True,
                                                "featureValues": [{"value": "60.0 cm"}],
                                            },
                                        ]
                                    }
                                ],
                                "ean": "6945878331785",
                                "brand": "MIDEA",
                                "energyClass": "D",
                            }
                        },
                        "variants": {
                            "value": {
                                "ean": "6945878331785",
                                "brand": "MIDEA",
                                "energyClass": "D",
                            }
                        },
                        "details": {"value": {"ean": "6945878331785", "energyClass": "D"}},
                    }
                }
            }
        }
    }
}


LISTING_HTML = f"""
<html>
  <body>
    <script id="ng-state" type="application/json">{json.dumps(LISTING_STATE, ensure_ascii=False)}</script>
    <te-product-box data-product-id="653705">Price: 199.90 € / 390.97 лв. Add to cart</te-product-box>
  </body>
</html>
"""


DETAIL_HTML = f"""
<html>
  <body>
    <script id="ng-state" type="application/json">{json.dumps(DETAIL_STATE, ensure_ascii=False)}</script>
  </body>
</html>
"""


TECHNOPOLIS_HUB_HTML = """
<html>
  <body>
    <a href="javascript:void(0);">Washing machines</a>
    <a href="/en/Domakinski-elektrouredi/Peralni/Peralni-s-predno-zarezhdane/c/P11100101">Front loading washing machines</a>
    <a href="/en/Domakinski-elektrouredi/Peralni/Peralni-s-gorno-zarezhdane/c/P11100103">Top loading washing machines</a>
    <a href="/en/Domakinski-elektrouredi/Peralni/Peralni-sas-Sushilni/c/P11100102">Washing machines & Dryers</a>
  </body>
</html>
"""


def test_extract_total_pages_technopolis():
    soup = BeautifulSoup(LISTING_HTML, "html.parser")
    assert extract_total_pages(soup) == 3


def test_extract_products_technopolis():
    rows = extract_products(
        html=LISTING_HTML,
        base_url="https://www.technopolis.bg",
        category_name="Washing machines",
        category_path="/en/Domakinski-elektrouredi/Peralni/c/P111001",
        page=1,
        in_stock_only=True,
    )
    assert len(rows) == 1
    row = rows[0].to_dict()
    assert row["store"] == "technopolis"
    assert row["product_code"] == "653705"
    assert row["price_eur"] == 19990
    assert row["price_bgn"] == 39097
    assert row["energy_class"] == "D"


def test_extract_product_details_technopolis():
    details = extract_product_details(DETAIL_HTML)
    assert details["ean"] == "6945878331785"
    assert details["brand"] == "MIDEA"
    assert details["energy_class"] == "D"
    assert details["detail_specs"]["model"] == "MF100W60/W-HR"
    assert details["detail_specs"]["washing_capacity_kg"] == 6
    assert details["detail_specs"]["width_cm"] == 60


def test_discover_categories_from_technopolis_hub():
    categories = discover_categories_from_html(
        TECHNOPOLIS_HUB_HTML,
        {
            "Front loading washing machines",
            "Top loading washing machines",
            "Washing machines & Dryers",
        },
    )
    assert [category.path for category in categories] == [
        "/en/Domakinski-elektrouredi/Peralni/Peralni-s-predno-zarezhdane/c/P11100101",
        "/en/Domakinski-elektrouredi/Peralni/Peralni-s-gorno-zarezhdane/c/P11100103",
        "/en/Domakinski-elektrouredi/Peralni/Peralni-sas-Sushilni/c/P11100102",
    ]
