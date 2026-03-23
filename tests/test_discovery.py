from technomarket_fridge_scraper.discovery import discover_categories
from technomarket_fridge_scraper.scraper import _format_category_name


SAMPLE_HUB_HTML = """
<html>
  <body>
    <a href="/produkti/hladilnitzi-dolna-kamera">С долна камера</a>
    <a href="/produkti/hladilnitzi-gorna-kamera">С горна камера</a>
    <a href="/produkti/side-by-side-hladilnitzi">Side By Side</a>
    <a href="/produkti/hladilnitzi-s-edna-vrata">С една врата</a>
    <a href="/produkti/hladilnitzi-dolna-kamera">С долна камера</a>
    <a href="/not-a-category">С долна камера</a>
    <a href="/produkti/frizeri">Фризери</a>
  </body>
</html>
"""


def test_discover_categories_from_hub():
    categories = discover_categories(
        SAMPLE_HUB_HTML,
        {
            "С долна камера",
            "С горна камера",
            "Side By Side",
            "С една врата",
            "Фризери",
        },
    )
    assert [category.path for category in categories] == [
        "/produkti/hladilnitzi-dolna-kamera",
        "/produkti/hladilnitzi-gorna-kamera",
        "/produkti/side-by-side-hladilnitzi",
        "/produkti/hladilnitzi-s-edna-vrata",
        "/produkti/frizeri",
    ]
    assert [category.name for category in categories] == [
        "С долна камера",
        "С горна камера",
        "Side By Side",
        "С една врата",
        "Фризери",
    ]


def test_format_category_name_with_prefix():
    assert _format_category_name("Хладилници", "С долна камера") == "Хладилници с долна камера"
    assert _format_category_name("Хладилници", "Всички хладилници") == "Хладилници"
